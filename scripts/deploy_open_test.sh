#!/bin/bash
# Deploy the open server to the Railway TEST service from the current working tree.
#
#   RAILWAY_PROJECT_ID=<project id> scripts/deploy_open_test.sh
#
# The repository's railway.json starts the keyed developer gateway. This script
# stages a copy of the tree in which railway.open.json takes its place, then
# uploads that copy. Nothing in the repository or in production changes.
# A service connected to GitHub does not need this script: set its
# "Railway config file" setting to railway.open.json instead.
set -euo pipefail

PROJECT="${RAILWAY_PROJECT_ID:?Set RAILWAY_PROJECT_ID to the id of the yochai-kg Railway project}"
SERVICE="${RAILWAY_SERVICE:-yochai-plugin-test}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -r "$STAGE"' EXIT

rsync -a --exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache \
  --exclude .ruff_cache --exclude '*.egg-info' --exclude 'plugin/evals/results' "$ROOT/" "$STAGE/"
cp "$STAGE/railway.open.json" "$STAGE/railway.json"
# Railway's current builder reads the start command from a Procfile when it is uploaded this way.
echo 'web: python -m uvicorn gateway.open_server:get_app --factory --host 0.0.0.0 --port $PORT' > "$STAGE/Procfile"

cd "$STAGE"
railway up --project "$PROJECT" --environment production --service "$SERVICE" --detach
