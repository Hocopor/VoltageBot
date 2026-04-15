# VOLTAGE — инструкция по заполнению `.env`

## Что это за файл

Файл `.env` хранит конфигурацию проекта **VOLTAGE** для backend, Docker Compose и части production-операций.

Базовый шаблон уже есть в проекте: `.env.example`.

Создай `.env` в корне проекта рядом с:
- `docker-compose.yml`
- `docker-compose.prod.yml`

---

## Как создать `.env`

```bash
cp .env.example .env
nano .env
```

---

## Полный список переменных с пояснениями

Ниже — **каждая строка**, что она делает, нужно ли её менять, и откуда брать значение.

---

### `PROJECT_NAME=VOLTAGE`

**Что делает:** имя проекта для внутренних отчётов и release/backup-метаданных.

**Нужно ли менять:** нет, можно оставить `VOLTAGE`.

**Откуда брать значение:** это внутреннее имя проекта.

**Рекомендуемое значение:**
```env
PROJECT_NAME=VOLTAGE
```

---

### `ENVIRONMENT=production`

**Что делает:** помечает среду как production.

**Нужно ли менять:** нет.

**Откуда брать значение:** это режим окружения.

**Рекомендуемое значение:**
```env
ENVIRONMENT=production
```

---

### `API_V1_PREFIX=/api/v1`

**Что делает:** базовый префикс backend API.

**Нужно ли менять:** нет, если не хочешь менять маршруты API.

**Откуда брать значение:** это внутренняя схема API проекта.

**Рекомендуемое значение:**
```env
API_V1_PREFIX=/api/v1
```

---

### `BACKEND_HOST=0.0.0.0`

**Что делает:** логическое значение хоста backend.

**Нюанс:** в текущей сборке контейнера backend запускается через Dockerfile с жёстким `uvicorn ... --host 0.0.0.0 --port 8000`, поэтому эта переменная сейчас **практически информационная**.

**Нужно ли менять:** нет.

**Рекомендуемое значение:**
```env
BACKEND_HOST=0.0.0.0
```

---

### `BACKEND_PORT=8000`

**Что делает:** логическое значение порта backend.

**Нюанс:** в текущем Dockerfile backend порт запуска тоже зафиксирован как `8000`, поэтому эту переменную лучше оставить как есть.

**Нужно ли менять:** нет.

**Рекомендуемое значение:**
```env
BACKEND_PORT=8000
```

---

### `SECRET_KEY=change-me`

**Что делает:** секрет приложения. Используется как production-secret и участвует в readiness/preflight-проверках.

**Нужно ли менять:** **обязательно да**.

**Откуда брать значение:** сгенерируй самостоятельно на VPS или локально.

**Надёжный способ сгенерировать:**
```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
```

**Пример:**
```env
SECRET_KEY=твоя_длинная_случайная_строка
```

---

### `ALLOWED_ORIGINS=["http://localhost:8080","http://localhost"]`

**Что делает:** список origin-ов для CORS в backend.

**Нужно ли менять:** **да**, под твой реальный URL.

**Что сюда ставить:**
- локальный frontend для отладки;
- публичный домен/поддомен, через который будешь открывать приложение.

**Формат:** это должна быть **JSON-строка массива**, а не список “через запятую”.

**Пример для твоего случая:**
```env
ALLOWED_ORIGINS=["http://localhost:8080","https://voltage.example.com"]
```

Если будешь открывать только через Cloudflare Tunnel, обязательно добавь туда публичный `https://...` адрес.

---

### `DATABASE_URL=postgresql+psycopg://voltage:voltage_password@postgres:5432/voltage`

**Что делает:** строка подключения backend к PostgreSQL.

**Нужно ли менять:** **обычно да**, хотя host `postgres` и порт `5432` внутри Docker Compose оставляются как есть.

**Что важно:**
- `postgres` — это имя сервиса в Compose, его менять не нужно;
- логин, пароль и имя БД должны совпадать с:
  - `POSTGRES_DB`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`

**Рекомендуемая схема:**
```env
DATABASE_URL=postgresql+psycopg://voltage:СИЛЬНЫЙ_ПАРОЛЬ@postgres:5432/voltage
```

---

### `REDIS_URL=redis://redis:6379/0`

**Что делает:** подключение к Redis.

**Нужно ли менять:** обычно нет.

**Почему:** сервис `redis` в Compose уже так и называется.

**Рекомендуемое значение:**
```env
REDIS_URL=redis://redis:6379/0
```

---

### `POSTGRES_DB=voltage`

**Что делает:** имя базы PostgreSQL.

**Нужно ли менять:** можно оставить.

