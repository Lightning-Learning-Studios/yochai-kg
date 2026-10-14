# Skills

A **skill** is a portable recipe — a single `SKILL.md` file — that teaches an AI
agent how to produce excellent, source-grounded output by calling the Yochai Open
KG **MCP gateway**. The gateway exposes the Jewish textual corpus and its knowledge
graph as a small set of **read-only** tools. A skill chains those tools into a
method: search, look up, cross-reference, then synthesize.

Skills are model-agnostic and runtime-agnostic. Any agent that can speak MCP and
read Markdown can load a skill and follow it. Nothing here depends on Yochai's
internal app, its UI, or its rendering layer — only on the public MCP tools.

## The MCP tools a skill may call

All tools are read-only and return bilingual (Hebrew + English) passages with a
citation reference and a deep-link where applicable.

| Tool | What it does |
| --- | --- |
| `search_corpus(query, text_filter?, limit?)` | Semantic search over the corpus. Returns ranked bilingual passages with `su_id`, `anchor`, `reference` + deep-link. |
| `lookup_passage(reference)` | Exact passage by **slug-style canonical id**, e.g. `bereishit_1_1`. Deterministic, not similarity-based. See *Referencing passages* below. |
| `list_texts(genre?, limit?)` | List corpus texts with their `slug`, `title`, `genre`, `era`. The way to discover a `text_filter` or build a canonical id. |
| `search_concepts(query, limit?)` | Find canonical concepts by theme. |
| `get_concept(canonical_id)` | A concept's definition, guiding question, gateway insight, difficulty, traditions, era span. |
| `get_concept_neighborhood(canonical_id, rel_types?, limit?)` | Typed concept neighbors: `DEVELOPS`, `CONTRADICTS`, `RESONATES`, `EXEMPLIFIES`, `APPLIES_TO`, `ADDRESSES`, `SHARES_METHOD`, `CONTEXTUALIZES`, `COMMENTARY`. |
| `get_concept_sources(canonical_id, limit?)` | The corpus passages that ground a concept — read the texts behind the abstraction. |
| `get_prerequisites(canonical_id, limit?)` | Prerequisite-DAG ancestors and what the concept unlocks, for learning order. |
| `get_temporal_neighbors(canonical_id, limit?)` | Concepts that historically precede/follow this one — chronological, distinct from the pedagogical order. |
| `list_galaxies()` / `browse_constellation(constellation_id?, galaxy_id?, limit?)` | Macro thematic navigation across the graph. |
| `get_corridors_for_text(text_slug, limit?)` / `get_corridor(corridor_id, limit?)` | Pre-built learning sequences over a text: ordered modules with concept, domain, anchor quote. |
| `get_commentaries_on(reference, limit?)` | Commentary passages on a base text. Takes a **base slug** (`bavli-berakhot`) or canonical id. In practice it resolves for Talmud bases; Tanakh bases return `count: 0` — see *Getting commentary on a Torah verse* below. |
| `get_connections(reference, kinds?, limit?)` | The Sefaria/citation connection graph for a passage (`CONNECTS_TO`): commentary, quoting-commentary, midrash, targum, cross-Talmud/Tanakh links, mesorat hashas, ein mishpat. |
| `get_entities_in_passage(su_id, limit?)` | People, places, themes, and concepts mentioned in a passage. |
| `search_entities(query, entity_type?, limit?)` | Search the extraction layer (people, places, themes, teachings, tensions, questions). Machine-extracted — rich evidence, not adjudicated truth. |
| `get_related_entities(entity_id, rel_types?, limit?)` | Entity-to-entity relations found within texts. |
| `get_talmudic_structure(reference)` | For a Talmud passage: its sugya (driving question, `maskana`) and the ordered dialectical moves (speaker, stratum). |
| `run_cypher(query, params?, limit?)` | Your own read-only Cypher against the graph. Writes blocked, LIMIT enforced. See [`docs/schema.md`](../docs/schema.md). |

## Referencing passages

