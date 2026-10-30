"""Supabase-backed store for API key requests (PostgREST via httpx).

Uses the service-role key, so it bypasses RLS. Never expose the service-role key
to clients — this runs server-side only.
"""
from __future__ import annotations

import asyncio
import logging
import os
import secrets

import httpx

log = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
TABLE = "yochai_kg_api_keys"

_TIMEOUT = 10.0


def _headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _base() -> str:
    return f"{SUPABASE_URL}/rest/v1/{TABLE}"


def configured() -> bool:
    return bool(SUPABASE_URL and SERVICE_ROLE_KEY)


def new_key() -> str:
    return "yk_" + secrets.token_hex(24)


async def create_request(email: str, name: str | None, intended_use: str | None) -> dict:
    """Insert a pending key request and return the created row."""
    payload = {"email": email, "name": name, "intended_use": intended_use, "api_key": new_key(), "status": "pending"}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.post(_base(), headers=_headers({"Prefer": "return=representation"}), json=payload)
        r.raise_for_status()
        return r.json()[0]


async def set_status(request_id: str, status: str, decided_by: str | None = None, slack_ts: str | None = None) -> dict | None:
    patch: dict = {"status": status}
    if status in ("active", "denied"):
        patch["decided_at"] = "now()"
        patch["decided_by"] = decided_by
    if slack_ts:
        patch["slack_ts"] = slack_ts
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.patch(f"{_base()}?id=eq.{request_id}", headers=_headers({"Prefer": "return=representation"}), json=patch)
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None


async def validate_key(api_key: str) -> str | None:
    """Return the key's row id if the key exists and is active, else None.

    Usage stats are NOT written here; the caller reports each request through
    record_usage_soon() once the response status and latency are known.
    """
    if not api_key or not configured():
        return None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(
            f"{_base()}?api_key=eq.{api_key}&status=eq.active&select=id",
            headers=_headers(),
        )
        if r.status_code != 200 or not r.json():
            return None
        return r.json()[0]["id"]


# --- usage tracking -----------------------------------------------------------
# One call per authenticated /mcp request. The RPC (migrations/002_api_usage.sql)
# bumps request_count + last_used_at in one atomic UPDATE and appends a
# metadata-only row to yochai_kg_api_usage. Never stores tool arguments or results.
USAGE_RPC = "record_yochai_kg_api_usage"
_USAGE_TIMEOUT = 5.0
_pending: set[asyncio.Task] = set()  # strong refs so tasks are not GC'd mid-flight


async def record_usage(
    key_id: str,
    *,
    http_method: str,
    rpc_method: str | None = None,
    tool_name: str | None = None,
    client_name: str | None = None,
    session_id: str | None = None,
    status_code: int | None = None,
    latency_ms: int | None = None,
) -> None:
    """Record one request against a key. Swallows every error: usage stats must
    never affect the request they describe."""
    if not key_id or not configured():
        return
    body = {
        "p_key_id": key_id,
        "p_http_method": http_method,
        "p_rpc_method": rpc_method,
        "p_tool_name": tool_name,
        "p_client_name": client_name,
        "p_session_id": session_id,
        "p_status_code": status_code,
        "p_latency_ms": latency_ms,
    }
    try:
        async with httpx.AsyncClient(timeout=_USAGE_TIMEOUT) as c:
            r = await c.post(f"{SUPABASE_URL}/rest/v1/rpc/{USAGE_RPC}", headers=_headers(), json=body)
            if r.status_code == 404:
                # RPC not deployed yet (migration pending): keep last_used_at fresh as before.
                await c.patch(
                    f"{_base()}?id=eq.{key_id}",
                    headers=_headers({"Prefer": "return=minimal"}),
                    json={"last_used_at": "now()"},
                )
            elif r.status_code >= 300:
                log.warning("usage record failed: %s %s", r.status_code, r.text[:200])
    except Exception as e:  # noqa: BLE001 — best-effort by design
        log.warning("usage record error: %s", e)


def record_usage_soon(key_id: str, **fields) -> None:
    """Fire-and-forget wrapper around record_usage()."""
    try:
        task = asyncio.get_running_loop().create_task(record_usage(key_id, **fields))
    except RuntimeError:  # no running loop
        return
    _pending.add(task)
    task.add_done_callback(_pending.discard)
