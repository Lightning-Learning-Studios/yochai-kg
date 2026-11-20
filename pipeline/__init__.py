"""Create-to-plugin pipeline.

Turns an approved, published Yochai Create method into a skill on the plugin's
live shelf (`shelf/community/<slug>/SKILL.md`). Four gates protect the shelf:

1. A Yochai reviewer approved the method (it is in the public feed).
2. The author gave consent to publish it in the open plugin.
3. The automated safety check passed (`pipeline.safety`).
4. A person merged the pull request.

This package covers gates 1 to 3 and prepares the pull request for gate 4.
It never merges anything.
"""

# The tools the open plugin server offers. A community skill may name only these.
PLUGIN_TOOLS: tuple[str, ...] = (
    "search_passages",
    "get_passage",
    "get_commentaries",
    "get_cross_references",
    "get_talmud_discussion",
    "search_concepts",
    "get_concept",
    "get_related_concepts",
    "get_learning_path",
    "get_concept_sources",
    "browse_themes",
    "list_texts",
    "get_study_path",
    "get_jewish_calendar",
)

# The shelf's own two tools. A skill may mention them, but does not need them.
SHELF_TOOLS: tuple[str, ...] = ("list_skills", "load_skill")

# Names the core skills use. A community skill must not take one of them.
# `pipeline.safety.core_skill_names()` adds every folder it finds under
# `plugin/skills/` and `shelf/core/`, so this list is only the floor.
CORE_SKILL_NAMES: frozenset[str] = frozenset(
    {
        "find-a-source",
        "weekly-portion",
        "explain-this-passage",
        "prepare-to-teach",
        "practical-law",
        "holiday-prep",
        "study-partner",
        "build-a-course",
        "cite",
        "dvar-torah",
        "outline",
        "research",
        "source-sheet",
    }
)

DEFAULT_LICENSE = "CC BY 4.0"
ALLOWED_LICENSES: frozenset[str] = frozenset({"CC BY 4.0", "CC BY-SA 4.0", "CC0 1.0"})
