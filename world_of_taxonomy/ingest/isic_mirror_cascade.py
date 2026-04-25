"""Cascade ISIC Rev 4 child descriptions up to empty parent aggregates
across the entire ISIC family (isic_rev4 + 123 mirrors).

After the NACE-driven crosswalk cascade (#54) populated the codes that
NACE and ISIC align 1:1, every ISIC mirror has 279 empty rows: the
2 sections, 6 divisions, 163 groups and 108 classes that were either
NACE-split 1:N (skipped by safety) or had no English note in the EU
RDF for the matching NACE code.

For empty parents whose direct children include exactly one populated
entry, cascading the child's description up is safe. Iteration walks
from longest code length down, so a 2-digit division can pick up its
description after its 3-digit group child has been populated by a
4-digit class.

System detection reuses the same heuristic as the ISIC-from-NACE
cascade: a system is treated as ISIC-derived if it shares >=95% of
its code set with ``isic_rev4``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping


def build_parent_mapping(
    parent_codes: Iterable[str],
    populated_descriptions: Mapping[str, str],
) -> Dict[str, str]:
    """Return ``{parent_code: description}`` for parents whose direct
    children include exactly one populated entry."""
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


async def isic_family_systems(conn) -> List[str]:
    """Return systems whose code set overlaps >=95% with ``isic_rev4``.

    Includes ``isic_rev4`` itself plus the 123 country / regional
    mirrors (``isic_*``, ``ciiu_*``, ``kbli_id``, ``bsic``, ``caeb``,
    ``nic_2008``, ``psic_pk``, ``slsic``, ``vsic_2018``).
    """
    isic_codes = await conn.fetch(
        "SELECT code FROM classification_node WHERE system_id = 'isic_rev4'"
    )
    isic_set = {r["code"] for r in isic_codes}
    rows = await conn.fetch(
        "SELECT DISTINCT system_id FROM classification_node "
        "WHERE code = '0111' AND system_id <> 'isic_rev4' ORDER BY system_id"
    )
    selected: List[str] = ["isic_rev4"]
    for r in rows:
        sid = r["system_id"]
        codes = await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = $1", sid,
        )
        system_codes = {x["code"] for x in codes}
        if len(system_codes) > 0 and len(isic_set & system_codes) / len(isic_set) >= 0.95:
            selected.append(sid)
    return sorted(selected)
