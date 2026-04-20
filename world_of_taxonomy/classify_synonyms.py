"""Classify synonym layer - Karpathy Wiki Pattern.

Single source of truth lives in wiki/classify-synonyms.md as a fenced JSON
block. This module parses that block at import time and exposes a small
expand_query() API the classify engine uses before running its OR fallback.

Why parse markdown instead of loading a plain JSON file: one curated file
feeds three surfaces (wiki page at /guide/classify-synonyms, llms-full.txt,
and this engine). No duplicate sources to drift apart.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_WIKI_FILE = Path(__file__).resolve().parent.parent / "wiki" / "classify-synonyms.md"
_FENCE_RX = re.compile(r"```json\s*(.*?)```", re.DOTALL)


def _load_synonyms() -> dict[str, list[str]]:
    if not _WIKI_FILE.exists():
        return {}
    text = _WIKI_FILE.read_text(encoding="utf-8")
    match = _FENCE_RX.search(text)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return {k.lower().strip(): [v.lower().strip() for v in vs] for k, vs in data.items()}


# Cached at import time. Cheap to refresh by restarting the process.
_SYNONYMS: dict[str, list[str]] = _load_synonyms()


def expand_query(text: str) -> list[str]:
    """Return extra keywords to OR into the full-text query.

    Matching is whole-query substring (case-insensitive) so that multi-word
    keys like "urgent care" or "dark kitchen" work without token-level
    reconstruction. Returns the flat list of expansion keywords; duplicates
    are removed, original query tokens are not included.
    """
    if not text or not _SYNONYMS:
        return []
    lower = text.lower()
    expansions: list[str] = []
    seen: set[str] = set()
    for key, values in _SYNONYMS.items():
        if re.search(r"\b" + re.escape(key) + r"\b", lower):
            for v in values:
                if v not in seen:
                    seen.add(v)
                    expansions.append(v)
    return expansions


def synonym_count() -> int:
    """Count of curated synonym entries - used by observability / health check."""
    return len(_SYNONYMS)
