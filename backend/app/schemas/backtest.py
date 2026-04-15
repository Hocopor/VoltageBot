from datetime import datetime

from pydantic import BaseModel, Field


class BacktestRunRequest(BaseModel):
    symbol: str = Field(min_length=3)
    market_type: str = Field(pattern='^(spot|futures)$')
    timeframe: str = '1H'
    candles: int = Field(default=240, ge=120, le=1000)
    start_balance: float = Field(default=10000.0, gt=0)
    side_policy: str = Field(default='both', pattern='^(long_only|short_only|both)$')


class BacktestTradeRead(BaseModel):
    id: int
    run_id: int
    symbol: str
    market_type: str
    direction: str
    entry_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    quantity: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    realized_pnl: float
    rr_multiple: float
    close_reason: str
    notes: str | None
    created_at: datetime


class BacktestRunRead(BaseModel):
    id: int
    mode: str
    market_type: str
    symbol: str
    timeframe: str
    candles: int
    start_balance: float
    end_balance: float
    total_trades: int
    closed_trades: int
    wins: int
    losses: int
    win_rate: float
    realized_pnl: float
    max_drawdown: float
    profit_factor: float
    average_rr: float
    target_metrics_met: bool
    notes: str | None
    created_at: datetime


class BacktestRunDetail(BacktestRunRead):
    trades: list[BacktestTradeRead]
