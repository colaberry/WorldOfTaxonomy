-- WoT-specific auth artifacts (NOT extracted with the developer-key
-- system). Depends on schema_devkeys.sql (uses app_user, api_key).
--
-- Everything portable - org, app_user, api_key, magic_link_token -
-- lives in schema_devkeys.sql. This file holds only the WoT-product
-- pieces: per-request usage logging, daily caps, and the classify
-- lead-capture stopgap that disappears once Zitadel ships.

-- Per-request usage tracking
CREATE TABLE IF NOT EXISTS usage_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES app_user(id),
    api_key_id  UUID REFERENCES api_key(id),
    endpoint    TEXT NOT NULL,
    method      TEXT NOT NULL,
    status_code INTEGER,
    ip_address  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_log(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_log(user_id, created_at);

-- Daily usage counters for tier-based daily caps
CREATE TABLE IF NOT EXISTS daily_usage (
    user_id     UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    usage_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    count       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, usage_date)
);

-- Lead capture for the free /classify web tool. Anonymous users give
-- an email in exchange for a classify query. Used for lead nurture
-- marketing, NOT for authentication. Migrates to Zitadel accounts
-- once the central IdP is provisioned.
CREATE TABLE IF NOT EXISTS classify_lead (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email        TEXT NOT NULL,
    query_text   TEXT NOT NULL,
    ip_address   TEXT,
    user_agent   TEXT,
    referrer     TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_classify_lead_email ON classify_lead(email);
CREATE INDEX IF NOT EXISTS idx_classify_lead_created ON classify_lead(created_at);
