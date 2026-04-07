"""SIC 1987 ingester.

Parses Standard Industrial Classification codes from two sources:
1. OSHA SIC Manual HTML (divisions + major groups) — already downloaded
2. BLS SIC titles CSV (industry groups + industries) — downloaded on demand

Structure:
  Division (letter A-J)  = level 0
  Major Group (2-digit)  = level 1
  Industry Group (3-digit) = level 2
  Industry (4-digit)     = level 3

Source: https://www.osha.gov/data/sic-manual
       https://www.bls.gov/cew/classifications/industry/sic-titles.csv
"""

import csv
import io
import re
from pathlib import Path
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

# ── Data sources ────────────────────────────────────────────────

BLS_SIC_CSV_URL = "https://www.bls.gov/cew/classifications/industry/sic-titles.csv"
BLS_SIC_LOCAL = Path("data/sic/sic-titles.csv")

OSHA_HTML_LOCAL = Path("data/sic/OSHA_SIC.html")

# ── Division structure (A-J) ────────────────────────────────────
# Maps division letter -> (title, range of major group numbers)

SIC_DIVISION_STRUCTURE = {
    "A": ("Agriculture, Forestry, And Fishing", range(1, 10)),       # 01-09
    "B": ("Mining", range(10, 15)),                                   # 10-14
    "C": ("Construction", range(15, 18)),                             # 15-17
    "D": ("Manufacturing", range(20, 40)),                            # 20-39
    "E": ("Transportation, Communications, Electric, Gas, And Sanitary Services",
          range(40, 50)),                                             # 40-49
    "F": ("Wholesale Trade", range(50, 52)),                          # 50-51
    "G": ("Retail Trade", range(52, 60)),                             # 52-59
    "H": ("Finance, Insurance, And Real Estate", range(60, 68)),      # 60-67
    "I": ("Services", range(70, 90)),                                 # 70-89
    "J": ("Public Administration", range(91, 100)),                   # 91-99
}

# Build reverse lookup: major group number -> division letter
_MG_TO_DIVISION = {}
for division, (_, mg_range) in SIC_DIVISION_STRUCTURE.items():
    for mg in mg_range:
        _MG_TO_DIVISION[mg] = division


def _get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def _determine_level(code: str) -> int:
    """Determine hierarchy level for SIC code.

    Letter (A-J) = level 0 (division)
    2-digit      = level 1 (major group)
    3-digit      = level 2 (industry group)
    4-digit      = level 3 (industry)
    """
    if code.isalpha():
        return 0
    return len(code) - 1


def _determine_parent(code: str) -> Optional[str]:
    """Determine parent code for SIC code."""
    if code.isalpha():
        return None  # Divisions have no parent

    if len(code) == 2:
        # Major Group -> Division
        mg_num = int(code)
        return _MG_TO_DIVISION.get(mg_num)

    # Industry Group (3-digit) -> Major Group (2-digit)
    # Industry (4-digit) -> Industry Group (3-digit)
    return code[:-1]


def _determine_sector(code: str) -> str:
    """Determine top-level division for a SIC code."""
    if code.isalpha():
        return code
    mg_num = int(code[:2])
    return _MG_TO_DIVISION.get(mg_num, "?")


# ── OSHA HTML parsing ──────────────────────────────────────────

def _parse_osha_html(html_path: Path) -> list[tuple[str, str]]:
    """Parse divisions and major groups from OSHA SIC Manual HTML.

    Returns list of (code, title) tuples.
    Divisions have letter codes (A-J), major groups have 2-digit codes.
    """
    text = html_path.read_text(encoding="utf-8")
    results = []

    # Match division links: "Division A: Agriculture, Forestry, And Fishing"
    div_pattern = re.compile(
        r'Division\s+([A-J]):\s*(.+?)(?:<|")', re.IGNORECASE
    )
    for match in div_pattern.finditer(text):
        letter = match.group(1).upper()
        title = match.group(2).strip()
        if (letter, title) not in [(c, t) for c, t in results]:
            results.append((letter, title))

    # Match major group links: "Major Group 01: Agricultural Production Crops"
    mg_pattern = re.compile(
        r'Major\s+Group\s+(\d{2}):\s*(.+?)(?:<|")', re.IGNORECASE
    )
    for match in mg_pattern.finditer(text):
        code = match.group(1)
        title = match.group(2).strip()
        if (code, title) not in [(c, t) for c, t in results]:
            results.append((code, title))

    return results


