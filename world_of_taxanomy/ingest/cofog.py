"""COFOG ingester.

Classification of the Functions of Government (COFOG).
Source: UN Statistics Division via GitHub datasets/cofog
  https://raw.githubusercontent.com/datasets/cofog/master/data/cofog.csv
License: open (UN Statistics Division)

Hierarchy (3 levels):
  Division  2-digit        e.g. "01"       Level 1
  Group     X.X            e.g. "01.1"     Level 2
  Class     X.X.X          e.g. "01.1.1"   Level 3 (leaf)

10 top-level divisions (01-10), ~188 codes total.
"""
from __future__ import annotations

import csv
import io
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

_URL = "https://raw.githubusercontent.com/datasets/cofog/master/data/cofog.csv"
_DEFAULT_PATH = "data/cofog.csv"

_SYSTEM_ROW = (
    "cofog",
    "COFOG",
    "Classification of the Functions of Government",
    "2011",
    "Global",
    "UN Statistics Division",
)

CHUNK = 200


def _determine_level(code: str) -> int:
    """Return level based on dot count: 0 dots=1, 1 dot=2, 2 dots=3."""
    return code.count(".") + 1


def _determine_parent(code: str) -> Optional[str]:
    """Return parent code by stripping everything after the last dot."""
    if "." not in code:
        return None
    return code.rsplit(".", 1)[0]


def _determine_sector(code: str) -> str:
    """Return the 2-digit division ancestor."""
    return code[:2]


async def ingest_cofog(conn, path: Optional[str] = None) -> int:
    """Ingest COFOG into classification_system + classification_node.

    Downloads from GitHub datasets/cofog if not cached locally.
    Returns total nodes inserted (or already present on re-run).
    """
    local = ensure_data_file(_URL, path or _DEFAULT_PATH)

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    records = []
    parent_set: set[str] = set()

    with open(local, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            code = row.get("Code", "").strip()
            title = row.get("Description_EN", "").strip()
            if not code or not title:
                continue

            level = _determine_level(code)
            parent = _determine_parent(code)
            sector = _determine_sector(code)

            if parent:
                parent_set.add(parent)

            records.append((code, title, level, parent, sector))

    # Leaf = never appears as anyone's parent
    leaf_set = {r[0] for r in records} - parent_set

    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        rows = [
            (
                "cofog",
                code,
                title,
                level,
                parent,
                sector,
                code in leaf_set,
            )
            for code, title, level, parent, sector in chunk
        ]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (system_id, code) DO NOTHING""",
            rows,
        )
        count += len(rows)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'cofog'",
        count,
    )

    return count
