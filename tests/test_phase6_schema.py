"""Phase 6 schema tests: org table, app_user new columns, api_key new columns, migration backfill.

Layer A of the developer-key system. These tests assert the
post-migration shape of the auth tables so that the standalone
extraction to developer.aixcelerator.ai later is a copy of the
schema, not a redesign.
"""

import asyncio
from pathlib import Path

import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# Layer A test 1 - org table exists


class TestOrgTable:
    def test_org_table_exists_with_required_columns(self, db_pool):
        """org has id, name, domain UNIQUE nullable, kind CHECK, tier, rate_limit_pool_per_minute, stripe_customer_id, zitadel_org_id."""
        async def _test():
            async with db_pool.acquire() as conn:
                cols = await conn.fetch(
                    """SELECT column_name, data_type, is_nullable
                       FROM information_schema.columns
                       WHERE table_schema = current_schema() AND table_name = 'org'
                       ORDER BY ordinal_position"""
                )
                names = {c["column_name"] for c in cols}
                assert {"id", "name", "domain", "kind", "tier",
                        "rate_limit_pool_per_minute", "stripe_customer_id",
                        "zitadel_org_id", "created_at"}.issubset(names)

                # domain must be UNIQUE (nullable allowed for personal orgs without a real domain)
                uniques = await conn.fetch(
                    """SELECT tc.constraint_name
                       FROM information_schema.table_constraints tc
                       JOIN information_schema.key_column_usage k
                         ON tc.constraint_name = k.constraint_name
                       WHERE tc.table_schema = current_schema()
                         AND tc.table_name = 'org'
                         AND tc.constraint_type = 'UNIQUE'
                         AND k.column_name = 'domain'"""
                )
                assert len(uniques) >= 1, "domain must be UNIQUE on org"

                # kind CHECK constraint admits only 'corporate' and 'personal'
                row = await conn.fetchval(
                    """SELECT pg_get_constraintdef(c.oid)
                       FROM pg_constraint c
                       JOIN pg_class t ON c.conrelid = t.oid
                       JOIN pg_namespace n ON t.relnamespace = n.oid
                       WHERE n.nspname = current_schema()
                         AND t.relname = 'org'
                         AND c.contype = 'c'
                         AND pg_get_constraintdef(c.oid) ILIKE '%kind%'"""
                )
                assert row is not None and "corporate" in row and "personal" in row

        _run(_test())


# Layer A test 2 - app_user new columns


class TestAppUserColumns:
    def test_app_user_has_org_id_not_null_role_zitadel_sub(self, db_pool):
        """app_user.org_id NOT NULL FK to org; role default 'member'; zitadel_sub UNIQUE nullable."""
        async def _test():
            async with db_pool.acquire() as conn:
                cols = {
                    c["column_name"]: c
                    for c in await conn.fetch(
                        """SELECT column_name, is_nullable, column_default
                           FROM information_schema.columns
                           WHERE table_schema = current_schema()
                             AND table_name = 'app_user'"""
                    )
                }
                assert "org_id" in cols
                assert cols["org_id"]["is_nullable"] == "NO"
                assert "role" in cols
                assert "zitadel_sub" in cols
                assert cols["zitadel_sub"]["is_nullable"] == "YES"

                # zitadel_sub UNIQUE
                row = await conn.fetchval(
                    """SELECT count(*)
                       FROM information_schema.table_constraints tc
                       JOIN information_schema.key_column_usage k
                         ON tc.constraint_name = k.constraint_name
                       WHERE tc.table_schema = current_schema()
                         AND tc.table_name = 'app_user'
                         AND tc.constraint_type = 'UNIQUE'
                         AND k.column_name = 'zitadel_sub'"""
                )
                assert row >= 1

                # org_id FK
                fks = await conn.fetch(
                    """SELECT k.column_name
                       FROM information_schema.table_constraints tc
                       JOIN information_schema.key_column_usage k
                         ON tc.constraint_name = k.constraint_name
                       WHERE tc.table_schema = current_schema()
                         AND tc.table_name = 'app_user'
                         AND tc.constraint_type = 'FOREIGN KEY'
                         AND k.column_name = 'org_id'"""
                )
                assert len(fks) >= 1
        _run(_test())


# Layer A test 3 - api_key new columns


class TestApiKeyColumns:
    def test_api_key_has_scopes_revoked_at_expires_at_name(self, db_pool):
        """api_key.scopes TEXT[] NOT NULL, revoked_at, revoked_reason, expires_at, last_used_at, name."""
        async def _test():
            async with db_pool.acquire() as conn:
                cols = {
                    c["column_name"]: c
                    for c in await conn.fetch(
                        """SELECT column_name, data_type, is_nullable, udt_name
                           FROM information_schema.columns
                           WHERE table_schema = current_schema()
                             AND table_name = 'api_key'"""
                    )
                }
                for required in ("scopes", "revoked_at", "revoked_reason",
                                 "expires_at", "last_used_at", "name"):
                    assert required in cols, f"missing column {required}"

                # scopes is an array of TEXT, NOT NULL
                assert cols["scopes"]["data_type"] == "ARRAY"
                assert cols["scopes"]["udt_name"] == "_text"
                assert cols["scopes"]["is_nullable"] == "NO"

                # revoked_at, expires_at nullable
                assert cols["revoked_at"]["is_nullable"] == "YES"
                assert cols["expires_at"]["is_nullable"] == "YES"
        _run(_test())


