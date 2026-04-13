"""Patent CPC ingester.

Cooperative Patent Classification (CPC) - EPO / USPTO joint system.
License: open (EPO)
Reference: https://www.cooperativepatentclassification.org/

CPC hierarchy (5 levels):
  Section   (1 letter,  level 1, e.g. 'A')           9 sections
  Class     (3 chars,   level 2, e.g. 'A01')         ~650 classes
  Subclass  (4 chars,   level 3, e.g. 'A01B')        ~9,000 subclasses
  Group     (with '/00',level 4, e.g. 'A01B 1/00')   ~70,000 groups (main groups)
  Subgroup  (non-/00,   level 5, leaf, e.g. 'A01B 1/02') ~180,000 subgroups

Total: ~260,000 nodes.

Data source: bulk XML files from CPC scheme download page.
  Combined ZIP: 'data/CPCSchemeXML202601.zip' (all 800 XMLs in one archive)
  Or per-section ZIPs: https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/bulk

Codes are stored with a space between subclass and group number
(e.g. 'A01B 1/00', not 'A01B1/00') for consistent display.
"""
from __future__ import annotations

import io
import os
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional

CHUNK = 500

_SYSTEM_ROW = (
    "patent_cpc",
    "Patent CPC",
    "Cooperative Patent Classification - EPO/USPTO",
    "2026-01",
    "Global",
    "European Patent Office / USPTO",
)

# CPC sections A through H plus Y (cross-sectional)
_SECTIONS = ["A", "B", "C", "D", "E", "F", "G", "H", "Y"]

_SECTION_ZIP_URL_TEMPLATE = (
    "https://www.cooperativepatentclassification.org"
    "/cpcSchemeAndDefinitions/bulk/cpc-scheme-{section}.zip"
)

_DEFAULT_DATA_DIR = "data/cpc"
_COMBINED_ZIP_PATH = "data/CPCSchemeXML202601.zip"

# Regex to insert space between subclass (4-char) and group number
_CPC_SPACE_RE = re.compile(r"^([A-Z][0-9]{2}[A-Z])([0-9]+/.+)$")


def _normalize_cpc_code(code: str) -> str:
    """Add space between subclass and group number if missing.

    'A01B1/00' -> 'A01B 1/00'
    'A01B 1/00' -> 'A01B 1/00' (already normalized)
    'A01B' -> 'A01B' (no change for subclass/class/section)
    """
    if "/" not in code or " " in code:
        return code
    m = _CPC_SPACE_RE.match(code)
    if m:
        return m.group(1) + " " + m.group(2)
    return code


def _determine_level(code: str) -> int:
    """Return CPC hierarchy level from code structure.

    Rules:
      Level 1: single letter (section, e.g. 'A')
      Level 2: 3 chars, no space (class, e.g. 'A01')
      Level 3: 4 chars, no space (subclass, e.g. 'A01B')
      Level 4: contains space + '/', suffix after '/' == '00' (main group)
      Level 5: contains space + '/', suffix after '/' != '00' (subgroup)
    """
    if " " not in code:
        length = len(code)
        if length == 1:
            return 1
        if length == 3:
            return 2
        if length == 4:
            return 3
        return 3

    # Has space - it's a group or subgroup
    if "/" not in code:
        return 4

    after_slash = code.split("/", 1)[1]
    if after_slash == "00":
        return 4  # main group
    return 5  # subgroup (leaf)


def _determine_parent(code: str) -> Optional[str]:
    """Return parent code for a CPC node.

    Section (level 1): no parent
    Class (level 2): parent = first letter (section)
    Subclass (level 3): parent = first 3 chars (class)
    Main group (level 4): parent = first 4 chars (subclass)
    Subgroup (level 5): parent = same prefix + '/00' (main group)
    """
    if " " not in code:
        if len(code) <= 1:
            return None
        if len(code) == 3:
            return code[0]
        if len(code) == 4:
            return code[:3]
        return code[:4]

    # Group or subgroup: 'A01B 1/02' -> parts = ['A01B 1', '02']
    parts = code.split("/", 1)
    after_slash = parts[1]
    if after_slash == "00":
        # Main group: parent is subclass ('A01B 1/00' -> 'A01B')
        return code.split(" ")[0]
    # Subgroup: parent is the main group (replace suffix with '00')
    return parts[0] + "/00"


def _determine_sector(code: str) -> str:
    """Return CPC section (first letter) as sector code."""
    return code[0]


