# VOLTAGE Release Acceptance

## Purpose
This document describes the final acceptance flow for the production-ready package.

## Acceptance flow
1. Run `python scripts/preflight_check.py`
2. Run backend smoke test for checkpoint 10.
3. Run `python scripts/run_release_acceptance.py`
4. Open **Release** page and verify:
   - overall status
   - recommended mode
   - readiness score
   - critical issues / warnings
5. Confirm generated acceptance artifacts in the configured `RELEASE_ROOT`.
6. Package a runtime snapshot with `./scripts/package_release_snapshot.sh` if you need an archival bundle.

## Minimum acceptance bar
- Backend smoke test passes.
- Frontend production build passes.
- Release acceptance artifacts are generated successfully.
- `ready_for_paper = true`.
- `ready_for_live = true` before first real-money launch.

## Recommended rollout path
1. Historical verification
2. Paper trading with chosen symbols and realistic balances
3. Limited live rollout with constrained working balance
4. Full live operation only after stable reconcile/recovery behavior is observed