# ── BLS CSV parsing ────────────────────────────────────────────

def _parse_bls_csv(csv_path: Path) -> list[tuple[str, str]]:
    """Parse SIC codes from BLS CSV file.

    The BLS CSV has columns like: industry_code, industry_title
    Codes may be prefixed with 'SIC' or have various formats.
    Returns list of (code, title) tuples for 2/3/4-digit numeric codes.
    """
    text = csv_path.read_text(encoding="utf-8-sig")
    results = []

    reader = csv.reader(io.StringIO(text))
    header = None

    for row in reader:
        if not row:
            continue

        # Detect header row
        if header is None:
            # Look for a row that contains 'code' and 'title' columns
            lower_row = [c.lower().strip() for c in row]
            if any("code" in c for c in lower_row) and any("title" in c for c in lower_row):
                header = lower_row
                continue
            # If first row looks like data (numeric first col), no header
            if row[0].strip().isdigit():
                header = []  # Mark as no-header
            else:
                continue

        # Find code and title columns
        if header:
            code_idx = next(
                (i for i, h in enumerate(header) if "code" in h), 0
            )
            title_idx = next(
                (i for i, h in enumerate(header) if "title" in h), 1
            )
        else:
            code_idx, title_idx = 0, 1

        if len(row) <= max(code_idx, title_idx):
            continue

        raw_code = row[code_idx].strip().strip('"')
        title = row[title_idx].strip().strip('"')

        # Clean code: remove 'SIC' prefix, spaces, etc.
        code = raw_code.replace("SIC", "").replace(" ", "").strip()

        # Only want 2, 3, or 4-digit numeric codes
        if not code.isdigit():
            continue
        if len(code) < 2 or len(code) > 4:
            continue

        # Zero-pad to expected length (some CSVs drop leading zeros)
        # 2-digit codes should be at least 2 chars
        if len(code) == 1:
            code = code.zfill(2)

        results.append((code, title))

    return results


GITHUB_SIC_CSV_LOCAL = Path("data/sic/sic-codes.csv")


def _parse_github_csv(csv_path: Path) -> list[tuple[str, str]]:
    """Parse SIC codes from GitHub CSV format.

    Expected columns: Division, Major Group, Industry Group, SIC, Description
    Produces (code, title) tuples for all hierarchy levels found.
    """
    text = csv_path.read_text(encoding="utf-8-sig")
    results = []
    seen = set()

    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if not header:
        return results

    # Find column indices
    lower = [c.lower().strip() for c in header]
    try:
        div_idx = next(i for i, h in enumerate(lower) if 'division' in h)
        mg_idx = next(i for i, h in enumerate(lower) if 'major' in h)
        ig_idx = next(i for i, h in enumerate(lower) if 'industry group' in h or 'group' in h)
        sic_idx = next(i for i, h in enumerate(lower) if 'sic' in h)
        desc_idx = next(i for i, h in enumerate(lower) if 'desc' in h)
    except StopIteration:
        return results

    for row in reader:
        if not row or len(row) <= max(div_idx, mg_idx, ig_idx, sic_idx, desc_idx):
            continue

        sic_code = str(row[sic_idx]).strip()
        description = str(row[desc_idx]).strip()

        if not sic_code or not sic_code.isdigit():
            continue

        # Zero-pad to 4 digits
        sic_code = sic_code.zfill(4)

        if sic_code not in seen:
            seen.add(sic_code)
            results.append((sic_code, description))

        # Also extract major group (2-digit) and industry group (3-digit) if present
        mg = str(row[mg_idx]).strip()
        if mg and mg.isdigit():
            mg = mg.zfill(2)
            if mg not in seen:
                seen.add(mg)
                # Use the description of the first SIC code in this major group
                results.append((mg, description.split(',')[0] if ',' in description else description))

        ig = str(row[ig_idx]).strip()
        if ig and ig.isdigit():
            ig = ig.zfill(3)
            if ig not in seen:
                seen.add(ig)
                results.append((ig, description.split(',')[0] if ',' in description else description))

    return results


# ── Main ingestion ─────────────────────────────────────────────

