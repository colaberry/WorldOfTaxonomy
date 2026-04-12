"""ESCO Skills ingester.

European Skills, Competences, Qualifications and Occupations (ESCO) - Skills.
Published by the European Commission.
License: CC BY 4.0
Reference: https://esco.ec.europa.eu/en/use-esco/download

ESCO skills include three sub-types:
  - skill/competence (transversal skills, language skills, etc.)
  - knowledge
  - attitude and value

All skill types are stored as a flat classification system:
  ~13,890 skill nodes (v1.1.1)
  All nodes are level=1, parent_code=None, is_leaf=True.
  sector_code = single letter abbreviating skill type:
    'S' for skill/competence, 'K' for knowledge, 'A' for attitude, '?' otherwise.

Download: skills_en.csv extracted from the bulk ESCO ZIP download.
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
_ZIP_MEMBER = "skills_en.csv"
_DEFAULT_PATH = "data/esco_skills_en.csv"

CHUNK = 500

_SYSTEM_ROW = (
    "esco_skills",
    "ESCO Skills",
    "European Skills, Competences, Qualifications and Occupations - Skills",
    "1.1.1",
    "Europe / Global",
    "European Commission",
)


def _extract_skill_code(concept_uri: str) -> str:
    """Extract skill code (UUID/slug) from ESCO conceptUri.

    Example:
      'http://data.europa.eu/esco/skill/b16c778c-6b4d-4c6e-a73f-9e1cf2ba1c3a'
      -> 'b16c778c-6b4d-4c6e-a73f-9e1cf2ba1c3a'
    """
    return concept_uri.rstrip("/").split("/")[-1]


def _determine_skill_sector(skill_type: str) -> str:
    """Map ESCO skillType to a single-letter sector code.

    'S' = skill/competence
    'K' = knowledge
    'A' = attitude or value
    '?' = unknown/empty
    """
    normalized = skill_type.lower().strip() if skill_type else ""
    if not normalized:
        return "?"
    if "knowledge" in normalized:
        return "K"
    if "attitude" in normalized:
        return "A"
    if "skill" in normalized or "competence" in normalized:
        return "S"
    return "?"


async def ingest_esco_skills(conn, path: Optional[str] = None) -> int:
    """Ingest ESCO Skills from bulk CSV download.

    Downloads skills_en.csv from the ESCO bulk ZIP export (v1.1.1).
    Stores ~13,890 skills as a flat system (all level=1, no parent).

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

            # Skip non-skill rows (e.g. skill group/pillar rows)
            in_scheme = row.get("inScheme", "")
            if "skillsCollection" in in_scheme or "iscoGroup" in in_scheme:
                continue

            code = _extract_skill_code(concept_uri)
            if not code or code in seen_codes:
                continue

            title = row.get("preferredLabel", "").strip()
            if not title:
                continue

            skill_type = row.get("skillType", "").strip()
            sector = _determine_skill_sector(skill_type)

            seen_codes.add(code)
            records.append((
                "esco_skills",
                code,
                title,
                1,       # level: flat
                None,    # parent_code: none
                sector,  # sector_code: S/K/A/?
                True,    # is_leaf: all skills are leaves
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
        "WHERE id = 'esco_skills'",
        count,
    )

    return count
