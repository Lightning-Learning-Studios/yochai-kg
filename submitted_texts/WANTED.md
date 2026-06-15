# Yochai Corpus — Help Wanted

> Auto-derived from `canonical_corpus.csv` vs. the live graph (`yochai_texts`) on 2026-06-15.
> Identified corpus: **1214** texts · Loaded in KG: **1037** · Gap: **177**.

## Tier 1 — Ready to pull (Sefaria source exists) — 37 texts

These are `MATCHED` on Sefaria but not yet built/extracted. 24 are per-section/per-book units whose **siblings are already loaded** (the pipeline is proven on the format — lowest risk); 13 are net-new standalone works. Pulling these needs no new source hunting.

### Sibling-proven units (24) — a sibling slug is already in the KG

- `hirsch-on-psalms` · commentary · R. Hirsch on Psalms — Per-book breakout from R. Hirsch parent row. Confirmed on Sefaria.
- `biur-hagra-choshen-mishpat` · halakhic_code · Beur HaGra on Choshen Mishpat — Split from biur-hagra
- `biur-hagra-even-haezer` · halakhic_code · Beur HaGra on Even HaEzer — Split from biur-hagra
- `biur-hagra-orach-chayim` · halakhic_code · Beur HaGra on Orach Chayim — Split from biur-hagra
- `biur-hagra-yoreh-deah` · halakhic_code · Beur HaGra on Yoreh De'ah — Split from biur-hagra
- `kaf-hachaim-orach-chayim` · halakhic_code · Kaf HaChaim on Orach Chayim — Split from kaf-hachaim
- `kaf-hachaim-yoreh-deah` · halakhic_code · Kaf HaChaim on Yoreh De'ah — Split from kaf-hachaim
- `netivot-hamishpat-beurim` · halakhic_code · Netivot HaMishpat, Beurim — Split from netivot-hamishpat
- `netivot-hamishpat-hidushim` · halakhic_code · Netivot HaMishpat, Hidushim — Split from netivot-hamishpat
- `pitchei-teshuvah-choshen-mishpat` · halakhic_code · Pitchei Teshuvah on Choshen Mishpat — Split from pitchei-teshuvah
- `pitchei-teshuvah-even-haezer` · halakhic_code · Pitchei Teshuvah on Even HaEzer — Split from pitchei-teshuvah
- `pitchei-teshuvah-yoreh-deah` · halakhic_code · Pitchei Teshuvah on Yoreh De'ah — Split from pitchei-teshuvah
- `shach-choshen-mishpat` · halakhic_code · Siftei Kohen on Choshen Mishpat — Split from siftei-kohen-shach
- `shach-yoreh-deah` · halakhic_code · Siftei Kohen on Yoreh De'ah — Split from siftei-kohen-shach
- `taz-choshen-mishpat` · halakhic_code · Turei Zahav on Choshen Mishpat — Split from turei-zahav-taz
- `taz-even-haezer` · halakhic_code · Turei Zahav on Even HaEzer — Split from turei-zahav-taz
- `taz-orach-chayim` · halakhic_code · Turei Zahav on Orach Chayim — Split from turei-zahav-taz
- `taz-yoreh-deah` · halakhic_code · Turei Zahav on Yoreh De'ah — Split from turei-zahav-taz
- `allegorical-interpretation` · philosophy · Allegorical Interpretation — Breakout from V1 'Philo of Alexandria – Selected Philosophical Works'.
- `on-the-creation-of-the-cosmos` · philosophy · On the Creation of the Cosmos — Breakout from V1 'Philo of Alexandria – Selected Philosophical Works'.
- `on-the-decalogue` · philosophy · On the Decalogue — Breakout from V1 'Philo of Alexandria – Selected Philosophical Works'.
- `on-the-life-of-moses` · philosophy · On the Life of Moses — Breakout from V1 'Philo of Alexandria – Selected Philosophical Works'.
- `on-the-special-laws` · philosophy · On the Special Laws — Breakout from V1 'Philo of Alexandria – Selected Philosophical Works'.
- `the-contemplative-life` · philosophy · The Contemplative Life — Breakout from V1 'Philo of Alexandria – Selected Philosophical Works'.

