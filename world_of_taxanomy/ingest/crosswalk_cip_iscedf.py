"""CIP 2020 <-> ISCED-F 2013 crosswalk ingester.

Source: Statistics Canada CIP 2016 / ISCED-F 2013 concordance (public domain)
  Locally downloaded as data/cip2016_iscedf.csv (encoding: latin-1)
  Columns: CIP Canada 2016 Code, CIP Canada 2016 Title, ISCED-F 2013 Code, ISCED-F 2013 Title

CIP codes (same format as CIP 2020) are filtered to those present in our cip_2020 DB.
ISCED codes ending with '*' indicate partial coverage - asterisk is stripped, match_type='partial'.
ISCED codes without '*' use match_type='exact'.
ISCED codes are filtered to those present in our iscedf_2013 DB.

~1,807 valid pairs x 2 = ~3,614 bidirectional edges.
"""
from __future__ import annotations

import csv
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

_DOWNLOAD_URL = ""  # No public download URL - Statistics Canada distribution only
_DEFAULT_PATH = "data/cip2016_iscedf.csv"

CHUNK = 500


def _match_type(isced_raw: str) -> str:
    """Return match type based on asterisk suffix in ISCED code.

    '*' suffix means the ISCED category only partially covers the CIP program.
    """
    if isced_raw.endswith("*"):
        return "partial"
    return "exact"


async def ingest_crosswalk_cip_iscedf(conn, path: Optional[str] = None) -> int:
    """Insert bidirectional CIP 2020 <-> ISCED-F 2013 equivalence edges.

    Reads Statistics Canada CIP 2016 / ISCED-F 2013 concordance CSV.
    CIP codes filtered to those in cip_2020 DB.
    ISCED codes filtered to those in iscedf_2013 DB.
    Asterisk suffix stripped from ISCED codes before insertion.

    Returns total edges inserted (bidirectional, so 2x unique pairs).
    """
    local = path or _DEFAULT_PATH

    if _DOWNLOAD_URL:
        ensure_data_file(_DOWNLOAD_URL, local)

    # Load CIP 2020 codes present in DB for filtering
    cip_codes = {
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = 'cip_2020'"
        )
    }

    # Load ISCED-F 2013 codes present in DB for filtering
    iscedf_codes = {
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = 'iscedf_2013'"
        )
    }

    rows: list[tuple[str, str, str, str, str]] = []

    with open(local, newline="", encoding="latin-1") as fh:
        reader = csv.DictReader(fh)
        for record in reader:
            cip_code = record["CIP Canada 2016 Code"].strip()
            isced_raw = record["ISCED-F 2013 Code"].strip()

            if not cip_code or not isced_raw:
                continue

            isced_code = isced_raw.rstrip("*")
            match = _match_type(isced_raw)

            if cip_code not in cip_codes:
                continue
            if isced_code not in iscedf_codes:
                continue

            rows.append(("cip_2020", cip_code, "iscedf_2013", isced_code, match))
            rows.append(("iscedf_2013", isced_code, "cip_2020", cip_code, match))

    count = 0
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO equivalence
                   (source_system, source_code, target_system, target_code, match_type)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING""",
            chunk,
        )
        count += len(chunk)

    return count
