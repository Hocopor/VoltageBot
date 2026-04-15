from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_06_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint06.db'
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

        state = client.get('/api/v1/ops/state')
        assert state.status_code == 200, state.text
        state_payload = state.json()
        assert state_payload['boot_count'] >= 1, state_payload
        assert state_payload['recovery_runs_count'] >= 1, state_payload

        recovery_runs = client.get('/api/v1/ops/recovery/runs')
        assert recovery_runs.status_code == 200, recovery_runs.text
        assert len(recovery_runs.json()) >= 1, recovery_runs.text

        save_pairs = client.post('/api/v1/pairs/selections', json={'spot_symbols': ['BTCUSDT'], 'futures_symbols': ['BTCUSDT']})
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
                'notes': 'checkpoint 06 smoke',
            },
        )
        assert save_settings.status_code == 200, save_settings.text

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

        lifecycle_sync = client.post('/api/v1/trade/lifecycle/sync')
        assert lifecycle_sync.status_code == 200, lifecycle_sync.text
        lifecycle_payload = lifecycle_sync.json()
        assert lifecycle_payload['synced_positions'] >= 1, lifecycle_payload

        positions = client.get('/api/v1/trade/positions')
        assert positions.status_code == 200, positions.text
        open_positions = positions.json()
        assert len(open_positions) >= 1, open_positions
        position_id = open_positions[0]['id']

        close_response = client.post(f'/api/v1/trade/positions/{position_id}/close', json={'reason': 'manual-close'})
        assert close_response.status_code == 200, close_response.text

        summary = client.get('/api/v1/journal/summary')
        assert summary.status_code == 200, summary.text
        assert summary.json()['total_entries'] >= 1, summary.text

        analytics = client.get('/api/v1/analytics/overview')
        assert analytics.status_code == 200, analytics.text
        analytics_payload = analytics.json()
        assert 'by_close_reason' in analytics_payload, analytics_payload
        assert 'tp_hit_distribution' in analytics_payload, analytics_payload

        lifecycle_events = client.get('/api/v1/trade/lifecycle/events')
        assert lifecycle_events.status_code == 200, lifecycle_events.text
        assert len(lifecycle_events.json()) >= 2, lifecycle_events.text

        recovery = client.post('/api/v1/ops/recovery/run')
        assert recovery.status_code == 200, recovery.text
        assert recovery.json()['status'] == 'completed', recovery.text

        print('[OK] checkpoint 06 smoke test passed')


if __name__ == '__main__':
    main()
