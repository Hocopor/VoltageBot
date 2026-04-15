from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import RuntimeSetting
from app.models.journal import JournalEntry
from app.models.market import PairSelection
from app.models.strategy import StrategyDecision
from app.models.system import SystemState
from app.models.trade import Order, PnlSnapshot, Position, PositionLifecycleEvent, Trade
from app.services.bybit import BybitError, BybitService


class TradingError(RuntimeError):
    pass


@dataclass
class ExecutionPlan:
    entry_price: float
    qty: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    risk_amount: float
    risk_per_unit: float
    working_balance: float
    rationale: str


class TradingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.bybit = BybitService()

    async def execute_trade(self, payload) -> dict:
        runtime = self._runtime_settings()
        state = self._system_state()
        if state.maintenance_mode:
            raise TradingError('System is in maintenance mode')
        if state.trading_paused:
            raise TradingError('Trading is paused by operations controls')
        if state.kill_switch_armed:
            raise TradingError('Kill switch is armed; execution is blocked')
        if runtime.mode == 'historical':
            raise TradingError('Historical mode does not accept live execution requests')
        market_type = payload.market_type
        side = payload.side.lower()
        if market_type == 'spot' and side != 'buy':
            raise TradingError('Spot mode supports long entries only')
        self._validate_selected_symbol(payload.symbol, market_type)

        entry_price = float(payload.price) if payload.price else await self._entry_price(payload.symbol, market_type, payload.order_type, side)
        plan = self._build_plan(
            entry_price=entry_price,
            market_type=market_type,
            symbol=payload.symbol,
            side=side,
            qty=payload.qty,
            stop_loss=payload.stop_loss,
            risk_percent=payload.risk_percent,
            working_balance=self._working_balance(runtime, market_type),
        )

        decision = StrategyDecision(
            strategy_name='VOLTAGE',
            symbol=payload.symbol,
            timeframe_context='1D,4H,1H',
            allowed=True,
            market_scenario='execution-core',
            filter_summary='Execution checkpoint validated mode, side, selected pair, mandatory SL/TP plan and risk bounds 1-3% per trade.',
            risk_summary=f'Working balance {plan.working_balance:.2f}, risk amount {plan.risk_amount:.2f}, qty {plan.qty:.8f}',
            confidence=0.8,
        )
        self.db.add(decision)
        self.db.flush()

        if runtime.mode == 'live':
            result = await self._execute_live(runtime.mode, payload, plan)
        else:
            result = await self._execute_paper(runtime.mode, payload, plan)

        self.db.commit()
        return result

    async def sync_paper_market(self) -> dict:
        open_orders = self.db.scalars(select(Order).where(Order.mode == 'paper', Order.status.in_(['created', 'open']))).all()
        open_positions = self.db.scalars(select(Position).where(Position.mode == 'paper', Position.status == 'open')).all()
        touched = {(row.symbol, row.market_type) for row in open_orders} | {(row.symbol, row.market_type) for row in open_positions}
        prices = await self._fetch_prices(touched)

        filled_orders = 0
        closed_positions = 0
        for order in open_orders:
            quote = prices.get((order.symbol, order.market_type))
            if quote is None:
                continue
            current = quote.last_price
            if order.order_type.lower() == 'limit' and self._limit_is_fillable(order.side, order.price or current, current):
                self._fill_pending_entry(order, current)
                filled_orders += 1
            elif order.order_type.lower() == 'market' and order.status in {'created', 'open'}:
                self._fill_pending_entry(order, current)
                filled_orders += 1

        for position in open_positions:
            quote = prices.get((position.symbol, position.market_type))
            if quote is None:
                continue
            if self._process_position(position, quote.last_price):
                closed_positions += 1

        self.db.commit()
        return {'filled_orders': filled_orders, 'closed_positions': closed_positions, 'tracked_symbols': len(touched)}

    async def sync_live_account(self) -> dict:
        balances_payload = await self.bybit.get_wallet_balances()
        orders_payload = await self.bybit.get_open_orders('spot', open_only=0)
        futures_orders_payload = await self.bybit.get_open_orders('futures', open_only=0)
        positions_payload = await self.bybit.get_positions()
        return {
            'balances': balances_payload.get('result', {}),
            'spot_orders': orders_payload.get('result', {}),
            'futures_orders': futures_orders_payload.get('result', {}),
            'positions': positions_payload.get('result', {}),
        }

    async def sync_live_lifecycle(self) -> dict:
        state = self._system_state()
        spot_open = await self.bybit.get_open_orders('spot', open_only=0)
        spot_recent = await self.bybit.get_open_orders('spot', open_only=1)
        futures_open = await self.bybit.get_open_orders('futures', open_only=0)
        futures_recent = await self.bybit.get_open_orders('futures', open_only=1)
        positions_payload = await self.bybit.get_positions()

        combined_orders = [
            ('spot', item) for item in self._merge_order_payloads(spot_open, spot_recent)
        ] + [
            ('futures', item) for item in self._merge_order_payloads(futures_open, futures_recent)
        ]

        order_sync = self._sync_live_orders(combined_orders)
        position_sync = await self._sync_live_positions(positions_payload)

        state.last_lifecycle_sync_at = self._utcnow_iso()
        state.last_live_sync_status = 'completed'
        state.last_live_sync_message = (
            f"orders_checked={order_sync['orders_checked']}; orders_filled={order_sync['orders_filled']}; "
            f"positions_seen={position_sync['positions_seen']}; positions_closed={position_sync['positions_closed']}"
        )
        self.db.add(state)
        self.db.commit()
        summary = {
            **order_sync,
            **position_sync,
            'summary': state.last_live_sync_message,
        }
        return summary

    async def sync_lifecycle(self) -> dict:
        open_positions = list(self.db.scalars(select(Position).where(Position.status == 'open')).all())
        touched = {(p.symbol, p.market_type) for p in open_positions}
        prices = await self._fetch_prices(touched)
        synced_positions = 0
        closed_positions = 0
        created_events = 0
        for position in open_positions:
            current = prices.get((position.symbol, position.market_type))
            mark = current.last_price if current else (position.mark_price or position.avg_entry_price)
            position.mark_price = mark
            self._update_extremes(position, mark)
            self._lifecycle_event(position, 'sync', f'Lifecycle sync mark={mark:.8f}', price=mark)
            synced_positions += 1
            created_events += 1
            if self._process_position(position, mark):
                closed_positions += 1
        self.db.commit()
        return {'synced_positions': synced_positions, 'closed_positions': closed_positions, 'created_events': created_events}

    def close_position(self, position_id: int, exit_price: float | None = None, reason: str = 'manual-close') -> dict:
        position = self.db.get(Position, position_id)
        if not position or position.status != 'open':
            raise TradingError('Open position not found')
        current_price = exit_price if exit_price is not None else (position.mark_price or position.avg_entry_price)

        if position.mode == 'live':
            trade = self.db.get(Trade, position.trade_id) if position.trade_id else None
            client_order_id = f'voltage-close-{uuid4().hex[:20]}'
            if position.market_type == 'futures':
                result = self._run_async(
                    self.bybit.close_linear_position(
                        symbol=position.symbol,
                        side=position.side,
                        qty=position.size,
                        position_idx=position.position_idx,
                        order_link_id=client_order_id,
                    )
                )
            else:
                if position.side != 'buy':
                    raise TradingError('Live spot close supports long spot positions only')
                result = self._run_async(
                    self.bybit.close_spot_position(symbol=position.symbol, qty=position.size, order_link_id=client_order_id)
                )
            exchange_order_id = result.get('result', {}).get('orderId')
            close_order = Order(
                mode='live',
                market_type=position.market_type,
                symbol=position.symbol,
                side='sell' if position.side == 'buy' else 'buy',
                order_type='market',
                stage=reason,
                status='submitted',
                bybit_order_id=exchange_order_id,
                client_order_id=client_order_id,
                qty=position.size,
                filled_qty=0.0,
                price=None,
                avg_fill_price=None,
                reduce_only=position.market_type == 'futures',
                rationale=f'Live close submitted by {reason}',
            )
            self.db.add(close_order)
            self._lifecycle_event(position, 'close-submitted', f'Live close order submitted by {reason}', price=current_price, payload={'client_order_id': client_order_id, 'exchange_order_id': exchange_order_id})
            if trade is not None:
                trade.notes = (trade.notes or '') + f' | close-submitted:{reason}'
                self.db.add(trade)
            self.db.commit()
            return {
                'position_id': position.id,
                'trade_id': trade.id if trade else None,
                'status': 'close-submitted',
                'exit_price': current_price,
                'exchange_order_id': exchange_order_id,
                'client_order_id': client_order_id,
            }

        self._close_remaining_position(position, current_price, reason)
        self.db.commit()
        trade = self.db.get(Trade, position.trade_id)
        return {
            'position_id': position.id,
            'trade_id': trade.id if trade else None,
            'status': position.status,
            'exit_price': current_price,
            'realized_pnl': trade.realized_pnl if trade else 0.0,
        }

    def list_orders(self) -> list[Order]:
        return list(self.db.scalars(select(Order).order_by(Order.created_at.desc())).all())

    def list_trades(self) -> list[Trade]:
        trades = list(self.db.scalars(select(Trade).order_by(Trade.created_at.desc())).all())
        for trade in trades:
            if trade.status == 'open':
                position = self.db.scalar(select(Position).where(Position.trade_id == trade.id, Position.status == 'open'))
                if position and position.mark_price is not None:
                    trade.unrealized_pnl = self._calculate_pnl(position.side, position.avg_entry_price, position.mark_price, position.size)
        return trades

    def list_positions(self) -> list[Position]:
        return list(self.db.scalars(select(Position).order_by(Position.created_at.desc())).all())

    def list_lifecycle_events(self) -> list[PositionLifecycleEvent]:
        return list(self.db.scalars(select(PositionLifecycleEvent).order_by(PositionLifecycleEvent.created_at.desc())).all())

    def pnl_overview(self) -> dict:
        trades = list(self.db.scalars(select(Trade)).all())
        positions = list(self.db.scalars(select(Position).where(Position.status == 'open')).all())
        realized = round(sum(t.realized_pnl for t in trades), 8)
        unrealized = round(sum(self._calculate_pnl(p.side, p.avg_entry_price, p.mark_price or p.avg_entry_price, p.size) for p in positions), 8)
        closed = [t for t in trades if t.status == 'closed']
        wins = sum(1 for t in closed if t.realized_pnl > 0)
        return {
            'realized_pnl': realized,
            'unrealized_pnl': unrealized,
            'open_positions': len(positions),
            'closed_trades': len(closed),
            'win_rate': round((wins / len(closed)) * 100, 2) if closed else 0.0,
        }

    def journal_entries(self) -> list[JournalEntry]:
        return list(self.db.scalars(select(JournalEntry).order_by(JournalEntry.created_at.desc())).all())

    def journal_summary(self) -> dict:
        entries = self.journal_entries()
        wins = sum(1 for e in entries if e.realized_pnl > 0)
        losses = sum(1 for e in entries if e.realized_pnl < 0)
        hold_values = [e.hold_minutes for e in entries if e.hold_minutes is not None]
        by_mode: dict[str, int] = {}
        for entry in entries:
            by_mode[entry.mode] = by_mode.get(entry.mode, 0) + 1
        return {
            'total_entries': len(entries),
            'total_realized_pnl': round(sum(e.realized_pnl for e in entries), 8),
            'wins': wins,
            'losses': losses,
            'avg_hold_minutes': round(sum(hold_values) / len(hold_values), 4) if hold_values else 0.0,
            'by_mode': by_mode,
        }

    def analytics_overview(self) -> dict:
        entries = list(reversed(self.journal_entries()))
        realized = round(sum(e.realized_pnl for e in entries), 8)
        rr_values: list[float] = []
        equity_curve = [0.0]
        cumulative = 0.0
        monthly: dict[str, float] = {}
        yearly: dict[str, float] = {}
        by_mode = self._bucket_sum(entries, lambda x: x.mode)
        by_market = self._bucket_sum(entries, lambda x: x.market_type)
        by_symbol = self._bucket_sum(entries, lambda x: x.symbol)
        by_direction = self._bucket_sum(entries, lambda x: x.direction)
        by_close_reason = self._bucket_sum(entries, lambda x: x.close_reason or 'unknown')
        by_weekday = self._bucket_sum(entries, lambda x: x.created_at.strftime('%A') if isinstance(x.created_at, datetime) else 'unknown')
        by_hour = self._bucket_sum(entries, lambda x: x.created_at.strftime('%H:00') if isinstance(x.created_at, datetime) else 'unknown')
        tp_hit_distribution: dict[str, int] = {'tp1': 0, 'tp2': 0, 'tp3': 0, 'trailing-stop': 0, 'stop-loss': 0, 'manual-close': 0, 'other': 0}
        compliance_values: list[float] = []
        hold_values: list[float] = []

        max_win_streak = 0
        max_loss_streak = 0
        win_streak = 0
        loss_streak = 0
        for entry in entries:
            risk = abs(entry.entry_price - (entry.stop_loss or entry.entry_price))
            if risk > 0 and entry.exit_price is not None:
                rr_values.append(abs(entry.exit_price - entry.entry_price) / risk)
            cumulative += entry.realized_pnl
            equity_curve.append(round(cumulative, 8))
            if isinstance(entry.created_at, datetime):
                month_bucket = entry.created_at.strftime('%Y-%m')
                year_bucket = entry.created_at.strftime('%Y')
            else:
                month_bucket = 'unknown'
                year_bucket = 'unknown'
            monthly[month_bucket] = round(monthly.get(month_bucket, 0.0) + entry.realized_pnl, 8)
            yearly[year_bucket] = round(yearly.get(year_bucket, 0.0) + entry.realized_pnl, 8)
            close_key = entry.close_reason or 'other'
            if close_key not in tp_hit_distribution:
                close_key = 'other'
            tp_hit_distribution[close_key] += 1
            if entry.compliance_score is not None:
                compliance_values.append(entry.compliance_score)
            if entry.hold_minutes is not None:
                hold_values.append(entry.hold_minutes)
            if entry.realized_pnl > 0:
                win_streak += 1
                loss_streak = 0
            elif entry.realized_pnl < 0:
                loss_streak += 1
                win_streak = 0
            else:
                win_streak = 0
                loss_streak = 0
            max_win_streak = max(max_win_streak, win_streak)
            max_loss_streak = max(max_loss_streak, loss_streak)

        return {
            'total_trades': len(entries),
            'closed_trades': len(entries),
            'realized_pnl': realized,
            'profit_factor': self._profit_factor(entries),
            'average_rr': round(sum(rr_values) / len(rr_values), 4) if rr_values else 0.0,
            'max_drawdown': round(self._max_drawdown(equity_curve), 4),
            'by_mode': by_mode,
            'by_market': by_market,
            'by_symbol': by_symbol,
            'by_direction': by_direction,
            'by_close_reason': by_close_reason,
            'by_weekday': by_weekday,
            'by_hour': by_hour,
            'monthly_pnl': monthly,
            'yearly_pnl': yearly,
            'tp_hit_distribution': tp_hit_distribution,
            'streaks': {'max_win_streak': max_win_streak, 'max_loss_streak': max_loss_streak},
            'average_hold_minutes': round(sum(hold_values) / len(hold_values), 4) if hold_values else 0.0,
            'average_compliance_score': round(sum(compliance_values) / len(compliance_values), 4) if compliance_values else 0.0,
            'recent_equity_curve': equity_curve[-30:],
        }

    async def _execute_live(self, mode: str, payload, plan: ExecutionPlan) -> dict:
        category = 'linear' if payload.market_type == 'futures' else 'spot'
        side = 'Buy' if payload.side.lower() == 'buy' else 'Sell'
        order_link_id = f'voltage-{uuid4().hex[:24]}'
        body = {
            'category': category,
            'symbol': payload.symbol,
            'side': side,
            'orderType': payload.order_type.title(),
            'qty': self._fmt(plan.qty),
            'orderLinkId': order_link_id,
            'stopLoss': self._fmt(plan.stop_loss),
            'takeProfit': self._fmt(plan.tp3),
            'slOrderType': 'Market',
            'tpOrderType': 'Market',
        }
        if payload.order_type.lower() == 'limit':
            body['price'] = self._fmt(plan.entry_price)
            body['timeInForce'] = 'GTC'
        result = await self.bybit.place_order(body)
        order = Order(
            mode=mode,
            market_type=payload.market_type,
            symbol=payload.symbol,
            side=payload.side.lower(),
            order_type=payload.order_type.lower(),
            stage='entry',
            status='submitted',
            bybit_order_id=result.get('result', {}).get('orderId'),
            client_order_id=order_link_id,
            qty=plan.qty,
            filled_qty=0.0,
            price=plan.entry_price if payload.order_type.lower() == 'limit' else None,
            avg_fill_price=None,
            stop_loss=plan.stop_loss,
            take_profit_1=plan.tp1,
            take_profit_2=plan.tp2,
            take_profit_3=plan.tp3,
            reduce_only=False,
            last_exchange_status='submitted',
            last_exchange_update_at=self._utcnow_iso(),
            rationale=plan.rationale,
        )
        self.db.add(order)
        self._record_snapshot(mode, payload.market_type, payload.symbol)
        return {
            'mode': mode,
            'execution': 'live',
            'order_id': order.bybit_order_id,
            'client_order_id': order.client_order_id,
            'status': order.status,
            'plan': self._plan_dict(plan),
            'note': 'Live checkpoint places the entry order with exchange-level SL and final TP. TP ladder management remains local for later checkpoints.',
        }

    async def _execute_paper(self, mode: str, payload, plan: ExecutionPlan) -> dict:
        order = Order(
            mode=mode,
            market_type=payload.market_type,
            symbol=payload.symbol,
            side=payload.side.lower(),
            order_type=payload.order_type.lower(),
            stage='entry',
            status='created',
            client_order_id=f'paper-{uuid4().hex[:18]}',
            qty=plan.qty,
            filled_qty=0.0,
            price=plan.entry_price if payload.order_type.lower() == 'limit' else None,
            avg_fill_price=None,
            stop_loss=plan.stop_loss,
            take_profit_1=plan.tp1,
            take_profit_2=plan.tp2,
            take_profit_3=plan.tp3,
            reduce_only=False,
            rationale=plan.rationale,
        )
        self.db.add(order)
        self.db.flush()
        if payload.order_type.lower() == 'market':
            self._fill_pending_entry(order, plan.entry_price)
        self._record_snapshot(mode, payload.market_type, payload.symbol)
        return {'mode': mode, 'execution': 'paper', 'order_id': order.id, 'status': order.status, 'plan': self._plan_dict(plan)}

    def _fill_pending_entry(self, order: Order, fill_price: float) -> None:
        if order.status == 'filled':
            return
        order.status = 'filled'
        order.filled_qty = order.qty
        order.avg_fill_price = fill_price
        order.last_exchange_status = 'filled' if order.mode == 'live' else order.last_exchange_status
        order.last_exchange_update_at = self._utcnow_iso() if order.mode == 'live' else order.last_exchange_update_at
        trade = Trade(
            order_id=order.id,
            mode=order.mode,
            market_type=order.market_type,
            symbol=order.symbol,
            direction=order.side,
            status='open',
            entry_price=fill_price,
            exit_price=None,
            initial_qty=order.qty,
            remaining_qty=order.qty,
            stop_loss=order.stop_loss or fill_price,
            take_profit_1=order.take_profit_1 or fill_price,
            take_profit_2=order.take_profit_2 or fill_price,
            take_profit_3=order.take_profit_3 or fill_price,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            notes=order.rationale,
        )
        self.db.add(trade)
        self.db.flush()
        risk_per_unit = abs(fill_price - (order.stop_loss or fill_price))
        position = Position(
            trade_id=trade.id,
            mode=order.mode,
            market_type=order.market_type,
            symbol=order.symbol,
            side=order.side,
            status='open',
            size=order.qty,
            initial_size=order.qty,
            avg_entry_price=fill_price,
            mark_price=fill_price,
            stop_loss=order.stop_loss or fill_price,
            take_profit_1=order.take_profit_1 or fill_price,
            take_profit_2=order.take_profit_2 or fill_price,
            take_profit_3=order.take_profit_3 or fill_price,
            trailing_distance=risk_per_unit if risk_per_unit > 0 else None,
            best_price=fill_price,
            worst_price=fill_price,
            entry_timeframe='runtime-execution',
            position_idx=0,
            last_exchange_size=order.qty if order.mode == 'live' else None,
            last_live_sync_at=self._utcnow_iso() if order.mode == 'live' else None,
            external_source='bybit' if order.mode == 'live' else 'paper-engine',
        )
        self.db.add(position)
        self.db.flush()
        self._lifecycle_event(position, 'opened', 'Position opened from filled entry order', price=fill_price, payload={'order_id': order.id})

    def _process_position(self, position: Position, current_price: float) -> bool:
        trade = self.db.get(Trade, position.trade_id)
        if not trade:
            return False
        position.mark_price = current_price
        self._update_extremes(position, current_price)
        trade.unrealized_pnl = self._calculate_pnl(position.side, position.avg_entry_price, current_price, position.size)

        if self._stop_is_hit(position.side, current_price, position.stop_loss):
            self._close_remaining_position(position, current_price, 'stop-loss')
            return True

        if not position.tp1_hit and self._target_is_hit(position.side, current_price, position.take_profit_1):
            self._partial_close(position, trade, current_price, 0.40, 'tp1')
            position.tp1_hit = True
            position.stop_loss = position.avg_entry_price
            self._lifecycle_event(position, 'tp1', 'TP1 reached; stop moved to break-even', price=current_price)
        if position.status != 'open':
            return True

        if not position.tp2_hit and self._target_is_hit(position.side, current_price, position.take_profit_2):
            self._partial_close(position, trade, current_price, 0.30, 'tp2')
            position.tp2_hit = True
            self._lifecycle_event(position, 'tp2', 'TP2 reached; partial close executed', price=current_price)
        if position.status != 'open':
            return True

        if not position.tp3_hit and self._target_is_hit(position.side, current_price, position.take_profit_3):
            position.tp3_hit = True
            position.trailing_active = True
            position.trailing_anchor_price = current_price
            if position.trailing_distance is None:
                position.trailing_distance = abs(position.avg_entry_price - position.stop_loss)
            self._lifecycle_event(position, 'tp3', 'TP3 reached; trailing stop armed', price=current_price)

        if position.trailing_active:
            if position.side == 'buy':
                position.trailing_anchor_price = max(position.trailing_anchor_price or current_price, current_price)
                if current_price <= (position.trailing_anchor_price or current_price) - (position.trailing_distance or 0.0):
                    self._close_remaining_position(position, current_price, 'trailing-stop')
                    return True
            else:
                position.trailing_anchor_price = min(position.trailing_anchor_price or current_price, current_price)
                if current_price >= (position.trailing_anchor_price or current_price) + (position.trailing_distance or 0.0):
                    self._close_remaining_position(position, current_price, 'trailing-stop')
                    return True

        self._record_snapshot(position.mode, position.market_type, position.symbol)
        return position.status != 'open'

    def _partial_close(self, position: Position, trade: Trade, price: float, ratio: float, stage: str) -> None:
        close_qty = min(position.size, round(position.initial_size * ratio, 12))
        if close_qty <= 0:
            return
        pnl = self._calculate_pnl(position.side, position.avg_entry_price, price, close_qty)
        trade.realized_pnl += pnl
        trade.remaining_qty = max(0.0, position.size - close_qty)
        trade.unrealized_pnl = self._calculate_pnl(position.side, position.avg_entry_price, price, trade.remaining_qty)
        position.size = max(0.0, position.size - close_qty)
        self._update_extremes(position, price)
        self.db.add(
            Order(
                mode=position.mode,
                market_type=position.market_type,
                symbol=position.symbol,
                side='sell' if position.side == 'buy' else 'buy',
                order_type='market',
                stage=stage,
                status='filled',
                qty=close_qty,
                filled_qty=close_qty,
                price=price,
                avg_fill_price=price,
                reduce_only=position.market_type == 'futures',
                rationale=f'Auto-managed {stage} partial exit',
            )
        )
        self._lifecycle_event(position, stage, f'Partial close executed for {stage}', price=price, payload={'close_qty': close_qty, 'realized_pnl': pnl})
        if position.size <= 0.0:
            self._finalize_trade_close(position, trade, price, stage)

    def _close_remaining_position(self, position: Position, price: float, reason: str) -> None:
        trade = self.db.get(Trade, position.trade_id)
        if not trade or position.status != 'open':
            return
        self._update_extremes(position, price)
        if position.size > 0:
            pnl = self._calculate_pnl(position.side, position.avg_entry_price, price, position.size)
            trade.realized_pnl += pnl
            self.db.add(
                Order(
                    mode=position.mode,
                    market_type=position.market_type,
                    symbol=position.symbol,
                    side='sell' if position.side == 'buy' else 'buy',
                    order_type='market',
                    stage=reason,
                    status='filled',
                    qty=position.size,
                    filled_qty=position.size,
                    price=price,
                    avg_fill_price=price,
                    reduce_only=position.market_type == 'futures',
                    rationale=f'Position closed by {reason}',
                )
            )
        self._finalize_trade_close(position, trade, price, reason)

    def _finalize_trade_close(self, position: Position, trade: Trade, price: float, reason: str) -> None:
        position.size = 0.0
        position.mark_price = price
        position.status = 'closed'
        position.trailing_active = False
        position.last_exchange_size = 0.0 if position.mode == 'live' else position.last_exchange_size
        position.last_live_sync_at = self._utcnow_iso() if position.mode == 'live' else position.last_live_sync_at
        trade.remaining_qty = 0.0
        trade.exit_price = price
        trade.unrealized_pnl = 0.0
        trade.status = 'closed'
        self._record_snapshot(position.mode, position.market_type, position.symbol)

        trade_created = trade.created_at if getattr(trade.created_at, 'tzinfo', None) else trade.created_at.replace(tzinfo=timezone.utc)
        hold_minutes = max(0.0, round((datetime.now(timezone.utc) - trade_created).total_seconds() / 60.0, 4))
        best = position.best_price if position.best_price is not None else max(trade.entry_price, price)
        worst = position.worst_price if position.worst_price is not None else min(trade.entry_price, price)
        if position.side == 'sell':
            mfe_pnl = self._calculate_pnl(position.side, trade.entry_price, worst, trade.initial_qty)
            mae_pnl = self._calculate_pnl(position.side, trade.entry_price, best, trade.initial_qty)
        else:
            mfe_pnl = self._calculate_pnl(position.side, trade.entry_price, best, trade.initial_qty)
            mae_pnl = self._calculate_pnl(position.side, trade.entry_price, worst, trade.initial_qty)
        chart_points = json.dumps({'entry_price': trade.entry_price, 'exit_price': price, 'stop_loss': trade.stop_loss, 'tp1': trade.take_profit_1, 'tp2': trade.take_profit_2, 'tp3': trade.take_profit_3})
        self.db.add(
            JournalEntry(
                trade_id=trade.id,
                mode=trade.mode,
                market_type=trade.market_type,
                symbol=trade.symbol,
                direction=trade.direction,
                quantity=trade.initial_qty,
                entry_price=trade.entry_price,
                exit_price=price,
                stop_loss=trade.stop_loss,
                take_profit_1=trade.take_profit_1,
                take_profit_2=trade.take_profit_2,
                take_profit_3=trade.take_profit_3,
                realized_pnl=trade.realized_pnl,
                chart_points=chart_points,
                tags='live-or-paper,auto-close',
                ai_review_status='pending',
                ai_review_text=f'Execution checkpoint journal entry generated after {reason}. Full AI post-trade review lands in later checkpoints.',
                close_reason=reason,
                hold_minutes=hold_minutes,
                best_price=best,
                worst_price=worst,
                mfe_pnl=mfe_pnl,
                mae_pnl=mae_pnl,
                strategy_scenario='execution-core',
                compliance_score=1.0,
                review_summary=f'Closed by {reason} with realized PnL {trade.realized_pnl:.4f}.',
            )
        )
        self._lifecycle_event(position, reason, f'Position closed by {reason}', price=price, payload={'trade_id': trade.id, 'realized_pnl': trade.realized_pnl})

    def _build_plan(
        self,
        *,
        entry_price: float,
        market_type: str,
        symbol: str,
        side: str,
        qty: float | None,
        stop_loss: float | None,
        risk_percent: float,
        working_balance: float,
    ) -> ExecutionPlan:
        normalized_stop = stop_loss if stop_loss is not None else self._default_stop(entry_price, symbol, side)
        risk_per_unit = abs(entry_price - normalized_stop)
        if risk_per_unit <= 0:
            raise TradingError('Stop-loss must differ from entry price')
        if not 0.01 <= risk_percent <= 0.03:
            raise TradingError('Risk percent must stay between 1% and 3%')
        risk_amount = working_balance * risk_percent
        effective_qty = qty if qty is not None else round(risk_amount / risk_per_unit, 8)
        if effective_qty <= 0:
            raise TradingError('Computed quantity must be positive')
        tp1 = self._target_from_r(entry_price, normalized_stop, side, 1.5)
        tp2 = self._target_from_r(entry_price, normalized_stop, side, 3.0)
        tp3 = self._target_from_r(entry_price, normalized_stop, side, 5.0)
        rationale = (
            f'Entry {entry_price:.8f}; stop {normalized_stop:.8f}; TP ladder {tp1:.8f}/{tp2:.8f}/{tp3:.8f}; '
            f'risk {risk_percent * 100:.2f}% of working balance.'
        )
        return ExecutionPlan(
            entry_price=entry_price,
            qty=effective_qty,
            stop_loss=normalized_stop,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            risk_amount=risk_amount,
            risk_per_unit=risk_per_unit,
            working_balance=working_balance,
            rationale=rationale,
        )

    async def _entry_price(self, symbol: str, market_type: str, order_type: str, side: str) -> float:
        quote = await self.bybit.fetch_ticker(symbol, market_type)
        if order_type.lower() == 'limit':
            return quote.last_price
        if side == 'buy':
            return quote.ask_price or quote.last_price
        return quote.bid_price or quote.last_price

    async def _fetch_prices(self, pairs: Iterable[tuple[str, str]]) -> dict[tuple[str, str], object]:
        unique = {(symbol, market_type) for symbol, market_type in pairs if symbol}
        result: dict[tuple[str, str], object] = {}
        for symbol, market_type in unique:
            try:
                result[(symbol, market_type)] = await self.bybit.fetch_ticker(symbol, market_type)
            except Exception:
                continue
        return result

    def _runtime_settings(self) -> RuntimeSetting:
        settings = self.db.scalar(select(RuntimeSetting).order_by(RuntimeSetting.id.asc()))
        if settings is None:
            settings = RuntimeSetting()
            self.db.add(settings)
            self.db.flush()
        return settings

    def _system_state(self) -> SystemState:
        state = self.db.scalar(select(SystemState).order_by(SystemState.id.asc()))
        if state is None:
            state = SystemState(
                maintenance_mode=False,
                trading_paused=False,
                kill_switch_armed=False,
                boot_count=0,
                last_live_sync_status='never',
                last_live_sync_message='Auto-created by trading service',
                recovery_runs_count=0,
            )
            self.db.add(state)
            self.db.flush()
        return state

    def _working_balance(self, runtime: RuntimeSetting, market_type: str) -> float:
        return runtime.spot_working_balance if market_type == 'spot' else runtime.futures_working_balance

    def _validate_selected_symbol(self, symbol: str, market_type: str) -> None:
        selected = list(self.db.scalars(select(PairSelection.symbol).where(PairSelection.market_type == market_type, PairSelection.selected.is_(True))).all())
        if selected and symbol not in selected:
            raise TradingError(f'Symbol {symbol} is not enabled in {market_type} pair settings')

    def _default_stop(self, entry_price: float, symbol: str, side: str) -> float:
        is_major = symbol.startswith('BTC') or symbol.startswith('ETH')
        pct = 0.06 if is_major else 0.10
        return entry_price * (1 - pct) if side == 'buy' else entry_price * (1 + pct)

    def _target_from_r(self, entry: float, stop: float, side: str, multiple: float) -> float:
        distance = abs(entry - stop) * multiple
        return entry + distance if side == 'buy' else entry - distance

    def _limit_is_fillable(self, side: str, limit_price: float, current_price: float) -> bool:
        return current_price <= limit_price if side == 'buy' else current_price >= limit_price

    def _stop_is_hit(self, side: str, current_price: float, stop_price: float) -> bool:
        return current_price <= stop_price if side == 'buy' else current_price >= stop_price

    def _target_is_hit(self, side: str, current_price: float, target_price: float) -> bool:
        return current_price >= target_price if side == 'buy' else current_price <= target_price

    def _calculate_pnl(self, side: str, entry: float, exit_price: float, qty: float) -> float:
        return round((exit_price - entry) * qty, 8) if side == 'buy' else round((entry - exit_price) * qty, 8)

    def _record_snapshot(self, mode: str, market_type: str, symbol: str) -> None:
        realized = sum(t.realized_pnl for t in self.db.scalars(select(Trade).where(Trade.mode == mode, Trade.market_type == market_type, Trade.symbol == symbol)).all())
        unrealized = sum(
            self._calculate_pnl(p.side, p.avg_entry_price, p.mark_price or p.avg_entry_price, p.size)
            for p in self.db.scalars(select(Position).where(Position.mode == mode, Position.market_type == market_type, Position.symbol == symbol, Position.status == 'open')).all()
        )
        self.db.add(PnlSnapshot(mode=mode, market_type=market_type, symbol=symbol, realized_pnl=realized, unrealized_pnl=unrealized))

    def _update_extremes(self, position: Position, price: float) -> None:
        if position.best_price is None:
            position.best_price = price
        if position.worst_price is None:
            position.worst_price = price
        if position.side == 'buy':
            position.best_price = max(position.best_price, price)
            position.worst_price = min(position.worst_price, price)
        else:
            position.best_price = min(position.best_price, price)
            position.worst_price = max(position.worst_price, price)

    def _lifecycle_event(self, position: Position, event_type: str, message: str, price: float | None = None, payload: dict | None = None) -> None:
        event = PositionLifecycleEvent(
            position_id=position.id,
            trade_id=position.trade_id,
            mode=position.mode,
            market_type=position.market_type,
            symbol=position.symbol,
            side=position.side,
            event_type=event_type,
            message=message,
            price=price,
            payload_json=json.dumps(payload) if payload is not None else None,
        )
        self.db.add(event)

    def _profit_factor(self, entries: list[JournalEntry]) -> float:
        gross_profit = sum(e.realized_pnl for e in entries if e.realized_pnl > 0)
        gross_loss = abs(sum(e.realized_pnl for e in entries if e.realized_pnl < 0))
        if gross_loss == 0:
            return round(gross_profit, 4) if gross_profit > 0 else 0.0
        return round(gross_profit / gross_loss, 4)

    def _max_drawdown(self, equity_curve: list[float]) -> float:
        if not equity_curve:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            dd = ((peak - value) / peak) * 100 if peak else 0.0
            max_dd = max(max_dd, dd)
        return max_dd

    def _bucket_sum(self, items: list[JournalEntry], key_func) -> dict[str, float]:
        out: dict[str, float] = {}
        for item in items:
            key = key_func(item)
            out[key] = round(out.get(key, 0.0) + item.realized_pnl, 8)
        return out

    def _plan_dict(self, plan: ExecutionPlan) -> dict:
        return {
            'entry_price': round(plan.entry_price, 8),
            'qty': round(plan.qty, 8),
            'stop_loss': round(plan.stop_loss, 8),
            'tp1': round(plan.tp1, 8),
            'tp2': round(plan.tp2, 8),
            'tp3': round(plan.tp3, 8),
            'risk_amount': round(plan.risk_amount, 8),
            'risk_per_unit': round(plan.risk_per_unit, 8),
            'working_balance': round(plan.working_balance, 8),
            'rationale': plan.rationale,
        }

    def _fmt(self, value: float) -> str:
        return f'{value:.8f}'.rstrip('0').rstrip('.')

    def _merge_order_payloads(self, *payloads: dict) -> list[dict]:
        merged: dict[str, dict] = {}
        for payload in payloads:
            for item in payload.get('result', {}).get('list', []) or []:
                key = str(item.get('orderId') or item.get('orderLinkId') or '')
                if not key:
                    continue
                merged[key] = item
        return list(merged.values())

    def _normalize_exchange_order_status(self, raw_status: str) -> str:
        status = (raw_status or '').lower()
        if status in {'new', 'created', 'untriggered', 'partiallyfilled', 'partially_filled'}:
            return 'open'
        if status in {'filled', 'deactivated'}:
            return 'filled'
        if status in {'cancelled', 'canceled'}:
            return 'cancelled'
        if status in {'rejected', 'rejected by system'}:
            return 'rejected'
        return status or 'unknown'

    def _sync_live_orders(self, exchange_orders: list[tuple[str, dict]]) -> dict:
        orders_checked = 0
        orders_updated = 0
        orders_filled = 0
        orders_cancelled = 0
        created_events = 0
        for market_type, item in exchange_orders:
            orders_checked += 1
            order_id = str(item.get('orderId') or '')
            link_id = str(item.get('orderLinkId') or '') or None
            local = None
            if order_id:
                local = self.db.scalar(select(Order).where(Order.bybit_order_id == order_id))
            if local is None and link_id:
                local = self.db.scalar(select(Order).where(Order.client_order_id == link_id))
            if local is None:
                local = Order(
                    mode='live',
                    market_type=market_type,
                    symbol=str(item.get('symbol') or ''),
                    side=str(item.get('side') or 'Buy').lower(),
                    order_type=str(item.get('orderType') or 'Market').lower(),
                    stage='entry',
                    status='submitted',
                    bybit_order_id=order_id or None,
                    client_order_id=link_id,
                    qty=float(item.get('qty') or item.get('orderQty') or 0.0),
                    filled_qty=float(item.get('cumExecQty') or 0.0),
                    price=float(item.get('price') or 0.0) if item.get('price') else None,
                    avg_fill_price=float(item.get('avgPrice') or 0.0) if item.get('avgPrice') else None,
                    stop_loss=float(item.get('stopLoss') or 0.0) if item.get('stopLoss') else None,
                    take_profit_3=float(item.get('takeProfit') or 0.0) if item.get('takeProfit') else None,
                    reduce_only=bool(item.get('reduceOnly') or False),
                    rationale='Adopted from exchange order stream',
                )
                self.db.add(local)
            prev_status = local.status
            normalized = self._normalize_exchange_order_status(str(item.get('orderStatus') or item.get('order_status') or 'unknown'))
            local.market_type = market_type
            local.symbol = str(item.get('symbol') or local.symbol)
            local.side = str(item.get('side') or local.side).lower()
            local.order_type = str(item.get('orderType') or local.order_type).lower()
            local.bybit_order_id = order_id or local.bybit_order_id
            local.client_order_id = link_id or local.client_order_id
            local.qty = float(item.get('qty') or item.get('orderQty') or local.qty or 0.0)
            local.filled_qty = float(item.get('cumExecQty') or item.get('cum_exec_qty') or local.filled_qty or 0.0)
            local.price = float(item.get('price') or 0.0) if item.get('price') else local.price
            local.avg_fill_price = float(item.get('avgPrice') or 0.0) if item.get('avgPrice') else local.avg_fill_price
            local.last_exchange_status = normalized
            local.last_exchange_update_at = self._utcnow_iso()
            local.status = normalized if normalized not in {'open', 'filled'} else ('submitted' if normalized == 'open' and local.status == 'submitted' else normalized)
            local.reduce_only = bool(item.get('reduceOnly') or local.reduce_only)
            self.db.add(local)
            if local.status != prev_status:
                orders_updated += 1
            if normalized == 'filled' and prev_status != 'filled':
                orders_filled += 1
                if local.stage == 'entry' and not self._trade_exists_for_order(local.id):
                    fill_price = local.avg_fill_price or local.price or 0.0
                    if fill_price > 0:
                        self._fill_pending_entry(local, fill_price)
                if local.stage != 'entry':
                    position = self._find_open_position(local.symbol, local.market_type, 'buy' if local.side == 'sell' else 'sell', mode='live')
                    if position is not None:
                        self._lifecycle_event(position, 'exchange-fill', f'Live close-stage order {local.stage} filled on exchange', price=local.avg_fill_price or local.price, payload={'order_id': local.id, 'bybit_order_id': local.bybit_order_id})
                        created_events += 1
            if normalized in {'cancelled', 'rejected'} and prev_status not in {'cancelled', 'rejected'}:
                orders_cancelled += 1
                position = self._find_open_position(local.symbol, local.market_type, local.side, mode='live')
                if position is not None:
                    self._lifecycle_event(position, 'order-cancelled', f'Exchange reported {normalized} for order stage {local.stage}', price=local.price, payload={'order_id': local.id})
                    created_events += 1
        self.db.flush()
        return {
            'orders_checked': orders_checked,
            'orders_updated': orders_updated,
            'orders_filled': orders_filled,
            'orders_cancelled': orders_cancelled,
            'created_events': created_events,
        }

    async def _sync_live_positions(self, positions_payload: dict) -> dict:
        items = positions_payload.get('result', {}).get('list', []) or []
        positions_seen = 0
        positions_adopted = 0
        positions_closed = 0
        protections_applied = 0
        created_events = 0
        active_keys: set[tuple[str, str]] = set()

        for item in items:
            size = abs(float(item.get('size') or 0.0))
            if size <= 0:
                continue
            positions_seen += 1
            symbol = str(item.get('symbol') or '')
            side = str(item.get('side') or 'Buy').lower()
            active_keys.add((symbol, side))
            avg_entry = float(item.get('avgPrice') or item.get('avgEntryPrice') or item.get('entryPrice') or 0.0)
            mark_price = float(item.get('markPrice') or avg_entry or 0.0)
            stop_loss = float(item.get('stopLoss') or 0.0) if item.get('stopLoss') else None
            take_profit = float(item.get('takeProfit') or 0.0) if item.get('takeProfit') else None
            position_idx = int(item.get('positionIdx') or 0)

            position = self._find_open_position(symbol, 'futures', side, mode='live')
            trade = self._find_open_trade(symbol, 'futures', side, mode='live')

            if trade is None:
                default_stop = stop_loss or self._default_stop(avg_entry, symbol, side)
                trade = Trade(
                    mode='live',
                    market_type='futures',
                    symbol=symbol,
                    direction=side,
                    status='open',
                    entry_price=avg_entry,
                    exit_price=None,
                    initial_qty=size,
                    remaining_qty=size,
                    stop_loss=default_stop,
                    take_profit_1=take_profit or self._target_from_r(avg_entry, default_stop, side, 1.5),
                    take_profit_2=self._target_from_r(avg_entry, default_stop, side, 3.0),
                    take_profit_3=take_profit or self._target_from_r(avg_entry, default_stop, side, 5.0),
                    realized_pnl=0.0,
                    unrealized_pnl=0.0,
                    notes='Adopted live trade from exchange state',
                )
                self.db.add(trade)
                self.db.flush()

            if position is None:
                position = Position(
                    trade_id=trade.id,
                    mode='live',
                    market_type='futures',
                    symbol=symbol,
                    side=side,
                    status='open',
                    size=size,
                    initial_size=size,
                    avg_entry_price=avg_entry,
                    mark_price=mark_price,
                    stop_loss=stop_loss or trade.stop_loss,
                    take_profit_1=trade.take_profit_1,
                    take_profit_2=trade.take_profit_2,
                    take_profit_3=trade.take_profit_3,
                    tp1_hit=False,
                    tp2_hit=False,
                    tp3_hit=False,
                    trailing_active=False,
                    trailing_anchor_price=None,
                    trailing_distance=None,
                    best_price=mark_price,
                    worst_price=mark_price,
                    entry_timeframe='reconciled-live',
                    position_idx=position_idx,
                    last_exchange_size=size,
                    last_live_sync_at=self._utcnow_iso(),
                    external_source='bybit',
                )
                self.db.add(position)
                self.db.flush()
                self._lifecycle_event(position, 'adopted-live-position', 'Live position adopted from exchange state.', price=mark_price, payload={'position_idx': position_idx})
                created_events += 1
                positions_adopted += 1

            position.trade_id = trade.id
            position.side = side
            position.size = size
            position.initial_size = max(position.initial_size, size)
            position.avg_entry_price = avg_entry
            position.mark_price = mark_price
            position.status = 'open'
            position.stop_loss = stop_loss or position.stop_loss
            position.best_price = mark_price if position.best_price is None else (max(position.best_price, mark_price) if side == 'buy' else min(position.best_price, mark_price))
            position.worst_price = mark_price if position.worst_price is None else (min(position.worst_price, mark_price) if side == 'buy' else max(position.worst_price, mark_price))
            position.position_idx = position_idx
            position.last_exchange_size = size
            position.last_live_sync_at = self._utcnow_iso()
            position.external_source = 'bybit'

            trade.remaining_qty = size
            trade.unrealized_pnl = self._calculate_pnl(side, avg_entry, mark_price, size)
            self.db.add(trade)
            self.db.add(position)

            if position.stop_loss and position.take_profit_3:
                try:
                    await self.bybit.set_trading_stop(
                        symbol=symbol,
                        stop_loss=position.stop_loss,
                        take_profit=position.take_profit_3,
                        position_idx=position.position_idx,
                    )
                    protections_applied += 1
                except Exception:
                    pass

        local_open_positions = list(self.db.scalars(select(Position).where(Position.mode == 'live', Position.market_type == 'futures', Position.status == 'open')).all())
        for position in local_open_positions:
            if (position.symbol, position.side) in active_keys:
                continue
            mark = position.mark_price or position.avg_entry_price
            self._close_remaining_position(position, mark, 'exchange-flat')
            position.last_exchange_size = 0.0
            position.last_live_sync_at = self._utcnow_iso()
            positions_closed += 1
            created_events += 1

        self.db.flush()
        return {
            'positions_seen': positions_seen,
            'positions_adopted': positions_adopted,
            'positions_closed': positions_closed,
            'protections_applied': protections_applied,
            'created_events': created_events,
        }

    def _trade_exists_for_order(self, order_id: int) -> bool:
        return self.db.scalar(select(Trade.id).where(Trade.order_id == order_id)) is not None

    def _find_open_trade(self, symbol: str, market_type: str, side: str, *, mode: str) -> Trade | None:
        return self.db.scalar(select(Trade).where(Trade.mode == mode, Trade.symbol == symbol, Trade.market_type == market_type, Trade.direction == side, Trade.status == 'open'))

    def _find_open_position(self, symbol: str, market_type: str, side: str, *, mode: str) -> Position | None:
        return self.db.scalar(select(Position).where(Position.mode == mode, Position.symbol == symbol, Position.market_type == market_type, Position.side == side, Position.status == 'open'))

    def _utcnow_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _run_async(self, awaitable):
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        raise TradingError('Live close must be called from a sync endpoint without an active event loop')
