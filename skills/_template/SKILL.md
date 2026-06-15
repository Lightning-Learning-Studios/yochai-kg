# <Skill Title>

## Purpose

<One or two sentences. What does this skill produce, and what does good output
look like? Lead with the deliverable, not the mechanism.>

## When to use

- <Trigger: the kind of request that should load this skill.>
- <Another trigger, if any.>
- **Not for:** <when an agent should reach for a different skill instead.>

## MCP tools used

<List only the gateway tools this skill actually calls, with a half-line on the
role each plays here. Reference real tools by name — do not invent tools.>

- `search_corpus(query, text_filter?, limit?)` — <role in this skill>
- `lookup_passage(reference)` — <role in this skill>
- `<other tools as needed>`

## Method

<Numbered steps. Every step that touches the corpus names a real tool call with
example arguments. Keep the staged shape: gather → cross-reference → synthesize.>

1. **<Step name>.** <What you do.> Call:
   `search_corpus(query="<example>", text_filter="<example-slug-or-omit>")`.
2. **<Step name>.** <What you do, and what you do with the result.>
3. **Synthesize.** <How the retrieved material becomes the deliverable. Cite
   every source by its proper reference; assert nothing the tools didn't return.>

### Retry budget

<State a concrete stopping rule so the agent doesn't loop. E.g. "2 attempts per
source; if both miss, omit and disclose by name.">

## Output format

<The exact shape of the deliverable: prose, a structured list, an ordered
sequence. Show the skeleton.>

## Worked example

**Request:** <a short, concrete user ask>

1. <tool call with real arguments> → <what came back, in one line>
2. <tool call> → <result>
3. <synthesis>

**Result (sketch):**

> <2–4 lines showing the shape of the output, with a cited reference or two.>

## Notes / limits

- <Honesty rule: what to do when a source isn't indexed.>
- <Scope limit: what this skill does *not* do — e.g. not a posek; not a ruling.>
- <Any voice note: cite by proper reference; don't narrate process.>
