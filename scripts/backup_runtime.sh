#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p deploy/backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="deploy/backups/runtime-$STAMP"
mkdir -p "$OUT_DIR"
cp -f .env "$OUT_DIR/.env.backup" 2>/dev/null || true
if docker compose ps postgres >/dev/null 2>&1; then
  docker compose exec -T postgres sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$OUT_DIR/postgres.sql" || true
fi
cp -f deploy/PRODUCTION_DEPLOY.md "$OUT_DIR/" 2>/dev/null || true
printf '{"generated_at":"%s","path":"%s"}\n' "$STAMP" "$OUT_DIR" > "$OUT_DIR/manifest.json"
echo "$OUT_DIR"
