-- Auth schema for WorldOfTaxanomy

-- Users
CREATE TABLE IF NOT EXISTS app_user (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             TEXT NOT NULL UNIQUE,
    password_hash     TEXT,               -- NULL for OAuth-only accounts
    display_name      TEXT,
    tier              TEXT NOT NULL DEFAULT 'free'
                      CHECK (tier IN ('free', 'pro', 'enterprise')),
    is_active         BOOLEAN DEFAULT TRUE,
    -- OAuth / social login fields
    oauth_provider    TEXT,               -- 'github' | 'google' | 'linkedin'
    oauth_provider_id TEXT,               -- provider's user ID
    avatar_url        TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_email ON app_user(email);
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_oauth
    ON app_user(oauth_provider, oauth_provider_id)
    WHERE oauth_provider IS NOT NULL AND oauth_provider_id IS NOT NULL;

-- API Keys
CREATE TABLE IF NOT EXISTS api_key (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    key_hash    TEXT NOT NULL,
    key_prefix  TEXT NOT NULL,
    name        TEXT DEFAULT 'Default',
    is_active   BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_apikey_prefix ON api_key(key_prefix);
CREATE INDEX IF NOT EXISTS idx_apikey_user ON api_key(user_id);

-- Usage tracking
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
