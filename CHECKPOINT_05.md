# CHECKPOINT 05 — Operations, Reconciliation, Recovery Controls

## Что добавлено
- Операционный контур `ops` для production-эксплуатации.
- Singleton `SystemState`:
  - `maintenance_mode`
  - `trading_paused`
  - `kill_switch_armed`
  - `boot_count`
  - `last_startup_at`
  - `last_shutdown_at`
  - `last_bot_heartbeat_at`
  - `last_reconcile_at`
  - `last_live_sync_status`
  - `last_live_sync_message`
- История reconcile-прогонов `ReconcileRun`.
- Startup/shutdown markers в backend lifespan.
- Heartbeat фонового bot-loop.
- Live reconciliation:
  - wallet balances -> `ExchangeBalance`
  - live orders -> локальные `Order`
  - live futures positions -> локальные `Trade` + `Position`
  - закрытие устаревших локальных live-позиций, исчезнувших на бирже
- Операционные API:
  - `GET /api/v1/ops/state`
  - `PUT /api/v1/ops/state`
  - `POST /api/v1/ops/reconcile/live`
  - `GET /api/v1/ops/reconcile/runs`
  - `POST /api/v1/ops/flatten-paper`
- Защитные блокировки исполнения:
  - manual execute блокируется при `maintenance_mode`
  - manual execute блокируется при `trading_paused`
  - manual execute блокируется при `kill_switch_armed`
- Bot runtime теперь учитывает operations controls.
- Новый frontend-раздел **Operations**.
- Dashboard дополнен operational state.
- Расширенный `/healthz` с runtime-state payload.

## Что проверено
- `python -m compileall app smoke_test_checkpoint_04.py`
- `python smoke_test_checkpoint_05.py`
- `npm ci`
- `npm run build`

## Smoke test checkpoint 05
Проверяет:
- health endpoint;
- initial ops state;
- pause trading -> execution blocked;
- resume trading -> execution allowed;
- paper position creation;
- flatten paper positions;
- reconcile runs list endpoint.

## Ограничения этого чекпоинта
- Полный live emergency flatten на Bybit ещё не реализован.
- Reconciliation сейчас фокусируется на wallet/orders/futures positions и не покрывает весь live lifecycle.
- WebSocket-streaming и real-time reconciliation ещё не добавлены.

## Следующий логичный этап
Checkpoint 06:
- live order lifecycle manager,
- advanced reconciliation,
- deeper trader journal,
- richer analytics and daily/monthly/yearly breakdown,
- устойчивость рестартов и recovery сценарии.
