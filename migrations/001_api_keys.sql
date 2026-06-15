-- API key requests for the Yochai Open KG gateway.
-- New, additive table. RLS on with no public policies → only the service role
-- (used by the gateway) can read/write. No end-user access.

create table if not exists public.yochai_kg_api_keys (
    id            uuid primary key default gen_random_uuid(),
    email         text not null,
    name          text,
    intended_use  text,
    api_key       text unique not null,
    status        text not null default 'pending'
                  check (status in ('pending', 'active', 'denied', 'revoked')),
    created_at    timestamptz not null default now(),
    decided_at    timestamptz,
    decided_by    text,
    slack_ts      text,
    last_used_at  timestamptz,
    request_count bigint not null default 0
);

-- Fast validation lookup of live keys.
create index if not exists yochai_kg_api_keys_active_idx
    on public.yochai_kg_api_keys (api_key) where status = 'active';

create index if not exists yochai_kg_api_keys_email_idx
    on public.yochai_kg_api_keys (email);

alter table public.yochai_kg_api_keys enable row level security;
-- (Intentionally no policies: service-role key bypasses RLS; nobody else gets in.)
