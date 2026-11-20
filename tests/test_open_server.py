"""The open server as the directories and the plugin see it. Offline: the graph
is replaced by canned rows, and no network call is made."""
import json
import re
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from gateway import config, open_server
from gateway import open_tools as T
from gateway.limits import RateLimiter, Usage
from gateway.refs import Catalog, TextInfo

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
EXPECTED_TOOLS = {
    "search_passages", "get_passage", "get_commentaries", "get_cross_references", "get_talmud_discussion",
    "search_concepts", "get_concept", "get_related_concepts", "get_learning_path", "get_concept_sources",
    "browse_themes", "list_texts", "get_study_path", "get_jewish_calendar", "list_skills", "load_skill",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(open_server.build_app()) as c:
        yield c


def rpc(client, method, params=None, rpc_id=1):
    body = {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params or {}}
    return client.post("/mcp", headers=HEADERS, content=json.dumps(body))


def call(client, name, arguments=None):
    r = rpc(client, "tools/call", {"name": name, "arguments": arguments or {}})
    assert r.status_code == 200, r.text
    return r.json()["result"]


@pytest.fixture(scope="module")
def tools(client):
    return rpc(client, "tools/list").json()["result"]["tools"]


# --- what the directories check --------------------------------------------------
def test_initialize(client):
    result = rpc(client, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "pytest", "version": "0"}}).json()["result"]
    assert result["serverInfo"]["name"] == "yochai-jewish-texts"
    assert "not a rabbinic authority" in result["instructions"]


def test_exactly_the_planned_tools_and_no_raw_query_door(tools):
    names = {t["name"] for t in tools}
    assert names == EXPECTED_TOOLS
    assert "run_cypher" not in names


def test_every_tool_meets_the_directory_rules(tools):
    for t in tools:
        name = t["name"]
        assert len(name) <= 64 and re.fullmatch(r"[a-z][a-z_]+", name), name
        assert t.get("title"), f"{name} has no title"
        ann = t["annotations"]
        assert ann["readOnlyHint"] is True and ann["destructiveHint"] is False and ann["openWorldHint"] is False, name
        assert ann["title"] == t["title"]
        assert t["description"].startswith("Use this when"), name
        assert len(t["description"]) <= 400, name
        assert t.get("outputSchema", {}).get("type") == "object", f"{name} has no output schema"
        assert t["_meta"]["securitySchemes"] == [{"type": "noauth"}], name
        assert t["inputSchema"]["type"] == "object"
        for prop, schema in t["inputSchema"].get("properties", {}).items():
            assert schema.get("description"), f"{name}.{prop} has no description"


def test_descriptions_describe_and_do_not_command_the_model(tools):
    banned = re.compile(r"\b(you must|always call|never call|ignore (all|any|previous)|do not tell|system prompt)\b", re.IGNORECASE)
    for t in tools:
        assert not banned.search(t["description"]), t["name"]


def test_keyed_gateway_is_unchanged():
    import asyncio

    from gateway.server import mcp as keyed

    names = {t.name for t in asyncio.run(keyed.list_tools())}
    assert "run_cypher" in names and "search_corpus" in names


# --- the plugin and the pipeline agree with the server ------------------------------
def test_skills_only_name_tools_that_exist():
    tool_like = re.compile(r"`((?:get|search|list|load|browse)_[a-z_]+)`")
    folders = list((ROOT / "plugin" / "skills").glob("*/SKILL.md")) + list((ROOT / "shelf").rglob("SKILL.md"))
    assert len(folders) >= 9
    for path in folders:
        named = set(tool_like.findall(path.read_text(encoding="utf-8")))
        assert named <= EXPECTED_TOOLS, f"{path.relative_to(ROOT)} names unknown tools: {sorted(named - EXPECTED_TOOLS)}"


def test_pipeline_knows_the_same_tools():
    import sys

    sys.path.insert(0, str(ROOT))
    import pipeline

    assert set(pipeline.PLUGIN_TOOLS) | set(pipeline.SHELF_TOOLS) == EXPECTED_TOOLS


