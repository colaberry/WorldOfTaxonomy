"""Parser for ANZSCO 2022 SDMX per-code annotations.

The structural ingester (``ingest.anzsco_2022``) persists only code and
title. The ABS SDMX file also carries a short ``common:Description``
plus ``INDICATIVE_SKILL_LEVEL`` and ``TASKS_INCLUDE`` annotation blocks
on every non-aggregate code -- the actual occupation-profile content
Australian and New Zealand statistical users look up. This module turns
each code into a single markdown body and keys it by the SDMX code id.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Mapping

_NS: Mapping[str, str] = {
    "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

_EM_DASH = "\u2014"
_BULLET_PREFIX = re.compile(r"^-\s{2,}", re.MULTILINE)


def _text_of(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def _annotation_text(code_el, ann_type: str, ns: Mapping[str, str]) -> str:
    for ann in code_el.findall("common:Annotations/common:Annotation", ns):
        type_el = ann.find("common:AnnotationType", ns)
        if _text_of(type_el) != ann_type:
            continue
        text_el = ann.find("common:AnnotationText", ns)
        return _text_of(text_el)
    return ""


def _normalize_bullets(text: str) -> str:
    return _BULLET_PREFIX.sub("- ", text)


def render_code_xml(code_el, ns: Mapping[str, str]) -> str:
    """Return a markdown description for one SDMX ``structure:Code`` element.

    Composes up to three sections in order:

    1. The short ``common:Description`` (plain paragraph).
    2. ``**Indicative skill level:**`` + the ``INDICATIVE_SKILL_LEVEL``
       annotation body.
    3. ``**Tasks include:**`` + the ``TASKS_INCLUDE`` annotation body.

    Returns ``""`` when none of the three sections carries content so
    callers can skip the row entirely rather than overwrite NULL with
    an empty string.
    """
    desc = _text_of(code_el.find("common:Description", ns))
    skill = _annotation_text(code_el, "INDICATIVE_SKILL_LEVEL", ns)
    tasks = _annotation_text(code_el, "TASKS_INCLUDE", ns)

    parts: list[str] = []
    if desc:
        parts.append(desc)
    if skill:
        parts.append(f"**Indicative skill level:**\n\n{skill}")
    if tasks:
        parts.append(f"**Tasks include:**\n\n{tasks}")

    if not parts:
        return ""

    body = "\n\n".join(parts)
    body = _normalize_bullets(body)
    return body.replace(_EM_DASH, "-")


def parse_anzsco_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{code: markdown_description}`` for every non-empty code.

    Excludes the ``TOT`` aggregate and any code where every source field
    is empty. Codes with only ORDER / LINK annotations (no Description,
    no skill level, no tasks) are skipped.
    """
    root = ET.parse(str(path)).getroot()
    out: Dict[str, str] = {}
    for code_el in root.findall(".//structure:Code", _NS):
        code_id = code_el.get("id", "")
        if not code_id or code_id == "TOT":
            continue
        rendered = render_code_xml(code_el, _NS)
        if rendered:
            out[code_id] = rendered
    return out
