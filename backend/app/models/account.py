from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import TimestampMixin


class RuntimeSetting(TimestampMixin, Base):
    __tablename__ = 'runtime_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(32), default='paper')
    spot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    futures_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    paper_start_balance: Mapped[float] = mapped_column(Float, default=10000.0)
    history_start_balance: Mapped[float] = mapped_column(Float, default=10000.0)
    spot_working_balance: Mapped[float] = mapped_column(Float, default=1000.0)
    futures_working_balance: Mapped[float] = mapped_column(Float, default=1000.0)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)


class ExchangeBalance(TimestampMixin, Base):
    __tablename__ = 'exchange_balances'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    balance_scope: Mapped[str] = mapped_column(String(32), default='wallet')
    market_type: Mapped[str] = mapped_column(String(16), default='spot')
    asset: Mapped[str] = mapped_column(String(24), index=True)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    available: Mapped[float] = mapped_column(Float, default=0.0)
    usd_value: Mapped[float] = mapped_column(Float, default=0.0)
