"""O*NET-SOC ingester.

O*NET (Occupational Information Network), US Department of Labor.
Published in collaboration with the National Center for O*NET Development.
License: CC BY 4.0
Reference: https://www.onetcenter.org/database.html

O*NET codes extend SOC 2018 with decimal suffixes:
  Base occupations: '11-1011.00' (stored - maps 1:1 with SOC detailed occ.)
  Sub-occupations:  '11-1011.03' (excluded - O*NET-specific specialisations)

Only base occupations (codes ending '.00') are stored. This gives ~867 nodes
that align with the SOC 2018 detailed occupation tier.

Structure:
  ~867 occupation nodes
  code = O*NET-SOC code, e.g. '11-1011.00'
  title = occupation title
  level = 1 (all flat)
  parent_code = None
  sector_code = SOC major group prefix (first 2 digits), e.g. '11'
  is_leaf = True

Download: Occupation Data.txt from O*NET Database v29.0
  https://www.onetcenter.org/dl_files/database/db_29_0_text/Occupation%20Data.txt
"""
from __future__ import annotations

import csv
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

_DOWNLOAD_URL = (
    "https://www.onetcenter.org/dl_files/database/db_29_0_text/Occupation%20Data.txt"
)
_DEFAULT_PATH = "data/onet_occupation_data.txt"

CHUNK = 500

_SYSTEM_ROW = (
    "onet_soc",
    "O*NET-SOC",
    "Occupational Information Network - Standard Occupational Classification",
    "29.0",
    "United States",
    "US Department of Labor / National Center for O*NET Development",
)


def _determine_sector(code: str) -> str:
    """Return the SOC major group prefix (first 2 digits before hyphen).

    Example: '11-1011.00' -> '11'
    """
    return code[:2]


def _is_base_occupation(code: str) -> bool:
    """Return True if code is a base O*NET occupation (ends '.00').

    Base occupations map 1:1 with SOC 2018 detailed occupations.
    Sub-occupations (e.g., '.03') are O*NET-specific specialisations.
    """
    return code.endswith(".00")


async def ingest_onet_soc(conn, path: Optional[str] = None) -> int:
    """Ingest O*NET-SOC base occupations from Occupation Data.txt.

    Downloads from the O*NET v29.0 database release.
    Stores ~867 base occupations (codes ending '.00') as a flat system.

    Returns count of nodes inserted (or already present on re-run).
    """
    local = path or _DEFAULT_PATH
    ensure_data_file(_DOWNLOAD_URL, local)

    # Register system
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    records: list[tuple] = []
    seen_codes: set[str] = set()

    with open(local, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            code = row.get("O*NET-SOC Code", "").strip()
            title = row.get("Title", "").strip()

            if not code or not title:
                continue
            if not _is_base_occupation(code):
                continue
            if code in seen_codes:
                continue

            seen_codes.add(code)
            records.append((
                "onet_soc",
                code,
                title,
                1,                      # level: flat
                None,                   # parent_code: crosswalk handles SOC relationship
                _determine_sector(code),  # sector_code: 2-digit major group
                True,                   # is_leaf: all are leaves
            ))

    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (system_id, code) DO NOTHING""",
            chunk,
        )
        count += len(chunk)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'onet_soc'",
        count,
    )

    return count
