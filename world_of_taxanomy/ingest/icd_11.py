"""ICD-11 MMS (Mortality and Morbidity Statistics) ingester.

Two ingestion modes:

1. CSV mode (ingest_icd_11): requires manual download from WHO API
   - Register at https://icd.who.int/icdapi (free account)
   - Download ICD-11 MMS linearization -> save as data/icd_11.csv
   - Columns: Code, Title, ParentCode
   - ~35,000-55,000 codes depending on release

2. Parquet mode (ingest_icd_11_from_parquet): uses on-disk synonyms file
   - data/icd11_synonyms.parquet (14,202 unique codes + 21 chapter nodes)
   - Source: Hugging Face dataset (public domain aggregation)
   - 3-level hierarchy: Chapter -> Base code (no dot) -> Sub-code (with dot)
   - No download required

License: CC BY-ND 3.0 IGO
  Attribution: World Health Organization
  No derivatives permitted.
"""
from __future__ import annotations

import csv
from typing import Optional

_DEFAULT_PATH = "data/icd_11.csv"

CHUNK = 500

_SYSTEM_ROW = (
    "icd_11",
    "ICD-11 MMS",
    "International Classification of Diseases 11th Revision - Mortality and Morbidity Statistics",
    "2024-01",
    "Global",
    "World Health Organization",
)


def _parse_level(depth: int) -> int:
    """Convert tree depth (0=root) to 1-indexed level.

    depth 0 -> level 1 (chapter)
    depth 1 -> level 2
    ...
    """
    return depth + 1


def _parse_sector(code: str, parent_map: dict[str, Optional[str]]) -> str:
    """Return the root ancestor code (chapter) for any node.

    Walks the parent_map chain until a node with no parent is found.
    Returns code itself if it has no parent (is a chapter).
    """
    current = code
    visited: set[str] = set()
    while True:
        parent = parent_map.get(current)
        if parent is None:
            return current
        if parent in visited:
            return current  # cycle guard
        visited.add(current)
        current = parent


