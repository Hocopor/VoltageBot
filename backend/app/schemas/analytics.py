from pydantic import BaseModel


class AnalyticsOverviewRead(BaseModel):
    total_trades: int
    closed_trades: int
    realized_pnl: float
    profit_factor: float
    average_rr: float
    max_drawdown: float
    by_mode: dict[str, float]
    by_market: dict[str, float]
    by_symbol: dict[str, float]
    by_direction: dict[str, float]
    by_close_reason: dict[str, float]
    by_weekday: dict[str, float]
    by_hour: dict[str, float]
    monthly_pnl: dict[str, float]
    yearly_pnl: dict[str, float]
    tp_hit_distribution: dict[str, int]
    streaks: dict[str, int]
    average_hold_minutes: float
    average_compliance_score: float
    recent_equity_curve: list[float]


class AnalyticsReviewRead(BaseModel):
    status: str
    text: str
