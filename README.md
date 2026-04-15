# VOLTAGE

Checkpoint 10 completes the release acceptance layer for VOLTAGE and packages the project as a final production-oriented checkpoint.

## Included
- FastAPI backend
- React/Vite frontend
- Docker composition with postgres, redis and cloudflared
- Bybit public + signed client
- Paper execution engine with stop-loss, TP ladder and trailing stop
- Strategy engine for VOLTAGE evaluation
- Historical backtest engine with run/trade persistence
- Bot runtime automation with cycle control and event logs
- Journal AI review via DeepSeek with fallback mode
- Live lifecycle sync, recovery, flatten and operations controls
- Production preflight, release readiness and backup manifest endpoints
- Codex browser persistence and DeepSeek integration checks
- Final release acceptance report generation and operator runbooks

## Quick start
1. Copy `.env.example` to `.env`
2. Fill secrets and production paths
3. Run `python scripts/preflight_check.py`
4. Run `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
5. Open the frontend through the local web port or Cloudflare Tunnel
6. Open **Release** page and run release acceptance

## Final release endpoints
- `/healthz`
- `/api/v1/ops/preflight`
- `/api/v1/ops/release-readiness`
- `/api/v1/ops/release-report`
- `/api/v1/ops/release-acceptance/run`
- `/api/v1/ops/releases`
- `/api/v1/ops/backup/manifest`
- `/api/v1/ops/backups`

## Operator docs
- `deploy/PRODUCTION_DEPLOY.md`
- `deploy/OPERATOR_RUNBOOK.md`
- `deploy/RELEASE_ACCEPTANCE.md`

## Validation
- `python backend/smoke_test_checkpoint_10.py`
- `python scripts/run_release_acceptance.py`
- `npm run build` in `frontend`

## Notes
- For local smoke tests without postgres, override `DATABASE_URL` with a sqlite URL.
- The project is intended for a controlled rollout path: historical → paper → limited live → full live.
- Final live use still depends on real credentials, deployment correctness, and operator validation on the target VPS.
