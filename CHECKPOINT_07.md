# CHECKPOINT 07 — live lifecycle manager + emergency flatten

## Что добавлено
- Deep live lifecycle sync для live-ордера/позициий.
- Обновление локальных live orders по данным Bybit (`open` + recent closed).
- Авто-адоптирование live futures positions из состояния биржи.
- Закрытие локальных live positions, если биржа уже flat.
- Protective sync для futures positions через `set trading stop`.
- Live close action из UI/API теперь отправляет реальный close-order, а не закрывает локально “вслепую”.
- Emergency live flatten:
  - cancel all orders;
  - submit reduce-only market closes по открытым futures positions;
  - отдельная история flatten runs;
  - вариант `flatten live + arm kill switch`.
- Расширено системное состояние:
  - `last_lifecycle_sync_at`
  - `last_flatten_at`
  - `last_flatten_status`
  - `last_flatten_message`
- Расширены модели `Order` и `Position` полями exchange/runtime sync.
- Обновлён frontend:
  - Orders page показывает live lifecycle summary;
  - Operations page показывает flatten history и live flatten actions;
  - Dashboard показывает lifecycle/flatten operational state.

## Новые/расширенные API
- `POST /api/v1/trade/live/lifecycle`
- `POST /api/v1/ops/flatten/live`
- `POST /api/v1/ops/flatten/live/kill-switch`
- `GET /api/v1/ops/flatten/runs`

## Что проверено
- `python -m compileall app`
- `python smoke_test_checkpoint_07.py`
- `npm ci`
- `npm run build`

## Ограничения этого чекпоинта
- Реальный WebSocket-streaming Bybit ещё не добавлен.
- Full TP ladder management on-exchange ещё не завершён.
- Live spot flatten пока не реализован как отдельный биржевой контур.
- Real-time order state всё ещё подтверждается polling/sync, а не streaming.

## Следующий логичный этап
- checkpoint 08:
  - Codex OAuth/browser persistence;
  - deeper AI review/explainability;
  - journal closer to CScalp layout;
  - stronger prod deployment/hardening layer.
