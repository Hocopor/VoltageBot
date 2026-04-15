from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.account import ExchangeBalance
from app.models.system import BotRun, FlattenRun, ReconcileRun, RecoveryRun, SystemEvent, SystemState
from app.models.trade import Order, Position, PositionLifecycleEvent, Trade
from app.services.bybit import BybitService
from app.services.trading import TradingService


class OperationsError(RuntimeError):
    pass


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OperationsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.bybit = BybitService()

    def get_state(self) -> SystemState:
        state = self.db.scalar(select(SystemState).order_by(SystemState.id.asc()))
        if state is None:
            state = SystemState(
                maintenance_mode=False,
                trading_paused=False,
                kill_switch_armed=False,
                boot_count=0,
                last_live_sync_status='never',
                last_live_sync_message='System state initialized',
                recovery_runs_count=0,
            )
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
        return state

    def update_controls(self, *, maintenance_mode: bool, trading_paused: bool, kill_switch_armed: bool) -> SystemState:
        state = self.get_state()
        state.maintenance_mode = maintenance_mode
        state.trading_paused = trading_paused
        state.kill_switch_armed = kill_switch_armed
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        self.log_event(
            'warning' if (trading_paused or kill_switch_armed or maintenance_mode) else 'info',
            'ops',
            'controls-updated',
            'Operations controls updated',
            payload_json=json.dumps(
                {
                    'maintenance_mode': maintenance_mode,
                    'trading_paused': trading_paused,
                    'kill_switch_armed': kill_switch_armed,
                }
            ),
        )
        return state

    def mark_startup(self) -> SystemState:
        state = self.get_state()
        state.boot_count += 1
        state.last_startup_at = utcnow_iso()
        self.db.add(state)
        self.db.commit()
        self.log_event('info', 'system', 'startup', 'Application startup completed')
        self.run_recovery_scan(startup_context='automatic')
        return state

    def mark_shutdown(self) -> SystemState:
        state = self.get_state()
        state.last_shutdown_at = utcnow_iso()
        self.db.add(state)
        self.db.commit()
        self.log_event('warning', 'system', 'shutdown', 'Application shutdown completed')
        return state

    def heartbeat(self, component: str) -> SystemState:
        state = self.get_state()
        if component == 'bot-loop':
            state.last_bot_heartbeat_at = utcnow_iso()
        self.db.add(state)
        self.db.commit()
        return state

    def system_health(self) -> dict:
        state = self.get_state()
        open_positions = self.db.scalar(select(func.count()).select_from(Position).where(Position.status == 'open'))
        open_live_positions = self.db.scalar(select(func.count()).select_from(Position).where(Position.status == 'open', Position.mode == 'live'))
        open_paper_positions = self.db.scalar(select(func.count()).select_from(Position).where(Position.status == 'open', Position.mode == 'paper'))
        return {
            'maintenance_mode': state.maintenance_mode,
            'trading_paused': state.trading_paused,
            'kill_switch_armed': state.kill_switch_armed,
            'boot_count': state.boot_count,
            'last_startup_at': state.last_startup_at,
            'last_shutdown_at': state.last_shutdown_at,
            'last_bot_heartbeat_at': state.last_bot_heartbeat_at,
            'last_reconcile_at': state.last_reconcile_at,
            'last_lifecycle_sync_at': state.last_lifecycle_sync_at,
            'last_live_sync_status': state.last_live_sync_status,
            'last_live_sync_message': state.last_live_sync_message,
            'recovery_runs_count': state.recovery_runs_count,
            'last_recovery_at': state.last_recovery_at,
            'last_flatten_at': state.last_flatten_at,
            'last_flatten_status': state.last_flatten_status,
            'last_flatten_message': state.last_flatten_message,
            'open_positions': open_positions or 0,
            'open_live_positions': open_live_positions or 0,
            'open_paper_positions': open_paper_positions or 0,
        }

    async def reconcile_live_account(self) -> dict:
        run = ReconcileRun(source='live', status='running', started_at=utcnow_iso())
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            balances_payload = await self.bybit.get_wallet_balances()
            spot_orders_payload = await self.bybit.get_open_orders('spot', open_only=0)
            futures_orders_payload = await self.bybit.get_open_orders('futures', open_only=0)
            positions_payload = await self.bybit.get_positions()

            balances_count = self._sync_balances(balances_payload)
            orders_count = self._sync_orders(spot_orders_payload, 'spot') + self._sync_orders(futures_orders_payload, 'futures')
            positions_count, closed_local_positions = self._sync_positions(positions_payload)

            run.status = 'completed'
            run.balances_synced = balances_count
            run.orders_seen = orders_count
            run.positions_seen = positions_count
            run.closed_local_positions = closed_local_positions
            run.finished_at = utcnow_iso()
            run.summary = f'Balances={balances_count}; orders={orders_count}; positions={positions_count}; closed_local_positions={closed_local_positions}'
            self.db.add(run)

            state = self.get_state()
            state.last_reconcile_at = run.finished_at
            state.last_live_sync_status = 'completed'
            state.last_live_sync_message = run.summary
            self.db.add(state)
            self.db.commit()
            self.log_event('info', 'ops', 'live-reconcile-completed', run.summary, payload_json=json.dumps({'run_id': run.id}))
            return {
                'id': run.id,
                'source': run.source,
                'status': run.status,
                'balances_synced': run.balances_synced,
                'orders_seen': run.orders_seen,
                'positions_seen': run.positions_seen,
                'closed_local_positions': run.closed_local_positions,
                'summary': run.summary or '',
                'started_at': run.started_at,
                'finished_at': run.finished_at,
                'created_at': run.created_at,
            }
        except Exception as exc:
            run.status = 'failed'
            run.finished_at = utcnow_iso()
            run.summary = str(exc)
            self.db.add(run)
            state = self.get_state()
            state.last_reconcile_at = run.finished_at
            state.last_live_sync_status = 'failed'
            state.last_live_sync_message = str(exc)
            self.db.add(state)
            self.db.commit()
            self.log_event('error', 'ops', 'live-reconcile-failed', str(exc), payload_json=json.dumps({'run_id': run.id}))
            raise OperationsError(str(exc)) from exc

    def list_reconcile_runs(self, limit: int = 20) -> list[ReconcileRun]:
        stmt = select(ReconcileRun).order_by(ReconcileRun.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def run_recovery_scan(self, startup_context: str = 'manual') -> dict:
        run = RecoveryRun(startup_context=startup_context, status='running', started_at=utcnow_iso())
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        stale_bot_runs = list(self.db.scalars(select(BotRun).where(BotRun.status == 'running')).all())
        recovered_positions = list(self.db.scalars(select(Position).where(Position.status == 'open')).all())

        stale_count = 0
        for bot_run in stale_bot_runs:
            bot_run.status = 'interrupted'
            bot_run.finished_at = utcnow_iso()
            bot_run.summary = (bot_run.summary or 'Interrupted by recovery scan').strip()
            self.db.add(bot_run)
            stale_count += 1

        recovered_count = 0
        for position in recovered_positions:
            event = PositionLifecycleEvent(
                position_id=position.id,
                trade_id=position.trade_id,
                mode=position.mode,
                market_type=position.market_type,
                symbol=position.symbol,
                side=position.side,
                event_type='recovery-scan',
                message='Recovery scan inspected open position after startup/manual recovery.',
                price=position.mark_price,
                payload_json=json.dumps({'startup_context': startup_context}),
            )
            self.db.add(event)
            recovered_count += 1

        run.status = 'completed'
        run.stale_bot_runs = stale_count
        run.recovered_positions = recovered_count
        run.summary = f'Stale bot runs={stale_count}; inspected open positions={recovered_count}'
        run.finished_at = utcnow_iso()
        self.db.add(run)

        state = self.get_state()
        state.recovery_runs_count += 1
        state.last_recovery_at = run.finished_at
        self.db.add(state)
        self.db.commit()
        self.log_event('warning', 'ops', 'recovery-scan-completed', run.summary, payload_json=json.dumps({'recovery_run_id': run.id, 'startup_context': startup_context}))
        return {
            'id': run.id,
            'startup_context': run.startup_context,
            'status': run.status,
            'stale_bot_runs': run.stale_bot_runs,
            'recovered_positions': run.recovered_positions,
            'summary': run.summary or '',
            'started_at': run.started_at,
            'finished_at': run.finished_at,
            'created_at': run.created_at,
        }

    def list_recovery_runs(self, limit: int = 20) -> list[RecoveryRun]:
        stmt = select(RecoveryRun).order_by(RecoveryRun.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def flatten_paper_positions(self) -> dict:
        positions = list(self.db.scalars(select(Position).where(Position.mode == 'paper', Position.status == 'open')).all())
        trading = TradingService(self.db)
        closed = 0
        for position in positions:
            exit_price = position.mark_price or position.avg_entry_price
            trading.close_position(position.id, exit_price=exit_price, reason='ops-flatten-paper')
            closed += 1
        self.log_event('warning', 'ops', 'flatten-paper', f'Flattened {closed} open paper positions')
        return {'closed_positions': closed, 'status': 'completed'}

    async def flatten_live_positions(self, *, arm_kill_switch: bool = False) -> dict:
        run = FlattenRun(mode='live', scope='all', status='running', started_at=utcnow_iso())
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        state = self.get_state()
        try:
            if arm_kill_switch:
                state.kill_switch_armed = True
                state.trading_paused = True
                self.db.add(state)
                self.db.commit()

            cancel_spot = await self.bybit.cancel_all_orders('spot')
            cancel_futures = await self.bybit.cancel_all_orders('futures')
            positions_payload = await self.bybit.get_positions()
            items = positions_payload.get('result', {}).get('list', []) or []

            orders_cancelled = len(cancel_spot.get('result', {}).get('list', []) or []) + len(cancel_futures.get('result', {}).get('list', []) or [])
            submitted = 0
            touched_symbols: set[str] = set()
            trading = TradingService(self.db)

            for item in items:
                size = abs(float(item.get('size') or 0.0))
                if size <= 0:
                    continue
                symbol = str(item.get('symbol') or '')
                side = str(item.get('side') or 'Buy').lower()
                position_idx = int(item.get('positionIdx') or 0)
                touched_symbols.add(symbol)
                client_order_id = f'voltage-flatten-{uuid4().hex[:18]}'
                response = await self.bybit.close_linear_position(symbol=symbol, side=side, qty=size, position_idx=position_idx, order_link_id=client_order_id)
                order = Order(
                    mode='live',
                    market_type='futures',
                    symbol=symbol,
                    side='sell' if side == 'buy' else 'buy',
                    order_type='market',
                    stage='emergency-flatten',
                    status='submitted',
                    bybit_order_id=response.get('result', {}).get('orderId'),
                    client_order_id=client_order_id,
                    qty=size,
                    filled_qty=0.0,
                    price=None,
                    avg_fill_price=None,
                    reduce_only=True,
                    last_exchange_status='submitted',
                    last_exchange_update_at=utcnow_iso(),
                    rationale='Emergency live flatten submitted by operations service',
                )
                self.db.add(order)
                position = self.db.scalar(select(Position).where(Position.mode == 'live', Position.symbol == symbol, Position.market_type == 'futures', Position.side == side, Position.status == 'open'))
                if position is not None:
                    trading._lifecycle_event(position, 'flatten-submitted', 'Emergency live flatten order submitted', price=position.mark_price, payload={'client_order_id': client_order_id, 'exchange_order_id': order.bybit_order_id})
                submitted += 1

            run.status = 'completed'
            run.orders_cancelled = orders_cancelled
            run.close_orders_submitted = submitted
            run.symbols_touched = len(touched_symbols)
            run.finished_at = utcnow_iso()
            run.summary = f'cancelled={orders_cancelled}; close_orders_submitted={submitted}; symbols={len(touched_symbols)}'
            self.db.add(run)

            state.last_flatten_at = run.finished_at
            state.last_flatten_status = 'completed'
            state.last_flatten_message = run.summary
            self.db.add(state)
            self.db.commit()
            self.log_event('warning', 'ops', 'flatten-live', run.summary, payload_json=json.dumps({'run_id': run.id, 'arm_kill_switch': arm_kill_switch}))
            return {
                'run_id': run.id,
                'mode': run.mode,
                'scope': run.scope,
                'status': run.status,
                'orders_cancelled': run.orders_cancelled,
                'close_orders_submitted': run.close_orders_submitted,
                'symbols_touched': run.symbols_touched,
                'summary': run.summary,
            }
        except Exception as exc:
            run.status = 'failed'
            run.finished_at = utcnow_iso()
            run.summary = str(exc)
            self.db.add(run)
            state.last_flatten_at = run.finished_at
            state.last_flatten_status = 'failed'
            state.last_flatten_message = str(exc)
            self.db.add(state)
            self.db.commit()
            self.log_event('error', 'ops', 'flatten-live-failed', str(exc), payload_json=json.dumps({'run_id': run.id, 'arm_kill_switch': arm_kill_switch}))
            raise OperationsError(str(exc)) from exc

    def list_flatten_runs(self, limit: int = 20) -> list[FlattenRun]:
        stmt = select(FlattenRun).order_by(FlattenRun.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def _sync_balances(self, payload: dict) -> int:
        accounts = payload.get('result', {}).get('list', [])
        rows: list[ExchangeBalance] = []
        for account in accounts:
            for coin in account.get('coin', []):
                usd_value = float(coin.get('usdValue') or 0.0)
                wallet_balance = float(coin.get('walletBalance') or 0.0)
                available = float(coin.get('availableToWithdraw') or coin.get('walletBalance') or 0.0)
                if wallet_balance == 0 and usd_value == 0:
                    continue
                rows.append(ExchangeBalance(balance_scope='wallet', market_type='wallet', asset=coin.get('coin', ''), total=wallet_balance, available=available, usd_value=usd_value))
        self.db.execute(delete(ExchangeBalance))
        for row in rows:
            self.db.add(row)
        self.db.commit()
        return len(rows)

    def _sync_orders(self, payload: dict, market_type: str) -> int:
        items = payload.get('result', {}).get('list', []) or []
        count = 0
        for item in items:
            bybit_order_id = str(item.get('orderId') or '')
            if not bybit_order_id:
                continue
            existing = self.db.scalar(select(Order).where(Order.bybit_order_id == bybit_order_id))
            side = str(item.get('side') or 'Buy').lower()
            order_type = str(item.get('orderType') or 'Market').lower()
            status = str(item.get('orderStatus') or item.get('order_status') or 'unknown').lower()
            qty = float(item.get('qty') or item.get('orderQty') or 0.0)
            cum_exec_qty = float(item.get('cumExecQty') or item.get('cum_exec_qty') or 0.0)
            price = float(item.get('price') or 0.0) if item.get('price') else None
            avg_fill_price = float(item.get('avgPrice') or 0.0) if item.get('avgPrice') else None
            target = existing or Order(
                mode='live',
                market_type=market_type,
                symbol=str(item.get('symbol') or ''),
                side=side,
                order_type=order_type,
                stage='entry',
                status=status,
                qty=qty,
                filled_qty=cum_exec_qty,
                price=price,
                avg_fill_price=avg_fill_price,
                bybit_order_id=bybit_order_id,
                client_order_id=str(item.get('orderLinkId') or '') or None,
                last_exchange_status=status,
                last_exchange_update_at=utcnow_iso(),
                rationale='Reconciled from Bybit live account',
            )
            target.mode = 'live'
            target.market_type = market_type
            target.symbol = str(item.get('symbol') or target.symbol)
            target.side = side
            target.order_type = order_type
            target.status = status
            target.qty = qty
            target.filled_qty = cum_exec_qty
            target.price = price
            target.avg_fill_price = avg_fill_price
            target.bybit_order_id = bybit_order_id
            target.client_order_id = str(item.get('orderLinkId') or '') or target.client_order_id
            target.last_exchange_status = status
            target.last_exchange_update_at = utcnow_iso()
            self.db.add(target)
            count += 1
        self.db.commit()
        return count

    def _sync_positions(self, payload: dict) -> tuple[int, int]:
        items = payload.get('result', {}).get('list', []) or []
        active_symbols: set[str] = set()
        seen = 0
        for item in items:
            size = abs(float(item.get('size') or 0.0))
            if size <= 0:
                continue
            seen += 1
            symbol = str(item.get('symbol') or '')
            active_symbols.add(symbol)
            side = str(item.get('side') or 'Buy').lower()
            avg_entry = float(item.get('avgPrice') or item.get('avgEntryPrice') or item.get('entryPrice') or 0.0)
            mark_price = float(item.get('markPrice') or avg_entry or 0.0)
            stop_loss = float(item.get('stopLoss') or 0.0) if item.get('stopLoss') else None
            take_profit = float(item.get('takeProfit') or 0.0) if item.get('takeProfit') else None
            position_idx = int(item.get('positionIdx') or 0)

            trade = self.db.scalar(select(Trade).where(Trade.mode == 'live', Trade.symbol == symbol, Trade.market_type == 'futures', Trade.status == 'open'))
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
                    take_profit_1=take_profit or self._default_target(avg_entry, default_stop, side, 1.5),
                    take_profit_2=self._default_target(avg_entry, default_stop, side, 3.0),
                    take_profit_3=take_profit or self._default_target(avg_entry, default_stop, side, 5.0),
                    realized_pnl=0.0,
                    unrealized_pnl=0.0,
                    notes='Reconciled live trade from Bybit',
                )
                self.db.add(trade)
                self.db.flush()

            position = self.db.scalar(select(Position).where(Position.mode == 'live', Position.symbol == symbol, Position.market_type == 'futures', Position.status == 'open'))
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
                    last_live_sync_at=utcnow_iso(),
                    external_source='bybit',
                )
                self.db.add(position)
                self.db.flush()
                self.db.add(
                    PositionLifecycleEvent(
                        position_id=position.id,
                        trade_id=trade.id,
                        mode='live',
                        market_type='futures',
                        symbol=symbol,
                        side=side,
                        event_type='reconciled-open',
                        message='Live position reconciled from exchange state.',
                        price=mark_price,
                    )
                )
            position.trade_id = trade.id
            position.side = side
            position.size = size
            position.initial_size = max(position.initial_size, size)
            position.avg_entry_price = avg_entry
            position.mark_price = mark_price
            position.status = 'open'
            position.stop_loss = stop_loss or position.stop_loss
            position.position_idx = position_idx
            position.last_exchange_size = size
            position.last_live_sync_at = utcnow_iso()
            position.external_source = 'bybit'
            position.best_price = min(position.best_price, mark_price) if side == 'sell' and position.best_price is not None else max(position.best_price or mark_price, mark_price) if side == 'buy' else position.best_price
            position.worst_price = max(position.worst_price or mark_price, mark_price) if side == 'sell' else min(position.worst_price or mark_price, mark_price)
            trade.remaining_qty = size
            trade.unrealized_pnl = self._calculate_pnl(side, avg_entry, mark_price, size)
            self.db.add(trade)
            self.db.add(position)
        local_open_positions = list(self.db.scalars(select(Position).where(Position.mode == 'live', Position.market_type == 'futures', Position.status == 'open')).all())
        closed_local_positions = 0
        for position in local_open_positions:
            if position.symbol in active_symbols:
                continue
            position.status = 'closed'
            position.size = 0.0
            position.last_exchange_size = 0.0
            position.last_live_sync_at = utcnow_iso()
            trade = self.db.get(Trade, position.trade_id) if position.trade_id else None
            if trade and trade.status == 'open':
                trade.status = 'closed'
                trade.exit_price = position.mark_price or trade.entry_price
                trade.remaining_qty = 0.0
                trade.unrealized_pnl = 0.0
                self.db.add(trade)
            self.db.add(position)
            self.db.add(
                PositionLifecycleEvent(
                    position_id=position.id,
                    trade_id=position.trade_id,
                    mode=position.mode,
                    market_type=position.market_type,
                    symbol=position.symbol,
                    side=position.side,
                    event_type='reconciled-closed',
                    message='Local live position closed because it no longer exists on exchange.',
                    price=position.mark_price,
                )
            )
            closed_local_positions += 1
        self.db.commit()
        return seen, closed_local_positions

    def _default_stop(self, entry_price: float, symbol: str, side: str) -> float:
        is_major = symbol.startswith('BTC') or symbol.startswith('ETH')
        pct = 0.06 if is_major else 0.10
        return entry_price * (1 - pct) if side == 'buy' else entry_price * (1 + pct)

    def _default_target(self, entry: float, stop: float, side: str, multiple: float) -> float:
        distance = abs(entry - stop) * multiple
        return entry + distance if side == 'buy' else entry - distance

    def _calculate_pnl(self, side: str, entry: float, mark: float, qty: float) -> float:
        return round((mark - entry) * qty, 8) if side == 'buy' else round((entry - mark) * qty, 8)

    def log_event(self, level: str, source: str, event_type: str, message: str, payload_json: str | None = None) -> SystemEvent:
        event = SystemEvent(level=level, source=source, event_type=event_type, message=message, payload_json=payload_json)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
