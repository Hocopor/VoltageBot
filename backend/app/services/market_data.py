from __future__ import annotations

import math
from dataclasses import dataclass

from app.services.bybit import BybitService


@dataclass
class Candle:
    index: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataService:
    def __init__(self) -> None:
        self.bybit = BybitService()

    async def historical_candles(self, symbol: str, market_type: str, timeframe: str = '1H', limit: int = 240) -> list[Candle]:
        try:
            data = await self.bybit.fetch_klines(symbol, market_type, timeframe=timeframe, limit=limit)
            candles: list[Candle] = []
            for idx, row in enumerate(data):
                if len(row) < 6:
                    continue
                candles.append(
                    Candle(
                        index=idx,
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                    )
                )
            if candles:
                return candles
        except Exception:
            pass
        return self.synthetic_candles(symbol, market_type, timeframe=timeframe, limit=limit)

    def synthetic_candles(self, symbol: str, market_type: str, timeframe: str = '1H', limit: int = 240) -> list[Candle]:
        seed = sum(ord(c) for c in f'{symbol}-{market_type}-{timeframe}')
        base = 100 + (seed % 130)
        drift = 0.18 if (seed % 2 == 0) else -0.04
        amplitude = 2.0 + (seed % 7) * 0.35
        candles: list[Candle] = []
        previous_close = float(base)
        for idx in range(limit):
            wave = math.sin((idx + (seed % 11)) / 8.0) * amplitude
            trend = idx * drift
            regime_shift = 5.5 if idx > limit * 0.58 else 0.0
            close = max(1.0, base + wave + trend + regime_shift)
            open_ = previous_close
            intrabar = 0.6 + abs(math.cos((idx + 3) / 4.0)) * 2.1
            high = max(open_, close) + intrabar
            low = max(0.1, min(open_, close) - intrabar * 0.9)
            volume = 1500 + abs(math.sin(idx / 3.0)) * 1000 + idx * 1.5
            if idx in {limit // 3, limit // 2, int(limit * 0.76)}:
                volume *= 1.9
            candles.append(Candle(index=idx, open=open_, high=high, low=low, close=close, volume=volume))
            previous_close = close
        return candles
