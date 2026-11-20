"""Output shapes for the open server's tools.

Each tool returns one of these models. The MCP library turns the model into the
tool's output schema and into structured content, which both the Claude and
ChatGPT directories ask for.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel as _PydanticModel
from pydantic import Field


class BaseModel(_PydanticModel):
    """Empty fields are left out of every response, which keeps answers short."""

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs: Any) -> str:
        kwargs.setdefault("exclude_none", True)
        return super().model_dump_json(**kwargs)


class Passage(BaseModel):
    reference: str = Field(description="Citation a person can read, for example 'Genesis 22:2' or 'Berakhot 2a'.")
    id: str | None = Field(None, description="Graph id of the passage. Pass it to other tools as a reference.")
    text_title: str | None = None
    author: str | None = None
    category: str | None = Field(None, description="Kind of text, for example tanakh, talmud_bavli, commentary.")
    era: str | None = None
    hebrew: str | None = Field(None, description="Original text, Hebrew or Aramaic.")
    english: str | None = None
    translation_source: str | None = Field(None, description="Where the English came from. Show it with the quote.")
    link: str | None = Field(None, description="Opens this passage in the Yochai reader.")
    relevance: float | None = Field(None, description="Search similarity from 0 to 1. Absent for exact lookups.")
    truncated: bool = Field(False, description="True when the text was cut to fit the length cap.")


class SearchPassagesResult(BaseModel):
    query: str
    text: str | None = Field(None, description="Title of the single text searched, when one was named.")
    count: int
    passages: list[Passage] = []
    message: str | None = None
    suggestions: list[str] = []


class PassageResult(BaseModel):
    found: bool
    reference: str
    text_title: str | None = None
    author: str | None = None
    category: str | None = None
    translation_source: str | None = Field(None, description="Where the English came from. Show it with the quote.")
    segments: list[Passage] = Field(default_factory=list, description="The verses or lines, in order.")
    link: str | None = None
    truncated: bool = False
    continue_from: str | None = Field(None, description="Reference to request next when the passage was cut.")
    message: str | None = None
    suggestions: list[str] = []


class CommentariesResult(BaseModel):
    found: bool
    reference: str
    count: int = 0
    commentators: list[str] = Field(default_factory=list, description="Every commentator available on this passage.")
    commentaries: list[Passage] = []
    message: str | None = None
    suggestions: list[str] = []


class CrossReference(BaseModel):
    kind: str = Field(description="Type of link, for example Midrash, Talmud, Halakhah, Tanakh.")
    reference: str
    id: str
    text_title: str | None = None
    excerpt: str | None = None
    link: str | None = None


class CrossReferencesResult(BaseModel):
    found: bool
    reference: str
    count: int = 0
    kinds_available: dict[str, int] = Field(default_factory=dict, description="How many links of each kind exist.")
    cross_references: list[CrossReference] = []
    message: str | None = None
    suggestions: list[str] = []


class TalmudMove(BaseModel):
    step: int | None = None
    move: str | None = Field(None, description="Role in the argument: question, answer, objection, proof and so on.")
    speaker: str | None = None
    layer: str | None = Field(None, description="Historical layer of the speaker, for example tannaitic or amoraic.")
    marker: str | None = Field(None, description="The Aramaic phrase that signals the move, with its meaning.")
    summary: str | None = None


class TalmudDiscussion(BaseModel):
    id: str
    reference: str | None = None
    kind: str | None = None
    driving_question: str | None = None
    conclusion: str | None = None
    conclusion_status: str | None = None
    moves: list[TalmudMove] = []
    link: str | None = None


class TalmudDiscussionResult(BaseModel):
    found: bool
    reference: str
    count: int = 0
    discussions: list[TalmudDiscussion] = []
    message: str | None = None
    suggestions: list[str] = []


class ConceptSummary(BaseModel):
    concept_id: str
    name: str | None = None
    hebrew_name: str | None = None
    definition: str | None = None
    difficulty: str | None = None
    keystone: bool | None = Field(None, description="True for an idea that many others build on.")
    relation: str | None = Field(None, description="How it relates to the concept asked about.")
    relevance: float | None = None


class SearchConceptsResult(BaseModel):
    query: str
    count: int
    concepts: list[ConceptSummary] = []
    message: str | None = None


class ConceptResult(BaseModel):
    found: bool
    concept_id: str
    name: str | None = None
    hebrew_name: str | None = None
    also_known_as: list[str] = []
    definition: str | None = None
    description: str | None = None
    guiding_question: str | None = None
    key_insight: str | None = None
    difficulty: str | None = None
    keystone: bool | None = None
    eras: list[str] = []
    traditions: list[str] = []
    related: list[ConceptSummary] = Field(default_factory=list, description="A few of the closest related concepts.")
    message: str | None = None


class RelatedConceptsResult(BaseModel):
    found: bool
    concept_id: str
    relation: str | None = None
    count: int = 0
    related: list[ConceptSummary] = []
    message: str | None = None


class LearningPathResult(BaseModel):
    found: bool
    concept_id: str
    name: str | None = None
    learn_first: list[ConceptSummary] = Field(default_factory=list, description="Concepts to study before this one.")
    leads_to: list[ConceptSummary] = Field(default_factory=list, description="Concepts this one opens up.")
    message: str | None = None


class ConceptSourcesResult(BaseModel):
    found: bool
    concept_id: str
    count: int = 0
    passages: list[Passage] = []
    message: str | None = None


class Theme(BaseModel):
    theme_id: str
    name: str | None = None
    hebrew_name: str | None = None
    question: str | None = None
    description: str | None = None
    size: int | None = Field(None, description="Number of items inside this theme.")


class BrowseThemesResult(BaseModel):
    found: bool = True
    level: str = Field(description="'top' for the 11 great themes, 'theme' for the groups inside one, 'group' for concepts.")
    theme: Theme | None = None
    themes: list[Theme] = []
    concepts: list[ConceptSummary] = []
    start_here: list[ConceptSummary] = Field(default_factory=list, description="Good first concepts in this group.")
    message: str | None = None


class TextEntry(BaseModel):
    title: str
    slug: str
    category: str | None = None
    author: str | None = None
    era: str | None = None


class ListTextsResult(BaseModel):
    count: int
    total_in_library: int
    categories: dict[str, int] = Field(default_factory=dict, description="Every category and how many texts it holds.")
    texts: list[TextEntry] = []
    message: str | None = None


class StudyStep(BaseModel):
    step: int
    idea: str | None = None
    summary: str | None = None
    kind: str | None = None
    quote: str | None = None
    quote_hebrew: str | None = None
    key_figures: list[str] = []


class StudyPathResult(BaseModel):
    found: bool
    text: str
    text_title: str | None = None
    total_steps: int = 0
    start: int = 1
    steps: list[StudyStep] = []
    link: str | None = None
    message: str | None = None
    suggestions: list[str] = []


class TorahPortion(BaseModel):
    name: str
    hebrew_name: str | None = None
    reference: str
    first_verse: str
    book: str
    double_portion: bool = False


class DafYomi(BaseModel):
    tractate: str
    page: int
    label: str
    cycle: int
    reference: str | None = Field(None, description="Pass this to get_passage. Absent when the tractate is not in the library.")
    in_library: bool


class Holiday(BaseModel):
    name: str
    date: str
    days_away: int
    begins: str


class CalendarResult(BaseModel):
    date: str
    weekday: str
    hebrew_date: str
    hebrew_date_hebrew: str
    israel: bool
    today: str | None = Field(None, description="Holiday or fast on this date, if any.")
    shabbat_date: str
    torah_portion: TorahPortion | None = None
    torah_portion_note: str | None = None
    daf_yomi: DafYomi
    upcoming_holidays: list[Holiday] = []
    note: str


class SkillEntry(BaseModel):
    name: str
    kind: str = Field(description="'core' ships with Yochai. 'community' was written by a named author and approved.")
    description: str
    author: str | None = None


class ListSkillsResult(BaseModel):
    count: int
    skills: list[SkillEntry] = []
    message: str | None = None


class LoadSkillResult(BaseModel):
    found: bool
    name: str
    kind: str | None = None
    author: str | None = None
    licence: str | None = None
    instructions: str | None = Field(None, description="The full text of the skill: a study method written for an assistant.")
    message: str | None = None
    suggestions: list[str] = []
