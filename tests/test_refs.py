"""Reference parsing: what a person types becomes the right graph id. Offline."""
import pytest

from gateway.refs import Catalog, TextInfo, daf_label, label_for_id, normalize_key, skeleton


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return Catalog([
        TextInfo("bereishit", "Genesis", "tanakh"),
        TextInfo("tehillim", "Psalms", "tanakh"),
        TextInfo("shmuel-i", "I Samuel", "tanakh"),
        TextInfo("shir-hashirim", "Song of Songs", "tanakh"),
        TextInfo("bavli-berakhot", "Berakhot", "talmud_bavli"),
        TextInfo("bavli-shabbat", "Shabbat", "talmud_bavli"),
        TextInfo("bavli-bava-metzia", "Bava Metzia", "talmud_bavli"),
        TextInfo("mishnah-berakhot", "Mishnah Berakhot", "mishnah"),
        TextInfo("mishnah-avot", "Pirkei Avot", "mishnah"),
        TextInfo("rashi-on-genesis", "Rashi on Genesis", "commentary"),
        TextInfo("kli-yakar-on-bereishit", "Kli Yakar on Genesis", "commentary"),
        TextInfo("rashi-on-berakhot", "Rashi on Berakhot", "commentary"),
        TextInfo("mishneh-torah-repentance", "Mishneh Torah, Repentance", "halakhic_code", "Rambam (Maimonides)"),
        TextInfo("moreh-nevuchim", "Guide for the Perplexed", "philosophy"),
        TextInfo("sefer-hakuzari", "Kuzari", "philosophy"),
        TextInfo("meor-einayim", "Me'or Einayim", "hasidut"),
    ])


@pytest.mark.parametrize("typed, kind, slug, chapter, verse", [
    ("Genesis 22:2", "verse", "bereishit", 22, 2),
    ("genesis 22.2", "verse", "bereishit", 22, 2),
    ("Bereshit 22:2", "verse", "bereishit", 22, 2),
    ("Gen 1:1", "verse", "bereishit", 1, 1),
    ("Psalm 23", "chapter", "tehillim", 23, None),
    ("Psalms 23:4", "verse", "tehillim", 23, 4),
    ("Tehillim chapter 23", "chapter", "tehillim", 23, None),
    ("1 Samuel 1:1", "verse", "shmuel-i", 1, 1),
    ("I Samuel 1:1", "verse", "shmuel-i", 1, 1),
    ("Song of Songs 1:2", "verse", "shir-hashirim", 1, 2),
    ("Pirkei Avot 1:14", "verse", "mishnah-avot", 1, 14),
    ("Avot 1:14", "verse", "mishnah-avot", 1, 14),
    ("Ethics of the Fathers 2:4", "verse", "mishnah-avot", 2, 4),
    ("Mishneh Torah, Repentance 3:4", "verse", "mishneh-torah-repentance", 3, 4),
    ("Rambam Hilchot Teshuva 3:4", "verse", "mishneh-torah-repentance", 3, 4),
    ("Rashi on Genesis 22:2", "verse", "rashi-on-genesis", 22, 2),
    ("Rashi on Bereishit 22:2", "verse", "rashi-on-genesis", 22, 2),
    ("Kli Yakar on Genesis 22:2", "verse", "kli-yakar-on-bereishit", 22, 2),
    ("Mishnah Berakhot 1:1", "verse", "mishnah-berakhot", 1, 1),
    ("Berakhot 1:1", "verse", "mishnah-berakhot", 1, 1),        # chapter:mishnah form means the Mishnah
])
def test_verse_and_chapter_references(catalog, typed, kind, slug, chapter, verse):
    ref = catalog.parse(typed)
    assert (ref.kind, ref.slug, ref.chapter, ref.verse) == (kind, slug, chapter, verse)


