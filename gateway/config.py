"""Configuration for the Yochai Open KG MCP gateway.

All secrets come from environment variables — see .env.example. Nothing here
is ever written to the graph; the gateway is read-only by construction.
"""
from __future__ import annotations

import os

# --- Neo4j (read-only) -------------------------------------------------------
# Point this at a database whose ACCESS is set to READ ONLY
# (`ALTER DATABASE neo4j SET ACCESS READ ONLY`). The gateway never issues writes.
NEO4J_URI = os.getenv("NEO4J_YOCHAI_URI", "")
NEO4J_USER = os.getenv("NEO4J_YOCHAI_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_YOCHAI_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_YOCHAI_DATABASE", "neo4j")

# Keep the gateway's pool small so public traffic can never starve the
# connection budget of the production chat service sharing the instance.
NEO4J_MAX_POOL = int(os.getenv("GATEWAY_NEO4J_MAX_POOL", "12"))
NEO4J_QUERY_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_NEO4J_QUERY_TIMEOUT_SECONDS", "10"))

# --- Embeddings (DeepInfra BGE-M3, 1024-dim) ---------------------------------
DEEPINFRA_API_URL = "https://api.deepinfra.com/v1/inference/BAAI/bge-m3"
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY", "")
EMBEDDING_DIMENSION = 1024

# --- Retrieval defaults (match production Yochai) ----------------------------
SIMILARITY_THRESHOLD = float(os.getenv("GATEWAY_SIMILARITY_THRESHOLD", "0.40"))
DEFAULT_LIMIT = int(os.getenv("GATEWAY_DEFAULT_LIMIT", "8"))
MAX_LIMIT = int(os.getenv("GATEWAY_MAX_LIMIT", "25"))  # hard cap on every tool's result count

# --- Deep links --------------------------------------------------------------
APP_URL = os.getenv("YOCHAI_APP_URL", "https://www.yochai.wiki").rstrip("/")

# --- Gateway auth (free API keys) --------------------------------------------
# Comma-separated allowlist of accepted keys. When REQUIRE_API_KEY is false
# (default, for local dev) all requests are allowed.
REQUIRE_API_KEY = os.getenv("GATEWAY_REQUIRE_API_KEY", "false").lower() in {"1", "true", "yes"}
API_KEYS = {k.strip() for k in os.getenv("GATEWAY_API_KEYS", "").split(",") if k.strip()}

# --- HTTP server -------------------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


def clamp_limit(requested: int | None) -> int:
    """Clamp any caller-supplied limit into [1, MAX_LIMIT]."""
    if not requested or requested < 1:
        return DEFAULT_LIMIT
    return min(int(requested), MAX_LIMIT)


# --- Open (no sign-in) server -------------------------------------------------
# The plugin door: gateway.open_server. It shares the Neo4j instance with the
# live Yochai app, so its pool and its concurrency are deliberately small.
OPEN_NEO4J_MAX_POOL = int(os.getenv("OPEN_NEO4J_MAX_POOL", "8"))
OPEN_DB_CONCURRENCY = int(os.getenv("OPEN_DB_CONCURRENCY", "6"))
OPEN_RATE_PER_MINUTE = int(os.getenv("OPEN_RATE_PER_MINUTE", "240"))   # per network address
OPEN_RATE_PER_DAY = int(os.getenv("OPEN_RATE_PER_DAY", "40000"))
OPEN_MAX_IN_FLIGHT = int(os.getenv("OPEN_MAX_IN_FLIGHT", "48"))        # whole server
# Lowest vector score a search hit may have (Neo4j reports cosine as (1 + cos) / 2).
# Measured on the live graph: on-topic questions score 0.80 to 0.85, off-topic ones 0.71 to 0.74.
OPEN_MIN_SCORE = float(os.getenv("OPEN_MIN_SCORE", "0.76"))
OPEN_CACHE_SECONDS = float(os.getenv("OPEN_CACHE_SECONDS", "900"))
OPEN_CACHE_ITEMS = int(os.getenv("OPEN_CACHE_ITEMS", "3000"))
OPEN_CATALOG_SECONDS = float(os.getenv("OPEN_CATALOG_SECONDS", "21600"))
OPEN_MAX_BODY_BYTES = int(os.getenv("OPEN_MAX_BODY_BYTES", "65536"))
# Shown by /.well-known/openai-apps-challenge for ChatGPT domain verification.
OPENAI_APPS_CHALLENGE = os.getenv("OPENAI_APPS_CHALLENGE", "")
# Bearer token for the /stats page. The page is off when this is empty.
OPEN_STATS_TOKEN = os.getenv("OPEN_STATS_TOKEN", "")
OPEN_PUBLIC_URL = os.getenv("OPEN_PUBLIC_URL", "").rstrip("/")
