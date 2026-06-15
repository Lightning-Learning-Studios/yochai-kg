# Submission Schema

A submission is one YAML file describing one text. The fields below mirror the columns the catalog
generator (`apps/yochai/knowledge_graph_pipeline/generate_text_catalog.py`) actually reads when it
turns a `canonical_corpus.csv` row into a catalog entry, plus a `source` block telling us where to
get the text.

## Required fields

| Field | Required | Notes |
| --- | --- | --- |
| `text_slug` | ✅ | Lowercase, hyphenated, ASCII. Unique vs. `canonical_corpus.csv`. e.g. `ketzot-hachoshen`. |
| `english_title` | ✅ | Display title, e.g. `Ketzot HaChoshen`. |
| `original_title` | ✅ | Hebrew title, e.g. `קצות החושן`. |
| `section_id` | ✅ | **Constrained** — must be one of the values below. Drives library placement; an unknown value makes the generator hard-fail. |
| `genre` | ✅ | **Constrained** — must be one of the values below. |
| `era_key` / `era_display` | ✅ | Period, e.g. `acharonim` / `Acharonim`. |
| `description` | ✅ | 1–2 sentences on what the work is and why it matters. |
| `source` | ✅ | See **Source block** below — where the Hebrew + English come from. |

## Optional / structural fields

| Field | Notes |
| --- | --- |
| `author` | Author name (English). |
| `group_id` / `group` | Library grouping (e.g. `methodology_analytical_halakha` / its display name). Match an existing group when possible. |
| `spine_item` | Top-level navigation unit: one of `Chapter`, `Section`, `Siman`, `Daf`, `Parasha`, etc. (maps via `SPINE_TS_MAP`; defaults to `section`). |
| `frontend_navigation` | Human-readable nav path, e.g. `Siman > Se'if`. |
| `dependent_on` | Slug of the base text this comments on (commentaries set this so the base is ingested first). |
| `sort_order` | Integer ordering within its group. |
| `notes` | Anything the maintainers should know (provenance quirks, splits, etc.). |

## Valid `section_id` values (16)

The library is organized into these top-level sections. **Pick exactly one.** (Source of truth:
`CATEGORY_CONFIG` in `generate_text_catalog.py`.)

```
tanakh                         rabbinic_literature            talmud_commentaries
rishonim_tanakh_commentaries   halacha                        kabbalah
hasidut                        musar                          jewish_thought
responsa                       liturgy                        piyyut_and_poetry
targumim                       methodology_structure          second_temple_hellenistic
sephardic_mizrahi_heritage
```

## Valid `genre` values (17)

(Source of truth: `GENRE_TS_MAP` in `generate_text_catalog.py`.)

```
tanakh            mishnah           talmud_bavli      talmud_yerushalmi
tosefta           midrash_aggadah   midrash_halakha   commentary
halakhic_code     kabbalah          hasidut           mussar
philosophy        responsa          liturgy           poetry
targumim
```

## Source block

```yaml
source:
  hebrew:
    type: sefaria | url | upload          # how we get the Hebrew
    ref: "https://www.sefaria.org/..."    # Sefaria URL or source URL
    license: "CC-BY / public-domain / ..."
  english:
    type: sefaria | url | upload | none   # 'none' if Hebrew-only for now
    ref: "..."
    license: "..."
  provenance: "One line on where this edition comes from and its rights status."
```

- **Preferred:** `type: sefaria` with a Sefaria URL — these are already rights-cleared and slot
  straight into our build.
- `type: url` — a stable public URL to a clean source. State the license.
- `type: upload` — you'll attach the file in the PR. Only for rights-cleared / public-domain text.

## What we do NOT need from you

You do **not** hand-author the Lightning bilingual EPUB markup (the `data-canonical-id`,
`verse-en`/`verse-he`, `lightning-sentence`, `paragraph-unit` structure) or the
`*_semantic_units.json` files. Those are **produced by our build step** from your source. Submit the
metadata + source; we generate the rest.
