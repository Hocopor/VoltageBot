from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_10_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint10.db'
    if db_path.exists():
        db_path.unlink()

    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['CODEX_SESSION_DIR'] = str(base / 'codex')
    os.environ['BACKUP_ROOT'] = str(base / 'backups')
    os.environ['RELEASE_ROOT'] = str(base / 'releases')
    os.environ['PUBLIC_BASE_URL'] = 'https://voltage.example.com'
    os.environ['CLOUDFLARE_TUNNEL_TOKEN'] = 'dummy-token'
    os.environ['SECRET_KEY'] = 'checkpoint-10-secret'
    os.environ['BYBIT_TIMEOUT_SECONDS'] = '1'

    from app.main import app

    with TestClient(app) as client:
        report = client.get('/api/v1/ops/release-report')
        assert report.status_code == 200, report.text
        report_payload = report.json()
        assert report_payload['project'] == 'VOLTAGE', report.text
        assert report_payload['recommended_mode'] in {'paper', 'live', 'historical', 'blocked'}, report.text
        assert isinstance(report_payload['acceptance_checks'], list), report.text

        acceptance = client.post('/api/v1/ops/release-acceptance/run')
        assert acceptance.status_code == 200, acceptance.text
        acceptance_payload = acceptance.json()
        assert acceptance_payload['json_artifact']['name'].endswith('.json'), acceptance.text
        assert Path(acceptance_payload['json_artifact']['path']).exists(), acceptance.text
        assert Path(acceptance_payload['markdown_artifact']['path']).exists(), acceptance.text

        releases = client.get('/api/v1/ops/releases')
        assert releases.status_code == 200, releases.text
        releases_payload = releases.json()
        assert any(item['name'] == acceptance_payload['json_artifact']['name'] for item in releases_payload), releases.text
        assert any(item['name'] == acceptance_payload['markdown_artifact']['name'] for item in releases_payload), releases.text

        print('[OK] checkpoint 10 smoke test passed')


if __name__ == '__main__':
    main()
