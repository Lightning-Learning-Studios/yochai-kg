"""The passage card: the panel Claude, ChatGPT and other MCP Apps hosts show beside
the three passage tools. Offline: no graph and no network."""
import json
import re
import tomllib
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from gateway import config, open_server

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "gateway" / "widgets" / "passage-card.html"
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
URI = "ui://widget/passage-card.html"
MIME = "text/html;profile=mcp-app"
CARD_TOOLS = {"get_passage", "search_passages", "get_commentaries"}


@pytest.fixture(scope="module")
def client():
    # FastMCP keeps one session manager, and each manager runs once; another test module
    # may already have run it, so start a fresh one here and leave a fresh one behind.
    open_server.mcp._session_manager = None
    with TestClient(open_server.build_app()) as c:
        yield c
    open_server.mcp._session_manager = None


def rpc(client, method, params=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    r = client.post("/mcp", headers=HEADERS, content=json.dumps(body))
    assert r.status_code == 200, r.text
    return r.json()["result"]


@pytest.fixture(scope="module")
def html():
    return HTML_PATH.read_text(encoding="utf-8")


# --- what the server declares ---------------------------------------------------------
def test_resource_is_listed_with_the_mcp_apps_type(client):
    resources = rpc(client, "resources/list")["resources"]
    (card,) = [r for r in resources if r["uri"] == URI]
    assert card["mimeType"] == MIME
    assert card["name"] == "passage-card"


def test_resource_read_returns_the_html_and_its_policy(client, html):
    (content,) = rpc(client, "resources/read", {"uri": URI})["contents"]
    assert content["uri"] == URI and content["mimeType"] == MIME
    assert content["text"] == html
    meta = content["_meta"]
    assert meta["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}   # the card fetches nothing
    assert meta["ui"]["prefersBorder"] is True
    assert meta["openai/widgetCSP"]["redirect_domains"] == [config.APP_URL]     # where "Open in Yochai" goes
    assert meta["openai/widgetCSP"]["connect_domains"] == [] and meta["openai/widgetCSP"]["resource_domains"] == []
    assert meta["openai/widgetDescription"]


def test_only_the_three_passage_tools_name_the_card(client):
    tools = rpc(client, "tools/list")["tools"]
    assert len(tools) == 16
    for t in tools:
        meta = t["_meta"]
        assert meta["securitySchemes"] == [{"type": "noauth"}], t["name"]
        if t["name"] in CARD_TOOLS:
            assert meta["ui"] == {"resourceUri": URI}, t["name"]
            assert meta["openai/outputTemplate"] == URI, t["name"]
        else:
            assert set(meta) == {"securitySchemes"}, t["name"]


def test_text_answers_do_not_depend_on_the_card(client):
    # A host with no UI support sees the same tools with the same result shapes as before.
    from gateway import models as M

    shapes = {"get_passage": M.PassageResult, "search_passages": M.SearchPassagesResult,
              "get_commentaries": M.CommentariesResult}
    tools = {t["name"]: t for t in rpc(client, "tools/list")["tools"]}
    for name, model in shapes.items():
        assert tools[name]["outputSchema"]["properties"] == model.model_json_schema()["properties"], name


# --- the HTML file itself ---------------------------------------------------------------
def test_html_is_small_and_self_contained(html):
    assert len(html.encode("utf-8")) < 60 * 1024
    assert "http://" not in html and "https://" not in html
    for needle in ("<link", "@import", "url(", " src=", "fetch(", "XMLHttpRequest", "WebSocket", "@font-face"):
        assert needle not in html, needle


def test_html_never_writes_markup_from_data(html):
    assert not re.search(r"innerHTML\s*=|outerHTML\s*=|insertAdjacentHTML|document\.write|\beval\(", html)
    assert "textContent" in html


def test_html_speaks_both_host_protocols(html):
    for needle in ("ui/initialize", "ui/notifications/initialized", "ui/notifications/tool-result",
                   "ui/notifications/host-context-changed", "ui/open-link", "ui/notifications/size-changed",
                   "window.openai", "toolOutput", "openai:set_globals", "openExternal"):
        assert needle in html, needle


def test_html_marks_hebrew_and_handles_themes(html):
    assert '"lang", "he"' in html and '"dir", "rtl"' in html
    assert "prefers-color-scheme: dark" in html and 'data-theme="dark"' in html
    assert "max-width: 560px" in html                       # Hebrew above English on narrow screens


def test_widget_ships_with_the_package():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "widgets/*.html" in data["tool"]["setuptools"]["package-data"]["gateway"]
