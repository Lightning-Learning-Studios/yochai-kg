# Research

## Purpose

Multi-query deep research over the corpus: decompose a question into angles, run
several searches, cross-reference the concepts they surface, and synthesize a
concise, cited findings summary that names the clusters, tensions, and outliers.
Sources are the deliverable here — not an essay.

## When to use

- The user wants to *discover and map* what the tradition says on a topic, person,
  or theme — across genres and eras — before deciding what to do with it.
- **Not for:** composing a finished teaching (use **dvar-torah**) or a curated
  handout (use **source-sheet**).

## MCP tools used

- `search_corpus(query, text_filter?, limit?)` — the workhorse; run several,
  one per angle.
- `search_concepts(query)` / `get_concept(canonical_id)` — name and define the
  concepts the passages cluster around.
- `get_concept_neighborhood(canonical_id, rel_types?)` — find tensions
  (`CONTRADICTS`), developments (`DEVELOPS`), and resonances (`RESONATES`) to
  cross-reference.
- `get_entities_in_passage(su_id)` — see who/what a key passage invokes, to chase
  threads.

## Method

**Search before you speak.** Any topic, person, theme, or concept the user names
triggers a search *before* you write a word of synthesis. Don't chat about the
topic in general terms; don't ask clarifying questions first — search with your
best reading, then offer to refine.

1. **Decompose the question into angles.** A good research question has 2–4
   distinct facets — e.g. *"the Talmudic, Hasidic, and Mussar takes on anger."*
   List the angles before searching.
2. **Run one search per angle.** `search_corpus(query="anger Talmud one who tears garments idolatry", text_filter="bavli-shabbat")`,
   `search_corpus(query="anger as fallen middah inner work", text_filter="sefat-emet")`,
   `search_corpus(query="overcoming anger character refinement", text_filter="orchot-tzaddikim")`.
   Use `limit` to widen a thin angle. One pass per angle; don't loop the same query.
3. **Cross-reference via concepts.** Name the recurring concept:
   `search_concepts(query="anger ka'as")` → `get_concept(canonical_id="c_kaas")`.
   Then `get_concept_neighborhood(canonical_id="c_kaas", rel_types=["CONTRADICTS","DEVELOPS"])`
   to find where the sources disagree or build on each other — that's your tension map.
4. **Chase threads from key passages.** For a pivotal hit,
   `get_entities_in_passage(su_id="<su_id from the result>")` to see the people,
   places, and concepts it invokes, and run a follow-up `search_corpus` if a thread
   is worth pulling.
5. **Synthesize a source map.** Group the findings into clusters; name the
   tension(s) and any outlier; refer to every source by its citation. Keep the
   prose focused — you're a research librarian presenting a map, not a teacher
   delivering a lecture. Close by inviting refinement.

## Output format

A short cited synthesis: 2–4 named clusters, each with its key sources by
reference; an explicit tension or outlier if one emerged; a closing line inviting
the user to drill into a cluster. Source-forward and efficient — no padding, no
"great question," no re-explaining the topic from scratch.

## Worked example

**Request:** "What does the tradition say about anger?"

1. Angles: Talmudic law/aggadah, Hasidic inner work, Mussar character refinement.
2. `search_corpus(query="anger tears garments like idolatry", text_filter="bavli-shabbat")`
   → Shabbat 105b; plus Hasidic and Mussar passes (above).
3. `search_concepts(query="anger ka'as")` → `c_kaas`;
   `get_concept_neighborhood(canonical_id="c_kaas", rel_types=["CONTRADICTS"])`
   → tension between anger as forbidden vs. anger as occasionally warranted.
4. `get_entities_in_passage(su_id="su_shabbat_105b_anger")` → surfaces Rambam's
   middot framing; follow-up search confirms.

**Result (sketch):**

> Three clusters. **(1) Talmudic severity** — Shabbat 105b equates the angry
> person with an idolater. **(2) Mussar refinement** — Orchot Tzaddikim treats
> anger as a middah to be retrained, not merely suppressed. **(3) Hasidic inner
> work** — the Sefat Emet reads anger as a fallen energy to be elevated. The live
> tension: is *all* anger forbidden, or is there a warranted anger? — Rambam
> (Hilchot De'ot) carves a middle path. Want me to drill into the Rambam thread?

## Notes / limits

- Every source must earn its place; cite each by reference, not "the Gemara says."
- Don't fabricate sources or assert what the searches didn't return. If an angle
  comes up empty, say so and offer to rephrase.
- Surfaces and maps what sources say; not a posek, not a ruling.
- If a follow-up names a source already shown in this thread, engage with it —
  don't re-run the search.
