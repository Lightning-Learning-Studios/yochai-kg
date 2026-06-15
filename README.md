# Yochai Open KG

**Open, read-only access to the Yochai knowledge graph of the Jewish textual tradition — for AI agents and developers.**

Point your own agent at 1,000+ works (Tanakh, Talmud, Midrash, Halakha, Kabbalah, Hasidut, philosophy, responsa, and their commentaries), woven into a graph of ~373k searchable passages, ~17,600 synthesized concepts, a prerequisite learning DAG, and a thematic map of galaxies and constellations. Use it to study, research, build source sheets, compose divrei torah — whatever your agent can imagine.

Built by [Lightning Learning Studios](https://lightningstudios.ai), the team behind [Yochai](https://yochai.lightningstudios.ai).

---

## What's here

| | |
| --- | --- |
| **[`gateway/`](./gateway)** | A read-only **MCP server** exposing curated query tools over the graph. The safe public doorway — your agent connects to it; no database credentials are ever exposed. |
| **[`skills/`](./skills/README.md)** | A library of portable **recipes** (compose a dvar torah, build a source sheet, run deep research…) your agent loads to produce excellent, grounded output. Seeded from Yochai's own methods; PR your own. |
| **[`submitted_texts/`](./submitted_texts)** | A PR-based **corpus intake** — propose a new text for the graph. See the live [help-wanted list](./submitted_texts/WANTED.md). |
| **[`docs/`](./docs)** | [Quickstart](./docs/quickstart-mcp.md) · [Schema](./docs/schema.md) · [Cypher cookbook](./docs/cypher-cookbook.md) · [Disclaimer](./docs/disclaimer.md) |

## Quickstart

Connect any MCP client (Claude Desktop, Claude API, Cursor, your own agent) to the hosted endpoint:

```json
{
  "mcpServers": {
    "yochai-kg": {
      "type": "http",
      "url": "https://yochai-kg-gateway-production.up.railway.app/mcp",
      "headers": { "x-api-key": "YOUR_FREE_KEY" }
    }
  }
}
```

Then ask your agent: *"Use yochai-kg to find three passages on teshuvah, the concept that develops the idea, and what I'd need to learn first."* Full guide → [docs/quickstart-mcp.md](./docs/quickstart-mcp.md). Run it yourself → same doc, Option B.

## The tools (18 — every layer of the graph is reachable)

**Corpus & passages:** `search_corpus` · `lookup_passage` · `get_commentaries_on` · `list_texts`
**Concepts:** `search_concepts` · `get_concept` · `get_concept_neighborhood` · `get_concept_sources` · `get_prerequisites` · `get_temporal_neighbors`
**Map:** `list_galaxies` · `browse_constellation`
**Talmudic structure:** `get_talmudic_structure` (sugya + dialectical moves)
**Learning paths:** `get_corridors_for_text` · `get_corridor`
**Extraction layer:** `get_entities_in_passage` · `search_entities` · `get_related_entities`

Every node label (Text, TextUnit, SemanticUnit, Entity, Sugya, Move, CanonicalConcept, Constellation, Galaxy, Corridor, CorridorModule) and every relationship type is reachable through these tools. Each returns structured, bilingual (Hebrew + English) results with citations and deep links back to the source. See [docs/schema.md](./docs/schema.md) for the full inventory.

## Getting an API key

The hosted gateway uses **free API keys** (so we can keep it healthy for everyone — rate limits, abuse protection, no cost to you). [Request one here](#) *(link TBD)*. Or run your own copy with no key at all.

## Design principles

- **Read-only by construction.** The database is in read-only access mode and the gateway refuses write Cypher. You cannot edit the graph; neither can anyone else.
- **Curated by default, honest about the rest.** Texts, passages, and canonical concepts are the high-signal spine. The 2.5M-node entity layer is machine-extracted — powerful, but evidence, not adjudicated truth.
- **A chavruta, not a posek.** Everything is derived study material with a link to the source. Verify against the primary text. See [docs/disclaimer.md](./docs/disclaimer.md).

## Contributing

Skills, corpus submissions, gateway improvements, and docs are all welcome — see [CONTRIBUTING.md](./CONTRIBUTING.md). Be excellent; this corpus is sacred to many.

## License

Code: [Apache-2.0](./LICENSE). Corpus data: provided for study/research; underlying texts retain their own licenses (largely public-domain / Sefaria CC).
