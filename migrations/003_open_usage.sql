-- Yochai open plugin server: daily usage counts.
--
-- NOT APPLIED. Apply only after explicit approval (see readiverse-haven CLAUDE.md).
-- Until it is applied the open server keeps its counts in memory and logs a
-- warning when a flush is refused; nothing else is affected.
--
-- What is stored: one row per (day, tool, client) with a call count and an
-- error count. "client" is one of claude, chatgpt, other. The pseudo-tool
-- "_session" counts new connections. No query text, no results, no network
-- addresses and no identifiers of any person are stored.

CREATE TABLE IF NOT EXISTS public.yochai_open_usage_daily (
  day date NOT NULL,
  tool text NOT NULL,
  client text NOT NULL,
  calls bigint NOT NULL DEFAULT 0,
  errors bigint NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (day, tool, client)
);

ALTER TABLE public.yochai_open_usage_daily ENABLE ROW LEVEL SECURITY;
-- No policies: only the service role (which bypasses RLS) reads or writes.

CREATE OR REPLACE FUNCTION public.record_yochai_open_usage(p_rows jsonb)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  INSERT INTO public.yochai_open_usage_daily AS u (day, tool, client, calls, errors)
  SELECT (r->>'day')::date,
         left(r->>'tool', 64),
         left(r->>'client', 16),
         coalesce((r->>'calls')::bigint, 0),
         coalesce((r->>'errors')::bigint, 0)
  FROM jsonb_array_elements(p_rows) AS r
  ON CONFLICT (day, tool, client) DO UPDATE
    SET calls = u.calls + EXCLUDED.calls,
        errors = u.errors + EXCLUDED.errors,
        updated_at = now();
$$;

REVOKE ALL ON FUNCTION public.record_yochai_open_usage(jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.record_yochai_open_usage(jsonb) TO service_role;
