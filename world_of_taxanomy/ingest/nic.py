"""NIC 2008 ingester.

Parses India's National Industrial Classification 2008 from an Excel file.
NIC 2008 is aligned 1:1 with ISIC Rev 4 up to the 4-digit class level;
India adds a 5th digit for national detail.

Source: https://www.mospi.gov.in/
"""

from pathlib import Path
from typing import Optional

import openpyxl

from world_of_taxanomy.ingest.base import ensure_data_file
from world_of_taxanomy.ingest.isic import ISIC_SECTION_DIVISIONS, _DIV_TO_SECTION

# Download URL and local cache path
NIC_2008_URL = "https://www.mospi.gov.in/sites/default/files/main_menu/national_product_classification/NIC_2008.xlsx"
NIC_2008_LOCAL = Path("data/nic/NIC_2008.xlsx")

# Section names - same as ISIC Rev 4 since NIC 2008 is aligned
SECTION_NAMES = {
    "A": "Agriculture, forestry and fishing",
    "B": "Mining and quarrying",
    "C": "Manufacturing",
    "D": "Electricity, gas, steam and air conditioning supply",
    "E": "Water supply; sewerage, waste management and remediation activities",
    "F": "Construction",
    "G": "Wholesale and retail trade; repair of motor vehicles and motorcycles",
    "H": "Transportation and storage",
    "I": "Accommodation and food service activities",
    "J": "Information and communication",
    "K": "Financial and insurance activities",
    "L": "Real estate activities",
    "M": "Professional, scientific and technical activities",
    "N": "Administrative and support service activities",
    "O": "Public administration and defence; compulsory social security",
    "P": "Education",
    "Q": "Human health and social work activities",
    "R": "Arts, entertainment and recreation",
    "S": "Other service activities",
    "T": "Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use",
    "U": "Activities of extraterritorial organizations and bodies",
}


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _determine_level(code: str) -> int:
    """Determine hierarchy level for NIC code.

    Letter = level 0 (section)
    2-digit = level 1 (division)
    3-digit = level 2 (group)
    4-digit = level 3 (class)
    5-digit = level 4 (sub-class, India-specific)
    """
    if code.isalpha():
        return 0
    return len(code) - 1


def _determine_parent(code: str) -> Optional[str]:
    """Determine parent code for NIC code."""
    if code.isalpha():
        return None  # Sections have no parent

    if len(code) == 2:
        # Division -> Section
        div_num = int(code)
        return _DIV_TO_SECTION.get(div_num)

    # Group (3-digit) -> Division (2-digit)
    # Class (4-digit) -> Group (3-digit)
    # Sub-class (5-digit) -> Class (4-digit)
    return code[:-1]


def _determine_sector(code: str) -> str:
    """Determine top-level section letter for a NIC code."""
    if code.isalpha():
        return code
    div_num = int(code[:2])
    return _DIV_TO_SECTION.get(div_num, "?")


async def ingest_nic_2008(conn, xlsx_path: Optional[Path] = None) -> int:
    """Ingest NIC 2008 codes from the MOSPI Excel file.

    The Excel file contains only numeric codes (2-5 digits). Section nodes
    (A-U) are synthesized using the same division-to-section mapping as
    ISIC Rev 4, since NIC 2008 is aligned with ISIC at the 4-digit level.

    Args:
        conn: asyncpg connection
        xlsx_path: Path to Excel file. Downloads if None.

    Returns:
        Number of codes ingested.
    """
    if xlsx_path is None:
        xlsx_path = ensure_data_file(
            NIC_2008_URL,
            _get_project_root() / NIC_2008_LOCAL,
        )

    # Register the classification system
    await conn.execute("""
        INSERT INTO classification_system (id, name, full_name, region, version, authority, url, tint_color)
        VALUES ('nic_2008', 'NIC 2008',
                'National Industrial Classification 2008',
                'India', '2008', 'Ministry of Statistics and Programme Implementation',
                'https://www.mospi.gov.in/', '#FF6B35')
        ON CONFLICT (id) DO UPDATE SET node_count = 0
    """)

    # Parse the Excel file
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
    ws = wb.active

    nodes = []
    seq = 0
    seen_codes = set()
    seen_sections = set()

    for row in ws.iter_rows(min_row=1, values_only=True):
        if len(row) < 2:
            continue

        raw_code = row[0]
        title = row[1]

        if raw_code is None or title is None:
            continue

        code = str(raw_code).strip()
        title = str(title).strip()

        # Skip header rows or empty
        if not code or not title:
            continue

        # Only accept numeric codes (2-5 digits)
        if not code.isdigit():
            continue

        # Pad single-digit codes if any (shouldn't happen, but be safe)
        if len(code) < 2 or len(code) > 5:
            continue

        if code in seen_codes:
            continue
        seen_codes.add(code)

        # Track which sections we need based on division codes
        if len(code) >= 2:
            div_num = int(code[:2])
            section = _DIV_TO_SECTION.get(div_num)
            if section and section not in seen_sections:
                seen_sections.add(section)
                # Insert section node before its first division
                seq += 1
                section_title = SECTION_NAMES.get(section, f"Section {section}")
                nodes.append((section, section_title, 0, None, section, seq))

        seq += 1
        level = _determine_level(code)
        parent = _determine_parent(code)
        sector = _determine_sector(code)

        if sector == "?":
            seq -= 1  # undo seq increment for skipped row
            continue  # skip codes with unmapped division (e.g. aggregate rows)

        nodes.append((code, title, level, parent, sector, seq))

    # Determine leaf status: a node is a leaf if no other node has it as parent
    parent_set = {n[3] for n in nodes if n[3] is not None}

    # Batch insert
    count = 0
    for code, title, level, parent, sector, seq_order in nodes:
        is_leaf = code not in parent_set
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('nic_2008', $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (system_id, code) DO NOTHING
        """, code, title, level, parent, sector, is_leaf, seq_order)
        count += 1

    # Update node count
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'nic_2008'",
        count,
    )

    wb.close()
    print(f"  Ingested {count} NIC 2008 codes")
    return count
