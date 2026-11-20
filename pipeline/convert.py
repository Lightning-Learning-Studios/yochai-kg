"""Turn a published Create method into a plugin SKILL.md.

The output depends only on the method version, so a second run over the same feed
writes the same bytes and makes no diff.
"""
from __future__ import annotations

import json
import re
import unicodedata

from . import PLUGIN_TOOLS
from .fetch import Method

MAX_SLUG = 48
MAX_DESCRIPTION = 600

# Tool names a Create method may use (Yochai app tools, and the older open-gateway
# names) mapped to the tool the plugin offers for the same job.
TOOL_MAP: dict[str, str] = {
    # Yochai app runtime tools
    "search_corpus": "search_passages",
    "batch_search_corpus": "search_passages",
    "lookup_canonical_text": "get_passage",
    "lookup_daf_text": "get_passage",
    "text_lookup": "get_passage",
    "resolve_citations": "get_passage",
    "lookup_commentary_passage": "get_commentaries",
    "get_hebrew_calendar": "get_jewish_calendar",
    # Older open-gateway names
    "lookup_passage": "get_passage",
    "get_commentaries_on": "get_commentaries",
    "get_connections": "get_cross_references",
    "get_talmudic_structure": "get_talmud_discussion",
    "get_concept_neighborhood": "get_related_concepts",
    "get_prerequisites": "get_learning_path",
    "list_galaxies": "browse_themes",
    "browse_constellation": "browse_themes",
    "get_corridors_for_text": "get_study_path",
    "get_corridor": "get_study_path",
}

# Yochai app tools that have no place in a chat plugin. The phrase replaces the name.
TOOL_PHRASES: dict[str, str] = {
    "navigate_user": "give the reader the passage link",
}

_TOOL_RE = re.compile(
    r"`?\b(" + "|".join(sorted(map(re.escape, [*TOOL_MAP, *TOOL_PHRASES]), key=len, reverse=True)) + r")\b`?"
)

_TOOL_NOTES = (
    "This skill runs with the Yochai tools only: "
    + ", ".join(f"`{t}`" for t in PLUGIN_TOOLS)
    + ".\n\n"
    "- Quote only the passages that a Yochai tool returned in this conversation.\n"
    "- Give the reference and the Yochai link for each passage you quote.\n"
    "- Say which translation a passage comes from when the tool gives that.\n"
    "- If the tools return nothing useful, say so and suggest a nearby question. Do not invent a source.\n"
    "- This is study help. It is not a religious ruling. For a ruling, the reader asks their own rabbi.\n"
)


def slugify(title: str) -> str:
    """ASCII, lower-case, dash-separated name, at most MAX_SLUG characters."""
    text = unicodedata.normalize("NFKD", title)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(text) > MAX_SLUG:
        text = text[:MAX_SLUG].rsplit("-", 1)[0] if "-" in text[:MAX_SLUG] else text[:MAX_SLUG]
    return text.strip("-")


def skill_slug(method: Method) -> str:
    """The folder and skill name. Falls back to the method id for a title with no Latin letters."""
    return slugify(method.title) or f"skill-{method.method_id[:8]}"


def map_tools(text: str) -> str:
    """Rewrite Yochai-app tool names to the plugin's tool names."""

    def _swap(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in TOOL_PHRASES:
            return TOOL_PHRASES[name]
        return f"`{TOOL_MAP[name]}`"

    return _TOOL_RE.sub(_swap, text)


def _clean(text: str) -> str:
    """Normalize newlines and trailing spaces so output is stable."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    out = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", out)


def _one_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_frontmatter(text: str) -> str:
    """An imported SKILL.md carries its own frontmatter. The plugin writes a new one."""
    if text.lstrip().startswith("---"):
        body = text.lstrip()[3:]
        end = body.find("\n---")
        if end != -1:
            return body[end + 4 :].lstrip("\n")
    return text


def _demote_headings(text: str) -> str:
    """Push headings down two levels so they sit under the '## Full instructions' heading."""
    out, in_code = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,4} ", line):
            line = "##" + line
        out.append(line)
    return "\n".join(out)


def description(method: Method) -> str:
    text = _one_line(method.outcome)
    if method.audience:
        text = f"{text} For: {_one_line(method.audience)}"
    text = f"{text} Community skill by {method.author}."
    if len(text) > MAX_DESCRIPTION:
        text = text[: MAX_DESCRIPTION - 1].rstrip() + "…"
    return text


def _yaml(value: str | int) -> str:
    """A YAML scalar. Strings use JSON double quotes, which YAML reads the same way."""
    if isinstance(value, int):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def frontmatter(method: Method, slug: str) -> str:
    fields: list[tuple[str, str | int]] = [
        ("name", slug),
        ("description", description(method)),
        ("author", method.author),
        ("license", method.plugin_license),
        ("category", method.category),
        ("source", "yochai-create"),
        ("source_method_id", method.method_id),
        ("source_version_id", method.version_id),
        ("source_revision", method.revision),
        ("approved", method.published_at[:10]),
    ]
    lines = [f"{key}: {value if key == 'name' else _yaml(value)}" for key, value in fields]
    return "---\n" + "\n".join(lines) + "\n---\n"


def to_skill_md(method: Method, slug: str | None = None) -> str:
    """Return the full SKILL.md text for one method."""
    slug = slug or skill_slug(method)
    parts: list[str] = [frontmatter(method, slug)]
    parts.append(f"# {_one_line(method.title)}\n")
    parts.append(
        f"*A community skill from Yochai Create, by {method.author}. "
        f"Licence: {method.plugin_license}. A Yochai reviewer approved it.*\n"
    )
    if method.audience:
        parts.append("## Who this is for\n\n" + map_tools(_clean(method.audience)) + "\n")
    parts.append("## What you get\n\n" + map_tools(_clean(method.outcome)) + "\n")
    if method.steps:
        steps = "\n".join(f"{i}. {map_tools(_one_line(step))}" for i, step in enumerate(method.steps, 1))
        parts.append("## Steps\n\n" + steps + "\n")
    if method.full_instructions:
        body = _demote_headings(_clean(_strip_frontmatter(method.full_instructions)))
        parts.append("## Full instructions\n\n" + map_tools(body) + "\n")
    parts.append("## Tools and rules\n\n" + _TOOL_NOTES)
    return "\n".join(parts)


def read_frontmatter(skill_md: str) -> dict[str, str]:
    """Read the simple `key: value` frontmatter this module writes."""
    if not skill_md.startswith("---\n"):
        return {}
    end = skill_md.find("\n---\n", 4)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for line in skill_md[4:end].split("\n"):
        key, sep, value = line.partition(": ")
        if not sep:
            continue
        value = value.strip()
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                pass
        out[key.strip()] = str(value)
    return out
