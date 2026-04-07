"""NACE-derived classification system ingesters.

These systems (WZ 2008, ONACE 2008, NOGA 2008) are national adaptations of
NACE Rev 2.  At the NACE-level granularity the codes are identical, so we
derive them by copying every node from the existing nace_rev2 data in the
database and creating exact-match equivalence edges back to nace_rev2.

National extensions (codes finer than the 4-digit NACE class level) can be
added later by parsing country-specific data files.

Must be called AFTER nace_rev2 has been ingested.
"""

from __future__ import annotations

from typing import NamedTuple


class _SystemMeta(NamedTuple):
    id: str
    name: str
    full_name: str
    region: str
    version: str
    authority: str
    tint_color: str


_WZ_2008 = _SystemMeta(
    id="wz_2008",
    name="WZ 2008",
    full_name="Klassifikation der Wirtschaftszweige 2008",
    region="Germany",
    version="2008",
    authority="Statistisches Bundesamt (Destatis)",
    tint_color="#EF4444",
)

_ONACE_2008 = _SystemMeta(
    id="onace_2008",
    name="ÖNACE 2008",
    full_name="Österreichische Systematik der Wirtschaftstätigkeiten 2008",
    region="Austria",
    version="2008",
    authority="Statistik Austria",
    tint_color="#DC2626",
)

_NOGA_2008 = _SystemMeta(
    id="noga_2008",
    name="NOGA 2008",
    full_name="Nomenclature Générale des Activités économiques 2008",
    region="Switzerland",
    version="2008",
    authority="Swiss Federal Statistical Office (BFS)",
    tint_color="#B91C1C",
)


# ── Core derivation logic ───────────────────────────────────────


async def _ingest_derived_from_nace(conn, meta: _SystemMeta) -> int:
    """Generic ingester that copies nace_rev2 nodes into a derived system.

    Steps:
      1. Register the classification_system.
      2. Copy every classification_node from nace_rev2 with the new system_id.
      3. Create bidirectional exact-match equivalence edges.
      4. Update node_count on the new system.

    Args:
        conn: asyncpg connection (search_path already set).
        meta: metadata for the derived system.

    Returns:
        Number of nodes ingested.
    """
    # 1. Register classification system
    await conn.execute(
        """
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, tint_color)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (id) DO UPDATE SET node_count = 0
        """,
        meta.id,
        meta.name,
        meta.full_name,
        meta.region,
        meta.version,
        meta.authority,
        meta.tint_color,
    )

    # 2. Copy nodes from nace_rev2
    nace_rows = await conn.fetch(
        """
        SELECT code, title, description, level, parent_code,
               sector_code, is_leaf, seq_order
        FROM classification_node
        WHERE system_id = 'nace_rev2'
        ORDER BY seq_order
        """
    )

    if not nace_rows:
        print(f"  WARNING: No nace_rev2 nodes found — {meta.id} will be empty")
        return 0

    count = 0
    for row in nace_rows:
        await conn.execute(
            """
            INSERT INTO classification_node
                (system_id, code, title, description, level,
                 parent_code, sector_code, is_leaf, seq_order)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (system_id, code) DO NOTHING
            """,
            meta.id,
            row["code"],
            row["title"],
            row["description"],
            row["level"],
            row["parent_code"],
            row["sector_code"],
            row["is_leaf"],
            row["seq_order"],
        )
        count += 1

    # 3. Create bidirectional exact-match equivalence edges
    for row in nace_rows:
        code = row["code"]
        # Forward: derived -> nace_rev2
        await conn.execute(
            """
            INSERT INTO equivalence
                (source_system, source_code, target_system, target_code, match_type)
            VALUES ($1, $2, 'nace_rev2', $3, 'exact')
            ON CONFLICT (source_system, source_code, target_system, target_code)
            DO NOTHING
            """,
            meta.id,
            code,
            code,
        )
        # Reverse: nace_rev2 -> derived
        await conn.execute(
            """
            INSERT INTO equivalence
                (source_system, source_code, target_system, target_code, match_type)
            VALUES ('nace_rev2', $1, $2, $3, 'exact')
            ON CONFLICT (source_system, source_code, target_system, target_code)
            DO NOTHING
            """,
            code,
            meta.id,
            code,
        )

    # 4. Update node_count
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count,
        meta.id,
    )

    print(f"  Ingested {count} {meta.name} codes (derived from NACE Rev 2)")
    return count


# ── Public API ──────────────────────────────────────────────────


async def ingest_wz_2008(conn) -> int:
    """Ingest German WZ 2008 (Klassifikation der Wirtschaftszweige).

    Derives all codes from NACE Rev 2 already present in the database.
    National 5-digit extensions can be added later from Destatis data.
    """
    return await _ingest_derived_from_nace(conn, _WZ_2008)


async def ingest_onace_2008(conn) -> int:
    """Ingest Austrian ONACE 2008.

    Derives all codes from NACE Rev 2 already present in the database.
    National extensions can be added later from Statistik Austria data.
    """
    return await _ingest_derived_from_nace(conn, _ONACE_2008)


async def ingest_noga_2008(conn) -> int:
    """Ingest Swiss NOGA 2008.

    Derives all codes from NACE Rev 2 already present in the database.
    National extensions can be added later from BFS data.
    """
    return await _ingest_derived_from_nace(conn, _NOGA_2008)
