# Claude directory submission: Yochai: Jewish Texts

Status: draft, ready to paste after the items in "Before you submit" are done.

Alex performs one step: he opens the form, pastes these fields and presses Submit. The form needs a paid Claude plan.

## Before you submit

| Item | State |
| --- | --- |
| The pull requests are merged, and the public repository holds the plugin | Open |
| The production server answers at its final address | Open. The address goes in `https://mcp.yochai.wiki/mcp` below. |
| The pages `/privacy`, `/terms` and `/support` are reviewed and live | Open. Legal text needs Alex's review. |
| The support email address exists and someone reads it | To confirm |
| The icon file is final | To confirm |
| Each community author has agreed in writing | Not needed for this submission. A named author's skills stay off the shelf until that author agrees. |

## Click path

1. Open https://claude.ai/directory/manage and sign in with the Lightning Studios account.
2. Choose **Submit**, then **MCP connector**. Paste the fields from Part 1.
3. Choose **Submit** again, then **Plugin bundle**. Paste the fields from Part 2. Use the same server address.
4. Read the summary screen and press **Submit for review**.

The connector and the plugin bundle are two entries in the same form. Submit the connector first, because the plugin bundle points at it.

## Part 1: MCP connector

An MCP connector is the server that gives Claude its tools.

| Field | Limit | Value | Count |
| --- | --- | --- | --- |
| Name | 100 | Yochai: Jewish Texts | 20 |
| One-line description | 200 | Search and read the Jewish library: Torah, Talmud, Midrash, law, philosophy and mysticism, in Hebrew and English, with commentaries and this week's portion. | 156 |
| Server address | https only | `https://mcp.yochai.wiki/mcp` | |
| Transport | | Streamable HTTP | |
| Authentication | | None (`none`). The server is open and has rate limits. | |
| Test account | | None needed. The server has no sign-in. | |
| Publisher | | Lightning Studios | |
| Category | | Education (or the nearest choice on the form) | |
| Documentation address | | https://github.com/Lightning-Learning-Studios/yochai-kg/blob/main/plugin/README.md | |
| Privacy policy address | | `https://mcp.yochai.wiki/privacy` | |
| Terms address | | `https://mcp.yochai.wiki/terms` | |
| Support contact | | support@lightningstudios.ai (to confirm) | |
| Icon | | `plugin/assets/icon.png` (to confirm) | |

### Long description (limit 2,000 characters)

```text
Yochai brings the Jewish library into your conversation with Claude. Ask a question in plain words and Claude answers from real passages, in Hebrew and English, each with its reference and a link to the full text.

What you can do:
- Ask what the sources say about any topic, story or idea.
- Look up an exact passage, such as Genesis 22:2 or Berakhot 2a.
- Read the classical commentators on a verse.
- Get this week's Torah portion and today's page of Talmud.
- Follow an idea across 3,000 years, and see who agrees and who disagrees.
- Get a short study plan that puts the sources in a sensible order.

The library holds more than 1,000 works: Tanakh, Mishnah, Talmud, Midrash, codes of Jewish law, philosophy, Mussar, Kabbalah and Hasidic teaching. A map of about 17,600 concepts connects them, so Claude can tell you what to read first and which texts answer each other.

Yochai is free and needs no account. It is a study aid, not a rabbinic authority, and it gives no rulings on Jewish law.

Yochai is made by Lightning Studios with Gratz College and is supported by the Maimonides Fund.
```

Count: 1,094 characters.

### Example prompts for the listing

1. What does Jewish tradition say about forgiving someone who never apologised?
2. What is this week's Torah portion, and what is one big question in it?
3. Show me Genesis 22:2 with Rashi's comment.

### Tools

Every tool only reads. Every tool carries a title, `readOnlyHint: true` and `destructiveHint: false`. No tool runs a free-form query. This table must match the final server before submission (to confirm against the merged code).

