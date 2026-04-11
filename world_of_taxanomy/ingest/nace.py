"""NACE Rev 2 ingester.

Builds the NACE Rev 2 classification structure from the ISIC4-to-NACE2
crosswalk file.  NACE codes are extracted from the crosswalk, and titles
are looked up from the ISIC Rev 4 codes already stored in the database.

Source crosswalk: Eurostat RAMON correspondence table.
"""

import csv
from pathlib import Path
from typing import Optional

from world_of_taxanomy.ingest.isic import _DIV_TO_SECTION

CROSSWALK_LOCAL = Path("data/crosswalk/ISIC4_to_NACE2.txt")


def _get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


# ── NACE code helpers ────────────────────────────────────────────


def _nace_level(code: str) -> int:
    """Determine hierarchy level for a NACE code.

    Letter       = level 0 (section)
    2-digit      = level 1 (division)     e.g. "01"
    XX.X format  = level 2 (group)        e.g. "01.1"
    XX.XX format = level 3 (class)        e.g. "01.11"
    """
    if code.isalpha():
        return 0
    if code.isdigit() and len(code) == 2:
        return 1
    if "." in code:
        after_dot = code.split(".", 1)[1]
        return 2 if len(after_dot) == 1 else 3
    return 1  # fallback for bare 2-digit


def _nace_parent(code: str) -> Optional[str]:
    """Determine the parent code for a NACE code."""
    if code.isalpha():
        return None  # sections have no parent

    if code.isdigit() and len(code) == 2:
        # Division -> Section (reuse ISIC's mapping - identical for NACE)
        div_num = int(code)
        return _DIV_TO_SECTION.get(div_num)

    if "." in code:
        before_dot, after_dot = code.split(".", 1)
        if len(after_dot) == 1:
            # Group (XX.X) -> Division (XX)
            return before_dot
        # Class (XX.XX) -> Group (XX.X)
        return before_dot + "." + after_dot[0]

    return None


def _nace_sector(code: str) -> str:
    """Determine the top-level section letter for a NACE code."""
    if code.isalpha():
        return code
    digits = code.split(".")[0]
    if digits.isdigit():
        div_num = int(digits)
        return _DIV_TO_SECTION.get(div_num, "?")
    return "?"


def _nace_to_isic(code: str) -> str:
    """Convert a NACE code to its ISIC equivalent by stripping dots.

    "01.11" -> "0111"
    "01.1"  -> "011"
    "01"    -> "01"
    "A"     -> "A"
    """
    return code.replace(".", "")


def _determine_match_type(isic_part: int, nace_part: int) -> str:
    """Determine equivalence match type from part flags.

    Part = 0 on both sides means exact 1:1 correspondence.
    Part = 1 on either side means the code is split (partial).
    """
    if isic_part != 0 or nace_part != 0:
        return "partial"
    return "exact"


# ── Crosswalk parser ─────────────────────────────────────────────


def parse_crosswalk(file_path: Path) -> list[dict]:
    """Parse the ISIC4-to-NACE2 crosswalk CSV.

    Returns a list of dicts with keys:
      isic_code, isic_part, nace_code, nace_part
    """
    rows = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header row
        for row in reader:
            if len(row) < 4:
                continue
            isic_code = row[0].strip()
            isic_part = int(row[1].strip())
            nace_code = row[2].strip()
            nace_part = int(row[3].strip())
            rows.append({
                "isic_code": isic_code,
                "isic_part": isic_part,
                "nace_code": nace_code,
                "nace_part": nace_part,
            })
    return rows


# ── Main ingesters ───────────────────────────────────────────────


