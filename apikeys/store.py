"""Supabase-backed store for API key requests (PostgREST via httpx).

Uses the service-role key, so it bypasses RLS. Never expose the service-role key
to clients — this runs server-side only.
"""
from __future__ import annotations

import os
import secrets

import httpx

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


async def validate_key(api_key: str) -> bool:
    """True iff the key exists and is active. Best-effort usage bump."""
    if not api_key or not configured():
        return False
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(
            f"{_base()}?api_key=eq.{api_key}&status=eq.active&select=id",
            headers=_headers(),
        )
        if r.status_code != 200 or not r.json():
            return False
        row_id = r.json()[0]["id"]
        try:  # fire-and-forget usage stats
            await c.patch(
                f"{_base()}?id=eq.{row_id}",
                headers=_headers({"Prefer": "return=minimal"}),
                json={"last_used_at": "now()"},
            )
        except Exception:
            pass
        return True
