from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    order_type: Mapped[str] = mapped_column(String(16))
    stage: Mapped[str] = mapped_column(String(32), default='entry')
    status: Mapped[str] = mapped_column(String(32), default='created')
    bybit_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qty: Mapped[float] = mapped_column(Float)
    filled_qty: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_3: Mapped[float | None] = mapped_column(Float, nullable=True)
    reduce_only: Mapped[bool] = mapped_column(Boolean, default=False)
    last_exchange_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_exchange_update_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text(), nullable=True)


class Trade(TimestampMixin, Base):
    __tablename__ = 'trades'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey('orders.id'), nullable=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    direction: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default='open')
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    initial_qty: Mapped[float] = mapped_column(Float)
    remaining_qty: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit_1: Mapped[float] = mapped_column(Float)
    take_profit_2: Mapped[float] = mapped_column(Float)
    take_profit_3: Mapped[float] = mapped_column(Float)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)


class Position(TimestampMixin, Base):
    __tablename__ = 'positions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int | None] = mapped_column(ForeignKey('trades.id'), nullable=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default='open')
    size: Mapped[float] = mapped_column(Float)
    initial_size: Mapped[float] = mapped_column(Float)
    avg_entry_price: Mapped[float] = mapped_column(Float)
    mark_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit_1: Mapped[float] = mapped_column(Float)
    take_profit_2: Mapped[float] = mapped_column(Float)
    take_profit_3: Mapped[float] = mapped_column(Float)
    tp1_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    tp2_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    tp3_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    trailing_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trailing_anchor_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    worst_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_timeframe: Mapped[str | None] = mapped_column(String(16), nullable=True)
    position_idx: Mapped[int] = mapped_column(Integer, default=0)
    last_exchange_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_live_sync_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_source: Mapped[str | None] = mapped_column(String(32), nullable=True)


class PositionLifecycleEvent(TimestampMixin, Base):
    __tablename__ = 'position_lifecycle_events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey('positions.id'), nullable=True, index=True)
    trade_id: Mapped[int | None] = mapped_column(ForeignKey('trades.id'), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    message: Mapped[str] = mapped_column(Text())
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text(), nullable=True)


class PnlSnapshot(TimestampMixin, Base):
    __tablename__ = 'pnl_snapshots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
