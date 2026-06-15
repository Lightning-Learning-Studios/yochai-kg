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

- `lookup_passage(reference)` — verify each detected citation and obtain its
  deep-link. Deterministic lookup by reference.

## Method

1. **Detect every citation.** Scan the essay for canonical Jewish references in
   all their forms: Tanakh (*"Genesis 22:2"*, *"Vayikra 19:18"*), Talmud
   (*"Sanhedrin 56a"*, *"Berakhot 2a:4"*), Mishnah (*"Pirkei Avot 3:14"*),
   commentaries (*"Rashi on Genesis 22:2"*, *"Ramban on Numbers 13:27"*), and
   codes (*"Mishneh Torah, Hilchot Teshuvah 3:5"*). Build a list of the exact
   reference strings as they appear.
2. **Verify each one.** For every detected reference, call
   `lookup_passage(reference="Sanhedrin 56a")`. A hit confirms the citation is
   real and gives you its deep-link. A miss means the citation does not cleanly
   resolve in the corpus.
3. **Resolve ambiguous references with one clarification.** If a reference is
   ambiguous (*"the Guide"*, *"the Rambam"* with no locus), don't guess. List the
   ambiguous items and ask the user to pick the canonical form (*"Guide for the
   Perplexed 3:13?"*) or to skip it. On their reply, run `lookup_passage` once
   more per resolved reference.
4. **Rewrite minimally.** Return the essay verbatim except that each *verified*
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
2. `lookup_passage(reference="Rashi on Genesis 22:2")` → hit, deep-link returned.
3. `lookup_passage(reference="Sanhedrin 56a")` → hit, deep-link returned.

**Result:**

> As Rashi notes on [Genesis 22:2](…), the command is deliberately ambiguous; the
> Gemara in [Sanhedrin 56a](…) counts the Noahide laws.

(If the essay had said *"as the Guide explains"*, you'd first ask: *"By 'the
Guide,' do you mean Guide for the Perplexed — and which part?"*)

## Notes / limits

- Never invent a link, slug, or anchor. If `lookup_passage` doesn't resolve a
  reference, leave it as plain text — don't fabricate a target.
- Never add or alter the essay's content. This skill links; it does not edit,
  improve, or fact-check the argument.
- A reference that comes from the right work but the user cited the wrong locus
  will still link to whatever `lookup_passage` returns for the string given —
  verify the locus, don't second-guess the author's intent silently.
