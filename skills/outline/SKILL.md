# Outline

## Purpose

Build a learning outline on a topic: an ordered sequence of concepts from
foundational to advanced, each grounded in the knowledge graph and the corpus, so
a learner knows *what to study in what order* and why. A map for first encounter,
not a table of contents.

## When to use

- The user wants a study path, syllabus, or learning sequence for a topic or
  concept ("how do I work up to understanding *tzimtzum*?", "outline a path
  through the laws of teshuvah").
- **Not for:** a sources handout (use **source-sheet**) or a finished essay
  (use **dvar-torah**).

## MCP tools used

- `search_concepts(query)` — find the canonical concept(s) at the heart of the topic.
- `get_concept(canonical_id)` — definition, difficulty, traditions for ordering.
- `get_prerequisites(canonical_id)` — prerequisite-DAG ancestors → the foundation
  layer and the order to climb.
- `browse_constellation(constellation_id)` / `list_galaxies()` — the macro
  thematic neighborhood the topic sits in.
- `get_corridors_for_text(text_slug)` / `get_corridor(corridor_id)` — a pre-built
  learning sequence over a text, if one exists. Ordered modules, each with a concept,
  domain, and anchor quote. Check this before building a path by hand.
- `get_temporal_neighbors(canonical_id)` — historical order, as distinct from the
  pedagogical order `get_prerequisites` gives. Use it when the learner wants to know
  how an idea developed, not just what to read first.
- `search_corpus(query, text_filter?)` — attach a real anchor text to each step.

## Method

Sequence from the graph's prerequisite structure; ground each step in a passage.

1. **Check for an existing corridor.** If the topic maps onto one text, call
   `get_corridors_for_text(text_slug="bereishit")` → `corridor_bereishit`, 71 modules.
   `get_corridor(corridor_id="corridor_bereishit")` returns them ordered, each with a
   `concept_name`, `domain`, and `anchor_quote`. A curated sequence beats one you
   assemble from the DAG; adapt it rather than duplicating it. If no corridor exists,
   build the path from step 2.
2. **Locate the concept.** `search_concepts(query="tzimtzum divine contraction")`
   → pick the canonical id (e.g. `c_tzimtzum`). `get_concept(canonical_id="c_tzimtzum")`
   to read its definition and difficulty.
3. **Pull the prerequisite DAG.** `get_prerequisites(canonical_id="c_tzimtzum")`
   returns the ancestors a learner needs first. These give you the *foundational*
   end of the sequence and the climb order — study prerequisites before the target.
4. **Place it in the macro map.** `browse_constellation(constellation_id="<the
   constellation the concept belongs to>")` (start from `list_galaxies()` if you
   need to find it) to see sibling concepts and where the topic widens.
5. **Order foundational → advanced.** Lay out the steps: each prerequisite first,
   then the target concept, then 1–2 advanced neighbors that extend it. Use the
   `difficulty` from `get_concept` to break ties and to flag where the climb steepens.
6. **Anchor each step in a text.** For every step, attach one real source so the
   outline is studyable, not abstract:
   `search_corpus(query="tzimtzum self-limitation creation", text_filter="tanya")`.
   Use the returned reference; don't invent one.

## Output format

An ordered list of steps. Per step: a short label, the concept it teaches (with
difficulty), *why it comes here* (what it builds on), and one anchor source by
reference. Foundational steps first; advanced last. A one-line framing of the
whole arc at the top.

## Worked example

**Request:** "A path to understanding *tzimtzum*."

1. `search_concepts(query="tzimtzum divine contraction")` → `c_tzimtzum`;
   `get_concept(canonical_id="c_tzimtzum")` → advanced; Kabbalistic/Hasidic.
2. `get_prerequisites(canonical_id="c_tzimtzum")` → `c_creation_ex_nihilo`,
   `c_divine_infinitude`, `c_ein_sof`.
3. `browse_constellation(constellation_id="kabbalah-cosmology")` → neighbors:
   `c_sefirot`, `c_shevirat_hakelim`.
4. Order: creation ex nihilo → divine infinitude → Ein Sof → **tzimtzum** →
   shevirat hakelim.
5. `search_corpus(query="tzimtzum contraction make room for world", text_filter="tanya")`
   → anchor for the target step.

**Result (sketch):**

> **Arc:** from "why is there a world at all" up to the Lurianic contraction.
> 1. *Creation ex nihilo* (intro) — anchor: Genesis 1:1 + Ramban there. Builds the
>    question tzimtzum answers.
> 2. *Ein Sof / divine infinitude* (intermediate) — …
> 4. **Tzimtzum** (advanced) — anchor: Tanya, Shaar HaYichud ch. 7. The contraction
>    that makes room for a world.

## Notes / limits

- The DAG is the authority on pedagogical order — don't reorder from intuition
  against it. It is not a chronology; for that use `get_temporal_neighbors`, which
  returns `earlier`/`later` with `era_span`.
- Corridor `anchor_id`s use a different identifier scheme from canonical ids
  (`gen.1.1-2`, not `bereishit_1_1`). Use the `deep_link` the corridor returns rather
  than converting between them.
- If a concept isn't in the graph, `search_concepts` will return the nearest
  matches; pick a real one or tell the user the exact concept isn't indexed.
- Attach only real anchor texts (from `search_corpus`/`lookup_passage`). Don't
  invent a reference to make a step look complete.
- This is a study path, not a ruling on what a learner "must" believe.
