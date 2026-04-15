# CHECKPOINT 09 — production deploy hardening

## Scope
This checkpoint focuses on production deployment safety and release hardening.

## Added
- backend deployment ops service:
  - preflight checks
  - release readiness scoring
  - backup artifact listing
  - runtime backup manifest generation
- new ops endpoints:
  - `GET /api/v1/ops/preflight`
  - `GET /api/v1/ops/release-readiness`
  - `GET /api/v1/ops/backups`
  - `POST /api/v1/ops/backup/manifest`
- `/healthz` now includes readiness data
- frontend operations page extended with:
  - preflight summary
  - readiness score
  - blockers and warnings
  - backup artifact view
  - manifest generation
- production deployment assets:
  - `docker-compose.prod.yml`
  - `deploy/cloudflared/config.example.yml`
  - `deploy/PRODUCTION_DEPLOY.md`
  - `scripts/preflight_check.py`
  - `scripts/run_prod_stack.sh`
  - `scripts/stop_prod_stack.sh`
  - `scripts/create_runtime_manifest.sh`
  - `scripts/backup_runtime.sh`
  - `scripts/restore_runtime.sh`

## Validation
- backend compileall
- backend smoke test for checkpoint 09
- frontend production build

## Purpose
This checkpoint is intended to make the project substantially closer to real VPS deployment and safer day-to-day operation, while leaving final release acceptance for the last checkpoint.
