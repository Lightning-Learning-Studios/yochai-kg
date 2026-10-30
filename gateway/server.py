"""Yochai Open KG — MCP gateway server.

Exposes the read-only knowledge-graph tools over MCP. Run locally over stdio
(for Claude Desktop / agent dev) or hosted over Streamable HTTP (the public
endpoint). Free API keys are enforced on the HTTP transport when
GATEWAY_REQUIRE_API_KEY=true.
"""
from __future__ import annotations

import json
import logging
import os
import time

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from . import config, tools

logging.basicConfig(level=logging.INFO)

# Hosted behind a reverse proxy (Railway) with arbitrary forwarded Host headers,
# and gated by our own API key. MCP's DNS-rebinding host check (meant to protect
# localhost servers from malicious web pages) is inapplicable here and rejects the
# proxy host with "Invalid Host header", so disable it for the HTTP transport.
mcp = FastMCP(
    "yochai-kg",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    instructions=(
        "Read-only access to the Yochai knowledge graph of the Jewish textual tradition "
        "(1,000+ works: Tanakh, Talmud, Midrash, Halakha, Kabbalah, Hasidut, philosophy, "
        "responsa and their commentaries). Use search_corpus for meaning-based passage "
        "retrieval, lookup_passage for an exact reference, the concept tools to navigate the "
        "~17,600 canonical concepts and their relationships, and the galaxy/constellation tools "
        "for the thematic map. Every passage is derived study material with a deep link back to "
        "the source — always verify against the primary text; this is not a rabbinic authority."
    ),
)


# --- tool registrations (thin wrappers so descriptions live with the schema) --
@mcp.tool()
async def search_corpus(query: str, text_filter: str | None = None, limit: int | None = None):
    """Semantic search over the corpus. Returns bilingual passages (Hebrew+English)
    with a citation reference and a deep link. Optionally scope to one text by slug
    (text_filter, e.g. 'moreh-nevuchim')."""
    return await tools.search_corpus(query, text_filter, limit)


@mcp.tool()
async def lookup_passage(reference: str):
    """Fetch an exact passage by slug-style reference, e.g. 'bereishit_1_1' or
    'bavli-berakhot_5_1'."""
    return await tools.lookup_passage(reference)


@mcp.tool()
async def search_concepts(query: str, limit: int | None = None):
    """Find canonical concepts by meaning. Returns concept name, definition,
    difficulty, and whether it's a keystone idea."""
    return await tools.search_concepts(query, limit)


@mcp.tool()
async def get_concept(canonical_id: str):
    """Full detail for one canonical concept (definition, guiding question,
    gateway insight, difficulty, traditions, era span)."""
    return await tools.get_concept(canonical_id)


@mcp.tool()
async def get_concept_neighborhood(canonical_id: str, rel_types: list[str] | None = None, limit: int | None = None):
    """Concepts related to this one via typed edges: DEVELOPS, CONTRADICTS,
    RESONATES, EXEMPLIFIES, APPLIES_TO, ADDRESSES, SHARES_METHOD, CONTEXTUALIZES,
    COMMENTARY. Filter with rel_types."""
    return await tools.get_concept_neighborhood(canonical_id, rel_types, limit)


@mcp.tool()
async def get_prerequisites(canonical_id: str, limit: int | None = None):
    """Learning order: concepts to study BEFORE this one, and concepts it unlocks
    (walks the prerequisite DAG)."""
    return await tools.get_prerequisites(canonical_id, limit)


@mcp.tool()
async def list_galaxies():
    """The 11 top-level thematic galaxies — the broadest map of the tradition."""
    return await tools.list_galaxies()


@mcp.tool()
async def browse_constellation(constellation_id: str | None = None, galaxy_id: str | None = None, limit: int | None = None):
    """With a constellation_id: that constellation plus its member concepts.
    Otherwise lists constellations (optionally within a galaxy_id)."""
    return await tools.browse_constellation(constellation_id, galaxy_id, limit)


@mcp.tool()
async def get_commentaries_on(reference: str, limit: int | None = None):
    """Commentary passages on a base text. Pass a base slug ('bavli-berakhot') or
    canonical id ('bavli-berakhot_5_1')."""
    return await tools.get_commentaries_on(reference, limit)


@mcp.tool()
async def get_entities_in_passage(su_id: str, limit: int | None = None):
    """People, places, themes, and concepts mentioned in a semantic unit
    (su_id comes from search_corpus results)."""
    return await tools.get_entities_in_passage(su_id, limit)


@mcp.tool()
async def list_texts(genre: str | None = None, limit: int | None = None):
    """List corpus texts, optionally filtered by genre (e.g. 'commentary',
    'halakhic_code', 'kabbalah')."""
    return await tools.list_texts(genre, limit)


@mcp.tool()
async def search_entities(query: str, entity_type: str | None = None, limit: int | None = None):
    """Search the extraction layer (people, places, themes, concepts, teachings,
    tensions, questions, …) by name/description. Filter by entity_type. This layer is
    machine-extracted — rich evidence, not adjudicated truth."""
    return await tools.search_entities(query, entity_type, limit)


@mcp.tool()
async def get_related_entities(entity_id: str, rel_types: list[str] | None = None, limit: int | None = None):
    """Entity-to-entity relations found within texts: DEVELOPS, CONTRADICTS,
    EXEMPLIFIES, APPLIES_TO, CONTEXTUALIZES, EQUIVALENT."""
    return await tools.get_related_entities(entity_id, rel_types, limit)


@mcp.tool()
async def get_talmudic_structure(reference: str):
    """For a Talmud passage: its sugya (driving question, conclusion/maskana) and the
    ordered dialectical moves (speaker, stratum). Pass a sugya_id or TextUnit
    canonical_id (e.g. 'bavli-arakhin_3_1')."""
    return await tools.get_talmudic_structure(reference)


