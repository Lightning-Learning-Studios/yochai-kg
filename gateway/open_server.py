"""Yochai: Jewish Texts. The open MCP server behind the Claude and ChatGPT plugin.

No sign-in. Sixteen read-only tools over the Yochai library and knowledge
graph, plus the public pages the directories ask for. Run it with:

    uvicorn gateway.open_server:get_app --factory --host 0.0.0.0 --port $PORT

The keyed developer gateway (gateway.server, with run_cypher and API keys) is a
separate app and is not changed by this module.
"""
from __future__ import annotations

import asyncio
import functools
import json
import logging
import re
import time
from pathlib import Path
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response

from . import config
from . import models as M
from . import open_tools as T
from .limits import RateLimiter, Usage, client_label, flush_usage_forever

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("yochai.open")

# The open server gets its own small share of database connections.
config.NEO4J_MAX_POOL = config.OPEN_NEO4J_MAX_POOL

VERSION = "0.1.0"
PAGES = Path(__file__).resolve().parent / "pages"
ICON = Path(__file__).resolve().parent.parent / "plugin" / ".claude-plugin" / "icon.png"

mcp = FastMCP(
    "yochai-jewish-texts",
    instructions=(
        "Yochai is a library of more than 1,000 Jewish texts in Hebrew and English: Tanakh, Mishnah, Talmud, "
        "Midrash, law codes, philosophy, Kabbalah, Hasidut and their commentaries, joined by a map of about "
        "17,600 concepts. The tools find and quote real passages, show commentaries and cross-references, map "
        "Talmud discussions, trace how ideas relate, and report the Jewish calendar. Every passage comes with "
        "its reference, the source of its English translation and a link to read it on yochai.wiki. Yochai is "
        "a study aid, not a rabbinic authority."
    ),
    website_url="https://www.yochai.wiki",
    stateless_http=True,
    json_response=True,
    # Hosted behind a proxy with forwarded Host headers; the localhost DNS-rebinding
    # check does not apply to a public server.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_NO_AUTH = {"securitySchemes": [{"type": "noauth"}]}


def tool(name: str, title: str):
    """Register a read-only tool with the annotations both directories require,
    and turn internal failures into messages a person can act on."""

    def wrap(fn):
        @functools.wraps(fn)
        async def guarded(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except ToolError:
                raise
            except ValueError as e:
                raise ToolError(str(e)) from e
            except T.Busy as e:
                raise ToolError(f"{e} Wait a minute and try again. Nothing is wrong with the request.") from e
            except Exception as e:
                log.exception("tool %s failed", name)
                raise ToolError("Yochai could not complete this request. Try again, or rephrase it.") from e

        return mcp.tool(name=name, title=title, annotations=ToolAnnotations(title=title, **_READ_ONLY),
                        meta=_NO_AUTH, structured_output=True)(guarded)

    return wrap


Ref = Annotated[str, Field(description="A passage reference such as 'Genesis 22:2', 'Psalms 23', 'Berakhot 2a', "
                                       "'Pirkei Avot 1:14' or 'Rashi on Genesis 22:2'. An id returned by another "
                                       "tool also works.")]
ConceptId = Annotated[str, Field(description="A concept id from search_concepts, for example 'cluster_123'.")]


@tool("search_passages", "Search Jewish texts")
async def search_passages(
    query: Annotated[str, Field(description="A topic, question or phrase in English or Hebrew.")],
    text: Annotated[str | None, Field(description="Optional. Limit the search to one text, by title, for example "
                                                  "'Mishneh Torah, Repentance' or 'Pirkei Avot'.")] = None,
    limit: Annotated[int | None, Field(description="How many passages to return. Default 6, maximum 12.")] = None,
) -> M.SearchPassagesResult:
    """Use this when the user asks what Jewish sources say about a topic, wants a source for an idea, or half
    remembers a quote. Searches by meaning across more than 1,000 texts and returns real passages in Hebrew and
    English with their reference, translation source and a link."""
    return await T.search_passages(query, text, limit)


@tool("get_passage", "Read a passage")
async def get_passage(reference: Ref) -> M.PassageResult:
    """Use this when the user names a specific verse, chapter, Mishnah or Talmud page and wants to read or check
    it. Returns the exact text in Hebrew and English with a link. Accepts a single verse, a range such as
    'Genesis 22:1-19', a whole chapter, or a Talmud page."""
    return await T.get_passage(reference)


@tool("get_commentaries", "Read commentaries on a passage")
async def get_commentaries(
    reference: Ref,
    commentator: Annotated[str | None, Field(description="Optional. One commentator, for example 'Rashi' or 'Ramban'.")] = None,
    limit: Annotated[int | None, Field(description="How many notes to return. Default 8, maximum 20.")] = None,
) -> M.CommentariesResult:
    """Use this when the user asks how the classical commentators read a verse or a Talmud passage, or asks for
    one commentator by name. Returns the commentators' own words and the list of every commentator available on
    that passage."""
    return await T.get_commentaries(reference, commentator, limit)


@tool("get_cross_references", "Find linked passages")
async def get_cross_references(
    reference: Ref,
    kinds: Annotated[list[str] | None, Field(description="Optional. Kinds of link to keep, for example "
                                                         "['Midrash', 'Talmud', 'Halakhah'].")] = None,
    limit: Annotated[int | None, Field(description="How many links to return. Default 8, maximum 20.")] = None,
) -> M.CrossReferencesResult:
    """Use this when the user wants to know where else a verse or passage is quoted, retold or applied: in
    Midrash, in the Talmud, in law codes or in later thought. Returns the linked passages with a short excerpt
    and a count of links by kind."""
    return await T.get_cross_references(reference, kinds, limit)


@tool("get_talmud_discussion", "Map a Talmud discussion")
async def get_talmud_discussion(
    reference: Annotated[str, Field(description="A Babylonian Talmud page such as 'Berakhot 2a', or a discussion id "
                                                "returned by this tool.")],
) -> M.TalmudDiscussionResult:
    """Use this when the user is studying a page of Talmud and wants the shape of the argument: the question that
    drives it, each step in order with its speaker, and where it ends. Covers the Babylonian Talmud."""
    return await T.get_talmud_discussion(reference)


@tool("search_concepts", "Search ideas in Jewish thought")
async def search_concepts(
    query: Annotated[str, Field(description="An idea or theme, for example 'repentance', 'free will' or "
                                            "'saving a life'.")],
    limit: Annotated[int | None, Field(description="How many concepts to return. Default 8, maximum 20.")] = None,
) -> M.SearchConceptsResult:
    """Use this when the user wants to explore an idea in Jewish thought and the map of related ideas matters
    more than one quote. Returns matching concepts with a one-line definition and an id for the other concept
    tools."""
    return await T.search_concepts(query, limit)


@tool("get_concept", "Explain a concept")
async def get_concept(concept_id: ConceptId) -> M.ConceptResult:
    """Use this when a concept id is known and the user wants it explained. Returns the definition, the question
    the concept answers, its key insight, its historical span and the closest related concepts."""
    return await T.get_concept(concept_id)


@tool("get_related_concepts", "Find related concepts")
async def get_related_concepts(
    concept_id: ConceptId,
    relation: Annotated[str | None, Field(description="Optional. One of DEVELOPS, CONTRADICTS, RESONATES, EXEMPLIFIES, "
                                                      "APPLIES_TO, ADDRESSES, SHARES_METHOD, CONTEXTUALIZES, COMMENTARY.")] = None,
    limit: Annotated[int | None, Field(description="How many concepts to return. Default 8, maximum 20.")] = None,
) -> M.RelatedConceptsResult:
    """Use this when the user asks who disagrees with an idea, what develops it, or what it resembles. Returns
    concepts linked to the given one, each with the kind of link. Pass relation CONTRADICTS for opposing views."""
    return await T.get_related_concepts(concept_id, relation, limit)


@tool("get_learning_path", "Plan what to learn first")
async def get_learning_path(concept_id: ConceptId) -> M.LearningPathResult:
    """Use this when the user asks where to start, what to learn before a topic, or what to study next. Returns
    the concepts to learn first and the concepts this one leads to."""
    return await T.get_learning_path(concept_id)


@tool("get_concept_sources", "Read the sources behind a concept")
async def get_concept_sources(
    concept_id: ConceptId,
    limit: Annotated[int | None, Field(description="How many passages to return. Default 5, maximum 10.")] = None,
) -> M.ConceptSourcesResult:
    """Use this when the user wants the primary texts behind a concept. Returns the passages that ground it, in
    Hebrew and English, drawn from different texts where possible."""
    return await T.get_concept_sources(concept_id, limit)


@tool("browse_themes", "Browse the map of Jewish thought")
async def browse_themes(
    theme_id: Annotated[str | None, Field(description="Optional. Leave empty for the 11 great themes. Pass an id from a "
                                                      "previous call ('galaxy_03' or 'constellation_0042') to go one "
                                                      "level down.")] = None,
) -> M.BrowseThemesResult:
    """Use this when the user wants an overview, asks what there is to learn, or wants to browse without a
    question in mind. Returns the 11 great themes of the tradition, then the groups inside a theme, then the
    concepts inside a group."""
    return await T.browse_themes(theme_id)


@tool("list_texts", "List the texts in the library")
async def list_texts(
    category: Annotated[str | None, Field(description="Optional. For example tanakh, mishnah, talmud_bavli, "
                                                      "midrash_aggadah, halakhic_code, philosophy, kabbalah, hasidut, "
                                                      "mussar, commentary, responsa, liturgy.")] = None,
    search: Annotated[str | None, Field(description="Optional. Words from a title or an author's name.")] = None,
    limit: Annotated[int | None, Field(description="How many texts to list. Default 40, maximum 80.")] = None,
) -> M.ListTextsResult:
    """Use this when the user asks whether a book is in the library, what texts are available, or how a title is
    spelled here. Returns titles with author, era and category, and the count of texts in every category."""
    return await T.list_texts(category, search, limit)


@tool("get_study_path", "Get a guided path through a text")
async def get_study_path(
    text: Annotated[str, Field(description="The title of a text, for example 'Pirkei Avot' or 'Mesillat Yesharim'.")],
    start: Annotated[int | None, Field(description="Optional. The step to start from. Default 1.")] = None,
    limit: Annotated[int | None, Field(description="How many steps to return. Default 12, maximum 25.")] = None,
) -> M.StudyPathResult:
    """Use this when the user wants to work through one text in order, or wants a course or reading plan built on
    a text. Returns the ordered steps of that text's study path: the idea of each step, a summary and its anchor
    quote."""
    return await T.get_study_path(text, start, limit)


@tool("get_jewish_calendar", "Check the Jewish calendar")
async def get_jewish_calendar(
    date: Annotated[str | None, Field(description="Optional. A civil date as YYYY-MM-DD. Default is today (UTC).")] = None,
    israel: Annotated[bool | None, Field(description="Optional. True for the reading schedule followed in Israel. "
                                                     "Default false (the diaspora schedule).")] = None,
) -> M.CalendarResult:
    """Use this when the user asks about this week's Torah portion, today's Daf Yomi page, the Hebrew date or an
    upcoming holiday. Returns all four for the given date, with references that get_passage accepts."""
    return await T.get_jewish_calendar(date, israel)


@tool("list_skills", "List Yochai study skills")
async def list_skills() -> M.ListSkillsResult:
    """Use this when the user asks what Yochai can do, asks for study methods, or names a method that may be a
    community skill. Returns the study skills on the shelf: the core Yochai skills and the community skills
    approved through Yochai Create, each with its author."""
    return await T.list_skills()


@tool("load_skill", "Open a Yochai study skill")
async def load_skill(
    name: Annotated[str, Field(description="The skill name from list_skills, for example 'prepare-to-teach'.")],
) -> M.LoadSkillResult:
    """Use this when the user picks a study skill from the shelf. Returns the full text of that skill: a study
    method, with its author and licence."""
    return await T.load_skill(name)


# --- public pages -----------------------------------------------------------------
_CSS = ("body{font:17px/1.6 Georgia,serif;max-width:720px;margin:48px auto;padding:0 20px;color:#22201c;"
        "background:#fbf8f1}h1,h2,h3{font-family:system-ui,sans-serif;line-height:1.25}a{color:#7a4b12}"
        "code{background:#efe9da;padding:1px 5px;border-radius:4px}table{border-collapse:collapse}"
        "td,th{border:1px solid #d9d0bb;padding:6px 10px;text-align:left}footer{margin-top:48px;font-size:14px;"
        "color:#6b6557}@media(prefers-color-scheme:dark){body{background:#1b1a17;color:#ece7da}a{color:#e0b574}"
        "code{background:#2c2a25}td,th{border-color:#45413a}footer{color:#a39c8c}}")


def _page(name: str, title: str) -> Response:
    path = PAGES / f"{name}.md"
    if not path.is_file():
        return PlainTextResponse("Not found", status_code=404)
    import markdown

    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    body = markdown.markdown(text, extensions=["tables"])
    html = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width,initial-scale=1'><title>{title} | Yochai: Jewish Texts</title>"
            f"<style>{_CSS}</style></head><body>{body}<footer><a href='/'>Yochai: Jewish Texts</a> · "
            f"<a href='/privacy'>Privacy</a> · <a href='/terms'>Terms</a> · <a href='/support'>Support</a></footer>"
            f"</body></html>")
    return HTMLResponse(html, headers={"Cache-Control": "public, max-age=600"})


@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def home(_: Request) -> Response:
    return _page("home", "Study Torah, Talmud and more")


@mcp.custom_route("/privacy", methods=["GET"], include_in_schema=False)
async def privacy(_: Request) -> Response:
    return _page("privacy", "Privacy")


@mcp.custom_route("/terms", methods=["GET"], include_in_schema=False)
async def terms(_: Request) -> Response:
    return _page("terms", "Terms")


@mcp.custom_route("/support", methods=["GET"], include_in_schema=False)
async def support(_: Request) -> Response:
    return _page("support", "Support")


@mcp.custom_route("/icon.png", methods=["GET"], include_in_schema=False)
async def icon(_: Request) -> Response:
    if not ICON.is_file():
        return PlainTextResponse("Not found", status_code=404)
    return Response(ICON.read_bytes(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


# --- the public skills feed -----------------------------------------------------------
# The same shelf the assistants read, as plain web addresses. Yochai Create shows its
# community skills from this feed, so this repository is the one source for both.
_FEED_HEADERS = {"Cache-Control": "public, max-age=300", "Access-Control-Allow-Origin": "*"}
_REPO_TREE = "https://github.com/Lightning-Learning-Studios/yochai-kg/tree/main"


def _skill_record(skill, base: str) -> dict[str, Any]:
    folder = "plugin/skills" if skill.kind == "core" else "shelf/community"
    return {
        "name": skill.name,
        "kind": skill.kind,
        "description": skill.description,
        "author": skill.author or None,
        "licence": skill.licence or None,
        "url": f"{base}/skills/{skill.name}.md",
        "source": f"{_REPO_TREE}/{folder}/{skill.name}/SKILL.md",
    }


@mcp.custom_route("/skills.json", methods=["GET"], include_in_schema=False)
async def skills_feed(request: Request) -> Response:
    base = config.OPEN_PUBLIC_URL or str(request.base_url).rstrip("/")
    skills = sorted(T._shelf().values(), key=lambda s: (s.kind != "core", s.name))
    return JSONResponse({"count": len(skills), "skills": [_skill_record(s, base) for s in skills]},
                        headers=_FEED_HEADERS)


@mcp.custom_route("/skills/{name}.md", methods=["GET"], include_in_schema=False)
async def skill_text(request: Request) -> Response:
    skill = T._shelf().get(request.path_params["name"].lower())
    if skill is None:
        return PlainTextResponse("No skill with that name is on the shelf.", status_code=404, headers=_FEED_HEADERS)
    return PlainTextResponse(skill.body + "\n", media_type="text/markdown; charset=utf-8", headers=_FEED_HEADERS)


@mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)
async def healthz(_: Request) -> Response:
    return JSONResponse({"ok": True, "server": "yochai-jewish-texts", "version": VERSION})


@mcp.custom_route("/.well-known/openai-apps-challenge", methods=["GET"], include_in_schema=False)
async def openai_challenge(_: Request) -> Response:
    if not config.OPENAI_APPS_CHALLENGE:
        return PlainTextResponse("Not configured", status_code=404)
    return PlainTextResponse(config.OPENAI_APPS_CHALLENGE)


usage = Usage()


@mcp.custom_route("/stats", methods=["GET"], include_in_schema=False)
async def stats(request: Request) -> Response:
    token = config.OPEN_STATS_TOKEN
    if not token or request.headers.get("authorization", "") != f"Bearer {token}":
        return PlainTextResponse("Not found", status_code=404)
    snap = usage.snapshot()
    snap["cache"] = {"hits": T._cache.hits, "misses": T._cache.misses}
    return JSONResponse(snap)


# --- the gate in front of /mcp ------------------------------------------------------
def rpc_meta(body: bytes) -> dict[str, Any]:
    """Pull the JSON-RPC method, tool name, client name and id out of a request
    body. Arguments are never read."""
    try:
        data = json.loads(body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return {}
    if isinstance(data, list):
        data = data[0] if data and isinstance(data[0], dict) else {}
    if not isinstance(data, dict):
        return {}
    params = data.get("params") if isinstance(data.get("params"), dict) else {}
    info = params.get("clientInfo") if isinstance(params.get("clientInfo"), dict) else {}
    method = data.get("method") if isinstance(data.get("method"), str) else None
    return {
        "id": data.get("id"),
        "method": method,
        "tool": params.get("name") if method == "tools/call" and isinstance(params.get("name"), str) else None,
        "client_name": info.get("name") if isinstance(info.get("name"), str) else None,
    }


def _address(scope: dict[str, Any], headers: dict[str, str]) -> str:
    forwarded = headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return headers.get("x-real-ip") or (scope.get("client") or ("unknown", 0))[0]


class OpenGate:
    """Pure ASGI middleware: size cap, rate limit, in-flight cap and usage counts
    for the MCP endpoint. Every other path passes straight through."""

    def __init__(self, app, limiter: RateLimiter | None = None, usage_counter: Usage | None = None):
        self.app = app
        self.limiter = limiter or RateLimiter(config.OPEN_RATE_PER_MINUTE, config.OPEN_RATE_PER_DAY)
        self.usage = usage_counter or usage
        self.in_flight = 0
        self._flusher: asyncio.Task | None = None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").rstrip("/").endswith("/mcp"):
            return await self.app(scope, receive, send)
        if self._flusher is None:
            self._flusher = asyncio.get_running_loop().create_task(flush_usage_forever(self.usage))
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        if scope["method"] != "POST":
            return await self.app(scope, receive, send)

        body = b""
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body += message.get("body", b"")
            more = message.get("more_body", False)
            if len(body) > config.OPEN_MAX_BODY_BYTES:
                return await self._refuse(send, 413, None, "The request is too large.", None)

        meta = rpc_meta(body)
        caller = self.usage.caller_id(_address(scope, headers))
        client = client_label(headers.get("user-agent"), meta.get("client_name"))
        allowed, wait = self.limiter.check(caller)
        if not allowed:
            self.usage.record(rpc_method=meta.get("method"), tool=meta.get("tool"), client=client, caller=caller,
                              ok=False, latency_ms=0)
            return await self._refuse(send, 429, meta.get("id"),
                                      f"Too many requests from this network. Try again in {wait} seconds.", wait)
        if self.in_flight >= config.OPEN_MAX_IN_FLIGHT:
            return await self._refuse(send, 503, meta.get("id"),
                                      "Yochai is handling many requests. Try again in a few seconds.", 5)

        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        status = 500
        tool_error = False

        async def capture(message):
            nonlocal status, tool_error
            if message["type"] == "http.response.start":
                status = message["status"]
            elif message["type"] == "http.response.body" and b'"isError":true' in message.get("body", b""):
                tool_error = True
            await send(message)

        started = time.monotonic()
        self.in_flight += 1
        try:
            await self.app(scope, replay, capture)
        finally:
            self.in_flight -= 1
            self.usage.record(rpc_method=meta.get("method"), tool=meta.get("tool"), client=client, caller=caller,
                              ok=status < 400 and not tool_error, latency_ms=int((time.monotonic() - started) * 1000))

    @staticmethod
    async def _refuse(send, status: int, rpc_id: Any, message: str, retry_after: int | None) -> None:
        payload = json.dumps({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": message}}).encode()
        headers = [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode())]
        if retry_after:
            headers.append((b"retry-after", str(retry_after).encode()))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": payload})


def build_app():
    app = mcp.streamable_http_app()
    app.add_middleware(OpenGate)
    return app


_app = None


def get_app():
    global _app
    if _app is None:
        _app = build_app()
    return _app


def main() -> None:
    import os

    if os.getenv("MCP_TRANSPORT", "http") == "stdio":
        mcp.run()
    else:
        import uvicorn

        uvicorn.run(get_app(), host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
