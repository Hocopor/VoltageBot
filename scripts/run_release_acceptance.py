#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    backend_root = project_root / 'backend'
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    os.environ.setdefault('DATABASE_URL', 'sqlite:////tmp/voltage_release_acceptance.db')
    os.environ.setdefault('BACKUP_ROOT', '/tmp/voltage_backups')
    os.environ.setdefault('RELEASE_ROOT', '/tmp/voltage_releases')
    os.environ.setdefault('CODEX_SESSION_DIR', '/tmp/voltage_codex')
    os.environ.setdefault('SECRET_KEY', 'release-acceptance-script')

    import app.models  # noqa: F401
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.seed import seed_runtime_state
    from app.services.release_manager import ReleaseManagerService

    Base.metadata.create_all(bind=engine)
    seed_runtime_state()
    with SessionLocal() as db:
        result = ReleaseManagerService(db).run_release_acceptance(trigger='script')
    print('[OK] release acceptance generated')
    print(f"status={result['overall_status']} mode={result['recommended_mode']} score={result['score']}")
    print(f"json={result['json_artifact']['path']}")
    print(f"markdown={result['markdown_artifact']['path']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
