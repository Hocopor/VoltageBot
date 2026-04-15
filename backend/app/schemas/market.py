from pydantic import BaseModel


class SymbolItem(BaseModel):
    symbol: str
    market_type: str


class PairSelectionsUpdate(BaseModel):
    spot_symbols: list[str] = []
    futures_symbols: list[str] = []


class PairSelectionsRead(BaseModel):
    spot_symbols: list[str]
    futures_symbols: list[str]
