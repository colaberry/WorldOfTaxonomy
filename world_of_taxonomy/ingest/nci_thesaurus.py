"""NCI Thesaurus full ingester (211K concepts from NCI EVS flat file).

National Cancer Institute Thesaurus - a comprehensive biomedical vocabulary
covering cancer biology, clinical trials, drugs, anatomy, genes, diseases,
and more. One of the largest open biomedical ontologies.

Source: NCI Enterprise Vocabulary Services (public, CC BY 4.0)
URL: https://evs.nci.nih.gov/evs-download/thesaurus-downloads
Data file: data/nci_thesaurus.zip containing Thesaurus.txt

Format: tab-delimited flat file (no header row). Columns:
  0: concept code (e.g. C100000)
  1: concept URL
  2: parent code(s) (pipe-delimited if multiple)
  3: synonyms (pipe-delimited, first = display name)
  4: definition
  5: (unused)
  6: (unused)
  7: semantic type
  8: subset membership

Hierarchy: derived from parent column. Multi-parent concepts use first
parent only (polyhierarchy flattened to tree). Levels computed via BFS
from root concepts (concepts with no parent).

Overlap check: NCI Thesaurus covers cancer/biomedical vocabulary with
NCI-specific concept codes (C######). Different from MeSH (literature
indexing), ICD (diagnosis codes), and LOINC (lab tests). No duplication.

Verified 2025-04-15: 211,072 concepts, 19 roots, max depth 22.
"""
from __future__ import annotations

import zipfile
from collections import deque
from pathlib import Path
from typing import Optional

from world_of_taxonomy.ingest.hash_util import sha256_of_file

CHUNK = 500

_SYSTEM_ROW = (
    "nci_thesaurus",
    "NCI Thesaurus",
    "NCI Thesaurus (NCI/NIH)",
    "26.03e",
    "Global",
    "National Cancer Institute (NCI/NIH)",
)

_SOURCE_URL = "https://evs.nci.nih.gov/evs-download/thesaurus-downloads"
_DATA_PROVENANCE = "official_download"
_LICENSE = "CC BY 4.0"

_DEFAULT_ZIP = "data/nci_thesaurus.zip"
_EXPECTED_MIN = 180_000


def _find_data_file() -> Optional[str]:
    """Auto-detect the NCI Thesaurus data file."""
    p = Path(_DEFAULT_ZIP)
    if p.exists():
        return str(p)
    zips = sorted(Path("data").glob("*thesaurus*.zip"), key=lambda x: x.name.lower())
    for z in reversed(zips):
        if "nci" in z.name.lower() or "thesaurus" in z.name.lower():
            return str(z)
    return None


def parse_nci_thesaurus(path: str) -> list[tuple[str, str, int, Optional[str]]]:
    """Parse NCI Thesaurus flat file into (code, title, level, parent_code) tuples.

    Reads the tab-delimited file, builds the parent-child graph, computes
    levels via BFS from root concepts.
    """
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            txt_files = [f for f in z.namelist() if f.endswith(".txt")]
            if not txt_files:
                raise FileNotFoundError(f"No .txt file found in {path}")
            # Prefer Thesaurus.txt
            target = "Thesaurus.txt"
            if target not in txt_files:
                target = txt_files[0]
            raw = z.read(target).decode("utf-8", errors="replace")
    else:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")

    lines = raw.splitlines()

    # Phase 1: collect concepts
    name_map: dict[str, str] = {}      # code -> display name
    parent_map: dict[str, str] = {}    # code -> first parent code
    children_map: dict[str, list[str]] = {}  # parent -> [children]

    for line in lines:
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        code = cols[0].strip()
        if not code:
            continue

        parents_str = cols[2].strip()
        syns = cols[3].strip()
        # First synonym is the display name
        name = syns.split("|")[0] if syns else code
        # Replace em-dashes with hyphens
        name = name.replace("\u2014", "-")

        name_map[code] = name

        if parents_str:
            first_parent = parents_str.split("|")[0].strip()
            parent_map[code] = first_parent
            children_map.setdefault(first_parent, []).append(code)

    # Phase 2: compute levels via BFS from roots
    roots = [c for c in name_map if c not in parent_map]
    levels: dict[str, int] = {}
    q: deque[str] = deque()
    for r in roots:
        levels[r] = 1
        q.append(r)

    while q:
        node = q.popleft()
        lev = levels[node]
        for child in children_map.get(node, []):
            if child not in levels:
                levels[child] = lev + 1
                q.append(child)

    # Phase 3: build node list
    nodes: list[tuple[str, str, int, Optional[str]]] = []

    for code in sorted(name_map):
        level = levels.get(code, 1)
        parent = parent_map.get(code)
        nodes.append((code, name_map[code], level, parent))

    return nodes


async def ingest_nci_thesaurus(conn, path: Optional[str] = None) -> int:
    """Ingest full NCI Thesaurus from EVS flat file.

    Parses the flat file, computes hierarchy via BFS,
    and batch-inserts ~211K nodes.

    Returns total node count.
    """
    local = path or _find_data_file()
    if local is None:
        raise FileNotFoundError(
            "NCI Thesaurus data not found. Download from "
            "https://evs.nci.nih.gov/evs-download/thesaurus-downloads "
            "and place the ZIP at data/nci_thesaurus.zip"
        )

    nodes = parse_nci_thesaurus(local)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} NCI Thesaurus nodes, expected >= {_EXPECTED_MIN}. "
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
        if count % 50_000 == 0:
            print(f"  nci_thesaurus: {count:,} nodes inserted...")

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )
    return count
