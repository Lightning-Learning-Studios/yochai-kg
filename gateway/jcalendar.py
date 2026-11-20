"""The Jewish calendar, computed locally: Hebrew date, weekly Torah portion,
daily Talmud page (Daf Yomi) and upcoming holidays.

No network call is made. The Hebrew date, portion and holidays come from the
pyluach library. The Daf Yomi page is arithmetic on the fixed 2,711-day cycle.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from pyluach import dates, parshios

# (name, slug of the book in the graph, first verse, last verse) in Torah order.
# The index matches pyluach's portion numbers (0 to 53).
PORTIONS: list[tuple[str, str, str, str]] = [
    ("Bereshit", "bereishit", "1:1", "6:8"), ("Noach", "bereishit", "6:9", "11:32"),
    ("Lech-Lecha", "bereishit", "12:1", "17:27"), ("Vayera", "bereishit", "18:1", "22:24"),
    ("Chayei Sarah", "bereishit", "23:1", "25:18"), ("Toldot", "bereishit", "25:19", "28:9"),
    ("Vayetzei", "bereishit", "28:10", "32:3"), ("Vayishlach", "bereishit", "32:4", "36:43"),
    ("Vayeshev", "bereishit", "37:1", "40:23"), ("Miketz", "bereishit", "41:1", "44:17"),
    ("Vayigash", "bereishit", "44:18", "47:27"), ("Vayechi", "bereishit", "47:28", "50:26"),
    ("Shemot", "shemot", "1:1", "6:1"), ("Vaera", "shemot", "6:2", "9:35"),
    ("Bo", "shemot", "10:1", "13:16"), ("Beshalach", "shemot", "13:17", "17:16"),
    ("Yitro", "shemot", "18:1", "20:23"), ("Mishpatim", "shemot", "21:1", "24:18"),
    ("Terumah", "shemot", "25:1", "27:19"), ("Tetzaveh", "shemot", "27:20", "30:10"),
    ("Ki Tisa", "shemot", "30:11", "34:35"), ("Vayakhel", "shemot", "35:1", "38:20"),
    ("Pekudei", "shemot", "38:21", "40:38"),
    ("Vayikra", "vayikra", "1:1", "5:26"), ("Tzav", "vayikra", "6:1", "8:36"),
    ("Shemini", "vayikra", "9:1", "11:47"), ("Tazria", "vayikra", "12:1", "13:59"),
    ("Metzora", "vayikra", "14:1", "15:33"), ("Acharei Mot", "vayikra", "16:1", "18:30"),
    ("Kedoshim", "vayikra", "19:1", "20:27"), ("Emor", "vayikra", "21:1", "24:23"),
    ("Behar", "vayikra", "25:1", "26:2"), ("Bechukotai", "vayikra", "26:3", "27:34"),
    ("Bamidbar", "bamidbar", "1:1", "4:20"), ("Nasso", "bamidbar", "4:21", "7:89"),
    ("Beha'alotcha", "bamidbar", "8:1", "12:16"), ("Sh'lach", "bamidbar", "13:1", "15:41"),
    ("Korach", "bamidbar", "16:1", "18:32"), ("Chukat", "bamidbar", "19:1", "22:1"),
    ("Balak", "bamidbar", "22:2", "25:9"), ("Pinchas", "bamidbar", "25:10", "30:1"),
    ("Matot", "bamidbar", "30:2", "32:42"), ("Masei", "bamidbar", "33:1", "36:13"),
    ("Devarim", "devarim", "1:1", "3:22"), ("Vaetchanan", "devarim", "3:23", "7:11"),
    ("Eikev", "devarim", "7:12", "11:25"), ("Re'eh", "devarim", "11:26", "16:17"),
    ("Shoftim", "devarim", "16:18", "21:9"), ("Ki Teitzei", "devarim", "21:10", "25:19"),
    ("Ki Tavo", "devarim", "26:1", "29:8"), ("Nitzavim", "devarim", "29:9", "30:20"),
    ("Vayeilech", "devarim", "31:1", "31:30"), ("Ha'azinu", "devarim", "32:1", "32:52"),
    ("Vezot Haberakhah", "devarim", "33:1", "34:12"),
]
_BOOK_ENGLISH = {"bereishit": "Genesis", "shemot": "Exodus", "vayikra": "Leviticus",
                 "bamidbar": "Numbers", "devarim": "Deuteronomy"}

# Daf Yomi order: (display name, slug in the graph or None, last page number).
# Kinnim, Tamid and Middot are printed with continuing page numbers after Meilah.
_SHAS: list[tuple[str, str | None, int]] = [
    ("Berakhot", "bavli-berakhot", 64), ("Shabbat", "bavli-shabbat", 157), ("Eruvin", "bavli-eruvin", 105),
    ("Pesachim", "bavli-pesachim", 121), ("Shekalim", "yerushalmi-shekalim", 22), ("Yoma", "bavli-yoma", 88),
    ("Sukkah", "bavli-sukkah", 56), ("Beitzah", "bavli-beitzah", 40), ("Rosh Hashanah", "bavli-rosh-hashanah", 35),
    ("Taanit", "bavli-taanit", 31), ("Megillah", "bavli-megillah", 32), ("Moed Katan", "bavli-moed-katan", 29),
    ("Chagigah", "bavli-chagigah", 27), ("Yevamot", "bavli-yevamot", 122), ("Ketubot", "bavli-ketubot", 112),
    ("Nedarim", "bavli-nedarim", 91), ("Nazir", "bavli-nazir", 66), ("Sotah", "bavli-sotah", 49),
    ("Gittin", "bavli-gittin", 90), ("Kiddushin", "bavli-kiddushin", 82), ("Bava Kamma", "bavli-bava-kamma", 119),
    ("Bava Metzia", "bavli-bava-metzia", 119), ("Bava Batra", "bavli-bava-batra", 176),
    ("Sanhedrin", "bavli-sanhedrin", 113), ("Makkot", "bavli-makkot", 24), ("Shevuot", "bavli-shevuot", 49),
    ("Avodah Zarah", "bavli-avodah-zarah", 76), ("Horayot", "bavli-horayot", 14),
    ("Zevachim", "bavli-zevachim", 120), ("Menachot", "bavli-menachot", 110), ("Chullin", "bavli-chullin", 142),
    ("Bekhorot", "bavli-bekhorot", 61), ("Arakhin", "bavli-arakhin", 34), ("Temurah", "bavli-temurah", 34),
    ("Keritot", "bavli-keritot", 28), ("Meilah", "bavli-meilah", 22), ("Kinnim", None, 4),
    ("Tamid", None, 9), ("Middot", None, 5), ("Niddah", "bavli-niddah", 73),
]
_SHAS_OFFSET = {"Kinnim": 21, "Tamid": 24, "Middot": 32}
_CYCLE_DAYS = 2711
_CYCLE_8_START = dt.date(1975, 6, 24)  # the current page counts began with cycle 8
assert sum(n - 1 for _, _, n in _SHAS) == _CYCLE_DAYS


def daf_yomi(day: dt.date) -> dict[str, Any]:
    """The Daf Yomi page for a civil date."""
    offset = (day - _CYCLE_8_START).days % _CYCLE_DAYS
    cycle = 8 + (day - _CYCLE_8_START).days // _CYCLE_DAYS
    total = 0
    for name, slug, last in _SHAS:
        total += last - 1
        if offset < total:
            page = last + 1 - (total - offset) + _SHAS_OFFSET.get(name, 0)
            out: dict[str, Any] = {"tractate": name, "page": page, "label": f"{name} {page}", "cycle": cycle}
            if slug and slug.startswith("bavli-"):
                out["reference"] = f"{name} {page}a"
                out["in_library"] = True
            else:
                out["reference"] = None
                out["in_library"] = False
            return out
    raise RuntimeError("unreachable: the cycle table covers every day")


def _portion(day: dates.GregorianDate, israel: bool) -> dict[str, Any] | None:
    idx = parshios.getparsha(day, israel=israel)
    if not idx:
        return None
    first, last = PORTIONS[idx[0]], PORTIONS[idx[-1]]
    book = _BOOK_ENGLISH[first[1]]
    return {
        "name": "-".join(PORTIONS[i][0] for i in idx),
        "hebrew_name": parshios.getparsha_string(day, israel=israel, hebrew=True),
        "reference": f"{book} {first[2]}-{last[3]}",
        "first_verse": f"{book} {first[2]}",
        "book": book,
        "double_portion": len(idx) > 1,
    }


# pyluach uses Ashkenazi spellings; the plugin shows the more common ones.
_HOLIDAY_NAMES = {
    "Chanuka": "Chanukah", "10 of Teves": "Fast of 10 Tevet", "Succos": "Sukkot", "Shavuos": "Shavuot",
    "Shmini Atzeres": "Shemini Atzeret", "Simchas Torah": "Simchat Torah", "Taanis Esther": "Fast of Esther",
    "9 of Av": "Tisha B'Av", "17 of Tamuz": "Fast of 17 Tammuz", "Tzom Gedalia": "Fast of Gedaliah",
    "Rosh Hashana": "Rosh Hashanah", "Pesach": "Passover (Pesach)", "Tu B'shvat": "Tu BiShvat",
    "Lag Ba'omer": "Lag BaOmer", "Tu B'av": "Tu B'Av",
}


def _today_name(h: Any, israel: bool) -> str | None:
    raw = h.holiday(israel=israel)
    if not raw:
        return None
    full = h.holiday(israel=israel, prefix_day=True)
    return full.replace(raw, _HOLIDAY_NAMES.get(raw, raw))


def _shabbat_on_or_after(day: dt.date) -> dt.date:
    return day + dt.timedelta(days=(5 - day.weekday()) % 7)


def calendar_for(day: dt.date, *, israel: bool = False, days_ahead: int = 45) -> dict[str, Any]:
    """Everything the study skills need for one civil date."""
    g = dates.GregorianDate(day.year, day.month, day.day)
    h = g.to_heb()
    shabbat = _shabbat_on_or_after(day)
    portion = _portion(g, israel)
    upcoming: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i in range(days_ahead + 1):
        d = day + dt.timedelta(days=i)
        hd = dates.GregorianDate(d.year, d.month, d.day).to_heb()
        raw = hd.holiday(israel=israel)
        if not raw:
            continue
        key = f"{raw}-{hd.year}"
        if key in seen:
            continue
        seen.add(key)
        item: dict[str, Any] = {"name": _HOLIDAY_NAMES.get(raw, raw), "date": d.isoformat(), "days_away": i}
        if hd.fast_day() and raw not in ("9 of Av", "Yom Kippur"):
            item["begins"] = "at dawn on the date shown"
        else:
            item["begins"] = f"at sunset on {(d - dt.timedelta(days=1)).isoformat()}"
        upcoming.append(item)
    out: dict[str, Any] = {
        "date": day.isoformat(),
        "weekday": day.strftime("%A"),
        "hebrew_date": f"{h.day} {h.month_name()} {h.year}",
        "hebrew_date_hebrew": h.hebrew_date_string(),
        "israel": israel,
        "today": _today_name(h, israel),
        "shabbat_date": shabbat.isoformat(),
        "torah_portion": portion,
        "daf_yomi": daf_yomi(day),
        "upcoming_holidays": upcoming[:6],
        "note": ("A Jewish day begins at sunset on the evening before the civil date shown. "
                 "When a holiday falls on Shabbat there is a holiday reading in place of a weekly portion."),
    }
    if portion is None:
        out["torah_portion_note"] = "This Shabbat has a holiday reading, so there is no weekly portion."
    return out


def parse_date(value: str | None, *, today: dt.date | None = None) -> dt.date:
    """Accept YYYY-MM-DD, 'today' or 'tomorrow'. Raises ValueError otherwise."""
    base = today or dt.datetime.now(dt.UTC).date()
    if not value or value.strip().lower() == "today":
        return base
    v = value.strip().lower()
    if v == "tomorrow":
        return base + dt.timedelta(days=1)
    if v == "yesterday":
        return base - dt.timedelta(days=1)
    try:
        d = dt.date.fromisoformat(v)
    except ValueError as e:
        raise ValueError("Give the date as YYYY-MM-DD, for example 2026-12-04.") from e
    if not 1900 <= d.year <= 2200:
        raise ValueError("The calendar covers the years 1900 to 2200.")
    return d
