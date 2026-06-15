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

_STYLE = """
 @font-face{font-family:'Feature Deck';src:url('https://yochai.lightningstudios.ai/fonts/FeatureDeck-Medium.otf') format('opentype');font-weight:500;font-display:swap}
 @font-face{font-family:'EF Circular';src:url('https://yochai.lightningstudios.ai/fonts/EFCircular-Book.otf') format('opentype');font-weight:400;font-display:swap}
 :root{--ink:#173257;--muted:#7E8E9E;--line:#E8EDF2;--card:#FCFAF2;--link:#4A6D8C}
 *{box-sizing:border-box}
 body{margin:0;min-height:100vh;background:linear-gradient(180deg,#F3F8FB 0%,#DBE3EB 100%);
   font-family:'EF Circular',system-ui,-apple-system,sans-serif;color:var(--ink);
   display:flex;align-items:center;justify-content:center;padding:2.5rem 1rem;line-height:1.55}
 .card{background:var(--card);border:1px solid var(--line);border-radius:20px;max-width:560px;width:100%;
   padding:2.5rem;box-shadow:0 10px 40px rgba(23,50,87,.08),0 2px 8px rgba(23,50,87,.04)}
 .eyebrow{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 .5rem}
 h1{font-family:'Feature Deck',Georgia,serif;font-weight:500;font-size:2.1rem;margin:0 0 .6rem;line-height:1.1;
   background:linear-gradient(95deg,#2D5979,#7E8E9E);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
 p.lede{color:#5E6773;margin:0 0 1.6rem}
 label{display:block;margin:1.1rem 0 .35rem;font-weight:500;font-size:.92rem}
 .opt{color:var(--muted);font-weight:400}
 input,textarea{width:100%;padding:.7rem .85rem;border:1px solid #D5DFEA;border-radius:10px;font:inherit;
   color:var(--ink);background:#fff;transition:border-color .15s,box-shadow .15s}
 input:focus,textarea:focus{outline:none;border-color:#2A4B7C;box-shadow:0 0 0 3px rgba(42,75,124,.15)}
 textarea{resize:vertical}
 button{margin-top:1.8rem;width:100%;padding:.85rem 1.4rem;border:0;border-radius:999px;background:#173257;
   color:#FAFAFA;font:inherit;font-weight:500;font-size:1rem;cursor:pointer;transition:transform .1s,background .15s}
 button:hover{background:#0f2540} button:active{transform:scale(.99)}
 .fine{color:var(--muted);font-size:.82rem;margin:1.4rem 0 0}
 a{color:var(--link)}
"""

_FORM = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Request access · Yochai Open Knowledge Graph</title>
<style>{_STYLE}</style></head><body>
<div class="card">
 <p class="eyebrow">Yochai · Open Knowledge Graph</p>
 <h1>Request your access key</h1>
 <p class="lede">Free, read-only access to the knowledge graph of the Jewish textual tradition —
 for your own agent to study, research, and learn. We review each request and email your key.</p>
 <form method="post" action="/request-key">
  <label>Email</label><input type="email" name="email" required placeholder="you@example.com">
  <label>Name <span class="opt">(optional)</span></label><input type="text" name="name">
  <label>What would you like to build or learn?</label>
  <textarea name="intended_use" rows="4" required placeholder="e.g. an agent that helps me prepare a weekly dvar torah"></textarea>
  <button type="submit">Request access key</button>
 </form>
 <p class="fine">A chavruta, not a posek — everything is derived study material; verify against the
 primary sources. <a href="https://github.com/Lightning-Learning-Studios/yochai-kg">Learn more</a>.</p>
</div></body></html>"""

_THANKS = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Request received · Yochai KG</title>
<style>{_STYLE}</style></head><body><div class="card">
 <p class="eyebrow">Yochai · Open Knowledge Graph</p>
 <h1>Request received</h1>
 <p class="lede">Thank you. Your request is in, and we'll email your access key to <b>%s</b> once it's
 approved. In the meantime, you can <a href="https://yochai.lightningstudios.ai/knowledge-graph-preview">explore the graph</a>.</p>
</div></body></html>"""


async def _send_key_email(email: str, api_key: str) -> bool:
    """Email the approved key via Mandrill (Mailchimp Transactional). Returns True if sent."""
    key = os.getenv("MANDRILL_API_KEY")
    from_email = os.getenv("MANDRILL_FROM_EMAIL", "noreply@lightningstudios.ai")
    from_name = os.getenv("MANDRILL_FROM_NAME", "Yochai Open KG")
    if not key:
        return False
    body = (
        f"Your Yochai Open KG API key is approved.\n\nAPI key: {api_key}\n\n"
        "Use it in your MCP client as the x-api-key header against\n"
        "https://yochai-kg-gateway-production.up.railway.app/mcp\n\n"
        "Quickstart: https://github.com/Lightning-Learning-Studios/yochai-kg/blob/main/docs/quickstart-mcp.md\n\n"
        "Free and read-only. A chavruta, not a posek — verify all output against the primary sources."
    )
    payload = {"key": key, "message": {
        "from_email": from_email, "from_name": from_name,
        "to": [{"email": email, "type": "to"}],
        "subject": "Your Yochai Open KG API key", "text": body}}
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post("https://mandrillapp.com/api/1.0/messages/send.json", json=payload)
        if r.status_code >= 300:
            return False
        data = r.json()
        return bool(isinstance(data, list) and data and data[0].get("status") in ("sent", "queued", "scheduled"))


async def get_form(request):
    return HTMLResponse(_FORM)


async def post_request(request):
    is_json = "application/json" in request.headers.get("content-type", "")
    data = await request.json() if is_json else await request.form()
    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip() or None
    use = (data.get("intended_use") or "").strip() or None

    if "@" not in email:
        msg = "A valid email is required."
        return JSONResponse({"ok": False, "error": msg}, status_code=400) if is_json \
            else HTMLResponse(f"<p>{msg} <a href='/request-key'>Back</a></p>", status_code=400)
    if not store.configured():
        msg = "Key requests are not configured on this deployment."
        return JSONResponse({"ok": False, "error": msg}, status_code=503) if is_json \
            else HTMLResponse(f"<p>{msg}</p>", status_code=503)

    row = await store.create_request(email, name, use)
    ts = await slack.post_request(row)
    if ts:
        await store.set_status(row["id"], "pending", slack_ts=ts)
    if is_json:
        return JSONResponse({"ok": True, "message": "Request received — we'll email your key once approved."})
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
