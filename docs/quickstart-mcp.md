# Quickstart — connect your agent

The gateway speaks the **Model Context Protocol (MCP)**. Any MCP-capable agent
(Claude Desktop, Claude API, Cursor, your own) can use it as a toolset.

## Option A — hosted endpoint (recommended)

Point your client at the public Streamable-HTTP endpoint and (if enabled) pass your
free API key.

**Claude Desktop / MCP client config:**
```json
{
  "mcpServers": {
    "yochai-kg": {
      "type": "http",
      "url": "https://<gateway-host>/mcp",
      "headers": { "x-api-key": "YOUR_FREE_KEY" }
    }
  }
}
```

Get a free key: see the repo README ("Getting an API key").

## Option B — run it yourself

You'll need read access to a Yochai KG Neo4j (or your own export) and a DeepInfra key
for query embeddings.

```bash
git clone https://github.com/Lightning-Learning-Studios/yochai-kg
cd yochai-kg
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in NEO4J_* and DEEPINFRA_API_KEY
# stdio (Claude Desktop):
yochai-kg-gateway
# or hosted HTTP:
MCP_TRANSPORT=http PORT=8000 yochai-kg-gateway
```

**Claude Desktop (stdio) config:**
```json
{
  "mcpServers": {
    "yochai-kg": {
      "command": "yochai-kg-gateway",
      "env": { "NEO4J_YOCHAI_URI": "bolt://...", "NEO4J_YOCHAI_PASSWORD": "...", "DEEPINFRA_API_KEY": "..." }
    }
  }
}
```

## The tools

| Tool | Use it to… |
| --- | --- |
| `search_corpus(query, text_filter?, limit?)` | Find passages by meaning |
| `lookup_passage(reference)` | Get an exact passage (`bereishit_1_1`) |
| `get_commentaries_on(reference)` | Pull commentary on a base text |
| `get_connections(reference, kinds?)` | The full Sefaria/citation connection graph for a passage |
| `run_cypher(query, params?)` | Run your **own** read-only Cypher — traverse the graph freely |
| `list_texts(genre?)` | Browse the corpus |
| `search_concepts(query)` / `get_concept(id)` | Explore the ~17.6k canonical concepts |
| `get_concept_neighborhood(id, rel_types?)` | See how a concept relates to others |
| `get_concept_sources(id)` | Read the passages behind a concept |
| `get_prerequisites(id)` | Build a learning order (prerequisite DAG) |
| `get_temporal_neighbors(id)` | Place a concept chronologically |
| `list_galaxies()` / `browse_constellation(id?)` | Navigate the thematic map |
| `get_talmudic_structure(reference)` | Sugya + dialectical moves of a Talmud passage |
| `get_corridors_for_text(slug)` / `get_corridor(id)` | Walk a built learning sequence |
| `get_entities_in_passage(su_id)` | See who/what a passage mentions |
| `search_entities(query, entity_type?)` | Search the 2.5M-node extraction layer |
| `get_related_entities(entity_id, rel_types?)` | Entity-to-entity relations within texts |

## A first conversation

> "Use yochai-kg to find three passages on *teshuvah* (repentance), then show me one
> concept that develops the idea and what you'd need to understand first."

A capable agent will `search_corpus("teshuvah repentance")`, `search_concepts("teshuvah")`,
`get_concept_neighborhood(...)`, and `get_prerequisites(...)` — and cite each passage with its
deep link. For repeatable, high-quality outputs (a dvar torah, a source sheet, a learning
outline), load a **skill** from [`/skills`](../skills/README.md).

> Everything returned is derived study material with a link back to the source. Verify against
> the primary text. This is a chavruta, not a posek — see [disclaimer.md](./disclaimer.md).
