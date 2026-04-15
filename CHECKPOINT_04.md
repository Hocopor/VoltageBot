# CHECKPOINT 04 — Bot Runtime, Cycle Automation, System Events, Hardening Scripts

## Что реализовано

- Добавлен `bot runtime` с собственной конфигурацией.
- Добавлен `manual run cycle` endpoint для немедленного запуска сканирования выбранных пар.
- Добавлен фоновый `bot loop`, который периодически проверяет конфигурацию и при включённом боте запускает цикл автоматически.
- Реализован цикл сканирования:
  - чтение текущего runtime режима;
  - чтение выбранных пар;
  - проверка открытых позиций;
  - оценка VOLTAGE-сигналов;
  - автозапуск сделок в `paper`/`live` режимах по настройкам безопасности.
- Добавлены сущности:
  - `BotConfig`;
  - `BotRun`;
  - `SystemEvent`.
- Добавлены API разделы:
  - `/api/v1/bot/config`;
  - `/api/v1/bot/cycle`;
  - `/api/v1/bot/runs`;
  - `/api/v1/bot/events`.
- Добавлена новая страница UI: `Bot`.
- На `Dashboard` добавлен блок состояния бота и график equity curve.
- В `Analytics` добавлен простой встроенный график equity curve.
- Добавлены скрипты резервного копирования и восстановления БД:
  - `scripts/backup_db.sh`
  - `scripts/restore_db.sh`
- Добавлен smoke test чекпоинта: `backend/smoke_test_checkpoint_04.py`.

## Что проверено

- Backend компилируется без синтаксических ошибок.
- Ручной запуск bot cycle создаёт bot run и system events.
- При выбранной паре `BTCUSDT` в `paper` режиме bot cycle может создать позицию.
- Frontend собирается в production build.
- Smoke test чекпоинта проходит на чистой sqlite базе.

## Ограничения этапа

- Реальный browser callback flow для Codex всё ещё не доведён до полноценного production OAuth-потока.
- Live order lifecycle manager ещё не завершён на уровне полного частичного управления TP ladder на бирже.
- Recovery после аварийного падения ещё не покрывает все продовые сценарии reconciliation.
- Графики в UI пока реализованы как встроенные lightweight SVG-визуализации, без полноценной charting-библиотеки.

## Следующий логический этап

- расширение live order lifecycle manager;
- более глубокий reconciliation layer;
- углубление дневника сделок;
- release hardening и deployment polishing.
