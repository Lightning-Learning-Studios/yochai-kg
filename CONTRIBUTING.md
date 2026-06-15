# Contributing

Thanks for helping grow an open resource for Jewish learning. Three ways to contribute:

## 1. Skills (recipes for agents)
Add or improve a recipe in [`skills/`](./skills/README.md). Copy `skills/_template/SKILL.md`,
write a concrete method that calls the gateway tools, include a worked example, and open a PR.
Keep the chevruta values: grounded, cite primary sources, honest about gaps, not a posek.

## 2. Corpus submissions (new texts)
Propose a text for the graph via [`submitted_texts/`](./submitted_texts). Check
[`WANTED.md`](./submitted_texts/WANTED.md) first — there's a prioritized list of texts we're
actively looking for. Follow [`SUBMISSION_SCHEMA.md`](./submitted_texts/SUBMISSION_SCHEMA.md)
and validate locally before opening a PR. Only rights-cleared / public-domain sources.

## 3. Gateway & docs
Improve the MCP server, add a tool, fix a query, sharpen the docs.

### Dev setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env     # fill in NEO4J_* + DEEPINFRA_API_KEY (read-only access)
ruff check .
pytest -q
yochai-kg-gateway        # stdio; or MCP_TRANSPORT=http yochai-kg-gateway
```

### Ground rules
- **Read-only only.** No tool may write to the graph. The client refuses write Cypher; keep it that way.
- **Every result cites its source.** Preserve `deep_link` / references in tool outputs.
- **Cap results.** Use `config.clamp_limit`; never return unbounded sets.
- **Be kind to the shared instance.** Keep queries bounded and indexed; no cartesian blowups.
- **Respect the texts.** This corpus is sacred to many.

By contributing you agree your contribution is licensed under Apache-2.0.
