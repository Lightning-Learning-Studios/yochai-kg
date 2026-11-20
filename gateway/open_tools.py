"""The tools behind the open (no sign-in) server.

Every function is read-only, returns a model from gateway.models, caps its
output, credits the translation and links back to the Yochai reader. Human
references ("Genesis 22:2", "Berakhot 2a") are resolved by gateway.refs.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import re
import time
from typing import Any

from . import config, jcalendar, shelf
from . import models as M
from .embeddings import embed_query
from .limits import TTLCache
from .neo4j_client import read, read_with_vector
from .refs import _TANAKH, Catalog, ParsedRef, TextInfo, daf_label, label_for_id
from .tools import _SU_FIELDS, _reference

log = logging.getLogger("yochai.open")

# --- caps ----------------------------------------------------------------------
SEGMENT_CHARS = 2400       # per language, per verse or line
RESPONSE_CHARS = 14000     # passage text in one response, both languages together
SEARCH_DEFAULT, SEARCH_MAX = 6, 12
LIST_DEFAULT, LIST_MAX = 8, 20
QUERY_CHARS = 500

_cache = TTLCache(max_items=config.OPEN_CACHE_ITEMS, ttl_seconds=config.OPEN_CACHE_SECONDS)
_db_gate = asyncio.Semaphore(config.OPEN_DB_CONCURRENCY)
_catalog: Catalog | None = None
_catalog_loaded = 0.0
_catalog_lock = asyncio.Lock()
_skills: dict[str, shelf.Skill] | None = None

# Commentators shown first when a verse has many.
_COMMENTATOR_ORDER = ("rashi", "ramban", "ibn-ezra", "rashbam", "sforno", "radak", "tosafot", "ohr-hachaim",
                      "kli-yakar", "malbim", "shadal", "haamek-davar", "steinsaltz")
RELATIONS = ("DEVELOPS", "CONTRADICTS", "RESONATES", "EXEMPLIFIES", "APPLIES_TO", "ADDRESSES",
             "SHARES_METHOD", "CONTEXTUALIZES", "COMMENTARY")


class Busy(Exception):
    """The library could not answer in time. The server turns this into a clear message."""


# --- small helpers ---------------------------------------------------------------
def _limit(requested: int | None, default: int, maximum: int) -> int:
    if not requested or requested < 1:
        return default
    return min(int(requested), maximum)


def link_for(anchor: str | None) -> str | None:
    if not anchor:
        return None
    return f"{config.APP_URL}/p/{anchor}?utm_source=yochai-plugin&utm_medium=mcp"


def text_link(slug: str | None) -> str | None:
    return f"{config.APP_URL}/?utm_source=yochai-plugin&utm_medium=mcp&text={slug}" if slug else None


def credit(en_source: str | None, english: str | None) -> str | None:
    """Plain statement of where the English came from."""
    if not english:
        return None
    s = (en_source or "").lower()
    if s.startswith("sefaria"):
        return "English from the Sefaria library (sefaria.org), shown under Yochai's display licence."
    if s == "dicta":
        return "English is a machine translation by Dicta (dicta.org.il). Check it against the Hebrew."
    if s in ("", "unknown"):
        return "English translation source not recorded. Check it against the Hebrew."
    if s == "translator":
        return "English by a Yochai translator."
    return "English is an AI-assisted translation prepared for Yochai. Check it against the Hebrew."


_HEBREW_CHARS = re.compile(r"[\u05d0-\u05ea]")


def clean_english(text: str | None) -> str | None:
    """Drop 'English' that is a failed-translation marker or is really Hebrew."""
    if not text:
        return None
    s = text.strip()
    if not s or s.startswith("[[FAILED TO TRANSLATE"):
        return None
    if len(_HEBREW_CHARS.findall(s)) > 0.5 * len(s):
        return None
    return s


def _clip(text: str | None, budget: list[int]) -> tuple[str | None, bool]:
    """Cut `text` to the segment cap and the remaining response budget."""
    if not text:
        return None, False
    room = min(SEGMENT_CHARS, max(budget[0], 0))
    if len(text) <= room:
        budget[0] -= len(text)
        return text, False
    budget[0] -= room
    cut = text[:room].rsplit(" ", 1)[0] if room > 40 else text[:room]
    return (cut + " […]") if cut else None, True


async def _read(cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        async with _db_gate:
            return await read(cypher, params)
    except TimeoutError as e:
        raise Busy("The library took too long to answer.") from e
    except ValueError:
        raise
    except Exception as e:
        log.warning("graph read failed: %s", str(e)[:300])
        raise Busy("The library is not reachable right now.") from e


async def _cached(key: str, make):
    hit = _cache.get(key)
    if hit is not None:
        return hit
    value = await make()
    _cache.put(key, value)
    return value


async def get_catalog() -> Catalog:
    """The list of texts, loaded once and refreshed every few hours."""
    global _catalog, _catalog_loaded
    if _catalog and time.monotonic() - _catalog_loaded < config.OPEN_CATALOG_SECONDS:
        return _catalog
    async with _catalog_lock:
        if _catalog and time.monotonic() - _catalog_loaded < config.OPEN_CATALOG_SECONDS:
            return _catalog
        rows = await _read("MATCH (t:Text) RETURN t.slug AS slug, t.title AS title, t.genre AS genre, "
                           "t.author AS author, t.era AS era")
        _catalog = Catalog([TextInfo(r["slug"], r.get("title") or r["slug"], r.get("genre") or "",
                                     r.get("author") or "", r.get("era") or "") for r in rows if r.get("slug")])
        _catalog_loaded = time.monotonic()
        return _catalog


def set_catalog_for_tests(catalog: Catalog | None) -> None:
    global _catalog, _catalog_loaded
    _catalog, _catalog_loaded = catalog, time.monotonic() if catalog else 0.0
    _cache.clear()


def _su_passage(row: dict[str, Any], budget: list[int]) -> M.Passage:
    """Shape a search hit (a SemanticUnit row) into a Passage."""
    hebrew, cut_h = _clip(row.get("hebrew_text"), budget)
    english, cut_e = _clip(clean_english(row.get("english_text")), budget)
    sim = row.get("similarity")
    return M.Passage(
        reference=_reference(row) or row.get("text_slug") or "",
        id=row.get("first_anchor_id"),
        text_title=row.get("text_title"), author=row.get("text_author") or None,
        category=row.get("genre") or None, era=row.get("era") or None,
        hebrew=hebrew, english=english,
        translation_source=credit(row.get("en_source"), english),
        link=link_for(row.get("first_anchor_id")),
        relevance=round(sim, 3) if isinstance(sim, (int, float)) else None,
        truncated=cut_h or cut_e,
    )


def _tu_passage(row: dict[str, Any], catalog: Catalog, budget: list[int]) -> M.Passage:
    """Shape an exact TextUnit row into a Passage."""
    cid = row["canonical_id"]
    info = catalog.by_slug.get(row.get("text_slug") or cid.split("_", 1)[0])
    hebrew, cut_h = _clip(row.get("hebrew_text"), budget)
    english, cut_e = _clip(clean_english(row.get("english_text")), budget)
    return M.Passage(
        reference=label_for_id(cid, catalog), id=cid,
        text_title=info.title if info else None, author=(info.author or None) if info else None,
        category=info.genre if info else None, era=(info.era or None) if info else None,
        hebrew=hebrew, english=english, translation_source=credit(row.get("en_source"), english),
        link=link_for(cid), truncated=cut_h or cut_e,
    )


_TU_RETURN = ("tu.canonical_id AS canonical_id, tu.text_slug AS text_slug, tu.hebrew_text AS hebrew_text, "
              "tu.english_text AS english_text, tu.en_source AS en_source")


def _natural(cid: str) -> tuple[int, ...]:
    return tuple(int(n) for n in cid.split("_")[1:] if n.isdigit())


async def _units(ref: ParsedRef, cap: int = 60) -> list[dict[str, Any]]:
    """Fetch the TextUnits a parsed reference names, in reading order."""
    slug = ref.slug
    if ref.kind == "id":
        rows = await _read(f"MATCH (tu:TextUnit {{canonical_id: $id}}) RETURN {_TU_RETURN}", {"id": ref.canonical_id})
        if rows:
            return rows
        return await _prefix(slug, f"{ref.canonical_id}_", cap)
    if ref.kind == "comment":
        cid = f"{slug}_{ref.chapter}_{ref.verse}_{ref.comment}"
        return await _read(f"MATCH (tu:TextUnit {{canonical_id: $id}}) RETURN {_TU_RETURN}", {"id": cid})
    if ref.kind == "verse":
        cid = f"{slug}_{ref.chapter}_{ref.verse}"
        rows = await _read(f"MATCH (tu:TextUnit {{canonical_id: $id}}) RETURN {_TU_RETURN}", {"id": cid})
        return rows or await _prefix(slug, f"{cid}_", cap)   # a commentary holds several notes per verse
    if ref.kind == "range":
        ids = [f"{slug}_{ref.chapter}_{v}" for v in range(ref.verse, (ref.verse_end or ref.verse) + 1)]
        rows = await _read(f"MATCH (tu:TextUnit) WHERE tu.canonical_id IN $ids RETURN {_TU_RETURN}", {"ids": ids})
        return sorted(rows, key=lambda r: _natural(r["canonical_id"]))
    if ref.kind in ("chapter", "daf"):
        out: list[dict[str, Any]] = []
        for idx in range(ref.chapter, (ref.chapter_end or ref.chapter) + 1):
            out.extend(await _prefix(slug, f"{slug}_{idx}_", cap - len(out)))
            if len(out) >= cap:
                break
        return out
    return []


async def _prefix(slug: str | None, prefix: str, cap: int) -> list[dict[str, Any]]:
    if cap <= 0:
        return []
    rows = await _read(
        f"MATCH (tu:TextUnit) WHERE tu.canonical_id STARTS WITH $p AND tu.text_slug = $slug "
        f"RETURN {_TU_RETURN} LIMIT 400", {"p": prefix, "slug": slug})
    return sorted(rows, key=lambda r: _natural(r["canonical_id"]))[:cap]


def _ref_label(ref: ParsedRef, catalog: Catalog) -> str:
    info = catalog.by_slug.get(ref.slug or "")
    title = info.title if info else (ref.slug or ref.raw)
    if ref.kind == "id":
        return label_for_id(ref.canonical_id or "", catalog)
    if ref.kind == "daf":
        first = daf_label(ref.chapter or 1)
        if ref.chapter_end and ref.chapter_end != ref.chapter:
            return f"{title} {first}-{daf_label(ref.chapter_end)}"
        return f"{title} {first}"
    if ref.kind == "chapter":
        return f"{title} {ref.chapter}"
    if ref.kind == "range":
        return f"{title} {ref.chapter}:{ref.verse}-{ref.verse_end}"
    if ref.kind == "comment":
        return f"{title} {ref.chapter}:{ref.verse}:{ref.comment}"
    if ref.kind == "verse":
        return f"{title} {ref.chapter}:{ref.verse}"
    return title


def _not_found(ref: ParsedRef) -> tuple[str, list[str]]:
    if ref.suggestions:
        return (f"{ref.reason or 'That text is not in the library.'} Close matches: "
                f"{', '.join(ref.suggestions)}."), ref.suggestions
    return (ref.reason or f"Could not read '{ref.raw}' as a reference.") + \
        " Try a form such as 'Genesis 22:2', 'Berakhot 2a' or 'Pirkei Avot 1:14'.", []


async def _missing_hint(ref: ParsedRef, catalog: Catalog) -> str:
    """Explain an empty lookup with the real size of the text."""
    label = _ref_label(ref, catalog)
    info = catalog.by_slug.get(ref.slug or "")
    title = info.title if info else ref.slug
    rows = await _read("MATCH (tu:TextUnit {text_slug: $slug}) RETURN tu.canonical_id AS id LIMIT 60000", {"slug": ref.slug})
    chapters: dict[int, int] = {}
    for r in rows:
        nums = _natural(r["id"])
        if len(nums) >= 2:
            chapters[nums[0]] = max(chapters.get(nums[0], 0), nums[1])
    if not chapters:
        return f"No passage found for '{label}'. {title} has no text loaded yet."
    if catalog.is_daf_text(ref.slug or ""):
        return (f"No passage found for '{label}'. {title} runs from {daf_label(min(chapters))} "
                f"to {daf_label(max(chapters))}.")
    if ref.chapter and ref.chapter in chapters and ref.verse:
        return f"No passage found for '{label}'. {title} {ref.chapter} has {chapters[ref.chapter]} verses or sections."
    return f"No passage found for '{label}'. {title} has {max(chapters)} chapters."


# --- 1. search_passages ------------------------------------------------------------
# Search blends two lanes: meaning (vector) and exact words (full text). The two
# ranked lists are merged by reciprocal rank, with a small lift for primary
# sources so that the Talmud page itself outranks a late sermon that quotes it.
_SU_RETURN = _SU_FIELDS + ", head([(v:TextUnit)-[:IN_UNIT]->(su) | v.en_source]) AS en_source"
_TANAKH_SLUGS = frozenset(_TANAKH)


def primary_lift(slug: str) -> float:
    """A small lift for the sources everything else quotes. Decided by slug,
    because the genre label in the graph is wrong for a few texts."""
    if slug in _TANAKH_SLUGS:
        return 0.02
    if slug.startswith("bavli-") or (slug.startswith("mishnah-") and slug != "mishnah-berurah"):
        return 0.018
    if slug.endswith("-rabbah") or slug.startswith(("midrash-", "mishneh-torah-", "sifr", "mechilta", "pirkei-de")):
        return 0.01
    return 0.0


_STOP = frozenset(
    ["the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was", "were", "what", "does", "do", "did", "say", "says", "said", "about", "how", "why", "who", "whom", "which", "that", "this", "these", "those", "for", "with", "from", "on", "at", "by", "as", "it", "its", "be", "been", "being", "have", "has", "had", "not", "but", "can", "should", "would", "will", "there", "their", "they", "them", "his", "her", "him", "she", "he", "you", "your", "our", "we", "me", "my", "any", "some", "all", "more", "most", "than", "then", "when", "where", "judaism", "jewish", "jews", "jew", "torah", "sources", "source", "text", "texts", "passage", "passages", "tell", "give", "find", "show"])
EXCERPT_CHARS = 1500
_LUCENE_SPECIAL = re.compile(r'([+\-!(){}\[\]^"~*?:\\/]|&&|\|\|)')


def _terms(q: str) -> list[str]:
    words = re.findall(r"[a-z֐-׿][a-z֐-׿']+", q.lower())
    out: list[str] = []
    for w in words:
        if len(w) > 2 and w not in _STOP and w not in out:
            out.append(w)
    return out[:10]


def _stems(terms: list[str]) -> list[str]:
    """Crude stems for matching inside a passage: 'welcoming' and 'welcome' share 'welco'."""
    return [t[:5] if len(t) > 6 and t.isascii() else t for t in terms]


def merge_ranked(vector: list[dict[str, Any]], keyword: list[dict[str, Any]], phrase: list[dict[str, Any]],
                 n: int, per_text: int = 2) -> list[tuple[str, str]]:
    """Blend the three lanes into one ranked list of (kind, id), where kind is
    'su' for a passage unit and 'tu' for a single line found by its words.

    Meaning leads. A passage from the vector lane scores 1 to 2 by similarity,
    plus up to 0.3 when its words also match. A passage found by words alone
    scores under 1, so it fills gaps and does not displace meaning. A true
    quote (a line that carries the user's own words) scores above 2 and goes
    first. A primary source adds up to 0.5 in every lane."""
    score: dict[tuple[str, str], float] = {}
    slug_of: dict[tuple[str, str], str] = {}
    if vector:
        low = min(r["score"] for r in vector)
        span = (max(r["score"] for r in vector) - low) or 1.0
        for r in vector:
            key = ("su", r["su_id"])
            score[key] = 1.0 + (r["score"] - low) / span
            slug_of[key] = r.get("slug") or ""
    for rank, r in enumerate(keyword):
        key = ("su", r["su_id"])
        score[key] = score.get(key, 0.6) + 0.3 * (1 - rank / 20)
        slug_of[key] = r.get("slug") or ""
    for rank, r in enumerate(phrase):
        key = ("tu", r["id"])
        score[key] = (2.2 + 0.3 * r["cover"] if r["quote"] else 0.9) - 0.01 * rank
        slug_of[key] = r.get("slug") or ""
    for key in score:
        score[key] += 25 * primary_lift(slug_of[key])
    chosen: list[tuple[str, str]] = []
    used: dict[str, int] = {}
    for key in sorted(score, key=lambda k: -score[k]):
        slug = slug_of[key]
        if used.get(slug, 0) >= per_text:
            continue
        used[slug] = used.get(slug, 0) + 1
        chosen.append(key)
        if len(chosen) >= n + 3:        # a few spares, because duplicates are dropped later
            break
    return chosen


def best_window(units: list[dict[str, Any]], stems: list[str], max_chars: int = EXCERPT_CHARS) -> list[dict[str, Any]]:
    """Pick the lines of a long passage that carry the query's words."""
    units = [u for u in units if u.get("id") and (u.get("en") or u.get("he"))]
    if not units:
        return []

    def hits(u: dict[str, Any]) -> int:
        blob = f"{(u.get('en') or '').lower()} {u.get('he') or ''}"
        return sum(1 for s in stems if s in blob)

    scores = [hits(u) for u in units]
    best = max(range(len(units)), key=lambda i: (scores[i], -i))
    if scores[best] == 0:
        best = 0
    lo = hi = best
    size = len(units[best].get("en") or units[best].get("he") or "")
    while hi + 1 < len(units):
        nxt = len(units[hi + 1].get("en") or units[hi + 1].get("he") or "")
        if size + nxt > max_chars:
            break
        hi += 1
        size += nxt
    if lo > 0 and scores[lo - 1] > 0:
        prev = len(units[lo - 1].get("en") or units[lo - 1].get("he") or "")
        if size + prev <= max_chars * 1.3:
            lo -= 1
    return units[lo:hi + 1]


def _pretty_id(cid: str, catalog: Catalog) -> str:
    """Citation for ids whose middle parts are words: 'meor-einayim_vayera_10'."""
    parts = cid.split("_")
    info = catalog.by_slug.get(parts[0])
    title = info.title if info else parts[0]
    if all(p.isdigit() for p in parts[1:]):
        return label_for_id(cid, catalog)
    words = [re.sub(r"^\d+-", "", p).replace("-", " ").title() for p in parts[1:] if not p.isdigit()]
    nums = [p for p in parts[1:] if p.isdigit()]
    tail = f" {':'.join(nums)}" if nums else ""
    return f"{title}, {' '.join(words)}{tail}"


def _window_label(window: list[dict[str, Any]], catalog: Catalog) -> str:
    first, last = window[0]["id"], window[-1]["id"]
    label = _pretty_id(first, catalog)
    a, b = first.split("_"), last.split("_")
    plain = all(p.isdigit() for p in a[1:]) and all(p.isdigit() for p in b[1:])
    if plain and len(a) == 3 and len(b) == 3 and a[:2] == b[:2] and a[2] != b[2] and not catalog.is_daf_text(a[0]):
        label += f"-{b[2]}"
    return label


_NIKUD = re.compile(r"[\u0591-\u05c7]")


def phrase_query(q: str) -> tuple[str, str] | None:
    """Build a Lucene phrase query for quote-like input.
    Returns (index name, query) or None when the input is too short."""
    hebrew = bool(re.search(r"[\u05d0-\u05ea]", q))
    text = _NIKUD.sub("", q.lower())
    words = re.findall(r"[\u05d0-\u05ea]+" if hebrew else r"[a-z0-9]+", text)
    if len(words) < 2:
        return None
    index = "textunit_hebrew" if hebrew else "textunit_english"
    if len(words) < 5:
        return index, f'"{" ".join(words)}"~1'
    shingles = [f'"{" ".join(words[i:i + 5])}"~2' for i in range(min(len(words) - 4, 6))]
    whole = f'"{" ".join(words[:12])}"~4^2'
    return index, " OR ".join([whole, *shingles])


async def _lanes(q: str, slug: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Run the three lanes together. Returns (vector, keyword, phrase, vector_ok)."""
    terms = _terms(q)

    async def vector() -> list[dict[str, Any]] | None:
        try:
            vec = await embed_query(q)
        except ValueError:
            raise
        except Exception as e:  # noqa: BLE001 - the word lanes still answer
            log.warning("embedding failed, word search only: %s", str(e)[:200])
            return None
        if slug:
            return await _gated_vector("""
                MATCH (su:SemanticUnit {text_slug: $slug})
                WHERE su.embedding IS NOT NULL AND coalesce(su.first_anchor_id,'') <> ''
                WITH su, vector.similarity.cosine(su.embedding, $embedding) AS score
                WHERE score >= $floor
                RETURN su.su_id AS su_id, su.text_slug AS slug, score
                ORDER BY score DESC LIMIT 30""", vec, {"slug": slug, "floor": config.OPEN_MIN_SCORE})
        return await _gated_vector("""
            CALL db.index.vector.queryNodes('semantic_unit_embeddings', 40, $embedding)
            YIELD node AS su, score
            WHERE score >= $floor AND coalesce(su.first_anchor_id,'') <> ''
            RETURN su.su_id AS su_id, su.text_slug AS slug, score
            ORDER BY score DESC LIMIT 30""", vec, {"floor": config.OPEN_MIN_SCORE})

    async def keyword() -> list[dict[str, Any]]:
        if len(terms) < 2:
            return []
        lucene = " ".join(_LUCENE_SPECIAL.sub(r"\\\1", t) for t in terms)
        try:
            return await _read("""
                CALL db.index.fulltext.queryNodes('semantic_unit_text_fulltext', $q, {limit: $pool})
                YIELD node AS su, score
                WHERE coalesce(su.first_anchor_id,'') <> '' AND ($slug IS NULL OR su.text_slug = $slug)
                RETURN su.su_id AS su_id, su.text_slug AS slug, score
                ORDER BY score DESC LIMIT 20""", {"q": lucene, "slug": slug, "pool": 400 if slug else 25})
        except Busy:
            return []           # a bonus lane; the vector lane can answer alone

    async def phrase() -> list[dict[str, Any]]:
        built = phrase_query(q)
        if not built:
            return []
        index, lucene = built
        try:
            rows = await _read("""
                CALL db.index.fulltext.queryNodes($index, $q, {limit: $pool}) YIELD node AS tu, score
                WHERE ($slug IS NULL OR tu.text_slug = $slug)
                  AND (coalesce(tu.english_text, '') <> '' OR coalesce(tu.hebrew_text, '') <> '')
                RETURN tu.canonical_id AS id, tu.text_slug AS slug, score,
                       left(coalesce(tu.english_text, ''), 2400) AS en, left(coalesce(tu.hebrew_text, ''), 2400) AS he,
                       tu.en_source AS src
                ORDER BY score DESC LIMIT 30""", {"index": index, "q": lucene, "slug": slug, "pool": 300 if slug else 40})
        except Busy:
            return []
        # A hit is a quote only when it carries most of the user's words, content words included.
        # Stock phrases ("it is permitted to ...") must not outrank passages about the topic.
        hebrew = index == "textunit_hebrew"
        pattern = r"[\u05d0-\u05ea]+" if hebrew else r"[a-z0-9]+"
        asked = set(re.findall(pattern, _NIKUD.sub("", q.lower())))
        stems = _stems(terms)
        kept: list[dict[str, Any]] = []
        for r in rows:
            body = _NIKUD.sub("", r["he"]) if hebrew else r["en"].lower()
            cover = len(asked & set(re.findall(pattern, body))) / max(len(asked), 1)
            content = sum(1 for st in stems if st in body) / len(stems) if stems else 1.0
            r["cover"] = cover
            r["quote"] = len(asked) >= 5 and cover >= 0.75 and content >= 0.8
            if len(asked) >= 5 and not r["quote"]:
                continue
            kept.append(r)
        kept.sort(key=lambda r: -(r["score"] * (1 + 25 * primary_lift(r["slug"] or ""))))   # the source before its quoters
        return kept[:6]

    v, k, p = await asyncio.gather(vector(), keyword(), phrase())
    return (v or []), k, p, v is not None


async def search_passages(query: str, text: str | None = None, limit: int | None = None) -> M.SearchPassagesResult:
    q = (query or "").strip()[:QUERY_CHARS]
    if len(q) < 2:
        raise ValueError("Give a question or topic to search for, for example 'welcoming guests'.")
    n = _limit(limit, SEARCH_DEFAULT, SEARCH_MAX)
    catalog = await get_catalog()
    slug = title = None
    if text and text.strip():
        slug, suggestions = catalog.resolve_text(text)
        if not slug:
            return M.SearchPassagesResult(
                query=q, count=0, suggestions=suggestions,
                message=(f"No text named '{text}' is in the library."
                         + (f" Close matches: {', '.join(suggestions)}." if suggestions else "")
                         + " Search again without a text, or use list_texts to find the title."))
        title = catalog.by_slug[slug].title

    async def run() -> M.SearchPassagesResult:
        vector, keyword, phrase, vector_ok = await _lanes(q, slug)
        if vector_ok and not vector and not phrase:
            keyword = []        # nothing is close in meaning, so loose word matches would mislead
        chosen = merge_ranked(vector, keyword, phrase, n)
        note = None if vector_ok else "Meaning-based search was unavailable, so these are word matches."
        nothing = ("No passage matched closely enough. Try different words, a broader topic, "
                   "or search_concepts to find the idea first.")
        if not chosen:
            return M.SearchPassagesResult(query=q, text=title, count=0, message=nothing)
        su_ids = [i for kind, i in chosen if kind == "su"]
        rows = await _read("""
            MATCH (su:SemanticUnit) WHERE su.su_id IN $ids
            MATCH (su)-[:BELONGS_TO]->(t:Text)
            OPTIONAL MATCH (tu:TextUnit)-[:IN_UNIT]->(su)
            WITH su, t, tu ORDER BY tu.chapter_index, tu.position_in_chapter
            WITH su, t, collect({id: tu.canonical_id, en: left(coalesce(tu.english_text, ''), 2400),
                                 he: left(coalesce(tu.hebrew_text, ''), 2400), src: tu.en_source})[0..160] AS units
            RETURN su.su_id AS su_id, su.first_anchor_id AS first_anchor_id, su.daf_label AS daf_label,
                   su.canonical_ref AS canonical_ref, su.section_label AS section_label, su.text_slug AS text_slug,
                   su.era AS era, t.title AS text_title, t.author AS text_author,
                   left(coalesce(su.english_text, ''), 2400) AS english_text,
                   left(coalesce(su.hebrew_text, ''), 2400) AS hebrew_text, units
            """, {"ids": su_ids}) if su_ids else []
        by_su = {r["su_id"]: r for r in rows}
        by_tu = {r["id"]: r for r in phrase}
        sims = {r["su_id"]: r["score"] for r in vector}
        stems = _stems(_terms(q))
        budget = [RESPONSE_CHARS]
        passages: list[M.Passage] = []
        quoted: set[str] = set()
        prints: set[str] = set()
        for kind, ident in chosen:
            if len(passages) >= n:
                break
            sim = None
            if kind == "tu":
                r = by_tu[ident]
                if ident in quoted:
                    continue
                info = catalog.by_slug.get(r["slug"] or "")
                window = [r]
                title_, author, category, era = (info.title, info.author, info.genre, info.era) if info else (None,) * 4
                fallback = None
            else:
                r = by_su.get(ident)
                if not r:
                    continue
                for u in r["units"]:
                    u["en"] = clean_english(u.get("en")) or ""
                window = best_window(r["units"], stems)
                if any(u["id"] in quoted for u in window):
                    continue
                info = catalog.by_slug.get(r["text_slug"] or "")
                title_, author, era = r["text_title"], r["text_author"], r["era"]
                category = info.genre if info else None
                fallback, sim = r, sims.get(ident)
            if window:
                hebrew, cut_h = _clip(" ".join(u["he"] for u in window if u.get("he")), budget)
                english, cut_e = _clip(clean_english(" ".join(u["en"] for u in window if u.get("en"))), budget)
                anchor, reference, source = window[0]["id"], _window_label(window, catalog), window[0].get("src")
                quoted.update(u["id"] for u in window)
            else:
                hebrew, cut_h = _clip(fallback["hebrew_text"], budget)
                english, cut_e = _clip(clean_english(fallback["english_text"]), budget)
                anchor, reference, source = fallback["first_anchor_id"], _reference(fallback) or title_, None
            fingerprint = (english or hebrew or "")[:160]
            if not fingerprint or fingerprint in prints:      # the same words printed in two editions
                continue
            prints.add(fingerprint)
            passages.append(M.Passage(
                reference=reference, id=anchor, text_title=title_, author=author or None, category=category or None,
                era=era or None, hebrew=hebrew, english=english, translation_source=credit(source, english),
                link=link_for(anchor), relevance=round(sim, 3) if isinstance(sim, (int, float)) else None,
                truncated=cut_h or cut_e))
            if budget[0] <= 0:
                break
        passages.sort(key=lambda p: p.english is None)     # passages with an English translation first
        return M.SearchPassagesResult(query=q, text=title, count=len(passages), passages=passages,
                                      message=note if passages else nothing)

    return await _cached(f"search|{q}|{slug}|{n}", run)


async def _gated_vector(cypher: str, vec: list[float], params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        async with _db_gate:
            return await read_with_vector(cypher, vec, params)
    except TimeoutError as e:
        raise Busy("The library took too long to answer.") from e
    except Exception as e:
        log.warning("vector read failed: %s", str(e)[:300])
        raise Busy("The library is not reachable right now.") from e


# --- 2. get_passage ---------------------------------------------------------------
async def get_passage(reference: str) -> M.PassageResult:
    catalog = await get_catalog()
    ref = catalog.parse(reference)
    if not ref.ok:
        message, suggestions = _not_found(ref)
        return M.PassageResult(found=False, reference=reference, message=message, suggestions=suggestions)
    info = catalog.by_slug[ref.slug]  # type: ignore[index]
    label = _ref_label(ref, catalog)

    async def run() -> M.PassageResult:
        base = {"reference": label, "text_title": info.title, "author": info.author or None, "category": info.genre}
        if ref.kind == "text":
            example = "2a" if catalog.is_daf_text(info.slug) else "1:1"
            return M.PassageResult(
                found=False, **base, link=text_link(info.slug),
                message=(f"'{info.title}' is in the library. Add a place in the text to read it, "
                         f"for example '{info.title} {example}'."))
        rows = await _units(ref)
        if not rows:
            return M.PassageResult(found=False, **base, message=await _missing_hint(ref, catalog))
        budget = [RESPONSE_CHARS]
        segments: list[M.Passage] = []
        continue_from = None
        for row in rows:
            if budget[0] <= 0:
                continue_from = label_for_id(row["canonical_id"], catalog)
                if catalog.is_daf_text(info.slug):
                    continue_from = row["canonical_id"]
                break
            seg = _tu_passage(row, catalog, budget)
            if seg.hebrew or seg.english:
                segments.append(seg)
        if not segments:
            return M.PassageResult(found=False, **base, message=await _missing_hint(ref, catalog))
        cut = continue_from is not None or any(s.truncated for s in segments)
        link, source = segments[0].link, segments[0].translation_source
        for seg in segments:               # say the shared facts once, not on every verse
            seg.text_title = seg.author = seg.category = seg.era = seg.link = None
            if seg.translation_source == source:
                seg.translation_source = None
        return M.PassageResult(
            found=True, **base, translation_source=source, segments=segments, link=link, truncated=cut,
            continue_from=continue_from,
            message=("The passage is longer than one response allows. Ask for the reference in "
                     "'continue_from' to read on, or open the link.") if continue_from else None)

    return await _cached(f"passage|{label}|{ref.kind}", run)


async def _base_ids(reference: str, cap: int = 12) -> tuple[ParsedRef, Catalog, list[str]]:
    catalog = await get_catalog()
    ref = catalog.parse(reference)
    if not ref.ok or ref.kind == "text":
        return ref, catalog, []
    rows = await _units(ref, cap=cap)
    return ref, catalog, [r["canonical_id"] for r in rows]


def _unresolved(ref: ParsedRef, catalog: Catalog) -> tuple[str, list[str]]:
    if not ref.ok:
        return _not_found(ref)
    if ref.kind == "text":
        title = catalog.by_slug[ref.slug].title  # type: ignore[index]
        return f"Add a place in the text, for example '{title} 1:1' or a page such as '2a'.", []
    return f"No passage found for '{_ref_label(ref, catalog)}', so there is nothing to look up.", []


# --- 3. get_commentaries ----------------------------------------------------------
async def get_commentaries(reference: str, commentator: str | None = None, limit: int | None = None) -> M.CommentariesResult:
    n = _limit(limit, LIST_DEFAULT, LIST_MAX)
    ref, catalog, ids = await _base_ids(reference)
    if not ids:
        message, suggestions = _unresolved(ref, catalog)
        return M.CommentariesResult(found=False, reference=reference, message=message, suggestions=suggestions)
    label = _ref_label(ref, catalog)
    want = re.sub(r"[^a-z]+", "-", (commentator or "").lower()).strip("-")

    async def run() -> M.CommentariesResult:
        rows = await _read(f"""
            MATCH (b:TextUnit)-[r:CONNECTS_TO]-(tu:TextUnit)
            WHERE b.canonical_id IN $ids
              AND toLower(coalesce(r.kind, r.link_type, '')) IN ['comments_on', 'commentary']
            WITH DISTINCT tu
            MATCH (tu)-[:BELONGS_TO]->(t:Text) WHERE t.genre = 'commentary'
            RETURN {_TU_RETURN} LIMIT 400
            """, {"ids": ids})
        rows = [r for r in rows if r.get("hebrew_text") or r.get("english_text")]
        by_slug: dict[str, list[dict[str, Any]]] = {}
        for r in sorted(rows, key=lambda r: _natural(r["canonical_id"])):
            by_slug.setdefault(r["text_slug"], []).append(r)

        def rank(slug: str) -> tuple[int, str]:
            for i, name in enumerate(_COMMENTATOR_ORDER):
                if slug.startswith(name):
                    return i, slug
            return len(_COMMENTATOR_ORDER), slug

        ordered = sorted(by_slug, key=rank)
        names = [catalog.by_slug[s].title if s in catalog.by_slug else s for s in ordered]
        if want:
            ordered = [s for s in ordered if want in s or want in re.sub(r"[^a-z]+", "-", (catalog.by_slug[s].title if s in catalog.by_slug else s).lower())]
            if not ordered:
                return M.CommentariesResult(
                    found=False, reference=label, commentators=names,
                    message=(f"No commentary by '{commentator}' on {label} is in the library."
                             + (f" Available: {', '.join(names[:12])}." if names else "")))
        picked: list[dict[str, Any]] = []
        depth = 0
        while len(picked) < n and any(len(by_slug[s]) > depth for s in ordered):   # one note per commentator, then a second
            for s in ordered:
                if len(by_slug[s]) > depth and len(picked) < n:
                    picked.append(by_slug[s][depth])
            depth += 1
        budget = [RESPONSE_CHARS]
        out = [_tu_passage(r, catalog, budget) for r in picked]
        out = [p for p in out if p.hebrew or p.english]
        if not out:
            return M.CommentariesResult(found=False, reference=label, commentators=names,
                                        message=f"No commentary on {label} is in the library yet.")
        return M.CommentariesResult(found=True, reference=label, count=len(out), commentators=names, commentaries=out)

    return await _cached(f"comm|{label}|{want}|{n}", run)


# --- 4. get_cross_references ------------------------------------------------------
async def get_cross_references(reference: str, kinds: list[str] | None = None, limit: int | None = None) -> M.CrossReferencesResult:
    n = _limit(limit, LIST_DEFAULT, LIST_MAX)
    ref, catalog, ids = await _base_ids(reference)
    if not ids:
        message, suggestions = _unresolved(ref, catalog)
        return M.CrossReferencesResult(found=False, reference=reference, message=message, suggestions=suggestions)
    label = _ref_label(ref, catalog)
    wanted = sorted({k.strip().lower() for k in (kinds or []) if k and k.strip()})

    async def run() -> M.CrossReferencesResult:
        rows = await _read("""
            MATCH (b:TextUnit)-[r:CONNECTS_TO]-(tu:TextUnit)
            WHERE b.canonical_id IN $ids AND NOT tu.canonical_id IN $ids
              AND NOT toLower(coalesce(r.kind, r.link_type, '')) IN ['comments_on', 'commentary']
            WITH DISTINCT tu, coalesce(r.kind, r.link_type, 'related') AS kind
            RETURN kind, tu.canonical_id AS canonical_id, tu.text_slug AS text_slug,
                   left(coalesce(tu.english_text, ''), 320) AS english, left(coalesce(tu.hebrew_text, ''), 200) AS hebrew
            LIMIT 400
            """, {"ids": ids})
        counts: dict[str, int] = {}
        for r in rows:
            counts[r["kind"]] = counts.get(r["kind"], 0) + 1
        if wanted:
            rows = [r for r in rows if r["kind"].lower() in wanted]
        # spread the answer across kinds instead of returning 8 links of one kind
        by_kind: dict[str, list[dict[str, Any]]] = {}
        for r in sorted(rows, key=lambda r: (r["kind"], _natural(r["canonical_id"]))):
            by_kind.setdefault(r["kind"], []).append(r)
        picked: list[dict[str, Any]] = []
        depth = 0
        while len(picked) < n and any(len(v) > depth for v in by_kind.values()):
            for kind in sorted(by_kind):
                if len(by_kind[kind]) > depth and len(picked) < n:
                    picked.append(by_kind[kind][depth])
            depth += 1
        out = [M.CrossReference(
            kind=r["kind"], reference=label_for_id(r["canonical_id"], catalog), id=r["canonical_id"],
            text_title=catalog.by_slug[r["text_slug"]].title if r["text_slug"] in catalog.by_slug else None,
            excerpt=(clean_english(r["english"]) or r["hebrew"] or None), link=link_for(r["canonical_id"])) for r in picked]
        if not out:
            extra = f" Kinds available: {', '.join(sorted(counts))}." if counts else ""
            return M.CrossReferencesResult(found=False, reference=label, kinds_available=counts,
                                           message=f"No cross-references found for {label}.{extra}")
        return M.CrossReferencesResult(found=True, reference=label, count=len(out), kinds_available=counts,
                                       cross_references=out)

    return await _cached(f"xref|{label}|{','.join(wanted)}|{n}", run)


# --- 5. get_talmud_discussion -------------------------------------------------------
async def get_talmud_discussion(reference: str) -> M.TalmudDiscussionResult:
    ref, catalog, ids = await _base_ids(reference, cap=60)
    raw = (reference or "").strip()
    if not ids and not raw.lower().startswith("sugya_"):
        message, suggestions = _unresolved(ref, catalog)
        return M.TalmudDiscussionResult(found=False, reference=reference, message=message, suggestions=suggestions)
    label = _ref_label(ref, catalog) if ids else raw

    async def run() -> M.TalmudDiscussionResult:
        if ids:
            sugyot = await _read("""
                MATCH (s:Sugya)-[:LOCATED_IN]->(tu:TextUnit) WHERE tu.canonical_id IN $ids
                WITH s, min(tu.canonical_id) AS at
                RETURN s.sugya_id AS id, s.canonical_reference AS reference, s.sugya_type AS kind,
                       s.driving_question AS driving_question, s.maskana AS conclusion,
                       s.conclusion_status AS conclusion_status, at LIMIT 12
                """, {"ids": ids})
            sugyot = sorted(sugyot, key=lambda s: _natural(s["at"]))[:3]
        else:
            sugyot = await _read("""
                MATCH (s:Sugya {sugya_id: $id}) OPTIONAL MATCH (s)-[:LOCATED_IN]->(tu:TextUnit)
                RETURN s.sugya_id AS id, s.canonical_reference AS reference, s.sugya_type AS kind,
                       s.driving_question AS driving_question, s.maskana AS conclusion,
                       s.conclusion_status AS conclusion_status, min(tu.canonical_id) AS at LIMIT 1
                """, {"id": raw})
        if not sugyot:
            talmud = bool(ref.slug) and catalog.is_daf_text(ref.slug or "")
            return M.TalmudDiscussionResult(
                found=False, reference=label,
                message=(f"No mapped discussion starts on {label}. Try the page before it, or read the page with get_passage."
                         if talmud else f"{label} is not a Babylonian Talmud passage. This tool maps Talmud discussions only."))
        moves = await _read("""
            MATCH (m:Move)-[:PART_OF]->(s:Sugya) WHERE s.sugya_id IN $ids
            RETURN s.sugya_id AS sid, m.sequence AS step, m.move_type AS move, m.speaker AS speaker,
                   m.stratum AS layer, m.marker AS marker, m.marker_translation AS marker_translation,
                   m.content_summary AS summary ORDER BY m.sequence LIMIT 120
            """, {"ids": [s["id"] for s in sugyot]})
        out = []
        for s in sugyot:
            steps = [M.TalmudMove(
                step=m["step"], move=m["move"], speaker=m["speaker"] or None, layer=m["layer"] or None,
                marker=" = ".join(x for x in (m["marker"], m["marker_translation"]) if x) or None,
                summary=m["summary"]) for m in moves if m["sid"] == s["id"]][:30]
            out.append(M.TalmudDiscussion(
                id=s["id"], reference=s["reference"], kind=s["kind"], driving_question=s["driving_question"],
                conclusion=s["conclusion"], conclusion_status=s["conclusion_status"], moves=steps,
                link=link_for(s.get("at"))))
        return M.TalmudDiscussionResult(found=True, reference=label, count=len(out), discussions=out)

    return await _cached(f"sugya|{label}", run)


# --- 6 to 10. concepts ------------------------------------------------------------
def _concept(row: dict[str, Any], relation: str | None = None) -> M.ConceptSummary:
    sim = row.get("similarity")
    return M.ConceptSummary(
        concept_id=row["canonical_id"], name=row.get("name"), hebrew_name=row.get("name_hebrew") or None,
        definition=row.get("one_line_definition") or None, difficulty=row.get("difficulty") or None,
        keystone=row.get("is_keystone"), relation=relation or row.get("rel_type"),
        relevance=round(sim, 3) if isinstance(sim, (int, float)) else None)


_C_SHORT = ("c.canonical_id AS canonical_id, c.name AS name, c.name_hebrew AS name_hebrew, "
            "c.one_line_definition AS one_line_definition, c.difficulty AS difficulty, c.is_keystone AS is_keystone")


async def search_concepts(query: str, limit: int | None = None) -> M.SearchConceptsResult:
    q = (query or "").strip()[:QUERY_CHARS]
    if len(q) < 2:
        raise ValueError("Give an idea to search for, for example 'repentance' or 'free will'.")
    n = _limit(limit, LIST_DEFAULT, LIST_MAX)

    async def run() -> M.SearchConceptsResult:
        try:
            vec = await embed_query(q)
            rows = await _gated_vector(f"""
                CALL db.index.vector.queryNodes('canonical_concept_embeddings', $n, $embedding)
                YIELD node AS c, score AS similarity
                RETURN {_C_SHORT}, similarity ORDER BY similarity DESC LIMIT $n
                """, vec, {"n": n})
        except Busy:
            raise
        except ValueError:
            raise
        except Exception as e:  # noqa: BLE001 - keyword fallback
            log.warning("embedding failed, using keyword search: %s", str(e)[:200])
            words = " ".join(re.findall(r"[\w֐-׿]+", q)[:8])
            rows = await _read(f"""
                CALL db.index.fulltext.queryNodes('canonical_fulltext', $q) YIELD node AS c, score
                RETURN {_C_SHORT}, null AS similarity ORDER BY score DESC LIMIT $n
                """, {"q": words, "n": n})
        out = [_concept(r) for r in rows]
        return M.SearchConceptsResult(query=q, count=len(out), concepts=out,
                                      message=None if out else "No concept matched. Try a broader word.")

    return await _cached(f"csearch|{q}|{n}", run)


def _no_concept(concept_id: str) -> str:
    return (f"No concept has the id '{concept_id}'. Concept ids look like 'cluster_123'. "
            "Use search_concepts to find the id from a name or a topic.")


async def get_concept(concept_id: str) -> M.ConceptResult:
    cid = (concept_id or "").strip()

    async def run() -> M.ConceptResult:
        rows = await _read(f"""
            MATCH (c:CanonicalConcept {{canonical_id: $id}})
            RETURN {_C_SHORT}, c.description AS description, c.question AS question,
                   c.gateway_insight AS gateway_insight, c.era_span AS era_span, c.traditions AS traditions,
                   c.also_known_as AS also_known_as LIMIT 1
            """, {"id": cid})
        if not rows:
            return M.ConceptResult(found=False, concept_id=cid, message=_no_concept(cid))
        r = rows[0]
        related = await _related_rows(cid, None, 8, skip_commentary=True)
        return M.ConceptResult(
            found=True, concept_id=cid, name=r.get("name"), hebrew_name=r.get("name_hebrew") or None,
            also_known_as=list(r.get("also_known_as") or [])[:6], definition=r.get("one_line_definition") or None,
            description=r.get("description") or None, guiding_question=r.get("question") or None,
            key_insight=r.get("gateway_insight") or None, difficulty=r.get("difficulty") or None,
            keystone=r.get("is_keystone"), eras=list(r.get("era_span") or []), traditions=list(r.get("traditions") or []),
            related=[_concept(x) for x in related])

    return await _cached(f"concept|{cid}", run)


async def _related_rows(cid: str, relation: str | None, n: int, *, skip_commentary: bool = False) -> list[dict[str, Any]]:
    return await _read("""
        MATCH (c0:CanonicalConcept {canonical_id: $id})-[r:CANONICAL_REL]-(c:CanonicalConcept)
        WITH c, r, coalesce(r.relationship_type, r.type) AS rel_type
        WHERE ($rel IS NULL OR rel_type = $rel) AND (NOT $skip OR rel_type <> 'COMMENTARY')
        WITH c, rel_type, max(coalesce(r.confidence, 0.0)) AS confidence
        RETURN c.canonical_id AS canonical_id, c.name AS name, c.name_hebrew AS name_hebrew,
               c.one_line_definition AS one_line_definition, c.difficulty AS difficulty,
               c.is_keystone AS is_keystone, rel_type
        ORDER BY confidence DESC LIMIT $n
        """, {"id": cid, "rel": relation, "n": n, "skip": skip_commentary})


async def _concept_exists(cid: str) -> str | None:
    rows = await _read("MATCH (c:CanonicalConcept {canonical_id: $id}) RETURN c.name AS name LIMIT 1", {"id": cid})
    return rows[0]["name"] if rows else None


async def get_related_concepts(concept_id: str, relation: str | None = None, limit: int | None = None) -> M.RelatedConceptsResult:
    cid = (concept_id or "").strip()
    n = _limit(limit, LIST_DEFAULT, LIST_MAX)
    rel = (relation or "").strip().upper().replace(" ", "_") or None
    if rel and rel not in RELATIONS:
        raise ValueError(f"'{relation}' is not a relation. Use one of: {', '.join(RELATIONS)}.")

    async def run() -> M.RelatedConceptsResult:
        if await _concept_exists(cid) is None:
            return M.RelatedConceptsResult(found=False, concept_id=cid, relation=rel, message=_no_concept(cid))
        rows = await _related_rows(cid, rel, n, skip_commentary=rel is None)
        out = [_concept(r) for r in rows]
        msg = None
        if not out:
            msg = (f"No concept is linked to this one by {rel}." if rel else "No related concepts are recorded.")
        return M.RelatedConceptsResult(found=True, concept_id=cid, relation=rel, count=len(out), related=out, message=msg)

    return await _cached(f"related|{cid}|{rel}|{n}", run)


async def get_learning_path(concept_id: str) -> M.LearningPathResult:
    cid = (concept_id or "").strip()

    async def run() -> M.LearningPathResult:
        name = await _concept_exists(cid)
        if name is None:
            return M.LearningPathResult(found=False, concept_id=cid, message=_no_concept(cid))
        before = await _read(f"""
            MATCH (c:CanonicalConcept)-[r:PREREQUISITE]->(:CanonicalConcept {{canonical_id: $id}})
            RETURN {_C_SHORT} ORDER BY r.confidence DESC LIMIT 8""", {"id": cid})
        after = await _read(f"""
            MATCH (:CanonicalConcept {{canonical_id: $id}})-[r:PREREQUISITE]->(c:CanonicalConcept)
            RETURN {_C_SHORT} ORDER BY r.confidence DESC LIMIT 8""", {"id": cid})
        msg = None
        if not before and not after:
            msg = "No learning order is recorded for this concept. It can be studied on its own."
        elif not before:
            msg = "Nothing needs to come first. This concept is a starting point."
        return M.LearningPathResult(found=True, concept_id=cid, name=name, learn_first=[_concept(r) for r in before],
                                    leads_to=[_concept(r) for r in after], message=msg)

    return await _cached(f"path|{cid}", run)


async def get_concept_sources(concept_id: str, limit: int | None = None) -> M.ConceptSourcesResult:
    cid = (concept_id or "").strip()
    n = _limit(limit, 5, 10)

    async def run() -> M.ConceptSourcesResult:
        if await _concept_exists(cid) is None:
            return M.ConceptSourcesResult(found=False, concept_id=cid, message=_no_concept(cid))
        rows = await _read(f"""
            MATCH (c:CanonicalConcept {{canonical_id: $id}})<-[:INSTANCE_OF]-(m:CorridorModule)-[:COVERS]->(su:SemanticUnit)
            WHERE coalesce(su.first_anchor_id,'') <> ''
            MATCH (su)-[:BELONGS_TO]->(t:Text)
            WITH DISTINCT su, t LIMIT $pool
            RETURN {_SU_RETURN}, null AS similarity
            """, {"id": cid, "pool": n * 3})
        seen: set[str] = set()
        spread: list[dict[str, Any]] = []
        for r in rows:                      # prefer one passage per text before a second from the same text
            if r.get("text_slug") not in seen:
                seen.add(r.get("text_slug"))
                spread.append(r)
        spread += [r for r in rows if r not in spread]
        budget = [RESPONSE_CHARS]
        out = [p for p in (_su_passage(r, budget) for r in spread[:n]) if p.hebrew or p.english]
        catalog = await get_catalog()
        for p in out:
            if p.id:
                p.reference = _pretty_id(p.id, catalog)
        return M.ConceptSourcesResult(found=True, concept_id=cid, count=len(out), passages=out,
                                      message=None if out else "No source passages are linked to this concept yet.")

    return await _cached(f"csrc|{cid}|{n}", run)


# --- 11. browse_themes ------------------------------------------------------------
async def browse_themes(theme_id: str | None = None) -> M.BrowseThemesResult:
    tid = (theme_id or "").strip().lower()

    async def run() -> M.BrowseThemesResult:
        if not tid:
            rows = await _read("MATCH (g:Galaxy) RETURN g.galaxy_id AS id, g.name AS name, g.name_hebrew AS he, "
                               "g.great_question AS q, g.description AS d, g.constellation_count AS size ORDER BY g.galaxy_id")
            return M.BrowseThemesResult(level="top", themes=[
                M.Theme(theme_id=r["id"], name=r["name"], hebrew_name=r["he"] or None, question=r["q"],
                        description=(r["d"] or "")[:220] or None, size=r["size"]) for r in rows])
        if tid.startswith("galaxy_"):
            head = await _read("MATCH (g:Galaxy {galaxy_id: $id}) RETURN g.galaxy_id AS id, g.name AS name, "
                               "g.name_hebrew AS he, g.great_question AS q, g.description AS d, "
                               "g.constellation_count AS size", {"id": tid})
            if not head:
                return M.BrowseThemesResult(found=False, level="theme", message=_no_theme(tid))
            rows = await _read("MATCH (c:Constellation {galaxy_id: $id}) RETURN c.constellation_id AS id, c.name AS name, "
                               "c.name_hebrew AS he, left(c.fundamental_question, 200) AS q, c.size AS size "
                               "ORDER BY c.size DESC LIMIT 30", {"id": tid})
            h = head[0]
            return M.BrowseThemesResult(
                level="theme",
                theme=M.Theme(theme_id=h["id"], name=h["name"], hebrew_name=h["he"] or None, question=h["q"],
                              description=h["d"] or None, size=h["size"]),
                themes=[M.Theme(theme_id=r["id"], name=r["name"], hebrew_name=r["he"] or None, question=r["q"],
                                size=r["size"]) for r in rows])
        if tid.startswith("constellation_"):
            head = await _read("MATCH (c:Constellation {constellation_id: $id}) RETURN c.constellation_id AS id, "
                               "c.name AS name, c.name_hebrew AS he, c.fundamental_question AS q, "
                               "c.description AS d, c.size AS size", {"id": tid})
            if not head:
                return M.BrowseThemesResult(found=False, level="group", message=_no_theme(tid))
            members = await _read(f"MATCH (c:CanonicalConcept)-[:IN_CONSTELLATION]->(:Constellation {{constellation_id: $id}}) "
                                  f"RETURN {_C_SHORT} ORDER BY c.is_keystone DESC, c.name LIMIT 30", {"id": tid})
            entry = await _read(f"MATCH (:Constellation {{constellation_id: $id}})-[:ENTRY_POINT]->(c:CanonicalConcept) "
                                f"RETURN {_C_SHORT} LIMIT 6", {"id": tid})
            h = head[0]
            return M.BrowseThemesResult(
                level="group",
                theme=M.Theme(theme_id=h["id"], name=h["name"], hebrew_name=h["he"] or None, question=h["q"],
                              description=h["d"] or None, size=h["size"]),
                concepts=[_concept(r) for r in members], start_here=[_concept(r) for r in entry])
        return M.BrowseThemesResult(found=False, level="top", message=_no_theme(tid))

    return await _cached(f"themes|{tid}", run)


def _no_theme(tid: str) -> str:
    return (f"No theme has the id '{tid}'. Call browse_themes with no id to see the 11 great themes "
            "(ids like 'galaxy_03'), then pass one of those ids, then a group id like 'constellation_0042'.")


# --- 12. list_texts ---------------------------------------------------------------
async def list_texts(category: str | None = None, search: str | None = None, limit: int | None = None) -> M.ListTextsResult:
    catalog = await get_catalog()
    n = _limit(limit, 40, 80)
    texts = sorted(catalog.by_slug.values(), key=lambda t: t.title.lower())
    categories: dict[str, int] = {}
    for t in texts:
        categories[t.genre or "other"] = categories.get(t.genre or "other", 0) + 1
    cat = re.sub(r"[^a-z]+", "_", (category or "").strip().lower()).strip("_")
    aliases = {"talmud": "talmud_bavli", "bavli": "talmud_bavli", "yerushalmi": "talmud_yerushalmi",
               "halakhah": "halakhic_code", "halakha": "halakhic_code", "law": "halakhic_code",
               "midrash": "midrash_aggadah", "chassidut": "hasidut", "chasidut": "hasidut", "bible": "tanakh",
               "musar": "mussar", "prayer": "liturgy", "targum": "targumim", "commentaries": "commentary"}
    cat = aliases.get(cat, cat)
    message = None
    if cat:
        if cat not in categories:
            message = f"'{category}' is not a category. Categories: {', '.join(sorted(categories))}."
            texts = []
        else:
            texts = [t for t in texts if (t.genre or "other") == cat]
    if search and search.strip():
        words = [w for w in re.split(r"[^a-z0-9֐-׿]+", search.lower()) if w]
        texts = [t for t in texts if all(w in f"{t.title} {t.slug} {t.author}".lower() for w in words)]
        if not texts and message is None:
            slug, suggestions = catalog.resolve_text(search)
            if slug:
                texts = [catalog.by_slug[slug]]
            else:
                message = (f"No text matches '{search}'."
                           + (f" Close matches: {', '.join(suggestions)}." if suggestions else ""))
    total = len(texts)
    shown = texts[:n]
    if total > n and message is None:
        message = f"Showing {n} of {total}. Narrow the list with 'search' or 'category'."
    return M.ListTextsResult(
        count=len(shown), total_in_library=len(catalog.by_slug), categories=dict(sorted(categories.items())),
        texts=[M.TextEntry(title=t.title, slug=t.slug, category=t.genre or None, author=t.author or None,
                           era=t.era or None) for t in shown], message=message)


# --- 13. get_study_path -----------------------------------------------------------
async def get_study_path(text: str, start: int | None = None, limit: int | None = None) -> M.StudyPathResult:
    catalog = await get_catalog()
    slug, suggestions = catalog.resolve_text(text or "")
    if not slug:
        return M.StudyPathResult(found=False, text=text or "", suggestions=suggestions,
                                 message=f"No text named '{text}' is in the library."
                                 + (f" Close matches: {', '.join(suggestions)}." if suggestions else ""))
    info = catalog.by_slug[slug]
    first = max(int(start or 1), 1)
    n = _limit(limit, 12, 25)

    async def run() -> M.StudyPathResult:
        head = await _read("MATCH (c:Corridor {text_slug: $slug}) RETURN c.corridor_id AS id, c.total_modules AS total LIMIT 1",
                           {"slug": slug})
        if not head:
            return M.StudyPathResult(found=False, text=slug, text_title=info.title, link=text_link(slug),
                                     message=f"No study path has been built for {info.title} yet.")
        rows = await _read("""
            MATCH (m:CorridorModule {text_slug: $slug}) WHERE m.module_number >= $first
            RETURN m.module_number AS step, m.concept_name AS idea, m.description AS summary, m.type AS kind,
                   m.anchor_quote AS quote, m.anchor_quote_hebrew AS quote_hebrew, m.key_entities AS figures
            ORDER BY m.module_number LIMIT $n
            """, {"slug": slug, "first": first, "n": n})
        steps = [M.StudyStep(step=r["step"], idea=r["idea"], summary=r["summary"], kind=r["kind"],
                             quote=(r["quote"] or "")[:400] or None, quote_hebrew=(r["quote_hebrew"] or "")[:300] or None,
                             key_figures=list(r["figures"] or [])[:6]) for r in rows]
        total = head[0]["total"] or 0
        msg = None
        if steps and steps[-1].step < total:
            msg = f"Steps {steps[0].step} to {steps[-1].step} of {total}. Pass start={steps[-1].step + 1} for the next steps."
        elif not steps:
            msg = f"{info.title} has {total} steps. Pass a start between 1 and {total}."
        return M.StudyPathResult(found=bool(steps), text=slug, text_title=info.title, total_steps=total, start=first,
                                 steps=steps, link=text_link(slug), message=msg)

    return await _cached(f"study|{slug}|{first}|{n}", run)


# --- 14. get_jewish_calendar ------------------------------------------------------
async def get_jewish_calendar(date: str | None = None, israel: bool | None = None) -> M.CalendarResult:
    day = jcalendar.parse_date(date)
    data = jcalendar.calendar_for(day, israel=bool(israel))
    return M.CalendarResult.model_validate(data)


# --- 15 and 16. the skill shelf ---------------------------------------------------
def _shelf() -> dict[str, shelf.Skill]:
    global _skills
    if _skills is None:
        _skills = shelf.load_all()
    return _skills


def reload_shelf(sources=None) -> int:
    global _skills
    _skills = shelf.load_all(sources) if sources else shelf.load_all()
    return len(_skills)


async def list_skills() -> M.ListSkillsResult:
    skills = _shelf()
    entries = [M.SkillEntry(name=s.name, kind=s.kind, description=s.description[:400], author=s.author or None)
               for s in sorted(skills.values(), key=lambda s: (s.kind != "core", s.name))]
    return M.ListSkillsResult(count=len(entries), skills=entries,
                              message=None if entries else "The skill shelf is empty right now.")


async def load_skill(name: str) -> M.LoadSkillResult:
    skills = _shelf()
    skill, suggestions = shelf.find(skills, name)
    if skill is None:
        return M.LoadSkillResult(
            found=False, name=name or "", suggestions=suggestions,
            message=(f"No skill named '{name}' is on the shelf."
                     + (f" Close matches: {', '.join(suggestions)}." if suggestions else " Call list_skills to see them all.")))
    return M.LoadSkillResult(found=True, name=skill.name, kind=skill.kind, author=skill.author or None,
                             licence=skill.licence or None, instructions=skill.body)


def today_utc() -> dt.date:
    return dt.datetime.now(dt.UTC).date()
