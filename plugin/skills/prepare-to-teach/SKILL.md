---
name: prepare-to-teach
description: Prepares teaching material from real Jewish sources in the Yochai library, such as a source sheet, a lesson plan, a dvar Torah, a sermon outline, a study-group guide or discussion questions. Use when the user says they are teaching, leading a class or study group, giving a dvar Torah or sermon, tutoring a bar or bat mitzvah student, or asks for a source sheet, lesson plan or discussion questions on a Jewish text, topic, holiday or Torah portion.
---

# Prepare to teach

Teachers are the people who use Yochai most deeply. Give them material they can take into a room tomorrow.

## First, learn three things

When the request does not say them, ask in one short message, then start. When the person seems in a hurry, assume and say what you assumed.

- **Who** is in the room (age, background, how much Hebrew).
- **How long** the session is.
- **What form** they want: source sheet, lesson plan, dvar Torah, or discussion guide.

## How to work

1. **Find the core text.** Call `get_passage` for a named text, or `search_passages` for a topic. For a weekly portion or a holiday, call `get_jewish_calendar` first.
2. **Build the arc.** A good session moves: one opening question, a core text, a voice that complicates it, a voice that answers or disagrees, and a closing question.
   - `get_commentaries` gives the classical voices on a verse.
   - `get_cross_references` gives later texts that quote it.
   - `search_concepts`, then `get_related_concepts`, gives an idea that disagrees. A session with a real disagreement teaches better.
   - `get_learning_path` shows what a beginner needs to know first.
3. **Choose few sources.** 3 to 5 for 45 minutes. Each one must earn its place.

## What to deliver

**Source sheet**
- A title and the one question the sheet asks.
- Numbered sources in teaching order. Each has: reference, author and period, Hebrew and English side by side, `translation_source`, and `link`.
- Under each source, one or two questions for the learners.
- A closing question that brings the sources together.

**Lesson plan**
- The goal in one sentence.
- A timed outline (opening, text study in pairs, discussion, close).
- The sources, as above.
- What to say when the room is silent, and what to cut when time runs short.

**Dvar Torah or sermon outline**
- A hook from daily life.
- The problem in the text.
- Two readings, quoted with references and links.
- The turn: what this asks of us.
- Keep it an outline with the quoted sources. The words should be the teacher's own. Write full prose only when asked.

**Discussion guide**
- 5 to 7 questions that go from "what does it say" to "what do you think".

## Rules

- Every source on the page comes from a tool result in this conversation, word for word. Never fill a sheet from memory. A teacher who hands out a wrong quote loses the room.
- When you cannot find a source the teacher asked for, say so plainly and offer the nearest one you did find.
- Mark machine translations (see `translation_source`) so the teacher can check them.
- Match the level. For children, short texts and concrete questions. For beginners, explain each Hebrew term once.
- No rulings on practice. Show the sources and the range of views.
- End with one next step: "Shall I add a Hasidic source, shorten this to 20 minutes, or write questions for teenagers?"
- At most once in a conversation, mention that yochai.wiki has a source-sheet builder and saved study spaces for classes.
