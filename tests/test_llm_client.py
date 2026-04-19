"""Tests for the shared LLM client (Ollama Cloud, OpenAI-compatible).

All HTTP is mocked; we never reach the real endpoint in tests.
"""
from __future__ import annotations

import asyncio

import httpx
import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestIsConfigured:
    def test_returns_false_without_any_api_key(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        assert llm_client.is_configured() is False

    def test_returns_true_with_ollama_key(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        assert llm_client.is_configured() is True

    def test_returns_true_with_only_openrouter_key(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")
        assert llm_client.is_configured() is True


class TestActiveModel:
    def test_returns_none_without_any_key(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        assert llm_client.active_model() is None

    def test_returns_ollama_default_when_no_override(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        assert llm_client.active_model() == llm_client.DEFAULT_MODEL

    def test_respects_ollama_model_override(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.setenv("OLLAMA_MODEL", "custom-model:42b")
        assert llm_client.active_model() == "custom-model:42b"

    def test_prefers_ollama_when_both_providers_configured(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        assert llm_client.active_model() == llm_client.DEFAULT_MODEL

    def test_returns_openrouter_model_when_only_openrouter(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        assert llm_client.active_model() == llm_client.DEFAULT_OPENROUTER_MODEL


class TestChatJson:
    def test_raises_when_no_provider_configured(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(llm_client.LLMNotConfiguredError):
            _run(llm_client.chat_json([{"role": "user", "content": "hi"}]))

    def test_posts_to_ollama_cloud_openai_compatible_endpoint(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

        captured = {}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                captured["client_timeout"] = kwargs.get("timeout")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, url, json=None, headers=None):
                captured["url"] = url
                captured["json"] = json
                captured["headers"] = headers
                return httpx.Response(
                    200,
                    json={
                        "choices": [
                            {"message": {"content": '{"ok": true}'}}
                        ]
                    },
                    request=httpx.Request("POST", url),
                )

        monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

        result = _run(
            llm_client.chat_json(
                [{"role": "user", "content": "hello"}],
                model="gpt-oss:20b",
                max_tokens=64,
                temperature=0.1,
            )
        )

        assert result == '{"ok": true}'
        assert captured["url"] == "https://ollama.com/v1/chat/completions"
        assert captured["headers"]["Authorization"] == "Bearer fake-key"
        assert captured["json"]["model"] == "gpt-oss:20b"
        assert captured["json"]["messages"] == [
            {"role": "user", "content": "hello"}
        ]
        assert captured["json"]["max_tokens"] == 64
        assert captured["json"]["temperature"] == 0.1

    def test_respects_base_url_override(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_BASE_URL", "https://my-proxy.example.com/v1")

        captured = {}

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, url, json=None, headers=None):
                captured["url"] = url
                return httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": "ok"}}]},
                    request=httpx.Request("POST", url),
                )

        monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

        _run(llm_client.chat_json([{"role": "user", "content": "x"}]))
        assert captured["url"] == "https://my-proxy.example.com/v1/chat/completions"

    def test_uses_default_model_when_not_specified(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)

        captured = {}

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, url, json=None, headers=None):
                captured["model"] = json["model"]
                return httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": "ok"}}]},
                    request=httpx.Request("POST", url),
                )

        monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

        _run(llm_client.chat_json([{"role": "user", "content": "x"}]))
        assert captured["model"] == llm_client.DEFAULT_MODEL

    def test_raises_llm_error_on_http_error(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, *a, **k):
                raise httpx.ConnectError("boom")

        monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

        with pytest.raises(llm_client.LLMCallError):
            _run(llm_client.chat_json([{"role": "user", "content": "x"}]))

    def test_raises_when_ollama_fails_and_no_fallback_key(self, monkeypatch):
        """Ollama HTTP failure with no OpenRouter key must surface LLMCallError."""
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, *a, **k):
                raise httpx.ConnectError("ollama down")

        monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

        with pytest.raises(llm_client.LLMCallError):
            _run(llm_client.chat_json([{"role": "user", "content": "x"}]))

    def test_raises_llm_error_on_unexpected_shape(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "fake-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def post(self, url, json=None, headers=None):
                return httpx.Response(
                    200,
                    json={"not_choices": []},
                    request=httpx.Request("POST", url),
                )

        monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

        with pytest.raises(llm_client.LLMCallError):
            _run(llm_client.chat_json([{"role": "user", "content": "x"}]))


class _ScriptedClient:
    """AsyncClient stand-in driven by a list of per-host post handlers.

    `handlers` maps a URL prefix (e.g. `https://ollama.com`) to a callable
    that receives `(url, json, headers)` and returns an `httpx.Response` or
    raises. Records each call to `calls` in order.
    """

    def __init__(self, handlers, calls):
        self._handlers = handlers
        self._calls = calls

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def post(self, url, json=None, headers=None):
        self._calls.append({"url": url, "json": json, "headers": headers})
        for prefix, handler in self._handlers.items():
            if url.startswith(prefix):
                result = handler(url, json, headers)
                if isinstance(result, Exception):
                    raise result
                return result
        raise AssertionError(f"Unexpected URL {url!r}")


class TestFallback:
    def test_uses_openrouter_when_only_openrouter_configured(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")
        monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

        calls = []

        def or_handler(url, json, headers):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "or-ok"}}]},
                request=httpx.Request("POST", url),
            )

        scripted = _ScriptedClient(
            {"https://openrouter.ai": or_handler}, calls
        )
        monkeypatch.setattr(llm_client.httpx, "AsyncClient", scripted)

        result = _run(llm_client.chat_json([{"role": "user", "content": "hi"}]))

        assert result == "or-ok"
        assert len(calls) == 1
        assert calls[0]["url"] == "https://openrouter.ai/api/v1/chat/completions"
        assert calls[0]["headers"]["Authorization"] == "Bearer or-fake-key"
        assert calls[0]["json"]["model"] == llm_client.DEFAULT_OPENROUTER_MODEL

    def test_falls_back_to_openrouter_when_ollama_http_fails(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "ol-fake-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)

        calls = []

        def ollama_handler(url, json, headers):
            return httpx.ConnectError("ollama down")

        def or_handler(url, json, headers):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "recovered"}}]},
                request=httpx.Request("POST", url),
            )

        scripted = _ScriptedClient(
            {
                "https://ollama.com": ollama_handler,
                "https://openrouter.ai": or_handler,
            },
            calls,
        )
        monkeypatch.setattr(llm_client.httpx, "AsyncClient", scripted)

        result = _run(llm_client.chat_json([{"role": "user", "content": "hi"}]))

        assert result == "recovered"
        assert len(calls) == 2
        assert calls[0]["url"].startswith("https://ollama.com")
        assert calls[1]["url"].startswith("https://openrouter.ai")
        assert calls[1]["headers"]["Authorization"] == "Bearer or-fake-key"

    def test_raises_llm_error_when_both_providers_fail(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "ol-fake-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")

        calls = []

        def fail(url, json, headers):
            return httpx.ConnectError(f"{url} down")

        scripted = _ScriptedClient(
            {
                "https://ollama.com": fail,
                "https://openrouter.ai": fail,
            },
            calls,
        )
        monkeypatch.setattr(llm_client.httpx, "AsyncClient", scripted)

        with pytest.raises(llm_client.LLMCallError):
            _run(llm_client.chat_json([{"role": "user", "content": "hi"}]))
        assert len(calls) == 2

    def test_does_not_fall_back_on_unexpected_shape(self, monkeypatch):
        """Shape errors are bugs, not transient failures; fallback would mask them."""
        from world_of_taxonomy import llm_client

        monkeypatch.setenv("OLLAMA_API_KEY", "ol-fake-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")

        calls = []

        def ollama_shape_bug(url, json, headers):
            return httpx.Response(
                200,
                json={"not_choices": []},
                request=httpx.Request("POST", url),
            )

        def or_handler(url, json, headers):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "should-not-reach"}}]},
                request=httpx.Request("POST", url),
            )

        scripted = _ScriptedClient(
            {
                "https://ollama.com": ollama_shape_bug,
                "https://openrouter.ai": or_handler,
            },
            calls,
        )
        monkeypatch.setattr(llm_client.httpx, "AsyncClient", scripted)

        with pytest.raises(llm_client.LLMCallError):
            _run(llm_client.chat_json([{"role": "user", "content": "hi"}]))
        assert len(calls) == 1
        assert calls[0]["url"].startswith("https://ollama.com")

    def test_openrouter_respects_model_and_base_url_overrides(self, monkeypatch):
        from world_of_taxonomy import llm_client

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-fake-key")
        monkeypatch.setenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
        monkeypatch.setenv(
            "OPENROUTER_BASE_URL", "https://custom-or.example.com/api/v1"
        )

        calls = []

        def or_handler(url, json, headers):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
                request=httpx.Request("POST", url),
            )

        scripted = _ScriptedClient(
            {"https://custom-or.example.com": or_handler}, calls
        )
        monkeypatch.setattr(llm_client.httpx, "AsyncClient", scripted)

        _run(llm_client.chat_json([{"role": "user", "content": "hi"}]))

        assert calls[0]["url"] == "https://custom-or.example.com/api/v1/chat/completions"
        assert calls[0]["json"]["model"] == "meta-llama/llama-3.3-70b-instruct"