**Рекомендуемое значение:**
```env
POSTGRES_DB=voltage
```

---

### `POSTGRES_USER=voltage`

**Что делает:** пользователь PostgreSQL.

**Нужно ли менять:** можно оставить.

**Рекомендуемое значение:**
```env
POSTGRES_USER=voltage
```

---

### `POSTGRES_PASSWORD=voltage_password`

**Что делает:** пароль PostgreSQL.

**Нужно ли менять:** **обязательно да**.

**Откуда брать значение:** придумай свой длинный пароль.

**Пример:**
```env
POSTGRES_PASSWORD=Очень_сложный_пароль_для_Postgres
```

---

### `BYBIT_API_BASE_URL=https://api.bybit.com`

**Что делает:** базовый URL Bybit API.

**Нужно ли менять:** нет, если ты торгуешь на **Bybit mainnet**, а по проекту именно так и нужно.

**Откуда брать значение:** это mainnet endpoint Bybit.

**Рекомендуемое значение:**
```env
BYBIT_API_BASE_URL=https://api.bybit.com
```

**Где брать API-ключи:** в веб-кабинете Bybit, раздел API Management. Создание API-ключей доступно через сайт Bybit, не через приложение.  
Официальная справка Bybit:  
- https://www.bybit.com/en/help-center/article/How-to-create-your-API-key/

---

### `BYBIT_API_KEY=`

**Что делает:** API key для live-работы с Bybit.

**Нужно ли заполнять:** **обязательно для реальной торговли**. Для paper/history можно оставить пустым.

**Откуда брать значение:** создаёшь ключ в Bybit API Management.

**Что рекомендую выставить при создании ключа:**
- только нужные права;
- включённый IP whitelist, если возможно;
- отдельный ключ именно под этого бота.

**Пример:**
```env
BYBIT_API_KEY=xxxxxxxxxxxxxxxx
```

---

### `BYBIT_API_SECRET=`

**Что делает:** секретный ключ Bybit.

**Нужно ли заполнять:** **обязательно для реальной торговли**.

**Откуда брать значение:** выдаётся Bybit при создании API key.

**Пример:**
```env
BYBIT_API_SECRET=yyyyyyyyyyyyyyyy
```

---

### `BYBIT_RECV_WINDOW=5000`

**Что делает:** окно допустимой задержки для подписанных запросов Bybit в миллисекундах.

**Нужно ли менять:** обычно нет.

**Когда менять:** если на VPS будут проблемы с сетевой задержкой и это будет видно по ошибкам подписи/времени.

**Рекомендуемое значение:**
```env
BYBIT_RECV_WINDOW=5000
```

---

### `BYBIT_TIMEOUT_SECONDS=20`

**Что делает:** timeout HTTP-запросов к Bybit.

**Нужно ли менять:** обычно нет.

**Когда менять:** если сеть нестабильная и явно не хватает времени.

**Рекомендуемое значение:**
```env
BYBIT_TIMEOUT_SECONDS=20
```

---

### `DEEPSEEK_BASE_URL=https://api.deepseek.com`

**Что делает:** базовый URL DeepSeek API.

**Нужно ли менять:** нет.

**Откуда брать значение:** официальный DeepSeek API base URL.

