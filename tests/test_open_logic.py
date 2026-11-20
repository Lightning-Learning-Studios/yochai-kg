"""Limits, the skill shelf and the search ranking rules. Offline."""
from pathlib import Path

from gateway import open_tools as T
from gateway import shelf
from gateway.limits import RateLimiter, TTLCache, Usage, client_label
from gateway.refs import Catalog, TextInfo


# --- limits ---------------------------------------------------------------------
def test_rate_limiter_minute_window():
    rl = RateLimiter(per_minute=3, per_day=100)
    assert [rl.check("a", now=t)[0] for t in (0, 1, 2)] == [True, True, True]
    allowed, wait = rl.check("a", now=3)
    assert not allowed and 1 <= wait <= 61
    assert rl.check("b", now=3)[0]                  # another caller is not affected
    assert rl.check("a", now=61)[0]                 # the window slides


def test_rate_limiter_daily_budget():
    rl = RateLimiter(per_minute=1000, per_day=5)
    assert all(rl.check("a", now=i * 100)[0] for i in range(5))
    allowed, wait = rl.check("a", now=600)
    assert not allowed and wait >= 60


def test_cache_expires_and_evicts():
    cache = TTLCache(max_items=2, ttl_seconds=1000)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)                               # evicts the least recently used: b
    assert cache.get("b") is None and cache.get("a") == 1 and cache.get("c") == 3
    expired = TTLCache(ttl_seconds=-1)
    expired.put("x", 1)
    assert expired.get("x") is None


def test_client_label():
    assert client_label("Claude-User", None) == "claude"
    assert client_label("python-httpx", "claude-ai") == "claude"
    assert client_label("openai-mcp/1.0", None) == "chatgpt"
    assert client_label("curl/8", "cursor") == "other"
    assert client_label(None, None) == "other"


def test_usage_counts_without_identifying_anyone():
    usage = Usage()
    caller = usage.caller_id("203.0.113.7")
    assert "203.0.113.7" not in caller and len(caller) == 16
    assert caller == usage.caller_id("203.0.113.7") and caller != usage.caller_id("203.0.113.8")
    usage.record(rpc_method="initialize", tool=None, client="claude", caller=caller, ok=True, latency_ms=3)
    usage.record(rpc_method="tools/call", tool="get_passage", client="claude", caller=caller, ok=True, latency_ms=40)
    usage.record(rpc_method="tools/call", tool="get_passage", client="claude", caller=caller, ok=False, latency_ms=40)
    snap = usage.snapshot()
    assert snap["tool_calls"] == 2 and snap["errors"] == 1 and snap["sessions_started"] == {"claude": 1}
    assert snap["distinct_callers_today"] == 1
    rows = usage.drain()
    assert {(r["tool"], r["calls"], r["errors"]) for r in rows} == {("_session", 1, 0), ("get_passage", 2, 1)}
    assert set(rows[0]) == {"day", "tool", "client", "calls", "errors"}     # nothing else leaves the server
    assert usage.drain() == []
    usage.restore(rows)
    assert len(usage.drain()) == 2


# --- the skill shelf ------------------------------------------------------------
def _write(folder: Path, name: str, text: str) -> None:
    (folder / name).mkdir(parents=True)
    (folder / name / "SKILL.md").write_text(text, encoding="utf-8")


def test_shelf_loads_core_and_community_and_never_held(tmp_path):
    core, community = tmp_path / "core", tmp_path / "community"
    _write(core, "find-a-source", "---\nname: find-a-source\ndescription: Finds sources.\n---\n# Find\nBody.")
    _write(community, "seder-night", "---\nname: seder-night\ndescription: >\n  A plan for the\n  seder.\n"
                                     "author: Dana Levi\nlicense: CC BY 4.0\n---\nBody of the skill.")
    _write(community, "_held", "---\nname: held\ndescription: x\n---\nMust not be served.")
    _write(community, "find-a-source", "---\nname: find-a-source\ndescription: impostor\n---\nNo.")
    _write(community, "empty", "---\nname: empty\ndescription: x\n---\n")
    skills = shelf.load_all((("core", core), ("community", community)))
    assert set(skills) == {"find-a-source", "seder-night"}
    assert skills["find-a-source"].kind == "core" and skills["find-a-source"].description == "Finds sources."
    night = skills["seder-night"]
    assert (night.kind, night.author, night.licence) == ("community", "Dana Levi", "CC BY 4.0")
    assert night.description == "A plan for the seder." and night.body == "Body of the skill."


