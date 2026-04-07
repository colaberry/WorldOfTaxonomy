"""ANZSIC 2006 ingester.

Parses the Australian and New Zealand Standard Industrial Classification
(ANZSIC 2006) from an XLS file using xlrd.
Source: Australian Bureau of Statistics / Stats NZ.
"""

from pathlib import Path
from typing import Optional

import xlrd

from world_of_taxanomy.ingest.base import ensure_data_file

ANZSIC_2006_URL = (
    "https://archive.org/download/1292055002-2006/"
    "1292.0.55.002_anzsic%202006%20-%20codes%20and%20titles.xls"
)

ANZSIC_2006_LOCAL = Path("data/anzsic/ANZSIC_2006_codes_titles.xls")

SYSTEM_ID = "anzsic_2006"


def _get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def _determine_level(code: str) -> int:
    """Determine hierarchy level for ANZSIC code.

    Letter (A-S) = level 0 (division)
    2-digit      = level 1 (subdivision)
    3-digit      = level 2 (group)
    4-digit      = level 3 (class)
    """
    if code.isalpha() and len(code) == 1:
        return 0
    if code.isdigit():
        return len(code) - 1
    return -1


def _determine_parent(code: str, current_division: Optional[str],
                       current_subdivision: Optional[str]) -> Optional[str]:
    """Determine parent code for an ANZSIC code.

    Division (letter)  -> None
    Subdivision (2-dig) -> current division letter
    Group (3-dig)       -> first 2 digits (subdivision)
    Class (4-dig)       -> first 3 digits (group)
    """
    if code.isalpha():
        return None

    if len(code) == 2:
        return current_division
    if len(code) == 3:
        return code[:2]
    if len(code) == 4:
        return code[:3]
    return None


def _determine_sector(code: str, current_division: Optional[str]) -> str:
    """Determine top-level division letter for an ANZSIC code."""
    if code.isalpha() and len(code) == 1:
        return code
    return current_division or "?"


def parse_anzsic_xls(file_path: Path) -> list:
    """Parse the ANZSIC 2006 XLS file and return a list of node tuples.

    Each tuple: (code, title, level, parent_code, sector_code, seq_order)
    """
    workbook = xlrd.open_workbook(str(file_path))
    sheet = workbook.sheet_by_name("Classes")

    nodes = []
    seq = 0
    current_division = None
    current_subdivision = None

    # Data rows start at row index 6 (row 7 in 1-based)
    for row_idx in range(6, sheet.nrows):
        row = [sheet.cell_value(row_idx, col) for col in range(sheet.ncols)]

        # Determine which level this row represents by checking columns
        code = None
        title = None

        # Division: col[1] = letter, col[2] = title
        if row[1] and str(row[1]).strip():
            val = str(row[1]).strip()
            if val.isalpha() and len(val) == 1:
                code = val
                title = str(row[2]).strip() if row[2] else ""
                current_division = code
                current_subdivision = None

        # Subdivision: col[2] = 2-digit code, col[3] = title
        elif row[2] and str(row[2]).strip():
            val = str(row[2]).strip()
            # xlrd may read numeric cells as floats
            if isinstance(row[2], float):
                val = str(int(row[2])).zfill(2)
            if val.isdigit() and len(val) == 2:
                code = val
                title = str(row[3]).strip() if row[3] else ""
                current_subdivision = code

        # Group: col[3] = 3-digit code, col[4] = title
        elif row[3] and str(row[3]).strip():
            val = str(row[3]).strip()
            if isinstance(row[3], float):
                val = str(int(row[3])).zfill(3)
            if val.isdigit() and len(val) == 3:
                code = val
                title = str(row[4]).strip() if row[4] else ""

        # Class: col[4] = 4-digit code, col[5] = title
        elif len(row) > 5 and row[4] and str(row[4]).strip():
            val = str(row[4]).strip()
            if isinstance(row[4], float):
                val = str(int(row[4])).zfill(4)
            if val.isdigit() and len(val) == 4:
                code = val
                title = str(row[5]).strip() if len(row) > 5 and row[5] else ""

        if code and title:
            seq += 1
            level = _determine_level(code)
            parent = _determine_parent(code, current_division, current_subdivision)
            sector = _determine_sector(code, current_division)
            nodes.append((code, title, level, parent, sector, seq))

    return nodes


async def ingest_anzsic_2006(conn, file_path: Optional[Path] = None) -> int:
    """Ingest ANZSIC 2006 codes.

    Args:
        conn: asyncpg connection
        file_path: Path to data file. Downloads if None.

    Returns:
        Number of codes ingested.
    """
    # Register the classification system
    await conn.execute("""
        INSERT INTO classification_system (id, name, full_name, region, version, authority, url, tint_color)
        VALUES ('anzsic_2006', 'ANZSIC 2006',
                'Australian and New Zealand Standard Industrial Classification 2006',
                'Australia, New Zealand', '2006 (Revision 2.0)', 'ABS + Stats NZ',
                'https://www.abs.gov.au/ausstats/abs@.nsf/mf/1292.0', '#14B8A6')
        ON CONFLICT (id) DO UPDATE SET node_count = 0
    """)

    if file_path is None:
        file_path = ensure_data_file(
            ANZSIC_2006_URL,
            _get_project_root() / ANZSIC_2006_LOCAL,
        )

    nodes = parse_anzsic_xls(file_path)

    # Determine leaf status
    parent_set = {n[3] for n in nodes if n[3] is not None}

    count = 0
    for code, title, level, parent, sector, seq_order in nodes:
        is_leaf = code not in parent_set
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('anzsic_2006', $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (system_id, code) DO NOTHING
        """, code, title, level, parent, sector, is_leaf, seq_order)
        count += 1

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'anzsic_2006'",
        count,
    )

    print(f"  Ingested {count} ANZSIC 2006 codes")
    return count
