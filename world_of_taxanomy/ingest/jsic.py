"""JSIC 2013 (Rev 13) ingester.

Japan Standard Industrial Classification, Revision 13 (2013).
Since the official data is only available as Japanese-language PDFs from
the Ministry of Internal Affairs and Communications, this ingester
provides the 20 division-level codes (A-T) with English titles and
creates ISIC Rev 4 equivalence edges at division level.

Full 4-digit industry data (approx. 1,460 codes) would require manual
compilation from the Japanese PDFs or a pre-structured CSV.

Structure:
  Division (letter A-T) = level 0  (20 codes)
  Major Group (2-digit) = level 1  (~99 codes)   -- not included in skeleton
  Group (3-digit)       = level 2  (~530 codes)   -- not included in skeleton
  Industry (4-digit)    = level 3  (~1,460 codes) -- not included in skeleton

Source: https://www.soumu.go.jp/toukei_toukatsu/index/seido/sangyo/
"""

from typing import Optional

# ── Division structure (A-T) ────────────────────────────────────

JSIC_DIVISIONS = {
    "A": "Agriculture and Forestry",
    "B": "Fisheries",
    "C": "Mining and Quarrying of Stone and Gravel",
    "D": "Construction",
    "E": "Manufacturing",
    "F": "Electricity, Gas, Heat Supply and Water",
    "G": "Information and Communications",
    "H": "Transport and Postal Activities",
    "I": "Wholesale and Retail Trade",
    "J": "Finance and Insurance",
    "K": "Real Estate and Goods Rental and Leasing",
    "L": "Scientific Research, Professional and Technical Services",
    "M": "Accommodations, Eating and Drinking Services",
    "N": "Living-Related and Personal Services and Amusement Services",
    "O": "Education, Learning Support",
    "P": "Medical, Health Care and Welfare",
    "Q": "Compound Services",
    "R": "Services, N.E.C.",
    "S": "Government (Except Elsewhere Classified)",
    "T": "Industries Unable to Classify",
}

# ── JSIC -> ISIC Rev 4 division-level mapping ──────────────────
# Maps JSIC division code -> list of (ISIC division code, match_type)
# Where a JSIC division maps to a single ISIC division, match_type is "broad"
# (since the division-level mapping is approximate; sub-divisions may differ).

JSIC_TO_ISIC_MAPPING = {
    "A": [("A", "broad")],   # Agriculture -> Agriculture, forestry and fishing
    "B": [("A", "broad")],   # Fisheries -> part of ISIC A
    "C": [("B", "broad")],   # Mining -> Mining and quarrying
    "D": [("F", "broad")],   # Construction -> Construction
    "E": [("C", "broad")],   # Manufacturing -> Manufacturing
    "F": [("D", "broad"), ("E", "broad")],  # Utilities -> Electricity + Water
    "G": [("J", "broad")],   # ICT -> Information and communication
    "H": [("H", "broad")],   # Transport -> Transportation and storage
    "I": [("G", "broad")],   # Trade -> Wholesale and retail trade
    "J": [("K", "broad")],   # Finance -> Financial and insurance activities
    "K": [("L", "broad")],   # Real estate -> Real estate activities
    "L": [("M", "broad")],   # Professional -> Professional, scientific, technical
    "M": [("I", "broad")],   # Accommodation -> Accommodation and food service
    "O": [("P", "broad")],   # Education -> Education
    "P": [("Q", "broad")],   # Health -> Human health and social work
    "S": [("O", "broad")],   # Government -> Public administration and defence
}


# ── Main ingestion ─────────────────────────────────────────────


async def ingest_jsic_2013(conn) -> int:
    """Ingest JSIC 2013 (Rev 13) division-level codes.

    Inserts the 20 division codes (A-T) with English titles and creates
    ISIC Rev 4 equivalence edges at division level where a clear mapping
    exists.

    Args:
        conn: asyncpg connection

    Returns:
        Number of codes ingested.
    """
    # Register the classification system
    await conn.execute("""
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, tint_color)
        VALUES ('jsic_2013', 'JSIC 2013',
                'Japan Standard Industrial Classification (Rev 13)',
                'Japan', '2013 (Rev 13)',
                'Ministry of Internal Affairs and Communications',
                '#F43F5E')
        ON CONFLICT (id) DO UPDATE SET node_count = 0
    """)

    # Insert division nodes
    count = 0
    seq = 0
    for code in sorted(JSIC_DIVISIONS.keys()):
        title = JSIC_DIVISIONS[code]
        seq += 1
        # All divisions are leaf nodes in the skeleton (no children yet)
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('jsic_2013', $1, $2, 0, NULL, $1, TRUE, $3)
            ON CONFLICT (system_id, code) DO NOTHING
        """, code, title, seq)
        count += 1

    # Create ISIC <-> JSIC equivalence edges at division level
    edge_count = 0
    for jsic_code, isic_targets in JSIC_TO_ISIC_MAPPING.items():
        for isic_code, match_type in isic_targets:
            # Forward: JSIC -> ISIC
            await conn.execute("""
                INSERT INTO equivalence
                    (source_system, source_code, target_system, target_code, match_type)
                VALUES ('jsic_2013', $1, 'isic_rev4', $2, $3)
                ON CONFLICT DO NOTHING
            """, jsic_code, isic_code, match_type)
            edge_count += 1

            # Reverse: ISIC -> JSIC
            await conn.execute("""
                INSERT INTO equivalence
                    (source_system, source_code, target_system, target_code, match_type)
                VALUES ('isic_rev4', $1, 'jsic_2013', $2, $3)
                ON CONFLICT DO NOTHING
            """, isic_code, jsic_code, match_type)
            edge_count += 1

    # Update node count
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'jsic_2013'",
        count,
    )

    print(f"  Ingested {count} JSIC 2013 division codes, {edge_count} equivalence edges")
    return count
