from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import TimestampMixin


class JournalEntry(TimestampMixin, Base):
    __tablename__ = 'journal_entries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int | None] = mapped_column(ForeignKey('trades.id'), nullable=True)
    backtest_run_id: Mapped[int | None] = mapped_column(ForeignKey('backtest_runs.id'), nullable=True)
    mode: Mapped[str] = mapped_column(String(16), index=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    direction: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_3: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    entry_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exit_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chart_points: Mapped[str | None] = mapped_column(Text(), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text(), nullable=True)
    ai_review_status: Mapped[str] = mapped_column(String(32), default='pending')
    ai_review_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hold_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    worst_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    mfe_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    strategy_scenario: Mapped[str | None] = mapped_column(String(64), nullable=True)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
