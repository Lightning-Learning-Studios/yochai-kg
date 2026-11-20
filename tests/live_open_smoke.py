"""Live check of the open server: every tool, over the real protocol.

    python tests/live_open_smoke.py                       the hosted test server
    python tests/live_open_smoke.py http://127.0.0.1:8000/mcp

It needs no key and no account. It is not collected by pytest, because it calls
a running server. Exit code 0 means every check passed.
"""
from __future__ import annotations

import asyncio
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

DEFAULT_URL = "https://yochai-plugin-test-production.up.railway.app/mcp"

# (tool, arguments, check on the structured result, what the check means)
CHECKS = [
    ("get_jewish_calendar", {"date": "2026-11-20"},
     lambda d: d["torah_portion"]["name"] == "Vayetzei" and d["daf_yomi"]["label"] == "Arakhin 3",
     "20 November 2026 is Vayetzei and Arakhin 3"),
    ("get_passage", {"reference": "Genesis 22:2"},
     lambda d: d["found"] and "Isaac" in d["segments"][0]["english"] and d["segments"][0]["hebrew"]
     and "Sefaria" in d["translation_source"] and "/p/bereishit_22_2" in d["link"],
     "Genesis 22:2 comes back in Hebrew and English with credit and a link"),
    ("get_passage", {"reference": "Pirkei Avot 1:14"},
     lambda d: d["found"] and "If I am not for myself" in d["segments"][0]["english"], "Pirkei Avot 1:14 resolves"),
    ("get_passage", {"reference": "brachos 2a"},
     lambda d: d["found"] and d["reference"] == "Berakhot 2a" and len(d["segments"]) > 1,
     "a Talmud page resolves from an Ashkenazi spelling"),
    ("get_passage", {"reference": "Psalm 23"},
     lambda d: d["found"] and len(d["segments"]) == 6, "a whole chapter resolves"),
    ("get_passage", {"reference": "Genesis 99:1"},
     lambda d: not d["found"] and "50 chapters" in d["message"], "a missing passage explains itself"),
    ("search_passages", {"query": "If I am not for myself, who will be for me?", "limit": 3},
     lambda d: d["count"] >= 1 and d["passages"][0]["reference"] == "Pirkei Avot 1:14",
     "a quote search puts the original source first"),
    ("search_passages", {"query": "what does Judaism say about honoring parents", "limit": 5},
     lambda d: d["count"] >= 3 and any("Kiddushin" in p["reference"] for p in d["passages"])
     and all(p.get("link") for p in d["passages"]),
     "a topic search returns the Talmud's main discussion"),
    ("search_passages", {"query": "best pizza toppings in Chicago"},
     lambda d: d["count"] == 0 and d["message"], "an off-topic search returns nothing, with a reason"),
    ("search_passages", {"query": "repentance", "text": "Rambam Hilchot Teshuva", "limit": 2},
     lambda d: d["count"] >= 1 and all(p["text_title"] == "Mishneh Torah, Repentance" for p in d["passages"]),
     "a search inside one named text stays inside it"),
    ("get_commentaries", {"reference": "Genesis 22:2", "limit": 3},
     lambda d: d["found"] and "Rashi on Genesis" in d["commentators"]
     and d["commentaries"][0]["reference"].startswith("Rashi on Genesis 22:2"),
     "commentaries come back with Rashi first"),
    ("get_cross_references", {"reference": "Genesis 22:2", "limit": 5},
     lambda d: d["found"] and d["kinds_available"].get("Midrash", 0) > 0, "cross-references are grouped by kind"),
    ("get_talmud_discussion", {"reference": "Berakhot 2a"},
     lambda d: d["found"] and "Shema" in d["discussions"][0]["driving_question"] and d["discussions"][0]["moves"],
     "a Talmud discussion has its question and its steps"),
    ("search_concepts", {"query": "repentance", "limit": 3},
     lambda d: d["count"] == 3 and d["concepts"][0]["concept_id"].startswith("cluster_"), "concept search works"),
    ("get_concept", {"concept_id": "cluster_15434"},
     lambda d: d["found"] and d["definition"] and d["related"], "a concept explains itself and lists relatives"),
    ("get_related_concepts", {"concept_id": "cluster_15434", "limit": 3},
     lambda d: d["found"] and d["count"] >= 1, "related concepts come back"),
    ("get_learning_path", {"concept_id": "cluster_15434"},
     lambda d: d["found"] and (d["learn_first"] or d["leads_to"]), "a learning order comes back"),
    ("get_concept_sources", {"concept_id": "cluster_15434", "limit": 2},
     lambda d: d["found"] and d["count"] >= 1 and d["passages"][0]["link"], "a concept has source passages"),
    ("browse_themes", {}, lambda d: d["level"] == "top" and len(d["themes"]) == 11, "there are 11 great themes"),
    ("browse_themes", {"theme_id": "galaxy_05"},
     lambda d: d["level"] == "theme" and len(d["themes"]) > 3, "a theme opens into groups"),
    ("list_texts", {"category": "talmud"},
     lambda d: d["count"] == 36 and d["total_in_library"] > 1000, "the library lists 36 Talmud tractates"),
    ("get_study_path", {"text": "Pirkei Avot", "limit": 3},
     lambda d: d["found"] and d["total_steps"] > 5 and d["steps"][0]["step"] == 1, "a study path comes back in order"),
    ("list_skills", {}, lambda d: d["count"] >= 9 and any(s["name"] == "build-a-course" for s in d["skills"]),
     "the skill shelf lists the core skills"),
    ("load_skill", {"name": "weekly-portion"},
     lambda d: d["found"] and "get_jewish_calendar" in d["instructions"], "a skill loads from the shelf"),
]


async def main(url: str) -> int:
    failed = 0
    started = time.monotonic()
    async with streamablehttp_client(url) as (read, write, _), ClientSession(read, write) as session:
        init = await session.initialize()
        tools = (await session.list_tools()).tools
        print(f"{init.serverInfo.name} at {url}: {len(tools)} tools")
        seen = set()
        for name, arguments, check, meaning in CHECKS:
            seen.add(name)
            t0 = time.monotonic()
            try:
                result = await session.call_tool(name, arguments)
                ok = not result.isError and bool(check(result.structuredContent or {}))
                detail = "" if ok else f"  got: {str(result.structuredContent or result.content)[:300]}"
            except Exception as e:  # noqa: BLE001 - report every failure and keep going
                ok, detail = False, f"  error: {e}"
            failed += not ok
            print(f"  {'PASS' if ok else 'FAIL'}  {name:<22} {int((time.monotonic() - t0) * 1000):>5} ms  {meaning}{detail}")
        missing = {t.name for t in tools} - seen
        if missing:
            failed += 1
            print(f"  FAIL  no live check covers: {sorted(missing)}")
        bad = await session.call_tool("get_jewish_calendar", {"date": "next Tuesday"})
        ok = bad.isError and "YYYY-MM-DD" in bad.content[0].text
        failed += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  bad input returns a message a person can act on")
    print(f"{len(CHECKS) + 2 - failed} of {len(CHECKS) + 2} checks passed in {time.monotonic() - started:.1f} s")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL)))
