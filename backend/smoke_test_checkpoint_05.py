from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_05_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint05.db'
    if db_path.exists():
        db_path.unlink()

    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['CODEX_SESSION_DIR'] = str(base / 'codex')
    os.environ['BYBIT_TIMEOUT_SECONDS'] = '1'
    os.environ.setdefault('DEEPSEEK_API_KEY', '')

    from app.main import app

    with TestClient(app) as client:
        health = client.get('/healthz')
        assert health.status_code == 200, health.text
        health_payload = health.json()
        assert health_payload['status'] == 'ok', health_payload
        assert 'state' in health_payload, health_payload

        state = client.get('/api/v1/ops/state')
        assert state.status_code == 200, state.text
        assert state.json()['boot_count'] >= 1, state.text

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
                'notes': 'checkpoint 05 smoke',
            },
        )
        assert save_settings.status_code == 200, save_settings.text

        pause = client.put('/api/v1/ops/state', json={'maintenance_mode': False, 'trading_paused': True, 'kill_switch_armed': False})
        assert pause.status_code == 200, pause.text
        blocked = client.post(
            '/api/v1/trade/execute',
            json={
                'symbol': 'BTCUSDT',
                'market_type': 'spot',
                'side': 'buy',
                'order_type': 'market',
                'risk_percent': 0.01,
            },
        )
        assert blocked.status_code == 400, blocked.text
        assert 'paused' in blocked.text.lower(), blocked.text

        resume = client.put('/api/v1/ops/state', json={'maintenance_mode': False, 'trading_paused': False, 'kill_switch_armed': False})
        assert resume.status_code == 200, resume.text

        execute = client.post(
            '/api/v1/trade/execute',
            json={
                'symbol': 'BTCUSDT',
                'market_type': 'spot',
                'side': 'buy',
                'order_type': 'market',
                'risk_percent': 0.01,
            },
        )
        assert execute.status_code == 200, execute.text

        positions = client.get('/api/v1/trade/positions')
        assert positions.status_code == 200, positions.text
        assert len(positions.json()) >= 1, positions.text

        flatten = client.post('/api/v1/ops/flatten-paper')
        assert flatten.status_code == 200, flatten.text
        assert flatten.json()['closed_positions'] >= 1, flatten.text

        runs = client.get('/api/v1/ops/reconcile/runs')
        assert runs.status_code == 200, runs.text

        print('[OK] checkpoint 05 smoke test passed')
        print('boot_count:', state.json()['boot_count'])
        print('closed_positions:', flatten.json()['closed_positions'])


if __name__ == '__main__':
    main()
