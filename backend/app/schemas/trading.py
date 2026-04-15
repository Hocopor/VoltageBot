from datetime import datetime

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    symbol: str = Field(min_length=3)
    market_type: str = Field(pattern='^(spot|futures)$')
    side: str = Field(pattern='^(buy|sell)$')
    order_type: str = Field(pattern='^(market|limit)$')
    qty: float | None = Field(default=None, gt=0)
    price: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    risk_percent: float = Field(default=0.01, ge=0.01, le=0.03)
    note: str | None = None


class PositionCloseRequest(BaseModel):
    exit_price: float | None = Field(default=None, gt=0)
    reason: str = 'manual-close'


class OrderRead(BaseModel):
    id: int
    mode: str
    market_type: str
    symbol: str
    side: str
    order_type: str
    stage: str
    status: str
    qty: float
    filled_qty: float
    price: float | None
    avg_fill_price: float | None
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    take_profit_3: float | None
    reduce_only: bool = False
    last_exchange_status: str | None = None
    last_exchange_update_at: str | None = None
    created_at: datetime


class TradeRead(BaseModel):
    id: int
    mode: str
    market_type: str
    symbol: str
    direction: str
    status: str
    entry_price: float
    exit_price: float | None
    initial_qty: float
    remaining_qty: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    realized_pnl: float
    unrealized_pnl: float
    created_at: datetime


class PositionRead(BaseModel):
    id: int
    trade_id: int | None
    mode: str
    market_type: str
    symbol: str
    side: str
    status: str
    size: float
    initial_size: float
    avg_entry_price: float
    mark_price: float | None
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    tp1_hit: bool
    tp2_hit: bool
    tp3_hit: bool
    trailing_active: bool
    best_price: float | None
    worst_price: float | None
    position_idx: int = 0
    last_exchange_size: float | None = None
    last_live_sync_at: str | None = None
    external_source: str | None = None
    created_at: datetime


class PositionLifecycleEventRead(BaseModel):
    id: int
    position_id: int | None
    trade_id: int | None
    mode: str
    market_type: str
    symbol: str
    side: str
    event_type: str
    message: str
    price: float | None
    payload_json: str | None
    created_at: datetime


class PnlOverviewRead(BaseModel):
    realized_pnl: float
    unrealized_pnl: float
    open_positions: int
    closed_trades: int
    win_rate: float


class SyncRead(BaseModel):
    filled_orders: int
    closed_positions: int
    tracked_symbols: int


class LifecycleSyncRead(BaseModel):
    synced_positions: int
    closed_positions: int
    created_events: int


class LiveLifecycleSyncRead(BaseModel):
    orders_checked: int
    orders_updated: int
    orders_filled: int
    orders_cancelled: int
    positions_seen: int
    positions_adopted: int
    positions_closed: int
    protections_applied: int
    created_events: int
    summary: str
