# Knowledge Graph Schema

The Yochai KG is a Neo4j graph of the Jewish textual tradition. Counts below are
from the production graph (2026-06; they grow as the corpus expands). Everything
here is **read-only** through the gateway.

## How the graph is layered

```
Text ──BELONGS_TO── TextUnit ──IN_UNIT── SemanticUnit ──(vector search lands here)
                        │                      │
                  CONNECTS_TO            COVERS / MENTIONED_IN
                  (commentary)                 │
                                         CorridorModule ──INSTANCE_OF── CanonicalConcept
                                                                              │
                                              CANONICAL_REL / PREREQUISITE ───┤
                                                                              │
                                              IN_CONSTELLATION → Constellation → IN_GALAXY → Galaxy
```

- **Corpus layer** — the texts themselves, verse by verse (`TextUnit`), grouped into
  **`SemanticUnit`s**. This grouping is deliberate and is *the* reason retrieval works well:
  passages are segmented into **semantically coherent units of meaning** — not raw verses, and
  not arbitrary fixed-size chapters or windows. Each `SemanticUnit` is a self-contained idea
  (a complete teaching, a sugya step, a coherent passage), embedded as a whole, so a search
  returns a *meaningful* passage rather than a fragment or a wall of unrelated text. This is what
  `search_corpus` searches.
- **Extraction layer** — `Entity` nodes (people, places, themes, concepts, teachings,
  tensions, …) extracted from each passage. Surfaced by `get_entities_in_passage`.
- **Concept layer** — `CanonicalConcept`s: ~17,600 deduplicated ideas synthesized across
  the whole corpus, linked by typed relationships and a prerequisite DAG.
- **Map layer** — `Constellation`s and `Galaxy`s: thematic communities of concepts, the
  broadest navigable map.

## Node labels

| Label | ~Count | Key properties |
| --- | --- | --- |
| `Text` | 1,037 | `slug`, `title`, `genre`, `era`, `author` |
| `TextUnit` | 1.03M | `canonical_id` (`<slug>_<chapter>_<verse>`), `text_slug`, `english_text`, `hebrew_text`, `en_source` |
| `SemanticUnit` | 373K | `su_id`, `text_slug`, `english_text`, `hebrew_text`, `canonical_ref`, `section_label`, `first_anchor_id`, `last_anchor_id`, `genre`, `era`, `embedding` (1024-d) |
| `Entity` | 2.57M | `entity_id`, `entity_type`, `name`, `name_hebrew`, `description`, `domain`, `embedding` |
| `Sugya` / `Move` | 16.7K / 131K | Talmudic discourse structure (`driving_question`, `maskana`; move `type`, `speaker`, `stratum`) |
| `CanonicalConcept` | 17,635 | `canonical_id`, `name`, `name_hebrew`, `one_line_definition`, `description`, `question`, `gateway_insight`, `difficulty` (foundational/intermediate/advanced), `is_keystone`, `domain`, `traditions`, `era_span`, `embedding` |
| `Constellation` | 269 | `constellation_id`, `name`, `fundamental_question`, `gateway_insight`, `primary_domain`, `galaxy_id`, `size`, `embedding` |
| `Galaxy` | 11 | `galaxy_id`, `name`, `great_question`, `constellation_count`, `embedding` |
| `Corridor` / `CorridorModule` | 1,037 / 131.7K | Learning sequences; `CorridorModule` carries `concept_name`, `anchor_quote`, `su_coverage`, `domain` |

`entity_type` distribution (largest first): `teaching`, `interpretive_claim`, `tension`,
`theme`, `concept`, `question`, `language_token`, `citation`, `object`, `person`, `value`,
`argument`, `collective`, `place`. The entity layer is **LLM-extracted at scale** — rich and
useful (the live app uses it), but per-passage and not curated to the same bar as
`CanonicalConcept`. Treat it as evidence, not adjudicated truth.

## Relationship types — the COMPLETE list

