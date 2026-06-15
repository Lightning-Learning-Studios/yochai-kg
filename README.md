# Yochai Open KG

**A read-only doorway into a knowledge graph of the Jewish textual tradition — open to any AI agent.**

This repository is a gateway. Behind it sits a graph that weaves together more than a thousand foundational Jewish works — Tanakh, Talmud, Midrash, Halakha, Kabbalah, Hasidut, philosophy, responsa, and their commentaries — into something an AI agent can walk through, search by meaning, and reason over. Point your agent (Claude, or any tool that speaks MCP) at the gateway and ask it to study with you: find sources, trace how an idea develops across centuries, build a source sheet, compose a dvar torah, map what you'd need to learn first.

It is a **chavruta** — a study partner — not a *posek*. Everything it returns is derived study material with a link back to the source. Verify against the primary text. ([Why this matters →](./docs/disclaimer.md))

### See it before you connect

The fastest way to understand what's inside is to look at it. The **Atlas** is a live, interactive map of the graph — galaxies, constellations, and the concepts inside them — no login, no key:

**→ [yochai.lightningstudios.ai/knowledge-graph-preview](https://yochai.lightningstudios.ai/knowledge-graph-preview)**

Built by [Lightning Learning Studios](https://lightningstudios.ai), the team behind [Yochai](https://yochai.lightningstudios.ai).

### What's inside the graph

- **1,037 texts** — Tanakh, Talmud (Bavli & Yerushalmi), Midrash, Halakha, Kabbalah, Hasidut, Jewish philosophy, responsa, and their commentaries.
- **373,000 searchable passages** — every one bilingual (Hebrew + English), retrievable by *meaning*, not just keyword.
- **2.57 million extracted entities** — the people, places, themes, teachings, claims, and tensions the texts mention (machine-extracted; evidence, not adjudicated truth).
- **17,635 canonical concepts** — deduplicated ideas synthesized across the whole corpus, linked by typed relationships.
- **A prerequisite learning DAG** — for any concept, what you'd want to understand first.
- **269 constellations in 11 galaxies** — a thematic map of the tradition, from the broadest "great questions" down to individual ideas.
- **Learning corridors** — built study sequences that walk you through a text concept by concept.
- **Citations + deep links on everything** — every passage comes back with its reference and a link straight to the source.

All of it is reachable through **18 read-only MCP tools**. You cannot edit the graph; neither can anyone else. The gateway is read-only by construction — it refuses any write and never exposes database credentials.

---

## Get connected in 2 minutes

You need two things: a (free) API key, and an MCP client. The example below uses **Claude Desktop**, but any MCP-capable agent works (Claude API, Cursor, your own).

### 1. Request a free key

The gateway is free to use. We ask for a key so we can keep it healthy for everyone (rate limits, abuse protection — no cost to you). Requests are reviewed by the team and the key arrives by email.

**→ [Request a free API key](https://yochai-kg-gateway-production.up.railway.app/request-key)**

### 2. Paste this into your Claude Desktop config

Open Claude Desktop → Settings → Developer → Edit Config, and add the `yochai-kg` block. Drop your key in where it says `YOUR_FREE_KEY`, save, and restart Claude Desktop.

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

The key always travels in the `x-api-key` header. That's the whole setup.

### 3. Ask your first question

Paste this to your agent and watch it work:

> **Use the yochai-kg tools to find three passages on *teshuvah* (repentance), then show me one canonical concept that develops the idea and what I'd want to understand first. Cite each passage with its reference and link.**

A capable agent will call `search_corpus("teshuvah repentance")`, `search_concepts("teshuvah")`, `get_concept_neighborhood(...)`, and `get_prerequisites(...)`, then hand you cited, bilingual sources with a suggested learning order. You're studying.

> Full walkthrough → [docs/quickstart-mcp.md](./docs/quickstart-mcp.md). Want a dozen worked conversations across every kind of user? → [docs/use-cases.md](./docs/use-cases.md).

---

## Choose your path

The same graph serves a curious child and a seasoned scholar. Here's where to start, with prompts you can literally type to your agent.

### For the curious (including kids, with a grown-up or agent helping)

The Torah is full of stories and questions. Just ask, and the agent will find the real sources and explain them simply.

- *"What does the Torah say about being kind to animals? Find me two real sources and explain them like I'm 10."* → The agent searches the corpus, returns passages (e.g. on shooing away the mother bird, or feeding your animals before yourself), and explains them in plain language — with the real references so you can check.
- *"Tell me the story of Noah and the flood, and find the actual verses it comes from."* → Real verses, in Hebrew and English, with a link to read more.
- *"What's a galaxy in this map? Show me one and a question it asks."* → `list_galaxies()` returns the 11 great themes; pick one and explore.

What you get: real sources, explained gently, never made up. If the agent can't find something, it says so.

### For educators (Hebrew school, adult ed, day school)

Build teaching material grounded in primary sources in minutes, then check every citation.

- *"Build me a one-page source sheet on *hachnasat orchim* (welcoming guests) with 4 sources spanning Torah, Talmud, and a later code. Hebrew and English, with references."* → The agent runs the **source-sheet** skill: `search_corpus`, `lookup_passage`, and `list_texts(genre=...)` to span eras, returning a ready-to-print sheet.
- *"Give me three discussion questions for a class on Cain and Abel, each anchored to a specific verse."* → Verse-anchored questions you can verify.
- *"What's a good order to teach the concept of *brit* (covenant)? Show me the prerequisite chain."* → `search_concepts` → `get_prerequisites` returns a learning sequence.

What you get: classroom-ready sheets and questions, every claim tied to a source you can open.

### For scholars and Rabbanim

The graph exposes structure you can interrogate, not just text you can search — Talmudic discourse, typed concept relations, prerequisite and temporal ordering.

- *"Map the sugya in Berakhot 2a: its driving question, the dialectical moves, and which canonical concepts the machloket touches."* → `get_talmudic_structure("Berakhot 2a")` returns the sugya's `driving_question`, its `Move`s (with speaker and stratum) and *maskana*; `search_concepts` ties the dispute to canonical concepts.
- *"Trace every commentary indexed on Genesis 22:2, and show me how the concept it anchors relates to others — DEVELOPS, CONTRADICTS, RESONATES."* → `get_commentaries_on("Genesis 22:2")` plus `get_concept_neighborhood(id, rel_types=["DEVELOPS","CONTRADICTS","RESONATES"])`.
- *"Build a source sheet on *teshuvah* across eras — a Tannaitic source, an Amoraic sugya, a Rishonic code, and a Hasidic teaching — and show the prerequisite concepts a beginner would need."* → `search_corpus` + `list_texts(genre)` across strata, then `get_prerequisites`.
- *"Place the concept of *tzimtzum* chronologically against its neighbors."* → `get_temporal_neighbors(id)` over the `TEMPORAL_PRECEDES` ordering.

What you get: structured, citeable scaffolding for your own learning and teaching — with the honest caveat that the concept and entity layers are machine-synthesized. Treat them as a map, then go to the daf.

### For researchers and academics

Query the graph as a dataset: a typed concept network, a 2.57M-entity extraction layer, a prerequisite DAG, and a thematic clustering — all behind structured tools.

- *"Across the corpus, which canonical concepts sit at the center of the most CANONICAL_REL connections, and what constellations do they belong to?"* → `search_concepts`, `get_concept_neighborhood`, `browse_constellation`.
- *"Find every passage where the entity 'Hillel' is MENTIONED_IN, then show his entity-to-entity relations."* → `search_entities("Hillel", entity_type="person")` → `get_related_entities(id)`.
- *"Compare how two constellations frame their 'fundamental question,' and list each one's entry-point concept."* → `list_galaxies()` → `browse_constellation(id)`.

What you get: a navigable research surface over the tradition. The schema, node labels, relationship types, and counts are documented in [docs/schema.md](./docs/schema.md). For local analysis at scale, run your own copy (below).

### For developers

The gateway is plain MCP over Streamable-HTTP. Wire it into any agent and you have a grounded, citeable Jewish-text toolset with zero database credentials exposed.

- Connect with the JSON config above, or run your own instance locally over stdio (see [Run your own copy](#run-your-own-copy)).
- Load a **skill** from [`/skills`](./skills/README.md) to get repeatable, high-quality output (a dvar torah, a source sheet, a research brief) instead of ad-hoc prompting.
- Build product on top: study apps, source-sheet generators, research assistants, classroom tools.

What you get: 18 read-only tools, bilingual results with citations and deep links, and a schema you can rely on. Start at [docs/quickstart-mcp.md](./docs/quickstart-mcp.md).

---

## What you can build

The [`/skills`](./skills/README.md) folder holds **ready-made recipes** — single `SKILL.md` files that teach an agent to chain the tools into excellent, source-grounded output:

| Skill | What it produces |
| --- | --- |
| [`dvar-torah`](./skills/dvar-torah) | A grounded dvar torah on a parsha, theme, or verse. |
| [`source-sheet`](./skills/source-sheet) | A curated, bilingual source sheet spanning texts and eras. |
| [`cite`](./skills/cite) | Verified citations — never a fabricated reference. |
| [`outline`](./skills/outline) | A learning outline ordered by the prerequisite DAG. |
| [`research`](./skills/research) | A deeper, multi-source research brief on a question. |

Tell your agent *"load the source-sheet skill from yochai-kg and build me a sheet on…"* and it follows the recipe. **Writing your own skill is the easiest way to contribute** — copy [`skills/_template/SKILL.md`](./skills/_template), fill it in, and open a PR. See [`skills/README.md`](./skills/README.md) for the anatomy and the chevruta values every skill holds.

## The tools

There are **18 read-only MCP tools**, covering every layer of the graph — corpus and passages, concepts, the thematic map, Talmudic structure, learning paths, and the extraction layer. Rather than re-list them all here, see the annotated table in **[docs/quickstart-mcp.md](./docs/quickstart-mcp.md)** (and the full coverage map in [docs/schema.md](./docs/schema.md)). Every tool returns structured, bilingual results with citations and deep links back to the source.

## Run your own copy

Prefer to run the gateway yourself — for local research, offline work, or to wire into Claude Desktop over stdio? You can, with no hosted key at all. It's a small Python package (`pip install -e .`). Full instructions, including the stdio config for Claude Desktop, are in **[docs/quickstart-mcp.md → Option B](./docs/quickstart-mcp.md)**.

## Contributing

This is meant to grow. Three ways to help, all warmly welcomed:

- **Write a skill** — a new recipe in [`/skills`](./skills/README.md). The lowest-friction, highest-value contribution.
- **Submit a text** — propose a work for the corpus via a PR to [`/submitted_texts`](./submitted_texts) (see the live [help-wanted list](./submitted_texts/WANTED.md)).
- **Improve the gateway or docs** — bug fixes, new tools, clearer guides.

Start with [CONTRIBUTING.md](./CONTRIBUTING.md). Be excellent; this corpus is sacred to many.

## Responsible use

This is derived study material, not a halakhic authority — a chavruta, not a posek. Verify against the primary text, distinguish source from synthesis, and never present output as p'sak. Please read [docs/disclaimer.md](./docs/disclaimer.md).

## License

Gateway **code** is [Apache-2.0](./LICENSE). Corpus **data** is provided for study and research; underlying texts retain their own licenses (largely public-domain / Sefaria CC) — follow the source links and don't assume blanket redistribution rights.
