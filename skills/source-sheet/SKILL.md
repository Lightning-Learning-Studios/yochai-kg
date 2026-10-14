# Source Sheet

## Purpose

Assemble a curated source sheet on a topic: 4–8 primary sources across eras,
ordered to build an arc (tension → revelation → progression), each with a framing
note and discussion questions. A teaching artifact, not a source dump.

## When to use

- The user wants a handout of primary texts for a shiur, class, Shabbat table, or
  self-study session on a named topic or question.
- **Not for:** a written essay (use **dvar-torah**) or open-ended discovery
  (use **research**).

## MCP tools used

- `lookup_passage(reference)` — pull the canonical anchor exactly (deterministic).
  Takes a slug-style canonical id, not a human citation — see *Referencing passages*
  in the [skills README](../README.md).
- `search_corpus(query, text_filter?, limit?)` — find thematic sources by role.
- `get_commentaries_on(reference, limit?)` — surface classical readings on the anchor.
  Takes a base slug (`bavli-berakhot`) or canonical id.
- `get_connections(reference, kinds?)` — the Sefaria citation graph on the anchor:
  midrash, targum, quoting-commentary, cross-Tanakh links. Finds the counter-voice
  and applied slots that a thematic search misses.

## Method

Curate by **role**, not by topic alone. Decide what job each source does in the
arc before you search; the search strategy follows the plan, not the reverse.

1. **Plan the roles (in your reasoning).** A 4-source sheet is the default:
   - **Source 1 — foundational text.** The canonical anchor (Tanakh, a primary
     sugya, a named Mishneh Torah section).
   - **Source 2 — the dominant classical reading.** The "of course" voice.
   - **Source 3 — a counter-voice or expansion.** Productive tension, not just more.
   - **Source 4 — an applied / contemporary thread.** Mussar, Hasidut, halakhic
     application — lands the arc.
2. **Anchor Source 1 deterministically.** Canonical citation is deterministic, so
   use exact lookup, not similarity search — but `lookup_passage` takes a canonical
   id, not a citation. Resolve the slug first, then build `<slug>_<chapter>_<verse>`:
   `lookup_passage(reference="bereishit_22_1")`. Ids carry no ranges, so for a span
   pull the opening verse and cite the range in the header.
3. **Mine the anchor's connection graph.** Before searching thematically, call
   `get_connections(reference="bereishit_22_1")` — the Sefaria graph already links
   the midrashim, targumim, and commentaries that cite this verse, and a passage
   that *quotes your anchor* is a stronger sheet entry than one that merely shares
   a theme. Filter with `kinds` when you want one genre.

   Coverage is partial — roughly a quarter of text units carry connections — so a
   `count: 0` means "not linked," not "nothing exists." Fall through to step 4 when
   that happens; don't retry the same reference.
4. **Fill the remaining roles with role-targeted search.** One query per role,
   each with a `text_filter` matching the role's expected genre when you have one:
   `search_corpus(query="Akedah why God tested Abraham", text_filter="rashi-on-genesis")`
   (classical), `text_filter="ramban-on-genesis"` (counter-voice),
   `text_filter="mesillat-yesharim"` (applied). Generic queries return only the
   most-discussed passage; targeted queries get you genre diversity.
5. **Verify each retrieval.** The returned text must contain the *specific*
   teaching the role names — not merely come from the right work or page. Rashi on
   Lev 19:18 about *"the great principle of the Torah"* is right; Rashi on the
   same verse about *lo tikom* is a miss. Re-query once with the teaching named
   (`"ואהבת לרעך כלל גדול"`); if it still misses, omit.
6. **Order and frame.** Sequence the sources into the arc. Add a 1–2 sentence
   framing note per source (what to *notice*, not what to think), discussion
   questions between sources, and a closing provocation.

### Retry budget

2 attempts per role. If both miss, OMIT that role and disclose by name:
*"I'd have included a Seforno here, but it isn't cleanly indexed — want me to swap
in another applied source?"* A clean 3-source sheet beats a 4-source sheet with a
mislabeled passage. Mislabeling is worse than omission.

## Output format

An ordered list. Per source: **header** (Work — reference), the bilingual
passage (from the tool result), and a **framing note**. Interleave discussion
questions. Open with a short introduction, close with a carry-forward question.

## Worked example

**Request:** "Four sources on teshuvah, for an adult-ed class."

1. `lookup_passage(reference="devarim_30_1")` → *"When all these things befall
   you—the blessing and the curse…"*, the foundational return-to-God. (Cite the span
   as Deuteronomy 30:1-10 in the header; the id resolves only the opening verse.)
2. `get_connections(reference="devarim_30_1")` → `count: 0`; this verse isn't in the
   connection layer, so fall through to targeted search for the classical slot:
   `search_corpus(query="return to God repentance restoration", text_filter="ramban-on-deuteronomy")`.
3. `search_corpus(query="teshuvah transforms deliberate sins into merits", text_filter="bavli-yoma")`
   → Yoma 86b on the power of return.
4. `search_corpus(query="teshuvah daily inner work returning to self", text_filter="sefat-emet")`
   → a Hasidic applied thread.

**Result (sketch):**

> **Introduction:** Teshuvah is both an event and a practice. These four sources
> move from the promise, to the mechanics, to the transformation, to the daily work.
> **Source 1 — Deuteronomy 30:1-10.** *Notice:* return is framed as something
> "not far off." … **Q after Source 2:** What does Rambam require beyond regret?

## Notes / limits

- Build only from indexed primary texts. If a requested source isn't in the
  corpus, say so and offer an indexed substitute by genre — never silently skip it.
- Every source must be backed by a tool-returned passage. No phantom sources.
- A correction to one slot is not a re-curation: re-search only the named slot;
  keep the others as they were.
- Surfaces what sources say; not a posek.
