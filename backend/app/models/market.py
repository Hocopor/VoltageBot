from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import TimestampMixin


class PairSelection(TimestampMixin, Base):
    __tablename__ = 'pair_selections'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_type: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=True)
