"""Smoke tests that need no live database.

Verifies the package imports, the limit clamp behaves, the write-Cypher guard
trips, and every MCP tool is registered. Live query tests require NEO4J_* +
DEEPINFRA_API_KEY and are intentionally out of CI.
"""
import pytest

from gateway import config
from gateway.neo4j_client import _WRITE_CLAUSE


def test_clamp_limit_bounds():
    assert config.clamp_limit(None) == config.DEFAULT_LIMIT
    assert config.clamp_limit(0) == config.DEFAULT_LIMIT
    assert config.clamp_limit(9999) == config.MAX_LIMIT
    assert config.clamp_limit(3) == 3


@pytest.mark.parametrize("cypher", [
    "MATCH (n) CREATE (m)",
    "MERGE (n:Text {slug:'x'})",
    "MATCH (n) SET n.x = 1",
    "MATCH (n) DETACH DELETE n",
    "DROP INDEX foo",
    "ALTER DATABASE neo4j SET ACCESS READ WRITE",
])
def test_write_cypher_is_rejected(cypher):
    assert _WRITE_CLAUSE.search(cypher) is not None


@pytest.mark.parametrize("cypher", [
    "MATCH (n:Text) RETURN n LIMIT 5",
    "CALL db.index.vector.queryNodes('semantic_unit_embeddings', 5, $embedding) YIELD node RETURN node",
])
def test_read_cypher_is_allowed(cypher):
    assert _WRITE_CLAUSE.search(cypher) is None


def test_all_tools_registered():
    import asyncio
    from gateway.server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    expected = {
        "search_corpus", "lookup_passage", "search_concepts", "get_concept",
        "get_concept_neighborhood", "get_prerequisites", "list_galaxies",
        "browse_constellation", "get_commentaries_on", "get_entities_in_passage",
        "list_texts",
    }
    assert expected <= names, f"missing tools: {expected - names}"
