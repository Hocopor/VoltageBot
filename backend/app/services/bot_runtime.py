from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.account import RuntimeSetting
from app.models.market import PairSelection
from app.models.system import BotConfig, BotRun, SystemEvent
from app.models.trade import Position
from app.schemas.trading import ExecutionRequest
from app.services.operations import OperationsService
from app.services.strategy_engine import StrategyEngineService
from app.services.trading import TradingError, TradingService


_bot_lock = asyncio.Lock()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BotRuntimeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.strategy = StrategyEngineService(db)
        self.trading = TradingService(db)

    def get_config(self) -> BotConfig:
        cfg = self.db.scalar(select(BotConfig).order_by(BotConfig.id.asc()))
        if cfg is None:
            cfg = BotConfig(
                enabled=False,
                auto_execute=True,
                live_execution_allowed=False,
                scan_interval_seconds=300,
                strategy_timeframe='1H',
                strategy_candles=240,
                risk_percent=0.01,
                max_new_positions_per_cycle=2,
                notes='Bot runtime config seeded automatically',
            )
            self.db.add(cfg)
            self.db.commit()
            self.db.refresh(cfg)
        return cfg

    def update_config(self, payload) -> BotConfig:
        cfg = self.get_config()
        cfg.enabled = payload.enabled
        cfg.auto_execute = payload.auto_execute
        cfg.live_execution_allowed = payload.live_execution_allowed
        cfg.scan_interval_seconds = payload.scan_interval_seconds
        cfg.strategy_timeframe = payload.strategy_timeframe
        cfg.strategy_candles = payload.strategy_candles
        cfg.risk_percent = payload.risk_percent
        cfg.max_new_positions_per_cycle = payload.max_new_positions_per_cycle
        cfg.notes = payload.notes
        self.db.add(cfg)
        self.db.commit()
        self.db.refresh(cfg)
        self.log_event('info', 'bot', 'config-updated', 'Bot runtime config updated', payload_json=json.dumps({
            'enabled': cfg.enabled,
            'auto_execute': cfg.auto_execute,
            'live_execution_allowed': cfg.live_execution_allowed,
            'scan_interval_seconds': cfg.scan_interval_seconds,
        }))
        return cfg

    def list_runs(self, limit: int = 30) -> list[BotRun]:
        stmt = select(BotRun).order_by(BotRun.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_events(self, limit: int = 100) -> list[SystemEvent]:
        stmt = select(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def log_event(
        self,
        level: str,
        source: str,
        event_type: str,
        message: str,
        *,
        related_symbol: str | None = None,
        related_market_type: str | None = None,
        bot_run_id: int | None = None,
        payload_json: str | None = None,
    ) -> SystemEvent:
        event = SystemEvent(
            level=level,
            source=source,
            event_type=event_type,
            message=message,
            related_symbol=related_symbol,
            related_market_type=related_market_type,
            bot_run_id=bot_run_id,
            payload_json=payload_json,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    async def run_cycle(self, trigger_type: str = 'manual', ignore_enabled_flag: bool = False) -> dict:
        async with _bot_lock:
            cfg = self.get_config()
            runtime = self._runtime_settings()
            ops_state = OperationsService(self.db).get_state()
            if ops_state.maintenance_mode:
                return {
                    'run_id': 0,
                    'mode': runtime.mode,
                    'status': 'skipped',
                    'scanned_pairs': 0,
                    'decisions_total': 0,
                    'allowed_total': 0,
                    'executed_total': 0,
                    'skipped_total': 0,
                    'errors_total': 0,
                    'summary': 'System is in maintenance mode; bot cycle skipped.',
                }
            if ops_state.trading_paused or ops_state.kill_switch_armed:
                return {
                    'run_id': 0,
                    'mode': runtime.mode,
                    'status': 'skipped',
                    'scanned_pairs': 0,
                    'decisions_total': 0,
                    'allowed_total': 0,
                    'executed_total': 0,
                    'skipped_total': 0,
                    'errors_total': 0,
                    'summary': 'Trading controls paused execution; bot cycle skipped.',
                }
            if not ignore_enabled_flag and not cfg.enabled:
                return {
                    'run_id': 0,
                    'mode': runtime.mode,
                    'status': 'skipped',
                    'scanned_pairs': 0,
                    'decisions_total': 0,
                    'allowed_total': 0,
                    'executed_total': 0,
                    'skipped_total': 0,
                    'errors_total': 0,
                    'summary': 'Bot is disabled. Enable it in runtime controls to allow automatic cycles.',
                }

            run = BotRun(
                mode=runtime.mode,
                status='running',
                trigger_type=trigger_type,
                started_at=utcnow_iso(),
                finished_at=None,
            )
            self.db.add(run)
            self.db.commit()
            self.db.refresh(run)

            cfg.last_cycle_started_at = run.started_at
            cfg.last_cycle_status = 'running'
            cfg.last_error = None
            self.db.add(cfg)
            self.db.commit()

            selected_pairs = self._selected_pairs(runtime)
            executed = 0
            allowed_total = 0
            decisions_total = 0
            skipped_total = 0
            errors_total = 0

            self.log_event('info', 'bot', 'cycle-started', f'Bot cycle started with {len(selected_pairs)} selected pairs', bot_run_id=run.id)

            for symbol, market_type in selected_pairs:
                if self._has_open_position(runtime.mode, symbol, market_type):
                    skipped_total += 1
                    self.log_event('info', 'bot', 'symbol-skipped-open-position', f'Skipped {symbol}: open position already exists', related_symbol=symbol, related_market_type=market_type, bot_run_id=run.id)
                    continue
                sides = ['buy'] if market_type == 'spot' else ['buy', 'sell']
                for side in sides:
                    try:
                        signal = await self.strategy.evaluate(
                            symbol,
                            market_type,
                            side,
                            timeframe=cfg.strategy_timeframe,
                            candles=cfg.strategy_candles,
                        )
                        decisions_total += 1
                        payload = json.dumps({
                            'allowed': signal.allowed,
                            'confidence': signal.confidence,
                            'scenario': signal.market_scenario,
                            'decision_id': signal.decision_id,
                        })
                        self.log_event(
                            'info',
                            'strategy',
                            'signal-evaluated',
                            f'{symbol} {market_type} {side}: allowed={signal.allowed} confidence={signal.confidence}',
                            related_symbol=symbol,
                            related_market_type=market_type,
                            bot_run_id=run.id,
                            payload_json=payload,
                        )
                        if not signal.allowed:
                            skipped_total += 1
                            continue
                        allowed_total += 1

                        can_execute = cfg.auto_execute and runtime.mode in {'paper', 'live'}
                        if runtime.mode == 'live' and not cfg.live_execution_allowed:
                            can_execute = False
                        if executed >= cfg.max_new_positions_per_cycle:
                            can_execute = False

                        if can_execute:
                            result = await self.trading.execute_trade(
                                ExecutionRequest(
                                    symbol=symbol,
                                    market_type=market_type,
                                    side=side,
                                    order_type='market',
                                    qty=None,
                                    price=None,
                                    stop_loss=signal.stop_loss,
                                    risk_percent=cfg.risk_percent,
                                    note=f'bot-cycle run={run.id} strategy={signal.market_scenario}',
                                )
                            )
                            executed += 1
                            self.log_event(
                                'info',
                                'trade',
                                'trade-executed',
                                f'Executed {runtime.mode} {market_type} {symbol} {side} via bot cycle',
                                related_symbol=symbol,
                                related_market_type=market_type,
                                bot_run_id=run.id,
                                payload_json=json.dumps(result),
                            )
                        else:
                            skipped_total += 1
                            reason = 'execution disabled by config or run limits'
                            self.log_event(
                                'warning',
                                'bot',
                                'signal-not-executed',
                                f'{symbol} {side} allowed but not executed: {reason}',
                                related_symbol=symbol,
                                related_market_type=market_type,
                                bot_run_id=run.id,
                            )
                    except Exception as exc:
                        errors_total += 1
                        self.log_event(
                            'error',
                            'bot',
                            'cycle-error',
                            f'Error while processing {symbol} {market_type}: {exc}',
                            related_symbol=symbol,
                            related_market_type=market_type,
                            bot_run_id=run.id,
                        )

            run.scanned_pairs = len(selected_pairs)
            run.decisions_total = decisions_total
            run.allowed_total = allowed_total
            run.executed_total = executed
            run.skipped_total = skipped_total
            run.errors_total = errors_total
            run.status = 'completed' if errors_total == 0 else 'completed-with-errors'
            run.finished_at = utcnow_iso()
            run.summary = (
                f'Scanned={run.scanned_pairs}; decisions={decisions_total}; allowed={allowed_total}; '
                f'executed={executed}; skipped={skipped_total}; errors={errors_total}; mode={runtime.mode}'
            )
            self.db.add(run)

            cfg.last_cycle_finished_at = run.finished_at
            cfg.last_cycle_status = run.status
            cfg.last_cycle_summary = run.summary
            cfg.last_error = None if errors_total == 0 else f'{errors_total} cycle errors logged'
            self.db.add(cfg)
            self.db.commit()

            self.log_event('info', 'bot', 'cycle-finished', run.summary, bot_run_id=run.id)
            return {
                'run_id': run.id,
                'mode': runtime.mode,
                'status': run.status,
                'scanned_pairs': run.scanned_pairs,
                'decisions_total': run.decisions_total,
                'allowed_total': run.allowed_total,
                'executed_total': run.executed_total,
                'skipped_total': run.skipped_total,
                'errors_total': run.errors_total,
                'summary': run.summary,
            }

    def _runtime_settings(self) -> RuntimeSetting:
        runtime = self.db.scalar(select(RuntimeSetting).order_by(RuntimeSetting.id.asc()))
        if runtime is None:
            runtime = RuntimeSetting()
            self.db.add(runtime)
            self.db.commit()
            self.db.refresh(runtime)
        return runtime

    def _selected_pairs(self, runtime: RuntimeSetting) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        if runtime.spot_enabled:
            spot = self.db.scalars(select(PairSelection).where(PairSelection.market_type == 'spot', PairSelection.selected.is_(True)).order_by(PairSelection.symbol.asc())).all()
            pairs.extend((item.symbol, 'spot') for item in spot)
        if runtime.futures_enabled:
            futures = self.db.scalars(select(PairSelection).where(PairSelection.market_type == 'futures', PairSelection.selected.is_(True)).order_by(PairSelection.symbol.asc())).all()
            pairs.extend((item.symbol, 'futures') for item in futures)
        if pairs:
            return pairs
        fallback = []
        if runtime.spot_enabled:
            fallback.append(('BTCUSDT', 'spot'))
        if runtime.futures_enabled:
            fallback.append(('BTCUSDT', 'futures'))
        return fallback

    def _has_open_position(self, mode: str, symbol: str, market_type: str) -> bool:
        stmt = select(Position).where(Position.mode == mode, Position.symbol == symbol, Position.market_type == market_type, Position.status == 'open')
        return self.db.scalar(stmt) is not None


async def bot_background_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            with SessionLocal() as db:
                OperationsService(db).heartbeat('bot-loop')
                service = BotRuntimeService(db)
                cfg = service.get_config()
                if cfg.enabled:
                    due = True
                    if cfg.last_cycle_started_at:
                        try:
                            last = datetime.fromisoformat(cfg.last_cycle_started_at)
                            due = (datetime.now(timezone.utc) - last).total_seconds() >= cfg.scan_interval_seconds
                        except Exception:
                            due = True
                    if due:
                        await service.run_cycle(trigger_type='auto', ignore_enabled_flag=False)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            continue
