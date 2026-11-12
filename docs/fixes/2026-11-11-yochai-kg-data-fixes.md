# Data fixes of 11–12 November 2026

The graph behind this gateway was repaired in four places. Every change was written so it can be undone,
was tested on a sample first (apply → roll back → compare → apply again), and was checked against Yochai's own
retrieval code before and after. This page says what changed for people who query the graph. The internal
record (backups, rollback commands, job ids) lives in the private pipeline repository.

## 1. Sugya daf labels (`Sugya.canonical_reference`)

**Before:** about 87% of the 16,709 Bavli sugya labels named the wrong daf, because the extraction model
wrote the amud index or the passage position as the daf ("Arakhin 10b-11a" for a sugya on 2a).

**Now:** 15,469 labels are computed from the TextUnits the sugya is `LOCATED_IN` (a TextUnit id
`<slug>_<N>_<pos>` has amud index N; daf = ceil(N/2), side a when N is odd). Changed nodes carry
`ref_fixed = '2026-11-11'`. 129 sugyot were left as they were because their ids collided at load
(for example `sugya_001` holds most of Beitzah); trust their label only if it agrees with their TextUnits.

## 2. Mention weights (`MENTIONED_IN.importance`)

**Before:** no `MENTIONED_IN` edge had a usable importance (442,225 were 0.0, the rest null).

**Now:** every edge has
- `importance` in (0, 1): an inverse-frequency weight, so an entity that names this passage's topic ranks above
  one mentioned everywhere; the median edge is 0.5;
- `idf_w`: the raw weight, log(N_su / mentions(e)) / log(1 + entities_in(su));
- `w_ver`: when it was computed.

414 passages linked to more than 300 entities carry `SemanticUnit.is_hub = true` (and `hub_reason`).
Filter them out, or weight them down, when you walk from a passage to its entities.

## 3. Re-segmented texts (passage metadata and study corridors)

**Before:** in texts that were re-cut into new passages after extraction, each passage's
`driving_question`, `key_entities`, `register`, `key_semantic_fields` and `commentary_base_ref` described another
passage, and corridor modules pointed at the wrong passages (91.6% of anchors in the affected texts were more
than three passages from their own anchor quote). 45 texts had lost their `MENTIONED_IN` edges.

**Now:** in 70 texts the metadata of 3,841 passages was moved to the passage it describes
(`meta_rekeyed = '2026-11-11'`; passages with no evidence for their metadata were blanked rather than left
wrong), 9,553 corridor modules (and the study app's corridor copy) were re-anchored (`anchor_rekeyed`; anchors far from their quote: 10.4%), 419,616
missing `MENTIONED_IN` edges were recreated, and 9,151 passage embeddings were rebuilt (`emb_fix`). 46 texts with
mixed evidence were not changed.

## 4. Entity fragmentation

**Before:** one idea was spread over several `Entity` nodes: Humility was `humility|value` (657 passages) and
`humility|concept` (640), plus per-text copies; 424,628 entities in 154 texts never joined a hub. Sefaria's
topic for the Kabbalistic Sefirah "Ḥokhma" lists "wisdom" as a form, so plain "Wisdom" (Avot 4:1, "Who is
wise?") was filed under the Sefirah.

**Now (no node deleted):**
- 43,586 duplicates (same normalized name; concept / value / theme treated as one family) were merged into their
  hub: their `MENTIONED_IN`, `EXTRACTED_FROM` and `COVERS_ENTITY` edges moved to the hub, and the old node keeps
  `merged_into = <hub entity_id>`. Humility is now one hub with 1,345 passages. Hubs list the merged names in
  `aliases` / `aliases_he`. If you hold an old entity id, follow `merged_into`.
- Passages that use a Kabbalistic term in its plain sense were moved off the Sefirah to the plain hub after a
  model read each passage (moved edges carry `sense_fix` and `moved_from`).
- 943 spelling and language variants (Yitzḥak / Yitzchak → Isaac, Rebbi Meïr → Rabbi Meir, Shlomo → King Solomon)
  were merged after a model judged each pair the same; homographs stayed apart (Judah ≠ Judea).
- Entity-to-entity relations of merged-away nodes were copied to their hubs (33,190 copies; originals stay).

## 5. Smaller fixes

- `Entity.wikidata_qid` and `Entity.sefaria_slug`: empty strings are now null (2.14M nodes), so
  `IS NOT NULL` means "has an id" (829 entities have a Wikidata QID).
- `SemanticUnit.genre`: 165,677 passages marked `unknown` now carry their text's genre (commentary,
  halakhic_code, philosophy, …).

## Properties added by these fixes

| node / edge | property | meaning |
| --- | --- | --- |
| Sugya | `ref_fixed` | label recomputed from TextUnits |
| MENTIONED_IN | `importance`, `idf_w`, `w_ver` | mention weight |
| SemanticUnit | `is_hub`, `hub_reason` | passage linked to more than 300 entities |
| SemanticUnit | `meta_rekeyed`, `emb_fix` | metadata moved / vector rebuilt |
| CorridorModule | `anchor_rekeyed` | anchor and coverage moved |
| Entity | `merged_into`, `merge_fix` | this node was merged into the named hub |
| Entity | `aliases`, `aliases_he`, `alias_fix` | names of nodes merged into this hub |
| MENTIONED_IN / EXTRACTED_FROM / COVERS_ENTITY | `merged_from`, `merge_fix` | edge moved here by a merge |
| MENTIONED_IN / EXTRACTED_FROM | `moved_from`, `sense_fix` | edge moved off a Kabbalistic sense |
| CONTRADICTS / DEVELOPS / … | `merged_from_rel`, `merge_fix` | relation copied to a hub from a merged-away node |
| Entity | `ids_fix` | empty external ids set to null |
| SemanticUnit | `genre_fix` | genre set from the text |