### Net-new standalone works (13)

- `sefer-haaruch` · commentary · Sefer HaAruch — Alphabetical dictionary of Talmudic terms
- `shita-mekubetzet-on-nedarim` · commentary · Shita Mekubetzet on Nedarim
- `tosafot-harosh-on-horayot` · commentary · Tosafot HaRosh on Horayot
- `ben-ish-chai` · halakhic_code · Ben Ish Chai — V3 author 'Yosef Chaim of Baghdad' matches V1. Structured by weekly To
- `chayei-adam-sephardic` · halakhic_code · Chayei Adam (Sephardic Reception) — Ashkenazi author but included here for its significance in the Sephard
- `ketzot-hachoshen` · halakhic_code · Ketzot HaChoshen — Commentary on Choshen Mishpat
- `maskil-le-david` · halakhic_code · Maskil le-David
- `minchat-chinuch` · halakhic_code · Minchat Chinuch — Commentary on all 613 mitzvot as enumerated in Sefer HaChinuch
- `shev-shmatata` · halakhic_code · Shev Shma'tata — Seven shma'ttot (discourses) on halakhic logic
- `eish-kodesh` · hasidut · Holy Fire
- `kinot-tisha-bav` · liturgy · Kinot for Tisha B'Av — Individual kinot as paragraph_unit within the Tisha B'Av service.
- `responsa-sheelat-yaavetz` · responsa · Responsa She'elat Ya'avetz — Ashkenazi author but included in Sephardic section for its significanc
- `teshuvot-harama` · responsa · Teshuvot HaRama

## Tier 2 — Need a source — 134 texts

`NOT_FOUND` on Sefaria. These need a contributor to supply a clean, rights-cleared bilingual source (this is where community PRs help most). Grouped by genre:


**commentary (72)**

