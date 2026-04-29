"""Layer C: key issuance + validation against the database.

Covers the full lifecycle:
  - issue_key returns the raw key once and stores only the bcrypt hash.
  - validate_key returns the user record + scopes when the key is good.
  - Missing scope -> denied (caller decides 401 vs 403).
  - Revoked / expired keys -> denied.
  - last_used_at is bumped on each successful validation.
  - Legacy `wot_<32hex>` keys created before Phase 6 keep working
    because the migration backfilled scopes=['wot:*'].
"""

import asyncio
from datetime import datetime, timedelta, timezone

import bcrypt


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# Issuance


class TestIssueKey:
    def test_returns_raw_once_and_bcrypt_hash(self):
        from world_of_taxonomy.auth.keys import issue_key
        out = issue_key(["wot:read"])
        # Exactly the four expected fields.
        assert set(out) == {"raw_key", "prefix", "key_prefix", "key_hash"}
        # Restricted scope -> rwot_ prefix.
        assert out["prefix"] == "rwot_"
        assert out["raw_key"].startswith("rwot_")
        # 8-char prefix index.
        assert len(out["key_prefix"]) == 8
        # Hash verifies against the raw key.
        assert bcrypt.checkpw(out["raw_key"].encode(), out["key_hash"].encode())
        # Wrong key does not verify (sanity).
        assert not bcrypt.checkpw(b"wrong", out["key_hash"].encode())

    def test_full_wot_key_uses_wot_prefix(self):
        from world_of_taxonomy.auth.keys import issue_key
        out = issue_key(["wot:*"])
        assert out["prefix"] == "wot_"
        assert out["raw_key"].startswith("wot_")

    def test_cross_product_uses_aix_prefix(self):
        from world_of_taxonomy.auth.keys import issue_key
        out = issue_key(["wot:*", "woo:*"])
        assert out["prefix"] == "aix_"


# Validation against the DB


async def _make_user(conn, email="dev@acme.com"):
    org_id = await conn.fetchval(
        """INSERT INTO org (name, domain, kind)
           VALUES ('acme', 'acme.com', 'corporate') RETURNING id"""
    )
    user_id = await conn.fetchval(
        """INSERT INTO app_user (email, org_id, role)
           VALUES ($1, $2, 'admin') RETURNING id""",
        email, org_id,
    )
    return user_id, org_id


async def _store_issued_key(conn, user_id, scopes, **overrides):
    from world_of_taxonomy.auth.keys import issue_key
    minted = issue_key(scopes)
    fields = {
        "user_id": user_id,
        "key_hash": minted["key_hash"],
        "key_prefix": minted["key_prefix"],
        "scopes": scopes,
        "name": "test",
    }
    fields.update(overrides)
    await conn.execute(
        """INSERT INTO api_key (user_id, key_hash, key_prefix, scopes, name,
                                expires_at, revoked_at, revoked_reason)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        fields["user_id"], fields["key_hash"], fields["key_prefix"],
        fields["scopes"], fields["name"],
        fields.get("expires_at"), fields.get("revoked_at"),
        fields.get("revoked_reason"),
    )
    return minted["raw_key"]


class TestValidateKey:
    def test_validate_returns_user_with_scopes_when_required_granted(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            async with db_pool.acquire() as conn:
                user_id, _ = await _make_user(conn)
                raw = await _store_issued_key(conn, user_id, ["wot:read", "wot:list"])
                result = await validate_key(conn, raw, required_scope="wot:read")
                assert result["allow"] is True
                assert str(result["user_id"]) == str(user_id)
                assert "wot:read" in result["scopes"]
        _run(_test())

    def test_validate_denies_when_scope_missing(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            async with db_pool.acquire() as conn:
                user_id, _ = await _make_user(conn)
                raw = await _store_issued_key(conn, user_id, ["wot:read"])
                result = await validate_key(conn, raw, required_scope="wot:admin")
                assert result["allow"] is False
                # Differentiated reason so the API layer can choose 401 vs 403.
                assert result["reason"] == "scope_missing"
        _run(_test())

    def test_validate_revoked_key_denied(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            async with db_pool.acquire() as conn:
                user_id, _ = await _make_user(conn)
                raw = await _store_issued_key(
                    conn, user_id, ["wot:*"],
                    revoked_at=datetime.now(timezone.utc),
                    revoked_reason="rotated",
                )
                result = await validate_key(conn, raw, required_scope="wot:read")
                assert result["allow"] is False
                assert result["reason"] == "revoked"
        _run(_test())

    def test_validate_expired_key_denied(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            async with db_pool.acquire() as conn:
                user_id, _ = await _make_user(conn)
                raw = await _store_issued_key(
                    conn, user_id, ["wot:*"],
                    expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                )
                result = await validate_key(conn, raw, required_scope="wot:read")
                assert result["allow"] is False
                assert result["reason"] == "expired"
        _run(_test())

    def test_validate_unknown_key_denied(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            async with db_pool.acquire() as conn:
                # No matching prefix in DB.
                result = await validate_key(
                    conn, "wot_deadbeefdeadbeefdeadbeefdeadbeef",
                    required_scope="wot:read",
                )
                assert result["allow"] is False
                assert result["reason"] == "not_found"
        _run(_test())

    def test_validate_bumps_last_used_at(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            async with db_pool.acquire() as conn:
                user_id, _ = await _make_user(conn)
                raw = await _store_issued_key(conn, user_id, ["wot:*"])
                before = await conn.fetchval(
                    "SELECT last_used_at FROM api_key WHERE user_id = $1", user_id
                )
                assert before is None
                await validate_key(conn, raw, required_scope="wot:read")
                after = await conn.fetchval(
                    "SELECT last_used_at FROM api_key WHERE user_id = $1", user_id
                )
                assert after is not None
        _run(_test())

    def test_legacy_wot_key_validates_under_wot_star(self, db_pool):
        """A pre-Phase-6 wot_<32hex> key was backfilled with scopes=['wot:*'].

        After migration, validating it for any wot:* action must still
        allow. Same key shape, same DB column conventions; only the
        scopes column is new.
        """
        async def _test():
            from world_of_taxonomy.auth.keys import validate_key
            import secrets
            async with db_pool.acquire() as conn:
                user_id, _ = await _make_user(conn)
                # Mint a legacy-shape key by hand: wot_ + 32 hex.
                raw = "wot_" + secrets.token_hex(16)
                key_hash = bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()
                await conn.execute(
                    """INSERT INTO api_key (user_id, key_hash, key_prefix, scopes, name)
                       VALUES ($1, $2, $3, $4, 'legacy')""",
                    user_id, key_hash, raw[4:12], ["wot:*"],
                )
                # Old key, new scope check.
                for action in ("wot:read", "wot:list", "wot:classify"):
                    result = await validate_key(conn, raw, required_scope=action)
                    assert result["allow"] is True, action
        _run(_test())
