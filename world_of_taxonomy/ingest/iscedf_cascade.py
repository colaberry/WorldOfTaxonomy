"""Cascade ISCED-F 2013 child descriptions to empty parent aggregates.

The ESCO-sourced backfill (#64) populated only the codes for which
ESCO carries an English ``description.nodeLiteral`` -- mostly the
4-digit narrowest level. A number of higher-level codes (2-digit
broad fields, 3-digit narrow fields) remained empty.

For parent codes whose set of direct children contains exactly one
populated child, the parent description is semantically equivalent
and can be cascaded up. Multi-child parents are left empty rather
than concatenating heterogeneous content.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Mapping


def iscedf_child_prefix(code: str) -> str:
    """The parent code is itself the prefix that all direct children
    share. Children extend the code by exactly one character."""
    return code


def build_parent_mapping(
    parent_codes: Iterable[str],
    populated_descriptions: Mapping[str, str],
) -> Dict[str, str]:
    """Return ``{parent_code: description}`` for parents whose direct
    children include exactly one populated entry.

    A direct child is a code that extends the parent by one character.
    Codes that extend by 2+ characters (grandchildren) do not count.
    """
    by_parent: Dict[str, list[str]] = defaultdict(list)
    for code, desc in populated_descriptions.items():
        if not desc:
            continue
        if len(code) <= 1:
            continue
        parent = code[:-1]
        by_parent[parent].append(code)

    out: Dict[str, str] = {}
    for parent in parent_codes:
        kids = by_parent.get(iscedf_child_prefix(parent), [])
        if len(kids) == 1:
            out[parent] = populated_descriptions[kids[0]]
    return out
