"""Parser for ANZSIC 2006 descriptions from the ABS SDMX codelist XML.

The structural ingester at :mod:`world_of_taxonomy.ingest.anzsic`
loads codes + titles from the ABS XLS support file. The companion
SDMX 2.1 codelist XML
(``https://api.data.abs.gov.au/codelist/ABS/CL_ANZSIC_2006/1.0.0``)
also carries multi-paragraph ``<common:Description>`` elements for
each Division and many lower-level codes. This parser surfaces those
into ``classification_node.description``.

Returns ``{code: description}`` for every code with a non-empty
description in the XML; the ``TOT`` total-aggregator code is dropped
so it cannot accidentally overwrite anything.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
from xml.etree import ElementTree as ET


_NS = {
    "structure": (
        "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
    ),
    "common": (
        "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
    ),
}


def parse_anzsic_2006_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{code: description}`` from the ANZSIC SDMX XML."""
    root = ET.parse(path).getroot()
    out: Dict[str, str] = {}
    for code_el in root.findall(".//structure:Code", _NS):
        cid = (code_el.get("id") or "").strip()
        if not cid or cid == "TOT":
            continue
        desc_el = code_el.find("common:Description", _NS)
        if desc_el is None:
            continue
        text = (desc_el.text or "").strip()
        if not text:
            continue
        cleaned = _normalize(text)
        if cleaned:
            out[cid] = cleaned
    return out


def _normalize(s: str) -> str:
    """Collapse runaway whitespace and strip surrounding blank lines."""
    paragraphs = []
    for paragraph in s.split("\n"):
        joined = " ".join(paragraph.split())
        if joined:
            paragraphs.append(joined)
    return "\n\n".join(paragraphs)