| Tool | Title | What it does | Reads only |
| --- | --- | --- | --- |
| `search_passages` | Search Jewish texts | Searches by meaning across more than 1,000 texts and returns real passages in Hebrew and English with their reference, translation source and a link. | Yes |
| `get_passage` | Read a passage | Returns the exact text in Hebrew and English with a link. Accepts a single verse, a range such as 'Genesis 22:1-19', a whole chapter, or a Talmud page. | Yes |
| `get_commentaries` | Read commentaries on a passage | Returns the commentators' own words and the list of every commentator available on that passage. | Yes |
| `get_cross_references` | Find linked passages | Returns the linked passages with a short excerpt and a count of links by kind. | Yes |
| `get_talmud_discussion` | Map a Talmud discussion | Covers the Babylonian Talmud. | Yes |
| `search_concepts` | Search ideas in Jewish thought | Returns matching concepts with a one-line definition and an id for the other concept tools. | Yes |
| `get_concept` | Explain a concept | Returns the definition, the question the concept answers, its key insight, its historical span and the closest related concepts. | Yes |
| `get_related_concepts` | Find related concepts | Returns concepts linked to the given one, each with the kind of link. Pass relation CONTRADICTS for opposing views. | Yes |
| `get_learning_path` | Plan what to learn first | Returns the concepts to learn first and the concepts this one leads to. | Yes |
| `get_concept_sources` | Read the sources behind a concept | Returns the passages that ground it, in Hebrew and English, drawn from different texts where possible. | Yes |
| `browse_themes` | Browse the map of Jewish thought | Returns the 11 great themes of the tradition, then the groups inside a theme, then the concepts inside a group. | Yes |
| `list_texts` | List the texts in the library | Returns titles with author, era and category, and the count of texts in every category. | Yes |
| `get_study_path` | Get a guided path through a text | Returns the ordered steps of that text's study path: the idea of each step, a summary and its anchor quote. | Yes |
| `get_jewish_calendar` | Check the Jewish calendar | Returns all four for the given date, with references that get_passage accepts. | Yes |
| `list_skills` | List Yochai study skills | Returns the study skills on the shelf: the core Yochai skills and the community skills approved through Yochai Create, each with its author. | Yes |
| `load_skill` | Open a Yochai study skill | Returns the full text of that skill: a study method, with its author and licence. | Yes |

### Notes for the reviewer

```text
- No sign-in. The server is open, read-only and rate limited per network address.
- Every tool is read-only. There is no write tool and no general query tool.
- Tool descriptions describe the tool. They contain no instructions to Claude.
- Errors are plain sentences that say what to change, for example "No passage found for 'Genesis 99:1'. Genesis has 50 chapters."
- list_skills and load_skill return study guides from our public repository. A team member reviews and merges each one by pull request. The server does not fetch skill text from any other place.
- Texts are shown under Yochai's display licences, with the source of each translation credited in the result.
```

## Part 2: Plugin bundle

A plugin bundle is the folder of skills that tells Claude how to use the tools well.

| Field | Limit | Value | Count |
| --- | --- | --- | --- |
| Plugin name | lowercase, hyphens, permanent | `yochai-jewish-texts` | 19 |
| Display name | 100 | Yochai: Jewish Texts | 20 |
| One-line description | 200 | Study Torah, Talmud and more with real sources: find a passage, prepare to teach, follow the weekly portion, or learn with a study partner. | 139 |
| Repository | public GitHub | https://github.com/Lightning-Learning-Studios/yochai-kg | |
| Path in the repository | | `plugin/` (to confirm against the merged layout) | |
| Licence | | Apache-2.0 | |
| MCP server address | same as Part 1 | `https://mcp.yochai.wiki/mcp` | |
| Privacy, terms, support, icon | | Same as Part 1 | |

Long description: use the Part 1 text, and add this paragraph at the end.

```text
The plugin adds 9 skills: find a source, this week's portion and today's page, explain a passage, prepare to teach, practical law with sources, holiday preparation, study partner mode with six reading lenses, build a course, and a shelf of community skills that grows as the Yochai community adds to it.
```

Count with this paragraph: 1,399 characters.

### Checks the bundle passes

| Requirement | How we meet it |
| --- | --- |
| Public GitHub repository | The `yochai-kg` repository is public |
| README of 40 words or more | `plugin/README.md` |
| Licence file | Apache-2.0 |
| Server address uses https | Yes |
| No credentials in the bundle | The server needs none |
| Each file under 256 KiB | Checked by the automated tests |
| `claude plugin validate --strict` | Passes in the automated tests |

## The one step Alex performs

Open https://claude.ai/directory/manage, paste Part 1 and Part 2, and press **Submit for review**.

If the review stalls for more than 10 working days, write to mcp-review@anthropic.com for the connector or directory@anthropic.com for the listing.
