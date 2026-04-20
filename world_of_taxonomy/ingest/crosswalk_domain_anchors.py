"""Sector-anchor bridge ingester.

Reads a mapping of domain_* system ids to NAICS anchor codes and emits
equivalence edges connecting each NAICS anchor to every level=1 code in
the domain taxonomy, plus the reverse edge for bidirectional traversal.

All generated edges:
    match_type = 'broad'
    notes      = 'derived:sector_anchor:v1'

This replicates the existing pilot (crosswalk_naics484_domains.py) at scale
by generating the (naics_code, domain_system, domain_root_code) tuples
programmatically from a single JSON mapping instead of hand-crafting one
module per domain.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

PROVENANCE = "derived:sector_anchor:v1"
ANCHORS_PATH = Path(__file__).parent / "domain_anchors.json"


def load_domain_anchors(path: Optional[Path] = None) -> dict:
    p = path or ANCHORS_PATH
    with open(p) as fh:
        return json.load(fh)


async def ingest_crosswalk_domain_anchors(conn, anchors: Optional[dict] = None) -> int:
    """Emit sector-anchor bridges for every domain_* in the anchor map.

    Returns number of edges inserted (deduped).
    """
    if anchors is None:
        anchors = load_domain_anchors()

    naics_codes = {
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = 'naics_2022'"
        )
    }
    if not naics_codes:
        return 0

    rows: list[tuple[str, str, str, str, str, str]] = []
    for domain_id, entry in anchors.items():
        domain_roots = [
            r["code"]
            for r in await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id = $1 AND level = 1",
                domain_id,
            )
        ]
        if not domain_roots:
            continue
        for naics_code in entry.get("naics", []):
            if naics_code not in naics_codes:
                continue
            for root_code in domain_roots:
                rows.append(
                    ("naics_2022", naics_code, domain_id, root_code, "broad", PROVENANCE)
                )
                rows.append(
                    (domain_id, root_code, "naics_2022", naics_code, "broad", PROVENANCE)
                )

    rows = list(set(rows))
    if not rows:
        return 0

    await conn.executemany(
        """INSERT INTO equivalence
               (source_system, source_code, target_system, target_code, match_type, notes)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING""",
        rows,
    )

    return len(rows)