def test_shelf_skips_oversized_files(tmp_path):
    _write(tmp_path, "huge", "---\nname: huge\ndescription: x\n---\n" + "a" * (shelf.MAX_BYTES + 10))
    assert shelf.load_all((("community", tmp_path),)) == {}


def test_shelf_find_is_forgiving(tmp_path):
    _write(tmp_path, "weekly-portion", "---\nname: weekly-portion\ndescription: x\n---\nBody")
    _write(tmp_path, "holiday-prep", "---\nname: holiday-prep\ndescription: x\n---\nBody")
    skills = shelf.load_all((("core", tmp_path),))
    assert shelf.find(skills, "Weekly Portion")[0].name == "weekly-portion"
    assert shelf.find(skills, "weekly-portions")[0].name == "weekly-portion"
    missing, _ = shelf.find(skills, "quantum-physics")
    assert missing is None


def test_the_real_shelf_serves_the_core_skills_and_no_held_skill():
    skills = shelf.load_all()
    assert {"find-a-source", "weekly-portion", "explain-a-passage", "prepare-to-teach", "practical-law",
            "holiday-prep", "study-partner", "build-a-course", "yochai-skill-shelf"} <= set(skills)
    held = {p.parent.name for p in (shelf.ROOT / "shelf" / "_held").rglob("SKILL.md")}
    assert not (held & set(skills))                         # a held skill is never served
    for skill in skills.values():
        assert skill.description, f"{skill.name} has no description"


# --- search ranking -------------------------------------------------------------
def test_primary_sources_get_a_lift():
    assert T.primary_lift("bereishit") > T.primary_lift("bereishit-rabbah") > T.primary_lift("shem-mishmuel") == 0
    assert T.primary_lift("bavli-shabbat") > 0 and T.primary_lift("mishnah-avot") > 0
    assert T.primary_lift("mishnah-berurah") == 0          # a late law code, despite its name


def test_meaning_leads_and_words_alone_stay_below():
    vector = [{"su_id": "v1", "slug": "sefer-a", "score": 0.84}, {"su_id": "v2", "slug": "sefer-b", "score": 0.80}]
    keyword = [{"su_id": "k1", "slug": "sefer-c", "score": 20.0}, {"su_id": "v2", "slug": "sefer-b", "score": 9.0}]
    order = T.merge_ranked(vector, keyword, [], n=3)
    assert order[0] == ("su", "v1")
    assert order.index(("su", "v2")) < order.index(("su", "k1"))


def test_a_true_quote_goes_first_and_the_source_outranks_its_quoters():
    vector = [{"su_id": "v1", "slug": "shem-mishmuel", "score": 0.84}]
    phrase = [{"id": "mishnah-avot_1_14", "slug": "mishnah-avot", "quote": True, "cover": 0.8},
              {"id": "toldot_8", "slug": "toldot-yaakov-yosef", "quote": True, "cover": 0.9}]
    order = T.merge_ranked(vector, [], phrase, n=3)
    assert order[0] == ("tu", "mishnah-avot_1_14") and order[-1] == ("su", "v1")


def test_a_word_match_that_is_not_a_quote_does_not_outrank_meaning():
    vector = [{"su_id": "v1", "slug": "shaarei-teshuvah", "score": 0.80},
              {"su_id": "v2", "slug": "orchot-tzaddikim", "score": 0.78}]
    phrase = [{"id": "magen-avraham_151_17", "slug": "magen-avraham", "quote": False, "cover": 0.6}]
    assert T.merge_ranked(vector, [], phrase, n=3)[0][0] == "su"


