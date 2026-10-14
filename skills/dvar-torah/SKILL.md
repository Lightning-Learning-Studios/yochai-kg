# Dvar Torah

## Purpose

Compose a short Jewish teaching essay (a *dvar torah*) on a parasha, topic, or
verse: a real textual problem, illuminated through cited sources, landing on an
insight with relevance beyond the text. 600–1200 words by default; one central
problem, one insight, one landing.

## When to use

- The user wants a written teaching — a dvar torah, a short shiur in prose, a
  table teaching for Shabbat — on a named parasha, sugya, verse, or theme.
- **Not for:** assembling a sources-only handout (use **source-sheet**), or
  open-ended source discovery (use **research**).

## MCP tools used

- `search_corpus(query, text_filter?, limit?)` — find the core text and surface
  midrash/commentary thematically.
- `lookup_passage(reference)` — pull the anchor verse or sugya exactly. Takes a
  slug-style canonical id, not a human citation — see *Referencing passages* in the
  [skills README](../README.md).
- `get_commentaries_on(reference, limit?)` — gather the traditional voices. Takes a
  base slug (`bavli-berakhot`) or canonical id, not `"Genesis 22:2"`.
- `get_talmudic_structure(reference)` — when the anchor is a sugya: its driving
  question, its `maskana`, and the ordered dialectical moves. The textual problem a
  dvar needs is often already named there.
- `search_concepts` / `get_concept_neighborhood` — find a productive tension or
  development to drive the dvar.

## Method

A good dvar identifies a real textual problem and uses it to illuminate something
larger. The problem must be real, not invented; the relevance must be earned, not
imposed. Work in three stages — **outline → source-step → build** — and only
attribute an idea to a named source when a retrieved passage supports it.

1. **Anchor the core text.** Pull the verse or sugya exactly so you quote it
   honestly. Resolve the citation to a canonical id first —
   `lookup_passage(reference="bereishit_22_2")`, not `"Genesis 22:2"`, which returns
   `found: false`. Read what's actually there; name the textual problem precisely
   (an odd word, a doubling, a gap, a contradiction).

   If the anchor is a Talmudic passage, call
   `get_talmudic_structure(reference="bavli-berakhot_5_1")` as well: it returns the
   sugya's `driving_question` and `maskana` outright, which saves you reconstructing
   the problem from the surface of the text.
2. **Outline the move (in your reasoning, not the essay).** Decide the path:
   a difficulty the commentaries skip; a rishonim dialectic; a pshat→derash arc;
   or a perennial human problem the text lights up. The outline tells you which
   sources you need before you search.
3. **Gather the traditional voices.** For a Talmudic anchor,
   `get_commentaries_on(reference="bavli-berakhot")` works directly. For a Torah
   anchor it returns `count: 0` — go through the commentary text instead:
   `lookup_passage(reference="rashi-on-genesis_22_2_1")` for the exact comment
   (note the fourth id segment), or
   `search_corpus(query="…", text_filter="ramban-on-genesis")` for a thematic pull.
   See *Getting commentary on a Torah verse* in the [skills README](../README.md). Then one targeted
   `search_corpus(query="Akedah test why God commanded sacrifice", text_filter="ramban-on-genesis")`
   per role you still need (a counter-voice, a midrash, a Hasidic expansion).
4. **Find the tension to explore.** `search_concepts(query="trial of faith")` →
   `get_concept_neighborhood(canonical_id="<id>", rel_types=["DEVELOPS","CONTRADICTS"])`
   to surface a development or a contradiction the dvar can turn on.
5. **Build and synthesize.** Write flowing prose: an opening hook (a concrete
   scene), the textual problem, the argument tracked through sources (each
   introduced where the argument needs it, by its proper reference), and a
   landing that opens rather than ties off. Quote the anchor verse with a short
   transliteration + your own translation.

### Retry budget

2 search attempts per source-role. If both miss, omit and disclose by name:
*"I'd have brought in a Berditchever reading here, but it isn't cleanly indexed —
want me to swap in something else?"* Don't loop.

## Output format

Flowing prose, not a bulleted handout. Inline every source by its proper
reference. Shape: **hook → textual problem → argument-through-sources → landing.**
3–5 cited sources is typical. Don't pad; don't end with "and so we see…".

## Worked example

**Request:** "A six-minute dvar on Korach for a shul crowd."

1. `lookup_passage(reference="bamidbar_16_3")` → Korach's challenge: *"all the
   congregation are holy."* (Ids carry no ranges; pull 16:1 and 16:2 separately if
   you need the full opening.)
2. Korach is a Torah anchor, so skip `get_commentaries_on` and pull the commentary
   text directly: `search_corpus(query="Korach lineage motive rebellion",
   text_filter="rashi-on-numbers")` → Rashi on Korach's lineage and motive.
3. `search_concepts(query="dissent and authority")` →
   `get_concept_neighborhood(canonical_id="c_dissent", rel_types=["CONTRADICTS"])`
   → a tension between legitimate critique and self-serving rebellion.
4. `search_corpus(query="Korach holiness everyone equal challenge Moshe", text_filter="midrash-tanchuma")`
   → a midrash sharpening the demagogue's half-truth.

**Result (sketch):**

> Korach says something true — *"all the congregation are holy"* (Numbers
> 16:3) — to argue for something false. Rashi notices he was a clever man; the
> question is how a true premise becomes a rebellion. … The text leaves us not
> with an answer about hierarchy but with a sharper unease about the slogans we
> half-believe.

## Notes / limits

- Never fabricate a source. If `get_commentaries_on` or `search_corpus` doesn't
  return it, say so in prose and swap or omit.
- Don't attribute a reconstructed idea to a named rebbe or commentator unless a
  retrieved passage supports that exact claim. If it's stylistically in a
  tradition but not text-backed, phrase it without attribution
  (*"a Hasidic-style reading would say…"*).
- Surfaces what sources say; not a posek, not a ruling.
- Current request overrides cached context: if asked for Korach, don't reuse
  sources from last week's parasha.
