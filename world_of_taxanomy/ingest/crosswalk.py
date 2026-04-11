"""NAICS-to-ISIC crosswalk ingester.

Parses the Census Bureau concordance file mapping NAICS 2022 to ISIC Rev 4.
Source: https://www.census.gov/naics/concordances/2022_NAICS_to_ISIC_Rev_4.xlsx

Actual Excel layout (7 columns):
  0: "Part of NAICS" marker (None or text)
  1: NAICS code (int)
  2: NAICS title
  3: "Part of ISIC" marker (* = partial, None = full)
  4: ISIC code (int)
  5: ISIC title
  6: Notes
"""

from pathlib import Path
from typing import Optional

import openpyxl

from world_of_taxanomy.ingest.base import ensure_data_file

# Census Bureau concordance file
CROSSWALK_URL = "https://www.census.gov/naics/concordances/2022_NAICS_to_ISIC_Rev_4.xlsx"
CROSSWALK_LOCAL = Path("data/crosswalk/2022_NAICS_to_ISIC_Rev_4.xlsx")


def _get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def _determine_match_type(part_of_naics, part_of_isic) -> str:
    """Determine match type from the 'Part of' marker columns.

    If either column has a marker (* or text), it's a partial match.
    If both are empty/None, the mapping covers the full code - exact.
    """
    has_naics_part = part_of_naics is not None and str(part_of_naics).strip() != ""
    has_isic_part = part_of_isic is not None and str(part_of_isic).strip() != ""

    if has_naics_part or has_isic_part:
        return "partial"
    return "exact"


async def ingest_crosswalk(conn, file_path: Optional[Path] = None) -> int:
    """Ingest NAICS 2022 to ISIC Rev 4 crosswalk.

    Inserts bidirectional equivalence edges:
    - NAICS -> ISIC
    - ISIC -> NAICS (reverse)

    Args:
        conn: asyncpg connection
        file_path: Path to Excel file. Downloads if None.

    Returns:
        Number of equivalence edges ingested (bidirectional count).
    """
    if file_path is None:
        file_path = ensure_data_file(
            CROSSWALK_URL,
            _get_project_root() / CROSSWALK_LOCAL,
        )

    wb = openpyxl.load_workbook(str(file_path), read_only=True)
    ws = wb.active

    count = 0
    seen = set()

    for row in ws.iter_rows(min_row=2, values_only=True):
        if len(row) < 5:
            continue

        # Columns: [0]=Part of NAICS, [1]=NAICS code, [2]=NAICS title,
        #           [3]=Part of ISIC, [4]=ISIC code, [5]=ISIC title, [6]=Notes
        raw_naics = row[1]
        raw_isic = row[4]

        if raw_naics is None or raw_isic is None:
            continue

        # Convert codes to strings, zero-pad ISIC if needed
        naics_str = str(int(raw_naics)).strip() if isinstance(raw_naics, (int, float)) else str(raw_naics).strip()
        isic_str = str(int(raw_isic)).strip() if isinstance(raw_isic, (int, float)) else str(raw_isic).strip()

        # Skip code 0 (placeholder for "Multiple NAICS industries")
        if naics_str == "0" or isic_str == "0":
            continue

        # Validate NAICS: numeric, 2-6 digits (or range like 31-33)
        if not (naics_str.replace('-', '').isdigit() and 2 <= len(naics_str) <= 7):
            continue

        # Validate ISIC: numeric, 1-4 digits
        if not (isic_str.isdigit() and 1 <= len(isic_str) <= 4):
            continue

        # Deduplicate
        pair = (naics_str, isic_str)
        if pair in seen:
            continue
        seen.add(pair)

        # Determine match type from "Part of" columns
        part_of_naics = row[0]
        part_of_isic = row[3]
        match_type = _determine_match_type(part_of_naics, part_of_isic)

        # Insert forward: NAICS -> ISIC
        await conn.execute("""
            INSERT INTO equivalence (source_system, source_code, target_system, target_code, match_type)
            VALUES ('naics_2022', $1, 'isic_rev4', $2, $3)
            ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING
        """, naics_str, isic_str, match_type)

        # Insert reverse: ISIC -> NAICS
        await conn.execute("""
            INSERT INTO equivalence (source_system, source_code, target_system, target_code, match_type)
            VALUES ('isic_rev4', $1, 'naics_2022', $2, $3)
            ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING
        """, isic_str, naics_str, match_type)

        count += 2  # Both directions

    wb.close()
    print(f"  Ingested {count} crosswalk edges ({count // 2} pairs, bidirectional)")
    return count
