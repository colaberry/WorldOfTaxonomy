"""MeSH full ingester (31,110 descriptors from NLM XML).

Medical Subject Headings controlled vocabulary thesaurus published by the
National Library of Medicine (NLM). Used to index biomedical literature
in MEDLINE/PubMed.

Source: US National Library of Medicine (NLM) - public domain
URL: https://www.nlm.nih.gov/databases/download/mesh.html
Data file: data/desc2026.xml (or desc2026.gz)

Format: XML with <DescriptorRecord> elements. Each record has:
  - <DescriptorUI>  e.g. D000001
  - <DescriptorName><String>  e.g. Calcimycin
  - <TreeNumberList><TreeNumber>  e.g. D02.355.291.933.125

Hierarchy derived from tree numbers:
  Category letter (A-Z)     -> level 1, parent = None (16 categories)
  Tree depth 1 (e.g. A01)   -> level 2, parent = category letter
  Tree depth 2 (A01.456)    -> level 3, parent = descriptor owning A01
  Tree depth N               -> level N+1, parent = descriptor owning parent tree

Multi-tree descriptors: MeSH descriptors can have multiple tree numbers
(polyhierarchy). We use the FIRST tree number for level/parent assignment.
The descriptor still appears once with its DescriptorUI as the code.

Overlap check: MeSH is a biomedical subject vocabulary for literature indexing.
Different from ICD (diagnosis codes), NCI Thesaurus (cancer ontology),
and LOINC (lab test codes). No duplication.

Verified 2025-04-15: 31,110 descriptors (31,108 with tree numbers).
"""
from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from world_of_taxonomy.ingest.hash_util import sha256_of_file

CHUNK = 500

_SYSTEM_ROW = (
    "mesh",
    "MeSH",
    "Medical Subject Headings (NLM)",
    "2026",
    "Global",
    "US National Library of Medicine (NLM)",
)

_SOURCE_URL = "https://www.nlm.nih.gov/databases/download/mesh.html"
_DATA_PROVENANCE = "official_download"
_LICENSE = "Public Domain (US Government)"

_DEFAULT_XML = "data/desc2026.xml"
_DEFAULT_GZ = "data/desc2026.gz"
_EXPECTED_MIN = 28_000

# 16 top-level MeSH categories
MESH_CATEGORIES: list[tuple[str, str]] = [
    ("A", "Anatomy"),
    ("B", "Organisms"),
    ("C", "Diseases"),
    ("D", "Chemicals and Drugs"),
    ("E", "Analytical, Diagnostic and Therapeutic Techniques and Equipment"),
    ("F", "Psychiatry and Psychology"),
    ("G", "Phenomena and Processes"),
    ("H", "Disciplines and Occupations"),
    ("I", "Anthropology, Education, Sociology and Social Phenomena"),
    ("J", "Technology, Industry, Agriculture"),
    ("K", "Humanities"),
    ("L", "Information Science"),
    ("M", "Named Groups"),
    ("N", "Health Care"),
    ("V", "Publication Characteristics"),
    ("Z", "Geographicals"),
]

_CAT_CODES = {code for code, _ in MESH_CATEGORIES}


def _find_data_file() -> Optional[str]:
    """Auto-detect the MeSH descriptor data file."""
    p = Path(_DEFAULT_XML)
    if p.exists():
        return str(p)
    g = Path(_DEFAULT_GZ)
    if g.exists():
        return str(g)
    # Try any desc*.xml or desc*.gz in data/
    for pattern in ("desc*.xml", "desc*.gz"):
        matches = sorted(Path("data").glob(pattern))
        if matches:
            return str(matches[-1])
    return None


def parse_mesh_descriptors(path: str) -> list[tuple[str, str, int, Optional[str]]]:
    """Parse NLM MeSH descriptor XML into (code, title, level, parent_code) tuples.

    Returns 16 category nodes plus all descriptors with tree numbers.
    Uses iterparse for memory efficiency on the ~300MB XML file.
    """
    # Phase 1: collect all descriptors and build tree_number -> UI mapping
    descriptors: list[tuple[str, str, list[str]]] = []  # (ui, name, [tree_numbers])
    tree_to_ui: dict[str, str] = {}

    if path.endswith(".gz"):
        source = gzip.open(path, "rb")
    else:
        source = open(path, "rb")

    try:
        for event, elem in ET.iterparse(source, events=["end"]):
            if elem.tag != "DescriptorRecord":
                continue

            ui_elem = elem.find("DescriptorUI")
            name_elem = elem.find("DescriptorName/String")
            tree_elems = elem.findall(".//TreeNumber")

            if ui_elem is None or name_elem is None:
                elem.clear()
                continue

            ui = ui_elem.text
            name = name_elem.text or ""
            trees = [t.text for t in tree_elems if t.text]

            if trees:
                descriptors.append((ui, name, trees))
                for tn in trees:
                    tree_to_ui[tn] = ui

            elem.clear()
    finally:
        source.close()

    # Phase 2: build node list
    nodes: list[tuple[str, str, int, Optional[str]]] = []
    seen: set[str] = set()

    # Level 1: 16 categories
    for cat_code, cat_title in MESH_CATEGORIES:
        nodes.append((cat_code, cat_title, 1, None))
        seen.add(cat_code)

    # Level 2+: descriptors, using first tree number for hierarchy
    for ui, name, trees in descriptors:
        if ui in seen:
            continue

        first_tree = trees[0]
        depth = first_tree.count(".") + 1  # A01=1, A01.456=2, etc.
        level = depth + 1  # categories are level 1, so tree depth 1 = level 2

        if "." in first_tree:
            parent_tree = first_tree.rsplit(".", 1)[0]
            parent_code = tree_to_ui.get(parent_tree)
            # If parent tree doesn't map to a descriptor, walk up
            while parent_code is None and "." in parent_tree:
                parent_tree = parent_tree.rsplit(".", 1)[0]
                parent_code = tree_to_ui.get(parent_tree)
            # If still None, attach to category
            if parent_code is None:
                parent_code = first_tree[0] if first_tree[0] in _CAT_CODES else None
        else:
            # Top-level tree node (e.g., "A01") - parent is category letter
            parent_code = first_tree[0] if first_tree[0] in _CAT_CODES else None

        seen.add(ui)
        nodes.append((ui, name, level, parent_code))

    return nodes


async def ingest_mesh(conn, path: Optional[str] = None) -> int:
    """Ingest full MeSH from NLM descriptor XML.

    Parses the XML, builds hierarchy from tree numbers,
    and batch-inserts ~31K nodes.

    Returns total node count.
    """
    local = path or _find_data_file()
    if local is None:
        raise FileNotFoundError(
            "MeSH data not found. Download from "
            "https://www.nlm.nih.gov/databases/download/mesh.html "
            "and place desc2026.xml (or .gz) in data/"
        )

    nodes = parse_mesh_descriptors(local)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} MeSH nodes, expected >= {_EXPECTED_MIN}. "
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
            print(f"  mesh: {count:,} nodes inserted...")

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )
    return count
