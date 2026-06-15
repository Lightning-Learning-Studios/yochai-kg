"""Read-only query functions over the Yochai knowledge graph.

Each function returns plain JSON-serializable data. All Cypher here is read-only
and parameterized; result counts are clamped by config.clamp_limit. The graph
schema (node labels, edge types, properties) is documented in docs/schema.md.
"""
from __future__ import annotations

import re
from typing import Any

from . import config
from .embeddings import embed_query
from .neo4j_client import read, read_with_vector

# run_cypher only permits these read procedures (the vector/fulltext indexes).
_ALLOWED_CALL_PROCS = {"db.index.vector.querynodes", "db.index.fulltext.querynodes"}
_CALL_PROC_RE = re.compile(r"\bcall\s+([a-z0-9_.]+)", re.IGNORECASE)


def _deep_link(anchor: str | None) -> str | None:
    if not anchor:
        return None
    return f"{config.APP_URL}/p/{anchor}"


def _reference(row: dict[str, Any]) -> str | None:
    """Build a human citation. SemanticUnits have empty canonical_ref/section_label
    across the corpus, so derive one: Talmud → 'Berakhot, Daf 2a'; verse-structured
    texts → 'Bereishit 1:1' (from a clean <slug>_<ch>_<v> anchor); else the title.
    The anchor/deep_link always carries the precise, authoritative location."""
    title = row.get("text_title") or row.get("text_slug")
    if row.get("daf_label"):
        return f"{title}, {row['daf_label']}"
    if row.get("canonical_ref"):
        return row["canonical_ref"]
    if row.get("section_label"):
        return row["section_label"]
    slug = row.get("text_slug") or ""
    anchor = row.get("first_anchor_id") or ""
    m = re.match(rf"^{re.escape(slug)}_(\d+)_(\d+)$", anchor)
    if m:
        return f"{title} {m.group(1)}:{m.group(2)}"
    return title


def _passage(row: dict[str, Any]) -> dict[str, Any]:
    """Shape a SemanticUnit row into a public passage object."""
    return {
        "su_id": row.get("su_id"),
        "reference": _reference(row),
        "text_slug": row.get("text_slug"),
        "text_title": row.get("text_title"),
        "author": row.get("text_author"),
        "genre": row.get("genre"),
        "era": row.get("era"),
        "hebrew": row.get("hebrew_text"),
        "english": row.get("english_text"),
        "anchor": row.get("first_anchor_id"),
        "deep_link": _deep_link(row.get("first_anchor_id")),
        "similarity": round(row["similarity"], 4) if row.get("similarity") is not None else None,
    }


_SU_FIELDS = """
       su.su_id AS su_id, su.english_text AS english_text, su.hebrew_text AS hebrew_text,
       su.canonical_ref AS canonical_ref, su.section_label AS section_label,
       su.daf_label AS daf_label,
       su.first_anchor_id AS first_anchor_id, su.last_anchor_id AS last_anchor_id,
       su.text_slug AS text_slug, su.genre AS genre, su.era AS era,
       t.title AS text_title, t.author AS text_author
"""


