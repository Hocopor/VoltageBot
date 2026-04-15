# VOLTAGE production deploy notes

## Stack
- docker compose base: `docker-compose.yml`
- docker compose prod override: `docker-compose.prod.yml`
- cloudflared tunnel example: `deploy/cloudflared/config.example.yml`

## Recommended boot sequence
1. Copy `.env.example` to `.env` and fill all secrets.
2. Run `scripts/preflight_check.py`.
3. Start stack with `scripts/run_prod_stack.sh`.
4. Verify `/healthz`, `/api/v1/ops/preflight`, `/api/v1/ops/release-readiness`.
5. Create first manifest with `scripts/create_runtime_manifest.sh`.

## Recommended runtime checks
- preflight overall status must not be `error`
- release readiness score should be reviewed before live trading
- `SECRET_KEY` must be customized
- Bybit credentials must be set before live mode
- Cloudflare token and public URL must be set before remote operation

## Backups
- use `scripts/backup_runtime.sh` for database and runtime snapshot scaffolding
- manifests are stored under `${BACKUP_ROOT}/manifests`
- restore helpers are in `scripts/restore_runtime.sh`
