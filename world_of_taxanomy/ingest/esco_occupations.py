"""ESCO Occupations ingester.

European Skills, Competences, Qualifications and Occupations (ESCO).
Published by the European Commission.
License: CC BY 4.0
Reference: https://esco.ec.europa.eu/en/use-esco/download

ESCO occupations are stored as a flat classification system:
  ~2,942 occupation nodes (v1.1.1) / ~3,000+ nodes (v1.2.0+)
  All nodes are level=1, parent_code=None, is_leaf=True.
  sector_code = first digit of the associated ISCO-08 group code.

The relationship between ESCO occupations and ISCO-08 unit groups is
handled separately by the crosswalk ingester (Phase 7-C).

Download: occupations_en.csv extracted from the bulk ESCO ZIP download.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file_zip

_DOWNLOAD_URL = (
    "https://ec.europa.eu/esco/portal/escopedia_api"
    "?downloadFile=true&file=ESCO+dataset+v1.1.1+-+classification+-+en+-+csv.zip"
)
_ZIP_MEMBER = "occupations_en.csv"
_DEFAULT_PATH = "data/esco_occupations_en.csv"

CHUNK = 500

_SYSTEM_ROW = (
    "esco_occupations",
    "ESCO Occupations",
    "European Skills, Competences, Qualifications and Occupations - Occupations",
    "1.1.1",
    "Europe / Global",
    "European Commission",
)

# ISCO major group labels for sector assignment
_ISCO_MAJOR_LABELS: dict[str, str] = {
    "0": "Armed Forces Occupations",
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians and Associate Professionals",
    "4": "Clerical Support Workers",
    "5": "Service and Sales Workers",
    "6": "Skilled Agricultural, Forestry and Fishery Workers",
    "7": "Craft and Related Trades Workers",
    "8": "Plant and Machine Operators and Assemblers",
    "9": "Elementary Occupations",
}


def _extract_code(concept_uri: str) -> str:
    """Extract occupation code (UUID/slug) from ESCO conceptUri.

    Example:
      'http://data.europa.eu/esco/occupation/14a21b3e-8d10-49a7-a7fb-b2e2e61ebb13'
      -> '14a21b3e-8d10-49a7-a7fb-b2e2e61ebb13'
    """
    return concept_uri.rstrip("/").split("/")[-1]


def _determine_sector(isco_code: str) -> str:
    """Return ISCO major group (first digit) as sector code.

    Returns '0' if isco_code is empty or missing.
    """
    stripped = isco_code.strip() if isco_code else ""
    if not stripped:
        return "0"
    return stripped[0]


async def ingest_esco_occupations(conn, path: Optional[str] = None) -> int:
    """Ingest ESCO Occupations from bulk CSV download.

    Downloads occupations_en.csv from the ESCO bulk ZIP export (v1.1.1).
    Stores ~2,942 occupations as a flat system (all level=1, no parent).

    Returns count of nodes inserted (or already present on re-run).
    """
    local = path or _DEFAULT_PATH
    ensure_data_file_zip(_DOWNLOAD_URL, local, _ZIP_MEMBER)

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
        reader = csv.DictReader(fh)
        for row in reader:
            concept_uri = row.get("conceptUri", "").strip()
            if not concept_uri:
                continue

            # Skip ISCO group rows (some exports bundle them)
            in_scheme = row.get("inScheme", "")
            if "iscoGroup" in in_scheme:
                continue

            code = _extract_code(concept_uri)
            if not code or code in seen_codes:
                continue

            title = row.get("preferredLabel", "").strip()
            if not title:
                continue

            isco_code = row.get("code", "").strip()
            sector = _determine_sector(isco_code)

            seen_codes.add(code)
            records.append((
                "esco_occupations",
                code,
                title,
                1,       # level: flat
                None,    # parent_code: crosswalk handles ISCO relationship
                sector,  # sector_code: first digit of ISCO group
                True,    # is_leaf: all occupations are leaves
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
        "UPDATE classification_system SET node_count = $1 "
        "WHERE id = 'esco_occupations'",
        count,
    )

    return count
