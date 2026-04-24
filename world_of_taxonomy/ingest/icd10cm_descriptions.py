"""Parser for the ICD-10-CM Tabular XML file.

The CMS annual release ships two companion files:

* `icd10cm_order_<year>.txt`    -- fixed-width list of codes + titles.
  Consumed by :mod:`world_of_taxonomy.ingest.icd10cm` to build the
  node hierarchy.
* `icd10cm_tabular_<year>.xml`  -- the clinician-facing Tabular List
  with inclusion terms, excludes1/excludes2, use-additional and
  code-first instructional notes. Consumed here for the description
  backfill.

Both files are public domain CMS releases. Codes in the Tabular XML
are dotted (``A00.1``); the DB stores them without dots (``A001``).
The parser normalizes keys by stripping dots so
:func:`world_of_taxonomy.ingest.descriptions.apply_descriptions` can
match rows directly.

Chapters in the Tabular XML are numbered 1-22. The structural ingester
stores them as ``CH01``-``CH22`` to avoid collisions with the actual
code letters. The parser emits the same chapter keys.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET


_SECTION_ORDER: list[tuple[str, str]] = [
    ("includes", "**Includes:**"),
    ("inclusionTerm", "**Inclusion terms:**"),
    ("notes", "**Notes:**"),
    ("excludes1", "**Excludes1:**"),
    ("excludes2", "**Excludes2:**"),
    ("codeFirst", "**Code first:**"),
    ("codeAlso", "**Code also:**"),
    ("useAdditionalCode", "**Use additional code:**"),
    ("sevenChrNote", "**7th character note:**"),
    ("sevenChrDef", "**7th character:**"),
]


def parse_icd10cm_tabular_xml(path: Path) -> Dict[str, str]:
    """Return ``{code: markdown_description}`` for every code with notes.

    Codes with no inclusion/exclusion/instructional notes are omitted so
    the backfill does not overwrite the title with an empty description.
    """
    root = _load_root(path)
    out: Dict[str, str] = {}

    for chapter in root.findall("chapter"):
        chap_num = (chapter.findtext("name") or "").strip()
        if chap_num.isdigit():
            chap_code = f"CH{int(chap_num):02d}"
            body = _render_node(chapter)
            if body:
                out[chap_code] = body

        for diag in chapter.iter("diag"):
            name = (diag.findtext("name") or "").strip()
            if not name:
                continue
            key = name.replace(".", "")
            body = _render_node(diag)
            if body:
                out[key] = body

    return out


def _load_root(path: Path) -> ET.Element:
    """Load XML from a raw file or from a CMS release ZIP."""
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            xml_name = next(
                (n for n in z.namelist() if n.lower().endswith(".xml") and "tabular" in n.lower()),
                None,
            )
            if xml_name is None:
                raise FileNotFoundError(f"No tabular XML inside {p}")
            with z.open(xml_name) as fh:
                return ET.parse(fh).getroot()
    return ET.parse(p).getroot()


def _render_node(node: ET.Element) -> Optional[str]:
    """Render a <chapter>, <section>, or <diag> element as markdown."""
    blocks: List[str] = []
    for tag, heading in _SECTION_ORDER:
        child = node.find(tag)
        if child is None:
            continue
        items = _collect_items(child, tag)
        if not items:
            continue
        block = [heading]
        block.extend(f"- {item}" for item in items)
        blocks.append("\n".join(block))
    if not blocks:
        return None
    return "\n\n".join(blocks)


def _collect_items(child: ET.Element, tag: str) -> List[str]:
    """Extract line items for a given instructional block."""
    if tag == "sevenChrDef":
        return _collect_seven_chr_def(child)
    return [text for text in _iter_note_texts(child.findall("note")) if text]


def _collect_seven_chr_def(node: ET.Element) -> List[str]:
    items: List[str] = []
    for ext in node.findall("extension"):
        char = (ext.get("char") or "").strip()
        label = _clean_text(ext.text or "")
        if char and label:
            items.append(f"{char}: {label}")
    return items


def _iter_note_texts(notes: Iterable[ET.Element]) -> Iterable[str]:
    for n in notes:
        text = _clean_text("".join(n.itertext()))
        if text:
            yield text


def _clean_text(s: str) -> str:
    return " ".join(s.split())
