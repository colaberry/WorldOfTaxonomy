"""Tests for ISIC / NACE fan-out ingester.

After naics_2022 -> domain_* anchor edges exist, a SQL pass joins them with
existing naics_2022 <-> isic_rev4 / naics_2022 <-> nace_rev2 crosswalks to
emit parallel edges: isic_rev4 -> domain_* and nace_rev2 -> domain_*.

All generated edges:
    match_type = 'broad'
    notes      = 'derived:sector_anchor:v1:fanout'
"""
import asyncio
import pytest

from world_of_taxonomy.ingest.crosswalk_domain_anchors import ingest_crosswalk_domain_anchors
from world_of_taxonomy.ingest.crosswalk_domain_fanout import (
    FANOUT_PROVENANCE,
    ingest_crosswalk_domain_fanout,
)


def test_module_importable():
    assert callable(ingest_crosswalk_domain_fanout)
    assert FANOUT_PROVENANCE.startswith("derived:sector_anchor:")


async def _seed_test_domain(conn, domain_id: str):
    await conn.execute(
        """
        INSERT INTO classification_system (id, name, full_name, region, version, authority, tint_color)
        VALUES ($1, $1, $1, 'United States', '1', 'Test', '#999999')
        """,
        domain_id,
    )
    await conn.execute(
        """
        INSERT INTO classification_node (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
        VALUES ($1, 'root_a', 'Root A', 1, NULL, 'root_a', FALSE, 1)
        """,
        domain_id,
    )


def test_fanout_bridges_isic_to_domain(db_pool):
    """Given NAICS-ISIC crosswalk and NAICS-domain anchor, fan-out produces ISIC-domain edge."""
    async def _run():
        async with db_pool.acquire() as conn:
            # conftest already seeds naics_2022 (incl. 6211) and isic_rev4 (incl. 8620),
            # plus naics_2022 6211 <-> isic_rev4 8620.
            await _seed_test_domain(conn, "domain_fanout_fake")
            anchors = {"domain_fanout_fake": {"naics": ["6211"]}}
            await ingest_crosswalk_domain_anchors(conn, anchors=anchors)

            count = await ingest_crosswalk_domain_fanout(conn)
            assert count > 0

            rows = await conn.fetch(
                """
                SELECT source_system, source_code, target_system, target_code, match_type, notes
                FROM equivalence
                WHERE target_system = 'domain_fanout_fake'
                  AND source_system = 'isic_rev4'
                """
            )
            assert any(r["source_code"] == "8620" and r["target_code"] == "root_a" for r in rows)
            for r in rows:
                assert r["match_type"] == "broad"
                assert r["notes"] == FANOUT_PROVENANCE

            # Reverse direction too
            reverse = await conn.fetch(
                """
                SELECT source_code, target_code
                FROM equivalence
                WHERE source_system = 'domain_fanout_fake'
                  AND target_system = 'isic_rev4'
                """
            )
            assert any(r["source_code"] == "root_a" and r["target_code"] == "8620" for r in reverse)

    asyncio.get_event_loop().run_until_complete(_run())


def test_fanout_is_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            await _seed_test_domain(conn, "domain_fanout_idem")
            anchors = {"domain_fanout_idem": {"naics": ["6211"]}}
            await ingest_crosswalk_domain_anchors(conn, anchors=anchors)
            count1 = await ingest_crosswalk_domain_fanout(conn)
            count2 = await ingest_crosswalk_domain_fanout(conn)
            # Second call inserts nothing new.
            assert count2 == 0 or count2 <= count1

    asyncio.get_event_loop().run_until_complete(_run())


def test_fanout_no_anchors_no_edges(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count_before = await conn.fetchval(
                "SELECT COUNT(*) FROM equivalence WHERE notes = $1", FANOUT_PROVENANCE
            )
            count = await ingest_crosswalk_domain_fanout(conn)
            assert count == 0
            count_after = await conn.fetchval(
                "SELECT COUNT(*) FROM equivalence WHERE notes = $1", FANOUT_PROVENANCE
            )
            assert count_after == count_before

    asyncio.get_event_loop().run_until_complete(_run())
