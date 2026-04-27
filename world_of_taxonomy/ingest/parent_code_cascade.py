"""Generic single-child cascade keyed by ``parent_code`` column.

Some systems (ICD-11, ATC WHO) use codes whose hierarchical parent
relationship is not encoded in the code string itself; instead the
``parent_code`` column on ``classification_node`` records each row's
parent. This module provides a child->parent cascade that consults
``parent_code`` directly.

For empty parents whose set of direct children with non-empty
descriptions has size exactly 1, cascade the child's description up.
Multi-child parents are skipped to avoid synthesis.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Tuple


def build_parent_mapping(
    parent_codes: Iterable[str],
    populated_children: Iterable[Tuple[str, str, str]],
) -> Dict[str, str]:
    """Return ``{parent_code: description}``.

    ``populated_children`` is an iterable of ``(child_code,
    parent_code, description)`` triples sourced from the DB.
    """
    by_parent: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for child_code, parent_code, desc in populated_children:
        if not desc:
            continue
        if not parent_code:
            continue
        by_parent[parent_code].append((child_code, desc))

    out: Dict[str, str] = {}
    for parent in parent_codes:
        kids = by_parent.get(parent, [])
        if len(kids) == 1:
            _, desc = kids[0]
            out[parent] = desc
    return out
