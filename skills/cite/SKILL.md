# Cite

## Purpose

Given an essay or draft, detect every Jewish source citation in it, verify each
against the corpus, and return the essay with each verified reference turned into a
hyperlink to the source. The job is narrow and mechanical: link what's real, leave
the rest as plain text.

## When to use

- The user pastes an essay, dvar torah, or article and wants its citations
  hyperlinked and verified.
- **Not for:** writing new prose (use **dvar-torah**) or finding new sources
  (use **research**). This skill adds *zero* new content.

## MCP tools used

- `run_cypher(query)` / `list_texts(genre?)` — resolve a work's name to its `text_slug`,
  the first half of a canonical id. `list_texts` browses by genre; `run_cypher` finds a
  specific work by title.
- `lookup_passage(reference)` — verify a citation by its canonical id and obtain its
  deep-link. Deterministic lookup; see *Referencing passages* in the skills README.
- `search_corpus(query, text_filter?)` — fall back here when a citation can't be
  resolved to an id by hand; the result carries the real `anchor` and deep-link.

## Method

1. **Detect every citation.** Scan the essay for canonical Jewish references in
   all their forms: Tanakh (*"Genesis 22:2"*, *"Vayikra 19:18"*), Talmud
   (*"Sanhedrin 56a"*, *"Berakhot 2a:4"*), Mishnah (*"Pirkei Avot 3:14"*),
   commentaries (*"Rashi on Genesis 22:2"*, *"Ramban on Numbers 13:27"*), and
   codes (*"Mishneh Torah, Hilchot Teshuvah 3:5"*). Build a list of the exact
   reference strings as they appear.
2. **Resolve each one to a canonical id.** `lookup_passage` does not accept
   human-readable citations — `lookup_passage(reference="Genesis 22:2")` returns
   `found: false`. Translate the citation into `<text_slug>_<chapter>_<verse>`:
   find the slug, then build the id. `list_texts` is clamped to 25 results, so for a
   specific work use `run_cypher(query="MATCH (t:Text) WHERE toLower(t.title) CONTAINS
   'rashi on genesis' RETURN t.slug")`. *"Genesis 22:2"* → slug `bereishit` →
   `bereishit_22_2`.
3. **Verify each one.** Call `lookup_passage(reference="bereishit_22_2")`. A hit
   returns `found: true` with the bilingual text and deep-link — read it and confirm
   it is the verse the author meant. A miss means the citation does not cleanly
   resolve; try `search_corpus(query="<the quoted words>", text_filter="<slug>")`
   once and take the `anchor` from the result. If that also misses, treat it as
   unresolved.

   Four traps: canonical ids carry no ranges (`bereishit_22_1-19` fails — resolve
   the opening verse and cite the span in prose); Talmud chapter numbers are not
   daf/amud, so never convert *"Sanhedrin 56a"* arithmetically — search for the
   passage and take its id; commentary ids carry a fourth segment
   (`rashi-on-genesis_22_2_1`, not `rashi-on-genesis_22_2`); and a slug that resolves
   is not proof you got the right locus, so read the returned text.
4. **Resolve ambiguous references with one clarification.** If a reference is
   ambiguous (*"the Guide"*, *"the Rambam"* with no locus), don't guess. List the
   ambiguous items and ask the user to pick the canonical form (*"Guide for the
   Perplexed 3:13?"*) or to skip it. On their reply, run `lookup_passage` once
   more per resolved reference.
5. **Rewrite minimally.** Return the essay verbatim except that each *verified*
   reference becomes a link to its passage. Leave unresolved references as plain
   text. Change nothing else — no new prose, no intro, no outro, no commentary.

## Output format

The user's essay, unchanged, with each verified citation hyperlinked inline to its
deep-link. No preamble ("Here's your essay…"), no summary ("Sources linked!"). If
any references were ambiguous, list them once for disambiguation before linking.

## Worked example

**Request:** *"As Rashi notes on Genesis 22:2, the command is deliberately
ambiguous; the Gemara in Sanhedrin 56a counts the Noahide laws."* — (paste, link
the sources)

1. Detect: `Rashi on Genesis 22:2`, `Sanhedrin 56a`.
2. Resolve the Rashi: slug `rashi-on-genesis`, and a commentary id carries a
   comment number — `lookup_passage(reference="rashi-on-genesis_22_2_1")` →
   `found: true`, returning *"קח נא TAKE NOW — The word נא is used as a request…"*.
   (`rashi-on-genesis_22_2`, without the `_1`, returns `found: false`.)
3. `Sanhedrin 56a` is a daf reference, and daf is not the chapter number, so don't
   build the id by arithmetic.
   `search_corpus(query="Noahide laws seven commandments", text_filter="bavli-sanhedrin")`
   → returns `anchor: bavli-sanhedrin_112_23`, labelled *"Sanhedrin, Daf 56b-57a"*.
   Take that anchor; `bavli-sanhedrin_56_1` is a different passage entirely.

**Result:**

> As Rashi notes on [Genesis 22:2](…), the command is deliberately ambiguous; the
> Gemara in [Sanhedrin 56a](…) counts the Noahide laws.

(If the essay had said *"as the Guide explains"*, you'd first ask: *"By 'the
Guide,' do you mean Guide for the Perplexed — and which part?"*)

## Notes / limits

- Never invent a link, slug, or anchor. If `lookup_passage` doesn't resolve a
  reference, leave it as plain text — don't fabricate a target. In particular,
  don't invent a plausible-looking canonical id: a guessed slug that happens to
  resolve points at the wrong passage, which is worse than no link.
- Never add or alter the essay's content. This skill links; it does not edit,
  improve, or fact-check the argument.
- A reference that comes from the right work but the user cited the wrong locus
  will still link to whatever the canonical id you built resolves to — verify the
  locus against the returned text, don't second-guess the author's intent silently.
