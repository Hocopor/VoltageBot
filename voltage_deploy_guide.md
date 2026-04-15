# VOLTAGE — инструкция по деплою на VPS Ubuntu 24

## Для чего эта инструкция

Это практическая инструкция по деплою **VOLTAGE** на **VPS Ubuntu 24** через:
- Docker Engine
- Docker Compose plugin
- Cloudflare Tunnel
- `.env`
- production compose stack

Инструкция написана именно под финальную структуру проекта из архива `voltage_checkpoint_10_final_release.zip`.

---

## Важное перед стартом

### Что у тебя уже должно быть
- VPS с **Ubuntu 24.04**
- доступ по SSH
- домен, подключённый к Cloudflare
- созданный Cloudflare Tunnel
- Bybit API key/secret для mainnet, если хочешь live
- DeepSeek API key, если хочешь полноценный AI review

---

## Что реально запускается в проекте

Стек проекта:
- `postgres`
- `redis`
- `api` (FastAPI backend)
- `web` (React build + Nginx)
- `cloudflared`

Compose-файлы:
- `docker-compose.yml`
- `docker-compose.prod.yml`

Стартовая команда проекта:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 1. Подготовь VPS

### Обнови систему
```bash
sudo apt update && sudo apt upgrade -y
```

### Установи базовые утилиты
```bash
sudo apt install -y ca-certificates curl gnupg unzip git nano
```

---

## 2. Установи Docker Engine и Docker Compose plugin

Официальный рекомендуемый путь для Ubuntu — установка через репозиторий Docker.

### Добавь официальный Docker repo
```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```

### Установи Docker и Compose plugin
```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Проверь установку
```bash
docker --version
docker compose version
sudo docker run hello-world
```

### Чтобы запускать Docker без `sudo`
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 3. Подготовь директорию проекта

Пример:
```bash
mkdir -p ~/apps/voltage
cd ~/apps/voltage
```

### Залей архив проекта
Помести туда финальный архив:
```bash
voltage_checkpoint_10_final_release.zip
```

### Распакуй
```bash
unzip voltage_checkpoint_10_final_release.zip
cd voltage_checkpoint_10
```

---

## 4. Создай `.env`

Скопируй шаблон:
```bash
cp .env.example .env
nano .env
```

Заполни `.env` по отдельной инструкции:
- `voltage_env_guide.md`

Минимум до первого осмысленного запуска:
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `PUBLIC_BASE_URL`
- `CLOUDFLARE_TUNNEL_TOKEN`

Для live:
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

Для AI:
- `DEEPSEEK_API_KEY`

---

## 5. Подготовь Cloudflare Tunnel

### Что нужно сделать в Cloudflare Dashboard
1. Открой **Cloudflare Dashboard**
2. Перейди в **Networking → Tunnels**
3. Создай tunnel или открой уже существующий
4. Добавь published application route:
   - hostname: например `voltage.example.com`
   - service URL: для этого проекта удобно вести на `http://web:80` внутри compose-стека, но так как контейнер cloudflared работает в той же docker-сети, токеновый запуск уже использует конфигурацию самого туннеля
5. Возьми **tunnel token**
6. Запиши его в:
```env
CLOUDFLARE_TUNNEL_TOKEN=...
```

### Что поставить в `.env`
```env
CLOUDFLARE_TUNNEL_TOKEN=eyJ...
CLOUDFLARE_TUNNEL_HOSTNAME=voltage.example.com
PUBLIC_BASE_URL=https://voltage.example.com
ALLOWED_ORIGINS=["http://localhost:8080","https://voltage.example.com"]
```

---

## 6. Создай директории для runtime-артефактов

На всякий случай:
```bash
mkdir -p deploy/backups
mkdir -p deploy/releases
```

---

## 7. Проверь compose-файлы перед запуском

