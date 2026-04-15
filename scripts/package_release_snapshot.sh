#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/dist}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT_DIR"
ARCHIVE="$OUT_DIR/voltage-release-snapshot-$STAMP.tar.gz"

tar \
  --exclude='.git' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/dist' \
  --exclude='backend/__pycache__' \
  --exclude='backend/app/__pycache__' \
  --exclude='*.pyc' \
  -czf "$ARCHIVE" \
  -C "$ROOT_DIR" .

echo "[OK] created $ARCHIVE"
