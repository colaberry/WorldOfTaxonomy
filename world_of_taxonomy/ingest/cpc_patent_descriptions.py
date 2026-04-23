"""Parser for the CPC Patent full-definition XML archive.

The EPO/USPTO publishes Cooperative Patent Classification in two
parallel archives:

* ``CPCSchemeXML<version>.zip``         -- hierarchy + titles.
* ``FullCPCDefinitionXML<version>.zip`` -- definition statements,
  limiting references, and glossary per code.

The structural ingester at :mod:`world_of_taxonomy.ingest.patent_cpc`
only consumes the scheme archive. This module surfaces the richer
definition prose for the description backfill.

Codes in the definition XML are dot-free (``A22B3/00``); the DB stores
CPC codes as ``A22B 3/00`` with a space between the 4-character
subclass and the main-group number. The parser normalizes to DB form.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Optional
from xml.etree import ElementTree as ET


_SUBCLASS_RE = re.compile(r"^([A-Z]\d{2}[A-Z])(\d.*)$")


def parse_cpc_definition_xml(path: Path) -> Dict[str, str]:
    """Return ``{cpc_code: markdown_description}`` for every defined code.

    Accepts either a single cpc-definition XML file or the full ZIP
    archive containing one file per subclass.
    """
    out: Dict[str, str] = {}
    for root in _iter_roots(path):
        for item in root.findall("definition-item"):
            code = _extract_code(item)
            if not code:
                continue
            rendered = _render_item(item)
            if rendered:
                out[_normalize_code(code)] = rendered
    return out


def _extract_code(item: ET.Element) -> Optional[str]:
    sym = item.find("classification-symbol")
    if sym is None or not sym.text:
        return None
    return sym.text.strip()


def _normalize_code(code: str) -> str:
    """Insert a space between the 4-character subclass and the main group."""
    m = _SUBCLASS_RE.match(code)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return code


def _render_item(item: ET.Element) -> Optional[str]:
    blocks: list[str] = []

    defn = _render_definition_statement(item.find("definition-statement"))
    if defn:
        blocks.append(f"**Definition:**\n{defn}")

    refs = item.find("references")
    if refs is not None:
        limiting = refs.find("limiting-references")
        lines = _render_reference_table(limiting)
        if lines:
            blocks.append(
                "**Limiting references (this place does not cover):**\n"
                + "\n".join(f"- {line}" for line in lines)
            )

    glossary = _render_glossary(item.find("glossary-of-terms"))
    if glossary:
        blocks.append(
            "**Glossary:**\n" + "\n".join(f"- {line}" for line in glossary)
        )

    if not blocks:
        return None
    return "\n\n".join(blocks)


def _render_definition_statement(stmt: Optional[ET.Element]) -> Optional[str]:
    if stmt is None:
        return None
    body = stmt.find("section-body")
    if body is None:
        return None
    paragraphs: list[str] = []
    for para in body.findall("paragraph-text"):
        text = _text_content(para)
        if text:
            paragraphs.append(text)
    if not paragraphs:
        return None
    return "\n\n".join(paragraphs)


def _render_reference_table(ref: Optional[ET.Element]) -> list[str]:
    if ref is None:
        return []
    body = ref.find("section-body")
    if body is None:
        return []
    lines: list[str] = []
    for table in body.findall("table"):
        for row in table.findall("table-row"):
            cols = row.findall("table-column")
            if len(cols) < 2:
                continue
            label = _text_content(cols[0])
            target = _text_content(cols[1])
            if label and target:
                lines.append(f"{label} -> {target}")
            elif label:
                lines.append(label)
    return lines


def _render_glossary(gloss: Optional[ET.Element]) -> list[str]:
    if gloss is None:
        return []
    body = gloss.find("section-body")
    if body is None:
        return []
    lines: list[str] = []
    for table in body.findall("table"):
        for row in table.findall("table-row"):
            cols = row.findall("table-column")
            if len(cols) < 2:
                continue
            term = _text_content(cols[0])
            meaning = _text_content(cols[1])
            if term and meaning:
                lines.append(f"{term}: {meaning}")
    return lines


def _text_content(node: ET.Element) -> str:
    """Flatten element text, skipping <media> tags and normalizing whitespace."""
    parts: list[str] = []
    for elem in node.iter():
        if elem.tag == "media":
            continue
        if elem.text:
            parts.append(elem.text)
        if elem.tail and elem is not node:
            parts.append(elem.tail)
    text = " ".join(parts)
    return " ".join(text.split())


def _iter_roots(path: Path) -> Iterable[ET.Element]:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            members = [
                n
                for n in z.namelist()
                if n.lower().endswith(".xml") and "cpc-definition" in n.lower()
            ]
            for name in members:
                with z.open(name) as fh:
                    try:
                        yield ET.parse(fh).getroot()
                    except ET.ParseError:
                        continue
        return
    yield ET.parse(p).getroot()