**Рекомендуемое значение:**
```env
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

Официальная документация DeepSeek:  
- https://api-docs.deepseek.com/

---

### `DEEPSEEK_API_KEY=`

**Что делает:** API-ключ DeepSeek для AI review, explainability и проверок интеграции.

**Нужно ли заполнять:** **желательно да**, если хочешь реальный AI-анализ. Если оставить пустым, часть AI-функций будет работать в fallback/заглушечном режиме.

**Откуда брать значение:** в кабинете DeepSeek API.

**Пример:**
```env
DEEPSEEK_API_KEY=sk-...
```

---

### `DEEPSEEK_MODEL=deepseek-chat`

**Что делает:** модель DeepSeek по умолчанию.

**Нужно ли менять:** нет, если не хочешь тестировать другой supported model.

**Рекомендуемое значение:**
```env
DEEPSEEK_MODEL=deepseek-chat
```

---

### `CODEX_LOGIN_MODE=chatgpt`

**Что делает:** режим логина для Codex-слоя внутри проекта.

**Нужно ли менять:** нет.

**Важный нюанс:** в текущей реализации проекта это **не полноценный production OAuth-клиент OpenAI** с автоматическим обменом токенов через `.env`. Здесь реализован локальный browser-session persistence слой в директории сессий. То есть:
- сам mode лучше оставить `chatgpt`;
- отдельный API key для Codex в `.env` сейчас не используется;
- авторизация/сессия создаётся через проектный flow и хранится локально.

**Рекомендуемое значение:**
```env
CODEX_LOGIN_MODE=chatgpt
```

Официальная справка OpenAI по `codex --login` и Sign in with ChatGPT:  
- https://help.openai.com/en/articles/11381614

---

### `CODEX_SESSION_DIR=/data/codex`

**Что делает:** директория, где контейнер backend хранит локальные Codex session-файлы.

**Нужно ли менять:** обычно нет.

**Почему:** в production Compose эта директория уже примонтирована как persistent volume.

**Рекомендуемое значение:**
```env
CODEX_SESSION_DIR=/data/codex
```

---

### `CLOUDFLARE_TUNNEL_TOKEN=`

**Что делает:** токен для запуска контейнера `cloudflared`.

**Нужно ли заполнять:** **обязательно**, если хочешь открывать проект извне через Cloudflare Tunnel.

**Откуда брать значение:**
1. Cloudflare Dashboard → **Networking → Tunnels**
2. открыть нужный tunnel;
3. выбрать **Add a replica**;
4. скопировать команду запуска `cloudflared`;
5. взять из неё сам токен — длинную строку вида `eyJ...`

Официальные инструкции Cloudflare:
- tunnel token: https://developers.cloudflare.com/tunnel/advanced/tunnel-tokens/
- setup tunnel: https://developers.cloudflare.com/tunnel/setup/

**Пример:**
```env
CLOUDFLARE_TUNNEL_TOKEN=eyJ...
```

---

### `CLOUDFLARE_TUNNEL_HOSTNAME=`

**Что делает:** логическое поле под hostname туннеля.

**Важный нюанс:** в текущей сборке Compose контейнер `cloudflared` запускается **по токену**, а эта переменная в runtime проекта практически **информационная**. На сам запуск контейнера она не влияет.

**Нужно ли заполнять:** желательно да, для порядка и self-documentation.

**Что сюда ставить:** твой публичный поддомен, например:
```env
CLOUDFLARE_TUNNEL_HOSTNAME=voltage.example.com
```

---

### `PUBLIC_BASE_URL=`

**Что делает:** публичный URL приложения. Используется в readiness/preflight и как общее публичное основание для внешнего доступа.

**Нужно ли заполнять:** **обязательно для production**.

**Что сюда ставить:** итоговый внешний адрес через Cloudflare Tunnel.

**Пример:**
```env
PUBLIC_BASE_URL=https://voltage.example.com
```

---

### `FRONTEND_APP_TITLE=VOLTAGE`

**Что делает:** имя frontend-приложения.

**Нюанс:** в текущем коде эта переменная практически не задействована.

**Нужно ли менять:** нет.

**Рекомендуемое значение:**
```env
FRONTEND_APP_TITLE=VOLTAGE
```

---

### `BACKUP_ROOT=/data/backups`

**Что делает:** директория для backup-артефактов внутри backend-контейнера.

**Нужно ли менять:** обычно нет.

**Почему:** в production Compose уже есть bind-mount на `./deploy/backups`.

**Рекомендуемое значение:**
```env
BACKUP_ROOT=/data/backups
```

---

### `RELEASE_ROOT=/data/releases`

**Что делает:** директория для release-артефактов внутри backend-контейнера.

**Нужно ли менять:** обычно нет.

**Почему:** в production Compose уже есть bind-mount на `./deploy/releases`.

**Рекомендуемое значение:**
```env
RELEASE_ROOT=/data/releases
```

---

## Рекомендуемый `.env` для твоего сценария

Ниже — **рекомендуемый шаблон**, который ближе всего к твоему боевому сценарию.

```env
PROJECT_NAME=VOLTAGE
ENVIRONMENT=production
API_V1_PREFIX=/api/v1

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
SECRET_KEY=СЮДА_СГЕНЕРИРОВАННЫЙ_ДЛИННЫЙ_SECRET
ALLOWED_ORIGINS=["http://localhost:8080","https://voltage.example.com"]

DATABASE_URL=postgresql+psycopg://voltage:СИЛЬНЫЙ_POSTGRES_ПАРОЛЬ@postgres:5432/voltage
REDIS_URL=redis://redis:6379/0
POSTGRES_DB=voltage
POSTGRES_USER=voltage
POSTGRES_PASSWORD=СИЛЬНЫЙ_POSTGRES_ПАРОЛЬ

BYBIT_API_BASE_URL=https://api.bybit.com
BYBIT_API_KEY=ТВОЙ_BYBIT_API_KEY
BYBIT_API_SECRET=ТВОЙ_BYBIT_API_SECRET
BYBIT_RECV_WINDOW=5000
BYBIT_TIMEOUT_SECONDS=20

DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=ТВОЙ_DEEPSEEK_API_KEY
DEEPSEEK_MODEL=deepseek-chat

CODEX_LOGIN_MODE=chatgpt
CODEX_SESSION_DIR=/data/codex

CLOUDFLARE_TUNNEL_TOKEN=ТВОЙ_CLOUDFLARE_TUNNEL_TOKEN
CLOUDFLARE_TUNNEL_HOSTNAME=voltage.example.com
PUBLIC_BASE_URL=https://voltage.example.com

FRONTEND_APP_TITLE=VOLTAGE
BACKUP_ROOT=/data/backups
RELEASE_ROOT=/data/releases
```

---

## Что обязательно заполнить перед первым production-запуском

Вот список того, что **обязательно** должно быть не пустым:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `PUBLIC_BASE_URL`

Для live-торговли дополнительно обязательно:
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

Для внешнего доступа через туннель:
- `CLOUDFLARE_TUNNEL_TOKEN`

Для полноценного AI-слоя:
- `DEEPSEEK_API_KEY`

---

## Что можно оставить по умолчанию

Обычно можно не менять:
- `PROJECT_NAME`
- `ENVIRONMENT`
- `API_V1_PREFIX`
- `BACKEND_HOST`
- `BACKEND_PORT`
- `REDIS_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `BYBIT_API_BASE_URL`
- `BYBIT_RECV_WINDOW`
- `BYBIT_TIMEOUT_SECONDS`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `CODEX_LOGIN_MODE`
- `CODEX_SESSION_DIR`
- `FRONTEND_APP_TITLE`
- `BACKUP_ROOT`
- `RELEASE_ROOT`

---

## Важные нюансы именно этого проекта

### 1. `BACKEND_HOST` и `BACKEND_PORT`
Сейчас они фактически не управляют Docker-запуском backend, потому что в Dockerfile `uvicorn` уже зафиксирован на `0.0.0.0:8000`.

### 2. `CLOUDFLARE_TUNNEL_HOSTNAME`
Сейчас это в основном информационная переменная. Реальный запуск `cloudflared` идёт по `CLOUDFLARE_TUNNEL_TOKEN`.

### 3. `FRONTEND_APP_TITLE`
Сейчас почти не влияет на runtime.

### 4. `CODEX_LOGIN_MODE`
Это не место для API-ключа. Для текущего проекта mode лучше оставить `chatgpt`, а сам session persistence будет жить в `CODEX_SESSION_DIR`.

### 5. `DATABASE_URL` и `POSTGRES_*`
Они должны быть **согласованы между собой**. Если меняешь логин/пароль/БД в `POSTGRES_*`, обязательно меняй и `DATABASE_URL`.

---

## Проверка `.env` перед запуском

Минимальная ручная проверка:

1. Нет ли строк вида `change-me`
2. Не пусты ли:
   - `SECRET_KEY`
   - `POSTGRES_PASSWORD`
   - `PUBLIC_BASE_URL`
3. Для live не пусты ли:
   - `BYBIT_API_KEY`
   - `BYBIT_API_SECRET`
4. Для Cloudflare не пуст ли:
   - `CLOUDFLARE_TUNNEL_TOKEN`

---

## Официальные источники, откуда брать значения

### Docker
- https://docs.docker.com/engine/install/ubuntu/
- https://docs.docker.com/compose/install/

### Cloudflare Tunnel
- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/advanced/tunnel-tokens/

### Bybit API key
- https://www.bybit.com/en/help-center/article/How-to-create-your-API-key/

### DeepSeek API
- https://api-docs.deepseek.com/

### Codex CLI / Sign in with ChatGPT
- https://help.openai.com/en/articles/11381614

---

## Дополнительные переменные для входа в систему

### `AUTH_LOGIN=`
Логин для входа в интерфейс. Без него авторизация не будет настроена.

Пример:
```env
AUTH_LOGIN=admin
```

### `AUTH_PASSWORD_HASH=`
Хэш пароля для входа в интерфейс. В `.env` хранится именно хэш, а не открытый пароль.

Сгенерировать хэш можно так:
```bash
python3 scripts/generate_auth_hash.py
```

Или так:
```bash
python3 scripts/generate_auth_hash.py МойСложныйПароль
```

Полученную строку вставь в `.env` целиком.

### `AUTH_COOKIE_NAME=voltage_session`
Имя cookie сессии. Обычно менять не нужно.

### `AUTH_SESSION_TTL_HOURS=720`
Сколько часов живёт сессия после входа. Обычно можно оставить как есть.
