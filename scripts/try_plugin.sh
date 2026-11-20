#!/bin/bash
# Open Claude Code with the Yochai plugin wired to the hosted TEST server.
#
#   scripts/try_plugin.sh                     start a chat
#   scripts/try_plugin.sh "your question"     ask one question and print the answer
#   YOCHAI_MCP_URL=http://127.0.0.1:8000/mcp scripts/try_plugin.sh     use a server on this laptop
#
# The plugin in this repository points at the production address. This script
# makes a temporary copy that points at the test server, so you can try the
# plugin before production exists. It changes no file in the repository.
set -euo pipefail

URL="${YOCHAI_MCP_URL:-https://yochai-plugin-test-production.up.railway.app/mcp}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COPY="$(mktemp -d)"
trap 'rm -r "$COPY"' EXIT

rsync -a --exclude evals "$ROOT/plugin/" "$COPY/plugin/"
printf '{\n  "mcpServers": {\n    "yochai": { "type": "http", "url": "%s" }\n  }\n}\n' "$URL" > "$COPY/plugin/.mcp.json"
mkdir "$COPY/chat"
cd "$COPY/chat"

echo "Yochai plugin, using $URL"
if [ $# -gt 0 ]; then
  claude -p "$1" --plugin-dir "$COPY/plugin" --allowedTools "mcp__plugin_yochai-jewish-texts_yochai"
else
  claude --plugin-dir "$COPY/plugin" --allowedTools "mcp__plugin_yochai-jewish-texts_yochai"
fi