These are **all 34 relationship types in the live graph**, enumerated directly from Neo4j
(`CALL db.relationshipTypes()`) with counts, on 2026-06. If a relationship isn't in this table,
it isn't in the graph. (`RELATED` exists with 0 rows — deterministic scaffolding, cleared after
the concept DAG was built.)

**Corpus structure**
| Type | From → To | Count | Meaning |
| --- | --- | --- | --- |
| `BELONGS_TO` | TextUnit/SemanticUnit → Text | 1.36M | Membership |
| `IN_UNIT` | TextUnit → SemanticUnit | 969K | Verse → semantic unit |

**Connection / citation layer (the Sefaria + LLM citation graph)**
| Type | From → To | Count | Meaning |
| --- | --- | --- | --- |
| `CONNECTS_TO {kind, base_text_slug}` | TextUnit → TextUnit | 439K | The reference graph. `kind` ∈ ~28 values: `comments_on` (236K), `Quoting Commentary` (78K), `commentary` (61K), `Midrash`, `Tanakh`, `Talmud`, `targum`, `Halakhah`, `Kabbalah`, `Musar`, `Chasidut`, `mesorat hashas`, `ein mishpat / ner mitsvah`, `Responsa`, `Mishnah`, `Tosefta`, `quotation`, `reference`, `dibur_hamatchil`, `Second Temple`, … |

