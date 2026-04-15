#!/usr/bin/env bash
set -eu

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "Usage: $0 path/to/backup.sql" >&2
  exit 1
fi
cat "$FILE" | docker compose exec -T postgres psql -U voltage -d voltage
echo "Restore complete from $FILE"
