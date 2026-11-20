"""Gates 1 and 2: read the public Create feed and keep only eligible methods.

The feed is `GET {YOCHAI_API_URL}/api/methods/community`. It needs no sign-in and
returns only methods a Yochai reviewer has published. The shape (verified against
`railway-yochai-service/web/method_routes.py` and the `yochai_methods_command`
database function on the readiverse main branch) is:

    {"methods": [{
        "id": "<method uuid>", "creatorId": "<uuid>", "creatorName": "Display Name",
        "versionId": "<published version uuid>", "revision": 3,
        "status": "published", "visibility": "community",
        "publishedVersionId": "<uuid>", "submissionVersionId": null,
        "createdAt": "...", "updatedAt": "<when the published version was made>",
        "title": "...", "audience": "...", "outcome": "...", "steps": ["..."],
        "category": "Research|Teaching|Writing|Text Study",
        "compatibility": ["Yochai", "Agent"],
        "fullInstructions": "... optional, up to 200 KB ...",
        "attachments": [{... only files the author shared ...}],
        "publishedVersion": {... the same content fields again ...}
    }]}

Consent (gate 2) is two extra content fields that the Yochai app does not write
yet (see docs/plugin/community-skills.md):

    "pluginConsent": true            the author ticked the consent box
    "pluginLicense": "CC BY 4.0"     the licence the author chose (default CC BY 4.0)

The pipeline reads consent from `publishedVersion`, which is the immutable record
the reviewer approved. A method without consent is skipped, never guessed.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from . import ALLOWED_LICENSES, DEFAULT_LICENSE

FEED_PATH = "/api/methods/community"
_TIMEOUT = 30.0
_USER_AGENT = "yochai-kg-community-skills/1.0"


class FeedError(RuntimeError):
    """The feed could not be read or did not have the expected shape."""


@dataclass(frozen=True)
class Method:
    """One published Create method, reduced to what the pipeline needs."""

    method_id: str
    version_id: str
    revision: int
    title: str
    audience: str
    outcome: str
    steps: tuple[str, ...]
    category: str
    full_instructions: str | None
    author: str
    published_at: str  # ISO timestamp of the published version
    attachments: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    plugin_consent: bool = False
    plugin_license: str = DEFAULT_LICENSE


def feed_url(base_url: str | None = None) -> str:
    base = (base_url or os.getenv("YOCHAI_API_URL") or "").strip().rstrip("/")
    if not base:
        raise FeedError("YOCHAI_API_URL is not set, so the pipeline cannot find the Create feed.")
    if not base.startswith("https://") and not base.startswith("http://localhost"):
        raise FeedError("YOCHAI_API_URL must start with https://")
    return base + FEED_PATH


def fetch_feed(base_url: str | None = None) -> list[dict[str, Any]]:
    """Download the public feed and return the raw method records."""
    url = feed_url(base_url)
    try:
        resp = httpx.get(url, timeout=_TIMEOUT, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise FeedError(f"Could not read the Create feed: {exc}") from exc
    return _methods_from_payload(payload)


def load_fixture(path: str | Path) -> list[dict[str, Any]]:
    """Read a saved feed (same shape as the live one) from a file."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FeedError(f"Could not read the fixture {path}: {exc}") from exc
    return _methods_from_payload(payload)


def _methods_from_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("methods"), list):
        raise FeedError('The feed does not have the expected {"methods": [...]} shape.')
    return [m for m in payload["methods"] if isinstance(m, dict)]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def parse_method(raw: dict[str, Any]) -> Method:
    """Build a Method from one feed record. Content comes from the published version."""
    published = raw.get("publishedVersion")
    content: dict[str, Any] = published if isinstance(published, dict) else raw
    steps = content.get("steps")
    attachments = content.get("attachments")
    full = content.get("fullInstructions")
    license_name = _text(content.get("pluginLicense")) or DEFAULT_LICENSE
    try:
        revision = int(raw.get("revision") or 0)
    except (TypeError, ValueError):
        revision = 0
    return Method(
        method_id=_text(raw.get("id")),
        version_id=_text(raw.get("publishedVersionId")) or _text(raw.get("versionId")),
        revision=revision,
        title=_text(content.get("title")),
        audience=_text(content.get("audience")),
        outcome=_text(content.get("outcome")),
        steps=tuple(s.strip() for s in steps if isinstance(s, str) and s.strip()) if isinstance(steps, list) else (),
        category=_text(content.get("category")) or "Teaching",
        full_instructions=full if isinstance(full, str) and full.strip() else None,
        author=_text(raw.get("creatorName")) or "Yochai creator",
        published_at=_text(raw.get("updatedAt")) or _text(raw.get("createdAt")),
        attachments=tuple(a for a in attachments if isinstance(a, dict)) if isinstance(attachments, list) else (),
        # Only the JSON value `true` counts. The string "true" or the number 1 does not.
        plugin_consent=content.get("pluginConsent") is True,
        plugin_license=license_name,
    )


def eligibility(raw: dict[str, Any], method: Method) -> tuple[bool, str]:
    """Gates 1 and 2. Return (eligible, reason-when-not)."""
    if raw.get("status") != "published" or not method.version_id:
        return False, "it is not a published method"
    if not method.method_id:
        return False, "the feed record has no method id"
    if not method.title or not method.outcome:
        return False, "it has no title or no outcome"
    if not method.plugin_consent:
        return False, "the author has not given consent to publish it in the plugin"
    if method.plugin_license not in ALLOWED_LICENSES:
        return False, f"the licence '{method.plugin_license[:40]}' is not one the plugin accepts"
    return True, ""
