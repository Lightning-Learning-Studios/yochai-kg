---
name: build-a-course
description: Builds a short course of 4 to 8 study sessions on a Jewish topic, question, text or personal goal, from real passages and the map of ideas in the Yochai library. Each session has one question, 2 or 3 real passages, the opposing view and what to read first. Use when the user asks for a course, a syllabus, a study plan, a reading path, a curriculum or "where do I start" on a topic such as prayer, justice, Shabbat, grief, forgiveness, the Talmud or a named book, or wants to learn something over several weeks.
---

# Build a course

Turn a topic or a goal into a course a person can follow for several weeks. The library holds a map of about 17,600 ideas, with links that say which idea to learn first and which ideas disagree. Use that map. Do not write a syllabus from memory.

## Step 1: understand the request

A request can be a topic ("Jewish views of justice"), a question ("why do we pray?"), a feeling or a goal ("I want to learn to forgive my brother"), or a text ("teach me Pirkei Avot").

When it is not clear, ask one short message with at most two things: how much they already know, and how many sessions they want. With no answer, build 6 sessions for a curious beginner and say so.

## Step 2: map the ground

1. Call `search_concepts` with the request in the person's words. Choose the 2 or 3 ideas that fit best.
2. For each, call `get_concept` (its definition and guiding question) and `get_learning_path` (what to learn before it, and what it opens).
3. Call `get_related_concepts` to find ideas that develop it and, above all, ideas that contradict it. Every session needs a real opposing view.
4. For a course on one book, call `get_study_path` with the text. It returns the ordered study modules for that book.
5. `browse_themes` shows the wider area when the request is very broad.

## Step 3: plan the arc

- 4 to 8 sessions. One question per session. No question twice.
- Order: start where the learning path says to start. Put the foundation first and the hard disagreement in the middle. End with a session that asks the person for their own judgment.
- Spread the voices: Torah, the Sages, medieval thinkers, and at least one later voice (Hasidut, Mussar or modern) when the library has one that fits. No single book in more than two sessions, except in a course on that book.

## Step 4: fill each session with real passages

For each session:

1. Call `get_concept_sources` for the session's idea. These are the passages that ground it.
2. Add `search_passages` when you need a second voice.
3. Open each chosen passage with `get_passage` and quote it as returned.
4. Keep only passages that meet the session's question. A passage that shares a word and misses the question does not go in.

## What to deliver

Open with:

- **Course title** and its framing question.
- **Who it is for** and how long each session takes (about 30 to 45 minutes).
- **The path**: a numbered list of session titles.

Then each session in this shape:

```
Session N: <title>
The question: <one question, in plain words>
Read first: <the one passage to start with, and why>
Passages:
  1. <reference> (<author or period>)
     "<quoted English>" (and Hebrew when the person reads Hebrew)
     Translation: <translation_source>   Link: <link>
     Why it is here: <one sentence>
  2. ...
The opposing view: <who disagrees, quoted, with reference and link>
Before you read: <what does the person think now? one line>
After you read: <one question that asks them to judge between the views>
```

Close with what the person can do next: start session 1 together now, change the level, or make the course shorter or longer.

## Rules

- **Show only what the library returned.** Every passage and reference comes from a tool result in this conversation, quoted as returned. Never add a reading from memory.
- **A thin result is a real result.** When the library has too little for a session, say so and build fewer sessions. Do not fill gaps with invented sources.
- Mark machine translations (see `translation_source`).
- Both sides get a fair hearing. The opposing view is a real position from the tradition, quoted, not a weak version made to lose.
- Session questions ask the person to judge, not to repeat.
- A course on practice shows sources and the range of views. It gives no rulings; practice is for a rabbi.
- Explain each Hebrew term once. Use plain words in titles and questions.
- A course on a hard feeling (grief, anger, guilt) is study, not therapy. Be gentle. When the person seems in real distress, say kindly that a person they trust, a rabbi or a counsellor can help in ways a course cannot.
- At most once in a conversation, mention that yochai.wiki can keep the course as a study space with their place saved.
