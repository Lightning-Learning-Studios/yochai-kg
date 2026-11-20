"""Turn a reference a person would type into graph ids.

"Genesis 22:2", "Berakhot 2a", "Pirkei Avot 1:14", "Rashi on Genesis 22:2" and
the slug form "bereishit_22_2" all resolve here. The module is pure: it takes a
catalog (the list of texts in the graph) and returns a ParsedRef. It never
touches the database, so every rule is unit-testable offline.

Graph id shapes (TextUnit.canonical_id):
  verse texts        <slug>_<chapter>_<verse>            bereishit_22_2
  commentaries       <slug>_<chapter>_<verse>_<comment>  rashi-on-genesis_22_2_1
  Babylonian Talmud  <slug>_<page index>_<line>          bavli-berakhot_3_1
The Talmud page index counts sides from 1: 2a is 3, 2b is 4, so
index = 2 * daf - 1 for side a and 2 * daf for side b.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

# --- aliases -----------------------------------------------------------------
# English and common transliterated names for the Tanakh slugs in the graph.
_TANAKH: dict[str, tuple[str, ...]] = {
    "bereishit": ("genesis", "gen", "bereshit", "beresheet", "bereshis", "bereishis"),
    "shemot": ("exodus", "exod", "ex", "shmot", "shmos", "shemos"),
    "vayikra": ("leviticus", "lev"),
    "bamidbar": ("numbers", "num", "bemidbar"),
    "devarim": ("deuteronomy", "deut", "dvarim", "devorim"),
    "yehoshua": ("joshua", "josh"),
    "shoftim": ("judges", "shofetim"),
    "shmuel-i": ("1-samuel", "i-samuel", "first-samuel", "samuel-i", "samuel-1", "shmuel-1", "shmuel-aleph", "1-sam"),
    "shmuel-ii": ("2-samuel", "ii-samuel", "second-samuel", "samuel-ii", "samuel-2", "shmuel-2", "shmuel-bet", "2-sam"),
    "melachim-i": ("1-kings", "i-kings", "first-kings", "kings-i", "kings-1", "melachim-1", "melakhim-i", "melakhim-1"),
    "melachim-ii": ("2-kings", "ii-kings", "second-kings", "kings-ii", "kings-2", "melachim-2", "melakhim-ii", "melakhim-2"),
    "yeshayahu": ("isaiah", "isa", "yeshaya", "yeshayah"),
    "yirmiyahu": ("jeremiah", "jer", "yirmiya"),
    "yechezkel": ("ezekiel", "ezek", "yehezkel"),
    "hoshea": ("hosea",),
    "yoel": ("joel",),
    "amos": (),
    "ovadia": ("obadiah", "ovadya"),
    "yonah": ("jonah", "yona"),
    "micha": ("micah", "mikha"),
    "nachum": ("nahum",),
    "chavakuk": ("habakkuk", "habakuk"),
    "tzefania": ("zephaniah", "tsefania"),
    "chaggai": ("haggai",),
    "zecharia": ("zechariah", "zekharia"),
    "malachi": (),
    "tehillim": ("psalms", "psalm", "ps", "tehilim"),
    "mishlei": ("proverbs", "prov"),
    "iyov": ("job", "iyyov"),
    "shir-hashirim": ("song-of-songs", "song-of-solomon", "canticles", "shir-ha-shirim"),
    "rut": ("ruth",),
    "eicha": ("lamentations", "eichah", "eikhah"),
    "kohelet": ("ecclesiastes", "qohelet", "koheleth"),
    "esther": ("ester", "megillat-esther"),
    "daniel": (),
    "ezra": (),
    "nechemia": ("nehemiah", "nehemia", "nechemya"),
    "divrei-hayamim-i": ("1-chronicles", "i-chronicles", "first-chronicles", "chronicles-i", "chronicles-1", "divrei-hayamim-1"),
    "divrei-hayamim-ii": ("2-chronicles", "ii-chronicles", "second-chronicles", "chronicles-ii", "chronicles-2", "divrei-hayamim-2"),
}

# Names that point at exactly one text in the graph.
_DIRECT: dict[str, tuple[str, ...]] = {
    "mishnah-avot": ("avot", "pirkei-avot", "pirke-avot", "pirkei-avos", "ethics-of-the-fathers", "ethics-of-our-fathers"),
    "mishneh-torah-repentance": (
        "hilchot-teshuva", "hilchot-teshuvah", "hilkhot-teshuva", "hilkhot-teshuvah", "laws-of-repentance",
        "rambam-hilchot-teshuva", "rambam-hilchot-teshuvah", "mishneh-torah-hilchot-teshuvah",
        "mishneh-torah-laws-of-repentance", "mishneh-torah-teshuvah",
    ),
    "sefer-hazohar": ("zohar", "the-zohar", "sefer-ha-zohar"),
    "moreh-nevuchim": ("guide-for-the-perplexed", "guide-of-the-perplexed", "guide-to-the-perplexed", "moreh-nevukhim", "the-guide"),
    "sefer-hakuzari": ("kuzari", "the-kuzari"),
    "mesillat-yesharim": ("path-of-the-just", "mesilat-yesharim"),
    "chovot-halevavot": ("duties-of-the-heart", "chovot-ha-levavot"),
    "tanya": ("likutei-amarim", "the-tanya"),
    "haggadah-shel-pesach": ("haggadah", "passover-haggadah", "pesach-haggadah"),
    "sefer-hachinuch": ("sefer-ha-chinuch", "chinuch"),
}

# Spelling variants people use for Talmud tractates, mapped to the graph's name.
_TRACTATE_VARIANTS: dict[str, tuple[str, ...]] = {
    "berakhot": ("berachot", "brachot", "berachos", "brachos", "berakhos"),
    "shabbat": ("shabbos", "shabbath", "shabat"),
    "eruvin": ("eiruvin",),
    "pesachim": ("pesahim",),
    "rosh-hashanah": ("rosh-hashana",),
    "taanit": ("taanis", "ta-anit"),
    "megillah": ("megilla", "megila"),
    "moed-katan": ("moed-qatan",),
    "chagigah": ("hagigah", "chagiga"),
    "yevamot": ("yevamos", "yebamot"),
    "ketubot": ("ketubos", "kesubos", "kesuvos", "ketuvot"),
    "gittin": ("gitin",),
    "kiddushin": ("kidushin", "qiddushin"),
    "bava-kamma": ("baba-kamma", "bava-kama", "baba-kama", "bava-qamma"),
    "bava-metzia": ("baba-metzia", "bava-metsia", "baba-metsia", "bava-metziah"),
    "bava-batra": ("baba-batra", "bava-basra", "baba-basra"),
    "makkot": ("makkos", "makot"),
    "shevuot": ("shevuos", "shavuot-tractate"),
    "avodah-zarah": ("avoda-zara", "avodah-zara", "avoda-zarah"),
    "horayot": ("horayos",),
    "zevachim": ("zevahim",),
    "menachot": ("menahot", "menachos"),
    "chullin": ("hullin", "chulin"),
    "bekhorot": ("bechorot", "bechoros"),
    "arakhin": ("arachin", "erchin"),
    "keritot": ("kerisos", "kritot"),
    "meilah": ("meila",),
    "niddah": ("nidah", "nidda"),
    "sukkah": ("sukka", "succah"),
    "beitzah": ("beitza", "beiza", "betzah"),
    "sotah": ("sota",),
    "nedarim": (),
    "nazir": (),
    "sanhedrin": (),
    "yoma": (),
    "temurah": ("temura",),
}

_FILLER = re.compile(
    r"\b(talmud|bavli|babylonian|tractate|masechet|masekhet|maseches|the|book\s+of|sefer|parashat|parshat)\b", re.IGNORECASE
)
_SLUG_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:_\d+){1,3}$")
_DAF = re.compile(r"(?:\bdaf\s*)?(\d{1,3})\s*([ab])(?:\s*-\s*(?:(\d{1,3})\s*)?([ab]))?\s*$", re.IGNORECASE)
_CH_V = re.compile(r"(\d{1,3})\s*[:.,]\s*(\d{1,3})(?:\s*[:.]\s*(\d{1,3}))?(?:\s*-\s*(\d{1,3}))?\s*$")
_CH = re.compile(r"(?:\b(?:chapter|ch|perek)\.?\s*)?(\d{1,3})\s*$", re.IGNORECASE)

MAX_RANGE = 30  # verses in one range request


def normalize_key(value: str) -> str:
    """Lowercase, ASCII-dash key used for every catalog lookup."""
    v = value.strip().lower().replace("’", "").replace("'", "").replace("`", "")
    v = re.sub(r"[^a-z0-9֐-׿]+", "-", v)
    return re.sub(r"-{2,}", "-", v).strip("-")


def skeleton(key: str) -> str:
    """A spelling-tolerant form: 'Berachos' and 'Berakhot' share a skeleton."""
    s = key
    for a, b in (("kh", "ch"), ("tz", "ts"), ("ph", "f"), ("q", "k"), ("w", "v"), ("th", "t"),
                 ("ei", "e"), ("ai", "a"), ("ee", "i"), ("oo", "u"), ("y", "i")):
        s = s.replace(a, b)
    s = re.sub(r"(.)\1+", r"\1", s)                  # collapse doubled letters
    s = re.sub(r"s(?=-|$)", "t", s)                  # Ashkenazi final s / Sephardi final t
    s = re.sub(r"h(?=-|$)", "", s)                   # optional final h
    return s


@dataclass(frozen=True)
class TextInfo:
    slug: str
    title: str
    genre: str = ""
    author: str = ""
    era: str = ""


@dataclass
class ParsedRef:
    """The result of parsing. `kind` is one of: id, verse, range, comment, chapter,
    daf, text, unknown."""
    raw: str
    kind: str = "unknown"
    slug: str | None = None
    chapter: int | None = None       # chapter, or the first Talmud page index
    chapter_end: int | None = None   # last Talmud page index for a page range
    verse: int | None = None
    verse_end: int | None = None
    comment: int | None = None
    canonical_id: str | None = None  # for kind == "id"
    suggestions: list[str] = field(default_factory=list)
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.kind != "unknown"


class Catalog:
    """Name lookup over the texts in the graph."""

    def __init__(self, texts: list[TextInfo]):
        self.by_slug: dict[str, TextInfo] = {t.slug: t for t in texts}
        self._exact: dict[str, str] = {}
        self._skel: dict[str, set[str]] = {}
        self._bavli = {s[len("bavli-"):] for s in self.by_slug if s.startswith("bavli-")}

        def add(key: str, slug: str, *, override: bool = False) -> None:
            if not key or slug not in self.by_slug:
                return
            if override or key not in self._exact:
                self._exact[key] = slug
            self._skel.setdefault(skeleton(key), set()).add(slug)

        for t in texts:
            add(t.slug, t.slug, override=True)
        for t in texts:
            add(normalize_key(t.title), t.slug)
        for table in (_TANAKH, _DIRECT):
            for slug, aliases in table.items():
                for a in aliases:
                    add(normalize_key(a), slug, override=True)
        for tractate, variants in _TRACTATE_VARIANTS.items():
            for prefix in ("bavli", "mishnah", "yerushalmi", "tosefta"):
                slug = f"{prefix}-{tractate}"
                for v in variants:
                    add(f"{prefix}-{v}", slug, override=True)

    # -- text name → slug ---------------------------------------------------
    def is_daf_text(self, slug: str) -> bool:
        """True when the text is addressed by Talmud page (2a, 2b, ...)."""
        info = self.by_slug.get(slug)
        if info and info.genre == "talmud_bavli":
            return True
        if "-on-" in slug:
            tail = slug.split("-on-", 1)[1]
            return tail in self._bavli
        return False

    def _tractate(self, key: str) -> str:
        for tractate, variants in _TRACTATE_VARIANTS.items():
            if key == tractate or key in variants:
                return tractate
        return key

    def _book_variants(self, key: str) -> list[str]:
        """'rashi-on-bereishit' ↔ 'rashi-on-genesis': try each name of the base book."""
        if "-on-" not in key:
            return []
        head, tail = key.split("-on-", 1)
        out: list[str] = []
        tail_t = self._tractate(tail)
        if tail_t != tail:
            out.append(f"{head}-on-{tail_t}")
        for slug, aliases in _TANAKH.items():
            names = (slug, *(normalize_key(a) for a in aliases))
            if tail in names:
                out.extend(f"{head}-on-{n}" for n in names if n != tail)
        return out

    def resolve_text(self, name: str, *, locator: str | None = None) -> tuple[str | None, list[str]]:
        """Return (slug, suggestions). `locator` is 'daf', 'verse', 'chapter' or None
        and breaks the tie between a Talmud tractate and the Mishnah tractate."""
        key = normalize_key(_FILLER.sub(" ", name))
        if not key:
            return None, []
        raw_key = normalize_key(name)
        candidates = [raw_key, key]
        key = self._tractate(key)
        candidates.append(key)
        # Bare tractate names: a page reference means the Babylonian Talmud,
        # chapter:mishnah means the Mishnah.
        order = ("bavli", "mishnah") if locator in ("daf", None) else ("mishnah", "bavli")
        bare = re.sub(r"^(m|b|bt|tb|y|mishna|mishnah)-", "", key)
        bare = self._tractate(bare)
        if re.match(r"^(m|mishna|mishnah)-", key):
            order = ("mishnah",)
        elif re.match(r"^(b|bt|tb)-", key):
            order = ("bavli",)
        elif re.match(r"^y-", key):
            order = ("yerushalmi",)
        prefixed = [f"{p}-{bare}" for p in order]
        if any(c in self.by_slug for c in prefixed):
            candidates = prefixed + candidates     # a tractate name: the locator decides Talmud or Mishnah
        else:
            candidates.extend(prefixed)
        candidates.extend(self._book_variants(key))
        for c in candidates:
            if c in self._exact:
                return self._exact[c], []
        for c in candidates:
            hits = self._skel.get(skeleton(c))
            if hits and len(hits) == 1:
                return next(iter(hits)), []
        pool = list(self._exact)
        close = difflib.get_close_matches(key, pool, n=6, cutoff=0.72)
        seen: list[str] = []
        for c in close:
            slug = self._exact[c]
            if slug not in seen:
                seen.append(slug)
        return None, [self.by_slug[s].title for s in seen[:4]]

    # -- full reference -----------------------------------------------------
    def parse(self, reference: str) -> ParsedRef:
        raw = (reference or "").strip()
        ref = ParsedRef(raw=raw)
        if not raw:
            ref.reason = "The reference is empty."
            return ref
        text = raw.replace("–", "-").replace("—", "-").replace("־", "-")
        low = text.lower()

        if _SLUG_ID.match(low):
            slug = low.split("_", 1)[0]
            if slug in self.by_slug:
                ref.kind, ref.slug, ref.canonical_id = "id", slug, low
                return ref

        for kind, rx in (("daf", _DAF), ("verse", _CH_V), ("chapter", _CH)):
            m = rx.search(text)
            if not m:
                continue
            name = text[: m.start()].strip(" ,;:")
            if not name:
                continue
            slug, suggestions = self.resolve_text(name, locator=kind)
            if not slug:
                if ref.reason is None:      # keep the first, most specific reading of the name
                    ref.suggestions = suggestions
                    ref.reason = f"No text named '{name}' is in the library."
                # keep looking: 'Mishneh Torah 3' may parse better as a plain name
                continue
            ref.slug, ref.suggestions, ref.reason = slug, [], None
            if kind == "daf":
                if not self.is_daf_text(slug):
                    # e.g. "Genesis 2a" — treat the number as a chapter
                    ref.kind, ref.chapter = "chapter", int(m.group(1))
                    return ref
                d1, s1 = int(m.group(1)), m.group(2).lower()
                ref.kind = "daf"
                ref.chapter = 2 * d1 - (1 if s1 == "a" else 0)
                if m.group(4):
                    d2 = int(m.group(3)) if m.group(3) else d1
                    end = 2 * d2 - (1 if m.group(4).lower() == "a" else 0)
                    ref.chapter_end = min(max(end, ref.chapter), ref.chapter + 3)
                return ref
            if kind == "verse":
                ref.chapter, ref.verse = int(m.group(1)), int(m.group(2))
                if m.group(3):
                    ref.kind, ref.comment = "comment", int(m.group(3))
                elif m.group(4):
                    end = int(m.group(4))
                    ref.kind = "range"
                    ref.verse_end = min(max(end, ref.verse), ref.verse + MAX_RANGE - 1)
                else:
                    ref.kind = "verse"
                return ref
            ref.kind, ref.chapter = "chapter", int(m.group(1))
            return ref

        slug, suggestions = self.resolve_text(text)
        if slug:
            ref.kind, ref.slug, ref.reason, ref.suggestions = "text", slug, None, []
            return ref
        if not ref.suggestions:
            ref.suggestions = suggestions
        ref.reason = ref.reason or f"Could not read '{raw}' as a reference."
        return ref


# --- labels ------------------------------------------------------------------
def daf_label(index: int) -> str:
    """Talmud page index → '2a'."""
    return f"{(index + 1) // 2}{'a' if index % 2 else 'b'}"


def label_for_id(canonical_id: str, catalog: Catalog) -> str:
    """Human citation for a graph id: 'Genesis 22:2', 'Berakhot 2a', 'Rashi on Genesis 22:2:1'."""
    parts = canonical_id.split("_")
    slug, nums = parts[0], parts[1:]
    info = catalog.by_slug.get(slug)
    title = info.title if info else slug
    if not nums:
        return title
    if catalog.is_daf_text(slug) and nums[0].isdigit():
        return f"{title} {daf_label(int(nums[0]))}"
    return f"{title} {':'.join(nums)}"
