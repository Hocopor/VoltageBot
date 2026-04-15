#!/usr/bin/env python3
from getpass import getpass
import sys

sys.path.insert(0, '/app') if False else None

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(ROOT))

from app.services.admin_auth import AdminAuthService

password = sys.argv[1] if len(sys.argv) > 1 else getpass('Введите пароль: ')
print(AdminAuthService.hash_password(password))
