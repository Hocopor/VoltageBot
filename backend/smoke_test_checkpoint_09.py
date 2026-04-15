from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base = Path('/tmp/voltage_checkpoint_09_smoke')
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / 'checkpoint09.db'
    if db_path.exists():
        db_path.unlink()

    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['CODEX_SESSION_DIR'] = str(base / 'codex')
    os.environ['BACKUP_ROOT'] = str(base / 'backups')
    os.environ['RELEASE_ROOT'] = str(base / 'releases')
    os.environ['PUBLIC_BASE_URL'] = 'https://voltage.example.com'
    os.environ['CLOUDFLARE_TUNNEL_TOKEN'] = 'dummy-token'
    os.environ['SECRET_KEY'] = 'checkpoint-09-secret'
    os.environ['BYBIT_TIMEOUT_SECONDS'] = '1'

    from app.main import app

    with TestClient(app) as client:
        health = client.get('/healthz')
        assert health.status_code == 200, health.text
        assert 'readiness' in health.json(), health.text

        preflight = client.get('/api/v1/ops/preflight')
        assert preflight.status_code == 200, preflight.text
        preflight_payload = preflight.json()
        assert preflight_payload['overall_status'] in {'ok', 'warning'}, preflight.text
        assert preflight_payload['backup_root'].endswith('backups'), preflight.text

        readiness = client.get('/api/v1/ops/release-readiness')
        assert readiness.status_code == 200, readiness.text
        readiness_payload = readiness.json()
        assert readiness_payload['ready_for_paper'] is True, readiness.text
        assert readiness_payload['counts']['positions'] >= 0, readiness.text

        manifest = client.post('/api/v1/ops/backup/manifest')
        assert manifest.status_code == 200, manifest.text
        manifest_payload = manifest.json()
        assert manifest_payload['name'].endswith('.json'), manifest.text
        assert Path(manifest_payload['path']).exists(), manifest.text

        backups = client.get('/api/v1/ops/backups')
        assert backups.status_code == 200, backups.text
        backup_payload = backups.json()
        assert any(item['name'] == manifest_payload['name'] for item in backup_payload), backups.text

        print('[OK] checkpoint 09 smoke test passed')


if __name__ == '__main__':
    main()
