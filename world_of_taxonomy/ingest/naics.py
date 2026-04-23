"""NAICS 2022 ingester.

Parses the Census Bureau Excel file and loads into PostgreSQL.
Source: https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx
"""

from pathlib import Path
from typing import Optional

import openpyxl

from world_of_taxonomy.ingest.base import ensure_data_file
from world_of_taxonomy.models import NAICS_SECTOR_MAP

# Census Bureau download URL for NAICS 2022 structure
NAICS_2022_URL = "https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx"
NAICS_2022_LOCAL = Path("data/naics/2022_NAICS_Codes.xlsx")

# Provenance metadata for the system row.
_SOURCE_URL = NAICS_2022_URL
_DATA_PROVENANCE = "official_download"
_LICENSE = "Public Domain"
# Per-code authority deep link. `{code}` is substituted per node so the
# frontend can link any NAICS 2022 node to its Census Bureau page.
_NODE_URL_TEMPLATE = "https://www.census.gov/naics/?input={code}&year=2022"

# Range sector codes
RANGE_SECTORS = {"31-33", "44-45", "48-49"}


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _determine_level(code: str) -> int:
    """Determine hierarchy level from NAICS code.

    2-digit or range = level 1 (sector)
    3-digit = level 2 (subsector)
    4-digit = level 3 (industry group)
    5-digit = level 4 (NAICS industry)
    6-digit = level 5 (national industry)
    """
    if code in RANGE_SECTORS:
        return 1
    code_len = len(code)
    if code_len == 2:
        return 1
    return code_len - 1


def _determine_parent(code: str) -> Optional[str]:
    """Determine parent code for a NAICS code.

    For range-based children (e.g., codes starting with 31, 32, 33),
    the parent is the range code "31-33".
    """
    if code in RANGE_SECTORS:
        return None  # Sectors have no parent

    code_len = len(code)
    if code_len == 2:
        return None  # Sectors have no parent

    if code_len == 3:
        # Subsector: parent is the 2-digit prefix, but check range sectors
        prefix = code[:2]
        return NAICS_SECTOR_MAP.get(prefix, prefix)

    # For 4-6 digit codes, parent is one digit shorter
    return code[:-1]


def _determine_sector(code: str) -> str:
    """Determine the top-level sector code for color lookup."""
    if code in RANGE_SECTORS:
        return code
    prefix = code[:2]
    return NAICS_SECTOR_MAP.get(prefix, prefix)


async def ingest_naics_2022(conn, xlsx_path: Optional[Path] = None) -> int:
    """Ingest NAICS 2022 codes from Census Bureau Excel file.

    Args:
        conn: asyncpg connection
        xlsx_path: Path to Excel file. Downloads if None.

    Returns:
        Number of codes ingested.
    """
    if xlsx_path is None:
        xlsx_path = ensure_data_file(
            NAICS_2022_URL,
            _get_project_root() / NAICS_2022_LOCAL,
        )

    # Register the classification system (idempotent). Provenance and the
    # per-code URL template are refreshed on every run so re-ingesting
    # brings stale rows up to date.
    await conn.execute(
        """
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, url, tint_color,
             source_url, source_date, data_provenance, license, node_url_template)
        VALUES ('naics_2022', 'NAICS 2022',
                'North American Industry Classification System 2022',
                'North America', '2022', 'U.S. Census Bureau',
                'https://www.census.gov/naics/', '#F59E0B',
                $1, CURRENT_DATE, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE SET
            node_count = 0,
            source_url = EXCLUDED.source_url,
            source_date = CURRENT_DATE,
            data_provenance = EXCLUDED.data_provenance,
            license = EXCLUDED.license,
            node_url_template = EXCLUDED.node_url_template
        """,
        _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, _NODE_URL_TEMPLATE,
    )

    # Parse the Excel file
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
    ws = wb.active

    nodes = []
    seq = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        # Expected columns: Seq No, 2022 NAICS Code, 2022 NAICS Title
        if len(row) < 3:
            continue

        raw_code = row[1]
        title = row[2]

        if raw_code is None or title is None:
            continue

        code = str(raw_code).strip()
        title = str(title).strip()

        # Skip header rows or empty
        if not code or code.lower() == 'code':
            continue

        # Handle range codes like "31-33"
        if '-' in code and not code.replace('-', '').isdigit():
            continue  # Skip non-numeric ranges that aren't sector ranges

        seq += 1
        level = _determine_level(code)
        parent = _determine_parent(code)
        sector = _determine_sector(code)

        nodes.append((code, title, level, parent, sector, seq))

    # Determine leaf status: a node is a leaf if no other node has it as parent
    parent_set = {n[3] for n in nodes if n[3] is not None}
    code_set = {n[0] for n in nodes}

    # Batch insert
    count = 0
    for code, title, level, parent, sector, seq_order in nodes:
        is_leaf = code not in parent_set
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('naics_2022', $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (system_id, code) DO NOTHING
        """, code, title, level, parent, sector, is_leaf, seq_order)
        count += 1

    # Update node count
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'naics_2022'",
        count,
    )

    wb.close()
    print(f"  Ingested {count} NAICS 2022 codes")
    return count