async def ingest_nace_rev2(conn, file_path: Optional[Path] = None) -> int:
    """Ingest NACE Rev 2 classification nodes.

    Extracts unique NACE codes from the crosswalk file, looks up titles
    from the ISIC Rev 4 nodes already in the database, and inserts
    classification_system + classification_node records.

    Must be called AFTER ISIC Rev 4 has been ingested.

    Args:
        conn: asyncpg connection
        file_path: Path to crosswalk CSV. Uses default if None.

    Returns:
        Number of NACE codes ingested.
    """
    # Register the classification system
    await conn.execute("""
        INSERT INTO classification_system (id, name, full_name, region, version, authority, url, tint_color)
        VALUES ('nace_rev2', 'NACE Rev 2',
                'Statistical Classification of Economic Activities in the European Community, Rev. 2',
                'European Union (27 countries)', 'Rev 2', 'Eurostat',
                'https://ec.europa.eu/eurostat/ramon/nomenclatures/index.cfm?TargetUrl=LST_NOM_DTL&StrNom=NACE_REV2',
                '#1E40AF')
        ON CONFLICT (id) DO UPDATE SET node_count = 0
    """)

    if file_path is None:
        file_path = _get_project_root() / CROSSWALK_LOCAL

    # Parse the crosswalk to collect all unique NACE codes
    crosswalk_rows = parse_crosswalk(file_path)

    # Collect unique NACE codes and their corresponding ISIC codes
    nace_codes: set[str] = set()
    # Map NACE code -> first ISIC code seen (for title lookup)
    nace_to_isic_map: dict[str, str] = {}

    for row in crosswalk_rows:
        nace = row["nace_code"]
        isic = row["isic_code"]
        nace_codes.add(nace)
        if nace not in nace_to_isic_map:
            nace_to_isic_map[nace] = isic

    # Load all ISIC titles from the database for lookups
    isic_rows = await conn.fetch(
        "SELECT code, title FROM classification_node WHERE system_id = 'isic_rev4'"
    )
    isic_titles: dict[str, str] = {r["code"]: r["title"] for r in isic_rows}

    # Build nodes sorted by code for stable ordering
    sorted_codes = sorted(nace_codes, key=_sort_key)

    nodes = []
    seq = 0
    for code in sorted_codes:
        seq += 1
        level = _nace_level(code)
        parent = _nace_parent(code)
        sector = _nace_sector(code)

        # Look up title from ISIC equivalent
        isic_equiv = _nace_to_isic(code)
        title = isic_titles.get(isic_equiv)

        if title is None:
            # Try the mapped ISIC code from the crosswalk
            mapped_isic = nace_to_isic_map.get(code)
            if mapped_isic:
                title = isic_titles.get(mapped_isic)

        if title is None:
            # Derive from parent's ISIC title
            if parent:
                parent_isic = _nace_to_isic(parent)
                parent_title = isic_titles.get(parent_isic)
                if parent_title:
                    title = parent_title
                else:
                    title = f"NACE {code}"
            else:
                title = f"NACE {code}"

        nodes.append((code, title, level, parent, sector, seq))

    # Determine leaf status
    parent_set = {n[3] for n in nodes if n[3] is not None}

    count = 0
    for code, title, level, parent, sector, seq_order in nodes:
        is_leaf = code not in parent_set
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('nace_rev2', $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (system_id, code) DO NOTHING
        """, code, title, level, parent, sector, is_leaf, seq_order)
        count += 1

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'nace_rev2'",
        count,
    )

    print(f"  Ingested {count} NACE Rev 2 codes")
    return count


async def ingest_nace_isic_crosswalk(conn, file_path: Optional[Path] = None) -> int:
    """Ingest NACE Rev 2 <-> ISIC Rev 4 equivalence edges from the crosswalk.

    Inserts bidirectional equivalence edges:
    - NACE -> ISIC
    - ISIC -> NACE (reverse)

    Args:
        conn: asyncpg connection
        file_path: Path to crosswalk CSV. Uses default if None.

    Returns:
        Number of equivalence edges ingested (bidirectional count).
    """
    if file_path is None:
        file_path = _get_project_root() / CROSSWALK_LOCAL

    crosswalk_rows = parse_crosswalk(file_path)

    count = 0
    seen: set[tuple[str, str]] = set()

    for row in crosswalk_rows:
        nace = row["nace_code"]
        isic = row["isic_code"]

        pair = (nace, isic)
        if pair in seen:
            continue
        seen.add(pair)

        match_type = _determine_match_type(row["isic_part"], row["nace_part"])

        # Forward: NACE -> ISIC
        await conn.execute("""
            INSERT INTO equivalence (source_system, source_code, target_system, target_code, match_type)
            VALUES ('nace_rev2', $1, 'isic_rev4', $2, $3)
            ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING
        """, nace, isic, match_type)

        # Reverse: ISIC -> NACE
        await conn.execute("""
            INSERT INTO equivalence (source_system, source_code, target_system, target_code, match_type)
            VALUES ('isic_rev4', $1, 'nace_rev2', $2, $3)
            ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING
        """, isic, nace, match_type)

        count += 2

    print(f"  Ingested {count} NACE-ISIC crosswalk edges ({count // 2} pairs, bidirectional)")
    return count


def _sort_key(code: str) -> tuple:
    """Sort key that orders: sections first (alpha), then numeric codes."""
    if code.isalpha():
        return (0, code, 0)
    # Normalize: "01.11" -> (1, "01", 11)
    parts = code.split(".")
    try:
        main = int(parts[0])
    except ValueError:
        main = 0
    sub = int(parts[1]) if len(parts) > 1 else 0
    return (1, f"{main:02d}", sub)
