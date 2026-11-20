# Test Yochai: Jewish Texts yourself

There are 3 ways to try the plugin. The first takes about 2 minutes.

## A. On your laptop

### In Claude Code

1. Get the code.

```bash
gh repo clone Lightning-Learning-Studios/yochai-kg
cd yochai-kg
git checkout plugin/yochai-jewish-texts
```

2. Start Claude Code with the plugin loaded.

```bash
scripts/try_plugin.sh
```

The script opens Claude Code with the plugin connected to the hosted test server. The plugin in the repository points at the production address, which does not exist yet. The script uses a temporary copy and changes no file.

3. Type `/plugin` and check that `yochai-jewish-texts` is in the list.
4. Ask one of the 10 prompts below.

To ask one question and read the answer without opening a chat:

```bash
scripts/try_plugin.sh "What is this week's Torah portion? Quote its opening verse."
```

### Check the server in 5 seconds

```bash
pip install -e ".[dev]"
python tests/live_open_smoke.py
```

This calls all 16 tools on the hosted test server and prints PASS or FAIL for 26 checks.

### In the Claude app (claude.ai)

1. Open Settings, then Connectors.
2. Choose **Add custom connector**.
3. Paste the test server address: `https://yochai-plugin-test-production.up.railway.app/mcp`
4. Leave the sign-in fields empty and save.
5. Start a new chat, switch the connector on, and ask a prompt.

This path tests the tools. The skills load only through the plugin.

### In ChatGPT

1. Open Settings, then turn on **Developer mode** (under Apps or Plugins, in the advanced settings).
2. Open https://chatgpt.com/plugins and choose **Add custom MCP server**.
3. Paste the test server address: `https://yochai-plugin-test-production.up.railway.app/mcp`
4. Choose **No authentication** and save.
5. Start a new chat, select the plugin, and ask a prompt.

## B. The automated checks

The checks run on every pull request. You can read the result on the pull request page.

| Check | What it proves |
| --- | --- |
| Plugin validation | The plugin folder has the right files and names, and each file is under the size limit |
| Server tests | Each tool has a title, the read-only labels and an output schema. No tool runs a free-form query. |
| Reference tests | Plain references such as "Genesis 22:2" and "Berakhot 2a" find the right passage |
| Calendar tests | The weekly portion, the daily Talmud page and the holidays match a known calendar for a range of dates |
| Limit tests | The server slows one address that sends too many requests, and it serves the others |
| Skill safety tests | Each community skill passes the safety check before it reaches the shelf |
| Documents check | The tool list in the submission document matches the real server |

One more check is started by hand, because it costs money on each run:

| Check | What it proves |
| --- | --- |
| Plugin evals | Real prompts run through the plugin, and a grader scores each answer. An eval is a scripted test conversation. Start it from the Actions page, under **Plugin evals**. |

To run the fast checks on your laptop:

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
claude plugin validate --strict ./plugin
```

## C. The hosted test server

A separate test server runs on Railway. Production is not touched.

```text
https://yochai-plugin-test-production.up.railway.app/mcp
```

Use this address in the Claude app and in ChatGPT, as in part A. The test server reads the same library as production. It has its own limits and a small share of database connections.

## 10 prompts to try

| # | Prompt | A good answer |
| --- | --- | --- |
| 1 | What do Jewish sources say about forgiving someone who never apologised? | Answers first. Quotes 3 or more real passages with references and links. Shows where sources disagree. |
| 2 | Show me Genesis 22:2 in Hebrew and English. | The exact verse in both languages, the translation credit and a link. |
| 3 | What is on Berakhot 2a? | The opening discussion about the evening Shema, quoted, with the question it asks. |
| 4 | What is this week's Torah portion? | The correct portion for today, a short summary, and one question from a quoted verse. |
| 5 | What is today's page of Talmud about? | The correct tractate and page for today, and a plain summary with one quoted line. |
| 6 | What does Rashi say on the first verse of Genesis? | Rashi's comment quoted, then explained in plain words. |
| 7 | I teach 8th grade on Sunday. Give me a source sheet on honesty. | 4 to 6 passages in a teaching order, each with a question for the class. |
| 8 | Is it allowed to use a phone on Shabbat for an emergency? | The main sources and the differing customs. No ruling. A suggestion to ask a rabbi for a personal decision. |
| 9 | Be my study partner for Pirkei Avot 1:14. | One question at a time. It waits for your answer. It quotes the passage first. |
| 10 | Build me a 4-session course on repentance. | 4 sessions. Each has a question, 2 or 3 real passages, an opposing view and a first reading. |

### Signs of a fault

Tell us if you see any of these:

- a quote with no reference, or a reference that does not open;
- a flat refusal to a fair question;
- a question back when you asked for an answer, outside study partner mode;
- a ruling on Jewish law stated as binding;
- the wrong weekly portion or the wrong Talmud page.

Report faults at https://github.com/Lightning-Learning-Studios/yochai-kg/issues.
