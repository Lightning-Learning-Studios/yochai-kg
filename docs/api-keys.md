# API keys — request & approval flow

Free, read-only access is gated by lightweight API keys so the shared graph stays healthy
(rate-limiting, abuse control, attribution). The flow:

```
  Requester                    Gateway                     Slack #yochai            Approver
     │  GET /request-key          │                              │                     │
     │ ─────────────────────────► │  (serves the form)           │                     │
     │  POST /request-key         │                              │                     │
     │ ─────────────────────────► │  insert pending key ──────►  │  message + buttons   │
     │                            │                              │ ──────────────────► │
     │                            │                              │   click Approve      │
     │                            │  POST /slack/interactions ◄──┼──────────────────── │
     │                            │  set key active              │                     │
     │  ◄── email with key ───────│  (or shown in Slack thread)  │  msg updated ✅      │
```

## What ships
- `GET /request-key` — a simple form (email, name, what you're building).
- `POST /request-key` — creates a **pending** key, posts the request to `#yochai` with
  Approve / Deny buttons.
- `POST /slack/interactions` — verifies Slack's signature, and on **Approve** flips the key to
  `active` (and emails it if Resend is configured; otherwise the key is shown in the Slack thread
  for you to share). On **Deny** marks it `denied`.
- The gateway's `/mcp` endpoint accepts any key that is `active` in the store (or in the static
  `GATEWAY_API_KEYS` allowlist).

## Setup (one-time)

1. **Database:** run [`migrations/001_api_keys.sql`](../migrations/001_api_keys.sql) against your
   Supabase project (creates `yochai_kg_api_keys`, RLS-locked to the service role). Set
   `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
2. **Slack app** (api.slack.com/apps → Create New App):
   - OAuth scope `chat:write`; install to the workspace; invite the bot to `#yochai`.
   - Set `SLACK_BOT_TOKEN` (`xoxb-…`) and `SLACK_SIGNING_SECRET`.
   - **Interactivity & Shortcuts** → on → Request URL: `https://<gateway-host>/slack/interactions`.
   - Optionally set `SLACK_CHANNEL` (defaults to `#yochai`).
3. **Email (Mailchimp Transactional / Mandrill):** set `MAILCHIMP_API_KEY` — the **same key the rest
   of the app uses** (see `infrastructure/gcp-functions/shared/send-email`). Approved keys are emailed
   from the verified `support@lightninginspiration.com` sender via `messages/send` (override with
   `MAILCHIMP_FROM_EMAIL` / `MAILCHIMP_FROM_NAME`). Without it, the approved key appears in the Slack
   thread for manual delivery.
4. **Turn the gate on:** `GATEWAY_REQUIRE_API_KEY=true`.

## Operating
- Approve/deny from the `#yochai` message — no dashboard needed.
- Revoke a key: set its `status` to `revoked` in `yochai_kg_api_keys` (the gateway only accepts
  `active`).
- The store records `last_used_at`; add rate-limiting at the edge (e.g. Railway/Cloud proxy) keyed
  on the API key as usage grows.
