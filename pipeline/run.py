"""Run the Create-to-plugin pipeline.

    python -m pipeline.run                         # read the live feed, write shelf/community/
    python -m pipeline.run --dry-run               # show what would change, write nothing
    python -m pipeline.run --fixture pipeline/fixtures/feed.json --out /tmp/shelf

For each published method the run prints one line:

    added     <slug>   a new skill was written
    updated   <slug>   a newer approved version replaced the old one
    unchanged <slug>   the shelf already has this version
    skipped   <slug>   not eligible, with the reason (for example: no author consent)
    failed    <slug>   the safety check blocked it, with the reasons
    removed   <slug>   it left the feed or lost consent, so the file was deleted

The run only changes files. A person reviews and merges the pull request.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import convert, fetch, safety

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "shelf" / "community"
SKILL_FILE = "SKILL.md"


@dataclass
class Result:
    status: str  # added | updated | unchanged | skipped | failed | removed
    slug: str
    title: str = ""
    method_id: str = ""
    reasons: list[str] = field(default_factory=list)
    report: str = ""

    def line(self) -> str:
        why = f" ({'; '.join(self.reasons)})" if self.reasons else ""
        title = f' "{self.title}"' if self.title else ""
        return f"{self.status:<9} {self.slug}{title}{why}"


def _existing(out_dir: Path) -> dict[str, tuple[str, str]]:
    """Map source method id to (slug, file text) for skills this pipeline wrote."""
    found: dict[str, tuple[str, str]] = {}
    if not out_dir.is_dir():
        return found
    for path in sorted(out_dir.glob(f"*/{SKILL_FILE}")):
        text = path.read_text(encoding="utf-8")
        meta = convert.read_frontmatter(text)
        if meta.get("source") == "yochai-create" and meta.get("source_method_id"):
            found[meta["source_method_id"]] = (path.parent.name, text)
    return found


def _pick_slug(method: fetch.Method, existing: dict[str, tuple[str, str]], taken: set[str]) -> str:
    """Keep the folder a method already has. Otherwise use the title, and add the
    start of the method id when another method already holds that name."""
    if method.method_id in existing:
        return existing[method.method_id][0]
    slug = convert.skill_slug(method)
    if slug in taken:
        slug = f"{slug[: convert.MAX_SLUG - 9]}-{method.method_id[:8]}".strip("-")
    return slug


def run(
    raw_methods: list[dict[str, Any]],
    out_dir: Path = DEFAULT_OUT,
    *,
    dry_run: bool = False,
    core_names: set[str] | None = None,
    review: bool = True,
) -> list[Result]:
    existing = _existing(out_dir)
    taken = {slug for slug, _ in existing.values()}
    if out_dir.is_dir():
        taken |= {p.name for p in out_dir.iterdir() if p.is_dir()}
    core = core_names if core_names is not None else safety.core_skill_names()
    results: list[Result] = []
    live_ids: set[str] = set()

    # Oldest first, so the earliest method keeps a contested name on every run.
    parsed = [(raw, fetch.parse_method(raw)) for raw in raw_methods]
    parsed.sort(key=lambda pair: (pair[1].published_at, pair[1].method_id))

    for raw, method in parsed:
        ok, reason = fetch.eligibility(raw, method)
        if not ok:
            slug = convert.slugify(method.title) or (method.method_id[:8] or "unknown")
            results.append(Result("skipped", slug, method.title, method.method_id, [reason]))
            continue

        slug = _pick_slug(method, existing, taken)
        taken.add(slug)
        text = convert.to_skill_md(method, slug)
        previous = existing.get(method.method_id, (slug, None))[1]

        if previous == text:
            live_ids.add(method.method_id)
            results.append(Result("unchanged", slug, method.title, method.method_id))
            continue

        findings = safety.check(method, slug, text, core_names=core)
        verdict: dict[str, Any] = {"status": "skipped", "model": None, "reasons": []}
        if not findings and review:
            verdict = safety.model_review(text)
        report = safety.report_markdown(method, slug, findings, verdict)

        if findings or verdict["status"] in {"fail", "error"}:
            reasons = [f.message for f in findings] or [f"model review: {r}" for r in verdict["reasons"]] or ["model review failed"]
            if previous is not None:
                # The approved older version stays on the shelf.
                live_ids.add(method.method_id)
                reasons.append("the earlier approved version stays on the shelf")
            results.append(Result("failed", slug, method.title, method.method_id, reasons, report))
            continue

        live_ids.add(method.method_id)
        if not dry_run:
            target = out_dir / slug
            target.mkdir(parents=True, exist_ok=True)
            (target / SKILL_FILE).write_text(text, encoding="utf-8")
        results.append(Result("added" if previous is None else "updated", slug, method.title, method.method_id, report=report))

    # A skill leaves the shelf when its method leaves the feed or loses consent.
    for method_id, (slug, _) in sorted(existing.items(), key=lambda item: item[1][0]):
        if method_id in live_ids:
            continue
        if not dry_run:
            path = out_dir / slug / SKILL_FILE
            path.unlink(missing_ok=True)
            try:
                path.parent.rmdir()
            except OSError:
                pass
        results.append(Result("removed", slug, "", method_id, ["it is no longer published with consent in Yochai Create"],
                              report=f"### Removal of `{slug}`\n\nThe Create method `{method_id}` is no longer in the public feed with author consent. This pull request removes the skill from the shelf.\n"))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Turn published Yochai Create methods into plugin shelf skills.")
    parser.add_argument("--fixture", help="Read this saved feed file in place of the live feed.")
    parser.add_argument("--api-url", help="Base address of the Yochai service. Default: the YOCHAI_API_URL variable.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Folder to write skills to. Default: shelf/community/.")
    parser.add_argument("--dry-run", action="store_true", help="Show the result. Write and delete nothing.")
    parser.add_argument("--no-model-review", action="store_true", help="Run the fixed rules only.")
    parser.add_argument("--report", help="Also write the full result as JSON to this file.")
    args = parser.parse_args(argv)

    try:
        raw = fetch.load_fixture(args.fixture) if args.fixture else fetch.fetch_feed(args.api_url)
    except fetch.FeedError as exc:
        # Stop here. An unreadable feed must never look like "every skill was unpublished".
        print(f"error: {exc}", file=sys.stderr)
        return 2

    results = run(raw, Path(args.out), dry_run=args.dry_run, review=not args.no_model_review)

    print(f"Create-to-plugin pipeline{' (dry run, nothing written)' if args.dry_run else ''}: {len(raw)} published method(s) in the feed")
    for result in results:
        print(result.line())
    counts = {s: sum(r.status == s for r in results) for s in ("added", "updated", "unchanged", "skipped", "failed", "removed")}
    print("totals: " + ", ".join(f"{n} {s}" for s, n in counts.items()))

    if args.report:
        Path(args.report).write_text(
            json.dumps({"dry_run": args.dry_run, "totals": counts, "results": [asdict(r) for r in results]}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
