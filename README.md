# VOLTAGE

**VOLTAGE** — персональная production-oriented система для алгоритмической крипто-торговли на **Bybit Mainnet** с поддержкой:

- **реальной торговли**
- **бумажной торговли**
- **торговли на исторических данных**
- **ИИ-анализа сделок**
- **журнала трейдера**
- **операционного контроля**
- **production-деплоя на VPS через Docker и Cloudflare Tunnel**

Проект создавался как **личная рабочая платформа**, а не как SaaS, не как командный сервис и не как MVP-демо.  
Архитектура ориентирована на **одного владельца**, развёртывание на **Ubuntu 24 VPS**, управление через веб-интерфейс и запуск через **Docker Compose**.

---

## Содержание

- [Что умеет проект](#что-умеет-проект)
- [Ключевые возможности](#ключевые-возможности)
- [Торговые режимы](#торговые-режимы)
- [Стратегия](#стратегия)
- [Технологический стек](#технологический-стек)
- [Архитектура проекта](#архитектура-проекта)
- [Структура репозитория](#структура-репозитория)
- [Интерфейс](#интерфейс)
- [Быстрый старт](#быстрый-старт)
- [Запуск в production](#запуск-в-production)
- [Переменные окружения](#переменные-окружения)
- [Проверка работоспособности](#проверка-работоспособности)
- [Операционные сценарии](#операционные-сценарии)
- [Статус готовности](#статус-готовности)
- [Ограничения и важные замечания](#ограничения-и-важные-замечания)
- [Документация в проекте](#документация-в-проекте)

---

## Что умеет проект

VOLTAGE объединяет в одном приложении:

- подключение к **Bybit Mainnet**
- получение рыночных данных
- анализ рынка по стратегии **VOLTAGE**
- ручной и автоматический запуск торговых циклов
- ведение ордеров, сделок и позиций
- расчёт **реализованного** и **нереализованного PnL**
- управление **stop-loss**, **take-profit** и частичными фиксациями
- запуск **historical backtest**
- ведение **дневника трейдера**
- **AI review** завершённых сделок
- аналитику по результатам торговли
- операционный контроль:
  - maintenance mode
  - trading pause
  - kill switch
  - reconcile
  - recovery
  - flatten
- production-ready контур для деплоя через Docker

---

## Ключевые возможности

### 1. Несколько режимов торговли
Поддерживаются три независимых режима:

- **Live** — работа с реальными ордерами на Bybit Mainnet
- **Paper** — симуляция торговли без реальных ордеров
- **Historical** — торговля на исторических данных через backtest engine

### 2. Разделение спота и фьючерсов
Поддерживается:
- **spot** — long
- **futures** — long и short

Для спота и фьючерсов отдельно настраиваются:
- рабочий баланс
- список торговых пар
- логика исполнения и мониторинга

### 3. Обязательные защитные механизмы
Система проектировалась с обязательной защитной логикой:
- stop-loss
- TP1 / TP2 / TP3
- перенос стопа в безубыток после TP1
- trailing logic для остатка позиции
- lifecycle sync и reconcile

### 4. Журнал и аналитика
В проект встроены:
- журнал сделок
- summary по журналу
- review завершённых сделок
- AI summary по аналитике
- разбивка по направлениям, времени, причинам закрытия, streaks, hold time и другим срезам

### 5. Продовый операционный контур
В проект добавлены:
- preflight
- release readiness
- release acceptance
- backup manifest
- runtime backups
- recovery runs
- flatten runs
- release reports

---

## Торговые режимы

### Live
Боевой режим с реальными ордерами на Bybit Mainnet.

Используется для:
- реального исполнения сделок
- live sync ордеров и позиций
- reconcile локального состояния с биржей
- emergency flatten и kill-switch сценариев

### Paper
Безопасный режим симуляции торговли.

Используется для:
- тестов торговой логики
- прогона бота на “боевых” сценариях без денег
- проверки stop/take и lifecycle логики
- теста стратегии перед live

### Historical
Исторический режим.

Используется для:
- запуска backtests
- оценки качества стратегии
- анализа результатов по разным периодам и парам
- проверки статистики до реального запуска

---

## Стратегия

В проекте заложен отдельный **strategy engine**, который работает как нормативный слой торговой логики.

Он включает:
- регистрацию стратегии
- evaluation
- explainability
- журнал решений
- AI explanation по решениям

В документации проекта стратегия **VOLTAGE** зафиксирована как отдельный нормативный блок.  
README не заменяет её и не должен считаться полным формальным описанием стратегии.

---

## Технологический стек

### Backend
- **FastAPI**
- **SQLAlchemy 2**
- **Pydantic Settings**
- **httpx**
- **psycopg**
- **Uvicorn**

### Frontend
- **React 18**
- **TypeScript**
- **Vite**
- **React Router**

### Infrastructure
- **Docker**
- **Docker Compose**
- **PostgreSQL**
- **Redis**
- **Nginx**
- **Cloudflare Tunnel**

### Integrations
- **Bybit V5 API**
- **DeepSeek API**
- **Codex browser session persistence**

---

## Архитектура проекта

Проект разделён на несколько основных контуров:

### Backend API
Отвечает за:
- настройки
- пары
- балансы
- торговое исполнение
- стратегию
- журнал
- аналитику
- backtests
- bot runtime
- operations
- release acceptance

### Frontend
Веб-интерфейс для:
- мониторинга системы
- настройки пар
- просмотра ордеров, сделок и позиций
- управления ботом
- запуска backtests
- просмотра аналитики
- управления интеграциями
- release / operations контроля

### Execution Layer
Включает:
- paper execution engine
- live execution
- lifecycle sync
- live reconcile
- close / flatten logic

### Strategy Layer
Включает:
- strategy registry
- evaluate
- decision persistence
- explanation layer

### Operations / Release Layer
Включает:
- preflight
- release readiness
- release report
- acceptance run
- backup manifest
- recovery run
- flatten run

---

## Структура репозитория

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── smoke_test_checkpoint_*.py
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── deploy/
│   ├── PRODUCTION_DEPLOY.md
│   ├── OPERATOR_RUNBOOK.md
│   ├── RELEASE_ACCEPTANCE.md
│   └── cloudflared/
├── scripts/
│   ├── run_prod_stack.sh
│   ├── stop_prod_stack.sh
│   ├── backup_runtime.sh
│   ├── restore_runtime.sh
│   ├── create_runtime_manifest.sh
│   ├── run_release_acceptance.py
│   └── preflight_check.py
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── CHECKPOINT_*.md
```

---

## Интерфейс

Во frontend доступны основные разделы:

- **Dashboard**
- **Pairs**
- **Orders**
- **Strategy**
- **Backtests**
- **Bot**
- **Operations**
- **Journal**
- **Analytics**
- **Integrations**
- **Release**
- **Settings**

### Dashboard
Сводка по системе, операциям, equity и состоянию бота.

### Pairs
Выбор торговых пар отдельно для spot и futures.

### Orders
Просмотр ордеров, сделок, позиций, lifecycle events, PnL.

### Strategy
Оценка стратегии, журнал решений, explainability.

### Backtests
Запуск historical run и просмотр результатов.

### Bot
Настройка бота, запуск циклов, просмотр bot runs и system events.

### Operations
Операционный контроль:
- state
- reconcile
- recovery
- flatten
- preflight
- backups

### Journal
Записи сделок, review, summary.

### Analytics
Агрегаты, equity curve, breakdown-метрики, AI summary.

### Integrations
Статус DeepSeek и Codex, browser session flow.

### Release
Release readiness, release report, acceptance run.

### Settings
Runtime configuration и параметры окружения внутри приложения.

---

## Быстрый старт

### Требования
- **Docker Engine**
- **Docker Compose plugin**
- VPS или локальная машина
- Linux/macOS/WSL2 рекомендуется
- для live:
  - Bybit API key
  - Bybit API secret
- для AI:
  - DeepSeek API key
- для внешнего доступа:
  - Cloudflare Tunnel token

### 1. Склонировать репозиторий
```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd <ПАПКА_ПРОЕКТА>
```

### 2. Создать `.env`
```bash
cp .env.example .env
nano .env
```

### 3. Заполнить переменные окружения
Минимально:
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `PUBLIC_BASE_URL`

Для Cloudflare:
- `CLOUDFLARE_TUNNEL_TOKEN`

Для live:
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

Для AI:
- `DEEPSEEK_API_KEY`

### 4. Поднять стек
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 5. Проверить backend
```bash
curl http://127.0.0.1:8000/healthz
```

### 6. Открыть UI
Либо локально:
```text
http://<IP_СЕРВЕРА>:8080
```

Либо через Cloudflare Tunnel:
```text
https://<ТВОЙ_ПОДДОМЕН>
```

---

## Запуск в production

Рекомендуемый production-сценарий:

1. Подготовить VPS на **Ubuntu 24**
2. Установить Docker Engine и Docker Compose plugin
3. Распаковать проект
4. Создать `.env`
5. Заполнить production-переменные
6. Поднять стек
7. Проверить:
   - `/healthz`
   - Operations
   - Release
   - balances
   - pair selections
8. Сначала прогнать:
   - historical
   - paper
9. Только потом переходить к live

### Production-команда
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Скрипты проекта
```bash
./scripts/run_prod_stack.sh
./scripts/stop_prod_stack.sh
./scripts/backup_runtime.sh
./scripts/restore_runtime.sh
./scripts/create_runtime_manifest.sh
```

---

## Переменные окружения

Главный шаблон:
- `.env.example`

Ключевые переменные:

### Core
- `PROJECT_NAME`
- `ENVIRONMENT`
- `API_V1_PREFIX`
- `SECRET_KEY`

### Database / Redis
- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_URL`

### Bybit
- `BYBIT_API_BASE_URL`
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_RECV_WINDOW`
- `BYBIT_TIMEOUT_SECONDS`

### DeepSeek
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`

### Codex
- `CODEX_LOGIN_MODE`
- `CODEX_SESSION_DIR`

### Cloudflare
- `CLOUDFLARE_TUNNEL_TOKEN`
- `CLOUDFLARE_TUNNEL_HOSTNAME`
- `PUBLIC_BASE_URL`

### Runtime storage
- `BACKUP_ROOT`
- `RELEASE_ROOT`

Для подробного описания каждой строки `.env` рекомендуется использовать отдельный env guide.

---

## Проверка работоспособности

### Backend health
```bash
curl http://127.0.0.1:8000/healthz
```

### Compose config check
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

### Backend smoke-test
```bash
cd backend
python smoke_test_checkpoint_10.py
```

### Release acceptance
```bash
python scripts/run_release_acceptance.py
```

### Frontend build
```bash
cd frontend
npm ci
npm run build
```

---

## Операционные сценарии

### Preflight
Проверка готовности окружения к запуску.

### Release readiness
Проверка текущей эксплуатационной готовности системы.

### Reconcile
Сверка локального состояния с live-состоянием биржи.

### Recovery
Восстановление состояния после рестарта или сбоев.

### Flatten paper
Принудительное закрытие paper-позиций.

### Flatten live
Принудительное закрытие live-позиций.

### Flatten live + kill switch
Экстренный сценарий:
- закрытие live-позиций
- постановка kill-switch
- блокировка дальнейшего исполнения

---

## Статус готовности

Проект доведён до **финального release checkpoint** и включает:

- strategy engine
- execution core
- historical backtesting
- bot runtime
- operations / recovery
- lifecycle sync
- journal + analytics
- integrations / AI
- production hardening
- release acceptance

### Честная оценка состояния
Для:
- **historical**
- **paper trading**
- **операционного тестирования**
- **контролируемого pre-live rollout**

проект выглядит как рабочий пакет.

Для **боевого mainnet live** перед полноценным использованием всё равно обязательно нужно:
- развернуть проект на реальном VPS
- заполнить production `.env`
- проверить Bybit, DeepSeek, Cloudflare Tunnel
- выполнить reconcile
- сделать controlled rollout с маленьким рабочим лимитом
- пройти manual operator validation

---

## Ограничения и важные замечания

### 1. Это не финансовая рекомендация
Проект — инструмент автоматизации и анализа.  
Любая реальная торговля осуществляется на риск владельца.

### 2. Live требует отдельной осторожности
Наличие live-логики в коде не означает, что можно сразу запускать крупный капитал.  
Правильный путь:
**historical → paper → limited live → full live**

### 3. Часть интеграций зависит от реального окружения
Например:
- Bybit credentials
- Cloudflare Tunnel token
- Codex browser session flow
- DeepSeek API key

Без них часть функций будет работать в fallback или не будет активна вовсе.

### 4. README не заменяет операторскую документацию
Для боевого запуска нужно смотреть:
- deploy docs
- env guide
- operator runbook
- release acceptance checklist

---

## Документация в проекте

### Основные документы
- `CHECKPOINT_01.md` … `CHECKPOINT_10.md`
- `deploy/PRODUCTION_DEPLOY.md`
- `deploy/OPERATOR_RUNBOOK.md`
- `deploy/RELEASE_ACCEPTANCE.md`

### Рекомендуемые дополнительные документы
Если они ведутся рядом с проектом:
- подробное описание продукта
- техническое задание
- roadmap
- `.env` guide
- deploy guide

---

## Рекомендуемый сценарий первого запуска

1. Поднять стек через Docker Compose
2. Проверить `/healthz`
3. Проверить страницу **Release**
4. Проверить страницу **Operations**
5. Настроить пары и рабочие лимиты
6. Запустить **historical**
7. Запустить **paper**
8. Проверить journal и analytics
9. Подключить Bybit
10. Выполнить **reconcile live**
11. Запустить live только на небольшом капитале

---

## Для кого этот проект

Этот репозиторий подходит, если тебе нужна:
- личная торговая платформа
- единая система вместо набора сервисов
- paper + historical + live в одном месте
- журнал трейдера
- AI review
- production-деплой на VPS

Этот проект **не ориентирован** на:
- SaaS
- много пользователей
- роли и команды
- биллинг
- white-label продукт
- биржевой агрегатор “для всех”

---

## Лицензирование и статус

Проект собран как **персональная система** под конкретную задачу и развивался поэтапно через checkpoint-подход.  
Перед публичным распространением, коммерческим использованием или open-source публикацией рекомендуется отдельно определить:
- лицензию
- политику публикации секретов
- правила хранения production-конфигураций
- политику operator access

---

## Полезные команды

### Поднять проект
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Остановить проект
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### Посмотреть контейнеры
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Посмотреть логи
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=200
```

### Проверить backend
```bash
curl http://127.0.0.1:8000/healthz
```

### Проверить сборку frontend
```bash
cd frontend
npm ci
npm run build
```

### Проверить smoke-test backend
```bash
cd backend
python smoke_test_checkpoint_10.py
```

---

## Итог

**VOLTAGE** — это не просто торговый бот, а целостная рабочая платформа, объединяющая:

- торговое исполнение
- контроль рисков
- стратегический слой
- журнал и аналитику
- AI review
- operations-контур
- production deployment

Если нужна полноценная личная система для controlled rollout от historical к live — это именно такой проект.
