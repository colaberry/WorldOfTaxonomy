"""ICD-10-PCS full ingester (79,856 codes from CMS order file).

International Classification of Diseases, 10th Revision, Procedure Coding System.
Maintained by CMS for inpatient hospital procedure coding in US health care.

Source: CMS annual release (public domain, US government)
URL: https://www.cms.gov/medicare/coding-billing/icd-10-codes
Data file: data/icd10pcs_order_2025.zip containing icd10pcs_order_2025.txt

Format: fixed-width text (same layout as ICD-10-CM order file)
  Positions 0-4: order number (5 digits)
  Position 5: space
  Positions 6-13: code (left-aligned, space-padded to 7 chars + trailing space)
  Position 14: header flag ('0' = table header, '1' = valid code)
  Position 15: space
  Positions 16-76: short description (60 chars)
  Positions 77+: long description

Hierarchy derived from code structure:
  Section (1 char: 0-9, B-H, X)   -> level 1, parent = None
  Body System (2 chars)             -> level 2, parent = section (synthesized)
  Root Op Table (3 chars)           -> level 3, parent = 2-char prefix
  Full Code (7 chars)               -> level 4, parent = 3-char prefix

Overlap check: ICD-10-PCS covers procedures; ICD-10-CM covers diagnoses.
Entirely separate code spaces, same CMS authority. No duplication.

Verified 2025-04-15: 79,856 codes (908 3-char tables + 78,948 7-char codes).
SHA-256 of icd10pcs_order_2025.zip: (computed at ingest time)
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional

from world_of_taxonomy.ingest.hash_util import sha256_of_file

CHUNK = 500

SYSTEM_ID = "icd10_pcs"

_SYSTEM_ROW = (
    SYSTEM_ID,
    "ICD-10-PCS",
    "ICD-10 Procedure Coding System (US)",
    "FY2025",
    "United States",
    "CMS / National Center for Health Statistics",
)

_SOURCE_URL = "https://www.cms.gov/medicare/coding-billing/icd-10-codes"
_DATA_PROVENANCE = "official_download"
_LICENSE = "Public Domain (US Government)"

_DEFAULT_ZIP = "data/icd10pcs_order_2025.zip"
_EXPECTED_MIN = 75_000

# 17 top-level sections: (code, title)
ICD10PCS_SECTIONS: list[tuple[str, str]] = [
    ("0", "Medical and Surgical"),
    ("1", "Obstetrics"),
    ("2", "Placement"),
    ("3", "Administration"),
    ("4", "Measurement and Monitoring"),
    ("5", "Extracorporeal or Systemic Assistance and Performance"),
    ("6", "Extracorporeal or Systemic Therapies"),
    ("7", "Osteopathic"),
    ("8", "Other Procedures"),
    ("9", "Chiropractic"),
    ("B", "Imaging"),
    ("C", "Nuclear Medicine"),
    ("D", "Radiation Therapy"),
    ("F", "Physical Rehabilitation and Diagnostic Audiology"),
    ("G", "Mental Health"),
    ("H", "Substance Abuse Treatment"),
    ("X", "New Technology"),
]


def _find_data_file() -> Optional[str]:
    """Auto-detect the ICD-10-PCS data file."""
    p = Path(_DEFAULT_ZIP)
    if p.exists():
        return str(p)
    zips = sorted(Path("data").glob("icd10pcs_order_*.zip"))
    if zips:
        return str(zips[-1])
    return None


def parse_icd10pcs_order_file(path: str) -> list[tuple[str, str, int, Optional[str]]]:
    """Parse CMS order file into (code, title, level, parent_code) tuples.

    Returns list including 17 section nodes at level 1, synthesized body
    system nodes at level 2, 3-char root operation table nodes at level 3,
    and 7-char full codes at level 4.
    """
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            order_files = [
                f for f in z.namelist()
                if "order" in f.lower() and f.endswith(".txt")
                and "addend" not in f.lower()
            ]
            if not order_files:
                raise FileNotFoundError(f"No order file found in {path}")
            raw = z.read(order_files[0]).decode("utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")

    lines = raw.splitlines()

    # Collect all codes from the file first
    file_codes: dict[str, str] = {}  # code -> title
    for line in lines:
        if len(line) < 16:
            continue
        code = line[6:14].strip()
        if not code:
            continue
        title = line[77:].strip() if len(line) > 77 else line[16:77].strip()
        if not title:
            title = line[16:77].strip()
        if code not in file_codes:
            file_codes[code] = title

    # Build nodes list
    nodes: list[tuple[str, str, int, Optional[str]]] = []
    seen: set[str] = set()

    # Level 1: Sections
    section_set = {code for code, _ in ICD10PCS_SECTIONS}
    for sec_code, sec_title in ICD10PCS_SECTIONS:
        nodes.append((sec_code, sec_title, 1, None))
        seen.add(sec_code)

    # Level 2: Body Systems (synthesized from 2-char prefixes of 3-char codes)
    # Extract body system name from the first 3-char code's title:
    # "Body System Name, Root Operation" -> take part before last comma
    body_systems: dict[str, str] = {}
    for code in sorted(file_codes):
        if len(code) == 3:
            prefix = code[:2]
            if prefix not in body_systems:
                title = file_codes[code]
                parts = title.rsplit(", ", 1)
                body_systems[prefix] = parts[0] if len(parts) > 1 else title

    for bs_code in sorted(body_systems):
        section = bs_code[0]
        parent = section if section in section_set else None
        nodes.append((bs_code, body_systems[bs_code], 2, parent))
        seen.add(bs_code)

    # Level 3: Root Operation Tables (3-char codes from file)
    for code in sorted(file_codes):
        if len(code) == 3 and code not in seen:
            parent = code[:2] if code[:2] in seen else code[0]
            nodes.append((code, file_codes[code], 3, parent))
            seen.add(code)

    # Level 4: Full Codes (7-char codes from file)
    for code in sorted(file_codes):
        if len(code) == 7 and code not in seen:
            parent = code[:3] if code[:3] in seen else code[:2]
            nodes.append((code, file_codes[code], 4, parent))
            seen.add(code)

    return nodes


async def ingest_icd10_pcs(conn, path: Optional[str] = None) -> int:
    """Ingest full ICD-10-PCS from CMS order file.

    Parses the order file, builds hierarchy from code structure,
    and batch-inserts ~80K nodes.

    Returns total node count.
    """
    local = path or _find_data_file()
    if local is None:
        raise FileNotFoundError(
            "ICD-10-PCS data not found. Download from "
            "https://www.cms.gov/medicare/coding-billing/icd-10-codes "
            "and place the ZIP at data/icd10pcs_order_2025.zip"
        )

    nodes = parse_icd10pcs_order_file(local)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} ICD-10-PCS nodes, expected >= {_EXPECTED_MIN}. "
            "Data file may be corrupted or truncated."
        )

    file_hash = sha256_of_file(local)

    sid, short, full, ver, region, authority = _SYSTEM_ROW
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority,
                source_url, source_date, data_provenance, license,
                source_file_hash, node_count)
           VALUES ($1,$2,$3,$4,$5,$6,$7,CURRENT_DATE,$8,$9,$10,0)
           ON CONFLICT (id) DO UPDATE SET
                name=$2, full_name=$3, version=$4, region=$5, authority=$6,
                source_url=$7, source_date=CURRENT_DATE, data_provenance=$8,
                license=$9, source_file_hash=$10, node_count=0""",
        sid, short, full, ver, region, authority,
        _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, file_hash,
    )

    await conn.execute(
        "DELETE FROM classification_node WHERE system_id = $1", sid
    )

    records = [
        (sid, code, title, level, parent)
        for code, title, level, parent in nodes
    ]

    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code)
               VALUES ($1, $2, $3, $4, $5)""",
            chunk,
        )
        count += len(chunk)
        if count % 10_000 == 0:
            print(f"  icd10_pcs: {count:,} nodes inserted...")

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )
    return count