def test_plugin_points_at_one_fixed_https_server():
    mcp_file = json.loads((ROOT / "plugin" / ".mcp.json").read_text())
    (server,) = mcp_file["mcpServers"].values()
    assert server["type"] == "http" and server["url"].startswith("https://") and server["url"].endswith("/mcp")
    assert "${" not in server["url"]                       # a variable in the address does not load in chat
    manifest = json.loads((ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "yochai-jewish-texts" and not manifest["name"].startswith("claude")


# --- tools that need no graph ---------------------------------------------------
def test_calendar_tool(client):
    result = call(client, "get_jewish_calendar", {"date": "2026-11-20"})
    data = result["structuredContent"]
    assert data["torah_portion"]["name"] == "Vayetzei" and data["daf_yomi"]["label"] == "Arakhin 3"
    assert json.loads(result["content"][0]["text"])["hebrew_date"] == "10 Kislev 5787"
    assert "torah_portion_note" not in data                # empty fields are left out


def test_bad_input_gives_a_message_a_person_can_act_on(client):
    result = call(client, "get_jewish_calendar", {"date": "next Tuesday"})
    assert result["isError"] is True and "YYYY-MM-DD" in result["content"][0]["text"]


def test_skill_shelf_tools(client):
    listing = call(client, "list_skills")["structuredContent"]
    names = {s["name"] for s in listing["skills"]}
    assert "weekly-portion" in names and "hasidic-lens" not in names      # held skills are not served
    loaded = call(client, "load_skill", {"name": "weekly portion"})["structuredContent"]
    assert loaded["found"] and loaded["name"] == "weekly-portion" and "get_jewish_calendar" in loaded["instructions"]
    missing = call(client, "load_skill", {"name": "hasidic-lens"})["structuredContent"]
    assert missing["found"] is False and "list_skills" in missing["message"]


# --- tools over a canned graph ---------------------------------------------------
@pytest.fixture
def graph(monkeypatch):
    catalog = Catalog([TextInfo("bereishit", "Genesis", "tanakh", "", "biblical"),
                       TextInfo("bavli-berakhot", "Berakhot", "talmud_bavli", "", "amoraic"),
                       TextInfo("rashi-on-genesis", "Rashi on Genesis", "commentary", "Rashi", "rishonic")])
    units = {
        "bereishit_22_1": ("וַיְהִי אַחַר", "Some time afterward, God put Abraham to the test.", "sefaria"),
        "bereishit_22_2": ("קַח־נָא אֶת־בִּנְךָ", "Take your son, your favored one, Isaac.", "sefaria"),
        "bavli-berakhot_3_1": ("מֵאֵימָתַי", "From when does one recite Shema in the evening?", "dicta"),
        "bavli-berakhot_3_2": ("עַד סוֹף", "Until the end of the first watch.", "dicta"),
    }

    async def fake_read(cypher, params=None):
        params = params or {}
        if "RETURN tu.canonical_id AS id LIMIT" in cypher:           # the size of a text, for the hint
            return [{"id": k} for k in units if k.startswith(params["slug"] + "_")] + [{"id": "bereishit_50_26"}]
        if "STARTS WITH $p" in cypher:
            keys = [k for k in units if k.startswith(params["p"])]
        elif "IN $ids" in cypher:
            keys = [k for k in params["ids"] if k in units]
        elif "canonical_id: $id" in cypher:
            keys = [params["id"]] if params["id"] in units else []
        else:
            raise AssertionError(f"unexpected query: {cypher[:80]}")
        return [{"canonical_id": k, "text_slug": k.split("_")[0], "hebrew_text": units[k][0],
                 "english_text": units[k][1], "en_source": units[k][2]} for k in keys]

    T.set_catalog_for_tests(catalog)
    monkeypatch.setattr(T, "_read", fake_read)
    yield
    T.set_catalog_for_tests(None)


def test_get_passage_by_plain_reference(client, graph):
    data = call(client, "get_passage", {"reference": "Genesis 22:2"})["structuredContent"]
    assert data["found"] and data["reference"] == "Genesis 22:2" and data["category"] == "tanakh"
    (segment,) = data["segments"]
    assert segment["english"].startswith("Take your son") and segment["hebrew"] and segment["id"] == "bereishit_22_2"
    assert "Sefaria" in data["translation_source"]
    assert data["link"].startswith(f"{config.APP_URL}/p/bereishit_22_2")
    assert "translation_source" not in segment              # said once, not on every verse


def test_get_passage_range_and_talmud_page(client, graph):
    data = call(client, "get_passage", {"reference": "Genesis 22:1-2"})["structuredContent"]
    assert [s["reference"] for s in data["segments"]] == ["Genesis 22:1", "Genesis 22:2"]
    page = call(client, "get_passage", {"reference": "Berachos 2a"})["structuredContent"]
    assert page["reference"] == "Berakhot 2a" and len(page["segments"]) == 2
    assert "machine translation by Dicta" in page["translation_source"]


def test_missing_passage_explains_itself(client, graph):
    data = call(client, "get_passage", {"reference": "Genesis 99:1"})["structuredContent"]
    assert data["found"] is False and data["message"] == "No passage found for 'Genesis 99:1'. Genesis has 50 chapters."
    unknown = call(client, "get_passage", {"reference": "Book of Mormon 1:1"})["structuredContent"]
    assert unknown["found"] is False and "Genesis 22:2" in unknown["message"]
    bare = call(client, "get_passage", {"reference": "Genesis"})["structuredContent"]
    assert bare["found"] is False and "Genesis 1:1" in bare["message"]


def test_a_slow_graph_becomes_a_clear_message(client, graph, monkeypatch):
    async def busy(*_a, **_k):
        raise T.Busy("The library took too long to answer.")

    monkeypatch.setattr(T, "_read", busy)
    result = call(client, "get_passage", {"reference": "Genesis 22:1"})
    assert result["isError"] is True
    assert "Wait a minute and try again" in result["content"][0]["text"]


# --- the gate ---------------------------------------------------------------------
async def _ok_app(scope, receive, send):
    await receive()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"jsonrpc":"2.0","id":1,"result":{}}'})


def _gated(per_minute=2, usage=None):
    return TestClient(open_server.OpenGate(_ok_app, RateLimiter(per_minute, 1000), usage or Usage()))


def test_gate_limits_each_address_and_says_when_to_retry():
    usage = Usage()
    c = _gated(usage=usage)
    body = json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "get_passage"}})
    first = {"x-forwarded-for": "198.51.100.1"}
    assert c.post("/mcp", content=body, headers=first).status_code == 200
    assert c.post("/mcp", content=body, headers=first).status_code == 200
    refused = c.post("/mcp", content=body, headers=first)
    assert refused.status_code == 429 and int(refused.headers["retry-after"]) >= 1
    error = refused.json()
    assert error["id"] == 7 and "Too many requests" in error["error"]["message"]
    assert c.post("/mcp", content=body, headers={"x-forwarded-for": "198.51.100.2"}).status_code == 200
    assert usage.snapshot()["calls_by_tool"] == {"get_passage": 4}


