-- Yochai Open KG: count every API call and keep a metadata-only usage log.
--
-- Why: the gateway (apikeys/store.py validate_key) PATCHed only last_used_at on
-- each request, so yochai_kg_api_keys.request_count stayed 0 for every key. The
-- gateway now calls record_yochai_kg_api_usage() once per authenticated /mcp
-- request, fire-and-forget (it never delays or fails the request). The function
-- bumps request_count and last_used_at in one atomic UPDATE and appends one row
-- to yochai_kg_api_usage.
--
-- The usage log holds metadata only: which key, when, which MCP method / tool,
-- which MCP client, HTTP status and latency. It never stores tool arguments,
-- queries or results.

-- The key table is created by 001_api_keys.sql. Declare it idempotently here too
-- (canonical copy: readiverse-haven infrastructure/supabase/migrations/
-- 20261029120000_yochai_kg_api_usage.sql). Where 001 ran, this block is a no-op.
CREATE TABLE IF NOT EXISTS public.yochai_kg_api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  name text,
  intended_use text,
  api_key text NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'active', 'denied', 'revoked')),
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_at timestamptz,
  decided_by text,
  slack_ts text,
  last_used_at timestamptz,
  request_count bigint NOT NULL DEFAULT 0
);

ALTER TABLE public.yochai_kg_api_keys
  ADD COLUMN IF NOT EXISTS request_count bigint NOT NULL DEFAULT 0;

ALTER TABLE public.yochai_kg_api_keys ENABLE ROW LEVEL SECURITY;

-- One row per authenticated /mcp HTTP request.
CREATE TABLE IF NOT EXISTS public.yochai_kg_api_usage (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  key_id uuid NOT NULL REFERENCES public.yochai_kg_api_keys (id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  http_method text NOT NULL,      -- POST / GET / DELETE
  rpc_method text,                -- JSON-RPC method, e.g. initialize, tools/list, tools/call
  tool_name text,                 -- MCP tool for tools/call, e.g. search_corpus, run_cypher
  client_name text,               -- MCP clientInfo.name sent on initialize, e.g. claude-ai, cursor
  session_id text,                -- mcp-session-id header; groups the calls of one session
  status_code integer NOT NULL,
  latency_ms integer
);

CREATE INDEX IF NOT EXISTS yochai_kg_api_usage_key_created_idx
  ON public.yochai_kg_api_usage (key_id, created_at DESC);

CREATE INDEX IF NOT EXISTS yochai_kg_api_usage_created_idx
  ON public.yochai_kg_api_usage (created_at DESC);

ALTER TABLE public.yochai_kg_api_usage ENABLE ROW LEVEL SECURITY;

-- Only the gateway (service role, which bypasses RLS) reads or writes the log.
REVOKE ALL ON public.yochai_kg_api_usage FROM anon, authenticated;

COMMENT ON TABLE public.yochai_kg_api_usage IS
  'Metadata-only per-request log for the Yochai Open KG MCP gateway. No payloads.';

-- Atomic counter bump + usage row. Unknown key ids are ignored, so a stale or
-- revoked id can never insert an orphan row (the FK would reject it anyway).
CREATE OR REPLACE FUNCTION public.record_yochai_kg_api_usage(
  p_key_id uuid,
  p_http_method text,
  p_rpc_method text DEFAULT NULL,
  p_tool_name text DEFAULT NULL,
  p_client_name text DEFAULT NULL,
  p_session_id text DEFAULT NULL,
  p_status_code integer DEFAULT NULL,
  p_latency_ms integer DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  UPDATE public.yochai_kg_api_keys AS keys
     SET request_count = keys.request_count + 1,
         last_used_at = now()
   WHERE keys.id = p_key_id;

  IF NOT FOUND THEN
    RETURN;
  END IF;

  INSERT INTO public.yochai_kg_api_usage
    (key_id, http_method, rpc_method, tool_name, client_name, session_id, status_code, latency_ms)
  VALUES (
    p_key_id,
    left(coalesce(p_http_method, 'UNKNOWN'), 16),
    left(p_rpc_method, 64),
    left(p_tool_name, 64),
    left(p_client_name, 120),
    left(p_session_id, 128),
    coalesce(p_status_code, 0),
    p_latency_ms
  );
END;
$$;

REVOKE ALL ON FUNCTION public.record_yochai_kg_api_usage(uuid, text, text, text, text, text, integer, integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.record_yochai_kg_api_usage(uuid, text, text, text, text, text, integer, integer)
  TO service_role;