@mcp.tool()
async def get_corridors_for_text(text_slug: str, limit: int | None = None):
    """List the learning corridors built over a text."""
    return await tools.get_corridors_for_text(text_slug, limit)


@mcp.tool()
async def get_corridor(corridor_id: str, limit: int | None = None):
    """A corridor's ordered learning modules (concept, domain, anchor quote)."""
    return await tools.get_corridor(corridor_id, limit)


@mcp.tool()
async def get_concept_sources(canonical_id: str, limit: int | None = None):
    """The corpus passages that ground a canonical concept — read the texts behind
    the abstraction."""
    return await tools.get_concept_sources(canonical_id, limit)


@mcp.tool()
async def get_temporal_neighbors(canonical_id: str, limit: int | None = None):
    """Chronological context: concepts that historically precede/follow this one
    (distinct from the pedagogical prerequisite order)."""
    return await tools.get_temporal_neighbors(canonical_id, limit)


@mcp.tool()
async def get_connections(reference: str, kinds: list[str] | None = None, limit: int | None = None):
    """The Sefaria/citation connection graph for a passage (CONNECTS_TO): commentary,
    quoting-commentary, midrash, targum, cross-Talmud/Tanakh links, mesorat hashas,
    ein mishpat, and more. Pass a canonical id or text slug; filter by `kinds`."""
    return await tools.get_connections(reference, kinds, limit)


@mcp.tool()
async def run_cypher(query: str, params: dict | None = None, limit: int | None = None):
    """Run your OWN read-only Cypher and traverse the graph freely — the raw doorway.
    Writes/admin are blocked and a LIMIT is enforced. See the schema in docs/schema.md
    for every label, relationship type, and property. Use search_corpus for semantic
    search (vector); use this for structural graph traversal."""
    return await tools.run_cypher(query, params, limit)


# --- HTTP app with free-API-key gate ----------------------------------------
def _ms_since(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _rpc_meta(raw: bytes) -> dict:
    """Pull the JSON-RPC method, tool name and client name out of an MCP request
    body for usage stats. Reads only those three labels; never keeps arguments.
    Malformed bodies yield {} (the MCP layer reports the real error)."""
    try:
        msg = json.loads(raw or b"{}")
    except ValueError:
        return {}
    if isinstance(msg, list):  # JSON-RPC batch (older protocol versions)
        msg = msg[0] if msg else {}
    if not isinstance(msg, dict):
        return {}
    method = msg.get("method")
    params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
    meta: dict = {"rpc_method": method if isinstance(method, str) else None}
    if method == "tools/call" and isinstance(params.get("name"), str):
        meta["tool_name"] = params["name"]
    elif method == "initialize":
        info = params.get("clientInfo")
        if isinstance(info, dict) and isinstance(info.get("name"), str):
            meta["client_name"] = info["name"]
    return meta


def build_http_app():
    """Return the Streamable-HTTP ASGI app: the MCP endpoint at /mcp plus an API-key
    gate that validates against the static allowlist and the Supabase key store.

    Key *issuance* (request form, Slack approval, email) does NOT live here — it's a
    readiverse-haven GCP function (infrastructure/gcp-functions/shared/yochai-kg-access).
    The gateway only validates active keys against the shared yochai_kg_api_keys table.
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    from apikeys import store as key_store

    http_app = mcp.streamable_http_app()

    async def _check_key(provided: str) -> tuple[bool, str | None]:
        """(accepted, Supabase key id). Static allowlist keys have no row, so no id."""
        if provided and provided in config.API_KEYS:
            return True, None
        if key_store.configured():
            key_id = await key_store.validate_key(provided)
            return key_id is not None, key_id
        return False, None

    class ApiKeyMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if not (config.REQUIRE_API_KEY and request.url.path.rstrip("/").endswith("/mcp")):
                return await call_next(request)
            provided = request.headers.get("x-api-key") or ""
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                provided = provided or auth[7:].strip()
            ok, key_id = await _check_key(provided)
            if not ok:
                return JSONResponse({"error": "invalid or missing API key"}, status_code=401)
            if key_id is None:
                return await call_next(request)

            # Usage tracking: metadata only (method / tool / client), never arguments.
            started = time.monotonic()
            meta = _rpc_meta(await request.body()) if request.method == "POST" else {}
            fields = {
                "http_method": request.method,
                "session_id": request.headers.get("mcp-session-id"),
                **meta,
            }
            try:
                response = await call_next(request)
            except Exception:
                key_store.record_usage_soon(key_id, status_code=500,
                                            latency_ms=_ms_since(started), **fields)
                raise
            fields["status_code"] = int(response.status_code)
            # initialize is answered with a brand-new session id; tag it so the
            # client name links to the rest of that session's calls.
            fields["session_id"] = fields["session_id"] or response.headers.get("mcp-session-id")
            # Streamable HTTP may stream the body (SSE), so record when it finishes.
            body = response.body_iterator

            async def _timed_body():
                try:
                    async for chunk in body:
                        yield chunk
                finally:
                    key_store.record_usage_soon(key_id, latency_ms=_ms_since(started), **fields)

            response.body_iterator = _timed_body()
            return response

    http_app.add_middleware(ApiKeyMiddleware)
    return http_app


def main():
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run()  # stdio — for local dev / Claude Desktop
    else:
        import uvicorn

        uvicorn.run(build_http_app(), host=config.HOST, port=config.PORT)


app = None  # lazily built by ASGI servers that import gateway.server:get_app
def get_app():
    global app
    if app is None:
        app = build_http_app()
    return app


if __name__ == "__main__":
    main()
