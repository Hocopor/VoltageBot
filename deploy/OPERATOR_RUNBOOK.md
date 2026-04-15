# VOLTAGE Operator Runbook

## Daily operator checklist
1. Open **Operations** and confirm:
   - `maintenance_mode = false`
   - `trading_paused = false` only when trading is intended
   - `kill_switch_armed = false` unless emergency hold is required
2. Check **Release** page:
   - readiness score
   - critical issues
   - recommended mode
3. Confirm balances and working limits for spot/futures.
4. Confirm selected pairs for the intended market(s).
5. Confirm Codex session and DeepSeek status if AI workflows are expected.
6. For live trading, run a manual **reconcile live** before enabling autonomous cycles.

## Safe startup
1. Ensure `.env` is present and secrets are populated.
2. Run `python scripts/preflight_check.py`.
3. Run `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.
4. Wait for `/healthz` to report status `ok`.
5. Open **Release** and **Operations** pages to confirm runtime state.

## Safe shutdown
1. Pause trading in **Operations**.
2. If required, run **Flatten paper** or **Flatten live + arm kill switch**.
3. Stop the stack with `./scripts/stop_prod_stack.sh`.
4. Generate runtime manifest and backup artifacts.

## Incident handling
### Exchange/API mismatch
- Run **reconcile live**.
- Inspect `flatten runs`, `recovery runs`, and latest system events.
- Keep `trading_paused = true` until local state matches exchange state.

### Unintended live exposure
- Run **Flatten live + arm kill switch**.
- Verify the exchange no longer shows live positions.
- Reconcile again.
- Keep kill switch armed until root cause is understood.

### Restart recovery
- Restart stack.
- Wait for startup recovery to complete.
- Open **Operations** and verify `last_recovery_at` and `last_startup_at`.

## Go-live gate
Go live only when:
- Release page recommends `live`.
- No critical issues remain.
- Backup artifacts exist.
- Bybit credentials and Cloudflare tunnel are configured.
- Codex persistence and DeepSeek configuration have been tested if required.
