from pydantic import BaseModel


class BalanceItem(BaseModel):
    asset: str
    total: float
    available: float
    usd_value: float
    market_type: str


class BalanceOverview(BaseModel):
    mode: str
    total_wallet_usd: float
    spot_working_balance: float
    futures_working_balance: float
    balances: list[BalanceItem]
