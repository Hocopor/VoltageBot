from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_04_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint04.db'
    if db_path.exists():
        db_path.unlink()

    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['CODEX_SESSION_DIR'] = str(base / 'codex')
    os.environ['BYBIT_TIMEOUT_SECONDS'] = '1'
    os.environ.setdefault('DEEPSEEK_API_KEY', '')

    from app.main import app

    with TestClient(app) as client:
        assert client.get('/healthz').status_code == 200
        assert client.get('/api/v1/settings/runtime').status_code == 200
        assert client.get('/api/v1/bot/config').status_code == 200

        save_pairs = client.post('/api/v1/pairs/selections', json={'spot_symbols': ['BTCUSDT'], 'futures_symbols': []})
        assert save_pairs.status_code == 200, save_pairs.text

        save_settings = client.put(
            '/api/v1/settings/runtime',
            json={
                'mode': 'paper',
                'spot_enabled': True,
                'futures_enabled': False,
                'paper_start_balance': 10000,
                'history_start_balance': 10000,
                'spot_working_balance': 1000,
                'futures_working_balance': 1000,
                'notes': 'checkpoint 04 smoke',
            },
        )
        assert save_settings.status_code == 200, save_settings.text

        save_bot = client.put(
            '/api/v1/bot/config',
            json={
                'enabled': True,
                'auto_execute': True,
                'live_execution_allowed': False,
                'scan_interval_seconds': 300,
                'strategy_timeframe': '1H',
                'strategy_candles': 240,
                'risk_percent': 0.01,
                'max_new_positions_per_cycle': 1,
                'notes': 'checkpoint 04 smoke',
            },
        )
        assert save_bot.status_code == 200, save_bot.text

        cycle = client.post('/api/v1/bot/cycle')
        assert cycle.status_code == 200, cycle.text
        cycle_payload = cycle.json()
        assert cycle_payload['run_id'] >= 1, cycle_payload
        assert cycle_payload['scanned_pairs'] >= 1, cycle_payload

        orders = client.get('/api/v1/trade/orders')
        assert orders.status_code == 200, orders.text
        positions = client.get('/api/v1/trade/positions')
        assert positions.status_code == 200, positions.text
        assert len(positions.json()) >= 1, positions.text

        paper_sync = client.post('/api/v1/trade/paper/sync')
        assert paper_sync.status_code == 200, paper_sync.text

        runs = client.get('/api/v1/bot/runs')
        assert runs.status_code == 200, runs.text
        assert len(runs.json()) >= 1, runs.text

        events = client.get('/api/v1/bot/events')
        assert events.status_code == 200, events.text
        assert len(events.json()) >= 2, events.text

        print('[OK] checkpoint 04 smoke test passed')
        print('bot run:', cycle_payload['run_id'])
        print('executed_total:', cycle_payload['executed_total'])
        print('positions:', len(positions.json()))
        print('events:', len(events.json()))


if __name__ == '__main__':
    main()
