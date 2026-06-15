"""Slack integration for API-key approvals.

Posts each request to a channel (#yochai) with Approve / Deny buttons, verifies
inbound interaction signatures, and updates the message after a decision.
Requires a Slack app with: chat:write scope, Interactivity enabled pointing at
POST /slack/interactions, the bot invited to the channel.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time

import httpx

BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
CHANNEL = os.getenv("SLACK_CHANNEL", "#yochai")
_API = "https://slack.com/api"


def configured() -> bool:
    return bool(BOT_TOKEN and SIGNING_SECRET)


def verify_signature(headers, body: bytes) -> bool:
    """Verify the Slack request signature (v0 HMAC-SHA256)."""
    ts = headers.get("x-slack-request-timestamp", "")
    sig = headers.get("x-slack-signature", "")
    if not ts or not sig or not SIGNING_SECRET:
        return False
    try:
        if abs(time.time() - int(ts)) > 60 * 5:  # replay guard
            return False
    except ValueError:
        return False
    basestring = f"v0:{ts}:{body.decode('utf-8', 'ignore')}".encode()
    expected = "v0=" + hmac.new(SIGNING_SECRET.encode(), basestring, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def _request_blocks(row: dict) -> list:
    rid = row["id"]
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "🔑 Yochai KG — API key request"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Email:*\n{row.get('email')}"},
            {"type": "mrkdwn", "text": f"*Name:*\n{row.get('name') or '—'}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Intended use:*\n{row.get('intended_use') or '—'}"}},
        {"type": "actions", "block_id": f"req_{rid}", "elements": [
            {"type": "button", "style": "primary", "text": {"type": "plain_text", "text": "Approve"},
             "action_id": "approve", "value": rid},
            {"type": "button", "style": "danger", "text": {"type": "plain_text", "text": "Deny"},
             "action_id": "deny", "value": rid},
        ]},
    ]


async def post_request(row: dict) -> str | None:
    """Post a new request to the channel; return the message ts."""
    if not configured():
        return None
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post(
            f"{_API}/chat.postMessage",
            headers={"Authorization": f"Bearer {BOT_TOKEN}"},
            json={"channel": CHANNEL, "text": f"API key request from {row.get('email')}", "blocks": _request_blocks(row)},
        )
        data = r.json()
        return data.get("ts") if data.get("ok") else None


async def update_message(channel: str, ts: str, text: str) -> None:
    """Replace a request message with the decision outcome."""
    if not configured() or not ts:
        return
    async with httpx.AsyncClient(timeout=10.0) as c:
        await c.post(
            f"{_API}/chat.update",
            headers={"Authorization": f"Bearer {BOT_TOKEN}"},
            json={"channel": channel, "ts": ts, "text": text,
                  "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]},
        )
