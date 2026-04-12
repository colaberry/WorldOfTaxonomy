"""CPC v2.1 crosswalk ingesters.

Two crosswalks:
  1. cpc_v21 <-> isic_rev4  (CPCv21_ISIC4/cpc21-isic4.txt,   ~2,715 pairs)
  2. hs_2022 <-> cpc_v21    (CPCv21_HS2017/CPC21-HS2017.csv, ~5,843 pairs)

Match type: 'exact' when both partial flags are 0, 'partial' otherwise.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

_CPC_ISIC_URL = (
    "https://unstats.un.org/unsd/classifications/Econ/tables/CPC"
    "/CPCv21_ISIC4/cpc21-isic4.txt"
)
_CPC_HS_URL = (
    "https://unstats.un.org/unsd/classifications/Econ/tables/CPC"
    "/CPCv21_HS2017/CPC21-HS2017.csv"
)

_DEFAULT_ISIC_PATH = "data/cpc21_isic4.txt"
_DEFAULT_HS_PATH = "data/cpc21_hs2017.csv"

CHUNK = 500


def _match_type(partial_a: str, partial_b: str) -> str:
    """Return 'exact' when both partial flags are 0, 'partial' otherwise."""
    if partial_a == "0" and partial_b == "0":
        return "exact"
    return "partial"


async def ingest_crosswalk_cpc_isic(conn, path: Optional[str] = None) -> int:
    """Insert bidirectional CPC v2.1 <-> ISIC Rev 4 equivalence edges.

    Source: UN Statistics Division CPCv21_ISIC4/cpc21-isic4.txt
    Format: "CPC21code","CPC21partial","ISIC4code","ISIC4partial"

    Returns total edges inserted (bidirectional, so 2x unique pairs).
    Download: https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_ISIC4/cpc21-isic4.txt
    """
    local = path or _DEFAULT_ISIC_PATH
    ensure_data_file(_CPC_ISIC_URL, local)

    rows: list[tuple[str, str, str, str, str]] = []  # (src_sys, src, tgt_sys, tgt, match)

    with open(local, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for record in reader:
            cpc_code = record["CPC21code"].strip().strip('"')
            cpc_partial = record["CPC21partial"].strip().strip('"')
            isic_code = record["ISIC4code"].strip().strip('"')
            isic_partial = record["ISIC4partial"].strip().strip('"')

            if not cpc_code or not isic_code:
                continue

            mt = _match_type(cpc_partial, isic_partial)
            rows.append(("cpc_v21", cpc_code, "isic_rev4", isic_code, mt))
            rows.append(("isic_rev4", isic_code, "cpc_v21", cpc_code, mt))

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


async def ingest_crosswalk_cpc_hs(conn, path: Optional[str] = None) -> int:
    """Insert bidirectional HS 2022 <-> CPC v2.1 equivalence edges.

    Source: UN Statistics Division CPCv21_HS2017/CPC21-HS2017.csv
    Format: HS 2017,HS partial,CPC Ver. 2.1,CPC partial
    Note: HS codes use period notation (e.g. 0101.21) - dot is stripped.

    Returns total edges inserted (bidirectional, so 2x unique pairs).
    Download: https://unstats.un.org/unsd/classifications/Econ/tables/CPC/CPCv21_HS2017/CPC21-HS2017.csv
    """
    local = path or _DEFAULT_HS_PATH
    ensure_data_file(_CPC_HS_URL, local)

    rows: list[tuple[str, str, str, str, str]] = []

    with open(local, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for record in reader:
            hs_raw = record["HS 2017"].strip()
            hs_partial = record["HS partial"].strip()
            cpc_code = record["CPC Ver. 2.1"].strip()
            cpc_partial = record["CPC partial"].strip()

            if not hs_raw or not cpc_code:
                continue

            # Strip period from HS period notation: "0101.21" -> "010121"
            hs_code = hs_raw.replace(".", "")

            mt = _match_type(hs_partial, cpc_partial)
            rows.append(("hs_2022", hs_code, "cpc_v21", cpc_code, mt))
            rows.append(("cpc_v21", cpc_code, "hs_2022", hs_code, mt))

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
