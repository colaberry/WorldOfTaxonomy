"""Tests for the authentication system.

Covers: registration, login, JWT validation, API key lifecycle, password hashing.
Uses the test_wot schema (never touches production data).
"""

import asyncio
import bcrypt
import jwt
import pytest
import secrets
from datetime import datetime, timedelta, timezone

from world_of_taxonomy.api.deps import JWT_SECRET, JWT_ALGORITHM
from tests.conftest import DEFAULT_TEST_ORG_ID


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Password Hashing ──


class TestPasswordHashing:
    def test_bcrypt_hash_roundtrip(self):
        """Password hashing and verification works correctly."""
        password = "testpassword123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert bcrypt.checkpw(password.encode(), hashed.encode())

    def test_bcrypt_wrong_password_fails(self):
        """Wrong password does not verify."""
        password = "correctpassword"
        wrong = "wrongpassword"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert not bcrypt.checkpw(wrong.encode(), hashed.encode())

    def test_bcrypt_different_salts_produce_different_hashes(self):
        """Same password with different salts produces different hashes."""
        password = "samepassword"
        hash1 = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        hash2 = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert hash1 != hash2
        # But both verify
        assert bcrypt.checkpw(password.encode(), hash1.encode())
        assert bcrypt.checkpw(password.encode(), hash2.encode())


# ── JWT Tokens ──


class TestJWT:
    def test_create_and_decode_token(self):
        """JWT token can be created and decoded."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        payload = {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc)}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == user_id

    def test_expired_token_raises(self):
        """Expired JWT raises ExpiredSignatureError."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {"sub": user_id, "exp": expire}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    def test_invalid_secret_raises(self):
        """JWT with wrong secret raises InvalidSignatureError."""
        payload = {"sub": "test", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        token = jwt.encode(payload, "wrong-secret", algorithm=JWT_ALGORITHM)

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    def test_token_contains_required_claims(self):
        """Token has sub, exp, and iat claims."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        payload = {"sub": user_id, "exp": expire, "iat": datetime.now(timezone.utc)}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "sub" in decoded
        assert "exp" in decoded
        assert "iat" in decoded


# ── User Registration (Database) ──


class TestUserRegistration:
    def test_register_creates_user(self, db_pool):
        """Registering a user inserts a row in app_user."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                row = await conn.fetchrow(
                    """INSERT INTO app_user (email, password_hash, display_name, org_id)
                       VALUES ($1, $2, $3, $4::uuid) RETURNING id, email, tier, is_active""",
                    "test@example.com", password_hash, "Test User", DEFAULT_TEST_ORG_ID,
                )
                assert row["email"] == "test@example.com"
                assert row["tier"] == "free"
                assert row["is_active"] is True
                assert row["id"] is not None
        _run(_test())

    def test_duplicate_email_rejected(self, db_pool):
        """Duplicate email raises unique constraint error."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                await conn.execute(
                    "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid)",
                    "dup@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                )
                with pytest.raises(Exception):  # asyncpg.UniqueViolationError
                    await conn.execute(
                        "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid)",
                        "dup@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                    )
        _run(_test())

    def test_tier_check_constraint(self, db_pool):
        """Only valid tiers are accepted."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                with pytest.raises(Exception):  # asyncpg.CheckViolationError
                    await conn.execute(
                        "INSERT INTO app_user (email, password_hash, tier, org_id) VALUES ($1, $2, $3, $4::uuid)",
                        "tier@example.com", password_hash, "invalid_tier", DEFAULT_TEST_ORG_ID,
                    )
        _run(_test())

    def test_valid_tiers_accepted(self, db_pool):
        """free, pro, enterprise tiers are all valid."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                for i, tier in enumerate(["free", "pro", "enterprise"]):
                    await conn.execute(
                        "INSERT INTO app_user (email, password_hash, tier, org_id) VALUES ($1, $2, $3, $4::uuid)",
                        f"tier{i}@example.com", password_hash, tier, DEFAULT_TEST_ORG_ID,
                    )
                count = await conn.fetchval("SELECT COUNT(*) FROM app_user WHERE email LIKE 'tier%'")
                assert count == 3
        _run(_test())


# ── API Key Lifecycle ──


class TestApiKeyLifecycle:
    def test_create_api_key(self, db_pool):
        """Creating an API key stores hash and prefix."""
        async def _test():
            async with db_pool.acquire() as conn:
                # Create user first
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                user = await conn.fetchrow(
                    "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid) RETURNING id",
                    "apiuser@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                )

                # Generate key
                raw_key = "wot_" + secrets.token_hex(16)
                key_prefix = raw_key[4:12]
                key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

                row = await conn.fetchrow(
                    """INSERT INTO api_key (user_id, key_hash, key_prefix, name)
                       VALUES ($1, $2, $3, $4)
                       RETURNING id, key_prefix, name, is_active""",
                    user["id"], key_hash, key_prefix, "Test Key",
                )
                assert row["key_prefix"] == key_prefix
                assert row["name"] == "Test Key"
                assert row["is_active"] is True
        _run(_test())

    def test_api_key_format(self):
        """API keys follow the wot_ + 32 hex chars format."""
        raw_key = "wot_" + secrets.token_hex(16)
        assert raw_key.startswith("wot_")
        assert len(raw_key) == 36  # 4 + 32
        # The hex part should be valid hex
        int(raw_key[4:], 16)

    def test_api_key_prefix_extraction(self):
        """Key prefix is chars 4-12 of the raw key."""
        raw_key = "wot_" + "a1b2c3d4e5f6g7h8" + "i9j0k1l2m3n4o5p6"
        prefix = raw_key[4:12]
        assert prefix == "a1b2c3d4"

    def test_deactivate_api_key(self, db_pool):
        """Deactivating an API key sets is_active to FALSE."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                user = await conn.fetchrow(
                    "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid) RETURNING id",
                    "deactivate@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                )

                raw_key = "wot_" + secrets.token_hex(16)
                key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
                key = await conn.fetchrow(
                    """INSERT INTO api_key (user_id, key_hash, key_prefix, name)
                       VALUES ($1, $2, $3, $4) RETURNING id""",
                    user["id"], key_hash, raw_key[4:12], "To Deactivate",
                )

                await conn.execute(
                    "UPDATE api_key SET is_active = FALSE WHERE id = $1", key["id"]
                )

                row = await conn.fetchrow(
                    "SELECT is_active FROM api_key WHERE id = $1", key["id"]
                )
                assert row["is_active"] is False
        _run(_test())

    def test_api_key_verify_with_bcrypt(self, db_pool):
        """API key can be verified against its stored hash."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                user = await conn.fetchrow(
                    "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid) RETURNING id",
                    "verify@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                )

                raw_key = "wot_" + secrets.token_hex(16)
                key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
                await conn.execute(
                    """INSERT INTO api_key (user_id, key_hash, key_prefix, name)
                       VALUES ($1, $2, $3, $4)""",
                    user["id"], key_hash, raw_key[4:12], "Verify Key",
                )

                # Verify works
                rows = await conn.fetch(
                    "SELECT key_hash FROM api_key WHERE key_prefix = $1 AND is_active = TRUE",
                    raw_key[4:12],
                )
                assert len(rows) == 1
                assert bcrypt.checkpw(raw_key.encode(), rows[0]["key_hash"].encode())

                # Wrong key does not verify
                wrong_key = "wot_" + secrets.token_hex(16)
                assert not bcrypt.checkpw(wrong_key.encode(), rows[0]["key_hash"].encode())
        _run(_test())

    def test_cascade_delete_user_removes_keys(self, db_pool):
        """Deleting a user cascades to delete their API keys."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                user = await conn.fetchrow(
                    "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid) RETURNING id",
                    "cascade@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                )

                raw_key = "wot_" + secrets.token_hex(16)
                key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
                await conn.execute(
                    """INSERT INTO api_key (user_id, key_hash, key_prefix, name)
                       VALUES ($1, $2, $3, $4)""",
                    user["id"], key_hash, raw_key[4:12], "Cascade Key",
                )

                # Delete user
                await conn.execute("DELETE FROM app_user WHERE id = $1", user["id"])

                # API key should be gone
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM api_key WHERE user_id = $1", user["id"]
                )
                assert count == 0
        _run(_test())


