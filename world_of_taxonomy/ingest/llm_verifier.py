"""LLM verifier for the Track-2 generator + verifier pipeline.

The generator from ``llm_descriptions`` produces a candidate
description for a (system, code, title) triple. This module wraps a
second prompt that asks the LLM to judge the candidate's factual
accuracy and return one of ``yes`` / ``no`` / ``uncertain``.

Only candidates the verifier returns ``yes`` for are written to the
DB. ``no`` and ``uncertain`` rows are logged for human review or
re-generation at higher temperature.
"""

from __future__ import annotations

import re
from typing import List

_SYSTEM_PROMPT = (
    "You judge whether a description matches a code's title. "
    "Reply with one word: 'yes', 'no', or 'uncertain'."
)


_USER_TEMPLATE = (
    "Classification: {system_name}\n"
    "Code: {code}\n"
    "Title: {title}\n"
    "Description: {candidate}\n"
    "Verdict:"
)


def build_verifier_messages(
    *,
    system_name: str,
    code: str,
    title: str,
    candidate: str,
) -> List[dict]:
    """Return the messages list to feed to ``chat_json``."""
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _USER_TEMPLATE.format(
                system_name=(system_name or "").strip(),
                code=(code or "").strip(),
                title=(title or "").strip(),
                candidate=(candidate or "").strip(),
            ),
        },
    ]


_VERDICT_RE = re.compile(r"\b(yes|no|uncertain)\b", re.IGNORECASE)


def parse_verdict(text: str) -> str:
    """Return one of ``yes`` / ``no`` / ``uncertain``. Default to
    ``uncertain`` when the LLM emits something we cannot parse.
    """
    if not text:
        return "uncertain"
    s = str(text).strip().strip("'").strip('"').strip()
    if not s:
        return "uncertain"
    m = _VERDICT_RE.search(s.lower())
    if not m:
        return "uncertain"
    return m.group(1).lower()
