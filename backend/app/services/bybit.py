from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


@dataclass
class TickerQuote:
    symbol: str
    last_price: float
    bid_price: float | None = None
    ask_price: float | None = None


class BybitError(RuntimeError):
    pass


class BybitService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_symbols(self, category: str) -> list[str]:
        params = {'category': category}
        try:
            payload = await self._request('GET', '/v5/market/instruments-info', params=params)
        except Exception:
            return self._fallback(category)
        items = payload.get('result', {}).get('list', [])
        symbols: list[str] = []
        for item in items:
            symbol = item.get('symbol', '')
            if not symbol.endswith('USDT'):
                continue
            if category == 'spot' and item.get('status') not in {'Trading', None}:
                continue
            symbols.append(symbol)
        return sorted(symbols) or self._fallback(category)

    async def fetch_ticker(self, symbol: str, market_type: str) -> TickerQuote:
        category = 'linear' if market_type == 'futures' else 'spot'
        try:
            payload = await self._request('GET', '/v5/market/tickers', params={'category': category, 'symbol': symbol})
            items = payload.get('result', {}).get('list', [])
            if not items:
                raise BybitError(f'No ticker for {symbol}')
            row = items[0]
            return TickerQuote(
                symbol=symbol,
                last_price=float(row.get('lastPrice') or row.get('lastprice') or 0.0),
                bid_price=float(row['bid1Price']) if row.get('bid1Price') else None,
                ask_price=float(row['ask1Price']) if row.get('ask1Price') else None,
            )
        except Exception:
            return self._fallback_ticker(symbol)

    async def fetch_klines(self, symbol: str, market_type: str, timeframe: str = '60', limit: int = 240) -> list[list[str]]:
        category = 'linear' if market_type == 'futures' else 'spot'
        interval_map = {'15M': '15', '1H': '60', '4H': '240', '1D': 'D', '1W': 'W'}
        interval = interval_map.get(timeframe.upper(), timeframe)
        payload = await self._request('GET', '/v5/market/kline', params={'category': category, 'symbol': symbol, 'interval': interval, 'limit': limit})
        return list(reversed(payload.get('result', {}).get('list', [])))

    async def get_wallet_balances(self) -> dict:
        self._assert_credentials()
        return await self._request('GET', '/v5/account/wallet-balance', params={'accountType': 'UNIFIED'}, auth=True)

    async def get_open_orders(self, market_type: str, open_only: int = 0, symbol: str | None = None) -> dict:
        self._assert_credentials()
        category = 'linear' if market_type == 'futures' else 'spot'
        params = {'category': category, 'openOnly': open_only}
        if symbol:
            params['symbol'] = symbol
        elif category == 'linear':
            params['settleCoin'] = 'USDT'
        return await self._request('GET', '/v5/order/realtime', params=params, auth=True)

    async def get_positions(self, symbol: str | None = None) -> dict:
        self._assert_credentials()
        params = {'category': 'linear', 'settleCoin': 'USDT'}
        if symbol:
            params['symbol'] = symbol
        return await self._request('GET', '/v5/position/list', params=params, auth=True)

    async def place_order(self, payload: dict) -> dict:
        self._assert_credentials()
        return await self._request('POST', '/v5/order/create', json_body=payload, auth=True)

    async def cancel_all_orders(self, market_type: str, symbol: str | None = None) -> dict:
        self._assert_credentials()
        category = 'linear' if market_type == 'futures' else 'spot'
        body: dict[str, str] = {'category': category}
        if symbol:
            body['symbol'] = symbol
        elif category == 'linear':
            body['settleCoin'] = 'USDT'
        return await self._request('POST', '/v5/order/cancel-all', json_body=body, auth=True)

    async def set_trading_stop(
        self,
        *,
        symbol: str,
        stop_loss: float | None,
        take_profit: float | None,
        position_idx: int = 0,
        trailing_stop: float | None = None,
        active_price: float | None = None,
    ) -> dict:
        self._assert_credentials()
        body: dict[str, str | int] = {
            'category': 'linear',
            'symbol': symbol,
            'tpslMode': 'Full',
            'positionIdx': position_idx,
            'stopLoss': self._fmt(stop_loss) if stop_loss and stop_loss > 0 else '0',
            'takeProfit': self._fmt(take_profit) if take_profit and take_profit > 0 else '0',
            'tpOrderType': 'Market',
            'slOrderType': 'Market',
        }
        if trailing_stop and trailing_stop > 0:
            body['trailingStop'] = self._fmt(trailing_stop)
        if active_price and active_price > 0:
            body['activePrice'] = self._fmt(active_price)
        return await self._request('POST', '/v5/position/trading-stop', json_body=body, auth=True)

    async def close_linear_position(self, *, symbol: str, side: str, qty: float, position_idx: int = 0, order_link_id: str | None = None) -> dict:
        close_side = 'Sell' if side.lower() == 'buy' else 'Buy'
        payload = {
            'category': 'linear',
            'symbol': symbol,
            'side': close_side,
            'orderType': 'Market',
            'qty': self._fmt(qty),
            'reduceOnly': True,
            'positionIdx': position_idx,
        }
        if order_link_id:
            payload['orderLinkId'] = order_link_id
        return await self.place_order(payload)

    async def close_spot_position(self, *, symbol: str, qty: float, order_link_id: str | None = None) -> dict:
        payload = {
            'category': 'spot',
            'symbol': symbol,
            'side': 'Sell',
            'orderType': 'Market',
            'qty': self._fmt(qty),
        }
        if order_link_id:
            payload['orderLinkId'] = order_link_id
        return await self.place_order(payload)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        auth: bool = False,
    ) -> dict:
        url = f"{self.settings.bybit_api_base_url}{path}"
        headers: dict[str, str] = {}
        query_string = urlencode(params or {})
        body_string = json.dumps(json_body or {}, separators=(',', ':'))

        if auth:
            timestamp = str(int(time.time() * 1000))
            recv_window = str(self.settings.bybit_recv_window)
            payload = f"{timestamp}{self.settings.bybit_api_key}{recv_window}{query_string if method == 'GET' else body_string}"
            signature = hmac.new(
                self.settings.bybit_api_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256,
            ).hexdigest()
            headers.update(
                {
                    'X-BAPI-API-KEY': self.settings.bybit_api_key,
                    'X-BAPI-TIMESTAMP': timestamp,
                    'X-BAPI-RECV-WINDOW': recv_window,
                    'X-BAPI-SIGN': signature,
                }
            )

        if json_body is not None:
            headers['Content-Type'] = 'application/json'

        async with httpx.AsyncClient(timeout=float(self.settings.bybit_timeout_seconds)) as client:
            response = await client.request(method, url, params=params, json=json_body, headers=headers)
        response.raise_for_status()
        payload = response.json()
        if payload.get('retCode') not in (0, '0', None):
            raise BybitError(payload.get('retMsg', 'Unknown Bybit error'))
        return payload

    def _fallback(self, category: str) -> list[str]:
        if category == 'spot':
            return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT']
        return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT']

    def _fallback_ticker(self, symbol: str) -> TickerQuote:
        defaults = {
            'BTCUSDT': 65000.0,
            'ETHUSDT': 3200.0,
            'SOLUSDT': 150.0,
            'XRPUSDT': 0.62,
            'DOGEUSDT': 0.16,
            'ADAUSDT': 0.55,
        }
        price = defaults.get(symbol, 100.0)
        return TickerQuote(symbol=symbol, last_price=price, bid_price=price * 0.999, ask_price=price * 1.001)

    def _assert_credentials(self) -> None:
        if not self.settings.bybit_api_key or not self.settings.bybit_api_secret:
            raise BybitError('Bybit API credentials are not configured')

    def _fmt(self, value: float | None) -> str:
        value = float(value or 0.0)
        return f'{value:.8f}'.rstrip('0').rstrip('.') or '0'


class BybitPublicService(BybitService):
    pass