# ── Usage Logging ──


class TestUsageLog:
    def test_insert_usage_log(self, db_pool):
        """Usage log entries can be inserted."""
        async def _test():
            async with db_pool.acquire() as conn:
                password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                user = await conn.fetchrow(
                    "INSERT INTO app_user (email, password_hash, org_id) VALUES ($1, $2, $3::uuid) RETURNING id",
                    "usage@example.com", password_hash, DEFAULT_TEST_ORG_ID,
                )

                await conn.execute(
                    """INSERT INTO usage_log (user_id, endpoint, method, status_code, ip_address)
                       VALUES ($1, $2, $3, $4, $5)""",
                    user["id"], "/api/v1/systems", "GET", 200, "127.0.0.1",
                )

                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM usage_log WHERE user_id = $1", user["id"]
                )
                assert count == 1
        _run(_test())

    def test_usage_log_without_user(self, db_pool):
        """Anonymous usage can be logged (user_id NULL)."""
        async def _test():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO usage_log (endpoint, method, status_code, ip_address)
                       VALUES ($1, $2, $3, $4)""",
                    "/api/v1/search", "GET", 200, "10.0.0.1",
                )
                row = await conn.fetchrow(
                    "SELECT user_id FROM usage_log WHERE ip_address = '10.0.0.1'"
                )
                assert row["user_id"] is None
        _run(_test())
