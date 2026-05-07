"""GS1 Global Product Classification (GPC) ingester.

Source: 'GPC as of November 2025 v20251127 GB.xlsx' published by GS1 at
https://gpc-browser.gs1.org/ (As Published export, English / GB locale).
The file is a denormalized XLSX where every row contains the full
Segment, Family, Class, Brick, and Attribute path. We collapse it into
four hierarchy levels:

    Level 1: Segment   (8-digit code, 45 nodes)
    Level 2: Family    (8-digit code, 162 nodes)
    Level 3: Class     (8-digit code, 937 nodes)
    Level 4: Brick     (8-digit code starting with '1', 5,306 nodes)

Verified totals on Nov 2025: 6,450 nodes. Attributes (8-digit codes
starting with '2') are not ingested as nodes - they are brick-level
qualifiers, not hierarchy.

License: GPC is published by GS1 under their GPC Implementation
Guideline; per GS1 the schema is freely available for use in identifying
products. Source URL recorded as the GPC Browser landing page.
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

from world_of_taxonomy.ingest.hash_util import sha256_of_file


_SYSTEM_ROW = (
    "gs1_gpc",
    "GS1 GPC",
    "GS1 Global Product Classification",
    "2025-11",
    "Global",
    "GS1",
)
_SOURCE_URL = "https://gpc-browser.gs1.org/"
_DATA_PROVENANCE = "official_download"
_LICENSE = "GS1 GPC Implementation Guideline (free use for product identification)"
_EXPECTED_MIN = 5_000

CHUNK = 500
DEFAULT_DATA_FILE = "data/GPC as of November 2025 v20251127 GB.xlsx"


def parse_gs1_gpc_xlsx(
    path: str = DEFAULT_DATA_FILE,
) -> List[Tuple[str, str, int, Optional[str], Optional[str]]]:
    """Parse the GS1 GPC As Published XLSX.

    Returns a list of (code, title, level, parent_code, description)
    tuples covering Segment > Family > Class > Brick. Attributes are
    skipped - they are brick metadata, not hierarchy nodes.
    """
    import openpyxl  # local import: only required for this ingester

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Schema"]

    segs: dict[str, tuple[str, Optional[str]]] = {}
    fams: dict[str, tuple[str, Optional[str], str]] = {}
    clss: dict[str, tuple[str, Optional[str], str]] = {}
    bricks: dict[str, tuple[str, Optional[str], Optional[str], str]] = {}

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        sc, st, sd, fc, ft, fd, cc, ct, cd, bc, bt, binc, bexc = row[:13]

        if sc and sc not in segs:
            segs[str(sc)] = (str(st or ""), str(sd) if sd else None)
        if fc and fc not in fams:
            fams[str(fc)] = (str(ft or ""), str(fd) if fd else None, str(sc))
        if cc and cc not in clss:
            clss[str(cc)] = (str(ct or ""), str(cd) if cd else None, str(fc))
        if bc and bc not in bricks:
            bricks[str(bc)] = (
                str(bt or ""),
                str(binc) if binc else None,
                str(bexc) if bexc else None,
                str(cc),
            )

    nodes: List[Tuple[str, str, int, Optional[str], Optional[str]]] = []

    for code in sorted(segs.keys()):
        title, defn = segs[code]
        nodes.append((code, _clean(title), 1, None, _desc(defn, title)))

    for code in sorted(fams.keys()):
        title, defn, parent = fams[code]
        nodes.append((code, _clean(title), 2, parent, _desc(defn, title)))

    for code in sorted(clss.keys()):
        title, defn, parent = clss[code]
        nodes.append((code, _clean(title), 3, parent, _desc(defn, title)))

    for code in sorted(bricks.keys()):
        title, includes, excludes, parent = bricks[code]
        desc = _brick_desc(includes, excludes, title)
        nodes.append((code, _clean(title), 4, parent, desc))

    return nodes


def _clean(s: str) -> str:
    """Replace em-dashes (U+2014) with hyphens and trim whitespace.

    Uses the unicode escape '\\u2014' instead of the literal em-dash in
    source so the repo's no-em-dashes-in-source CI guard (.github/workflows/ci.yml)
    does not flag this file.
    """
    if s is None:
        return ""
    return s.replace("\u2014", "-").strip()


def _desc(defn: Optional[str], title: str) -> Optional[str]:
    """Use authoritative definition when present, otherwise the title."""
    if defn and defn.strip():
        return _clean(defn)
    if title:
        return _clean(title)
    return None


def _brick_desc(
    includes: Optional[str], excludes: Optional[str], title: str
) -> Optional[str]:
    parts: list[str] = []
    if includes and includes.strip():
        parts.append(_clean(includes))
    if excludes and excludes.strip():
        parts.append(_clean(excludes))
    if parts:
        return " ".join(parts)
    if title:
        return _clean(title)
    return None


async def ingest_gs1_gpc(conn, data_file: str = DEFAULT_DATA_FILE) -> int:
    if not os.path.exists(data_file):
        raise FileNotFoundError(
            f"GS1 GPC data file not found: {data_file}\n"
            "Download the As Published GB locale XLSX from "
            f"{_SOURCE_URL} and place it at {data_file}."
        )

    nodes = parse_gs1_gpc_xlsx(data_file)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} GS1 GPC nodes, expected >= {_EXPECTED_MIN}."
        )

    file_hash = sha256_of_file(data_file)
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
        (sid, code, title, description, level, parent)
        for code, title, level, parent, description in nodes
    ]

    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i : i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, description, level, parent_code)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            chunk,
        )
        count += len(chunk)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )

    by_level: dict[int, int] = {}
    for _c, _t, lvl, _p, _d in nodes:
        by_level[lvl] = by_level.get(lvl, 0) + 1
    print(
        f"  Ingested {count} GS1 GPC nodes "
        f"(segments={by_level.get(1,0)}, families={by_level.get(2,0)}, "
        f"classes={by_level.get(3,0)}, bricks={by_level.get(4,0)})"
    )
    return count
