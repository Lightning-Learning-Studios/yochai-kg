"""Protection and measurement for the open (no sign-in) server.

Three small pieces, all in memory:
  TTLCache      remembers tool results for a few minutes
  RateLimiter   a per-address request budget per minute and per day
  Usage         counts calls per day, per tool and per client; never stores
                query text, results or network addresses

The open server shares one Neo4j instance with the live Yochai app. These
limits, a small connection pool and a concurrency gate keep public traffic
from slowing the app down.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import secrets
import time
from collections import OrderedDict, defaultdict, deque
from typing import Any

log = logging.getLogger("yochai.open")


class TTLCache:
    """Least-recently-used cache with a time limit per entry."""

    def __init__(self, max_items: int = 2000, ttl_seconds: float = 600.0):
        self.max_items, self.ttl = max_items, ttl_seconds
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self.hits = self.misses = 0

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if item is None or item[0] < time.monotonic():
            self._data.pop(key, None)
            self.misses += 1
            return None
        self._data.move_to_end(key)
        self.hits += 1
        return item[1]

    def put(self, key: str, value: Any) -> None:
        self._data[key] = (time.monotonic() + self.ttl, value)
        self._data.move_to_end(key)
        while len(self._data) > self.max_items:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()


class RateLimiter:
    """Sliding one-minute window plus a rolling 24-hour budget per caller.

    Claude and ChatGPT call from shared addresses on behalf of many people, so
    the defaults are generous. The concurrency gate is the real safeguard."""

    def __init__(self, per_minute: int, per_day: int):
        self.per_minute, self.per_day = per_minute, per_day
        self._minute: dict[str, deque[float]] = defaultdict(deque)
        self._day: dict[str, deque[float]] = defaultdict(deque)
        self._last_sweep = time.monotonic()

    def check(self, caller: str, now: float | None = None) -> tuple[bool, int]:
        """Return (allowed, seconds to wait when refused)."""
        now = time.monotonic() if now is None else now
        m, d = self._minute[caller], self._day[caller]
        while m and m[0] <= now - 60:
            m.popleft()
        while d and d[0] <= now - 86400:
            d.popleft()
        if len(m) >= self.per_minute:
            return False, max(1, int(60 - (now - m[0])) + 1)
        if len(d) >= self.per_day:
            return False, max(60, int(86400 - (now - d[0])) + 1)
        m.append(now)
        d.append(now)
        if now - self._last_sweep > 300:
            self._sweep(now)
        return True, 0

    def _sweep(self, now: float) -> None:
        self._last_sweep = now
        for table, horizon in ((self._minute, 60), (self._day, 86400)):
            for k in [k for k, q in table.items() if not q or q[-1] <= now - horizon]:
                del table[k]


def client_label(user_agent: str | None, client_name: str | None = None) -> str:
    """Bucket the caller into claude, chatgpt or other. Used for counts only."""
    blob = f"{client_name or ''} {user_agent or ''}".lower()
    if "claude" in blob or "anthropic" in blob:
        return "claude"
    if "openai" in blob or "chatgpt" in blob:
        return "chatgpt"
    return "other"


class Usage:
    """Daily counters. Nothing here can identify a person.

    The address is hashed with a random salt that lives only in memory and
    changes every UTC day, so a hash cannot be linked across days or reversed."""

    def __init__(self) -> None:
        self._day = ""
        self._salt = b""
        self.calls: dict[tuple[str, str], int] = defaultdict(int)     # (tool, client) -> calls
        self.errors: dict[tuple[str, str], int] = defaultdict(int)
        self.sessions: dict[str, int] = defaultdict(int)              # client -> initialize calls
        self._callers: set[str] = set()
        self._unsent: dict[tuple[str, str, str, str], int] = defaultdict(int)
        self.started = time.time()

    def _roll(self) -> None:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        if today != self._day:
            self._day, self._salt = today, secrets.token_bytes(16)
            self.calls.clear()
            self.errors.clear()
            self.sessions.clear()
            self._callers.clear()

    def caller_id(self, address: str) -> str:
        self._roll()
        return hashlib.sha256(self._salt + address.encode()).hexdigest()[:16]

    def record(self, *, rpc_method: str | None, tool: str | None, client: str, caller: str,
               ok: bool, latency_ms: int) -> None:
        self._roll()
        self._callers.add(caller)
        if rpc_method == "initialize":
            self.sessions[client] += 1
            self._unsent[(self._day, "_session", client, "calls")] += 1
        if rpc_method == "tools/call" and tool:
            self.calls[(tool, client)] += 1
            self._unsent[(self._day, tool, client, "calls")] += 1
            if not ok:
                self.errors[(tool, client)] += 1
                self._unsent[(self._day, tool, client, "errors")] += 1
            log.info("call tool=%s client=%s ok=%s ms=%d", tool, client, ok, latency_ms)

    def snapshot(self) -> dict[str, Any]:
        self._roll()
        by_tool: dict[str, int] = defaultdict(int)
        by_client: dict[str, int] = defaultdict(int)
        for (tool, client), n in self.calls.items():
            by_tool[tool] += n
            by_client[client] += n
        return {
            "day": self._day,
            "uptime_seconds": int(time.time() - self.started),
            "tool_calls": sum(self.calls.values()),
            "errors": sum(self.errors.values()),
            "sessions_started": dict(self.sessions),
            "distinct_callers_today": len(self._callers),
            "calls_by_tool": dict(sorted(by_tool.items(), key=lambda kv: -kv[1])),
            "calls_by_client": dict(by_client),
        }

    def drain(self) -> list[dict[str, Any]]:
        """Counts added since the last drain, as rows for the daily table."""
        merged: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: {"calls": 0, "errors": 0})
        for (day, tool, client, kind), n in self._unsent.items():
            merged[(day, tool, client)][kind] += n
        self._unsent.clear()
        return [{"day": d, "tool": t, "client": c, **v} for (d, t, c), v in merged.items()]

    def restore(self, rows: list[dict[str, Any]]) -> None:
        """Put drained rows back after a failed send."""
        for r in rows:
            self._unsent[(r["day"], r["tool"], r["client"], "calls")] += r["calls"]
            self._unsent[(r["day"], r["tool"], r["client"], "errors")] += r["errors"]


async def flush_usage_forever(usage: Usage, interval: float = 300.0) -> None:
    """Send daily counts to Supabase when it is configured. Best effort only."""
    import httpx

    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not (url and key):
        log.info("usage counts stay in memory: Supabase is not configured")
        return
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    while True:
        await asyncio.sleep(interval)
        rows = usage.drain()
        if not rows:
            continue
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.post(f"{url}/rest/v1/rpc/record_yochai_open_usage", headers=headers, json={"p_rows": rows})
            if r.status_code >= 300:
                usage.restore(rows)
                log.warning("usage flush refused: %s %s", r.status_code, r.text[:160])
        except Exception as e:  # noqa: BLE001 - counts must never break the server
            usage.restore(rows)
            log.warning("usage flush failed: %s", e)
