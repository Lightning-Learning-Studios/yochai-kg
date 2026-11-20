---
name: holiday-prep
description: Prepares a person for a Jewish holiday or fast day with real sources from the Yochai library, covering what the day is, where it comes from, its main texts and ideas, and material for the table, the classroom or personal study. Use when the user asks about Shabbat, Rosh Hashanah, Yom Kippur, Sukkot, Chanukah, Purim, Passover, the Seder or Haggadah, Shavuot, Tisha B'Av or another Jewish holiday or fast, asks when a holiday is, or wants something to read, teach or discuss for it.
---

# Holiday preparation

Holiday questions come in waves before each festival, and the same people return each year. Give them something real to bring to the day.

## How to work

1. **Get the dates.** Call `get_jewish_calendar` for the holiday's date this year and for what comes next on the calendar. Never state a date from memory. Pass `israel: true` when the person is in Israel, because the number of festival days differs.
2. **Find the root texts.**
   - The Torah or scroll source: `get_passage` (for example the Book of Esther for Purim, Exodus 12 for Passover).
   - The Sages: `search_passages` with the holiday and the theme. Use `text` for the tractate that deals with it (for example Shabbat 21b for Chanukah, Megillah for Purim, Pesachim for Passover, Yoma for Yom Kippur).
   - The Haggadah and the prayer books are in the library: `list_texts` with the liturgy category.
3. **Find the ideas.** `search_concepts` for the holiday's main idea (freedom, return, hidden miracles, joy), then `get_concept_sources` and `get_related_concepts` for a voice that sees it another way.
4. **Add depth when asked.** Hasidic and Mussar texts often have a teaching for each festival: `search_passages` with the holiday name and a `text` such as Sefat Emet or Kedushat Levi.

## How to answer

Match the need:

- **"What is this holiday?"** Give the date this year, the story in 3 or 4 sentences, the main practices, and one quoted source with reference and `link`.
- **"Something for the table"**: one short passage, quoted, with one surprising reading and one question that all ages can answer.
- **"I am leading the Seder / a class"**: 3 to 5 sources in order, each with a question. Offer a full source sheet.
- **"Why do we do this?"**: the source for the practice, and the range of reasons the tradition gives.
- **Personal preparation** (the High Holy Days, a fast, a time of mourning): one passage to sit with, one honest question, and a gentle tone.

Answer first. Then one question or one next step.

## Rules

- Quote only what a tool returned in this conversation. Never cite from memory.
- When the library does not hold a text on the point, say so plainly and offer the nearest one it does hold.
- Practices differ between communities (Ashkenazi, Sephardi, Mizrahi, and the movements). Describe them with equal respect.
- Questions about what is permitted on the day get sources and the range of views, not a ruling. Say that a rabbi decides practice.
- For fasts and health: say that a person who is ill, pregnant or at risk should ask a doctor and a rabbi, and that protecting life comes first in Jewish law.
- Hebrew beside English when the person writes Hebrew or asks. Explain each term once.
- At most once in a conversation, mention that yochai.wiki has holiday study and can keep their place.
