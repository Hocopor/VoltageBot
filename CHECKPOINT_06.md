# CHECKPOINT 06 — lifecycle, recovery, richer journal and analytics

## Что добавлено
- lifecycle sync для открытых позиций;
- таблица событий жизненного цикла позиции (`position_lifecycle_events`);
- enriched journal fields:
  - `close_reason`
  - `hold_minutes`
  - `best_price`
  - `worst_price`
  - `mfe_pnl`
  - `mae_pnl`
  - `strategy_scenario`
  - `compliance_score`
  - `review_summary`
- journal summary endpoint;
- recovery scan и recovery history;
- автоматический recovery scan при startup;
- расширенная analytics overview:
  - by direction
  - by close reason
  - by weekday / hour
  - yearly pnl
  - tp hit distribution
  - streaks
  - average hold minutes
  - average compliance score
- frontend updates for Orders, Journal, Analytics, Operations, Dashboard.

## Новые API
- `POST /api/v1/trade/lifecycle/sync`
- `GET /api/v1/trade/lifecycle/events`
- `GET /api/v1/journal/summary`
- `POST /api/v1/ops/recovery/run`
- `GET /api/v1/ops/recovery/runs`

## Проверка
- `python -m compileall app`
- `python smoke_test_checkpoint_06.py`
- `npm ci`
- `npm run build`

## Примечание
Этот чекпоинт усиливает эксплуатационный и аналитический слой проекта, не заменяя последующие этапы live lifecycle manager и полного hardening под production.
