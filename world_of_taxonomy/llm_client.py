"""Shared LLM client with Ollama Cloud primary + OpenRouter fallback.

All LLM calls in the project go through `chat_json()`. Both providers speak
OpenAI-compatible chat completions, so the payload shape is identical; only
the base URL, API key, and default model differ.

Preference order:
1. Ollama Cloud (if `OLLAMA_API_KEY` is set).
2. OpenRouter (if `OPENROUTER_API_KEY` is set). Used as fallback when Ollama
   is not configured OR when an Ollama call raises a transient HTTP error.

A response-shape error from the primary provider is NOT masked by a fallback
retry. That is a bug in the provider's payload, not a transient failure, and
retrying would hide the real problem.

Env:
- OLLAMA_API_KEY    : primary provider key.
- OLLAMA_MODEL      : optional, default `gpt-oss:120b`.
- OLLAMA_BASE_URL   : optional, default `https://ollama.com/v1`.
- OPENROUTER_API_KEY: fallback provider key.
- OPENROUTER_MODEL  : optional, default `openai/gpt-oss-120b`.
- OPENROUTER_BASE_URL: optional, default `https://openrouter.ai/api/v1`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional

import httpx

DEFAULT_MODEL = "gpt-oss:120b"
DEFAULT_BASE_URL = "https://ollama.com/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-oss-120b"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT_SECONDS = 30.0


class LLMError(Exception):
    """Base class for LLM client errors."""


class LLMNotConfiguredError(LLMError):
    """Raised when no LLM provider key is set (neither Ollama nor OpenRouter)."""


class LLMCallError(LLMError):
    """Raised when the upstream call fails or returns an unexpected shape."""


@dataclass(frozen=True)
class _Provider:
    name: str
    api_key: str
    base_url: str
    model: str


def _ollama_provider() -> Optional[_Provider]:
    api_key = os.environ.get("OLLAMA_API_KEY")
    if not api_key:
        return None
    return _Provider(
        name="ollama",
        api_key=api_key,
        base_url=os.environ.get("OLLAMA_BASE_URL") or DEFAULT_BASE_URL,
        model=os.environ.get("OLLAMA_MODEL") or DEFAULT_MODEL,
    )


def _openrouter_provider() -> Optional[_Provider]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return _Provider(
        name="openrouter",
        api_key=api_key,
        base_url=os.environ.get("OPENROUTER_BASE_URL")
        or DEFAULT_OPENROUTER_BASE_URL,
        model=os.environ.get("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL,
    )


def _providers_in_order() -> List[_Provider]:
    chain: List[_Provider] = []
    ollama = _ollama_provider()
    if ollama is not None:
        chain.append(ollama)
    openrouter = _openrouter_provider()
    if openrouter is not None:
        chain.append(openrouter)
    return chain


def is_configured() -> bool:
    return bool(_providers_in_order())


def active_model() -> Optional[str]:
    chain = _providers_in_order()
    if not chain:
        return None
    return chain[0].model


async def _call_provider(
    provider: _Provider,
    messages: list,
    *,
    model: Optional[str],
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> str:
    payload = {
        "model": model or provider.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{provider.base_url}/chat/completions"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        body = resp.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMCallError(
            f"LLM response from {provider.name} had unexpected shape: {body!r}"
        ) from exc


async def chat_json(
    messages: Iterable[Mapping[str, str]],
    *,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    timeout: Optional[float] = None,
) -> str:
    """POST the chat completion request and return the raw assistant content.

    Tries providers in order (Ollama then OpenRouter). Transient HTTP failures
    on the primary are retried via the fallback. Response-shape errors are
    surfaced immediately without fallback.
    """
    chain = _providers_in_order()
    if not chain:
        raise LLMNotConfiguredError(
            "No LLM provider configured. Set OLLAMA_API_KEY or OPENROUTER_API_KEY."
        )

    messages_list = list(messages)
    effective_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS

    last_http_error: Optional[Exception] = None
    for provider in chain:
        try:
            return await _call_provider(
                provider,
                messages_list,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=effective_timeout,
            )
        except (httpx.HTTPError, ValueError) as exc:
            last_http_error = exc
            continue

    raise LLMCallError(
        f"All LLM providers failed. Last error: {last_http_error}"
    ) from last_http_error