### Проверка merged config
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config > /tmp/voltage-compose.rendered.yml
```

Если команда отработала без ошибки — compose-конфиг валидный.

---

## 8. Первый запуск

### Рекомендуемый запуск
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Или через скрипт проекта:
```bash
chmod +x scripts/*.sh
./scripts/run_prod_stack.sh
```

---

## 9. Что проверить сразу после запуска

### Состояние контейнеров
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Логи
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=200
```

### Проверка backend health
На VPS:
```bash
curl http://127.0.0.1:8000/healthz
```

Ожидаемо должен прийти JSON со статусом `ok`.

### Проверка frontend
Локально на VPS:
```bash
curl -I http://127.0.0.1:8080
```

### Проверка tunnel
Открой в браузере:
```text
https://твой-поддомен
```

---

## 10. Первые проверки уже в интерфейсе

После входа в UI:

### На странице Operations
Проверь:
- `maintenance_mode = false`
- `trading_paused = false` только если действительно хочешь торговать
- `kill_switch_armed = false`
- `last_startup_at` заполнен
- `last_bot_heartbeat_at` обновляется

### На странице Release
Проверь:
- readiness score
- critical issues
- warnings
- recommended mode

### Перед live
Обязательно:
- выполните `reconcile live`
- проверь реальный баланс Bybit
- проверь выбранные пары
- проверь рабочие лимиты spot/futures
- сначала включай не full live капитал, а минимальный рабочий лимит

---

## 11. Полезные команды эксплуатации

### Поднять стек
```bash
./scripts/run_prod_stack.sh
```

### Остановить стек
```bash
./scripts/stop_prod_stack.sh
```

### Посмотреть контейнеры
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Посмотреть логи
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=200
```

### Сделать runtime backup
```bash
./scripts/backup_runtime.sh
```

### Восстановить runtime backup
```bash
./scripts/restore_runtime.sh deploy/backups/runtime-YYYYMMDDTHHMMSSZ
```

### Сгенерировать runtime manifest через API
```bash
./scripts/create_runtime_manifest.sh
```

---

## 12. Важные нюансы именно этого проекта

## Нюанс 1. `scripts/preflight_check.py`
В проекте есть:
```bash
python scripts/preflight_check.py
```

Но **на голом VPS до первой сборки** он может не заработать, потому что этот скрипт импортирует backend-модули и требует Python-зависимости проекта на хосте.

### Что делать правильно
Для типичного Docker-only деплоя:
1. сначала собрать и поднять контейнеры;
2. потом проверять:
   - `/healthz`
   - `/api/v1/ops/preflight`
   - `/api/v1/ops/release-readiness`

Если хочешь запускать `scripts/preflight_check.py` на хосте до контейнеров — тогда придётся отдельно поднимать Python-окружение проекта на VPS.

---

## Нюанс 2. `create_runtime_manifest.sh`
Этот скрипт обращается к:
```text
http://127.0.0.1:8000/api/v1/ops/backup/manifest
```

То есть backend уже должен быть запущен и доступен локально на VPS.

---

## Нюанс 3. `backup_db.sh` и `restore_db.sh`
Эти скрипты захардкожены под:
- DB = `voltage`
- USER = `voltage`

Если ты эти значения оставишь как в шаблоне — всё ок.

Если изменишь `POSTGRES_DB` или `POSTGRES_USER`, то:
- либо исправь эти два скрипта,
- либо используй `backup_runtime.sh` / `restore_runtime.sh`, они безопаснее для текущей финальной сборки.

---

## Нюанс 4. `CLOUDFLARE_TUNNEL_HOSTNAME`
Сейчас контейнер `cloudflared` в compose реально стартует по токену:
```yaml
command: ["tunnel", "run", "--token", "${CLOUDFLARE_TUNNEL_TOKEN}"]
```

То есть сам запуск зависит от `CLOUDFLARE_TUNNEL_TOKEN`, а не от `CLOUDFLARE_TUNNEL_HOSTNAME`.

---

## Нюанс 5. Backend host/port
Переменные:
```env
BACKEND_HOST
BACKEND_PORT
```

в текущем Dockerfile почти не влияют на runtime, потому что `uvicorn` уже зафиксирован на `0.0.0.0:8000`.

---

## 13. Как делать безопасный go-live

Рекомендованный путь:

### Этап 1
Запусти только:
- historical
- paper trading

### Этап 2
Проверь:
- журнал сделок
- analytics
- backtest
- strategy decisions
- bot runtime
- reconcile

### Этап 3
Подключи Bybit keys и включи live, но:
- с маленьким рабочим лимитом;
- на ограниченном наборе пар;
- с постоянным контролем Operations и Release страниц.

### Этап 4
Только после нескольких успешных прогонов увеличивай лимит.

---

## 14. Что делать, если контейнеры не поднялись

### Посмотреть статус
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Посмотреть логи конкретного контейнера
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs api --tail=200
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs web --tail=200
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs cloudflared --tail=200
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs postgres --tail=200
```

### Типичные причины
- не заполнен `.env`
- `SECRET_KEY=change-me`
- нет `CLOUDFLARE_TUNNEL_TOKEN`
- плохой `DATABASE_URL`
- `POSTGRES_PASSWORD` не совпадает с `DATABASE_URL`
- порт 8000 или 8080 уже занят на VPS
- Docker установлен некорректно
- недостаточно RAM/диска
- Cloudflare Tunnel создан, но не настроен published hostname
- Bybit ключ неактивен или без нужных прав
- IP whitelist на Bybit не включает IP VPS

---

## 15. Минимальный post-deploy checklist

После первого успешного запуска проверь:

### На VPS
- `docker compose ... ps` — всё `Up`
- `curl http://127.0.0.1:8000/healthz` — статус `ok`
- `curl -I http://127.0.0.1:8080` — frontend отвечает

### В браузере
- открывается публичный URL
- работает Dashboard
- работает Operations
- работает Release
- видны balances/settings/pairs

### Для Cloudflare
- публичный hostname открывается по HTTPS
- нет tunnel error page

### Для live
- Bybit balances читаются
- reconcile live проходит
- нет critical issues на Release странице

---

## 16. Рекомендуемый порядок первого боевого запуска

1. Поднять стек
2. Проверить `/healthz`
3. Проверить UI
4. Проверить Release page
5. Проверить Operations page
6. Настроить пары и лимиты
7. Прогнать historical
8. Прогнать paper
9. Подключить Bybit
10. Сделать manual reconcile live
11. Запустить live только на малом рабочем лимите

---

## 17. Официальные источники

### Docker Engine на Ubuntu
- https://docs.docker.com/engine/install/ubuntu/

### Docker Compose plugin
- https://docs.docker.com/compose/install/

### Cloudflare Tunnel setup
- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/routing/
- https://developers.cloudflare.com/tunnel/advanced/tunnel-tokens/

### Bybit API key creation
- https://www.bybit.com/en/help-center/article/How-to-create-your-API-key/

### DeepSeek API
- https://api-docs.deepseek.com/

### Codex CLI / Sign in with ChatGPT
- https://help.openai.com/en/articles/11381614
