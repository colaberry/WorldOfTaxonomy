"""Tests that verify the per-IP rate guard is wired onto the right
endpoints with the right caps.

These are wiring tests, not behaviour tests. The rate-guard mechanism
itself is covered exhaustively in tests/test_rate_guard.py; here we
just assert that:

  - each protected route calls check_per_ip_rate
  - the endpoint_name matches the documented scope (per_ip:<name>)
  - the max_per_window matches the documented cap

We stub check_per_ip_rate to always raise 429 so we can capture its
arguments without needing real DB/LLM/network state. The real
end-to-end behaviour ("the 6th attempt returns 429") is covered by
tests/test_api_developers.py and tests/test_api_classify_demo.py for
the canonical signup + classify-demo flows; the same code path runs
here, so a wiring test is sufficient.
"""

import asyncio

import pytest
from fastapi import HTTPException


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _Client:
    host = "1.2.3.4"


class _StubRequest:
    client = _Client()
    headers = {}


def _install_capture(monkeypatch, target_module):
    """Replace check_per_ip_rate in `target_module` with a stub that
    captures its kwargs and always raises 429. Returns the capture dict.
    """
    captured = {}

    def _stub(endpoint_name, request, max_per_window=None, **kw):
        captured["endpoint_name"] = endpoint_name
        captured["max_per_window"] = max_per_window
        captured["kwargs"] = kw
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "scope": f"per_ip:{endpoint_name}",
            },
        )

    monkeypatch.setattr(target_module, "check_per_ip_rate", _stub)
    return captured


class TestAuthRegisterRateGuard:
    def test_register_route_calls_rate_guard_with_5_per_hour(self, monkeypatch):
        from world_of_taxonomy.api.routers import auth as auth_mod
        captured = _install_capture(monkeypatch, auth_mod)

        body = auth_mod.RegisterRequest(
            email="x@example.com", password="pwd12345", display_name="X",
        )

        async def go():
            with pytest.raises(HTTPException) as exc:
                await auth_mod.register(body, _StubRequest(), conn=None)
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "auth_register"
        assert captured["max_per_window"] == 5


class TestContactRateGuard:
    def test_contact_route_calls_rate_guard_with_5_per_hour(self, monkeypatch):
        from world_of_taxonomy.api.routers import contact as contact_mod
        captured = _install_capture(monkeypatch, contact_mod)

        body = contact_mod.ContactRequest(
            name="Jane Doe",
            company="Acme",
            email="jane@example.com",
            message="Hello, this is at least ten characters long.",
        )

        async def go():
            with pytest.raises(HTTPException) as exc:
                await contact_mod.submit_contact(body, _StubRequest())
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "contact"
        assert captured["max_per_window"] == 5


class TestSearchRateGuard:
    def test_search_route_calls_rate_guard_with_200_per_hour(self, monkeypatch):
        from world_of_taxonomy.api.routers import search as search_mod
        captured = _install_capture(monkeypatch, search_mod)

        async def go():
            with pytest.raises(HTTPException) as exc:
                await search_mod.search(_StubRequest(), q="health", conn=None)
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "search"
        assert captured["max_per_window"] == 200


class TestMcpHttpRateGuard:
    def test_mcp_http_route_calls_rate_guard_with_600_per_hour(self, monkeypatch):
        from world_of_taxonomy.api.routers import mcp_http as mcp_mod
        captured = _install_capture(monkeypatch, mcp_mod)

        async def go():
            with pytest.raises(HTTPException) as exc:
                await mcp_mod.mcp_http_bridge(_StubRequest())
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "mcp_http"
        assert captured["max_per_window"] == 600


class TestAuthSessionRateGuard:
    """The /auth/me, /auth/keys GET, and /auth/keys DELETE endpoints
    share an `auth_session` bucket at 120/min/IP. The /auth/keys POST
    endpoint additionally has its own `auth_keys_create` cap at 10/hour.
    """

    def test_get_me_calls_auth_session_guard(self, monkeypatch):
        from world_of_taxonomy.api.routers import auth as auth_mod
        captured = _install_capture(monkeypatch, auth_mod)

        async def go():
            with pytest.raises(HTTPException) as exc:
                await auth_mod.get_me(_StubRequest(), conn=None)
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "auth_session"
        assert captured["max_per_window"] == 120
        assert captured["kwargs"].get("window_seconds") == 60

    def test_create_api_key_calls_auth_keys_create_guard(self, monkeypatch):
        from world_of_taxonomy.api.routers import auth as auth_mod
        from world_of_taxonomy.api.schemas import CreateApiKeyRequest

        captured = _install_capture(monkeypatch, auth_mod)
        body = CreateApiKeyRequest(name="ci")

        async def go():
            with pytest.raises(HTTPException) as exc:
                await auth_mod.create_api_key(body, _StubRequest(), conn=None)
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "auth_keys_create"
        assert captured["max_per_window"] == 10

    def test_list_api_keys_calls_auth_session_guard(self, monkeypatch):
        from world_of_taxonomy.api.routers import auth as auth_mod
        captured = _install_capture(monkeypatch, auth_mod)

        async def go():
            with pytest.raises(HTTPException) as exc:
                await auth_mod.list_api_keys(_StubRequest(), conn=None)
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "auth_session"
        assert captured["max_per_window"] == 120

    def test_deactivate_api_key_calls_auth_session_guard(self, monkeypatch):
        from world_of_taxonomy.api.routers import auth as auth_mod
        captured = _install_capture(monkeypatch, auth_mod)

        async def go():
            with pytest.raises(HTTPException) as exc:
                await auth_mod.deactivate_api_key(
                    "00000000-0000-0000-0000-000000000000",
                    _StubRequest(),
                    conn=None,
                )
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "auth_session"
        assert captured["max_per_window"] == 120


class TestDevelopersKeysCreateRateGuard:
    def test_create_key_calls_rate_guard_with_10_per_hour(self, monkeypatch):
        from world_of_taxonomy.api.routers import developers as dev_mod

        captured = _install_capture(monkeypatch, dev_mod)
        body = dev_mod.CreateKeyRequest(name="ci", scopes=["wot:read"])

        async def go():
            with pytest.raises(HTTPException) as exc:
                await dev_mod.create_key(
                    body,
                    _StubRequest(),
                    user={"id": "00000000-0000-0000-0000-000000000000"},
                    conn=None,
                )
            assert exc.value.status_code == 429

        _run(go())
        assert captured["endpoint_name"] == "developers_keys_create"
        assert captured["max_per_window"] == 10