def test_at_most_two_passages_per_text():
    vector = [{"su_id": f"v{i}", "slug": "shem-mishmuel", "score": 0.9 - i / 100} for i in range(5)]
    vector.append({"su_id": "other", "slug": "bavli-shabbat", "score": 0.7})
    order = T.merge_ranked(vector, [], [], n=4)
    assert sum(1 for _, i in order if i.startswith("v")) == 2 and ("su", "other") in order


def test_best_window_picks_the_lines_with_the_users_words():
    units = [{"id": f"t_1_{i}", "en": text, "he": "עברית"} for i, text in enumerate([
        "An opening line about something else entirely.",
        "Another unrelated line of introduction.",
        "Hospitality toward guests is greater than receiving the Divine Presence.",
        "As it is written: do not pass by your servant.",
    ], start=1)]
    window = T.best_window(units, ["guest", "great", "divin"], max_chars=200)
    assert window[0]["id"] == "t_1_3" and window[-1]["id"] == "t_1_4"
    assert T.best_window(units, ["zzz"], max_chars=60)[0]["id"] == "t_1_1"     # no match: start of the passage
    assert T.best_window([], ["x"]) == []


def test_phrase_query():
    assert T.phrase_query("teshuvah") is None
    index, query = T.phrase_query("binding of Isaac")
    assert index == "textunit_english" and query == '"binding of isaac"~1'
    index, query = T.phrase_query("If I am not for myself, who will be for me?")
    assert query.startswith('"if i am not for myself who will be for me"~4^2 OR "if i am not for"~2')
    index, query = T.phrase_query("וְאָהַבְתָּ לְרֵעֲךָ כָּמוֹךָ")
    assert index == "textunit_hebrew" and query == '"ואהבת לרעך כמוך"~1'        # vowel points are removed


def test_terms_drop_filler_words():
    assert T._terms("What does Judaism say about honoring parents?") == ["honoring", "parents"]
    assert T._stems(["welcoming", "guests"]) == ["welco", "guests"]


def test_credit_states_the_real_source():
    assert "Sefaria" in T.credit("sefaria", "text")
    assert "machine translation by Dicta" in T.credit("dicta", "text")
    assert "AI-assisted" in T.credit("gemini-3-flash", "text")
    assert "not recorded" in T.credit(None, "text") and "not recorded" in T.credit("unknown", "text")
    assert T.credit("sefaria", None) is None                 # no English, so nothing to credit


def test_clean_english_drops_failed_translations():
    assert T.clean_english("[[FAILED TO TRANSLATE, KEEPING ORIGINAL:]] אמר רבי") is None
    assert T.clean_english("אמר רבי עקיבא זה כלל גדול בתורה") is None
    assert T.clean_english("  Rabbi Akiva said  ") == "Rabbi Akiva said"
    assert T.clean_english("קח נא TAKE NOW: the word is a request, said Rashi.") is not None


def test_clip_respects_both_caps():
    budget = [5000]
    text, cut = T._clip("word " * 1000, budget)
    assert cut and len(text) <= T.SEGMENT_CHARS + 5 and text.endswith("[…]")
    assert budget[0] == 5000 - T.SEGMENT_CHARS                # a cut passage uses its room, not the whole budget
    assert T._clip("short", [100]) == ("short", False)
    assert T._clip(None, [100]) == (None, False)


def test_links_and_labels():
    link = T.link_for("bereishit_22_2")
    assert link.startswith("https://") and "/p/bereishit_22_2?" in link and "utm_source=yochai-plugin" in link
    assert T.link_for(None) is None
    catalog = Catalog([TextInfo("meor-einayim", "Me'or Einayim", "hasidut"), TextInfo("bereishit", "Genesis", "tanakh"),
                       TextInfo("bavli-shabbat", "Shabbat", "talmud_bavli")])
    assert T._pretty_id("meor-einayim_vayera_6", catalog) == "Me'or Einayim, Vayera 6"
    assert T._pretty_id("bereishit_22_2", catalog) == "Genesis 22:2"
    assert T._window_label([{"id": "bereishit_22_3"}, {"id": "bereishit_22_6"}], catalog) == "Genesis 22:3-6"
    assert T._window_label([{"id": "bavli-shabbat_253_13"}, {"id": "bavli-shabbat_253_15"}], catalog) == "Shabbat 127a"
