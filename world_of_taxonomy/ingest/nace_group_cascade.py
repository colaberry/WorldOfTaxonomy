"""Cascade NACE Rev 2 class (XX.XX) descriptions up to group (XX.X).

Some NACE groups have no explanatory note in the EU Publications
Office RDF because they are defined entirely by their constituent
classes. When a group has exactly one class child with a populated
description, cascading the child's text up to the parent is safe.
For groups with multiple classes, the parent is left empty rather
than synthesizing concatenated content.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Mapping


def is_class_child_of(*, child: str, group: str) -> bool:
    """True when ``child`` is a 4-digit class code (``XX.XX``) whose
    first three digits equal ``group`` (a ``XX.X`` code)."""
    if not group or "." not in group:
        return False
    if not child or "." not in child:
        return False
    # class is XX.XX (5 chars including dot); group is XX.X (4 chars)
    if len(child) != 5 or len(group) != 4:
        return False
    return child.startswith(group)


def build_group_mapping(
    groups: Iterable[str],
    class_descriptions: Mapping[str, str],
) -> Dict[str, str]:
    """Return ``{group_code: description}`` for each group with exactly
    one populated class child.
    """
    # Bucket classes by their parent group (first 4 characters).
    by_parent: Dict[str, list[str]] = defaultdict(list)
    for code, desc in class_descriptions.items():
        if not desc:
            continue
        if len(code) != 5 or "." not in code:
            continue
        by_parent[code[:4]].append(code)

    out: Dict[str, str] = {}
    for g in groups:
        kids = by_parent.get(g, [])
        if len(kids) == 1:
            out[g] = class_descriptions[kids[0]]
    return out