def _parse_cpc_xml_data(data: bytes) -> list[tuple[str, str]]:
    """Parse CPC scheme XML bytes and return deduplicated list of (code, title) tuples.

    Handles two XML formats:
      - New format: classification-symbol as child element (CPCSchemeXML202601.zip)
      - Old format: classification-symbol as attribute (legacy per-section ZIPs)

    Normalizes codes to space format: 'A01B1/00' -> 'A01B 1/00'.
    """
    nodes: list[tuple[str, str]] = []
    seen_codes: set[str] = set()

    root = ET.fromstring(data)

    # Strip namespaces
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    for item in root.iter("classification-item"):
        # Try child element first (new format), then attribute (old format)
        sym_elem = item.find("classification-symbol")
        if sym_elem is not None and sym_elem.text:
            raw_code = sym_elem.text.strip()
        else:
            raw_code = item.get("classification-symbol", "").strip()

        if not raw_code:
            continue

        code = _normalize_cpc_code(raw_code)
        if code in seen_codes:
            continue

        # Extract title
        title = ""
        for title_elem in item.iter("class-title"):
            for text_part in title_elem.iter("title-part"):
                parts = []
                for child in text_part:
                    if child.text:
                        parts.append(child.text.strip())
                if not parts:
                    # Fall back to itertext
                    text = " ".join(text_part.itertext()).strip()
                    if text:
                        title = text
                        break
                else:
                    title = " ".join(parts)
                    break
            if title:
                break

        if not title:
            for title_elem in item.iter("class-title"):
                text = " ".join(title_elem.itertext()).strip()
                if text:
                    title = text
                    break

        if code and title:
            seen_codes.add(code)
            nodes.append((code, title))

    return nodes


def _parse_cpc_xml(xml_path: str) -> list[tuple[str, str]]:
    """Parse CPC scheme XML file and return list of (code, title) tuples."""
    with open(xml_path, "rb") as f:
        return _parse_cpc_xml_data(f.read())


def _ingest_from_combined_zip(zip_path: str) -> list[tuple[str, str]]:
    """Parse all CPC XML files from the combined ZIP archive.

    Returns deduplicated (code, title) pairs from all 800 XML files.
    """
    all_nodes: dict[str, str] = {}

    with zipfile.ZipFile(zip_path) as zf:
        xml_members = [m for m in zf.namelist() if m.endswith(".xml")]
        for member in xml_members:
            with zf.open(member) as f:
                data = f.read()
            pairs = _parse_cpc_xml_data(data)
            for code, title in pairs:
                if code not in all_nodes:
                    all_nodes[code] = title

    return list(all_nodes.items())


def _download_section_zip(section: str, data_dir: str) -> Optional[str]:
    """Download CPC section ZIP and extract XML, return path to XML file."""
    xml_path = os.path.join(data_dir, f"cpc-scheme-{section}.xml")
    if os.path.exists(xml_path):
        return xml_path

    url = _SECTION_ZIP_URL_TEMPLATE.format(section=section)
    print(f"  Downloading CPC section {section}: {url}")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WorldOfTaxanomy/0.1"})
        with urllib.request.urlopen(req, context=ctx, timeout=120) as response:
            zip_bytes = response.read()
    except Exception as exc:
        print(f"  WARNING: Could not download section {section}: {exc}")
        return None

    Path(data_dir).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        xml_members = [m for m in zf.namelist() if m.endswith(".xml")]
        if not xml_members:
            print(f"  WARNING: No XML file found in section {section} ZIP")
            return None
        xml_data = zf.read(xml_members[0])
        Path(xml_path).write_bytes(xml_data)
        size_kb = len(xml_data) / 1024
        print(f"  Extracted {xml_members[0]}: {size_kb:.1f} KB")

    return xml_path


async def ingest_patent_cpc(conn, data_dir: Optional[str] = None) -> int:
    """Ingest CPC patent classification hierarchy from EPO bulk XML.

    Auto-detects source in priority order:
      1. Combined ZIP at 'data/CPCSchemeXML202601.zip' (all sections, user-provided)
      2. Extracted XMLs in data_dir (or 'data/cpc/')
      3. Downloads per-section ZIPs from EPO (may fail due to URL changes)

    WARNING: Ingesting ~260K CPC codes takes several minutes.

    Returns total node count inserted.
    """
    print("  Loading ~260K CPC codes - this will take several minutes.")

    # Register system
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    # Determine source
    if Path(_COMBINED_ZIP_PATH).exists():
        print(f"  Reading from {_COMBINED_ZIP_PATH} ...")
        raw_nodes = _ingest_from_combined_zip(_COMBINED_ZIP_PATH)
        print(f"  Parsed {len(raw_nodes)} unique codes")
    else:
        # Per-section fallback
        local_dir = data_dir or _DEFAULT_DATA_DIR
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        raw_nodes = []
        seen: set[str] = set()
        for section in _SECTIONS:
            xml_path = _download_section_zip(section, local_dir)
            if not xml_path or not os.path.exists(xml_path):
                print(f"  Skipping section {section} (not available)")
                continue
            print(f"  Parsing section {section}...")
            for code, title in _parse_cpc_xml(xml_path):
                if code not in seen:
                    seen.add(code)
                    raw_nodes.append((code, title))

    if not raw_nodes:
        return 0

    # Determine parent codes for leaf detection
    all_codes = {code for code, _ in raw_nodes}
    parent_codes: set[str] = set()
    for code, _ in raw_nodes:
        parent = _determine_parent(code)
        if parent:
            parent_codes.add(parent)

    records = []
    for code, title in raw_nodes:
        records.append((
            "patent_cpc",
            code,
            title,
            _determine_level(code),
            _determine_parent(code),
            _determine_sector(code),
            code not in parent_codes,
        ))

    total_count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (system_id, code) DO NOTHING""",
            chunk,
        )
        total_count += len(chunk)
        if total_count % 50000 == 0:
            print(f"  Inserted {total_count} nodes...")

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'patent_cpc'",
        total_count,
    )

    return total_count
