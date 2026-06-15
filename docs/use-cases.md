# Use cases — worked conversations

This is a companion to the [README](../README.md): a dozen real conversations you can have
with an agent connected to the Yochai Open KG. Each one shows the **prompt** you'd type, a
**sketch of the tool calls** the agent makes, and **what comes back**. They span every kind of
user — a curious 10-year-old, an educator, a Rabbi, a researcher, a developer.

These are illustrations, not transcripts; exact tool arguments and results depend on the live
graph. The tools and skills named here are real — see [quickstart-mcp.md](./quickstart-mcp.md),
[schema.md](./schema.md), and [`/skills`](../skills/README.md).

Everything an agent returns is **derived study material with a link to the source**. It's a
chavruta, not a posek — verify against the primary text. ([disclaimer](./disclaimer.md))

---

## 1. A 10-year-old asks: what does the Torah say about being kind to animals?

**Prompt:** *"What does the Torah say about being kind to animals? Find me two real sources and
explain them like I'm 10."*

**Tool calls:**
- `search_corpus("kindness to animals, not causing them suffering")` → ranked bilingual passages
- `lookup_passage(...)` on the two strongest hits to get exact text + citation

**What comes back:** Two real passages (for example, one about sending away the mother bird
before taking the eggs, and one about not muzzling an ox while it works), each in Hebrew and
English, with a plain-language explanation and a link to read more. The agent never invents a
verse — if it can't find one, it says so.

---

## 2. Compose a dvar torah on Korach

**Prompt:** *"Load the dvar-torah skill from yochai-kg and write me a dvar torah on Parshat Korach
about the line between holy disagreement and destructive rebellion."*

**Tool calls (via the [`dvar-torah`](../skills/dvar-torah) skill):**
- `search_corpus("Korach rebellion, machloket for the sake of heaven")`
- `lookup_passage("Numbers 16:1")` and neighboring verses for the narrative anchor
- `get_commentaries_on("Numbers 16:3")` for classical readings of Korach's claim
- `search_concepts("machloket l'shem shamayim")` → `get_concept` for the framing idea

**What comes back:** A short, structured dvar torah anchored on the Korach narrative, weaving in
a commentary and the "argument for the sake of heaven" concept (Avot 5:17), each claim tied to a
cited source. The synthesis is the agent's; the sources are real and linked.

---

## 3. Build a 5-source sheet on teshuvah across eras

**Prompt:** *"Load the source-sheet skill and build a 5-source sheet on teshuvah (repentance) that
spans eras — a Torah source, a Talmudic sugya, a Rishonic code, a Mussar work, and a Hasidic
teaching. Hebrew and English, with references."*

**Tool calls (via the [`source-sheet`](../skills/source-sheet) skill):**
- `list_texts(genre="Tanakh" | "Talmud" | "Halakha" | "Mussar" | "Hasidut")` to span strata
- `search_corpus("teshuvah repentance return")` within each band
- `lookup_passage(...)` to pin each chosen source exactly (e.g. *Mishneh Torah, Hilchot Teshuvah 2:1*)

**What comes back:** A ready-to-print, bilingual sheet with five sources ordered chronologically,
each with its proper reference and deep link. Open each link to verify the translation and
segmentation before teaching from it.

---

## 4. Map the prerequisites for understanding tzimtzum

**Prompt:** *"I want to understand tzimtzum. What should I learn first? Show me the prerequisite
chain and a one-line definition of each step."*

**Tool calls:**
- `search_concepts("tzimtzum divine contraction")` → `get_concept(id)` for the definition
- `get_prerequisites(id)` → the prerequisite-DAG ancestors, ordered foundational → advanced
- `get_concept(id)` on each ancestor for its `one_line_definition`

**What comes back:** A learning ladder — e.g. divine infinitude → the problem of creation from
nothing → earlier Kabbalistic groundwork → tzimtzum — each rung with a short definition. This is
the `outline` pattern; the [`outline`](../skills/outline) skill formalizes it into a study plan.

---

## 5. Find the machloket in Berakhot 2a and the concepts it touches

**Prompt:** *"Map the sugya in Berakhot 2a: its driving question, the dialectical moves, and which
canonical concepts the machloket touches."*

**Tool calls:**
- `get_talmudic_structure("Berakhot 2a")` → the `Sugya` (`driving_question`, `maskana`) and its
  `Move`s, each with `type`, `speaker`, and `stratum`
- `search_concepts("evening Shema, when the time for Shema begins")` to tie the dispute to
  canonical concepts
- `get_concept_neighborhood(id, rel_types=["CONTRADICTS","DEVELOPS"])` to see how those concepts
  relate

**What comes back:** The sugya's opening question (*from when may one recite the evening Shema?*),
its sequence of dialectical moves and resolution, and the canonical concepts the dispute engages —
a structural skeleton of the daf. Confirm against the Gemara itself before relying on it.

---

## 6. Trace every commentary on the Akeida verse

**Prompt:** *"Show me every commentary indexed on Genesis 22:2, and the concept it most anchors."*

