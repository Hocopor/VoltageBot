#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-directory>" >&2
  exit 1
fi
BACKUP_DIR="$1"
if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory not found: $BACKUP_DIR" >&2
  exit 1
fi
if [ -f "$BACKUP_DIR/.env.backup" ]; then
  cp "$BACKUP_DIR/.env.backup" .env
fi
if [ -f "$BACKUP_DIR/postgres.sql" ]; then
  docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$BACKUP_DIR/postgres.sql"
fi
echo "Restore completed from $BACKUP_DIR"
