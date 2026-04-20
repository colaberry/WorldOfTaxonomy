"""LLM-based keyword expansion for classify - Ollama Cloud fallback.

Called only when the wiki-synonym-augmented OR-fallback produces zero
matches across every target system. The model is asked for 3-5 official
classification keywords that would match the user's free-text query.

Result is cached per-query (in-process) so repeat misses on the same
phrase cost one LLM call, not N.

All HTTP goes through `world_of_taxonomy.llm_client`. See that module for
env vars (OLLAMA_API_KEY, OLLAMA_MODEL, OLLAMA_BASE_URL).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from world_of_taxonomy import llm_client

_LOG = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 6.0
_MAX_KEYWORDS = 6

_SYSTEM_PROMPT = (
    "You are a classification keyword extractor. Given a short free-text "
    "description of a business, product, or occupation, output 3 to 5 single- "
    "or two-word English keywords that would appear in official industry or "
    "occupation classification system titles (NAICS, ISIC, NACE, SIC, SOC, "
    "ISCO, HS, CPC). Prefer nouns used by official classifiers (for example: "
    "'child care', 'ambulatory', 'janitorial', 'pet care', 'courier'). "
    "Return strictly JSON of the shape {\"keywords\": [\"...\", \"...\"]}. "
    "No commentary, no markdown fences."
)

# Process-local cache: query -> keywords list. Simple dict is fine for
# single-process deployments; swap to Redis once we horizontally scale.
_CACHE: dict[str, list[str]] = {}

# Fenced-JSON extraction fallback in case the model wraps output.
_FENCE_RX = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _cache_clear_for_tests() -> None:
    _CACHE.clear()


def _normalize_key(query: str) -> str:
    return " ".join(query.lower().split())


def _parse_model_output(text: str) -> list[str]:
    """Pull keywords out of a model response. Tolerates stray prose or code
    fences; returns [] on any parse failure so the caller degrades gracefully."""
    if not text:
        return []
    cleaned = text.strip()
    fence = _FENCE_RX.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    kws = data.get("keywords") if isinstance(data, dict) else None
    if not isinstance(kws, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for k in kws:
        if not isinstance(k, str):
            continue
        norm = k.strip().lower()
        if 2 <= len(norm) <= 32 and norm not in seen:
            seen.add(norm)
            out.append(norm)
        if len(out) >= _MAX_KEYWORDS:
            break
    return out


async def expand_via_llm(query: str) -> list[str]:
    """Return a list of classification keywords produced by the LLM.

    Returns [] (not None) on any failure path so the caller can blindly OR the
    result into its tsquery without null checks.
    """
    if not query:
        return []

    key = _normalize_key(query)
    if key in _CACHE:
        return _CACHE[key]

    if not llm_client.is_configured():
        _CACHE[key] = []
        return []

    try:
        content = await llm_client.chat_json(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query.strip()},
            ],
            max_tokens=120,
            temperature=0.0,
            timeout=_TIMEOUT_SECONDS,
        )
    except llm_client.LLMError as exc:
        _LOG.warning("LLM expand failed for %r: %s", query, exc)
        _CACHE[key] = []
        return []

    keywords = _parse_model_output(content)
    _CACHE[key] = keywords
    if keywords:
        _LOG.info("LLM fallback expansion for %r: %s", query, keywords)
    return keywords


def current_cache_size() -> int:
    """Observability hook - count of memoized queries."""
    return len(_CACHE)


def active_model() -> Optional[str]:
    """Active model string for the health/config endpoint."""
    return llm_client.active_model()
