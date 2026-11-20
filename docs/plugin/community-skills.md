# How a Yochai Create skill reaches the plugin

A person writes a skill in Yochai Create. A Yochai reviewer approves it. If the author agrees, the skill then appears in the Yochai plugin for Claude and ChatGPT, with the author's name on it.

This page explains the path, what you must check, and how to take a skill down.

## The short version

1. A robot checks Yochai Create once a day for approved skills.
2. For each new skill, the robot opens one pull request in this repository. A pull request is a proposed change that waits for a person to accept it.
3. You read the pull request and merge it, or you close it.
4. After the merge, the server restarts by itself. The skill is then on the shelf for every user, the same day. Users do not update anything.

The robot cannot merge. A skill never reaches users without a person's decision.

## The four gates

A skill must pass all four gates, in this order.

| Gate | Who decides | What it means |
| --- | --- | --- |
| 1. Reviewer approval | A Yochai reviewer, in the Yochai app | The skill is published in Yochai Create. |
| 2. Author consent | The author, in the Yochai app | The author ticked the box that allows the skill in the open plugin, and chose a licence. |
| 3. Safety check | The robot | The skill has no hidden instructions, no outside links, no personal data, and no tools the plugin lacks. |
| 4. Human merge | You | You read the skill and accept the pull request. |

A skill with no author consent stays in Yochai Create only. The robot skips it and says why.

## What the safety check looks for

The robot blocks a skill when it finds any of these.

- Text that tells the assistant to ignore its rules, to take a new role, or to hide something from the reader.
- Text that asks the assistant to show its own hidden instructions.
- A link or a site name outside yochai.wiki and sefaria.org.
- An email address, a phone number, or something that looks like a password or a key.
- A request to collect personal data, or to send data anywhere.
- A tool the plugin does not have, or a request to run code or change files.
- Attached files, invisible characters, or embedded web code.
- A name that a core skill already uses.
- A skill larger than 60 KB (about 10,000 words).

When an Anthropic key is set for the repository, a second check runs. A Claude model reads the skill and answers "pass" or "fail" with reasons. It looks for problems that fixed rules miss, such as an off-topic skill or one that demeans a group. Without the key, the pull request says that this second check did not run.

A blocked skill gets no pull request. The author can fix the skill in Yochai Create and publish a new version. The robot then tries again the next day.

## How to review a pull request

Each pull request holds one skill file and a safety report. The title starts with "Community skill".

1. Read the safety report at the top. Make sure that the fixed rules show "Passed".
2. Read the whole skill file. Ask one question: would we be glad to see our name next to this?
3. Check that the skill does not ask the assistant to give a religious ruling or to invent a source.
4. Check the author name and the licence.
5. Try the skill once. The next section tells you how.
6. Tick the boxes in the pull request, then merge it.

If you are not sure, do not merge. Leave a comment, or close the pull request. A closed pull request does not change anything for users.

### Try a skill before you merge

You need the repository on your computer and Claude Code installed.

```bash
gh pr checkout <number>
claude --plugin-dir ./plugin
```

Then ask Claude: "Load the Yochai skill named `<skill name>` and use it." The skill name is the folder name in the pull request.

## When an author changes a skill

A new approved version produces a new pull request with the title "Community skill: update". The earlier version stays on the shelf until you merge the new one. If the new version fails the safety check, the earlier version stays and no pull request opens.

## Remove a skill

There are two ways.

**The author removes it.** The author unpublishes the skill in Yochai Create, or unticks the consent box. The next day the robot opens a pull request with the title "Community skill: remove". Merge it.

**We remove it now.** Use this when a skill causes a problem and you cannot wait.

1. Delete the skill's folder (see the table below) in a new pull request.
2. Merge the pull request. The server restarts and the skill is gone within a few minutes.
3. Ask a Yochai reviewer to unpublish the skill in Yochai Create. If the skill stays published there with consent, the robot proposes it again the next day.

## Run the robot by hand

You can try the pipeline on your computer with sample skills. This writes to a temporary folder and changes nothing in the repository.

```bash
python -m pipeline.run --fixture pipeline/fixtures/feed.json --out /tmp/yochai-shelf-test --no-model-review
```

The output has one line for each skill: `added`, `updated`, `unchanged`, `skipped`, `failed` or `removed`, with the reason.

To see what the robot would do with the real feed, without writing anything:

```bash
YOCHAI_API_URL=<address of the Yochai service> python -m pipeline.run --dry-run
```

On GitHub, open the Actions tab, choose "Community skills", and choose "Run workflow". Tick "dry run" to see the result with no pull requests.

## One-time setup

| Setting | Where | Value |
| --- | --- | --- |
| `YOCHAI_API_URL` | Repository variables | The address of the Yochai service. The robot does nothing until this is set. |
| Allow GitHub Actions to create pull requests | Repository settings, Actions, General | On |
| `ANTHROPIC_API_KEY` | Repository secrets | Optional. Turns on the second, model-based check. |

The Yochai app also needs the consent box. That change is small and is described in the proposal that came with this work. Until the app has it, every skill is skipped for "no author consent", which is the safe result.

## Reference for engineers

| Item | Location |
| --- | --- |
| Feed the robot reads | `GET {YOCHAI_API_URL}/api/methods/community` |
| Consent fields on the published version | `pluginConsent` (must be `true`), `pluginLicense` (`CC BY 4.0`, `CC BY-SA 4.0` or `CC0 1.0`) |
| Where skills are written | `shelf/community/<skill name>/SKILL.md` |
| Branch for each pull request | `community-skill/<skill name>` |
| Pipeline code | `pipeline/` (`fetch.py`, `convert.py`, `safety.py`, `run.py`, `open_prs.py`) |
| Daily job | `.github/workflows/community-skills.yml` |
| Tests | `tests/pipeline/test_pipeline.py` |
| Sample skills | `pipeline/fixtures/feed.json` |

The converter rewrites the tool names that a Yochai app skill uses into the plugin's tool names. For example, `lookup_canonical_text` becomes `get_passage`. The full table is `TOOL_MAP` in `pipeline/convert.py`.

The same feed and the same shelf always produce the same files. A second run makes no change.
