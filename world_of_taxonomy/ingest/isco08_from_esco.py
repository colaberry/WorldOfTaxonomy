"""Extract ISCO-08 group descriptions from the ESCO v1.2.1 JSON-LD file.

ESCO publishes ISCO groups as SKOS concepts with URIs of the form
``http://data.europa.eu/esco/isco/C<notation>`` (notation is the ISCO
code, e.g. ``1111`` for Legislators). Each concept has a
``description`` that may be a single ``NodeLiteral`` object or a list
of them keyed by language; we pick the English one.

The structural ingester already persists titles, so this module only
returns the description text keyed by notation so it can be applied
via ``apply_descriptions``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Mapping

import ijson

_ISCO_PREFIX = "http://data.europa.eu/esco/isco/"
_EM_DASH = "\u2014"


def is_isco_entry(item: Mapping) -> bool:
    uri = item.get("uri", "") or ""
    return uri.startswith(_ISCO_PREFIX)


def _english_node_literal(desc) -> str:
    if isinstance(desc, list):
        for d in desc:
            if isinstance(d, dict) and d.get("language") == "en":
                return (d.get("nodeLiteral") or "").strip()
        return ""
    if isinstance(desc, dict):
        if desc.get("language") == "en":
            return (desc.get("nodeLiteral") or "").strip()
    return ""


def extract_english_description(item: Mapping) -> str:
    """Return the English description text, or ``""`` when absent."""
    raw = _english_node_literal(item.get("description"))
    if not raw:
        return ""
    return raw.replace(_EM_DASH, "-")


def parse_isco08_descriptions(jsonld_path: Path) -> Dict[str, str]:
    """Stream the ESCO JSON-LD and return ``{notation: description}``
    for every ISCO concept with a non-empty English description.
    """
    out: Dict[str, str] = {}
    with Path(jsonld_path).open("r", encoding="utf-8") as fh:
        for item in ijson.items(fh, "@graph.item"):
            if not is_isco_entry(item):
                continue
            notation = (item.get("notation") or "").strip()
            if not notation:
                continue
            desc = extract_english_description(item)
            if desc:
                out[notation] = desc
    return out
