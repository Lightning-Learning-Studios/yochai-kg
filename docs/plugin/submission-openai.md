# ChatGPT directory submission: Yochai: Jewish Texts

Status: draft, ready to paste after the items in "Before you submit" are done.

Alex performs two steps himself: the business verification, and the final Submit.

## Before you submit

| Item | Owner | State |
| --- | --- | --- |
| Business verification for Lightning Studios on the OpenAI platform | Alex. It needs company documents. | Open |
| The production server answers at its final address | Claude | Open. The address goes in `https://mcp.yochai.wiki/mcp`. |
| Domain verification passes (steps below) | Claude prepares, Alex clicks Verify | Open |
| The 4 pages are reviewed and live | Alex reviews the legal text | Open |
| The demo video is recorded and has a public link | To confirm who records it | Open |
| All 8 test cases pass in ChatGPT developer mode | Claude | Open |

OpenAI does not let us change the server address after listing without contacting support. Choose the final address before you submit.

## Step 1: Business verification (Alex)

1. Open https://platform.openai.com/settings/organization/general.
2. Under **Verifications**, start the business verification for Lightning Studios.
3. Upload the company documents the form asks for.
4. Wait for the confirmation email. The publisher name on the listing must match the verified name.

## Step 2: Domain verification

1. Open https://platform.openai.com/plugins and create the plugin with the fields in Step 3.
2. Enter the server address. The form shows a verification token.
3. Set the token as the value of the server's verification setting on Railway (to confirm the setting name against the merged code).
4. Check that this address returns the exact token as plain text:

```text
https://<the server host>/.well-known/openai-apps-challenge
```

5. Press **Verify Domain**.

## Step 3: Listing fields

| Field | Limit | Value | Count |
| --- | --- | --- | --- |
| Display name | 30 | Yochai: Jewish Texts | 20 |
| Short description | 30 | Study Torah, Talmud and more | 28 |
| Publisher | verified name | Lightning Studios | |
| Category | | Education | |
| MCP server address | | `https://mcp.yochai.wiki/mcp` | |
| Authentication | | No authentication | |
| Website address | | https://www.yochai.wiki | |
| Support address | | `https://mcp.yochai.wiki/support` | |
| Privacy policy address | | `https://mcp.yochai.wiki/privacy` | |
| Terms of service address | | `https://mcp.yochai.wiki/terms` | |
| Icon | | `plugin/assets/icon.png` (to confirm) | |
| Audience | | Ages 13 and over | |

### Long description

```text
Yochai brings the Jewish library into ChatGPT. Ask a question in plain words and get an answer from real passages, in Hebrew and English, each with its reference and a link to the full text.

Ask what the sources say about a topic. Look up an exact passage, such as Genesis 22:2 or Berakhot 2a. Read the classical commentators. Get this week's Torah portion and today's page of Talmud. Follow one idea across 3,000 years and see who disagrees. Ask for a short study plan.

The library holds more than 1,000 works: Tanakh, Mishnah, Talmud, Midrash, Jewish law, philosophy, Mussar, Kabbalah and Hasidic teaching.

Yochai is free and needs no account. It is a study aid, not a rabbinic authority, and it gives no rulings on Jewish law. Made by Lightning Studios with Gratz College, supported by the Maimonides Fund.
```

Count: 812 characters.

### Starter prompts (3 at most, 128 characters each)

| Prompt | Count |
| --- | --- |
| What is this week's Torah portion, and what is one big question in it? | 70 |
| What do Jewish sources say about forgiving someone who never apologised? | 72 |
| Show me Genesis 22:2 in Hebrew and English with Rashi's comment. | 64 |

### Tool information

Every tool sets `readOnlyHint: true`, `destructiveHint: false` and `openWorldHint: false`. Every tool has a title, an output schema and the `noauth` security scheme. Every description starts with "Use this when". Give this justification for each tool when the form asks:

```text
Read-only: the tool only reads from Yochai's own library. It changes nothing.
Not destructive: there is no write, update or delete path on the server.
Not open-world: the tool reads Yochai's own database and sends nothing to outside parties.
```

The tool list is in `submission-anthropic.md`. Both listings use the same server.

## Step 4: Test cases

Run each case in ChatGPT developer mode before submitting. Tool names must match the merged code (to confirm).

### 5 positive cases

| # | Scenario | User prompt | Expected tools | Expected result |
| --- | --- | --- | --- | --- |
| 1 | Topic question | What do Jewish sources say about forgiving someone who never apologised? | `search_passages` | An answer built on 3 or more quoted passages. Each has a reference and a link. No invented source. |
| 2 | Exact passage | Show me Genesis 22:2 in Hebrew and English. | `get_passage` | The verse in Hebrew and English, the translation source, and a link. |
| 3 | Weekly portion | What is this week's Torah portion? Give me one question to think about. | `get_jewish_calendar`, then `search_passages` or `get_passage` | The correct portion for today's date, a short summary, and one question tied to a quoted verse. |
| 4 | Commentary | What does Rashi say on the first verse of Genesis? | `get_passage`, `get_commentaries` | Rashi's comment quoted with its reference, then a plain explanation. |
| 5 | Idea and study order | I want to understand teshuvah (repentance). Where do I start? | `search_concepts`, `get_learning_path`, `get_concept_sources` | A short definition, what to learn first, and 2 or 3 opening passages with links. |

### 3 negative cases

| # | Scenario | User prompt | Why the plugin does not complete it | Expected behaviour |
| --- | --- | --- | --- | --- |
| 1 | Personal ruling | My oven was used for meat an hour ago. Am I allowed to bake a dairy cake in it now? Just tell me yes or no. | The plugin gives no binding ruling on Jewish law. | It shows what the main sources say and where customs differ. It states that it does not rule, and suggests asking a rabbi. It does not refuse flatly. |
| 2 | Outside the library | What is the weather in Jerusalem tomorrow? | The request has no link to Jewish texts. | ChatGPT answers without calling any Yochai tool, or says the plugin does not cover this. |
| 3 | A source that does not exist | Quote Genesis chapter 60, verse 3. | Genesis has 50 chapters. | `get_passage` returns a clear "not found" message. The answer says the verse does not exist and offers a real passage. It invents no text. |

## Step 5: Demo video (about 60 seconds)

Record in ChatGPT on the web, at normal speed, with no cuts inside a tool call.

| Time | Scene | What the viewer sees |
| --- | --- | --- |
| 0:00 to 0:05 | Title | The plugin page: "Yochai: Jewish Texts. Study Torah, Talmud and more." |
| 0:05 to 0:20 | Topic question | The user types test case 1. The tool call opens. The answer shows 3 quoted passages with links. |
| 0:20 to 0:30 | Link | The user opens one link. The passage opens on the Yochai website. |
| 0:30 to 0:42 | Weekly portion | The user types test case 3. The answer names the portion and gives one question. |
| 0:42 to 0:52 | Exact passage | The user types test case 2. Hebrew and English appear with the translation credit. |
| 0:52 to 1:00 | No ruling | The user types negative case 1. The answer shows sources and states that it does not rule. |

Upload the video where the reviewer can open it without sign-in, and paste the link in the form.

## Step 6: Release notes for the form

```text
First release. 16 read-only tools over the Yochai library of Jewish texts. No sign-in. Text answers only. A passage card is planned for the next release.
```

## The steps Alex performs

1. Complete the business verification (Step 1).
2. Press **Verify Domain** after the token is live (Step 2).
3. Open https://platform.openai.com/plugins, paste the fields, tick the confirmation boxes and press **Submit for review**.