# Layer A test 4 - migration backfills existing rows correctly


class TestMigrationBackfill:
    def test_migration_backfills_users_and_keys(self, db_pool):
        """Apply the migration to a pre-Phase-6 schema seeded with legacy rows.

        Expectations after the migration runs:
          - alice@gmail.com lands in a personal org (kind='personal').
          - bob@acme.com and carol@acme.com share one corporate org (kind='corporate', domain='acme.com').
          - bob is admin (first signup at the domain), carol is member.
          - Every legacy api_key row has scopes = ['wot:*'].
        """
        async def _test():
            mig_path = (
                Path(__file__).parent.parent
                / "world_of_taxonomy"
                / "migrations"
                / "003_phase6_developer_keys.sql"
            )
            assert mig_path.exists(), f"migration not found: {mig_path}"
            migration_sql = mig_path.read_text()

            async with db_pool.acquire() as conn:
                # Build an isolated scratch schema with the pre-Phase-6 shape.
                await conn.execute("DROP SCHEMA IF EXISTS test_wot_migration CASCADE")
                await conn.execute("CREATE SCHEMA test_wot_migration")
                await conn.execute("SET search_path TO test_wot_migration")
                await conn.execute(
                    """CREATE TABLE app_user (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT,
                        display_name TEXT,
                        tier TEXT NOT NULL DEFAULT 'free'
                            CHECK (tier IN ('free','pro','enterprise')),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )"""
                )
                await conn.execute(
                    """CREATE TABLE api_key (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
                        key_hash TEXT NOT NULL,
                        key_prefix TEXT NOT NULL,
                        name TEXT DEFAULT 'Default',
                        is_active BOOLEAN DEFAULT TRUE,
                        last_used_at TIMESTAMPTZ,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        expires_at TIMESTAMPTZ
                    )"""
                )

                # Seed legacy rows: 1 gmail user, 2 acme users (bob first, carol later).
                alice_id = await conn.fetchval(
                    "INSERT INTO app_user (email) VALUES ('alice@gmail.com') RETURNING id"
                )
                bob_id = await conn.fetchval(
                    "INSERT INTO app_user (email) VALUES ('bob@acme.com') RETURNING id"
                )
                carol_id = await conn.fetchval(
                    "INSERT INTO app_user (email) VALUES ('carol@acme.com') RETURNING id"
                )
                # Seed one legacy api_key for alice.
                await conn.execute(
                    """INSERT INTO api_key (user_id, key_hash, key_prefix, name)
                       VALUES ($1, 'fake_hash', 'abcd1234', 'legacy')""",
                    alice_id,
                )

                # Apply the migration in this scratch schema.
                await conn.execute(migration_sql)

                # alice@gmail.com -> personal org
                alice_org = await conn.fetchrow(
                    """SELECT o.kind, o.domain, u.role
                       FROM app_user u JOIN org o ON u.org_id = o.id
                       WHERE u.id = $1""",
                    alice_id,
                )
                assert alice_org["kind"] == "personal"

                # bob and carol share one acme.com corporate org
                bob_org_id = await conn.fetchval(
                    "SELECT org_id FROM app_user WHERE id = $1", bob_id
                )
                carol_org_id = await conn.fetchval(
                    "SELECT org_id FROM app_user WHERE id = $1", carol_id
                )
                assert bob_org_id == carol_org_id, "acme users must share one org"
                acme_org = await conn.fetchrow(
                    "SELECT kind, domain FROM org WHERE id = $1", bob_org_id
                )
                assert acme_org["kind"] == "corporate"
                assert acme_org["domain"] == "acme.com"

                # bob is admin (first signup), carol is member.
                bob_role = await conn.fetchval(
                    "SELECT role FROM app_user WHERE id = $1", bob_id
                )
                carol_role = await conn.fetchval(
                    "SELECT role FROM app_user WHERE id = $1", carol_id
                )
                assert bob_role == "admin"
                assert carol_role == "member"

                # Legacy api_key got scopes = ['wot:*']
                key_scopes = await conn.fetchval(
                    "SELECT scopes FROM api_key WHERE key_prefix = 'abcd1234'"
                )
                assert key_scopes == ["wot:*"]

                # Cleanup
                await conn.execute("DROP SCHEMA test_wot_migration CASCADE")
        _run(_test())
