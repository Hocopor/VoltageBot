from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.strategy import StrategyDecision
from app.models.trade import Trade
from app.services.market_data import Candle, MarketDataService


@dataclass
class StrategySignal:
    symbol: str
    market_type: str
    side: str
    allowed: bool
    market_scenario: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    filter_summary: str
    risk_summary: str
    decision_id: int


class StrategyEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.market_data = MarketDataService()

    async def evaluate(
        self,
        symbol: str,
        market_type: str,
        side: str,
        timeframe: str = '1H',
        candles: int = 240,
        series: list[Candle] | None = None,
    ) -> StrategySignal:
        candle_series = series if series is not None else await self.market_data.historical_candles(symbol, market_type, timeframe=timeframe, limit=candles)
        return self._evaluate_series(symbol, market_type, side, timeframe, candle_series)

    def _evaluate_series(self, symbol: str, market_type: str, side: str, timeframe: str, series: list[Candle]) -> StrategySignal:
        closes = [c.close for c in series]
        volumes = [c.volume for c in series]
        last = series[-1]
        previous = series[-2] if len(series) > 1 else series[-1]
        ema21 = self._ema(closes, 21)
        ema55 = self._ema(closes, 55)
        rsi14 = self._rsi(closes, 14)
        previous_rsi = self._rsi(closes[:-1], 14) if len(closes) > 15 else rsi14
        atr14 = self._atr(series, 14)
        macd_hist = self._macd_histogram(closes)
        obv_values = self._obv(closes, volumes)
        obv_slope = obv_values[-1] - obv_values[max(0, len(obv_values) - 10)]
        volume_ratio = last.volume / max(mean(volumes[-20:]), 1.0)
        trend_up = ema21 > ema55 and last.close > ema21
        trend_down = ema21 < ema55 and last.close < ema21
        btc_regime = self._btc_regime(series)
        sentiment = self._sentiment_score(series)
        scenario = self._scenario(trend_up, trend_down, btc_regime, sentiment)
        price_action = self._price_action(series)
        liquidity = self._liquidity_context(series)
        sector_ok = self._sector_risk(symbol)
        turning_up = rsi14 >= previous_rsi or last.close >= previous.close
        turning_down = rsi14 <= previous_rsi or last.close <= previous.close
        bullish_pattern = price_action in {'bullish-engulfing', 'pin-bar', 'range-compression'}
        bearish_pattern = price_action in {'bearish-engulfing', 'pin-bar', 'range-compression'}
        volume_ok = obv_slope >= 0 and volume_ratio >= 0.85

        if side == 'buy':
            momentum_ok = ((38 <= rsi14 <= 68) and turning_up and macd_hist >= -0.15) or (rsi14 < 40 and turning_up and macd_hist >= -0.25)
            sentiment_ok = (symbol.startswith('BTC') and btc_regime in {'rising', 'stable'} and sentiment <= 80) or sentiment < 55
            allowed = trend_up and momentum_ok and volume_ok and bullish_pattern and sentiment_ok and sector_ok
            stop_loss = self._default_stop(last.close, symbol, side)
        else:
            momentum_ok = ((32 <= rsi14 <= 62) and turning_down and macd_hist <= 0.15) or (rsi14 > 60 and turning_down and macd_hist <= 0.25)
            allowed = market_type == 'futures' and trend_down and momentum_ok and volume_ratio >= 0.85 and bearish_pattern and sector_ok
            stop_loss = self._default_stop(last.close, symbol, side)

        tp1 = self._target_from_r(last.close, stop_loss, side, 1.5)
        tp2 = self._target_from_r(last.close, stop_loss, side, 3.0)
        tp3 = self._target_from_r(last.close, stop_loss, side, 5.0)
        confidence = max(0.05, min(0.99, self._confidence(allowed, trend_up, trend_down, rsi14, macd_hist, obv_slope, volume_ratio, atr14)))
        filter_summary = (
            f'BTC regime: {btc_regime}; scenario: {scenario}; trend EMA21/55={ema21:.4f}/{ema55:.4f}; '
            f'RSI14={rsi14:.2f}; MACD hist={macd_hist:.4f}; ATR14={atr14:.4f}; OBV slope={obv_slope:.2f}; '
            f'volume ratio={volume_ratio:.2f}; price action={price_action}; liquidity={liquidity}.'
        )
        risk_summary = (
            f'Stop={stop_loss:.8f}; TP ladder={tp1:.8f}/{tp2:.8f}/{tp3:.8f}; '
            'risk policy 1-3% deposit, mandatory SL/TP, no more than 3 correlated positions in one sector.'
        )
        decision = StrategyDecision(
            strategy_name='VOLTAGE',
            symbol=symbol,
            timeframe_context=f'1D,4H,{timeframe}',
            allowed=allowed,
            market_scenario=scenario,
            filter_summary=filter_summary,
            risk_summary=risk_summary,
            confidence=confidence,
        )
        self.db.add(decision)
        self.db.flush()
        return StrategySignal(
            symbol=symbol,
            market_type=market_type,
            side=side,
            allowed=allowed,
            market_scenario=scenario,
            confidence=round(confidence, 4),
            entry_price=last.close,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            filter_summary=filter_summary,
            risk_summary=risk_summary,
            decision_id=decision.id,
        )

    def list_decisions(self, limit: int = 50) -> list[StrategyDecision]:
        stmt = select(StrategyDecision).order_by(StrategyDecision.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def _default_stop(self, entry_price: float, symbol: str, side: str) -> float:
        is_major = symbol.startswith('BTC') or symbol.startswith('ETH')
        pct = 0.06 if is_major else 0.10
        return entry_price * (1 - pct) if side == 'buy' else entry_price * (1 + pct)

    def _target_from_r(self, entry: float, stop: float, side: str, multiple: float) -> float:
        distance = abs(entry - stop) * multiple
        return entry + distance if side == 'buy' else entry - distance

    def _scenario(self, trend_up: bool, trend_down: bool, btc_regime: str, sentiment: int) -> str:
        if trend_up and btc_regime == 'falling' and sentiment < 45:
            return 'altseason'
        if trend_down and sentiment < 20:
            return 'bearish-market'
        if btc_regime in {'rising', 'stable'}:
            return 'bitcoin-dominance'
        return 'neutral'

    def _btc_regime(self, candles: list[Candle]) -> str:
        recent = mean(c.close for c in candles[-12:])
        prior = mean(c.close for c in candles[-24:-12])
        change = (recent - prior) / max(prior, 1e-9)
        if change > 0.02:
            return 'rising'
        if change < -0.02:
            return 'falling'
        return 'stable'

    def _sentiment_score(self, candles: list[Candle]) -> int:
        closes = [c.close for c in candles]
        swing = (max(closes[-30:]) - min(closes[-30:])) / max(mean(closes[-30:]), 1.0)
        downside = sum(1 for a, b in zip(closes[-15:], closes[-14:]) if b < a)
        greed = 50 + (10 if closes[-1] > mean(closes[-10:]) else -10) + int(swing * 20) - downside
        return max(5, min(95, greed))

    def _price_action(self, candles: list[Candle]) -> str:
        if len(candles) < 3:
            return 'insufficient-data'
        a, b, c = candles[-3], candles[-2], candles[-1]
        bullish_engulfing = c.close > c.open and b.close < b.open and c.close >= b.open and c.open <= b.close
        bearish_engulfing = c.close < c.open and b.close > b.open and c.open >= b.close and c.close <= b.open
        pin_bar = (c.high - max(c.open, c.close)) > 2 * abs(c.close - c.open) or (min(c.open, c.close) - c.low) > 2 * abs(c.close - c.open)
        if bullish_engulfing:
            return 'bullish-engulfing'
        if bearish_engulfing:
            return 'bearish-engulfing'
        if pin_bar:
            return 'pin-bar'
        return 'range-compression'

    def _liquidity_context(self, candles: list[Candle]) -> str:
        highs = [c.high for c in candles[-20:]]
        lows = [c.low for c in candles[-20:]]
        spread = max(highs) - min(lows)
        if spread / max(mean([c.close for c in candles[-20:]]), 1.0) < 0.06:
            return 'liquidity-cluster-nearby'
        return 'broad-liquidity'

    def _sector_risk(self, symbol: str) -> bool:
        sector_groups = {
            'AI': {'FETUSDT', 'AGIXUSDT', 'WLDUSDT'},
            'MEME': {'DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT'},
            'L1': {'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT'},
        }
        symbol_sector = next((name for name, members in sector_groups.items() if symbol in members), None)
        if not symbol_sector:
            return True
        open_trades = list(self.db.scalars(select(Trade).where(Trade.status == 'open')).all())
        open_in_sector = 0
        for trade in open_trades:
            other_sector = next((name for name, members in sector_groups.items() if trade.symbol in members), None)
            if other_sector == symbol_sector:
                open_in_sector += 1
        return open_in_sector < 3

    def _confidence(self, allowed: bool, trend_up: bool, trend_down: bool, rsi: float, macd_hist: float, obv_slope: float, volume_ratio: float, atr: float) -> float:
        score = 0.3
        if allowed:
            score += 0.2
        if trend_up or trend_down:
            score += 0.15
        if 40 <= rsi <= 60:
            score += 0.1
        if abs(macd_hist) > 0.05:
            score += 0.1
        if obv_slope > 0:
            score += 0.07
        if volume_ratio > 1.1:
            score += 0.05
        if atr > 0:
            score += 0.03
        return score

    def _ema(self, values: list[float], period: int) -> float:
        alpha = 2 / (period + 1)
        ema = values[0]
        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * ema
        return ema

    def _rsi(self, values: list[float], period: int) -> float:
        gains: list[float] = []
        losses: list[float] = []
        for prev, cur in zip(values[:-1], values[1:]):
            change = cur - prev
            gains.append(max(change, 0.0))
            losses.append(abs(min(change, 0.0)))
        avg_gain = mean(gains[-period:]) if gains[-period:] else 0.0
        avg_loss = mean(losses[-period:]) if losses[-period:] else 0.0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _atr(self, candles: list[Candle], period: int) -> float:
        trs = []
        for prev, cur in zip(candles[:-1], candles[1:]):
            tr = max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close))
            trs.append(tr)
        return mean(trs[-period:]) if trs[-period:] else 0.0

    def _macd_histogram(self, values: list[float]) -> float:
        if len(values) < 35:
            return 0.0
        ema12_series = self._ema_series(values, 12)
        ema26_series = self._ema_series(values, 26)
        macd_series = [a - b for a, b in zip(ema12_series, ema26_series)]
        signal_series = self._ema_series(macd_series, 9)
        return macd_series[-1] - signal_series[-1]

    def _ema_series(self, values: list[float], period: int) -> list[float]:
        if not values:
            return []
        alpha = 2 / (period + 1)
        out = [values[0]]
        for value in values[1:]:
            out.append(alpha * value + (1 - alpha) * out[-1])
        return out

    def _obv(self, closes: list[float], volumes: list[float]) -> list[float]:
        out = [0.0]
        for prev_close, close, volume in zip(closes[:-1], closes[1:], volumes[1:]):
            if close > prev_close:
                out.append(out[-1] + volume)
            elif close < prev_close:
                out.append(out[-1] - volume)
            else:
                out.append(out[-1])
        return out