**Tool calls:**
- `get_commentaries_on("Genesis 22:2")` → the commentary passages linked to that verse
  (`CONNECTS_TO {kind:'comments_on'}`)
- `search_concepts("akedah, the binding of Isaac, test of faith")` → `get_concept(id)`

**What comes back:** The indexed commentaries on the verse, in Hebrew and English with references,
plus the canonical concept they cluster around. Useful for seeing the range of classical readings
at a glance — then follow each link to the full commentary.

---

## 7. Trace how a concept develops, across centuries

**Prompt:** *"Take the concept of bechira chofshit (free will). Show me how it DEVELOPS and what it
CONTRADICTS or RESONATES with, and place it chronologically."*

**Tool calls:**
- `search_concepts("free will, bechira chofshit")` → `get_concept(id)`
- `get_concept_neighborhood(id, rel_types=["DEVELOPS","CONTRADICTS","RESONATES"])`
- `get_temporal_neighbors(id)` over the `TEMPORAL_PRECEDES` ordering
- `get_concept_sources(id)` to read the passages behind the concept

**What comes back:** A small typed network around free will — the ideas it grows out of, the
tensions it sits in (e.g. with divine foreknowledge), and where it falls chronologically — each
node grounded in retrievable sources. A research-grade view of one idea's life in the tradition.

---

## 8. Navigate the thematic map (the Atlas, in tools)

**Prompt:** *"Give me the 11 galaxies and their great questions, then open one constellation and
show me its fundamental question and entry-point concept."*

**Tool calls:**
- `list_galaxies()` → the 11 galaxies with their `great_question`
- `browse_constellation(constellation_id)` → its `fundamental_question`, member concepts, and
  `ENTRY_POINT` concept

**What comes back:** The same map you can see in the live [Atlas
preview](https://yochai.lightningstudios.ai/knowledge-graph-preview), but as data your agent can
reason over — a way to wander the tradition top-down, from great questions to a single idea.

---

## 9. Walk a learning corridor for a text

**Prompt:** *"Is there a built learning sequence for Pirkei Avot? Walk me through it module by
module."*

**Tool calls:**
- `get_corridors_for_text("pirkei-avot")` → available corridors for the text
- `get_corridor(id)` → the ordered `CorridorModule`s, each with a `concept_name` and an
  `anchor_quote`

**What comes back:** A guided sequence through the text, concept by concept, each module anchored
on a real quote with its source. A scaffolded path for self-study or for designing a class.

---

## 10. Mine the entity layer (researcher)

**Prompt:** *"Find every passage where the entity 'Hillel' is mentioned, then show his
entity-to-entity relations within the texts."*

**Tool calls:**
- `search_entities("Hillel", entity_type="person")` → the matching `Entity` node(s)
- `get_entities_in_passage(su_id)` on a passage to see who/what else it mentions
- `get_related_entities(entity_id)` for `DEVELOPS` / `CONTRADICTS` / `EXEMPLIFIES` /
  `APPLIES_TO` / `CONTEXTUALIZES` links

**What comes back:** Passages featuring Hillel and his web of related entities across the corpus.
A reminder from the [schema](./schema.md): the 2.57M-entity layer is **LLM-extracted at scale** —
rich for discovery, but evidence rather than adjudicated truth. Sample and verify.

---

## 11. A grounded research brief on a hard question

**Prompt:** *"Load the research skill and give me a multi-source brief on how the tradition treats
the tension between justice (din) and mercy (rachamim)."*

**Tool calls (via the [`research`](../skills/research) skill):**
- `search_concepts("midat ha-din, midat ha-rachamim, justice and mercy")` → `get_concept`
- `get_concept_neighborhood(id, rel_types=["CONTRADICTS","RESONATES","DEVELOPS"])`
- `search_corpus(...)` and `lookup_passage(...)` to anchor each claim in a real passage
- `get_concept_sources(id)` for the passages behind the concept

**What comes back:** A structured brief that lays out the tension, the major voices, and the
concepts that mediate it — every claim cited, gaps acknowledged honestly. Synthesis by the agent;
sources real and linked.

---

## 12. Build product on the gateway (developer)

**Prompt:** *"Sketch how I'd build a 'verse-of-the-day with three commentaries' feature using
yochai-kg."*

**Tool calls the feature would make:**
- `lookup_passage("<today's verse reference>")` for the base text
- `get_commentaries_on("<that reference>")` for the commentary layer
- optionally `get_entities_in_passage(su_id)` to tag people/themes for navigation

**What comes back:** A blueprint: the gateway hands back bilingual text, real commentaries, and
deep links — no database credentials, all read-only. Wrap it in your UI, cite every source, and
respect the [licensing and disclaimer](./disclaimer.md). For repeatable agent output inside your
product, ship a [skill](../skills/README.md) instead of ad-hoc prompts.

---

> Want to add a use case? These map naturally onto skills. If you find a conversation worth
> repeating, turn it into a recipe in [`/skills`](../skills/README.md) and open a PR — see
> [CONTRIBUTING.md](../CONTRIBUTING.md).