async def ingest_sic_1987(conn, csv_path: Optional[Path] = None,
                          html_path: Optional[Path] = None) -> int:
    """Ingest SIC 1987 codes.

    Strategy:
    1. Parse OSHA HTML for divisions (A-J) and major groups (2-digit)
    2. Download/parse BLS CSV for industry groups (3-digit) and industries (4-digit)
    3. Merge: OSHA HTML is authoritative for divisions/major groups;
       BLS CSV fills in the 3-digit and 4-digit codes.

    If OSHA HTML is not available, uses hardcoded division structure.
    If BLS CSV is not available, ingests only divisions and major groups from HTML.

    Args:
        conn: asyncpg connection
        csv_path: Path to BLS CSV file. Downloads if None.
        html_path: Path to OSHA HTML file. Uses default if None.

    Returns:
        Number of codes ingested.
    """
    # Register the classification system
    await conn.execute("""
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, url, tint_color)
        VALUES ('sic_1987', 'SIC 1987',
                'Standard Industrial Classification 1987',
                'USA/UK', '1987', 'U.S. Office of Management and Budget',
                'https://www.osha.gov/data/sic-manual', '#78716C')
        ON CONFLICT (id) DO UPDATE SET node_count = 0
    """)

    root = _get_project_root()

    # ── Step 1: Parse divisions and major groups from OSHA HTML ──
    osha_codes = {}  # code -> title

    if html_path is None:
        html_path = root / OSHA_HTML_LOCAL

    if html_path.exists():
        for code, title in _parse_osha_html(html_path):
            osha_codes[code] = title
        print(f"  Parsed {len(osha_codes)} codes from OSHA HTML")

    # Always ensure hardcoded divisions are present (fallback)
    for letter, (title, _) in SIC_DIVISION_STRUCTURE.items():
        if letter not in osha_codes:
            osha_codes[letter] = title

    # ── Step 2: Parse 3-digit and 4-digit codes from BLS CSV ──
    bls_codes = {}  # code -> title

    if csv_path is None:
        try:
            csv_path = ensure_data_file(
                BLS_SIC_CSV_URL,
                root / BLS_SIC_LOCAL,
            )
        except Exception as e:
            print(f"  Warning: Could not download BLS CSV: {e}")
            csv_path = root / BLS_SIC_LOCAL

    if csv_path.exists():
        for code, title in _parse_bls_csv(csv_path):
            bls_codes[code] = title
        print(f"  Parsed {len(bls_codes)} codes from BLS CSV")

    # Fallback: try GitHub CSV if BLS didn't yield much
    if len(bls_codes) < 50:
        github_csv = root / GITHUB_SIC_CSV_LOCAL
        if github_csv.exists():
            for code, title in _parse_github_csv(github_csv):
                if code not in bls_codes:
                    bls_codes[code] = title
            print(f"  Total {len(bls_codes)} codes after GitHub CSV fallback")

    # ── Step 3: Merge and build node list ──
    # Priority: OSHA HTML for divisions/major groups, BLS CSV for industry groups/industries
    merged = {}

    # Add divisions from OSHA (or hardcoded fallback)
    for code, title in osha_codes.items():
        merged[code] = title

    # Add BLS codes (2-digit will be overridden by OSHA if present)
    for code, title in bls_codes.items():
        if code not in merged:
            merged[code] = title
        elif len(code) > 2:
            # 3-digit and 4-digit always come from BLS
            merged[code] = title

    # Build ordered node list
    nodes = []
    seq = 0

    # Sort: divisions first (letters), then numeric codes by value
    def sort_key(code: str):
        if code.isalpha():
            return (0, ord(code), 0)
        return (1, int(code), len(code))

    for code in sorted(merged.keys(), key=sort_key):
        title = merged[code]
        level = _determine_level(code)
        parent = _determine_parent(code)
        sector = _determine_sector(code)

        # Skip codes whose parent division doesn't exist in our mapping
        if parent == "?" or sector == "?":
            continue

        seq += 1
        nodes.append((code, title, level, parent, sector, seq))

    # Determine leaf status
    parent_set = {n[3] for n in nodes if n[3] is not None}

    count = 0
    for code, title, level, parent, sector, seq_order in nodes:
        is_leaf = code not in parent_set
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('sic_1987', $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (system_id, code) DO NOTHING
        """, code, title, level, parent, sector, is_leaf, seq_order)
        count += 1

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'sic_1987'",
        count,
    )

    print(f"  Ingested {count} SIC 1987 codes")
    return count
