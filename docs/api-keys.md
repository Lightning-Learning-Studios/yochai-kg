# API keys — how they work

Free, read-only access is gated by lightweight API keys so the shared graph stays healthy
(rate-limiting, abuse control, attribution).

## Two pieces, two homes

- **Issuance** (request form → Slack approval → email) lives in **readiverse-haven** as a Cloud Run
  function: `infrastructure/gcp-functions/shared/yochai-kg-access`. The public request page is the
  Yochai app's **`/open-kg`** route (`yochai.lightningstudios.ai/open-kg`), which POSTs to that
  function. This keeps key issuance alongside the rest of our functions (`send-email`, `api-keys`,
  …) and uses the same Mailchimp Transactional method (`MAILCHIMP_API_KEY`).
- **Validation** lives in **this gateway**. The `/mcp` endpoint accepts any key that is `active` in
  the shared Supabase table `yochai_kg_api_keys` (or present in the static `GATEWAY_API_KEYS`
  allowlist). The gateway never issues or emails keys.

```
  Requester → /open-kg (Yochai app)
                 │ POST /request
                 ▼
        yochai-kg-access (Cloud Run) ──► Slack #yochai (Approve/Deny)
                 │  on approve: status=active + email via Mailchimp
                 ▼
        yochai_kg_api_keys (Supabase)
                 ▲
                 │ validate active key
        this gateway  ── /mcp (x-api-key)
```

## Gateway config (validation)
Set `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (reads `yochai_kg_api_keys`) and
`GATEWAY_REQUIRE_API_KEY=true`. That's all the gateway needs for keys.

## Issuance setup
See the function's `deploy.sh` and the readiverse-haven Slack setup:
- **DB:** `migrations/001_api_keys.sql` here created `yochai_kg_api_keys` (RLS service-role only).
- **Function env:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `MAILCHIMP_API_KEY` (from `.env.local`),
  `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` (from the Slack app).
- **Slack app:** `chat:write` scope, bot invited to `#yochai`, Interactivity Request URL →
  `<function-url>/slack/interactions`.
- **Yochai app:** set `VITE_GCP_YOCHAI_KG_ACCESS_URL` to the function URL.

Revoke a key by setting its `status` to `revoked` in `yochai_kg_api_keys` (the gateway only accepts
`active`).
