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
| `search_corpus(query, text_filter?, limit?)` | Semantic search over the corpus. Returns ranked bilingual passages with citation ref + deep-link. |
| `lookup_passage(reference)` | Exact passage by reference, e.g. `"Berakhot 2a"`, `"Genesis 1:1"`. Deterministic, not similarity-based. |
| `search_concepts(query)` | Find canonical concepts by theme. |
| `get_concept(canonical_id)` | A concept's definition, difficulty, and traditions. |
| `get_concept_neighborhood(canonical_id, rel_types?)` | Typed concept neighbors: `DEVELOPS`, `CONTRADICTS`, `RESONATES`, `EXEMPLIFIES`, `APPLIES_TO`, `ADDRESSES`, `SHARES_METHOD`, `CONTEXTUALIZES`. |
| `get_prerequisites(canonical_id)` | Prerequisite-DAG ancestors, for learning order. |
| `list_galaxies()` / `browse_constellation(constellation_id)` | Macro thematic navigation across the graph. |
| `get_commentaries_on(reference)` | Commentary passages on a base text. |
| `get_entities_in_passage(su_id)` | People, places, themes, and concepts mentioned in a passage. |

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
