"""HS 2022 Harmonized System ingester.

Source: github.com/datasets/harmonized-system (CC0)
        https://raw.githubusercontent.com/datasets/harmonized-system/main/data/harmonized-system.csv
License: CC0 (public domain)

Hierarchy:
  L1 - Section (Roman numeral, e.g. "I" = Live animals and animal products)
  L2 - Chapter (2-digit, e.g. "01" = Live animals)
  L3 - Heading (4-digit, e.g. "0101" = Horses, asses, mules, hinnies; live)
  L4 - Subheading (6-digit, leaf, e.g. "010121" = Pure-bred breeding horses)

~6,960 nodes total.
"""
import csv
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

DATA_URL = (
    "https://raw.githubusercontent.com/datasets/harmonized-system/main/data/harmonized-system.csv"
)
DATA_PATH = "data/hs2022.csv"

# 21 HS sections with official short names
_SECTION_NAMES = {
    "I":    "Live animals; animal products",
    "II":   "Vegetable products",
    "III":  "Animal or vegetable fats and oils and their cleavage products",
    "IV":   "Prepared foodstuffs; beverages, spirits and vinegar; tobacco",
    "V":    "Mineral products",
    "VI":   "Products of the chemical or allied industries",
    "VII":  "Plastics and articles thereof; rubber and articles thereof",
    "VIII": "Raw hides and skins, leather, furskins and articles thereof",
    "IX":   "Wood and articles of wood; wood charcoal; cork; straw manufactures",
    "X":    "Pulp of wood; paper or paperboard and articles thereof",
    "XI":   "Textiles and textile articles",
    "XII":  "Footwear, headgear, umbrellas, walking sticks, whips; prepared feathers",
    "XIII": "Articles of stone, plaster, cement, asbestos, mica; ceramic products; glass",
    "XIV":  "Natural or cultured pearls, precious stones, precious metals; imitation jewellery",
    "XV":   "Base metals and articles of base metal",
    "XVI":  "Machinery and mechanical appliances; electrical equipment",
    "XVII": "Vehicles, aircraft, vessels and associated transport equipment",
    "XVIII":"Optical, photographic, measuring, medical instruments; clocks; musical instruments",
    "XIX":  "Arms and ammunition; parts and accessories thereof",
    "XX":   "Miscellaneous manufactured articles",
    "XXI":  "Works of art, collectors' pieces and antiques",
}

# Set of valid section codes for O(1) lookup
_SECTION_CODES = frozenset(_SECTION_NAMES.keys())


def _determine_level(code: str) -> int:
    """Return hierarchy level based on code format.

    L1 = Section (Roman numeral)
    L2 = Chapter (2-digit numeric)
    L3 = Heading (4-digit numeric)
    L4 = Subheading (6-digit numeric, leaf)
    """
    if code in _SECTION_CODES:
        return 1
    if len(code) == 2:
        return 2
    if len(code) == 4:
        return 3
    return 4


def _determine_parent(code: str, csv_parent: str, section: str) -> Optional[str]:
    """Return parent code.

    Sections have no parent.
    Chapters (L2) parent is their section (Roman numeral).
    Headings and subheadings use the parent column from the CSV.
    """
    if code in _SECTION_CODES:
        return None
    if len(code) == 2:
        return section
    if csv_parent and csv_parent not in ("TOTAL", ""):
        return csv_parent
    return None


def _determine_sector(code: str, section: str) -> str:
    """Return sector code (the section Roman numeral) for any node."""
    if code in _SECTION_CODES:
        return code
    return section


async def ingest_hs2022(conn, path=None) -> int:
    """Ingest HS 2022 Harmonized System into the database.

    Returns total number of nodes inserted.
    """
    path = path or DATA_PATH
    ensure_data_file(DATA_URL, path)

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "hs_2022",
        "HS 2022",
        "Harmonized Commodity Description and Coding System",
        "2022",
        "Global",
        "World Customs Organization",
    )

    # Parse CSV
    nodes = []  # (code, title, level, parent, section)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["hscode"].strip()
            title = row["description"].strip()
            section = row["section"].strip()
            csv_parent = row["parent"].strip()

            # Skip the synthetic TOTAL root row
            if code == "TOTAL":
                continue

            level = _determine_level(code)
            parent = _determine_parent(code, csv_parent, section)
            sector = _determine_sector(code, section)
            nodes.append((code, title, level, parent, sector))

    # Insert section nodes first (L1) - hardcoded names, not in CSV
    # We derive section membership from chapters in the CSV
    chapter_to_section = {}
    for code, title, level, parent, sector in nodes:
        if level == 2:
            chapter_to_section[code] = sector

    present_sections = sorted({sector for _, _, level, _, sector in nodes if level == 2})

    # Determine which codes have children (non-leaf detection)
    parent_set = {parent for _, _, _, parent, _ in nodes if parent is not None}

    # Build full records list: sections first, then chapters/headings/subheadings
    records = []
    seq = 0

    for sec_code in present_sections:
        seq += 1
        sec_name = _SECTION_NAMES.get(sec_code, sec_code)
        records.append(("hs_2022", sec_code, sec_name, 1, None, sec_code, False, seq))

    for code, title, level, parent, sector in nodes:
        seq += 1
        is_leaf = code not in parent_set
        records.append(("hs_2022", code, title, level, parent, sector, is_leaf, seq))

    # Batch insert in chunks of 500 to avoid Neon timeout on large datasets
    CHUNK = 500
    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT DO NOTHING""",
            chunk,
        )
        count += len(chunk)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, "hs_2022",
    )
    return count
