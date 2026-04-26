#!/usr/bin/env bash
# One-shot: create venv and install production dependencies.
# Run from repo root on the VPS after git clone, e.g.:
#   cd /home/tradingbot/trading-bot && chmod +x deploy/install-vps.sh && ./deploy/install-vps.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -f requirements-prod.txt ]]; then
  echo "requirements-prod.txt not found in $ROOT" >&2
  exit 1
fi
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements-prod.txt
echo "OK: venv + requirements-prod.txt"
echo "Next: copy .env from .env.example, add secrets; then systemd + logrotate (see deploy/README.md)"