- `birkat-shmuel` · commentary · Birkat Shmuel — Organized by Talmudic tractate
- `chok-leyisrael` · commentary · Chok LeYisrael — V3 AUTHOR ERROR: V3 listed 'Yitzchak Baruch' which is incorrect. V1 co
- `halichot-teiman` · commentary · Halichot Teiman
- `iyunim-nechama-leibowitz` · commentary · Iyunim (Studies in the Weekly Parsha)
- `maharam-lublin-on-chagigah` · commentary · Maharam Lublin on Chagigah
- `maharam-lublin-on-megillah` · commentary · Maharam Lublin on Megillah
- `maharam-lublin-on-moed-katan` · commentary · Maharam Lublin on Moed Katan
- `maharam-lublin-on-nazir` · commentary · Maharam Lublin on Nazir
- `maharam-lublin-on-nedarim` · commentary · Maharam Lublin on Nedarim
- `maharam-lublin-on-sotah` · commentary · Maharam Lublin on Sotah
- `maharam-lublin-on-taanit` · commentary · Maharam Lublin on Taanit
- `meam-loez` · commentary · Me'am Lo'ez — V3 author 'Yaakov Culi' is shorthand; V1 says 'Rabbi Yaakov Culi and s
- `meiri-on-arakhin` · commentary · Meiri on Arakhin
- `meiri-on-bekhorot` · commentary · Meiri on Bekhorot
- `meiri-on-keritot` · commentary · Meiri on Keritot
- `meiri-on-menachot` · commentary · Meiri on Menachot
- `meiri-on-temurah` · commentary · Meiri on Temurah
- `meiri-on-zevachim` · commentary · Meiri on Zevachim
- `mordechai-on-avodah-zarah` · commentary · Mordechai on Avodah Zarah
- `mordechai-on-bava-kamma` · commentary · Mordechai on Bava Kamma
- `mordechai-on-bava-metzia` · commentary · Mordechai on Bava Metzia
- `mordechai-on-beitzah` · commentary · Mordechai on Beitzah
- `mordechai-on-berakhot` · commentary · Mordechai on Berakhot
- `mordechai-on-chullin` · commentary · Mordechai on Chullin
- `mordechai-on-eruvin` · commentary · Mordechai on Eruvin
- `mordechai-on-gittin` · commentary · Mordechai on Gittin
- `mordechai-on-ketubot` · commentary · Mordechai on Ketubot
- `mordechai-on-kiddushin` · commentary · Mordechai on Kiddushin
- `mordechai-on-megillah` · commentary · Mordechai on Megillah
- `mordechai-on-moed-katan` · commentary · Mordechai on Moed Katan
- `mordechai-on-niddah` · commentary · Mordechai on Niddah
- `mordechai-on-pesachim` · commentary · Mordechai on Pesachim
- `mordechai-on-sanhedrin` · commentary · Mordechai on Sanhedrin
- `mordechai-on-shabbat` · commentary · Mordechai on Shabbat
- `mordechai-on-shevuot` · commentary · Mordechai on Shevuot
- `mordechai-on-yevamot` · commentary · Mordechai on Yevamot
- `radak-on-proverbs` · commentary · Radak on Proverbs — V2 untrusted, validated against known Radak coverage
- `ran-on-bava-batra` · commentary · Ran on Bava Batra
- `ran-on-bava-kamma` · commentary · Ran on Bava Kamma
- `ran-on-bava-metzia` · commentary · Ran on Bava Metzia
- `ran-on-chagigah` · commentary · Ran on Chagigah
- `ran-on-moed-katan` · commentary · Ran on Moed Katan
- `ran-on-niddah` · commentary · Ran on Niddah
- `ran-on-sanhedrin` · commentary · Ran on Sanhedrin
- `ran-on-yevamot` · commentary · Ran on Yevamot
- `rashba-on-chagigah` · commentary · Rashba on Chagigah
- `rashba-on-pesachim` · commentary · Rashba on Pesachim
- `rashba-on-sukkah` · commentary · Rashba on Sukkah
- `rashba-on-yoma` · commentary · Rashba on Yoma
- `rif-on-chagigah` · commentary · Rif on Chagigah
- `rif-on-horayot` · commentary · Rif on Horayot
- `rif-on-nazir` · commentary · Rif on Nazir
- `rif-on-sotah` · commentary · Rif on Sotah
- `ritva-on-bava-batra` · commentary · Ritva on Bava Batra
- `ritva-on-bava-metzia` · commentary · Ritva on Bava Metzia
- `ritva-on-beitzah` · commentary · Ritva on Beitzah
- `ritva-on-chagigah` · commentary · Ritva on Chagigah
- `ritva-on-gittin` · commentary · Ritva on Gittin
- `ritva-on-nazir` · commentary · Ritva on Nazir
- `ritva-on-shabbat` · commentary · Ritva on Shabbat
- `rosh-on-chagigah` · commentary · Rosh on Chagigah
- `rosh-on-sotah` · commentary · Rosh on Sotah
- `sefer-haaggadah` · commentary · Sefer HaAggadah (The Book of Legends)
- `shem-hagedolim` · commentary · Shem HaGedolim — Only Maarekhet Sefarim section on Sefaria (Reference/Dictionary/Shem H
- `torah-shelemah` · commentary · Torah Shelemah
- `yam-shel-shlomo-on-bava-kamma` · commentary · Yam Shel Shlomo on Bava Kamma
- `yam-shel-shlomo-on-beitzah` · commentary · Yam Shel Shlomo on Beitzah
- `yam-shel-shlomo-on-chullin` · commentary · Yam Shel Shlomo on Chullin
- `yam-shel-shlomo-on-gittin` · commentary · Yam Shel Shlomo on Gittin
- `yam-shel-shlomo-on-ketubot` · commentary · Yam Shel Shlomo on Ketubot
- `yam-shel-shlomo-on-kiddushin` · commentary · Yam Shel Shlomo on Kiddushin
- `yam-shel-shlomo-on-yevamot` · commentary · Yam Shel Shlomo on Yevamot

**halakhic_code (23)**

- `chiddushei-rabbeinu-chaim-halevi` · halakhic_code · Chiddushei Rabbeinu Chaim HaLevi — Commentary on Mishneh Torah using the Brisker analytical method
- `derech-tevunot` · halakhic_code · Derech Tevunot
- `dor-revii` · halakhic_code · Dor Revi'i on Chullin — Introduction to Tractate Chullin
- `halichot-olam` · halakhic_code · Halichot Olam
- `keneset-hagedolah` · halakhic_code · Keneset HaGedolah — Kept in halacha per dedup rules; also listed in methodology_structure 
- `kerem-chemed` · halakhic_code · Kerem Chemed — V3 AUTHOR ERROR: V3 listed 'Avraham Chai HaKohen' which is incorrect. 
- `klalei-hatalmud` · halakhic_code · Klalei HaTalmud
- `kovetz-shiurim` · halakhic_code · Kovetz Shiurim
- `maaseh-rokeach` · halakhic_code · Ma'aseh Rokeach — 69 MT commentary volumes on Sefaria under Halakhah/Mishneh Torah/Comme
- `mappah-rema` · halakhic_code · Mappah (Glosses of the Rema) — Rema glosses are interleaved in Shulchan Arukh text on Sefaria. No sep
- `mevo-hatalmud` · halakhic_code · Mevo HaTalmud — Traditionally printed at the end of Tractate Berakhot
- `nahara-upashta` · halakhic_code · Nahara u'Pashta — V3 AUTHOR ERROR: V3 listed 'Shalom Messas' which is incorrect (that is
- `netivot-hamaarav` · halakhic_code · Netivot HaMa'arav — V3 AUTHOR ERROR: V3 listed 'Various' -- V1 correctly attributes to Rab
- `pachad-yitzchak-encyclopedia` · halakhic_code · Pachad Yitzchak (Encyclopedia)
- `peri-hadash` · halakhic_code · Peri Hadash
- `peulat-tzadik` · halakhic_code · Pe'ulat Tzadik (Maharitz) — V3 author 'Yichye Tzalach (Maharitz)' is a variant spelling. V1 uses '
- `pri-megadim` · halakhic_code · Pri Megadim — Only Yoreh De'ah section on Sefaria (Halakhah/Shulchan Arukh/Commentar
- `sdei-chemed` · halakhic_code · Sdei Chemed — DEDUP: Also appears in methodology section. Kept HERE in sephardic per
- `shaarei-yosher` · halakhic_code · Sha'arei Yosher
- `yad-malachi` · halakhic_code · Yad Malachi
- `yalkut-yosef` · halakhic_code · Yalkut Yosef
- `yavin-shemua` · halakhic_code · Yavin Shemu'a — V3 AUTHOR ERROR: V3 listed 'Shlomo Adeni' which is incorrect. V1 corre
- `zera-yitzchak` · halakhic_code · Zera Yitzchak — V3 AUTHOR ERROR: V3 listed 'Yitzchak Palagi' which is incorrect. V1 co

**responsa (15)**

- `avnei-nezer` · responsa · Avnei Nezer — Structured as responsa on all four sections of Shulchan Aruch
- `kedushat-yom-tov` · responsa · Kedushat Yom Tov
- `maaseh-nissim` · responsa · Ma'aseh Nissim — V3 AUTHOR ERROR: V3 listed 'Yaakov Sasportas' which is a completely di
- `otzar-ha-ketav` · responsa · Otzar ha-Ketav
- `otzrot-chaim` · responsa · Otzrot Chaim — V3 AUTHOR ERROR: V3 listed 'Chaim Vital' which is a completely differe
- `responsa-divrei-shalom` · responsa · Responsa Divrei Shalom — V3 AUTHOR ERROR: V3 listed 'Shalom Messas' which is incorrect. V1 corr
- `responsa-ginat-veradim` · responsa · Responsa Ginat Veradim
- `responsa-ish-matzliach` · responsa · Responsa Ish Matzliach
- `responsa-mayim-chaim` · responsa · Responsa Mayim Chaim — V3 author 'Yosef Mashash' is a variant spelling of V1's 'Rabbi Yosef M
- `responsa-yaskil-avdi` · responsa · Responsa Yaskil Avdi
- `shemesh-umagen` · responsa · Shemesh uMagen
- `shut-zera-emet` · responsa · Shu't Zera Emet
- `teshuvot-harashba` · responsa · Teshuvot HaRashba — Parts I, IV-VII + Meyuchas on Sefaria under Responsa/Rishonim/Rashba/.
- `teshuvot-harif` · responsa · Teshuvot HaRif
- `yabia-omer` · responsa · Yabia Omer

**philosophy (9)**

- `comprehensive-guide-servants-of-god` · philosophy · A Comprehensive Guide for the Servants of God — Also known as Kitab Kifayah al-Abidin. Composed in Judeo-Arabic.
- `goral-la-adonai` · philosophy · A Lot for the Lord
- `iggeret-tsarfati` · philosophy · Iggeret — V3 AUTHOR ERROR: V3 listed 'Various' which is incorrect. V1 correctly 
- `israel-and-humanity` · philosophy · Israel and Humanity — DEDUP: Kept here in jewish_thought per plan (not in sephardic section)
- `mishle-asaf` · philosophy · Proverbs of Asaf
- `mishnat-r-aharon` · philosophy · Mishnat R' Aharon
- `sefer-habrit` · philosophy · Sefer HaBrit — Ashkenazi author but included here for its deep influence in Sephardic
- `shalom-yerushalayim` · philosophy · Shalom Yerushalayim — V3 AUTHOR ERROR: V3 listed 'Yisrael Moshe Hazzan' which is a different
- `the-conciliator` · philosophy · The Conciliator — Originally written in Spanish.

**liturgy (6)**

- `liturgical-poetry-ibn-gabirol` · liturgy · Liturgical Poetry of Shlomo ibn Gabirol
- `machzor-shalosh-regalim` · liturgy · Machzor for Shalosh Regalim — Uses Holiday as spine_item since it covers three distinct pilgrim fest
- `piyyutim-eleazar-kalir` · liturgy · Piyyutim of Eleazar Kalir — Kalir's dating is debated (some place him earlier); classified per V1 
- `poetry-yehuda-halevi` · liturgy · Poetry of Rabbi Yehuda Halevi — Merged from liturgical-poetry-yehuda-halevi + diwan-yehuda-halevi-secu
- `shir-yedidut-bakashot` · liturgy · Shir Yedidut (Bakashot)
- `siddur-harashash` · liturgy · Siddur HaRashash (Nahar Shalom)

**kabbalah (5)**

- `abir-yaakov` · kabbalah · Abir Yaakov
- `hemdat-yamim` · kabbalah · Hemdat Yamim
- `leshem-shevo-vachlamah` · kabbalah · Leshem Shevo V'Achlamah
- `minchat-yehuda` · kabbalah · Minchat Yehuda — V3 author 'Yehuda Fetaya' is a variant spelling of V1's 'Rabbi Yehuda 
- `zohorei-chama` · kabbalah · Zohorei Chama — V3 AUTHOR ERROR: V3 listed 'Chaim Azulai' which is incorrect. V1 corre

**poetry (3)**

- `diwan-ibn-gabirol` · poetry · Poetry of Shlomo ibn Gabirol (Diwan) — Only Azharot on Sefaria (Liturgy/Piyyut/Azharot of Solomon ibn Gabirol
- `poetry-dunash-ben-labrat` · poetry · Poetry of Dunash ben Labrat
- `poetry-moshe-ibn-ezra` · poetry · Poetry of Moshe ibn Ezra

**mussar (1)**

- `qanun-al-nisa` · mussar · The Canon for Women

## Not work items — 6 aggregate parent rows

These `SPLIT` rows are **parent aggregates**; the pipeline loads their per-section children (listed under Tier 1), not the parent itself. Do not submit these as texts:

- `biur-hagra` — Covers all four sections of the Shulchan Aruch
- `kaf-hachaim` — aggregate row; load children instead
- `netivot-hamishpat` — Commentary on Choshen Mishpat; frequently studied alongside Ketzot HaChoshen
- `pitchei-teshuvah` — Covers Yoreh De'ah, Even HaEzer, and Choshen Mishpat
- `siftei-kohen-shach` — Covers primarily Yoreh De'ah and Choshen Mishpat
- `turei-zahav-taz` — Covers primarily Yoreh De'ah and Orach Chaim
