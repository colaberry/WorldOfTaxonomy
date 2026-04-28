-- Migration 003: Phase 6 developer-key system.
--
-- Adds the org table and the columns app_user / api_key need to gate
-- the API and MCP server. Backfills every existing user into a
-- per-domain corporate org (or per-email personal org for free-email
-- domains) so the org_id NOT NULL constraint can apply without
-- losing any live row. Backfills every existing api_key with the
-- catch-all scope ['wot:*'] so legacy keys keep working.
--
-- Idempotent: every CREATE / ALTER uses IF NOT EXISTS where possible,
-- and the backfill DO block skips users that are already linked to
-- an org. Re-runs are safe.

-- 1. org table
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

-- 2. app_user new columns (nullable until backfill completes)
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES org(id);
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'member';
DO $do$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'app_user'
          AND c.conname = 'app_user_role_check'
    ) THEN
        ALTER TABLE app_user
            ADD CONSTRAINT app_user_role_check
            CHECK (role IN ('admin', 'member'));
    END IF;
END $do$;
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS zitadel_sub TEXT;
DO $do$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'app_user'
          AND c.conname = 'app_user_zitadel_sub_key'
    ) THEN
        ALTER TABLE app_user
            ADD CONSTRAINT app_user_zitadel_sub_key UNIQUE (zitadel_sub);
    END IF;
END $do$;
CREATE INDEX IF NOT EXISTS idx_app_user_org ON app_user(org_id);
CREATE INDEX IF NOT EXISTS idx_app_user_zitadel_sub
    ON app_user(zitadel_sub) WHERE zitadel_sub IS NOT NULL;

-- 3. Backfill: bucket each existing user into an org by email domain.
-- The first user at a corporate domain becomes admin; subsequent ones
-- join as members. Free-email domains get a per-email personal org.
DO $do$
DECLARE
    free_domains TEXT[] := ARRAY[
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'proton.me', 'icloud.com', 'fastmail.com'
    ];
    user_rec       RECORD;
    user_domain    TEXT;
    target_org_id  UUID;
BEGIN
    FOR user_rec IN
        SELECT id, email
        FROM app_user
        WHERE org_id IS NULL
        ORDER BY created_at NULLS LAST, id
    LOOP
        user_domain := lower(split_part(user_rec.email, '@', 2));

        IF user_domain = ANY(free_domains) THEN
            -- Personal org, one per legacy user.
            INSERT INTO org (name, domain, kind)
                VALUES ('personal:' || user_rec.email, NULL, 'personal')
                RETURNING id INTO target_org_id;
            UPDATE app_user
                SET org_id = target_org_id, role = 'admin'
                WHERE id = user_rec.id;
        ELSE
            -- Corporate org by domain.
            SELECT id INTO target_org_id
                FROM org
                WHERE domain = user_domain AND kind = 'corporate';
            IF target_org_id IS NULL THEN
                INSERT INTO org (name, domain, kind)
                    VALUES (user_domain, user_domain, 'corporate')
                    RETURNING id INTO target_org_id;
                UPDATE app_user
                    SET org_id = target_org_id, role = 'admin'
                    WHERE id = user_rec.id;
            ELSE
                UPDATE app_user
                    SET org_id = target_org_id, role = 'member'
                    WHERE id = user_rec.id;
            END IF;
        END IF;
    END LOOP;
END $do$;

-- 4. app_user.org_id NOT NULL now that every row is backfilled.
ALTER TABLE app_user ALTER COLUMN org_id SET NOT NULL;

-- 5. api_key new columns (scopes, revoked_at, revoked_reason).
-- name, last_used_at, expires_at already exist from the original schema.
ALTER TABLE api_key ADD COLUMN IF NOT EXISTS scopes TEXT[];
ALTER TABLE api_key ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;
ALTER TABLE api_key ADD COLUMN IF NOT EXISTS revoked_reason TEXT;

-- 6. Backfill: every legacy key gets the catch-all WoT scope.
UPDATE api_key SET scopes = ARRAY['wot:*']::TEXT[] WHERE scopes IS NULL;

-- 7. api_key.scopes NOT NULL with a sane default for new rows.
ALTER TABLE api_key ALTER COLUMN scopes SET NOT NULL;
ALTER TABLE api_key ALTER COLUMN scopes SET DEFAULT ARRAY['wot:*']::TEXT[];

-- 8. Replace the prefix index with a partial index that ignores
-- revoked keys, so lookups skip dead rows automatically.
DROP INDEX IF EXISTS idx_apikey_prefix;
CREATE INDEX idx_apikey_prefix
    ON api_key(key_prefix) WHERE revoked_at IS NULL;

-- 9. magic_link_token table (one-time email sign-in for /developers).
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