(Also mirrored in Supabase: `yochai_connections` (1.09M, LLM-extracted explicit prooftexts),
`yochai_connections_new` (216K, Sefaria's official link graph), `yochai_connection_counts*`,
`yochai_sefaria_ref_map`. The `citation` entity_type (52K) is the citation layer at entity level.)

**Extraction layer**
| Type | From → To | Count | Meaning |
| --- | --- | --- | --- |
| `MENTIONED_IN {importance}` | Entity → SemanticUnit | 3.46M | Entity appears in passage |
| `EXTRACTED_FROM {importance}` | Entity → TextUnit | 4.85M | Extraction provenance |
| `DEVELOPS` / `CONTRADICTS` / `EXEMPLIFIES` / `APPLIES_TO` / `CONTEXTUALIZES` / `EQUIVALENT` | Entity → Entity | 614K / 338K / 190K / 23K / 6K / 31K | Discovered entity-to-entity relations |
| `LOCATED_IN` | Sugya → TextUnit | 18K | Talmudic sugya placement |
| `PART_OF` | Move → Sugya | 131K | Dialectical move in a sugya |

**Concept layer**
| Type | From → To | Count | Meaning |
| --- | --- | --- | --- |
| `INSTANCE_OF {role}` | CorridorModule → CanonicalConcept | 785K | Module realizes a concept |
| `CANONICAL_REL {relationship_type, confidence, direction}` | CanonicalConcept ↔ CanonicalConcept | 523K | `relationship_type` ∈ COMMENTARY, RESONATES, DEVELOPS, EXEMPLIFIES, ADDRESSES, APPLIES_TO, SHARES_METHOD, CONTEXTUALIZES, CONTRADICTS |
| `PREREQUISITE {confidence}` | CanonicalConcept → CanonicalConcept | 26K | Learning order (foundational → advanced) |
| `TEMPORAL_PRECEDES` | CanonicalConcept → CanonicalConcept | 54K | Chronological order |
| `ENRICHMENT {confidence}` | CanonicalConcept → CanonicalConcept | 24K | Non-prerequisite enrichment links |

**Cross-book reference graph (between corridor modules)**
| Type | From → To | Count | Meaning |
| --- | --- | --- | --- |
| `COMMENTS_ON` / `REFERENCES` / `DERIVES_FROM` / `TRANSLATES` / `CODIFIES` / `DISCUSSES` | CorridorModule → CorridorModule | 570K / 136K / 23K / 9K / 3K / 2K | How works reference each other across the corpus |

**Pedagogy & map**
| Type | From → To | Count | Meaning |
| --- | --- | --- | --- |
| `HAS_CORRIDOR` / `HAS_MODULE` / `LEADS_TO` | Text→Corridor / Corridor→Module / Module→Module | 1K / 132K / 140K | Learning corridors + their ordering |
| `COVERS` / `COVERS_ENTITY` | CorridorModule → SemanticUnit / Entity | 780K / 442K | Module grounding |
| `IN_CONSTELLATION` | CanonicalConcept → Constellation | 18K | Thematic membership |
| `IN_GALAXY` | Constellation → Galaxy | 269 | Map membership |
| `ENTRY_POINT` | Constellation → CanonicalConcept | 2K | Suggested starting concept |
| `BRIDGES` | Constellation → Constellation | 1.3K | Cross-constellation links |

**Don't want to learn the schema? You don't have to** — the curated tools cover the common
paths. **Want to traverse freely?** Use `run_cypher` to run your own read-only Cypher over
exactly these labels and edges. That's the raw doorway; this page is your map.

## Embeddings & indexes

All embeddings are **BGE-M3, 1024-dim, cosine**, stored on the `embedding` property and
served by Neo4j vector indexes: `semantic_unit_embeddings`, `canonical_concept_embeddings`,
`entity_embeddings`, plus `constellation_embeddings` / `galaxy_embeddings` / `sugya_embeddings`.
Fulltext indexes exist for concepts (`canonical_fulltext`), entities (`entity_name_fulltext`),
and semantic units (`semantic_unit_text_fulltext`). The gateway embeds your query with the same
model so vector search behaves exactly as it does in the live app.

## Identifiers you'll see

- `canonical_id` (TextUnit): `<slug>_<chapter>_<verse>`, e.g. `bavli-berakhot_5_1`, `bereishit_1_1`.
- `su_id` (SemanticUnit): `<slug>_su_<n>`.
- `canonical_id` (CanonicalConcept): `cluster_<n>`.
- `anchor` / `first_anchor_id`: the navigation token used in deep links `…/p/<anchor>`.

## Tool coverage — every layer is reachable

| Graph element | Tool(s) |
| --- | --- |
| `Text` | `list_texts`, `get_corridors_for_text` |
| `TextUnit` (verses) | `lookup_passage` |
| `SemanticUnit` + `embedding` | `search_corpus`, `get_concept_sources` |
| `CONNECTS_TO {comments_on}` | `get_commentaries_on` |
| `CONNECTS_TO` (all ~28 kinds — the Sefaria/citation graph) | `get_connections` |
| Cross-book module refs (`COMMENTS_ON`/`REFERENCES`/`DERIVES_FROM`/`TRANSLATES`/`CODIFIES`/`DISCUSSES`) + anything else | `run_cypher` |
| `Entity` + `MENTIONED_IN` | `get_entities_in_passage`, `search_entities` |
| Entity↔Entity (`DEVELOPS`/`CONTRADICTS`/`EXEMPLIFIES`/`APPLIES_TO`/`CONTEXTUALIZES`/`EQUIVALENT`) | `get_related_entities` |
| `Sugya` + `Move` (`LOCATED_IN`/`PART_OF`) | `get_talmudic_structure` |
| `CanonicalConcept` | `search_concepts`, `get_concept` |
| `CANONICAL_REL` (typed) | `get_concept_neighborhood` |
| `PREREQUISITE` DAG | `get_prerequisites` |
| `TEMPORAL_PRECEDES` | `get_temporal_neighbors` |
| `INSTANCE_OF` + `COVERS` | `get_concept_sources` |
| `Corridor`/`CorridorModule` (`HAS_CORRIDOR`/`HAS_MODULE`/`LEADS_TO`) | `get_corridors_for_text`, `get_corridor` |
| `Constellation`/`Galaxy` (`IN_CONSTELLATION`/`IN_GALAXY`/`ENTRY_POINT`/`BRIDGES`) | `list_galaxies`, `browse_constellation` |

If we map a new layer in the graph, it gets a tool here — the gateway is meant to expose the
*whole* graph, not a curated slice.
