# CHECKPOINT 10 — release acceptance / final production package

## Scope
This checkpoint finalizes the implementation with release-acceptance tooling, operator runbooks, release artifacts, and a final production-facing checkpoint package.

## Added
- backend release manager service
- new ops endpoints:
  - `GET /api/v1/ops/release-report`
  - `POST /api/v1/ops/release-acceptance/run`
  - `GET /api/v1/ops/releases`
- frontend **Release** page
- release acceptance artifact generation in `RELEASE_ROOT/acceptance`
- scripts:
  - `scripts/run_release_acceptance.py`
  - `scripts/package_release_snapshot.sh`
- deploy docs:
  - `deploy/OPERATOR_RUNBOOK.md`
  - `deploy/RELEASE_ACCEPTANCE.md`
- backend smoke test for checkpoint 10

## Validation
- backend compileall
- backend smoke test for checkpoint 10
- release acceptance script
- frontend production build

## Purpose
This is the final release-acceptance checkpoint intended to make the package operator-friendly and ready for controlled deployment on the target VPS environment.
