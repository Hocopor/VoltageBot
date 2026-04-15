from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.journal import JournalEntry
from app.models.trade import Order, Position, Trade
from app.services.operations import OperationsService


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeploymentOpsService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.settings = get_settings()

    def _ensure_dirs(self) -> tuple[Path, Path, Path]:
        backup_root = Path(self.settings.backup_root)
        release_root = Path(self.settings.release_root)
        codex_root = Path(self.settings.codex_session_dir)
        backup_root.mkdir(parents=True, exist_ok=True)
        release_root.mkdir(parents=True, exist_ok=True)
        codex_root.mkdir(parents=True, exist_ok=True)
        return backup_root, release_root, codex_root

    def preflight(self) -> dict[str, Any]:
        backup_root, release_root, codex_root = self._ensure_dirs()
        checks: list[dict[str, str]] = []

        def add(name: str, status: str, message: str) -> None:
            checks.append({'name': name, 'status': status, 'message': message})

        database_scheme = urlparse(self.settings.database_url).scheme or 'unknown'
        redis_scheme = urlparse(self.settings.redis_url).scheme or 'unknown'
        add('database_url', 'ok' if bool(self.settings.database_url) else 'error', f'Схема БД: {database_scheme}')
        add('redis_url', 'ok' if bool(self.settings.redis_url) else 'error', f'Схема Redis: {redis_scheme}')
        add('secret_key', 'warning' if self.settings.secret_key == 'change-me' else 'ok', 'SECRET_KEY must be changed for production.' if self.settings.secret_key == 'change-me' else 'SECRET_KEY is customized.')
        add('bybit_credentials', 'ok' if (self.settings.bybit_api_key and self.settings.bybit_api_secret) else 'warning', 'Ключи Bybit настроены.' if (self.settings.bybit_api_key and self.settings.bybit_api_secret) else 'Ключи Bybit не настроены.')
        add('deepseek', 'ok' if bool(self.settings.deepseek_api_key) else 'warning', 'Ключ DeepSeek настроен.' if self.settings.deepseek_api_key else 'Ключ DeepSeek не настроен.')
        add('cloudflare_tunnel', 'ok' if bool(self.settings.cloudflare_tunnel_token) else 'warning', 'Токен Cloudflare Tunnel настроен.' if self.settings.cloudflare_tunnel_token else 'Токен Cloudflare Tunnel не настроен.')
        add('public_base_url', 'ok' if bool(self.settings.public_base_url) else 'warning', 'Публичный base URL настроен.' if self.settings.public_base_url else 'Переменная PUBLIC_BASE_URL пуста.')
        add('backup_root', 'ok' if os.access(backup_root, os.W_OK) else 'error', f'Backup root: {backup_root}')
        add('release_root', 'ok' if os.access(release_root, os.W_OK) else 'error', f'Release root: {release_root}')
        add('codex_session_dir', 'ok' if codex_root.exists() else 'error', f'Каталог сессий Codex: {codex_root}')

        overall = 'ok'
        if any(item['status'] == 'error' for item in checks):
            overall = 'error'
        elif any(item['status'] == 'warning' for item in checks):
            overall = 'warning'

        return {
            'generated_at': utcnow_iso(),
            'environment': self.settings.environment,
            'database_scheme': database_scheme,
            'redis_scheme': redis_scheme,
            'backup_root': str(backup_root),
            'release_root': str(release_root),
            'codex_session_dir': str(codex_root),
            'cloudflare_configured': bool(self.settings.cloudflare_tunnel_token),
            'checks': checks,
            'overall_status': overall,
        }

    def release_readiness(self) -> dict[str, Any]:
        preflight = self.preflight()
        critical_issues: list[str] = []
        warnings: list[str] = []
        score = 100

        for item in preflight['checks']:
            if item['status'] == 'error':
                critical_issues.append(f"{item['name']}: {item['message']}")
                score -= 20
            elif item['status'] == 'warning':
                warnings.append(f"{item['name']}: {item['message']}")
                score -= 7

        state_summary: dict[str, Any] | None = None
        counts = {'orders': 0, 'trades': 0, 'positions': 0, 'journal_entries': 0}
        if self.db is not None:
            state_summary = OperationsService(self.db).system_health()
            counts = {
                'orders': int(self.db.scalar(select(func.count()).select_from(Order)) or 0),
                'trades': int(self.db.scalar(select(func.count()).select_from(Trade)) or 0),
                'positions': int(self.db.scalar(select(func.count()).select_from(Position)) or 0),
                'journal_entries': int(self.db.scalar(select(func.count()).select_from(JournalEntry)) or 0),
            }
            if state_summary['maintenance_mode']:
                warnings.append('System is in maintenance mode.')
                score -= 5
            if state_summary['trading_paused']:
                warnings.append('Trading is paused.')
                score -= 5
            if state_summary['kill_switch_armed']:
                critical_issues.append('Kill switch взведён.')
                score -= 15
            if state_summary['last_live_sync_status'] == 'failed':
                critical_issues.append(f"Last live sync failed: {state_summary['last_live_sync_message']}")
                score -= 15
            if state_summary['open_live_positions'] > 0 and not (self.settings.bybit_api_key and self.settings.bybit_api_secret):
                critical_issues.append('Open live positions exist while Bybit credentials are missing.')
                score -= 20

        score = max(0, min(100, score))
        ready_for_paper = not any(issue.startswith('backup_root') or issue.startswith('release_root') or issue.startswith('database_url') or issue.startswith('secret_key') for issue in critical_issues)
        ready_for_live = ready_for_paper and not critical_issues and bool(self.settings.bybit_api_key and self.settings.bybit_api_secret and self.settings.cloudflare_tunnel_token and self.settings.secret_key != 'change-me')

        return {
            'generated_at': utcnow_iso(),
            'score': score,
            'ready_for_paper': ready_for_paper,
            'ready_for_live': ready_for_live,
            'critical_issues': critical_issues,
            'warnings': warnings,
            'preflight_status': preflight['overall_status'],
            'counts': counts,
            'state': state_summary,
        }

    def list_backup_artifacts(self, limit: int = 50) -> list[dict[str, Any]]:
        backup_root, _, _ = self._ensure_dirs()
        patterns = ('*.json', '*.sql', '*.sql.gz', '*.tar', '*.tar.gz', '*.tgz', '*.zip')
        files: list[Path] = []
        for pattern in patterns:
            files.extend(backup_root.rglob(pattern))
        files = sorted([item for item in files if item.is_file()], key=lambda path: path.stat().st_mtime, reverse=True)
        artifacts: list[dict[str, Any]] = []
        for item in files[:limit]:
            artifacts.append(
                {
                    'name': item.name,
                    'path': str(item),
                    'size_bytes': item.stat().st_size,
                    'modified_at': datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc).isoformat(),
                    'kind': self._artifact_kind(item.name),
                }
            )
        return artifacts

    def write_backup_manifest(self, source: str = 'manual') -> dict[str, Any]:
        backup_root, _, codex_root = self._ensure_dirs()
        manifests_dir = backup_root / 'manifests'
        manifests_dir.mkdir(parents=True, exist_ok=True)
        readiness = self.release_readiness()
        state = OperationsService(self.db).system_health() if self.db is not None else None
        manifest = {
            'generated_at': utcnow_iso(),
            'source': source,
            'project': self.settings.project_name,
            'environment': self.settings.environment,
            'database_url_scheme': urlparse(self.settings.database_url).scheme or 'unknown',
            'redis_url_scheme': urlparse(self.settings.redis_url).scheme or 'unknown',
            'cloudflare_configured': bool(self.settings.cloudflare_tunnel_token),
            'public_base_url': self.settings.public_base_url,
            'codex_session_dir': str(codex_root),
            'release_readiness': readiness,
            'state': state,
        }
        payload = json.dumps(manifest, ensure_ascii=False, indent=2)
        digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        filename = f"runtime-manifest-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        path = manifests_dir / filename
        path.write_text(payload, encoding='utf-8')
        return {
            'name': filename,
            'path': str(path),
            'size_bytes': path.stat().st_size,
            'sha256': digest,
            'generated_at': manifest['generated_at'],
            'source': source,
        }

    @staticmethod
    def _artifact_kind(name: str) -> str:
        lower = name.lower()
        if lower.endswith('.json'):
            return 'manifest'
        if lower.endswith('.sql') or lower.endswith('.sql.gz'):
            return 'database'
        if lower.endswith('.tar') or lower.endswith('.tar.gz') or lower.endswith('.tgz'):
            return 'archive'
        if lower.endswith('.zip'):
            return 'zip'
        return 'file'