async def ingest_icd_11(conn, path: Optional[str] = None) -> int:
    """Ingest ICD-11 MMS into classification_system + classification_node.

    Expects a CSV with columns: Code, Title, ParentCode
    ParentCode is empty for chapter-level (root) nodes.

    Computes level from depth in parent chain.
    Leaf detection: nodes that never appear as ParentCode.

    Returns total nodes inserted (or already present on re-run).
    """
    local = path or _DEFAULT_PATH

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    # First pass: collect all rows and build parent map
    rows_raw: list[tuple[str, str, Optional[str]]] = []  # (code, title, parent_or_None)

    with open(local, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            code = row.get("Code", "").strip()
            title = row.get("Title", "").strip()
            parent_raw = row.get("ParentCode", "").strip()
            parent = parent_raw if parent_raw else None

            if not code:
                continue

            rows_raw.append((code, title, parent))

    # Build parent map and children set
    parent_map: dict[str, Optional[str]] = {code: parent for code, _, parent in rows_raw}
    has_children: set[str] = {parent for _, _, parent in rows_raw if parent is not None}

    # Build depth map (iterative, safe for deep trees)
    depth_map: dict[str, int] = {}

    def _get_depth(code: str) -> int:
        if code in depth_map:
            return depth_map[code]
        parent = parent_map.get(code)
        if parent is None:
            depth_map[code] = 0
            return 0
        d = _get_depth(parent) + 1
        depth_map[code] = d
        return d

    # Pre-compute depths with iterative approach to avoid recursion limit
    for code, _, _ in rows_raw:
        if code not in depth_map:
            # Walk chain iteratively
            chain = []
            current = code
            while current is not None and current not in depth_map:
                chain.append(current)
                current = parent_map.get(current)
            base_depth = depth_map.get(current, 0) if current is not None else 0
            for i, c in enumerate(reversed(chain)):
                depth_map[c] = base_depth + i + (1 if current is not None else 0)
            # Fix: if current is None, chain[0] is a root, depth=0
            if current is None and chain:
                # chain[-1] (last appended) is the root
                root_idx = len(chain) - 1
                for i, c in enumerate(reversed(chain)):
                    depth_map[c] = i

    records = []
    for code, title, parent in rows_raw:
        depth = depth_map.get(code, 0)
        level = _parse_level(depth)
        sector = _parse_sector(code, parent_map)
        is_leaf = code not in has_children

        records.append((
            "icd_11",
            code,
            title,
            level,
            parent,
            sector,
            is_leaf,
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
        "UPDATE classification_system SET node_count = $1 WHERE id = 'icd_11'",
        count,
    )

    return count


# ---------------------------------------------------------------------------
# Parquet-based ingestion (uses data/icd11_synonyms.parquet - no download needed)
# ---------------------------------------------------------------------------

_PARQUET_DEFAULT = "data/icd11_synonyms.parquet"

# Ordered chapter list derived from the synonyms dataset (21 chapters)
_CHAPTER_ORDER = [
    "Certain infectious or parasitic diseases",
    "Neoplasms",
    "Diseases of the blood or blood-forming organs",
    "Diseases of the immune system",
    "Endocrine, nutritional or metabolic diseases",
    "Mental, behavioural or neurodevelopmental disorders",
    "Sleep-wake disorders",
    "Diseases of the nervous system",
    "Diseases of the visual system",
    "Diseases of the ear or mastoid process",
    "Diseases of the circulatory system",
    "Diseases of the respiratory system",
    "Diseases of the digestive system",
    "Diseases of the skin",
    "Diseases of the musculoskeletal system or connective tissue",
    "Diseases of the genitourinary system",
    "Conditions related to sexual health",
    "Pregnancy, childbirth or the puerperium",
    "Certain conditions originating in the perinatal period",
    "Developmental anomalies",
    "Injury, poisoning or certain other consequences of external causes",
]

# Map chapter name -> synthetic chapter code (CH01 - CH21)
_CHAPTER_CODE: dict[str, str] = {
    ch: f"CH{i + 1:02d}" for i, ch in enumerate(_CHAPTER_ORDER)
}


def _derive_icd11_parent(code: str) -> Optional[str]:
    """Derive parent code for an ICD-11 code.

    Codes without a dot (base codes, e.g. '1A00') return None -
    their parent is the chapter node (set separately).
    Codes with a dot (e.g. '1A00.0') return the portion before the dot.
    Synthetic chapter codes ('CH01' etc.) return None.
    """
    if not code:
        return None
    if code.startswith("CH"):
        return None
    if "." in code:
        return code.split(".")[0]
    return None


def _derive_icd11_level(code: str) -> int:
    """Return hierarchy level.

    CH01-CH21 -> 1 (chapter)
    Base codes (4-char, no dot) -> 2
    Sub-codes (4-char.X) -> 3
    """
    if code.startswith("CH"):
        return 1
    if "." in code:
        return 3
    return 2


async def ingest_icd_11_from_parquet(conn, path: Optional[str] = None) -> int:
    """Ingest ICD-11 from the on-disk icd11_synonyms.parquet file.

    Hierarchy: Chapter (CH01-CH21) -> Base code (no dot) -> Sub-code (with dot)
    Total: 21 chapter nodes + 14,202 unique disease codes = ~14,223 nodes.

    Does NOT require WHO API registration - uses the parquet file already present.
    Returns total nodes ingested.
    """
    import pyarrow.parquet as pq

    local = path or _PARQUET_DEFAULT

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    # Read unique codes from parquet
    table = pq.read_table(local, columns=["icd11Code", "icd11Title", "ChapterNo"])
    codes_col = table.column("icd11Code").to_pylist()
    titles_col = table.column("icd11Title").to_pylist()
    chapters_col = table.column("ChapterNo").to_pylist()

    unique: dict[str, tuple[str, str]] = {}
    for code, title, chapter in zip(codes_col, titles_col, chapters_col):
        if code and code not in unique:
            unique[code] = (title, chapter or "")

    # Build chapter nodes first (synthetic CH01-CH21 codes)
    chapter_rows = []
    for ch_name, ch_code in _CHAPTER_CODE.items():
        chapter_rows.append((
            "icd_11",
            ch_code,
            ch_name,
            1,       # level
            None,    # parent
            ch_code, # sector_code = self
            False,   # is_leaf
        ))

    # Build disease code rows
    has_children: set[str] = set()
    for code in unique:
        if "." in code:
            has_children.add(code.split(".")[0])

    code_rows = []
    for code, (title, chapter) in unique.items():
        level = _derive_icd11_level(code)
        raw_parent = _derive_icd11_parent(code)
        # Base codes (level 2, no dot) -> parent is chapter node
        if level == 2:
            parent = _CHAPTER_CODE.get(chapter)
        else:
            parent = raw_parent
        sector = _CHAPTER_CODE.get(chapter, chapter[:4] if chapter else "?")
        is_leaf = code not in has_children and "." not in code or ("." in code and code not in has_children)
        code_rows.append((
            "icd_11",
            code,
            title,
            level,
            parent,
            sector,
            is_leaf,
        ))

    all_rows = chapter_rows + code_rows
    count = 0
    for i in range(0, len(all_rows), CHUNK):
        chunk = all_rows[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (system_id, code) DO NOTHING""",
            chunk,
        )
        count += len(chunk)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'icd_11'",
        count,
    )

    return count
