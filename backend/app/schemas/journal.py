from datetime import datetime

from pydantic import BaseModel


class JournalEntryRead(BaseModel):
    id: int
    trade_id: int | None
    backtest_run_id: int | None
    mode: str
    market_type: str
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: float | None
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    take_profit_3: float | None
    realized_pnl: float
    entry_index: int | None
    exit_index: int | None
    chart_points: str | None
    tags: str | None
    ai_review_status: str
    ai_review_text: str | None
    close_reason: str | None
    hold_minutes: float | None
    best_price: float | None
    worst_price: float | None
    mfe_pnl: float | None
    mae_pnl: float | None
    strategy_scenario: str | None
    compliance_score: float | None
    review_summary: str | None
    created_at: datetime


class JournalSummaryRead(BaseModel):
    total_entries: int
    total_realized_pnl: float
    wins: int
    losses: int
    avg_hold_minutes: float
    by_mode: dict[str, int]
