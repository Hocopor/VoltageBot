from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_07_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint07.db'
    if db_path.exists():
        db_path.unlink()

    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['CODEX_SESSION_DIR'] = str(base / 'codex')
    os.environ['BYBIT_TIMEOUT_SECONDS'] = '1'
    os.environ.setdefault('DEEPSEEK_API_KEY', '')

    from app.main import app
    from app.services.bybit import BybitService

    state: dict[str, object] = {
        'position_open': False,
        'orders': [],
        'stop_syncs': 0,
    }

    async def fake_place_order(self, payload: dict) -> dict:  # noqa: ANN001
        order_id = f"mock-{len(state['orders']) + 1}"
        record = dict(payload)
        record['orderId'] = order_id
        state['orders'].append(record)
        if record.get('category') == 'linear' and not record.get('reduceOnly'):
            state['position_open'] = True
        return {'retCode': 0, 'result': {'orderId': order_id}}

    async def fake_get_open_orders(self, market_type: str, open_only: int = 0, symbol: str | None = None) -> dict:  # noqa: ARG001
        rows: list[dict] = []
        for record in list(state['orders']):
            if market_type == 'futures' and record.get('category') != 'linear':
                continue
            if market_type == 'spot' and record.get('category') != 'spot':
                continue
            is_reduce = bool(record.get('reduceOnly'))
            status = 'New' if is_reduce and state['position_open'] else 'Filled'
            if open_only == 0 and status != 'New':
                continue
            if open_only == 1 and status == 'New':
                continue
            rows.append(
                {
                    'orderId': record['orderId'],
                    'orderLinkId': record.get('orderLinkId', ''),
                    'symbol': record['symbol'],
                    'side': record['side'],
                    'orderType': record['orderType'],
                    'orderStatus': status,
                    'qty': record['qty'],
                    'cumExecQty': record['qty'] if status == 'Filled' else '0',
                    'price': record.get('price', ''),
                    'avgPrice': record.get('price', '65000') if status == 'Filled' else '',
                    'stopLoss': record.get('stopLoss', ''),
                    'takeProfit': record.get('takeProfit', ''),
                    'reduceOnly': is_reduce,
                }
            )
        return {'retCode': 0, 'result': {'list': rows}}

    async def fake_get_positions(self, symbol: str | None = None) -> dict:  # noqa: ARG001
        if not state['position_open']:
            return {'retCode': 0, 'result': {'list': []}}
        return {
            'retCode': 0,
            'result': {
                'list': [
                    {
                        'symbol': 'BTCUSDT',
                        'side': 'Buy',
                        'size': '1',
                        'avgPrice': '65000',
                        'markPrice': '65200',
                        'stopLoss': '62000',
                        'takeProfit': '80000',
                        'positionIdx': 0,
                    }
                ]
            },
        }

    async def fake_get_wallet_balances(self) -> dict:
        return {'retCode': 0, 'result': {'list': [{'coin': [{'coin': 'USDT', 'walletBalance': '1000', 'availableToWithdraw': '900', 'usdValue': '1000'}]}]}}

    async def fake_cancel_all_orders(self, market_type: str, symbol: str | None = None) -> dict:  # noqa: ARG001
        return {'retCode': 0, 'result': {'list': [{'orderId': row.get('orderId', '')} for row in state['orders']]}}

    async def fake_set_trading_stop(self, **kwargs) -> dict:  # noqa: ANN003
        state['stop_syncs'] = int(state['stop_syncs']) + 1
        return {'retCode': 0, 'result': {}}

    BybitService.place_order = fake_place_order  # type: ignore[method-assign]
    BybitService.get_open_orders = fake_get_open_orders  # type: ignore[method-assign]
    BybitService.get_positions = fake_get_positions  # type: ignore[method-assign]
    BybitService.get_wallet_balances = fake_get_wallet_balances  # type: ignore[method-assign]
    BybitService.cancel_all_orders = fake_cancel_all_orders  # type: ignore[method-assign]
    BybitService.set_trading_stop = fake_set_trading_stop  # type: ignore[method-assign]

    with TestClient(app) as client:
        health = client.get('/healthz')
        assert health.status_code == 200, health.text

        save_pairs = client.post('/api/v1/pairs/selections', json={'spot_symbols': [], 'futures_symbols': ['BTCUSDT']})
        assert save_pairs.status_code == 200, save_pairs.text

        save_settings = client.put(
            '/api/v1/settings/runtime',
            json={
                'mode': 'live',
                'spot_enabled': False,
                'futures_enabled': True,
                'paper_start_balance': 10000,
                'history_start_balance': 10000,
                'spot_working_balance': 1000,
                'futures_working_balance': 1000,
                'notes': 'checkpoint 07 smoke',
            },
        )
        assert save_settings.status_code == 200, save_settings.text

        execute = client.post(
            '/api/v1/trade/execute',
            json={
                'symbol': 'BTCUSDT',
                'market_type': 'futures',
                'side': 'buy',
                'order_type': 'market',
                'qty': 1,
                'risk_percent': 0.01,
            },
        )
        assert execute.status_code == 200, execute.text

        lifecycle = client.post('/api/v1/trade/live/lifecycle')
        assert lifecycle.status_code == 200, lifecycle.text
        lifecycle_payload = lifecycle.json()
        assert lifecycle_payload['orders_filled'] >= 1, lifecycle_payload
        assert lifecycle_payload['positions_seen'] >= 1, lifecycle_payload
        assert lifecycle_payload['protections_applied'] >= 1, lifecycle_payload

        positions = client.get('/api/v1/trade/positions')
        assert positions.status_code == 200, positions.text
        assert any(row['mode'] == 'live' and row['status'] == 'open' for row in positions.json()), positions.text

        flatten = client.post('/api/v1/ops/flatten/live/kill-switch')
        assert flatten.status_code == 200, flatten.text
        flatten_payload = flatten.json()
        assert flatten_payload['close_orders_submitted'] >= 1, flatten_payload

        ops_state = client.get('/api/v1/ops/state')
        assert ops_state.status_code == 200, ops_state.text
        assert ops_state.json()['kill_switch_armed'] is True, ops_state.text

        state['position_open'] = False
        lifecycle_closed = client.post('/api/v1/trade/live/lifecycle')
        assert lifecycle_closed.status_code == 200, lifecycle_closed.text
        assert lifecycle_closed.json()['positions_closed'] >= 1, lifecycle_closed.text

        journal = client.get('/api/v1/journal/summary')
        assert journal.status_code == 200, journal.text
        assert journal.json()['total_entries'] >= 1, journal.text

        flatten_runs = client.get('/api/v1/ops/flatten/runs')
        assert flatten_runs.status_code == 200, flatten_runs.text
        assert len(flatten_runs.json()) >= 1, flatten_runs.text

        print('[OK] checkpoint 07 smoke test passed')


if __name__ == '__main__':
    main()