def test_gate_refuses_oversized_bodies_and_ignores_other_paths():
    c = _gated()
    assert c.post("/mcp", content=b"x" * (config.OPEN_MAX_BODY_BYTES + 1)).status_code == 413
    for _ in range(5):
        assert c.post("/elsewhere", content=b"{}").status_code == 200     # only /mcp is limited


def test_rpc_meta_reads_names_and_never_arguments():
    body = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                       "params": {"name": "search_passages", "arguments": {"query": "a private question"}}}).encode()
    meta = open_server.rpc_meta(body)
    assert meta == {"id": 3, "method": "tools/call", "tool": "search_passages", "client_name": None}
    init = json.dumps({"method": "initialize", "params": {"clientInfo": {"name": "claude-ai"}}}).encode()
    assert open_server.rpc_meta(init)["client_name"] == "claude-ai"
    assert open_server.rpc_meta(b"not json") == {} and open_server.rpc_meta(b"[]")["method"] is None


# --- public pages -----------------------------------------------------------------
@pytest.mark.parametrize("path, needle", [("/", "Study Torah, Talmud and more"), ("/privacy", "Privacy"),
                                          ("/terms", "Terms"), ("/support", "Support")])
def test_public_pages(client, path, needle):
    r = client.get(path)
    assert r.status_code == 200 and "text/html" in r.headers["content-type"] and needle in r.text
    assert "DRAFT" not in r.text                           # review notes stay out of the published page


def test_public_skills_feed_matches_the_shelf(client):
    feed = client.get("/skills.json")
    assert feed.status_code == 200 and feed.headers["access-control-allow-origin"] == "*"
    data = feed.json()
    names = [s["name"] for s in data["skills"]]
    assert data["count"] == len(names) >= 9 and "weekly-portion" in names
    assert names == [s["name"] for s in call(client, "list_skills")["structuredContent"]["skills"]]
    for s in data["skills"]:
        assert s["kind"] in ("core", "community") and s["description"]
        assert s["url"].endswith(f"/skills/{s['name']}.md") and "/SKILL.md" in s["source"]
    text = client.get("/skills/weekly-portion.md")
    assert text.status_code == 200 and "text/markdown" in text.headers["content-type"]
    assert "get_jewish_calendar" in text.text and not text.text.startswith("---")
    assert client.get("/skills/hasidic-lens.md").status_code == 404      # held skills are not served
    assert client.get("/skills/..%2Fsecret.md").status_code == 404


def test_health_icon_and_hidden_stats(client):
    assert client.get("/healthz").json()["ok"] is True
    assert client.get("/icon.png").headers["content-type"] == "image/png"
    assert client.get("/stats").status_code == 404         # off unless a token is set


def test_openai_domain_challenge(client, monkeypatch):
    assert client.get("/.well-known/openai-apps-challenge").status_code == 404
    monkeypatch.setattr(config, "OPENAI_APPS_CHALLENGE", "token-123")
    r = client.get("/.well-known/openai-apps-challenge")
    assert r.status_code == 200 and r.text == "token-123"
