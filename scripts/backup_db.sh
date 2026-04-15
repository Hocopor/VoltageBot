#!/usr/bin/env bash
set -eu

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"

docker compose exec -T postgres pg_dump -U voltage -d voltage > "$OUT_DIR/voltage_${STAMP}.sql"
echo "Backup written to $OUT_DIR/voltage_${STAMP}.sql"
