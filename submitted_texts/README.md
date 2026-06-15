# Submitted Texts — Community Corpus Intake

This folder is how anyone can **propose a new text for the Yochai knowledge graph** by opening a
pull request. You don't run the pipeline — you submit a small, structured description of the text
and a pointer to its source. The Yochai team reviews each submission and either accepts it (and
rolls it up through the construction pipeline) or declines it, with a reason.

> **You are proposing a text, not building graph data.** The 15-phase pipeline
> (`apps/yochai/knowledge_graph_pipeline/`) does the heavy lifting — EPUB parsing, entity
> extraction, embedding, relationship discovery, corridors, canonical concepts. Your job is to give
> us a clean, rights-cleared bilingual source and the catalog metadata so we can feed it in.

## What we're looking for

See **[WANTED.md](./WANTED.md)** for the live gap list (auto-derived from `canonical_corpus.csv`
vs. the loaded graph). It has three buckets:

1. **Ready-to-pull (37)** — texts with a known Sefaria source that simply haven't been built yet.
   If you want to help, flagging interest in these is the fastest path to a win; 24 of them have a
   sibling already in the graph, so the format is proven.
2. **Need-a-source (134)** — texts with **no Sefaria source**. This is where submissions matter
   most: a clean bilingual source you can point us to (with provenance and licensing) unblocks a
   text we otherwise can't add.
3. **Not work items (6)** — parent aggregate rows whose children are loaded individually. Listed so
   you don't submit them by mistake.

## Two ways to help

The WANTED texts **already have a row** in `canonical_corpus.csv` — they're catalogued but not yet
built into the graph. So there are two distinct contribution paths:

- **Path A — supply a source for a WANTED text.** These don't need a new submission file (a row
  already exists). Open a PR or issue pointing us at a clean, rights-cleared source for a
  `NOT_FOUND` text, or flag that you want to help build a `MATCHED` one. We add the source to the
  existing row and build it.
- **Path B — propose a brand-new text** not in the catalog at all. Use the `submission.yaml` flow
  below. The validator will reject a slug that already exists — that's the signal you're looking at
  a Path A text, not a Path B one.

Either way, the text should fit the corpus (serious Jewish textual tradition) and clear the
requirements below.

## How to submit (Path B — new text)

1. **Copy the template.** Duplicate [`_template/submission.yaml`](./_template/submission.yaml) to
   `submitted_texts/<your-text-slug>.yaml` (one file per text).
2. **Fill it in.** Every field is documented in
   [SUBMISSION_SCHEMA.md](./SUBMISSION_SCHEMA.md). The `section_id` and `genre` values are
   **constrained** — using an unrecognized value will make the catalog generator fail, so the
   validator checks them.
3. **Validate locally** (optional but appreciated):
   ```bash
   python apps/yochai/corpus_assembly/submitted_texts/validate_submission.py \
     apps/yochai/corpus_assembly/submitted_texts/<your-text-slug>.yaml
   ```
4. **Open a PR.** Title it `corpus: submit <english title>`. The PR body should state where the
   source comes from and confirm it's permissible to use (see Licensing below).

## What happens after you submit

```
PR opened  →  validator + maintainer review  →  ACCEPTED                         →  DECLINED
                                                 │                                   │
                                                 ├─ row appended to                  └─ PR closed with a
                                                 │  canonical_corpus.csv                 reason (source quality,
                                                 ├─ source built into a                  licensing, scope, duplicate)
                                                 │  Lightning bilingual EPUB
                                                 ├─ run through phases 1→15
                                                 │  (parse → extract → embed →
                                                 │  relationships → corridors →
                                                 │  canonical concepts → DAG)
                                                 └─ appears in the live graph,
                                                    reader, and chat retrieval
```

Acceptance is at the maintainers' discretion. Being on WANTED.md makes acceptance likely; off-list
texts are judged on fit, source quality, and licensing.

## Licensing & provenance (read this)

We can only ingest text we're permitted to use. For every submission:

- **Public-domain / freely-licensed sources are strongly preferred** (e.g. Sefaria's CC-licensed
  texts, public-domain translations). State the license explicitly.
- If the source is a modern copyrighted translation, **we will likely decline** unless you can show
  it's permissibly licensed.
- Always cite where the Hebrew and the English each come from — they're often different sources.

When in doubt, point us at a Sefaria URL; if it's not on Sefaria, describe the source and its rights
status in the PR.

## Conventions

- **Slugs** are lowercase, hyphen-separated, ASCII transliteration (`ben-ish-chai`,
  `ketzot-hachoshen`). They must be unique against `canonical_corpus.csv`.
- **Commentaries / dependent works** set `dependent_on` to the base text's slug so the pipeline
  orders them correctly (base text is ingested first).
- **Multi-section works** (e.g. a commentary spanning all four sections of the Shulchan Aruch) are
  submitted as **one file per section** (`taz-orach-chayim`, `taz-yoreh-deah`, …), not as a single
  combined work — that's how the corpus is structured.

Questions? Open a discussion or ping the Yochai team in your PR.
