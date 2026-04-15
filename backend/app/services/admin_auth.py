from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import get_settings


class AdminAuthError(Exception):
    pass


class AdminAuthService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.auth_login and self.settings.auth_password_hash)

    def login(self, username: str, password: str) -> str:
        if not self.is_configured():
            raise AdminAuthError('В .env не настроены AUTH_LOGIN и AUTH_PASSWORD_HASH.')
        if username != self.settings.auth_login:
            raise AdminAuthError('Неверный логин или пароль.')
        if not self.verify_password(password, self.settings.auth_password_hash):
            raise AdminAuthError('Неверный логин или пароль.')
        return self.create_session_token(username)

    def session_cookie_name(self) -> str:
        return self.settings.auth_cookie_name

    def cookie_is_secure(self) -> bool:
        return self.settings.public_base_url.startswith('https://')

    def create_session_token(self, username: str) -> str:
        expires_at = datetime.now(UTC) + timedelta(hours=self.settings.auth_session_ttl_hours)
        payload = {
            'sub': username,
            'exp': int(expires_at.timestamp()),
        }
        payload_b64 = self._b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        signature = hmac.new(self.settings.secret_key.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        return f'{payload_b64}.{signature}'

    def read_session(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        try:
            payload_b64, signature = token.split('.', 1)
        except ValueError:
            return None
        expected = hmac.new(self.settings.secret_key.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return None
        try:
            payload = json.loads(self._b64decode(payload_b64).decode('utf-8'))
        except Exception:
            return None
        exp = payload.get('exp')
        if not isinstance(exp, int) or exp < int(datetime.now(UTC).timestamp()):
            return None
        username = payload.get('sub')
        if not isinstance(username, str) or not username:
            return None
        return {
            'authenticated': True,
            'username': username,
            'expires_at': datetime.fromtimestamp(exp, UTC).isoformat(),
        }

    @staticmethod
    def hash_password(password: str, iterations: int = 600000) -> str:
        salt = secrets.token_urlsafe(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
        return f'pbkdf2_sha256${iterations}${salt}${base64.urlsafe_b64encode(digest).decode("ascii")}'

    @staticmethod
    def verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, iterations_raw, salt, digest_b64 = encoded.split('$', 3)
        except ValueError:
            return False
        if algorithm != 'pbkdf2_sha256':
            return False
        try:
            iterations = int(iterations_raw)
        except ValueError:
            return False
        computed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
        expected = base64.urlsafe_b64decode(AdminAuthService._pad_b64(digest_b64))
        return hmac.compare_digest(computed, expected)

    @staticmethod
    def _b64encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')

    @staticmethod
    def _b64decode(data: str) -> bytes:
        return base64.urlsafe_b64decode(AdminAuthService._pad_b64(data))

    @staticmethod
    def _pad_b64(data: str) -> str:
        return data + '=' * (-len(data) % 4)