async def search_corpus(query: str, text_filter: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """Semantic search over the corpus' semantic units (vector ANN, BGE-M3)."""
    n = config.clamp_limit(limit)
    vec = await embed_query(query)

    if text_filter:
        # Exact cosine scan scoped to one text — avoids cross-text leakage.
        cypher = f"""
        MATCH (su:SemanticUnit)-[:BELONGS_TO]->(t:Text)
        WHERE toLower(su.text_slug) = toLower($slug) AND su.embedding IS NOT NULL
        WITH su, t, vector.similarity.cosine(su.embedding, $embedding) AS similarity
        WHERE similarity > $threshold
        RETURN {_SU_FIELDS}, similarity
        ORDER BY similarity DESC LIMIT $n
        """
        rows = await read_with_vector(cypher, vec, {"slug": text_filter, "threshold": config.SIMILARITY_THRESHOLD, "n": n})
    else:
        cypher = f"""
        CALL db.index.vector.queryNodes('semantic_unit_embeddings', $pool, $embedding)
        YIELD node AS su, score AS similarity
        WHERE similarity > $threshold
        MATCH (su)-[:BELONGS_TO]->(t:Text)
        RETURN {_SU_FIELDS}, similarity
        ORDER BY similarity DESC LIMIT $n
        """
        rows = await read_with_vector(cypher, vec, {"pool": n, "threshold": config.SIMILARITY_THRESHOLD, "n": n})

    return {"query": query, "text_filter": text_filter, "count": len(rows), "passages": [_passage(r) for r in rows]}


async def lookup_passage(reference: str) -> dict[str, Any]:
    """Resolve an exact passage by slug-style reference (e.g. 'bereishit 1:1',
    'bavli-berakhot_5_1'). English book-name resolution (e.g. 'Genesis 1:1') is a
    planned enhancement; for now pass the slug or canonical id."""
    ref = reference.strip()
    canonical_id = ref.replace(" ", "_").replace(":", "_").lower()
    cypher = """
    MATCH (tu:TextUnit)
    WHERE toLower(tu.canonical_id) = $cid
    OPTIONAL MATCH (tu)-[:IN_UNIT]->(su:SemanticUnit)
    MATCH (tu)-[:BELONGS_TO]->(t:Text)
    RETURN tu.canonical_id AS canonical_id, tu.english_text AS english_text,
           tu.hebrew_text AS hebrew_text, tu.text_slug AS text_slug,
           t.title AS text_title, t.author AS text_author,
           su.su_id AS su_id, su.canonical_ref AS canonical_ref
    LIMIT 1
    """
    rows = await read(cypher, {"cid": canonical_id})
    if not rows:
        return {"reference": reference, "found": False, "hint": "Pass a slug-style ref like 'bereishit_1_1' or 'bavli-berakhot_5_1'."}
    r = rows[0]
    return {
        "reference": reference, "found": True,
        "canonical_id": r["canonical_id"], "text_slug": r["text_slug"],
        "text_title": r["text_title"], "author": r["text_author"],
        "reference_label": r.get("canonical_ref"),
        "hebrew": r["hebrew_text"], "english": r["english_text"],
        "deep_link": _deep_link(r["canonical_id"]),
    }


_CONCEPT_FIELDS = """
       c.canonical_id AS canonical_id, c.name AS name, c.name_hebrew AS name_hebrew,
       c.one_line_definition AS one_line_definition, c.description AS description,
       c.question AS question, c.gateway_insight AS gateway_insight,
       c.difficulty AS difficulty, c.domain AS domain, c.is_keystone AS is_keystone
"""


async def search_concepts(query: str, limit: int | None = None) -> dict[str, Any]:
    """Find canonical concepts by semantic similarity (vector) over ~17.6k concepts."""
    n = config.clamp_limit(limit)
    vec = await embed_query(query)
    cypher = f"""
    CALL db.index.vector.queryNodes('canonical_concept_embeddings', $n, $embedding)
    YIELD node AS c, score AS similarity
    RETURN {_CONCEPT_FIELDS}, similarity
    ORDER BY similarity DESC LIMIT $n
    """
    rows = await read_with_vector(cypher, vec, {"n": n})
    for r in rows:
        r["similarity"] = round(r["similarity"], 4)
    return {"query": query, "count": len(rows), "concepts": rows}


async def get_concept(canonical_id: str) -> dict[str, Any]:
    cypher = f"MATCH (c:CanonicalConcept {{canonical_id: $id}}) RETURN {_CONCEPT_FIELDS}, c.era_span AS era_span, c.traditions AS traditions, c.module_count AS module_count, c.book_count AS book_count LIMIT 1"
    rows = await read(cypher, {"id": canonical_id})
    return rows[0] if rows else {"canonical_id": canonical_id, "found": False}


async def get_concept_neighborhood(canonical_id: str, rel_types: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
    """Typed concept-to-concept neighbors via CANONICAL_REL.
    rel_types filters on: DEVELOPS, CONTRADICTS, RESONATES, EXEMPLIFIES,
    APPLIES_TO, ADDRESSES, SHARES_METHOD, CONTEXTUALIZES, COMMENTARY."""
    n = config.clamp_limit(limit)
    cypher = """
    MATCH (c:CanonicalConcept {canonical_id: $id})-[r:CANONICAL_REL]-(nbr:CanonicalConcept)
    WITH nbr, r, coalesce(r.relationship_type, r.type) AS rel_type
    WHERE $rel_types IS NULL OR rel_type IN $rel_types
    RETURN nbr.canonical_id AS canonical_id, nbr.name AS name,
           nbr.one_line_definition AS one_line_definition, nbr.difficulty AS difficulty,
           rel_type, r.confidence AS confidence, r.direction AS direction
    ORDER BY r.confidence DESC LIMIT $n
    """
    rows = await read(cypher, {"id": canonical_id, "rel_types": rel_types, "n": n})
    return {"canonical_id": canonical_id, "rel_types": rel_types, "count": len(rows), "neighbors": rows}


async def get_prerequisites(canonical_id: str, limit: int | None = None) -> dict[str, Any]:
    """Walk the prerequisite DAG. Returns concepts you should learn BEFORE this
    one (prerequisites) and concepts this one unlocks (next steps)."""
    n = config.clamp_limit(limit)
    prereqs = await read(
        "MATCH (p:CanonicalConcept)-[r:PREREQUISITE]->(c:CanonicalConcept {canonical_id:$id}) "
        "RETURN p.canonical_id AS canonical_id, p.name AS name, p.difficulty AS difficulty, r.confidence AS confidence "
        "ORDER BY r.confidence DESC LIMIT $n", {"id": canonical_id, "n": n})
    unlocks = await read(
        "MATCH (c:CanonicalConcept {canonical_id:$id})-[r:PREREQUISITE]->(d:CanonicalConcept) "
        "RETURN d.canonical_id AS canonical_id, d.name AS name, d.difficulty AS difficulty, r.confidence AS confidence "
        "ORDER BY r.confidence DESC LIMIT $n", {"id": canonical_id, "n": n})
    return {"canonical_id": canonical_id, "prerequisites": prereqs, "unlocks": unlocks}


async def list_galaxies() -> dict[str, Any]:
    """The 11 top-level thematic galaxies — the broadest map of the graph."""
    rows = await read(
        "MATCH (g:Galaxy) RETURN g.galaxy_id AS galaxy_id, g.name AS name, "
        "g.name_hebrew AS name_hebrew, g.great_question AS great_question, "
        "g.constellation_count AS constellation_count ORDER BY g.galaxy_id")
    return {"count": len(rows), "galaxies": rows}


async def browse_constellation(constellation_id: str | None = None, galaxy_id: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """With a constellation_id: return that constellation and its member concepts.
    Otherwise list constellations (optionally filtered by galaxy_id)."""
    n = config.clamp_limit(limit)
    if constellation_id:
        con = await read(
            "MATCH (con:Constellation {constellation_id:$id}) RETURN con.constellation_id AS constellation_id, "
            "con.name AS name, con.name_hebrew AS name_hebrew, con.fundamental_question AS fundamental_question, "
            "con.description AS description, con.gateway_insight AS gateway_insight, con.primary_domain AS primary_domain, "
            "con.galaxy_id AS galaxy_id, con.size AS size LIMIT 1", {"id": constellation_id})
        members = await read(
            "MATCH (c:CanonicalConcept)-[:IN_CONSTELLATION]->(con:Constellation {constellation_id:$id}) "
            "RETURN c.canonical_id AS canonical_id, c.name AS name, c.difficulty AS difficulty, c.is_keystone AS is_keystone "
            "ORDER BY c.is_keystone DESC, c.name LIMIT $n", {"id": constellation_id, "n": config.MAX_LIMIT})
        entry_points = await read(
            "MATCH (con:Constellation {constellation_id:$id})-[:ENTRY_POINT]->(c:CanonicalConcept) "
            "RETURN c.canonical_id AS canonical_id, c.name AS name, c.difficulty AS difficulty", {"id": constellation_id})
        bridges = await read(
            "MATCH (con:Constellation {constellation_id:$id})-[:BRIDGES]-(other:Constellation) "
            "RETURN DISTINCT other.constellation_id AS constellation_id, other.name AS name", {"id": constellation_id})
        return {"constellation": con[0] if con else None, "member_count": len(members),
                "concepts": members, "entry_points": entry_points, "bridges_to": bridges}
    where = "WHERE con.galaxy_id = $gid" if galaxy_id else ""
    rows = await read(
        f"MATCH (con:Constellation) {where} RETURN con.constellation_id AS constellation_id, con.name AS name, "
        "con.fundamental_question AS fundamental_question, con.galaxy_id AS galaxy_id, con.size AS size "
        "ORDER BY con.size DESC LIMIT $n", {"gid": galaxy_id, "n": n})
    return {"galaxy_id": galaxy_id, "count": len(rows), "constellations": rows}


async def get_commentaries_on(reference: str, limit: int | None = None) -> dict[str, Any]:
    """Commentary passages on a base text. Pass a base text slug (e.g.
    'bavli-berakhot') or a canonical id (e.g. 'bavli-berakhot_5_1')."""
    n = config.clamp_limit(limit)
    ref = reference.strip().lower()
    cypher = """
    MATCH (comm:TextUnit)-[r:CONNECTS_TO {kind:'comments_on'}]->(b:TextUnit)
    WHERE toLower(r.base_text_slug) = $ref OR toLower(b.canonical_id) = $ref OR toLower(b.text_slug) = $ref
    MATCH (comm)-[:BELONGS_TO]->(t:Text)
    RETURN DISTINCT comm.canonical_id AS canonical_id, comm.text_slug AS commentator_slug,
           t.title AS commentator_title, t.author AS author,
           comm.english_text AS english, comm.hebrew_text AS hebrew,
           b.canonical_id AS base_canonical_id
    LIMIT $n
    """
    rows = await read(cypher, {"ref": ref, "n": n})
    for r in rows:
        r["deep_link"] = _deep_link(r["canonical_id"])
    return {"reference": reference, "count": len(rows), "commentaries": rows}


async def get_entities_in_passage(su_id: str, limit: int | None = None) -> dict[str, Any]:
    """People, places, themes, concepts, etc. mentioned in a semantic unit."""
    n = config.clamp_limit(limit)
    rows = await read(
        "MATCH (su:SemanticUnit {su_id:$id})<-[m:MENTIONED_IN]-(e:Entity) "
        "RETURN e.entity_type AS type, e.name AS name, e.name_hebrew AS name_hebrew, "
        "e.description AS description, m.importance AS importance "
        "ORDER BY m.importance DESC LIMIT $n", {"id": su_id, "n": n})
    return {"su_id": su_id, "count": len(rows), "entities": rows}


async def list_texts(genre: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """List corpus texts (optionally filtered by genre)."""
    n = config.clamp_limit(limit)
    where = "WHERE t.genre = $genre" if genre else ""
    rows = await read(
        f"MATCH (t:Text) {where} RETURN t.slug AS slug, t.title AS title, t.genre AS genre, "
        "t.era AS era, t.author AS author ORDER BY t.title LIMIT $n", {"genre": genre, "n": n})
    return {"genre": genre, "count": len(rows), "texts": rows}


# ---------------------------------------------------------------------------
# Full-coverage tools — every node label and relationship type in the graph.
# ---------------------------------------------------------------------------

# entity_type values in the graph (largest first).
ENTITY_TYPES = [
    "teaching", "interpretive_claim", "tension", "theme", "concept", "question",
    "language_token", "citation", "object", "person", "value", "argument",
    "collective", "place",
]


async def search_entities(query: str, entity_type: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """Search the extraction layer (2.5M entities: people, places, themes, concepts,
    teachings, tensions, questions, …) by name/description. Optionally filter by
    entity_type (see ENTITY_TYPES). This layer is LLM-extracted — rich evidence,
    not adjudicated truth."""
    n = config.clamp_limit(limit)
    safe = " ".join(w for w in __import__("re").findall(r"[\w֐-׿]+", query) if len(w) > 1)
    cypher = """
    CALL db.index.fulltext.queryNodes('entity_name_fulltext', $q) YIELD node AS e, score
    WHERE $etype IS NULL OR e.entity_type = $etype
    RETURN e.entity_id AS entity_id, e.name AS name, e.name_hebrew AS name_hebrew,
           e.entity_type AS entity_type, e.description AS description,
           e.domain AS domain, e.text_slug AS text_slug, score
    ORDER BY score DESC LIMIT $n
    """
    rows = await read(cypher, {"q": safe or query, "etype": entity_type, "n": n})
    return {"query": query, "entity_type": entity_type, "count": len(rows), "entities": rows}


async def get_related_entities(entity_id: str, rel_types: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
    """Entity-to-entity relationships discovered within texts. rel_types filters on:
    DEVELOPS, CONTRADICTS, EXEMPLIFIES, APPLIES_TO, CONTEXTUALIZES, EQUIVALENT."""
    n = config.clamp_limit(limit)
    cypher = """
    MATCH (e:Entity {entity_id: $id})-[r:DEVELOPS|CONTRADICTS|EXEMPLIFIES|APPLIES_TO|CONTEXTUALIZES|EQUIVALENT]-(o:Entity)
    WHERE $rel_types IS NULL OR type(r) IN $rel_types
    RETURN o.entity_id AS entity_id, o.name AS name, o.entity_type AS entity_type,
           type(r) AS relationship, r.confidence AS confidence, r.evidence_count AS evidence_count
    ORDER BY r.confidence DESC LIMIT $n
    """
    rows = await read(cypher, {"id": entity_id, "rel_types": rel_types, "n": n})
    return {"entity_id": entity_id, "count": len(rows), "related": rows}


async def get_talmudic_structure(reference: str) -> dict[str, Any]:
    """For a Talmudic passage, return its sugya (driving question, conclusion/maskana,
    type) and the ordered dialectical moves (question/answer/objection/proof, speaker,
    stratum). Pass a sugya_id or a TextUnit canonical_id (e.g. 'bavli-arakhin_3_1')."""
    ref = reference.strip()
    sugya = await read(
        "MATCH (s:Sugya) WHERE s.sugya_id = $ref OR toLower(s.canonical_reference) = toLower($ref) "
        "OR EXISTS { (s)-[:LOCATED_IN]->(:TextUnit {canonical_id: $ref}) } "
        "RETURN s.sugya_id AS sugya_id, s.text_slug AS text_slug, s.canonical_reference AS canonical_reference, "
        "s.sugya_type AS sugya_type, s.driving_question AS driving_question, "
        "s.conclusion_status AS conclusion_status, s.maskana AS maskana LIMIT 1", {"ref": ref})
    if not sugya:
        return {"reference": reference, "found": False, "hint": "Pass a sugya_id or a Talmud TextUnit canonical_id like 'bavli-berakhot_5_1'."}
    sid = sugya[0]["sugya_id"]
    moves = await read(
        "MATCH (m:Move)-[:PART_OF]->(s:Sugya {sugya_id: $sid}) "
        "RETURN m.sequence AS sequence, m.move_type AS move_type, m.marker AS marker, "
        "m.marker_translation AS marker_translation, m.speaker AS speaker, m.stratum AS stratum, "
        "m.content_summary AS content_summary ORDER BY m.sequence", {"sid": sid})
    return {"reference": reference, "found": True, "sugya": sugya[0], "move_count": len(moves), "moves": moves}


async def get_corridors_for_text(text_slug: str, limit: int | None = None) -> dict[str, Any]:
    """List the learning corridors built over a text, with their module count."""
    n = config.clamp_limit(limit)
    rows = await read(
        "MATCH (t:Text {slug: $slug})-[:HAS_CORRIDOR]->(c:Corridor) "
        "RETURN c.corridor_id AS corridor_id, c.title AS title, c.total_modules AS total_modules "
        "ORDER BY c.corridor_id LIMIT $n", {"slug": text_slug, "n": n})
    return {"text_slug": text_slug, "count": len(rows), "corridors": rows}


async def get_corridor(corridor_id: str, limit: int | None = None) -> dict[str, Any]:
    """A corridor's ordered learning modules (concept, domain, anchor quote). Modules
    are sequenced by module_number and linked LEADS_TO in study order."""
    n = max(config.clamp_limit(limit), config.MAX_LIMIT)
    rows = await read(
        "MATCH (c:Corridor {corridor_id: $id})-[:HAS_MODULE]->(m:CorridorModule) "
        "RETURN m.module_id AS module_id, m.module_number AS module_number, m.concept_name AS concept_name, "
        "m.domain AS domain, m.anchor_quote AS anchor_quote, m.anchor_id AS anchor_id, m.stance AS stance "
        "ORDER BY m.module_number LIMIT $n", {"id": corridor_id, "n": n})
    for r in rows:
        r["deep_link"] = _deep_link(r.get("anchor_id"))
    return {"corridor_id": corridor_id, "module_count": len(rows), "modules": rows}


async def get_concept_sources(canonical_id: str, limit: int | None = None) -> dict[str, Any]:
    """The actual corpus passages that ground a canonical concept (via the modules
    that instantiate it). Use this to read the texts behind an abstract concept."""
    n = config.clamp_limit(limit)
    rows = await read(
        f"""
        MATCH (c:CanonicalConcept {{canonical_id: $id}})<-[:INSTANCE_OF]-(m:CorridorModule)-[:COVERS]->(su:SemanticUnit)
        MATCH (su)-[:BELONGS_TO]->(t:Text)
        WITH DISTINCT su, t
        RETURN {_SU_FIELDS}, null AS similarity
        LIMIT $n
        """, {"id": canonical_id, "n": n})
    return {"canonical_id": canonical_id, "count": len(rows), "passages": [_passage(r) for r in rows]}


async def get_temporal_neighbors(canonical_id: str, limit: int | None = None) -> dict[str, Any]:
    """Chronological context: concepts that historically precede or follow this one
    (TEMPORAL_PRECEDES — distinct from the pedagogical PREREQUISITE order)."""
    n = config.clamp_limit(limit)
    precedes = await read(
        "MATCH (a:CanonicalConcept)-[:TEMPORAL_PRECEDES]->(c:CanonicalConcept {canonical_id:$id}) "
        "RETURN a.canonical_id AS canonical_id, a.name AS name, a.era_span AS era_span LIMIT $n", {"id": canonical_id, "n": n})
    follows = await read(
        "MATCH (c:CanonicalConcept {canonical_id:$id})-[:TEMPORAL_PRECEDES]->(b:CanonicalConcept) "
        "RETURN b.canonical_id AS canonical_id, b.name AS name, b.era_span AS era_span LIMIT $n", {"id": canonical_id, "n": n})
    return {"canonical_id": canonical_id, "earlier": precedes, "later": follows}


async def get_connections(reference: str, kinds: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
    """The Sefaria/citation connection graph for a passage. CONNECTS_TO links a
    TextUnit to related TextUnits with a `kind`: comments_on, 'Quoting Commentary',
    Midrash, Tanakh, Talmud, targum, Halakhah, Kabbalah, Musar, Chasidut, Responsa,
    'mesorat hashas', 'ein mishpat', quotation, reference, … Pass a canonical id
    ('bavli-berakhot_5_1') or a text slug; optionally filter by kinds."""
    n = config.clamp_limit(limit)
    ref = reference.strip().lower()
    cypher = """
    MATCH (a:TextUnit)-[r:CONNECTS_TO]-(b:TextUnit)
    WHERE toLower(a.canonical_id) = $ref OR toLower(a.text_slug) = $ref
    WITH a, r, b, coalesce(r.kind, r.link_type, 'related') AS kind
    WHERE $kinds IS NULL OR kind IN $kinds
    MATCH (b)-[:BELONGS_TO]->(t:Text)
    RETURN kind, b.canonical_id AS target_id, b.text_slug AS target_slug,
           t.title AS target_title,
           CASE WHEN startNode(r) = a THEN 'outgoing' ELSE 'incoming' END AS direction
    LIMIT $n
    """
    rows = await read(cypher, {"ref": ref, "kinds": kinds, "n": n})
    for row in rows:
        row["deep_link"] = _deep_link(row.get("target_id"))
    return {"reference": reference, "count": len(rows), "connections": rows}


async def run_cypher(query: str, params: dict[str, Any] | None = None, limit: int | None = None) -> dict[str, Any]:
    """Run your OWN read-only Cypher and traverse the graph however you like — this
    is the raw doorway. Writes/admin are rejected; only db.index.vector/fulltext
    CALLs are allowed; a LIMIT is enforced. See docs/schema.md for every node label,
    relationship type, and property. (For semantic search use search_corpus — you
    can't easily pass a 1024-d vector here.)"""
    n = config.clamp_limit(limit)
    q = query.strip().rstrip(";")
    for m in _CALL_PROC_RE.finditer(q):
        if m.group(1).lower() not in _ALLOWED_CALL_PROCS:
            return {"error": f"CALL {m.group(1)} is not permitted. Only read queries "
                             "(plus db.index.vector / db.index.fulltext) are allowed."}
    if "limit" not in q.lower():
        q = f"{q}\nLIMIT {n}"
    try:
        rows = await read(q, params or {})  # read() rejects write/admin Cypher
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:  # surface Cypher syntax/runtime errors to the agent
        return {"error": f"query failed: {e}"}
    return {"row_count": len(rows[:n]), "rows": rows[:n], "note": "read-only result, capped"}
