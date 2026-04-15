from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import get_settings


class CodexAuthError(RuntimeError):
    pass


class CodexAuthService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session_dir = Path(self.settings.codex_session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / 'session.json'
        self.pending_file = self.session_dir / 'pending_login.json'

    def status(self) -> dict[str, Any]:
        session = self._read_json(self.session_file)
        pending = self._read_json(self.pending_file)
        if not session:
            return {
                'connected': False,
                'mode': self.settings.codex_login_mode,
                'message': 'Сессия Codex ещё не подключена.',
                'pending_login': bool(pending),
                'pending_login_id': pending.get('login_id') if pending else None,
                'expires_at': pending.get('expires_at') if pending else None,
            }
        session['pending_login'] = bool(pending)
        session['pending_login_id'] = pending.get('login_id') if pending else None
        session['expires_at'] = pending.get('expires_at') if pending else session.get('expires_at')
        return session

    def start_browser_login(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        login_id = uuid4().hex
        expires_at = (now + timedelta(minutes=15)).isoformat()
        payload = {
            'login_id': login_id,
            'created_at': now.isoformat(),
            'expires_at': expires_at,
            'mode': self.settings.codex_login_mode,
            'auth_url': f'/api/v1/auth/codex/browser/callback?login_id={login_id}&account_label=browser-linked-user',
            'callback_path': f'/api/v1/auth/codex/browser/callback?login_id={login_id}&account_label=browser-linked-user',
            'message': 'Откройте callback-путь в браузере после завершения входа Codex. Полученная сессия будет сохранена локально.',
        }
        self.pending_file.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return payload

    def complete_browser_login(self, login_id: str, account_label: str, external_user_id: str | None = None) -> dict[str, Any]:
        pending = self._require_pending(login_id)
        session_id = uuid4().hex[:20]
        now = datetime.now(timezone.utc)
        payload = {
            'connected': True,
            'mode': self.settings.codex_login_mode,
            'session_id': session_id,
            'account_label': account_label,
            'external_user_id': external_user_id,
            'connected_at': now.isoformat(),
            'last_sync_at': now.isoformat(),
            'message': 'Сессия Codex сохранена локально и переживёт перезапуск, пока сохраняется data-volume.',
        }
        self.session_file.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        self._clear_pending(pending)
        return payload

    def complete_browser_callback(self, login_id: str, account_label: str | None = None) -> dict[str, Any]:
        label = account_label or 'browser-linked-user'
        return self.complete_browser_login(login_id=login_id, account_label=label)

    def disconnect(self) -> dict[str, Any]:
        if self.session_file.exists():
            self.session_file.unlink()
        if self.pending_file.exists():
            self.pending_file.unlink()
        return {
            'connected': False,
            'mode': self.settings.codex_login_mode,
            'message': 'Сессия Codex удалена из локального хранилища.',
            'pending_login': False,
        }

    def save_placeholder_session(self, account_label: str) -> dict[str, Any]:
        payload = {
            'connected': True,
            'mode': self.settings.codex_login_mode,
            'session_id': f'placeholder-{uuid4().hex[:12]}',
            'account_label': account_label,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'last_sync_at': datetime.now(timezone.utc).isoformat(),
            'message': 'Тестовая сессия сохранена. В production замените её на реальный браузерный вход или синхронизацию CLI-сессии.',
        }
        self.session_file.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return payload

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding='utf-8'))

    def _require_pending(self, login_id: str) -> dict[str, Any]:
        pending = self._read_json(self.pending_file)
        if not pending:
            raise CodexAuthError('Ожидаемый браузерный вход Codex не найден.')
        if pending.get('login_id') != login_id:
            raise CodexAuthError('login_id Codex не совпадает с ожидающим браузерным входом.')
        expires_at = pending.get('expires_at')
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                self._clear_pending(pending)
                raise CodexAuthError('Срок действия ожидающего браузерного входа Codex истёк.')
        return pending

    def _clear_pending(self, pending: dict[str, Any] | None = None) -> None:
        if self.pending_file.exists():
            self.pending_file.unlink()
