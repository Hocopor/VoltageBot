from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import TimestampMixin


class BotConfig(TimestampMixin, Base):
    __tablename__ = 'bot_config'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_execute: Mapped[bool] = mapped_column(Boolean, default=True)
    live_execution_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    scan_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    strategy_timeframe: Mapped[str] = mapped_column(String(16), default='1H')
    strategy_candles: Mapped[int] = mapped_column(Integer, default=240)
    risk_percent: Mapped[float] = mapped_column(default=0.01)
    max_new_positions_per_cycle: Mapped[int] = mapped_column(Integer, default=2)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    last_cycle_started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_cycle_finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_cycle_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_cycle_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text(), nullable=True)


class BotRun(TimestampMixin, Base):
    __tablename__ = 'bot_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(32), default='running', index=True)
    trigger_type: Mapped[str] = mapped_column(String(16), default='manual')
    scanned_pairs: Mapped[int] = mapped_column(Integer, default=0)
    decisions_total: Mapped[int] = mapped_column(Integer, default=0)
    allowed_total: Mapped[int] = mapped_column(Integer, default=0)
    executed_total: Mapped[int] = mapped_column(Integer, default=0)
    skipped_total: Mapped[int] = mapped_column(Integer, default=0)
    errors_total: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SystemEvent(TimestampMixin, Base):
    __tablename__ = 'system_events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(16), default='info', index=True)
    source: Mapped[str] = mapped_column(String(32), default='system', index=True)
    event_type: Mapped[str] = mapped_column(String(64), default='info', index=True)
    message: Mapped[str] = mapped_column(Text())
    related_symbol: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    related_market_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bot_run_id: Mapped[int | None] = mapped_column(ForeignKey('bot_runs.id'), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text(), nullable=True)


class SystemState(TimestampMixin, Base):
    __tablename__ = 'system_state'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    trading_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    kill_switch_armed: Mapped[bool] = mapped_column(Boolean, default=False)
    boot_count: Mapped[int] = mapped_column(Integer, default=0)
    last_startup_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_shutdown_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_bot_heartbeat_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_reconcile_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_lifecycle_sync_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_live_sync_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_live_sync_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    recovery_runs_count: Mapped[int] = mapped_column(Integer, default=0)
    last_recovery_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_flatten_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_flatten_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_flatten_message: Mapped[str | None] = mapped_column(Text(), nullable=True)


class ReconcileRun(TimestampMixin, Base):
    __tablename__ = 'reconcile_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(16), default='live', index=True)
    status: Mapped[str] = mapped_column(String(32), default='running', index=True)
    balances_synced: Mapped[int] = mapped_column(Integer, default=0)
    orders_seen: Mapped[int] = mapped_column(Integer, default=0)
    positions_seen: Mapped[int] = mapped_column(Integer, default=0)
    closed_local_positions: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RecoveryRun(TimestampMixin, Base):
    __tablename__ = 'recovery_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    startup_context: Mapped[str] = mapped_column(String(16), default='manual', index=True)
    status: Mapped[str] = mapped_column(String(32), default='running', index=True)
    stale_bot_runs: Mapped[int] = mapped_column(Integer, default=0)
    recovered_positions: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class FlattenRun(TimestampMixin, Base):
    __tablename__ = 'flatten_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), default='live', index=True)
    scope: Mapped[str] = mapped_column(String(16), default='all', index=True)
    status: Mapped[str] = mapped_column(String(32), default='running', index=True)
    orders_cancelled: Mapped[int] = mapped_column(Integer, default=0)
    close_orders_submitted: Mapped[int] = mapped_column(Integer, default=0)
    symbols_touched: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
