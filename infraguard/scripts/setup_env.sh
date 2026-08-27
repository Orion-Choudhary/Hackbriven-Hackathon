#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cat <<'MSG'
Environment created.

Set ArmorIQ credentials in your shell before cloud tests:
  export ARMORIQ_API_KEY="YOUR_KEY"
  export BACKEND_ENDPOINT="https://api.armoriq.ai"
  export IAP_ENDPOINT="https://iap.armoriq.ai"
  export PROXY_ENDPOINT="https://proxy.armoriq.ai"
MSG
