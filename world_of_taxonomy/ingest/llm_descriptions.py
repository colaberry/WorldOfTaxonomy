"""LLM-based description generator for skeleton reference taxonomies.

Many small reference systems in the DB (OWASP Top 10, APGAR Score,
Bristol Stool Form Scale, BMI Categories, Numeric Pain Rating Scale,
MITRE ATT&CK skeleton, etc.) ship with code + title only because no
upstream publishes a structured "notes" file at this level of
granularity. The titles are concise and well-known, so a careful
single-shot prompt to the project LLM client produces reliable 1-2
sentence factual descriptions.

This module is responsible only for:

1. Building the LLM messages (``build_messages``).
2. Sanitizing the response (``sanitize_response``).

The orchestration (database I/O, JSONL caching, batching) lives in
``scripts/backfill_llm_descriptions.py``.
"""

from __future__ import annotations

import re
from typing import List, Mapping

_EM_DASH = "\u2014"
_EN_DASH = "\u2013"
_NBHYPHEN = "\u2011"  # non-breaking hyphen
_FIGURE_DASH = "\u2012"
_NARROW_NBSP = "\u202f"  # narrow no-break space
_NBSP = "\u00a0"
_LSQUO = "\u2018"
_RSQUO = "\u2019"
_LDQUO = "\u201c"
_RDQUO = "\u201d"
_WS = re.compile(r"[ \t]+")
_BLANKS = re.compile(r"\n\s*\n\s*\n+")
_REFUSAL_TOKENS = {"", "N/A", "...", "n/a", "unknown", "Unknown"}
_REFUSAL_PHRASES = (
    "is not a recognized",
    "does not correspond to any known",
    "i cannot",
    "i can't",
    "i'm sorry",
    "as an ai",
    "i don't have",
)
_MIN_LEN = 15
_MAX_LEN = 1200


_SYSTEM_PROMPT = (
    "You write short factual descriptions of classification codes. "
    "Reply with one short paragraph, 1 to 3 sentences, under 80 words. "
    "Plain prose only, no quotes, no labels like 'Description:', "
    "no markdown headers, no bullet lists. Use a regular hyphen "
    "instead of an em-dash."
)


_USER_TEMPLATE = (
    "Briefly describe this entry from a public reference classification.\n"
    "Classification: {system_name}\n"
    "Entry code: {code}\n"
    "Entry title: {title}"
)


def build_messages(*, system_name: str, code: str, title: str) -> List[dict]:
    """Return the messages list to feed to ``chat_json``."""
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _USER_TEMPLATE.format(
                system_name=(system_name or "").strip(),
                code=(code or "").strip(),
                title=(title or "").strip(),
            ),
        },
    ]


def sanitize_response(text: str) -> str:
    """Return a cleaned description body, or ``""`` if the response is
    a refusal / placeholder / too short / too long.
    """
    if text is None:
        return ""
    s = str(text).strip()

    # Strip surrounding quotes (single or double).
    while s.startswith(('"', "'")) and s.endswith(('"', "'")) and len(s) >= 2:
        s = s[1:-1].strip()

    # Strip leading role labels like "Description:" or "Answer:".
    s = re.sub(
        r"^(Description|Answer|Body|Output|Result)\s*[:\-]\s*",
        "",
        s,
        flags=re.IGNORECASE,
    )

    # Normalize unicode dashes / spaces / quotes to plain ASCII.
    for ch in (_EM_DASH, _EN_DASH, _NBHYPHEN, _FIGURE_DASH):
        s = s.replace(ch, "-")
    s = s.replace(_NARROW_NBSP, " ").replace(_NBSP, " ")
    s = s.replace(_LSQUO, "'").replace(_RSQUO, "'")
    s = s.replace(_LDQUO, '"').replace(_RDQUO, '"')

    s = _BLANKS.sub("\n\n", s)
    s = _WS.sub(" ", s).strip()

    if not s:
        return ""
    if s in _REFUSAL_TOKENS:
        return ""
    if len(s) < _MIN_LEN:
        return ""
    if len(s) > _MAX_LEN:
        return ""

    # Reject answers that begin with a refusal phrase.
    low = s.lower()
    for phrase in _REFUSAL_PHRASES:
        if phrase in low[:120]:
            return ""

    return s
