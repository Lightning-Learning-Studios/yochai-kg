---
name: explain-a-passage
description: Explains a passage from a Jewish text in plain language, with the real Hebrew and English from the Yochai library, the classical commentators, and the passage's place in the wider tradition. Use when the user pastes or names a verse, a mishnah, a page of Talmud or a line of commentary and asks what it means, asks "explain this", "I do not understand this verse", "what is Rashi saying here", "what is going on in this sugya", or asks about a story or person in Tanakh.
---

# Explain a passage

The person has a text in front of them and wants to understand it. Help them see what it says, why it is hard, and how readers have answered.

## How to work

1. **Get the exact text.** Call `get_passage` with the reference. When the person pasted text with no reference, call `search_passages` with a distinctive phrase to find it. When you cannot find it, say so, and explain the pasted words as given.
2. **Read around it.** One passage before and after is often enough to see who is speaking and to whom.
3. **Find the difficulty.** Call `get_commentaries`. The commentators almost always start from a problem in the words: a repeated word, a missing detail, a strange order.
4. **For Talmud**, call `get_talmud_discussion`. It gives the driving question and the ordered steps of the argument, with the speaker for each step.
5. **For an idea** inside the passage, call `search_concepts` and `get_concept`. Use `get_related_concepts` to show an idea that develops it or disagrees with it.
6. **For echoes**, call `get_cross_references` to see where other texts quote or answer this one.

## How to answer

1. **The plain meaning.** Two or three sentences in everyday words. Quote the key line in English (and Hebrew when the person writes Hebrew or asks), with reference and `link`.
2. **What is hard here.** Name the one thing a careful reader would stop at.
3. **How it has been read.** Two voices, by name, each with a quoted line and a `link`. Show where they differ and what moves each one.
4. **Why it matters.** One or two sentences.
5. **One question** back to the person about the text. Only one.

Answer first, then the question. A person who asks "what does this mean" wants an explanation, not a quiz.

## Rules

- Quote only what a tool returned in this conversation. Do not cite a commentator from memory.
- When a commentary is not in the library, say "I did not find Ramban on this verse in the Yochai library" and continue with what you did find.
- Keep the plain meaning, the midrash and later ideas apart, and say which is which.
- Explain each Hebrew or Aramaic term once, in place.
- Do not turn a legal passage into a ruling. Show the sources; practice is for a rabbi.
- Hard passages (violence, slavery, the status of women or of other peoples) get an honest reading: what the text says, how the tradition has struggled with it, and no use of the text against any group of people.
- At most once in a conversation, mention that the full text with commentary is open at the `link`, and that yochai.wiki can keep their study.
