"""Cascade SOC 2018 detailed-occupation descriptions up to broad occupations.

The U.S. BLS Standard Occupational Classification 2018 has four hierarchy
levels:

- Major group (``11-0000``)
- Minor group (``11-1000``)
- Broad occupation (``11-1010``) -- 6 digits ending in ``0``
- Detailed occupation (``11-1011``) -- 6 digits ending in a non-zero digit

Detailed occupations already carry the authoritative description. For a
broad occupation with exactly one detailed child, the semantic content
is identical (e.g. ``11-1010 Chief Executives`` -> ``11-1011 Chief
Executives``) so we safely cascade the child's description up. Broads
with multiple detailed children are skipped because concatenating
heterogeneous content would be misleading.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Mapping


def soc_broad_prefix(broad_code: str) -> str:
    """Return the 5-char prefix that all detailed children of a broad
    occupation share (e.g. ``11-1010`` -> ``11-101``)."""
    return broad_code[:-1]


def build_broad_mapping(
    broad_codes: Iterable[str],
    detailed_descriptions: Mapping[str, str],
) -> Dict[str, str]:
    """Return ``{broad_code: description}`` for every broad that has
    exactly one detailed child with a populated description.
    """
    # Group detailed codes by their broad prefix
    by_prefix: Dict[str, list[str]] = defaultdict(list)
    for code, desc in detailed_descriptions.items():
        if not desc:
            continue
        by_prefix[code[:-1]].append(code)

    out: Dict[str, str] = {}
    for broad in broad_codes:
        prefix = soc_broad_prefix(broad)
        children = by_prefix.get(prefix, [])
        if len(children) == 1:
            out[broad] = detailed_descriptions[children[0]]
    return out
