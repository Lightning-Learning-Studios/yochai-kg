# Evaluation suite

These cases check that the plugin's skills do their job. Each case is a folder with a prompt and its graders.

Run the full suite from the repository root:

```
claude plugin eval ./plugin --judge-model sonnet
```

Run one case, once, to check a change quickly:

```
claude plugin eval ./plugin --case find-a-source --runs 1 --ablation none --no-publish
```

The runs use real model calls on your own account. A full run is 14 cases, 3 runs each, with and without the plugin.

## What the cases cover

| Case | Skill | What it checks |
| --- | --- | --- |
| `find-a-source` | Find a source | The real verse, in Hebrew and English, with a reference and a link |
| `find-a-source-not-found` | Find a source | An honest "not found", and no invented citation |
| `weekly-portion` | Weekly portion | The portion comes from the calendar tool, with a real passage |
| `daf-yomi` | Weekly portion | Today's Talmud page, explained for a beginner |
| `explain-a-passage` | Explain a passage | The text, the difficulty, and the real commentary |
| `prepare-to-teach` | Prepare to teach | A source sheet a teacher can use |
| `practical-law` | Practical law | Sources and the range of views, no ruling, no refusal |
| `holiday-prep` | Holiday preparation | The root source and something for the family |
| `study-partner` | Study partner | The text, one observation, one question |
| `build-a-course` | Build a course | 4 sessions, each with a question, passages and an opposing view |
| `skill-shelf` | Skill shelf | Reads the live shelf and credits authors |
| `neg-off-topic` | none | A coding request does not start the plugin |
| `neg-binding-ruling` | Practical law | A demand for a ruling on a health matter gets care and sources, not a ruling |
| `neg-hateful-use` | none | A request to use the texts against a group is declined |

## The stand-in server

The cases do not call the real Yochai server. The folder `mocks/yochai/` describes a stand-in that answers each tool call. The file `_tools.json` there is a copy of the tool list.

When the tool list on the real server changes, save the new list to `mocks/yochai/_tools.json` and update `_server.md` to match.
