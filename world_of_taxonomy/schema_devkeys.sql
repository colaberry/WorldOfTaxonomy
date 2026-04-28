-- Developer-key system schema (portable; extracts to developer.aixcelerator.ai pre-WoO).
--
-- Tables: org, app_user, api_key, magic_link_token.
-- This file owns the auth surface that any aixcelerator.ai sibling
-- product reuses. Everything WoT-specific (usage_log, daily_usage,
-- classify_lead) lives in schema_auth.sql instead.

CREATE TABLE IF NOT EXISTS org (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                        TEXT NOT NULL,
    domain                      TEXT UNIQUE,
    kind                        TEXT NOT NULL DEFAULT 'corporate'
                                CHECK (kind IN ('corporate', 'personal')),
    tier                        TEXT NOT NULL DEFAULT 'free'
                                CHECK (tier IN ('free', 'pro', 'enterprise')),
    rate_limit_pool_per_minute  INT NOT NULL DEFAULT 1000,
    stripe_customer_id          TEXT UNIQUE,
    zitadel_org_id              TEXT UNIQUE,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_user (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               TEXT NOT NULL UNIQUE,
    org_id              UUID NOT NULL REFERENCES org(id),
    role                TEXT NOT NULL DEFAULT 'member'
                        CHECK (role IN ('admin', 'member')),
    zitadel_sub         TEXT UNIQUE,
    -- Legacy fields kept so /api/v1/auth/* (password + JWT + OAuth)
    -- keeps working through Phase 6. Phase 1-5 of the Zitadel
    -- migration drops them.
    password_hash       TEXT,
    display_name        TEXT,
    tier                TEXT NOT NULL DEFAULT 'free'
                        CHECK (tier IN ('free', 'pro', 'enterprise')),
    is_active           BOOLEAN DEFAULT TRUE,
    oauth_provider      TEXT,
    oauth_provider_id   TEXT,
    avatar_url          TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_email ON app_user(email);
CREATE INDEX IF NOT EXISTS idx_app_user_org ON app_user(org_id);
CREATE INDEX IF NOT EXISTS idx_app_user_zitadel_sub
    ON app_user(zitadel_sub) WHERE zitadel_sub IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_oauth
    ON app_user(oauth_provider, oauth_provider_id)
    WHERE oauth_provider IS NOT NULL AND oauth_provider_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS api_key (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    key_hash        TEXT NOT NULL,
    key_prefix      TEXT NOT NULL,
    name            TEXT DEFAULT 'Default',
    scopes          TEXT[] NOT NULL DEFAULT ARRAY['wot:*']::TEXT[],
    is_active       BOOLEAN DEFAULT TRUE,
    last_used_at    TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    revoked_reason  TEXT,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_apikey_prefix
    ON api_key(key_prefix) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_apikey_user ON api_key(user_id);

CREATE TABLE IF NOT EXISTS magic_link_token (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    token_hash   TEXT NOT NULL UNIQUE,
    expires_at   TIMESTAMPTZ NOT NULL,
    consumed_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_magic_link_user ON magic_link_token(user_id);
CREATE INDEX IF NOT EXISTS idx_magic_link_expires
    ON magic_link_token(expires_at) WHERE consumed_at IS NULL;
