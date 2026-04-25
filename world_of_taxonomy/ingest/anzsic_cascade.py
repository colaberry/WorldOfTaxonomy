"""Cascade ANZSIC 2006 child descriptions to empty parent aggregates.

The ABS SDMX backfill (#59) populated only the codes for which the
CONTEXT annotation carried "Exclusions/References" or "Primary
Activities" content - mostly the 4-digit class level. Many higher-level
codes (3-digit groups, 2-digit subdivisions) remained empty.

For empty parents whose direct children include exactly one populated
entry, cascading the child's description up is safe. Multi-child
parents are left empty rather than concatenating heterogeneous content.

Direct children are identified by code length: a child code is one
character longer than its parent and starts with the parent code.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Mapping


def is_direct_child(*, child: str, parent: str) -> bool:
    """True when ``child`` extends ``parent`` by exactly one character."""
    if not child or not parent:
        return False
    if len(child) != len(parent) + 1:
        return False
    return child.startswith(parent)


def build_parent_mapping(
    parent_codes: Iterable[str],
    populated_descriptions: Mapping[str, str],
) -> Dict[str, str]:
    """Return ``{parent_code: description}`` for parents whose direct
    children include exactly one populated entry.
    """
    by_parent: Dict[str, list[str]] = defaultdict(list)
    for code, desc in populated_descriptions.items():
        if not desc:
            continue
        if len(code) <= 1:
            continue
        by_parent[code[:-1]].append(code)

    out: Dict[str, str] = {}
    for parent in parent_codes:
        kids = by_parent.get(parent, [])
        if len(kids) == 1:
            out[parent] = populated_descriptions[kids[0]]
    return out
