from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.account import ExchangeBalance, RuntimeSetting
from app.services.bybit import BybitError, BybitService


@dataclass
class BalanceRow:
    asset: str
    total: float
    available: float
    usd_value: float
    market_type: str


class BalanceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def overview(self) -> list[BalanceRow]:
        settings = self.db.scalar(select(RuntimeSetting).order_by(RuntimeSetting.id.asc()))
        runtime_mode = settings.mode if settings else 'paper'

        if runtime_mode == 'live':
            try:
                rows = await self.refresh_from_bybit()
                if rows:
                    return rows
            except BybitError:
                pass

        rows = self.db.scalars(select(ExchangeBalance).order_by(ExchangeBalance.asset.asc())).all()
        if rows:
            return [
                BalanceRow(
                    asset=row.asset,
                    total=row.total,
                    available=row.available,
                    usd_value=row.usd_value,
                    market_type=row.market_type,
                )
                for row in rows
            ]
        return [
            BalanceRow(asset='USDT', total=10000.0, available=10000.0, usd_value=10000.0, market_type='spot'),
            BalanceRow(asset='BTC', total=0.05, available=0.05, usd_value=4200.0, market_type='spot'),
        ]

    async def refresh_from_bybit(self) -> list[BalanceRow]:
        payload = await BybitService().get_wallet_balances()
        accounts = payload.get('result', {}).get('list', [])
        balances: list[BalanceRow] = []
        for account in accounts:
            for coin in account.get('coin', []):
                usd_value = float(coin.get('usdValue') or 0.0)
                wallet_balance = float(coin.get('walletBalance') or 0.0)
                available = float(coin.get('availableToWithdraw') or coin.get('walletBalance') or 0.0)
                if wallet_balance == 0 and usd_value == 0:
                    continue
                balances.append(
                    BalanceRow(
                        asset=coin.get('coin', ''),
                        total=wallet_balance,
                        available=available,
                        usd_value=usd_value,
                        market_type='wallet',
                    )
                )

        self.db.execute(delete(ExchangeBalance))
        for row in balances:
            self.db.add(
                ExchangeBalance(
                    balance_scope='wallet',
                    market_type=row.market_type,
                    asset=row.asset,
                    total=row.total,
                    available=row.available,
                    usd_value=row.usd_value,
                )
            )
        self.db.commit()
        return balances
