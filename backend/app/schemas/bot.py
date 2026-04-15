from datetime import datetime

from pydantic import BaseModel, Field


class BotConfigRead(BaseModel):
    enabled: bool
    auto_execute: bool
    live_execution_allowed: bool
    scan_interval_seconds: int
    strategy_timeframe: str
    strategy_candles: int
    risk_percent: float
    max_new_positions_per_cycle: int
    notes: str | None = None
    last_cycle_started_at: str | None = None
    last_cycle_finished_at: str | None = None
    last_cycle_status: str | None = None
    last_cycle_summary: str | None = None
    last_error: str | None = None


class BotConfigUpdate(BaseModel):
    enabled: bool
    auto_execute: bool
    live_execution_allowed: bool
    scan_interval_seconds: int = Field(ge=15, le=3600)
    strategy_timeframe: str = Field(pattern='^(15M|1H|4H|1D)$')
    strategy_candles: int = Field(ge=120, le=1500)
    risk_percent: float = Field(ge=0.01, le=0.03)
    max_new_positions_per_cycle: int = Field(ge=1, le=20)
    notes: str | None = None


class BotRunRead(BaseModel):
    id: int
    mode: str
    status: str
    trigger_type: str
    scanned_pairs: int
    decisions_total: int
    allowed_total: int
    executed_total: int
    skipped_total: int
    errors_total: int
    summary: str | None
    started_at: str | None
    finished_at: str | None
    created_at: datetime


class SystemEventRead(BaseModel):
    id: int
    level: str
    source: str
    event_type: str
    message: str
    related_symbol: str | None
    related_market_type: str | None
    bot_run_id: int | None
    payload_json: str | None
    created_at: datetime


class BotCycleResult(BaseModel):
    run_id: int
    mode: str
    status: str
    scanned_pairs: int
    decisions_total: int
    allowed_total: int
    executed_total: int
    skipped_total: int
    errors_total: int
    summary: str