`lookup_passage` and `get_commentaries_on` take **slug-style canonical ids**, not human-readable
citations. `lookup_passage(reference="Genesis 22:2")` returns `found: false`; the id is
`bereishit_22_2`. The format is `<text_slug>_<chapter>_<verse>` (see
[`docs/schema.md`](../docs/schema.md#identifiers-youll-see)).

Two reliable ways to get a real id:

1. **From a search result.** `search_corpus` returns `su_id`, `text_slug`, and `anchor` on every
   passage. Pass those onward rather than reconstructing a citation by hand.
2. **By looking the slug up.** `list_texts(genre="midrash")` browses by genre, but results are
   clamped (25 per call against 1,037 texts), so it is for browsing, not for finding one known
   work. To find a specific slug, use `run_cypher`:

   ```cypher
   MATCH (t:Text) WHERE toLower(t.title) CONTAINS 'rashi on genesis'
   RETURN t.slug, t.title, t.genre
   ```

   Then combine the slug with chapter and verse.

Three things to know before you build an id by hand:

- **No ranges.** `bereishit_22_1-19` does not resolve. One call per verse, or use `search_corpus`
  for the span.
- **Commentaries carry a fourth segment.** A commentary id is
  `<slug>_<chapter>_<verse>_<comment#>`: Rashi on Genesis 22:2 is `rashi-on-genesis_22_2_1`, not
  `rashi-on-genesis_22_2`. Base texts use the three-part form.
- **Talmud numbering is not daf/amud.** `bavli-sanhedrin_56_1` is not "Sanhedrin 56a". Don't map
  a daf reference to a chapter number by arithmetic — search for the passage and take its id.
- **Verify the hit.** A resolved id returns `found: true` plus the text. Read it and confirm it is
  the passage you meant before you cite it. A miss returns `found: false` with a format hint.

## Getting commentary on a Torah verse

`get_commentaries_on` is the obvious call, but for Tanakh bases it comes back empty:
`get_commentaries_on(reference="bereishit_22_2")`, `"bereishit"`, and `"bamidbar_16_1"` all return
`count: 0`, while `get_commentaries_on(reference="bavli-berakhot")` returns results. The
commentary *texts* are in the corpus either way — `rashi-on-genesis`, `ramban-on-genesis`,
`ibn-ezra-on-genesis` all exist as `Text` nodes.

So for Torah commentary, go through the commentary text directly:

- **Exact comment:** `lookup_passage(reference="rashi-on-genesis_22_2_1")` → *"קח נא TAKE NOW —
  The word נא is used as a request…"*. Remember the fourth segment.
- **Thematic:** `search_corpus(query="…", text_filter="ramban-on-genesis")`.
- **Citation graph:** `get_connections(reference="bereishit_22_2")` surfaces quoting-commentary
  and midrash links where the connection layer covers the verse (roughly a quarter of text units).

## Anatomy of a `SKILL.md`

Every skill follows the same shape. Copy [`_template/SKILL.md`](./_template/SKILL.md)
to start.

1. **Title** — the skill name.
2. **Purpose** — one or two sentences on what good output looks like.
3. **When to use** — the triggers; when *not* to reach for it.
4. **MCP tools used** — the subset of gateway tools this skill calls.
5. **Method** — numbered steps. Each step that touches the corpus names a real
   tool call with example arguments. This is the heart of the recipe.
6. **Output format** — the shape of the deliverable.
7. **Worked example** — a short end-to-end run with real arguments and a sketch
   of the result.
8. **Notes / limits** — failure modes, retry budgets, honesty rules.

Keep a skill to roughly 60–120 lines. A skill is a recipe, not a manual.

## How to write and PR a new skill

1. Copy `_template/SKILL.md` into `skills/<your-skill>/SKILL.md`.
2. Fill in every section. Make the **Method** concrete: every corpus-touching
   step must name a tool and show example arguments. Prose like "search for
   relevant sources" is not a recipe — `search_corpus(query="...", text_filter="...")`
   is.
3. Add a worked example you actually ran against the gateway, so the next reader
   trusts the recipe.
4. Open a PR. In the description, state the trigger ("when an agent should load
   this") and link any sibling skill it composes with.

## The chevruta values

These skills inherit the voice and discipline of Yochai, an AI *chevruta* (study
partner). Hold them in every skill:

- **Derived, not declared.** Every claim is grounded in a retrieved passage. If a
  tool didn't return it, you don't assert it. Reason *from* the sources you have,
  not from memory of what a text "probably" says.
- **Cite primary sources.** Refer to texts by their proper reference (*"Rashi on
  Genesis 22:2"*, *"Sanhedrin 56a"*, *"Mishneh Torah, Hilchot Teshuvah 3:5"*) and
  back every reference with a `lookup_passage` or `search_corpus` result. Never
  fabricate a quotation, a citation, or a passage that doesn't exist.
- **Not a posek.** These skills surface what sources *say*; they do not issue
  binding halakhic rulings. Present multiple voices fairly. Flag uncertainty.
- **Honest about gaps.** The corpus is finite. When a source you wanted isn't
  indexed, say so and offer an indexed substitute — never silently skip it, never
  paper over it with an invented passage. Omission with disclosure beats a
  mislabeled or phantom source.
- **Warm and rigorous.** Think *with* the learner. Engage the substance; don't
  narrate process or applaud the question. The signal of respect is close
  engagement with the text, not affect.
