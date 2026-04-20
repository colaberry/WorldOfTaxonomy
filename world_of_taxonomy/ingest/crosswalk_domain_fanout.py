"""ISIC / NACE fan-out ingester for sector-anchor bridges.

Once naics_2022 -> domain_* anchor edges exist (see
crosswalk_domain_anchors.py), this module joins them against the existing
naics_2022 <-> isic_rev4 / naics_2022 <-> nace_rev2 crosswalks and emits
parallel edges in both directions so European / UN users reach the same
domain taxonomies.

All generated edges:
    match_type = 'broad'
    notes      = 'derived:sector_anchor:v1:fanout'
"""
from __future__ import annotations

FANOUT_PROVENANCE = "derived:sector_anchor:v1:fanout"
BRIDGE_SYSTEMS = ("isic_rev4", "nace_rev2")

_FORWARD_SQL = """
INSERT INTO equivalence
    (source_system, source_code, target_system, target_code, match_type, notes)
SELECT DISTINCT
    e_bridge.source_system,
    e_bridge.source_code,
    e_domain.target_system,
    e_domain.target_code,
    'broad',
    $1
FROM equivalence e_domain
JOIN equivalence e_bridge
  ON e_bridge.target_system = 'naics_2022'
 AND e_bridge.target_code   = e_domain.source_code
WHERE e_domain.source_system = 'naics_2022'
  AND e_domain.target_system LIKE 'domain_%'
  AND e_bridge.source_system = ANY($2::text[])
ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING
RETURNING 1
"""

_REVERSE_SQL = """
INSERT INTO equivalence
    (source_system, source_code, target_system, target_code, match_type, notes)
SELECT DISTINCT
    e_domain.target_system,
    e_domain.target_code,
    e_bridge.source_system,
    e_bridge.source_code,
    'broad',
    $1
FROM equivalence e_domain
JOIN equivalence e_bridge
  ON e_bridge.target_system = 'naics_2022'
 AND e_bridge.target_code   = e_domain.source_code
WHERE e_domain.source_system = 'naics_2022'
  AND e_domain.target_system LIKE 'domain_%'
  AND e_bridge.source_system = ANY($2::text[])
ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING
RETURNING 1
"""


async def ingest_crosswalk_domain_fanout(conn) -> int:
    """Fan out NAICS->domain anchor edges to ISIC/NACE. Returns rows inserted."""
    bridge_list = list(BRIDGE_SYSTEMS)
    forward = await conn.fetch(_FORWARD_SQL, FANOUT_PROVENANCE, bridge_list)
    reverse = await conn.fetch(_REVERSE_SQL, FANOUT_PROVENANCE, bridge_list)
    return len(forward) + len(reverse)
