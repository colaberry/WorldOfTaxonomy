"""CPC v2.1 Central Product Classification ingester.

Source: United Nations Statistics Division
        https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/CPC_Ver_2_1_english_structure.Txt
License: open (UN Statistics Division)

Hierarchy (determined by code length):
  L1 - Section (1-digit, e.g. "0" = Agriculture, forestry and fishery products)
  L2 - Division (2-digit, e.g. "01" = Products of agriculture)
  L3 - Group (3-digit, e.g. "011" = Cereals)
  L4 - Class (4-digit, e.g. "0111" = Wheat)
  L5 - Subclass (5-digit, leaf, e.g. "01111" = Wheat, seed)

4,596 nodes total.
"""
import csv
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

DATA_URL = (
    "https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/"
    "CPC_Ver_2_1_english_structure.Txt"
)
DATA_PATH = "data/cpc_v21.txt"


def _determine_level(code: str) -> int:
    """Return hierarchy level based on code length.

    1-digit = Section (L1), 2-digit = Division (L2), 3-digit = Group (L3),
    4-digit = Class (L4), 5-digit = Subclass (L5, leaf).
    """
    return len(code)


def _determine_parent(code: str) -> Optional[str]:
    """Return parent code (drop last digit), or None for sections (L1)."""
    if len(code) <= 1:
        return None
    return code[:-1]


def _determine_sector(code: str) -> str:
    """Return sector code (the 1-digit section)."""
    return code[0]


async def ingest_cpc_v21(conn, path=None) -> int:
    """Ingest CPC v2.1 Central Product Classification into the database.

    Returns total number of nodes inserted.
    """
    path = path or DATA_PATH
    ensure_data_file(DATA_URL, path)

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "cpc_v21",
        "CPC v2.1",
        "Central Product Classification Version 2.1",
        "2.1",
        "Global",
        "United Nations Statistics Division",
    )

    # Parse file
    nodes = []
    with open(path, encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["CPC21code"].strip().strip('"')
            title = row["CPC21title"].strip().strip('"')
            if not code:
                continue
            nodes.append((code, title))

    # Leaf detection: any code that is not a parent of another
    parent_set = {_determine_parent(code) for code, _ in nodes if _determine_parent(code) is not None}

    # Build records
    records = []
    for seq, (code, title) in enumerate(nodes, start=1):
        level = _determine_level(code)
        parent = _determine_parent(code)
        sector = _determine_sector(code)
        is_leaf = code not in parent_set
        records.append(("cpc_v21", code, title, level, parent, sector, is_leaf, seq))

    # Batch insert in chunks of 500
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
        count, "cpc_v21",
    )
    return count
