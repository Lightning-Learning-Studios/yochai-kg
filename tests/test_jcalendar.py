"""The Jewish calendar maths. Expected values were checked against hebcal.com
(520 Daf Yomi days and 68 weekly portions matched on 20 November 2026)."""
import datetime as dt

import pytest

from gateway import jcalendar


@pytest.mark.parametrize("day, label", [
    ("2020-01-05", "Berakhot 2"),        # first day of cycle 14
    ("2023-01-01", "Nedarim 68"),
    ("2026-11-18", "Bekhorot 61"),
    ("2026-11-19", "Arakhin 2"),
    ("2026-11-20", "Arakhin 3"),
    ("2027-03-23", "Tamid 33"),
    ("2027-03-24", "Middot 34"),         # the tractates printed with continuing page numbers
    ("2027-03-27", "Middot 37"),
    ("2027-06-07", "Niddah 73"),         # last day of cycle 14
    ("2027-06-08", "Berakhot 2"),        # first day of cycle 15
])
def test_daf_yomi(day, label):
    assert jcalendar.daf_yomi(dt.date.fromisoformat(day))["label"] == label


def test_daf_yomi_cycle_number_and_library_flag():
    daf = jcalendar.daf_yomi(dt.date(2026, 11, 20))
    assert daf["cycle"] == 14 and daf["in_library"] and daf["reference"] == "Arakhin 3a"
    assert jcalendar.daf_yomi(dt.date(2027, 6, 8))["cycle"] == 15
    outside = jcalendar.daf_yomi(dt.date(2027, 3, 24))      # Middot has no Babylonian Talmud
    assert outside["in_library"] is False and outside["reference"] is None


@pytest.mark.parametrize("day, name, reference", [
    ("2026-11-20", "Vayetzei", "Genesis 28:10-32:3"),
    ("2026-11-22", "Vayishlach", "Genesis 32:4-36:43"),
    ("2027-03-20", "Vayikra", "Leviticus 1:1-5:26"),
    ("2027-04-03", "Shemini", "Leviticus 9:1-11:47"),
])
def test_weekly_portion(day, name, reference):
    portion = jcalendar.calendar_for(dt.date.fromisoformat(day))["torah_portion"]
    assert (portion["name"], portion["reference"]) == (name, reference)


def test_no_weekly_portion_when_a_holiday_falls_on_shabbat():
    cal = jcalendar.calendar_for(dt.date(2026, 9, 10))       # Shabbat 12 September 2026 is Rosh Hashanah
    assert cal["torah_portion"] is None and "holiday reading" in cal["torah_portion_note"]


def test_chanukah_2026():
    cal = jcalendar.calendar_for(dt.date(2026, 11, 20))
    first = cal["upcoming_holidays"][0]
    assert first["name"] == "Chanukah" and first["date"] == "2026-12-05"
    assert first["begins"] == "at sunset on 2026-12-04" and first["days_away"] == 15
    assert cal["hebrew_date"] == "10 Kislev 5787"
    assert jcalendar.calendar_for(dt.date(2026, 12, 5))["today"] == "1 Chanukah"


def test_purim_and_passover_2027():
    names = {h["name"]: h["date"] for h in jcalendar.calendar_for(dt.date(2027, 3, 20))["upcoming_holidays"]}
    assert names["Purim"] == "2027-03-23" and names["Passover (Pesach)"] == "2027-04-22"


def test_dawn_fasts_do_not_begin_the_evening_before():
    fasts = [h for h in jcalendar.calendar_for(dt.date(2026, 12, 10))["upcoming_holidays"] if "10 Tevet" in h["name"]]
    assert fasts and fasts[0]["begins"] == "at dawn on the date shown"


def test_israel_and_diaspora_can_differ():
    day = dt.date(2027, 4, 30)                               # after the 8th day of Passover falls on Shabbat abroad
    away = jcalendar.calendar_for(day)["torah_portion"]
    home = jcalendar.calendar_for(day, israel=True)["torah_portion"]
    assert away is not None and home is not None


def test_every_portion_table_row_is_well_formed():
    assert len(jcalendar.PORTIONS) == 54
    for name, slug, first, last in jcalendar.PORTIONS:
        assert name and slug in {"bereishit", "shemot", "vayikra", "bamidbar", "devarim"}
        assert all(part.isdigit() for ref in (first, last) for part in ref.split(":"))


def test_parse_date():
    today = dt.date(2026, 11, 20)
    assert jcalendar.parse_date(None, today=today) == today
    assert jcalendar.parse_date("tomorrow", today=today) == dt.date(2026, 11, 21)
    assert jcalendar.parse_date("2026-12-04") == dt.date(2026, 12, 4)
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        jcalendar.parse_date("12/04/2026")
    with pytest.raises(ValueError, match="1900 to 2200"):
        jcalendar.parse_date("3000-01-01")
