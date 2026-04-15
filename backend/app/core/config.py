from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    project_name: str = 'VOLTAGE'
    environment: str = 'production'
    api_v1_prefix: str = '/api/v1'
    backend_host: str = '0.0.0.0'
    backend_port: int = 8000
    secret_key: str = 'change-me'
    allowed_origins: list[str] = ['http://localhost:8080', 'http://localhost']

    database_url: str = 'postgresql+psycopg://voltage:voltage_password@postgres:5432/voltage'
    redis_url: str = 'redis://redis:6379/0'
    postgres_db: str = 'voltage'
    postgres_user: str = 'voltage'
    postgres_password: str = 'voltage_password'

    bybit_api_base_url: str = 'https://api.bybit.com'
    bybit_api_key: str = ''
    bybit_api_secret: str = ''
    bybit_recv_window: int = 5000
    bybit_timeout_seconds: int = 20

    deepseek_base_url: str = 'https://api.deepseek.com'
    deepseek_api_key: str = ''
    deepseek_model: str = 'deepseek-chat'

    codex_login_mode: str = 'chatgpt'
    codex_session_dir: str = '/data/codex'

    cloudflare_tunnel_token: str = ''
    cloudflare_tunnel_hostname: str = ''
    public_base_url: str = ''
    frontend_app_title: str = 'VOLTAGE'

    backup_root: str = '/data/backups'
    release_root: str = '/data/releases'


@lru_cache
def get_settings() -> Settings:
    return Settings()
