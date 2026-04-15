"""ICD-10-CM full ingester (97,584 codes from CMS order file).

International Classification of Diseases, 10th Revision, Clinical Modification.
Maintained by CDC/CMS for morbidity coding in US health care.

Source: CMS annual release (public domain, US government)
URL: https://www.cms.gov/medicare/coding-billing/icd-10-codes
Data file: data/icd10cm_order_2025.zip containing icd10cm_order_2025.txt

Format: fixed-width text
  Positions 0-4: order number (5 digits)
  Position 5: space
  Positions 6-13: code (left-aligned, space-padded to 7 chars + trailing space)
  Position 14: header flag ('0' = category header, '1' = billable code)
  Position 15: space
  Positions 16-76: short description (60 chars)
  Positions 77+: long description

Hierarchy derived from code structure:
  Chapter (CH01-CH22)     -> level 1, parent = None
  3-char category (A00)   -> level 2, parent = chapter
  4-char (A000)           -> level 3, parent = 3-char prefix
  5-char (A0001)          -> level 4, parent = 4-char prefix
  6-char (A00012)         -> level 5, parent = 5-char prefix
  7-char (A000123)        -> level 6, parent = 6-char prefix

Overlap check: ICD-10-CM (CMS/CDC, US diagnosis codes) is different from
ICD-11 MMS (WHO, global classification). Different code systems, different
authorities, different hierarchies. No duplication.

Verified 2025-04-15: 97,584 codes (23,324 headers + 74,260 billable).
SHA-256 of icd10cm_order_2025.zip: 4f6c65f0034736d2b02fa9eb1128aab564fa673dd4d99363f8b2167af3994816
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Optional

from world_of_taxonomy.ingest.hash_util import sha256_of_file

CHUNK = 500

_SYSTEM_ROW = (
    "icd10cm",
    "ICD-10-CM",
    "International Classification of Diseases 10th Revision Clinical Modification (US)",
    "FY2025",
    "United States",
    "CDC / CMS / National Center for Health Statistics",
)

_SOURCE_URL = "https://www.cms.gov/medicare/coding-billing/icd-10-codes"
_DATA_PROVENANCE = "official_download"
_LICENSE = "Public Domain (US Government)"

_DEFAULT_ZIP = "data/icd10cm_order_2025.zip"
_EXPECTED_MIN = 90_000

# Chapter definitions: (code, title, range_low, range_high)
# Using CH prefix to avoid conflicts with ICD-10-CM neoplasm codes (C00-C96)
ICD10CM_CHAPTERS: list[tuple[str, str, str, str]] = [
    ("CH01", "Certain Infectious and Parasitic Diseases", "A00", "B99"),
    ("CH02", "Neoplasms", "C00", "D49"),
    ("CH03", "Diseases of the Blood and Blood-Forming Organs", "D50", "D89"),
    ("CH04", "Endocrine, Nutritional and Metabolic Diseases", "E00", "E89"),
    ("CH05", "Mental, Behavioral and Neurodevelopmental Disorders", "F01", "F99"),
    ("CH06", "Diseases of the Nervous System", "G00", "G99"),
    ("CH07", "Diseases of the Eye and Adnexa", "H00", "H59"),
    ("CH08", "Diseases of the Ear and Mastoid Process", "H60", "H95"),
    ("CH09", "Diseases of the Circulatory System", "I00", "I99"),
    ("CH10", "Diseases of the Respiratory System", "J00", "J99"),
    ("CH11", "Diseases of the Digestive System", "K00", "K95"),
    ("CH12", "Diseases of the Skin and Subcutaneous Tissue", "L00", "L99"),
    ("CH13", "Diseases of the Musculoskeletal System and Connective Tissue", "M00", "M99"),
    ("CH14", "Diseases of the Genitourinary System", "N00", "N99"),
    ("CH15", "Pregnancy, Childbirth and the Puerperium", "O00", "O9A"),
    ("CH16", "Certain Conditions Originating in the Perinatal Period", "P00", "P96"),
    ("CH17", "Congenital Malformations, Deformations and Chromosomal Abnormalities", "Q00", "Q99"),
    ("CH18", "Symptoms, Signs and Abnormal Clinical and Laboratory Findings", "R00", "R99"),
    ("CH19", "Injury, Poisoning and Certain Other Consequences of External Causes", "S00", "T88"),
    ("CH20", "External Causes of Morbidity", "V00", "Y99"),
    ("CH21", "Factors Influencing Health Status and Contact with Health Services", "Z00", "Z99"),
    ("CH22", "Codes for Special Purposes", "U00", "U85"),
]


def _code_to_chapter(code_3char: str) -> Optional[str]:
    """Map a 3-character ICD-10-CM code to its chapter code (CH01-CH22)."""
    for ch_code, _title, lo, hi in ICD10CM_CHAPTERS:
        if lo <= code_3char <= hi:
            return ch_code
    return None


def _find_data_file() -> Optional[str]:
    """Auto-detect the ICD-10-CM data file."""
    p = Path(_DEFAULT_ZIP)
    if p.exists():
        return str(p)
    zips = sorted(Path("data").glob("icd10cm_order_*.zip"))
    if zips:
        return str(zips[-1])
    return None


def parse_icd10cm_order_file(path: str) -> list[tuple[str, str, int, Optional[str]]]:
    """Parse CMS order file into (code, title, level, parent_code) tuples.

    Returns list including 22 chapter nodes at level 1 plus all codes from
    the order file at levels 2-6 (based on code length).
    """
    # Read lines from ZIP or plain text
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            order_files = [f for f in z.namelist() if "order" in f.lower() and f.endswith(".txt") and "addend" not in f.lower()]
            if not order_files:
                raise FileNotFoundError(f"No order file found in {path}")
            raw = z.read(order_files[0]).decode("utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")

    lines = raw.splitlines()

    # Start with chapter nodes (level 1)
    nodes: list[tuple[str, str, int, Optional[str]]] = []
    for ch_code, ch_title, _lo, _hi in ICD10CM_CHAPTERS:
        nodes.append((ch_code, ch_title, 1, None))

    seen_codes = {ch_code for ch_code, *_ in ICD10CM_CHAPTERS}

    for line in lines:
        if len(line) < 16:
            continue
        code = line[6:14].strip()
        if not code:
            continue
        # Long description starts at position 77
        title = line[77:].strip() if len(line) > 77 else line[16:77].strip()
        if not title:
            title = line[16:77].strip()

        code_len = len(code)
        if code_len == 3:
            level = 2
            parent = _code_to_chapter(code)
        elif code_len == 4:
            level = 3
            parent = code[:3]
        elif code_len == 5:
            level = 4
            parent = code[:4]
        elif code_len == 6:
            level = 5
            parent = code[:5]
        elif code_len == 7:
            level = 6
            parent = code[:6]
        else:
            continue

        # Handle ICD-10-CM X placeholder codes: e.g. E0837X1 has
        # naive parent E0837X which doesn't exist -- strip trailing X
        # to find the real parent (E0837).
        if parent and parent not in seen_codes:
            stripped = parent.rstrip("X")
            if stripped in seen_codes:
                parent = stripped

        if code not in seen_codes:
            seen_codes.add(code)
            nodes.append((code, title, level, parent))

    return nodes


async def ingest_icd10cm(conn, path: Optional[str] = None) -> int:
    """Ingest full ICD-10-CM from CMS order file.

    Parses the order file, builds hierarchy from code structure,
    and batch-inserts ~97K nodes.

    Returns total node count.
    """
    local = path or _find_data_file()
    if local is None:
        raise FileNotFoundError(
            "ICD-10-CM data not found. Download from "
            "https://www.cms.gov/medicare/coding-billing/icd-10-codes "
            "and place the ZIP at data/icd10cm_order_2025.zip"
        )

    nodes = parse_icd10cm_order_file(local)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} ICD-10-CM nodes, expected >= {_EXPECTED_MIN}. "
            "Data file may be corrupted or truncated."
        )

    # Compute file hash for audit trail
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

    # Clear existing nodes for clean reload
    await conn.execute(
        "DELETE FROM classification_node WHERE system_id = $1", sid
    )

    # Batch insert
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
            print(f"  icd10cm: {count:,} nodes inserted...")

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )
    return count
