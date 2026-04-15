from __future__ import annotations

import json
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal import JournalEntry
from app.models.strategy import BacktestRun, BacktestTrade
from app.services.market_data import MarketDataService
from app.services.strategy_engine import StrategyEngineService


class BacktestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.market_data = MarketDataService()
        self.strategy_engine = StrategyEngineService(db)

    async def run(self, symbol: str, market_type: str, timeframe: str, candles: int, start_balance: float, side_policy: str) -> BacktestRun:
        series = await self.market_data.historical_candles(symbol, market_type, timeframe=timeframe, limit=candles)
        directions = ['buy']
        if market_type == 'futures' and side_policy in {'short_only', 'both'}:
            directions = ['sell'] if side_policy == 'short_only' else ['buy', 'sell']

        run = BacktestRun(
            mode='historical',
            market_type=market_type,
            symbol=symbol,
            timeframe=timeframe,
            candles=candles,
            start_balance=start_balance,
            end_balance=start_balance,
            notes=f'Backtest generated from {len(series)} candles with side policy {side_policy}.',
        )
        self.db.add(run)
        self.db.flush()

        closed: list[BacktestTrade] = []
        equity = start_balance
        peak = start_balance
        equity_curve = [equity]
        rr_values: list[float] = []

        for direction in directions:
            for idx in range(55, len(series) - 6, 18):
                window = series[: idx + 1]
                local_signal = await self.strategy_engine.evaluate(
                    symbol,
                    market_type,
                    direction,
                    timeframe=timeframe,
                    candles=max(120, min(candles, len(window))),
                    series=window,
                )
                if not local_signal.allowed:
                    continue
                entry = series[idx].close
                stop = local_signal.stop_loss
                tp1 = local_signal.take_profit_1
                tp2 = local_signal.take_profit_2
                tp3 = local_signal.take_profit_3
                risk_per_unit = abs(entry - stop)
                if risk_per_unit <= 0:
                    continue
                risk_budget = min(equity * 0.02, equity * 0.03)
                qty = max(0.0001, round(risk_budget / risk_per_unit, 8))
                exit_index, exit_price, close_reason, realized = self._simulate_trade(series, idx, direction, qty, entry, stop, tp1, tp2, tp3)
                rr = realized / max(risk_per_unit * qty, 1e-9)
                rr_values.append(rr)
                trade = BacktestTrade(
                    run_id=run.id,
                    symbol=symbol,
                    market_type=market_type,
                    direction=direction,
                    entry_index=idx,
                    exit_index=exit_index,
                    entry_price=entry,
                    exit_price=exit_price,
                    quantity=qty,
                    stop_loss=stop,
                    take_profit_1=tp1,
                    take_profit_2=tp2,
                    take_profit_3=tp3,
                    realized_pnl=realized,
                    rr_multiple=rr,
                    close_reason=close_reason,
                    decision_id=local_signal.decision_id,
                    notes=f'Strategy scenario={local_signal.market_scenario}; confidence={local_signal.confidence}',
                )
                self.db.add(trade)
                self.db.flush()
                chart_points = json.dumps(
                    {
                        'entry_index': idx,
                        'exit_index': exit_index,
                        'entry_price': entry,
                        'exit_price': exit_price,
                        'stop_loss': stop,
                        'tp1': tp1,
                        'tp2': tp2,
                        'tp3': tp3,
                    }
                )
                self.db.add(
                    JournalEntry(
                        backtest_run_id=run.id,
                        mode='historical',
                        market_type=market_type,
                        symbol=symbol,
                        direction=direction,
                        quantity=qty,
                        entry_price=entry,
                        exit_price=exit_price,
                        stop_loss=stop,
                        take_profit_1=tp1,
                        take_profit_2=tp2,
                        take_profit_3=tp3,
                        realized_pnl=realized,
                        entry_index=idx,
                        exit_index=exit_index,
                        chart_points=chart_points,
                        tags='historical,voltage,auto-generated',
                        ai_review_status='generated',
                        ai_review_text=(
                            f'Historical review: scenario={local_signal.market_scenario}, confidence={local_signal.confidence}. '
                            f'Close reason={close_reason}, realized PnL={realized:.4f}, RR={rr:.2f}.'
                        ),
                        close_reason=close_reason,
                        hold_minutes=float(max(exit_index - idx, 0)),
                        best_price=max(entry, exit_price) if direction == 'buy' else min(entry, exit_price),
                        worst_price=min(entry, exit_price) if direction == 'buy' else max(entry, exit_price),
                        mfe_pnl=max(realized, 0.0),
                        mae_pnl=min(realized, 0.0),
                        strategy_scenario=local_signal.market_scenario,
                        compliance_score=1.0,
                        review_summary=f'Historical trade closed by {close_reason} with RR {rr:.2f}.',
                    )
                )
                equity += realized
                peak = max(peak, equity)
                equity_curve.append(round(equity, 8))
                closed.append(trade)

        run.total_trades = len(closed)
        run.closed_trades = len(closed)
        run.wins = sum(1 for t in closed if t.realized_pnl > 0)
        run.losses = sum(1 for t in closed if t.realized_pnl < 0)
        run.win_rate = round((run.wins / len(closed)) * 100, 2) if closed else 0.0
        run.realized_pnl = round(sum(t.realized_pnl for t in closed), 8)
        run.end_balance = round(start_balance + run.realized_pnl, 8)
        run.profit_factor = self._profit_factor(closed)
        run.average_rr = round(mean(rr_values), 4) if rr_values else 0.0
        run.max_drawdown = round(self._max_drawdown(equity_curve), 4)
        run.target_metrics_met = (
            run.win_rate >= 58 and run.profit_factor >= 2.2 and run.max_drawdown <= 18 and run.average_rr >= 2.8
        )
        run.notes = (
            f'Win rate {run.win_rate:.2f}%, PF {run.profit_factor:.2f}, MDD {run.max_drawdown:.2f}%, '
            f'Avg RR {run.average_rr:.2f}. Target metrics met={run.target_metrics_met}.'
        )
        self.db.commit()
        return run

    def list_runs(self) -> list[BacktestRun]:
        return list(self.db.scalars(select(BacktestRun).order_by(BacktestRun.created_at.desc())).all())

    def get_run(self, run_id: int) -> tuple[BacktestRun | None, list[BacktestTrade]]:
        run = self.db.get(BacktestRun, run_id)
        trades = list(self.db.scalars(select(BacktestTrade).where(BacktestTrade.run_id == run_id).order_by(BacktestTrade.id.asc())).all())
        return run, trades

    def _simulate_trade(self, series, entry_index: int, direction: str, qty: float, entry: float, stop: float, tp1: float, tp2: float, tp3: float):
        remaining = qty
        realized = 0.0
        trailing_active = False
        trailing_anchor = entry
        trailing_distance = abs(entry - stop)
        for candle in series[entry_index + 1 :]:
            current = candle.close
            high = candle.high
            low = candle.low
            if direction == 'buy':
                if low <= stop:
                    realized += (stop - entry) * remaining
                    return candle.index, stop, 'stop-loss', round(realized, 8)
                if remaining > qty * 0.60 and high >= tp1:
                    partial = qty * 0.40
                    realized += (tp1 - entry) * partial
                    remaining -= partial
                    stop = entry
                if remaining > qty * 0.30 and high >= tp2:
                    partial = qty * 0.30
                    realized += (tp2 - entry) * partial
                    remaining -= partial
                if high >= tp3:
                    trailing_active = True
                    trailing_anchor = max(trailing_anchor, high)
                if trailing_active:
                    trailing_anchor = max(trailing_anchor, high)
                    if low <= trailing_anchor - trailing_distance:
                        exit_price = trailing_anchor - trailing_distance
                        realized += (exit_price - entry) * remaining
                        return candle.index, exit_price, 'trailing-stop', round(realized, 8)
            else:
                if high >= stop:
                    realized += (entry - stop) * remaining
                    return candle.index, stop, 'stop-loss', round(realized, 8)
                if remaining > qty * 0.60 and low <= tp1:
                    partial = qty * 0.40
                    realized += (entry - tp1) * partial
                    remaining -= partial
                    stop = entry
                if remaining > qty * 0.30 and low <= tp2:
                    partial = qty * 0.30
                    realized += (entry - tp2) * partial
                    remaining -= partial
                if low <= tp3:
                    trailing_active = True
                    trailing_anchor = min(trailing_anchor, low)
                if trailing_active:
                    trailing_anchor = min(trailing_anchor, low)
                    if high >= trailing_anchor + trailing_distance:
                        exit_price = trailing_anchor + trailing_distance
                        realized += (entry - exit_price) * remaining
                        return candle.index, exit_price, 'trailing-stop', round(realized, 8)
        final_price = series[-1].close
        if direction == 'buy':
            realized += (final_price - entry) * remaining
        else:
            realized += (entry - final_price) * remaining
        return series[-1].index, final_price, 'end-of-series', round(realized, 8)

    def _profit_factor(self, trades: list[BacktestTrade]) -> float:
        gross_profit = sum(t.realized_pnl for t in trades if t.realized_pnl > 0)
        gross_loss = abs(sum(t.realized_pnl for t in trades if t.realized_pnl < 0))
        if gross_loss == 0:
            return round(gross_profit, 4) if gross_profit > 0 else 0.0
        return round(gross_profit / gross_loss, 4)

    def _max_drawdown(self, equity_curve: list[float]) -> float:
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            dd = ((peak - value) / peak) * 100 if peak else 0.0
            max_dd = max(max_dd, dd)
        return max_dd
