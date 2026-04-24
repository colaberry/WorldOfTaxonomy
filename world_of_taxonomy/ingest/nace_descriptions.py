"""Parser for NACE Rev 2 explanatory notes.

Each NACE Rev 2 concept is served as per-concept SKOS/XKOS RDF by the
EU Publications Office at ``http://data.europa.eu/ux2/nace2/<path>``.
The URI path is the dots-stripped code (``01.11`` -> ``0111``). Two
English annotations are the source of the description:

- ``xkos:coreContentNote`` -- "This class includes ..." narrative.
- ``xkos:exclusionNote``   -- "This class excludes ..." pointers.

Both blocks are already markdown-friendly (bullets, sub-bullets) so we
pass them through with minimal rewriting: strip em-dashes, normalize
line endings, and concatenate with a blank line between sections.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, Mapping

_BASE_URL = "http://data.europa.eu/ux2/nace2/"
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
_RDF_ABOUT = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"
_NS: Mapping[str, str] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xkos": "http://rdf-vocabulary.ddialliance.org/xkos#",
}

_EM_DASH = "\u2014"


def code_to_uri_path(code: str) -> str:
    """Return the EU-Publications-Office URI suffix for a NACE code.

    Section letters (``A``, ``B``) and 2-digit division codes pass through
    unchanged. Group and class codes with a dot (``01.11``) collapse to
    the dots-stripped form (``0111``).
    """
    return code.replace(".", "")


def build_concept_url(code: str) -> str:
    """Return the full RDF URL for a given NACE Rev 2 code."""
    return _BASE_URL + code_to_uri_path(code)


def parse_concept_rdf(xml_bytes: bytes, *, uri_suffix: str) -> Dict[str, str]:
    """Extract the English core-content + exclusion notes from a concept RDF.

    ``uri_suffix`` is the expected URI fragment (e.g. ``"0111"``) used to
    pick the right ``rdf:Description`` if the payload carries more than
    one. Returns ``{"core_content": "", "exclusion": ""}`` when the
    expected node or its English annotations are absent.
    """
    root = ET.fromstring(xml_bytes)
    target_tail = "/" + uri_suffix
    core = ""
    exclusion = ""
    for desc in root.findall("rdf:Description", _NS):
        about = desc.get(_RDF_ABOUT, "")
        if not about.endswith(target_tail):
            continue
        for el in desc.findall("xkos:coreContentNote", _NS):
            if el.get(_XML_LANG) == "en":
                core = (el.text or "").strip()
                break
        for el in desc.findall("xkos:exclusionNote", _NS):
            if el.get(_XML_LANG) == "en":
                exclusion = (el.text or "").strip()
                break
        break
    return {"core_content": core, "exclusion": exclusion}


def render_description(parts: Mapping[str, str]) -> str:
    """Concatenate core-content + exclusion notes into a single markdown body."""
    blocks: list[str] = []
    core = (parts.get("core_content") or "").strip()
    exclusion = (parts.get("exclusion") or "").strip()
    if core:
        blocks.append(core)
    if exclusion:
        blocks.append(exclusion)
    if not blocks:
        return ""
    body = "\n\n".join(blocks)
    return body.replace(_EM_DASH, "-")
