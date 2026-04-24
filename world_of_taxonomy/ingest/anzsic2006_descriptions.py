"""Parser for ANZSIC 2006 descriptions from the ABS SDMX codelist.

The ABS API at
``https://api.data.abs.gov.au/codelist/ABS/CL_ANZSIC_2006/1.0.0``
serves an SDMX v2.1 XML codelist. Each ``<structure:Code>`` element
carries a ``CONTEXT`` annotation whose body is a two-section text:

- ``Exclusions/References`` -- pointers to other classes
- ``Primary Activities``   -- illustrative activity list

The raw body is heavily tab-indented. This module collapses whitespace
and re-renders the body as clean markdown with the two section
headings bolded and each activity line converted to a bullet.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Mapping

_NS: Mapping[str, str] = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

_EM_DASH = "\u2014"
_SECTIONS = ("Exclusions/References", "Primary Activities")
_WS_RUN = re.compile(r"[ \t]+")


def _clean_line(s: str) -> str:
    return _WS_RUN.sub(" ", s).strip()


def render_context(body: str) -> str:
    """Return a cleaned markdown rendering of one CONTEXT annotation.

    Empty input returns ``""``. Section headings are surfaced as
    ``**Exclusions/References:**`` / ``**Primary Activities:**``, and
    lines within each section become markdown bullets.
    """
    if not (body or "").strip():
        return ""

    # Split into lines, strip each line, drop empties
    raw_lines = [_clean_line(ln) for ln in body.splitlines()]
    lines = [ln for ln in raw_lines if ln]

    blocks: list[tuple[str, list[str]]] = []  # [(heading, items)]
    current_heading: str | None = None
    current_items: list[str] = []
    for line in lines:
        if line in _SECTIONS:
            if current_heading is not None:
                blocks.append((current_heading, current_items))
            current_heading = line
            current_items = []
            continue
        if current_heading is None:
            # Text before any heading; treat as a lead paragraph under
            # a synthetic heading.
            current_heading = ""
            current_items = []
        current_items.append(line)
    if current_heading is not None:
        blocks.append((current_heading, current_items))

    out_parts: list[str] = []
    for heading, items in blocks:
        if not items:
            continue
        if heading:
            out_parts.append(f"**{heading}:**")
        # Bullet each item
        for item in items:
            out_parts.append(f"- {item}")
    body_out = "\n".join(out_parts)
    return body_out.replace(_EM_DASH, "-").strip()


def parse_anzsic2006_descriptions(xml_path: Path) -> Dict[str, str]:
    """Return ``{code: markdown_description}`` for every ANZSIC 2006 code
    that has a non-empty CONTEXT annotation.
    """
    root = ET.parse(str(xml_path)).getroot()
    out: Dict[str, str] = {}
    for code_el in root.findall(".//structure:Code", _NS):
        code_id = code_el.get("id", "")
        if not code_id or code_id == "TOT":
            continue
        for ann in code_el.findall("common:Annotations/common:Annotation", _NS):
            t = ann.find("common:AnnotationType", _NS)
            body = ann.find("common:AnnotationText", _NS)
            if t is None or body is None:
                continue
            if (t.text or "").strip() != "CONTEXT":
                continue
            rendered = render_context(body.text or "")
            if rendered:
                out[code_id] = rendered
            break
    return out
