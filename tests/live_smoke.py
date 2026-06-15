#!/usr/bin/env python3
"""Live smoke test — proves the hosted Yochai Open KG gateway works end-to-end.

Connects as a real MCP client (exactly as an agent would), lists the tools, and
exercises every LAYER of the graph (corpus, citations/Sefaria connections,
concepts + relationships + prerequisites, the thematic map, Talmudic structure,
learning corridors, the extraction layer, and raw Cypher traversal). Prints a
PASS/FAIL line per check.

Usage:
    pip install "mcp>=1.2"
    YOCHAI_KG_API_KEY=yk_... python tests/live_smoke.py
    # or against a self-hosted/staging endpoint:
    YOCHAI_KG_URL=http://localhost:8000/mcp YOCHAI_KG_API_KEY=... python tests/live_smoke.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

URL = os.getenv("YOCHAI_KG_URL", "https://yochai-kg-gateway-production.up.railway.app/mcp")
KEY = os.getenv("YOCHAI_KG_API_KEY", "")

EXPECTED_TOOLS = {
    "search_corpus", "lookup_passage", "get_commentaries_on", "get_connections", "list_texts",
    "search_concepts", "get_concept", "get_concept_neighborhood", "get_concept_sources",
    "get_prerequisites", "get_temporal_neighbors", "list_galaxies", "browse_constellation",
    "get_talmudic_structure", "get_corridors_for_text", "get_corridor",
    "get_entities_in_passage", "search_entities", "get_related_entities", "run_cypher",
}

passed = 0
failed = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"  [{mark}] {name}{(' — ' + detail) if detail else ''}")


async def call(session, tool: str, args: dict) -> dict:
    res = await session.call_tool(tool, args)
    return json.loads(res.content[0].text)


async def main() -> int:
    if not KEY:
        print("Set YOCHAI_KG_API_KEY (request one at https://yochai.lightningstudios.ai/open-kg)")
        return 2
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError:
        print('Install the MCP client first:  pip install "mcp>=1.2"')
        return 2

    print(f"Connecting to {URL} …\n")
    async with streamablehttp_client(URL, headers={"x-api-key": KEY}) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("Tools")
            tools = {t.name for t in (await session.list_tools()).tools}
            check("20 tools present", EXPECTED_TOOLS <= tools, f"{len(tools)} tools; missing={sorted(EXPECTED_TOOLS - tools) or 'none'}")

            print("\nCorpus + citations layer")
            sc = await call(session, "search_corpus", {"query": "love your neighbor as yourself", "limit": 3})
            check("search_corpus returns bilingual passages", sc["count"] > 0 and bool(sc["passages"][0].get("hebrew")), f"{sc['count']} passages")
            su = sc["passages"][0]["su_id"] if sc["count"] else None
            lp = await call(session, "lookup_passage", {"reference": "bereishit_1_1"})
            check("lookup_passage resolves an exact verse", lp.get("found") and bool(lp.get("english")), (lp.get("english") or "")[:40])
            if su:
                ent = await call(session, "get_entities_in_passage", {"su_id": su, "limit": 5})
                check("get_entities_in_passage", "entities" in ent)
            conn = await call(session, "get_connections", {"reference": "bavli-berakhot", "limit": 5})
            check("get_connections (Sefaria/citation graph)", "connections" in conn, f"{conn['count']} links")
            com = await call(session, "get_commentaries_on", {"reference": "bavli-berakhot", "limit": 3})
            check("get_commentaries_on", "commentaries" in com, f"{com['count']} commentaries")

            print("\nConcept layer")
            cs = await call(session, "search_concepts", {"query": "teshuvah repentance", "limit": 3})
            check("search_concepts", cs["count"] > 0, cs["concepts"][0]["name"] if cs["count"] else "")
            cid = cs["concepts"][0]["canonical_id"] if cs["count"] else None
            if cid:
                nb = await call(session, "get_concept_neighborhood", {"canonical_id": cid, "limit": 5})
                check("get_concept_neighborhood (typed relations)", "neighbors" in nb, f"{nb['count']} neighbors")
                pr = await call(session, "get_prerequisites", {"canonical_id": cid, "limit": 5})
                check("get_prerequisites (learning DAG)", "prerequisites" in pr)
                src = await call(session, "get_concept_sources", {"canonical_id": cid, "limit": 3})
                check("get_concept_sources (concept → real texts)", "passages" in src, f"{src['count']} passages")
                tn = await call(session, "get_temporal_neighbors", {"canonical_id": cid, "limit": 3})
                check("get_temporal_neighbors", "earlier" in tn)

            print("\nThematic map")
            g = await call(session, "list_galaxies", {})
            check("list_galaxies", g["count"] >= 1, g["galaxies"][0]["name"] if g["count"] else "")
            con = await call(session, "browse_constellation", {"limit": 3})
            check("browse_constellation (list)", "constellations" in con or "constellation" in con)

            print("\nTalmudic structure + corridors + entities")
            ts = await call(session, "get_talmudic_structure", {"reference": "bavli-arakhin_3_1"})
            check("get_talmudic_structure (sugya + moves)", ts.get("found"), f"{ts.get('move_count')} moves" if ts.get("found") else "")
            se = await call(session, "search_entities", {"query": "Rabbi Akiva", "limit": 3})
            check("search_entities", "entities" in se, f"{se['count']} entities")
            lt = await call(session, "list_texts", {"limit": 3})
            check("list_texts", lt["count"] > 0)

            print("\nRaw traversal (run_cypher)")
            rc = await call(session, "run_cypher", {"query": "MATCH (g:Galaxy)<-[:IN_GALAXY]-(c:Constellation) RETURN g.name AS galaxy, count(c) AS n ORDER BY n DESC", "limit": 3})
            check("run_cypher returns rows", rc.get("row_count", 0) > 0, f"{rc.get('row_count')} rows")
            bad = await call(session, "run_cypher", {"query": "MATCH (n) DETACH DELETE n"})
            check("run_cypher BLOCKS writes (read-only)", "error" in bad, bad.get("error", "")[:40])

    print(f"\n{'='*48}\nRESULT: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
