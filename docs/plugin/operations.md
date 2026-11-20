# Running the open plugin server

This page is for the person who deploys and watches the server behind the plugin.

## The two servers

| | Open plugin server | Developer gateway |
| --- | --- | --- |
| Code | `gateway/open_server.py` | `gateway/server.py` |
| Sign-in | None | A free key |
| Tools | 16 curated, read-only | All graph tools and `run_cypher` |
| Railway config file | `railway.open.json` | `railway.json` |
| Test address | `https://yochai-plugin-test-production.up.railway.app` | not applicable |
| Production address | `https://mcp.yochai.wiki` (planned, not created yet) | `https://yochai-kg-gateway-production.up.railway.app` |

The two servers share the code and the Neo4j database. They do not share a process, a connection pool or a rate limit. A problem in one does not stop the other.

## Run it on a laptop

```
pip install -e ".[dev]"
export NEO4J_YOCHAI_URI=... NEO4J_YOCHAI_USERNAME=... NEO4J_YOCHAI_PASSWORD=... DEEPINFRA_API_KEY=...
python -m uvicorn gateway.open_server:get_app --factory --port 8000
python tests/live_open_smoke.py http://127.0.0.1:8000/mcp
```

The last command calls every tool and prints one line for each check.

## Deploy the test server

```
export RAILWAY_PROJECT_ID=<the yochai-kg project id>
scripts/deploy_open_test.sh
python tests/live_open_smoke.py
```

The script uploads the working tree to the Railway service `yochai-plugin-test`. It changes nothing else.

## Create the production server (one time)

1. In the Railway project, add a service from this repository, branch `main`.
2. In the service settings, set **Railway config file** to `railway.open.json`.
3. Add the settings in the table below. Use references to the gateway service for the first four, so that no secret is copied by hand.
4. Add the custom domain `mcp.yochai.wiki` to the service. Railway shows one DNS record. Add that record where the `yochai.wiki` domain is managed.
5. Run `python tests/live_open_smoke.py https://mcp.yochai.wiki/mcp`. All checks must pass.

The address is permanent once a directory lists the plugin. Do not submit with a `railway.app` address.

## Settings

| Setting | Needed | Default | What it does |
| --- | --- | --- | --- |
| `NEO4J_YOCHAI_URI`, `NEO4J_YOCHAI_USERNAME`, `NEO4J_YOCHAI_PASSWORD` | Yes | none | The read connection to the graph |
| `DEEPINFRA_API_KEY` | Yes | none | Turns a search into a vector. Without it, search falls back to word matching. |
| `OPEN_NEO4J_MAX_POOL` | No | 8 | Most database connections this server may hold |
| `OPEN_DB_CONCURRENCY` | No | 6 | Most database queries at one time |
| `OPEN_RATE_PER_MINUTE` | No | 240 | Requests per network address per minute |
| `OPEN_RATE_PER_DAY` | No | 40000 | Requests per network address per day |
| `OPEN_MAX_IN_FLIGHT` | No | 48 | Most requests in progress on the whole server |
| `OPEN_MIN_SCORE` | No | 0.76 | The lowest similarity a search result may have |
| `OPEN_CACHE_SECONDS` | No | 900 | How long a result is remembered |
| `OPENAI_APPS_CHALLENGE` | For ChatGPT | empty | The domain verification token from the OpenAI platform |
| `OPEN_STATS_TOKEN` | No | empty | Turns on the `/stats` page for a caller that sends this token |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | No | empty | Saves daily usage counts. Needs `migrations/003_open_usage.sql`. |
| `YOCHAI_APP_URL` | No | `https://www.yochai.wiki` | The site that passage links open |

Claude and ChatGPT send requests from shared addresses on behalf of many people. For this reason the limits per address are high. The limit on database queries at one time is the real protection for the Yochai app.

## Pages the server shows

| Address | Purpose |
| --- | --- |
| `/mcp` | The server that assistants connect to |
| `/` , `/privacy`, `/terms`, `/support` | Public pages. The text is in `gateway/pages/`. |
| `/healthz` | Health check |
| `/.well-known/openai-apps-challenge` | Shows the ChatGPT verification token |
| `/stats` | Usage counts for today. Hidden unless `OPEN_STATS_TOKEN` is set. |

## The passage card

The passage card is a small panel that shows a passage beside the text answer. It shows the reference as the heading. It shows the Hebrew and the English side by side, or the Hebrew above the English on a narrow screen. It shows the translation credit and an "Open in Yochai" button.

Three tools show the card: `get_passage`, `search_passages` and `get_commentaries`. The other 13 tools show text only. The tool answers are the same with or without the card, so an assistant that cannot show panels still gets the full text.

The card is one file, `gateway/widgets/passage-card.html`. It loads nothing from the internet. It uses the fonts that are already on the reader's device.

| Host | How it finds the card |
| --- | --- |
| Claude and other MCP Apps hosts | The tool key `ui.resourceUri` |
| ChatGPT | The same key, and the older key `openai/outputTemplate` |

Both hosts read the same resource, `ui://widget/passage-card.html`, with the type `text/html;profile=mcp-app`.

A directory listing with a panel gets a stricter review than a listing with text only. Each directory asks for 3 to 5 screenshots of the panel in use. ChatGPT also asks for a dedicated web address for the panel, the `ui.domain` setting. The server does not set it yet. Add it before you submit to ChatGPT.

To see the card on your own computer, run this command from the repository root:

```
python -m http.server 8765 --directory gateway/widgets
```

Then open `http://127.0.0.1:8765/preview.html` in a browser. The preview page shows five sample answers in the card. Use the menus at the top to change the host, the theme and the width.

## What is counted

The server counts calls per day, per tool and per assistant (Claude, ChatGPT, other). It counts new connections as `_session`. It stores no question, no result and no network address.

Until `migrations/003_open_usage.sql` is applied, the counts stay in memory and reset on each deploy. The migration is not applied. Apply it only with the owner's approval.

These counts cannot show how many different people use the plugin, or how many return. Claude and ChatGPT hide the person behind a shared address. The directories report installs. Visits and new accounts on yochai.wiki are counted there, from the source tag that every passage link carries.

## When something is wrong

| Sign | Likely cause | What to do |
| --- | --- | --- |
| Tools answer "The library took too long to answer" | The graph is slow or busy | Check the Neo4j service. Lower `OPEN_DB_CONCURRENCY` if the Yochai app is affected. |
| Search answers "these are word matches" | DeepInfra is down or the key is wrong | Check `DEEPINFRA_API_KEY` and the DeepInfra status page |
| Many `429` answers | One address is over its limit | Check `/stats`. Raise `OPEN_RATE_PER_MINUTE` if the address is Claude or ChatGPT. |
| The Yochai app slows down | Public traffic is too heavy | Set `OPEN_MAX_IN_FLIGHT` to a low number, or stop the service. The app and the gateway keep running. |

To turn the plugin server off, stop its Railway service. Nothing else depends on it.

## Keep the documents in step

```
python scripts/sync_plugin_docs.py
```

This copies the server's real tool list into the submission document and into the stand-in server that the plugin evals use. The automated checks fail when they differ.
