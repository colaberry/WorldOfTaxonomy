"""Cascade NAICS 2022 child descriptions up to empty industry groups.

Industry groups (4 digits) are defined by their constituent industries
(5 digits) which in turn are defined by national industries (6 digits).
For groups with a single 5-digit child, the group's description is
semantically the same as the child's.

The Census Bureau often ships the 5-digit description as a pointer
of the form ``"See industry description for <6-digit>."``. This module
resolves that chain and returns the underlying 6-digit text.
"""

from __future__ import annotations

import re
from typing import Dict, Mapping, Optional

_POINTER_RE = re.compile(
    r"^\s*See industry description for\s+(\S+?)\.?\s*$",
    re.IGNORECASE,
)


def is_see_pointer(text: str) -> bool:
    """Return True when ``text`` is a Census 'See industry description
    for <code>.' redirect rather than a real description."""
    return bool(_POINTER_RE.match(text or ""))


def resolve_pointer_target(text: str) -> Optional[str]:
    """Return the target code embedded in a 'See industry description
    for <code>.' pointer, or ``None`` if the text is not a pointer."""
    m = _POINTER_RE.match(text or "")
    if not m:
        return None
    return m.group(1)


def resolve_description(
    code: str,
    code_to_description: Mapping[str, str],
    *,
    max_hops: int = 4,
) -> str:
    """Walk 'See industry description for X' pointers until a real
    description is found or the chain breaks. Returns ``""`` when the
    chain terminates in a missing code or loops.
    """
    visited: set[str] = set()
    current = code
    for _ in range(max_hops):
        if current in visited:
            return ""
        visited.add(current)
        text = code_to_description.get(current, "")
        if not text:
            return ""
        target = resolve_pointer_target(text)
        if target is None:
            return text
        current = target
    return ""
