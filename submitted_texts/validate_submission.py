#!/usr/bin/env python3
"""Validate a Yochai corpus submission YAML before opening a PR.

Checks required fields, the constrained ``section_id`` / ``genre`` vocabularies (read live from
``generate_text_catalog.py`` so they never drift), slug format, slug uniqueness against
``canonical_corpus.csv``, and the source block.

Usage:
    python validate_submission.py <submission.yaml> [<submission2.yaml> ...]

Exits non-zero if any submission has errors. Warnings do not fail the run.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_ASSEMBLY = HERE.parent
GENERATOR = CORPUS_ASSEMBLY.parent / "knowledge_graph_pipeline" / "generate_text_catalog.py"
CANONICAL_CSV = CORPUS_ASSEMBLY / "canonical_corpus.csv"

REQUIRED = [
    "text_slug", "english_title", "original_title",
    "section_id", "genre", "era_key", "era_display", "description",
]
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Fallbacks if the generator can't be parsed (kept in sync with SUBMISSION_SCHEMA.md).
_FALLBACK_SECTIONS = {
    "tanakh", "rabbinic_literature", "talmud_commentaries", "rishonim_tanakh_commentaries",
    "halacha", "kabbalah", "hasidut", "musar", "jewish_thought", "responsa", "liturgy",
    "piyyut_and_poetry", "targumim", "methodology_structure", "second_temple_hellenistic",
    "sephardic_mizrahi_heritage",
}
_FALLBACK_GENRES = {
    "tanakh", "mishnah", "talmud_bavli", "talmud_yerushalmi", "tosefta", "midrash_aggadah",
    "midrash_halakha", "commentary", "halakhic_code", "kabbalah", "hasidut", "mussar",
    "philosophy", "responsa", "liturgy", "poetry", "targumim",
}


def _load_vocab():
    """Pull the valid section_ids and genres straight from the generator (source of truth)."""
    sections, genres = set(_FALLBACK_SECTIONS), set(_FALLBACK_GENRES)
    try:
        text = GENERATOR.read_text(encoding="utf-8")
        cfg = re.search(r"CATEGORY_CONFIG\s*=\s*OrderedDict\(\[(.*?)\]\)", text, re.S)
        if cfg:
            keys = re.findall(r"\(\s*['\"]([a-z_]+)['\"]", cfg.group(1))
            if keys:
                sections = set(keys)
        gmap = re.search(r"GENRE_TS_MAP\s*=\s*\{(.*?)\}", text, re.S)
        if gmap:
            keys = re.findall(r"['\"]([a-z_]+)['\"]\s*:", gmap.group(1))
            if keys:
                genres = set(keys)
    except OSError:
        pass
    return sections, genres


def _load_existing_slugs():
    slugs = set()
    try:
        import csv
        with CANONICAL_CSV.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("text_slug"):
                    slugs.add(row["text_slug"].strip())
    except OSError:
        pass
    return slugs


def validate(path: Path, sections, genres, existing) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        import yaml
    except ImportError:
        return (["PyYAML not installed — run: pip install pyyaml"], [])
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:  # noqa: BLE001
        return ([f"could not parse YAML: {e}"], [])
    if not isinstance(data, dict):
        return (["top-level YAML must be a mapping of fields"], [])

    for field in REQUIRED:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"missing required field: {field}")

    slug = (data.get("text_slug") or "").strip()
    if slug:
        if not SLUG_RE.match(slug):
            errors.append(f"text_slug '{slug}' must be lowercase-hyphenated-ascii (a-z, 0-9, '-')")
        if slug in existing:
            errors.append(f"text_slug '{slug}' already exists in canonical_corpus.csv")

    sec = (data.get("section_id") or "").strip()
    if sec and sec not in sections:
        errors.append(f"section_id '{sec}' is not valid. Allowed: {', '.join(sorted(sections))}")

    gen = (data.get("genre") or "").strip()
    if gen and gen not in genres:
        errors.append(f"genre '{gen}' is not valid. Allowed: {', '.join(sorted(genres))}")

    src = data.get("source")
    if not isinstance(src, dict):
        errors.append("missing 'source' block (see SUBMISSION_SCHEMA.md)")
    else:
        heb = src.get("hebrew") if isinstance(src.get("hebrew"), dict) else {}
        if not (heb.get("type") and heb.get("ref")):
            errors.append("source.hebrew must have both 'type' and 'ref'")
        if not heb.get("license"):
            warnings.append("source.hebrew.license is empty — state the rights status")
        if not src.get("provenance"):
            warnings.append("source.provenance is empty — one line on edition + rights helps review")

    dep = (data.get("dependent_on") or "").strip()
    if dep and existing and dep not in existing:
        warnings.append(f"dependent_on '{dep}' is not a known slug — confirm the base text exists")
    if not (data.get("author") or "").strip():
        warnings.append("author is empty (optional, but recommended)")

    return (errors, warnings)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    sections, genres = _load_vocab()
    existing = _load_existing_slugs()
    failed = 0
    for arg in argv[1:]:
        path = Path(arg)
        print(f"\n=== {path} ===")
        if not path.exists():
            print("  ✗ file not found")
            failed += 1
            continue
        errors, warnings = validate(path, sections, genres, existing)
        for w in warnings:
            print(f"  ⚠ {w}")
        for e in errors:
            print(f"  ✗ {e}")
        if errors:
            failed += 1
        else:
            print("  ✓ valid" + (f" ({len(warnings)} warning(s))" if warnings else ""))
    print()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
