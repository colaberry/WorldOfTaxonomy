"""Parser for the ICD-10-PCS Tables XML, used for description backfill.

CMS publishes three companion files annually:

* `icd10pcs_order_<year>.txt`  -- consumed by
  :mod:`world_of_taxonomy.ingest.icd10_pcs` to build the structural
  hierarchy (section -> body system -> root op table -> leaf code).
* `icd10pcs_tables_<year>.xml` -- the per-table breakdown with axis
  definitions consumed here.
* `icd10pcs_definitions_<year>.xml` -- term-to-definition lookup
  (operations, body parts, approaches). Not parsed here; the tables
  XML embeds operation definitions inline.

For each ``<pcsTable>`` element, axes 1-3 (Section, Body System,
Operation) are constants for the entire table; the operation axis
carries a ``<definition>``. We map that definition onto the 3-char
prefix it covers, plus every 7-char leaf under that prefix - every
leaf shares the same root operation, so the operation definition is
the natural per-code description.

Returns ``{code: definition}`` covering both 3-char and 7-char codes.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET


def parse_icd10pcs_tables_xml(
    xml_path: Path,
    *,
    leaf_codes: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return ``{code: definition}`` for every 3-char and 7-char code.

    Parameters
    ----------
    xml_path
        Path to ``icd10pcs_tables_<year>.xml`` or a CMS release ZIP
        containing it.
    leaf_codes
        Optional list of 7-char leaf codes already known to the DB.
        Each leaf inherits its 3-char prefix's operation definition.
        If omitted, only 3-char prefixes are returned.
    """
    root = _load_root(xml_path)
    out: Dict[str, str] = {}

    for table in root.findall("pcsTable"):
        prefix = _table_prefix(table)
        if not prefix:
            continue
        op_definition = _operation_definition(table)
        if not op_definition:
            continue
        out[prefix] = op_definition

    if leaf_codes:
        for code in leaf_codes:
            if len(code) == 7 and code[:3] in out:
                out[code] = out[code[:3]]

    return out


def _load_root(path: Path) -> ET.Element:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            xml_name = next(
                (
                    n for n in z.namelist()
                    if n.lower().endswith(".xml") and "tables" in n.lower()
                ),
                None,
            )
            if xml_name is None:
                raise FileNotFoundError(f"No tables XML inside {p}")
            with z.open(xml_name) as fh:
                return ET.parse(fh).getroot()
    return ET.parse(p).getroot()


def _table_prefix(table: ET.Element) -> Optional[str]:
    """Return the 3-char prefix (section + body system + operation)."""
    parts: List[str] = []
    for pos in ("1", "2", "3"):
        axis = _table_axis(table, pos)
        if axis is None:
            return None
        label = axis.find("label")
        if label is None or not label.get("code"):
            return None
        parts.append(label.get("code"))
    return "".join(parts) if len(parts) == 3 else None


def _operation_definition(table: ET.Element) -> Optional[str]:
    """Pull the operation axis's <definition> text."""
    axis = _table_axis(table, "3")
    if axis is None:
        return None
    definition = axis.find("definition")
    if definition is None or not (definition.text or "").strip():
        return None
    return _clean_text(definition.text)


def _table_axis(table: ET.Element, pos: str) -> Optional[ET.Element]:
    """Return the table-level axis (not pcsRow) at the given position."""
    for axis in table.findall("axis"):
        if axis.get("pos") == pos:
            return axis
    return None


def _clean_text(s: str) -> str:
    return " ".join(s.split())
