"""ANZSCO 2022 ingester.

Australian and New Zealand Standard Classification of Occupations, 2022 edition.
Source: Australian Bureau of Statistics SDMX API
  https://api.data.abs.gov.au/codelist/ABS/CL_ANZSCO_2022/1.0.0
  (SDMX v2.1 XML, publicly accessible, no registration required)

License: CC BY 4.0 (ABS Open Data)
  Attribution: Australian Bureau of Statistics

Hierarchy (5 levels):
  Level 1: Major Group        (1-digit,  e.g. '1' Managers)
  Level 2: Sub-Major Group    (2-digit,  e.g. '11')
  Level 3: Minor Group        (3-digit,  e.g. '111')
  Level 4: Unit Group         (4-digit,  e.g. '1111')
  Level 5: Occupation         (6-digit,  e.g. '111111')

Note: ANZSCO skips 5-digit codes - jumps from 4-digit to 6-digit.
The 'TOT' (All occupations) aggregate code is excluded.

~1,590 codes (1,591 total minus TOT aggregate).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

_URL = "https://api.data.abs.gov.au/codelist/ABS/CL_ANZSCO_2022/1.0.0"
_DEFAULT_PATH = "data/anzsco_2022.xml"
_HEADERS = {"Accept": "application/vnd.sdmx.structure+xml"}

_NS = {
    "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

CHUNK = 500

_SYSTEM_ROW = (
    "anzsco_2022",
    "ANZSCO 2022",
    "Australian and New Zealand Standard Classification of Occupations, 2022",
    "2022",
    "Australia / New Zealand",
    "Australian Bureau of Statistics",
)


def _determine_level(code: str) -> int:
    """Return hierarchy level based on code length.

    1-digit -> 1 (Major Group)
    2-digit -> 2 (Sub-Major Group)
    3-digit -> 3 (Minor Group)
    4-digit -> 4 (Unit Group)
    6-digit -> 5 (Occupation)
    'TOT' or other non-numeric -> 0 (aggregate, excluded)
    """
    if not code.isdigit():
        return 0
    n = len(code)
    if n == 1:
        return 1
    if n == 2:
        return 2
    if n == 3:
        return 3
    if n == 4:
        return 4
    if n == 6:
        return 5
    return 0


def _determine_parent(code: str) -> Optional[str]:
    """Return parent code based on ANZSCO level rules.

    1-digit -> None
    2-digit -> first 1 char
    3-digit -> first 2 chars
    4-digit -> first 3 chars
    6-digit -> first 4 chars
    Non-numeric (TOT etc.) -> None
    """
    if not code.isdigit():
        return None
    n = len(code)
    if n == 2:
        return code[:1]
    if n == 3:
        return code[:2]
    if n == 4:
        return code[:3]
    if n == 6:
        return code[:4]
    return None


def _determine_sector(code: str) -> str:
    """Return Major Group (first digit) as sector code."""
    if code and code[0].isdigit():
        return code[0]
    return code


def _parse_sdmx(data: bytes) -> list[tuple[str, str, int, Optional[str], str, bool]]:
    """Parse ANZSCO SDMX XML into (code, title, level, parent, sector, is_leaf) rows.

    Excludes 'TOT' (all occupations aggregate).
    is_leaf = True for level 5 (6-digit occupation codes).
    """
    root = ET.fromstring(data)
    codes = root.findall(".//structure:Code", _NS)

    all_codes: set[str] = set()
    raw: list[tuple[str, str]] = []

    for c in codes:
        code_id = c.get("id", "")
        if code_id == "TOT":
            continue
        name_el = c.find("common:Name", _NS)
        title = name_el.text if name_el is not None else ""
        all_codes.add(code_id)
        raw.append((code_id, title))

    rows = []
    for code_id, title in raw:
        level = _determine_level(code_id)
        if level == 0:
            continue
        parent = _determine_parent(code_id)
        sector = _determine_sector(code_id)
        is_leaf = level == 5
        rows.append((code_id, title, level, parent, sector, is_leaf))

    return rows


async def ingest_anzsco_2022(conn, path: Optional[str] = None) -> int:
    """Ingest ANZSCO 2022 into classification_system + classification_node.

    Downloads the SDMX codelist from ABS if not already cached locally.
    Returns total nodes inserted.
    """
    local = Path(path or _DEFAULT_PATH)
    ensure_data_file(_URL, local, headers=_HEADERS)

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    data = local.read_bytes()
    rows = _parse_sdmx(data)

    count = 0
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (system_id, code) DO NOTHING""",
            [("anzsco_2022", code, title, level, parent, sector, is_leaf)
             for code, title, level, parent, sector, is_leaf in chunk],
        )
        count += len(chunk)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'anzsco_2022'",
        count,
    )

    return count
