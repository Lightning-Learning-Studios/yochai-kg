"""Read-only async Neo4j client for the gateway.

Defense in depth: the database itself should be in READ ONLY access mode, but
this client also refuses to send anything that looks like a write clause, so a
self-hoster who forgets the DB toggle still can't mutate the graph through the
gateway.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from . import config

logger = logging.getLogger(__name__)

_driver: AsyncDriver | None = None

# Refuse obvious write/admin clauses. The gateway only ships parameterized read
# queries, but this guards against accidental/malicious write Cypher.
_WRITE_CLAUSE = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH\s+DELETE|SET|REMOVE|DROP|CALL\s*\{[^}]*\b(CREATE|MERGE|SET|DELETE)\b|"
    r"LOAD\s+CSV|FOREACH|CREATE\s+(INDEX|CONSTRAINT)|ALTER|GRANT|DENY|REVOKE)\b",
    re.IGNORECASE,
)


async def get_driver() -> AsyncDriver:
    global _driver
    if _driver is not None:
        return _driver
    if not config.NEO4J_PASSWORD:
        raise ValueError("NEO4J_YOCHAI_PASSWORD is not set")
    _driver = AsyncGraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
        max_connection_pool_size=config.NEO4J_MAX_POOL,
        connection_acquisition_timeout=20.0,
    )
    logger.info("Neo4j driver created (read-only gateway, pool=%d)", config.NEO4J_MAX_POOL)
    return _driver


async def close_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def read(cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Run a read-only Cypher query in an explicit READ transaction."""
    if _WRITE_CLAUSE.search(cypher):
        raise ValueError("Write/admin Cypher is not permitted through the gateway")
    driver = await get_driver()
    async with driver.session(
        database=config.NEO4J_DATABASE,
        default_access_mode="READ",
    ) as session:
        result = await asyncio.wait_for(
            session.run(cypher, params or {}, timeout=config.NEO4J_QUERY_TIMEOUT_SECONDS),
            timeout=config.NEO4J_QUERY_TIMEOUT_SECONDS + 5,
        )
        return await result.data()


async def read_with_vector(
    cypher: str, embedding: list[float], params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    p = dict(params or {})
    p["embedding"] = embedding
    return await read(cypher, p)
