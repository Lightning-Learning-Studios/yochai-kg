"""Query embedding via DeepInfra BGE-M3 (1024-dim), matching production Yochai.

Used to embed the caller's natural-language query so we can run the same vector
ANN the live app uses. Ported from railway-yochai-service/rag/embeddings.py and
trimmed to the read path.
"""
from __future__ import annotations

import hashlib
import logging

import httpx

from . import config

logger = logging.getLogger(__name__)

_cache: dict[str, list[float]] = {}
_MAX_CACHE = 512


async def embed_query(text: str) -> list[float]:
    """Return a normalized 1024-dim embedding for `text`."""
    if not config.DEEPINFRA_API_KEY:
        raise ValueError("DEEPINFRA_API_KEY is not set")
    if not text or not text.strip():
        raise ValueError("Query text cannot be empty")

    text = text[:8000]
    key = hashlib.sha256(text.encode()).hexdigest()[:16]
    if key in _cache:
        return _cache[key]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            config.DEEPINFRA_API_URL,
            headers={"Authorization": f"Bearer {config.DEEPINFRA_API_KEY}"},
            json={"inputs": [text], "normalize": True},
        )
        resp.raise_for_status()
        data = resp.json()

    embeddings = data.get("embeddings") or []
    if not embeddings or len(embeddings[0]) != config.EMBEDDING_DIMENSION:
        raise RuntimeError(f"Unexpected embedding response shape: {list(data)[:4]}")

    vec = embeddings[0]
    if len(_cache) < _MAX_CACHE:
        _cache[key] = vec
    return vec
