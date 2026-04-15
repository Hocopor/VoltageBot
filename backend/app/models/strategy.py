from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import TimestampMixin


class StrategyDecision(TimestampMixin, Base):
    __tablename__ = 'strategy_decisions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_name: Mapped[str] = mapped_column(String(64), default='VOLTAGE', index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe_context: Mapped[str] = mapped_column(String(128), default='1D,4H,1H')
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    market_scenario: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filter_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    risk_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class BacktestRun(TimestampMixin, Base):
    __tablename__ = 'backtest_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), default='historical', index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), default='1H')
    candles: Mapped[int] = mapped_column(Integer, default=240)
    start_balance: Mapped[float] = mapped_column(Float, default=10000.0)
    end_balance: Mapped[float] = mapped_column(Float, default=10000.0)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    closed_trades: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown: Mapped[float] = mapped_column(Float, default=0.0)
    profit_factor: Mapped[float] = mapped_column(Float, default=0.0)
    average_rr: Mapped[float] = mapped_column(Float, default=0.0)
    target_metrics_met: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)


class BacktestTrade(TimestampMixin, Base):
    __tablename__ = 'backtest_trades'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey('backtest_runs.id'), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    direction: Mapped[str] = mapped_column(String(8))
    entry_index: Mapped[int] = mapped_column(Integer)
    exit_index: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit_1: Mapped[float] = mapped_column(Float)
    take_profit_2: Mapped[float] = mapped_column(Float)
    take_profit_3: Mapped[float] = mapped_column(Float)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    rr_multiple: Mapped[float] = mapped_column(Float, default=0.0)
    close_reason: Mapped[str] = mapped_column(String(32), default='signal')
    decision_id: Mapped[int | None] = mapped_column(ForeignKey('strategy_decisions.id'), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
