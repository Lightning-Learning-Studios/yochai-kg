"""Keep the documents and the eval stand-in in step with the real server.

    python scripts/sync_plugin_docs.py            rewrite the generated parts
    python scripts/sync_plugin_docs.py --check    exit 1 when something is out of date (used in CI)

The server's tool list is the single source. This script copies it into:
  docs/plugin/submission-anthropic.md   the per-tool table reviewers read
  plugin/evals/mocks/yochai/_tools.json the stand-in server the plugin evals use
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gateway.open_server import mcp

TABLE_HEAD = "| Tool | Title | What it does | Reads only |\n| --- | --- | --- | --- |\n"
TABLE_RE = re.compile(r"\| Tool \| Title \| What it does \| Reads only \|\n\| --- \| --- \| --- \| --- \|\n(?:\|.*\n)+")


def what_it_does(description: str) -> str:
    """The second sentence onward: the part that says what comes back."""
    flat = " ".join(description.split())
    parts = flat.split(". ", 1)
    return (parts[1] if len(parts) > 1 else flat).rstrip(".") + "."


def main() -> int:
    check = "--check" in sys.argv
    tools = asyncio.run(mcp.list_tools())
    stale: list[str] = []

    table = TABLE_HEAD + "".join(
        f"| `{t.name}` | {t.title} | {what_it_does(t.description or '')} | Yes |\n" for t in tools)
    doc = ROOT / "docs" / "plugin" / "submission-anthropic.md"
    text = doc.read_text(encoding="utf-8")
    if not TABLE_RE.search(text):
        print(f"no tool table found in {doc.relative_to(ROOT)}")
        return 1
    new_text = TABLE_RE.sub(lambda _: table, text, count=1)
    if new_text != text:
        stale.append(str(doc.relative_to(ROOT)))
        if not check:
            doc.write_text(new_text, encoding="utf-8")

    mock = ROOT / "plugin" / "evals" / "mocks" / "yochai" / "_tools.json"
    payload = json.JSONEncoder(indent=2, ensure_ascii=False).encode({"tools": [
        {"name": t.name, "description": " ".join((t.description or "").split()), "inputSchema": t.inputSchema}
        for t in tools]}) + "\n"
    if not mock.exists() or mock.read_text(encoding="utf-8") != payload:
        stale.append(str(mock.relative_to(ROOT)))
        if not check:
            mock.write_text(payload, encoding="utf-8")

    if stale and check:
        print("Out of date. Run: python scripts/sync_plugin_docs.py\n  " + "\n  ".join(stale))
        return 1
    print(("updated: " + ", ".join(stale)) if stale else f"in step with the server ({len(tools)} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