@pytest.mark.parametrize("typed, slug, index, index_end", [
    ("Berakhot 2a", "bavli-berakhot", 3, None),
    ("Berakhot 2b", "bavli-berakhot", 4, None),
    ("berachot 64a", "bavli-berakhot", 127, None),
    ("Brachos 2a", "bavli-berakhot", 3, None),
    ("Talmud Bavli Berakhot 2a", "bavli-berakhot", 3, None),
    ("Tractate Shabbat 31a", "bavli-shabbat", 61, None),
    ("Shabbos daf 31a", "bavli-shabbat", 61, None),
    ("Baba Metzia 59b", "bavli-bava-metzia", 118, None),
    ("Berakhot 2a-2b", "bavli-berakhot", 3, 4),
    ("Berakhot 2a-b", "bavli-berakhot", 3, 4),
    ("Rashi on Berakhot 2a", "rashi-on-berakhot", 3, None),
])
def test_talmud_page_references(catalog, typed, slug, index, index_end):
    ref = catalog.parse(typed)
    assert (ref.kind, ref.slug, ref.chapter, ref.chapter_end) == ("daf", slug, index, index_end)


def test_page_range_is_capped(catalog):
    ref = catalog.parse("Berakhot 2a-30b")
    assert ref.chapter == 3 and ref.chapter_end == 6       # at most 4 sides in one request


def test_verse_range(catalog):
    ref = catalog.parse("Genesis 22:1-19")
    assert (ref.kind, ref.chapter, ref.verse, ref.verse_end) == ("range", 22, 1, 19)
    capped = catalog.parse("Psalms 119:1-176")
    assert capped.verse_end == 30


def test_commentary_note(catalog):
    ref = catalog.parse("Rashi on Genesis 22:2:1")
    assert (ref.kind, ref.slug, ref.chapter, ref.verse, ref.comment) == ("comment", "rashi-on-genesis", 22, 2, 1)


def test_graph_id_passes_through(catalog):
    ref = catalog.parse("bavli-berakhot_3_1")
    assert (ref.kind, ref.slug, ref.canonical_id) == ("id", "bavli-berakhot", "bavli-berakhot_3_1")
    ref = catalog.parse("rashi-on-genesis_22_2_1")
    assert ref.kind == "id"


def test_text_without_a_place(catalog):
    ref = catalog.parse("Guide for the Perplexed")
    assert (ref.kind, ref.slug) == ("text", "moreh-nevuchim")
    assert catalog.parse("The Kuzari").slug == "sefer-hakuzari"


@pytest.mark.parametrize("typed", ["Book of Mormon 1:1", "Harry Potter 3", "", "   ", "22:2"])
def test_unknown_references_fail_cleanly(catalog, typed):
    ref = catalog.parse(typed)
    assert not ref.ok
    assert ref.reason


def test_unknown_text_keeps_the_most_specific_name(catalog):
    ref = catalog.parse("Book of Mormon 1:1")
    assert "Book of Mormon" in ref.reason and "Mormon 1" not in ref.reason


def test_close_spelling_gets_suggestions(catalog):
    slug, suggestions = catalog.resolve_text("Genesiss")
    assert slug == "bereishit" or "Genesis" in suggestions


def test_bare_tractate_defaults_to_talmud(catalog):
    assert catalog.resolve_text("Berakhot")[0] == "bavli-berakhot"
    assert catalog.resolve_text("Berakhot", locator="verse")[0] == "mishnah-berakhot"
    assert catalog.resolve_text("m. Berakhot", locator="daf")[0] == "mishnah-berakhot"


def test_labels(catalog):
    assert daf_label(3) == "2a" and daf_label(4) == "2b" and daf_label(127) == "64a"
    assert label_for_id("bereishit_22_2", catalog) == "Genesis 22:2"
    assert label_for_id("bavli-berakhot_3_1", catalog) == "Berakhot 2a"
    assert label_for_id("rashi-on-genesis_22_2_1", catalog) == "Rashi on Genesis 22:2:1"
    assert label_for_id("rashi-on-berakhot_3_1_1", catalog) == "Rashi on Berakhot 2a"


def test_key_helpers():
    assert normalize_key("  Me'or  Einayim ") == "meor-einayim"
    assert skeleton("berachos") == skeleton("berakhot")
    assert skeleton("kiddushin") == skeleton("kidushin")
