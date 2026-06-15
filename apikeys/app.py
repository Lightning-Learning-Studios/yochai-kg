"""Public API-key request form + Slack approval webhook.

Routes (mounted onto the gateway HTTP app):
  GET  /request-key        → the request form
  POST /request-key        → create a pending request, post it to Slack
  POST /slack/interactions → Slack Approve/Deny button handler
"""
from __future__ import annotations

import json
import os
from urllib.parse import parse_qs

import httpx
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route

from . import slack, store

_FORM = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Request a Yochai KG API key</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:640px;margin:3rem auto;padding:0 1rem;line-height:1.5;color:#1a1a1a}
 h1{font-size:1.5rem} label{display:block;margin:1rem 0 .25rem;font-weight:600}
 input,textarea{width:100%;padding:.6rem;border:1px solid #ccc;border-radius:8px;font:inherit}
 button{margin-top:1.5rem;padding:.7rem 1.4rem;border:0;border-radius:8px;background:#1a1a1a;color:#fff;font:inherit;cursor:pointer}
 .muted{color:#666;font-size:.9rem}
</style></head><body>
<h1>Request a Yochai Open KG API key</h1>
<p class="muted">Free, read-only access to the knowledge graph for your agent. Requests are
reviewed by the Lightning Learning Studios team; you'll get your key by email once approved.</p>
<form method="post" action="/request-key">
 <label>Email *</label><input type="email" name="email" required>
 <label>Name</label><input type="text" name="name">
 <label>What are you building? *</label>
 <textarea name="intended_use" rows="4" required placeholder="e.g. an agent that drafts divrei torah for my shul"></textarea>
 <button type="submit">Request key</button>
</form>
<p class="muted">By requesting a key you agree to use the graph as derived study material — verify
against primary sources. See the repo for terms.</p>
</body></html>"""

_THANKS = """<!doctype html><meta charset="utf-8"><body style="font-family:system-ui,sans-serif;max-width:640px;margin:3rem auto;padding:0 1rem">
<h1>Request received 🙏</h1><p>Thanks — your request is in. We'll review it and email your key to
<b>%s</b> once approved.</p></body>"""


async def _send_key_email(email: str, api_key: str) -> bool:
    """Email the approved key via Resend, if configured. Returns True if sent."""
    resend = os.getenv("RESEND_API_KEY")
    sender = os.getenv("RESEND_FROM", "Yochai KG <noreply@lightningstudios.ai>")
    if not resend:
        return False
    body = (
        f"Your Yochai Open KG API key is approved.\n\nAPI key: {api_key}\n\n"
        "Use it in your MCP client as the x-api-key header. Quickstart: "
        "https://github.com/Lightning-Learning-Studios/yochai-kg/blob/main/docs/quickstart-mcp.md\n\n"
        "Read-only, free. Verify all output against primary sources."
    )
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post("https://api.resend.com/emails",
                         headers={"Authorization": f"Bearer {resend}"},
                         json={"from": sender, "to": [email], "subject": "Your Yochai KG API key", "text": body})
        return r.status_code < 300


async def get_form(request):
    return HTMLResponse(_FORM)


async def post_request(request):
    form = await request.form()
    email = (form.get("email") or "").strip()
    if "@" not in email:
        return HTMLResponse("<p>A valid email is required. <a href='/request-key'>Back</a></p>", status_code=400)
    if not store.configured():
        return HTMLResponse("<p>Key requests are not configured on this deployment.</p>", status_code=503)
    row = await store.create_request(email, (form.get("name") or "").strip() or None,
                                     (form.get("intended_use") or "").strip() or None)
    ts = await slack.post_request(row)
    if ts:
        await store.set_status(row["id"], "pending", slack_ts=ts)
    return HTMLResponse(_THANKS % email)


async def slack_interactions(request):
    body = await request.body()
    if not slack.verify_signature(request.headers, body):
        return PlainTextResponse("invalid signature", status_code=401)
    parsed = parse_qs(body.decode("utf-8"))
    payload = json.loads(parsed.get("payload", ["{}"])[0])
    action = (payload.get("actions") or [{}])[0]
    action_id, rid = action.get("action_id"), action.get("value")
    decided_by = (payload.get("user") or {}).get("username")
    channel = (payload.get("channel") or {}).get("id")
    ts = (payload.get("message") or {}).get("ts")
    if not rid or action_id not in ("approve", "deny"):
        return JSONResponse({"ok": True})

    if action_id == "deny":
        await store.set_status(rid, "denied", decided_by=decided_by)
        await slack.update_message(channel, ts, f"❌ Denied by @{decided_by}.")
        return JSONResponse({"ok": True})

    row = await store.set_status(rid, "active", decided_by=decided_by)
    api_key = row.get("api_key") if row else None
    emailed = await _send_key_email(row["email"], api_key) if (row and api_key) else False
    note = "emailed to requester ✅" if emailed else f"share manually — key: `{api_key}`"
    await slack.update_message(channel, ts, f"✅ Approved by @{decided_by} for {row.get('email')} — {note}.")
    return JSONResponse({"ok": True})


routes = [
    Route("/request-key", get_form, methods=["GET"]),
    Route("/request-key", post_request, methods=["POST"]),
    Route("/slack/interactions", slack_interactions, methods=["POST"]),
]
