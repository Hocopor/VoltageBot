from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_08_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint08.db'
    if db_path.exists():
        db_path.unlink()

    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['CODEX_SESSION_DIR'] = str(base / 'codex')
    os.environ['DEEPSEEK_API_KEY'] = ''
    os.environ['BYBIT_TIMEOUT_SECONDS'] = '1'

    from app.db.session import SessionLocal
    from app.main import app
    from app.models.journal import JournalEntry
    from app.models.strategy import StrategyDecision

    with TestClient(app) as client:
        health = client.get('/healthz')
        assert health.status_code == 200, health.text

        start = client.post('/api/v1/auth/codex/browser/start')
        assert start.status_code == 200, start.text
        login_id = start.json()['login_id']

        complete = client.post(
            '/api/v1/auth/codex/browser/complete',
            json={'login_id': login_id, 'account_label': 'checkpoint-08-user'},
        )
        assert complete.status_code == 200, complete.text
        assert complete.json()['connected'] is True, complete.text

        deepseek_status = client.get('/api/v1/auth/deepseek/status')
        assert deepseek_status.status_code == 200, deepseek_status.text
        assert deepseek_status.json()['configured'] is False, deepseek_status.text

        deepseek_test = client.post('/api/v1/auth/deepseek/test', json={'prompt': 'Health check'})
        assert deepseek_test.status_code == 200, deepseek_test.text
        assert deepseek_test.json()['status'] in {'disabled', 'completed', 'empty'}, deepseek_test.text

        with SessionLocal() as db:
            decision = StrategyDecision(
                strategy_name='VOLTAGE',
                symbol='BTCUSDT',
                timeframe_context='1D,4H,1H',
                allowed=True,
                market_scenario='btc-dominance',
                filter_summary='EMA and momentum filters passed; volume confirms impulse.',
                risk_summary='Risk 1.0%, stop behind liquidity, TP ladder active.',
                confidence=0.84,
            )
            db.add(decision)
            db.flush()
            entry = JournalEntry(
                trade_id=None,
                backtest_run_id=None,
                mode='paper',
                market_type='futures',
                symbol='BTCUSDT',
                direction='buy',
                quantity=1.0,
                entry_price=65000.0,
                exit_price=66250.0,
                stop_loss=64000.0,
                take_profit_1=66500.0,
                take_profit_2=68000.0,
                take_profit_3=70000.0,
                realized_pnl=1250.0,
                ai_review_status='pending',
                close_reason='tp1',
                hold_minutes=95.0,
                best_price=66620.0,
                worst_price=64880.0,
                mfe_pnl=1620.0,
                mae_pnl=-120.0,
                strategy_scenario='btc-dominance',
                compliance_score=0.92,
                review_summary='Pending review',
            )
            db.add(entry)
            db.commit()
            decision_id = decision.id
            entry_id = entry.id

        explain = client.post(f'/api/v1/strategy/decisions/{decision_id}/explain')
        assert explain.status_code == 200, explain.text
        assert explain.json()['decision_id'] == decision_id, explain.text
        assert explain.json()['explanation'], explain.text

        reviewed = client.post('/api/v1/journal/review/pending?limit=5')
        assert reviewed.status_code == 200, reviewed.text
        reviewed_payload = reviewed.json()
        assert any(item['id'] == entry_id for item in reviewed_payload), reviewed.text
        assert any(item['ai_review_text'] for item in reviewed_payload), reviewed.text

        analytics = client.post('/api/v1/analytics/summary/review')
        assert analytics.status_code == 200, analytics.text
        assert analytics.json()['text'], analytics.text

        print('[OK] checkpoint 08 smoke test passed')


if __name__ == '__main__':
    main()
