"""The skill shelf: study skills the open server can hand to any assistant.

Two folders feed it:
  plugin/skills/<name>/SKILL.md      the core skills that ship in the plugin
  shelf/community/<name>/SKILL.md    skills approved through Yochai Create

A community skill reaches the shelf only through a merged pull request, so
every skill here has passed review. Folders whose name starts with an
underscore (for example shelf/_held) are never served.
"""
from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("yochai.open")

ROOT = Path(__file__).resolve().parent.parent
SOURCES: tuple[tuple[str, Path], ...] = (
    ("core", ROOT / "plugin" / "skills"),
    ("community", ROOT / "shelf" / "community"),
)
MAX_BYTES = 60_000
_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class Skill:
    name: str
    kind: str            # "core" or "community"
    description: str
    author: str
    licence: str
    body: str


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Read the small YAML subset that SKILL.md files use: `key: value` lines,
    with indented or `>`/`|` continuation lines folded into the value."""
    m = _FRONT.match(text)
    if not m:
        return {}, text
    meta: dict[str, str] = {}
    key: str | None = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            key = top.group(1).strip().lower()
            value = top.group(2).strip()
            meta[key] = "" if value in (">", "|", ">-", "|-") else value.strip("\"'")
        elif key:
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, m.group(2)


def load_all(sources: tuple[tuple[str, Path], ...] = SOURCES) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for kind, folder in sources:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*/SKILL.md")):
            if path.parent.name.startswith(("_", ".")):
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError as e:
                log.warning("skill unreadable: %s (%s)", path, e)
                continue
            if len(raw.encode("utf-8")) > MAX_BYTES:
                log.warning("skill skipped, larger than %d bytes: %s", MAX_BYTES, path)
                continue
            meta, body = parse_frontmatter(raw)
            name = (meta.get("name") or path.parent.name).strip().lower()
            if not body.strip() or name in skills:
                continue   # core skills win a name clash; empty files are ignored
            skills[name] = Skill(
                name=name,
                kind=kind,
                description=meta.get("description", "").strip(),
                author=meta.get("author", "Yochai" if kind == "core" else "").strip(),
                licence=(meta.get("license") or meta.get("licence") or "").strip(),
                body=body.strip(),
            )
    return skills


def find(skills: dict[str, Skill], name: str) -> tuple[Skill | None, list[str]]:
    """Exact name first, then a forgiving match. Returns (skill, suggestions)."""
    key = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    if key in skills:
        return skills[key], []
    close = difflib.get_close_matches(key, list(skills), n=3, cutoff=0.6)
    if len(close) == 1 or (close and difflib.SequenceMatcher(None, key, close[0]).ratio() > 0.85):
        return skills[close[0]], []
    return None, close
