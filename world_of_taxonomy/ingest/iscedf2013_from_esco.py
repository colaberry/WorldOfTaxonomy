"""Extract ISCED-F 2013 fields-of-education descriptions from the ESCO
v1.2.1 JSON-LD file.

ESCO publishes ISCED-F groups as SKOS concepts at
``http://data.europa.eu/esco/isced-f/<notation>`` with English
``description.nodeLiteral`` bodies. Same pattern as the ISCO-08
extractor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping

import ijson

_ISCEDF_PREFIX = "http://data.europa.eu/esco/isced-f/"
_EM_DASH = "\u2014"


def is_iscedf_entry(item: Mapping) -> bool:
    uri = item.get("uri", "") or ""
    return uri.startswith(_ISCEDF_PREFIX)


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
    raw = _english_node_literal(item.get("description"))
    if not raw:
        return ""
    return raw.replace(_EM_DASH, "-")


def parse_iscedf2013_descriptions(jsonld_path: Path) -> Dict[str, str]:
    """Return ``{notation: english_description}`` for every ISCED-F
    concept in the ESCO JSON-LD with a non-empty English body.
    """
    out: Dict[str, str] = {}
    with Path(jsonld_path).open("r", encoding="utf-8") as fh:
        for item in ijson.items(fh, "@graph.item"):
            if not is_iscedf_entry(item):
                continue
            notation = (item.get("notation") or "").strip()
            if not notation:
                continue
            desc = extract_english_description(item)
            if desc:
                out[notation] = desc
    return out
