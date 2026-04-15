from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_03_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint03.db'
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

        strategy = client.post(
            '/api/v1/strategy/evaluate',
            json={
                'symbol': 'BTCUSDT',
                'market_type': 'futures',
                'side': 'buy',
                'timeframe': '1H',
                'candles': 180,
            },
        )
        assert strategy.status_code == 200, strategy.text

        backtest = client.post(
            '/api/v1/backtest/run',
            json={
                'symbol': 'BTCUSDT',
                'market_type': 'futures',
                'timeframe': '1H',
                'candles': 180,
                'start_balance': 10000,
                'side_policy': 'both',
            },
        )
        assert backtest.status_code == 200, backtest.text
        run = backtest.json()
        assert run['closed_trades'] >= 1, run

        entries = client.get('/api/v1/journal/entries')
        assert entries.status_code == 200, entries.text
        data = entries.json()
        assert len(data) >= 1, data

        review = client.post(f"/api/v1/journal/entries/{data[0]['id']}/review")
        assert review.status_code == 200, review.text

        analytics = client.get('/api/v1/analytics/overview')
        assert analytics.status_code == 200, analytics.text

        print('[OK] checkpoint 03 smoke test passed')
        print('strategy decision id:', strategy.json()['created_decision_id'])
        print('backtest run id:', run['id'])
        print('closed trades:', run['closed_trades'])
        print('journal entries:', len(data))


if __name__ == '__main__':
    main()
