"""Layer D: magic-link sign-in tokens.

The magic-link flow has three moving pieces:
  - mint_token(user_id) returns the raw token (mailed once) and
    persists only its hash + a TTL.
  - consume_token(raw) returns the user record once; subsequent
    calls fail (single-use, server-side nonce).
  - send_login_email(email, link) hits an injectable EmailClient
    so tests can run with a stub.

15-minute TTL matches the Vercel / Linear / Notion convention. We
hash the token with SHA-256 (not bcrypt) because we need O(1)
lookup by hash and one-time tokens are throwaway anyway.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _make_user(conn, email="dev@acme.com"):
    org_id = await conn.fetchval(
        "INSERT INTO org (name, domain, kind) VALUES ('acme', 'acme.com', 'corporate') RETURNING id"
    )
    return await conn.fetchval(
        "INSERT INTO app_user (email, org_id, role) VALUES ($1, $2, 'admin') RETURNING id",
        email, org_id,
    )


class TestMagicLinkTokens:
    def test_mint_token_returns_raw_and_persists_hash(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.magic_link import mint_token
            async with db_pool.acquire() as conn:
                user_id = await _make_user(conn)
                raw = await mint_token(conn, user_id)
                assert isinstance(raw, str) and len(raw) >= 32
                # The DB stores the hash, not the raw value.
                row = await conn.fetchrow(
                    "SELECT token_hash, expires_at, consumed_at FROM magic_link_token WHERE user_id = $1",
                    user_id,
                )
                assert row is not None
                assert row["token_hash"] != raw
                assert row["consumed_at"] is None
                # 15-minute TTL by default.
                ttl = row["expires_at"] - datetime.now(timezone.utc)
                assert timedelta(minutes=14) < ttl < timedelta(minutes=16)
        _run(_test())

    def test_consume_token_returns_user_once(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.magic_link import mint_token, consume_token
            async with db_pool.acquire() as conn:
                user_id = await _make_user(conn)
                raw = await mint_token(conn, user_id)
                first = await consume_token(conn, raw)
                assert first is not None
                assert str(first["user_id"]) == str(user_id)
        _run(_test())

    def test_consume_token_is_single_use(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.magic_link import mint_token, consume_token
            async with db_pool.acquire() as conn:
                user_id = await _make_user(conn)
                raw = await mint_token(conn, user_id)
                await consume_token(conn, raw)
                second = await consume_token(conn, raw)
                assert second is None
        _run(_test())

    def test_consume_token_expired_returns_none(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.magic_link import consume_token
            import hashlib
            import secrets
            async with db_pool.acquire() as conn:
                user_id = await _make_user(conn)
                raw = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(raw.encode()).hexdigest()
                await conn.execute(
                    """INSERT INTO magic_link_token (user_id, token_hash, expires_at)
                       VALUES ($1, $2, $3)""",
                    user_id, token_hash,
                    datetime.now(timezone.utc) - timedelta(seconds=1),
                )
                result = await consume_token(conn, raw)
                assert result is None
        _run(_test())

    def test_consume_unknown_token_returns_none(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.magic_link import consume_token
            async with db_pool.acquire() as conn:
                result = await consume_token(conn, "this-token-was-never-minted")
                assert result is None
        _run(_test())


class TestEmailDelivery:
    def test_send_login_email_uses_injected_client(self):
        from world_of_taxonomy.auth.email import send_login_email

        sent = []

        class StubClient:
            def send(self, *, to, subject, html, text):
                sent.append({"to": to, "subject": subject, "html": html, "text": text})

        send_login_email(
            client=StubClient(),
            to="dev@acme.com",
            magic_link_url="https://worldoftaxonomy.com/auth/magic?t=abc",
        )
        assert len(sent) == 1
        assert sent[0]["to"] == "dev@acme.com"
        # Clear sender pattern: the link is the centerpiece.
        assert "https://worldoftaxonomy.com/auth/magic?t=abc" in sent[0]["text"]
        assert "https://worldoftaxonomy.com/auth/magic?t=abc" in sent[0]["html"]
        assert "sign in" in sent[0]["subject"].lower() or "magic" in sent[0]["subject"].lower()

    def test_no_op_email_client_when_unconfigured(self, capsys):
        """When RESEND_API_KEY is unset, send_login_email logs a warning
        instead of raising. Signup must not 500 on infra problems users
        cannot fix."""
        from world_of_taxonomy.auth.email import NoopEmailClient
        client = NoopEmailClient()
        client.send(to="x@y.com", subject="s", html="<p>hi</p>", text="hi")
        # No exception is the contract; output is informational.


def _fake_http_response(body_bytes):
    """Minimal context-manager stand-in for urllib's urlopen result."""

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return body_bytes

    return _Resp()


class TestResendClient:
    """ResendClient posts a single request to api.resend.com. These
    tests mock the HTTP layer, so no API key and no network are
    needed."""

    def test_send_posts_expected_resend_payload(self, monkeypatch):
        import json

        from world_of_taxonomy.auth.email import ResendClient

        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _fake_http_response(b'{"id":"abc-123"}')

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        ResendClient(api_key="re_test", sender="noreply@aixcelerator.ai").send(
            to="dev@acme.com",
            subject="Sign in to WorldOfTaxonomy",
            html="<p>link</p>",
            text="link",
        )

        assert captured["url"] == "https://api.resend.com/emails"
        assert captured["method"] == "POST"
        body = captured["body"]
        assert body["from"] == "noreply@aixcelerator.ai"
        assert body["to"] == ["dev@acme.com"]
        assert body["subject"] == "Sign in to WorldOfTaxonomy"

    def test_send_sets_explicit_user_agent(self, monkeypatch):
        """api.resend.com sits behind Cloudflare, which blocks urllib's
        default `Python-urllib/x.y` User-Agent with HTTP 403 ("error
        code: 1010"). The client must send an explicit, non-default UA
        or every magic-link email is silently dropped at the edge."""
        from world_of_taxonomy.auth.email import ResendClient

        captured = {}

        def fake_urlopen(req, timeout=None):
            # urllib normalises header keys to "User-agent".
            captured["ua"] = req.get_header("User-agent")
            return _fake_http_response(b'{"id":"abc-123"}')

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        ResendClient(api_key="re_test").send(
            to="x@y.com", subject="s", html="<p>h</p>", text="h",
        )
        assert captured["ua"]
        assert "python-urllib" not in captured["ua"].lower()

    def test_send_does_not_raise_on_http_error(self, monkeypatch, caplog):
        """A 403 / bad key must be swallowed and logged with the response
        body: signup cannot 500 on an email-infrastructure failure, and
        the body is what distinguishes an API error from a Cloudflare
        edge block."""
        import io
        import urllib.error

        from world_of_taxonomy.auth.email import ResendClient

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 403, "Forbidden", {},
                io.BytesIO(b"error code: 1010"),
            )

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        with caplog.at_level("ERROR", logger="wot.auth.email"):
            ResendClient(api_key="re_bad").send(
                to="x@y.com", subject="s", html="<p>h</p>", text="h",
            )
        messages = [r.getMessage() for r in caplog.records]
        assert any("resend_send_failed" in m for m in messages)
        assert any("1010" in m for m in messages)
