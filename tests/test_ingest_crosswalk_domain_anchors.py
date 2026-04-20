"""Tests for sector-anchor bridge ingester.

RED tests for crosswalk_domain_anchors: reads a (domain_system_id -> [naics_code])
anchor map and emits equivalence rows naics_2022 -> domain_*, plus the reverse
domain_* -> naics_2022 edge, for every level=1 code in the domain system.

All edges:
  - match_type='broad'
  - notes='derived:sector_anchor:v1'
"""
import asyncio
import pytest

from world_of_taxonomy.ingest.crosswalk_domain_anchors import (
    ingest_crosswalk_domain_anchors,
    load_domain_anchors,
)


def test_module_importable():
    assert callable(ingest_crosswalk_domain_anchors)
    assert callable(load_domain_anchors)


def test_load_domain_anchors_returns_dict():
    anchors = load_domain_anchors()
    assert isinstance(anchors, dict)
    assert len(anchors) > 0
    # Every value is a dict with at least a 'naics' list
    for domain_id, entry in anchors.items():
        assert domain_id.startswith("domain_")
        assert "naics" in entry
        assert isinstance(entry["naics"], list)
        assert len(entry["naics"]) > 0


async def _seed_test_domain(conn, domain_id: str, domain_name: str):
    """Insert a small test domain system with two level-1 nodes."""
    await conn.execute(
        """
        INSERT INTO classification_system (id, name, full_name, region, version, authority, tint_color)
        VALUES ($1, $2, $2, 'United States', '1', 'Test', '#999999')
        """,
        domain_id,
        domain_name,
    )
    await conn.execute(
        """
        INSERT INTO classification_node (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
        VALUES ($1, 'root_a', 'Root A', 1, NULL, 'root_a', FALSE, 1),
               ($1, 'root_b', 'Root B', 1, NULL, 'root_b', FALSE, 2)
        """,
        domain_id,
    )


def test_ingest_emits_broad_edges_with_provenance(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            await _seed_test_domain(conn, "domain_test_fake", "Test Fake Domain")
            anchors = {"domain_test_fake": {"naics": ["62", "6211"]}}
            count = await ingest_crosswalk_domain_anchors(conn, anchors=anchors)
            assert count > 0

            rows = await conn.fetch(
                """
                SELECT source_system, source_code, target_system, target_code, match_type, notes
                FROM equivalence
                WHERE target_system = 'domain_test_fake' OR source_system = 'domain_test_fake'
                """
            )
            assert len(rows) > 0
            for r in rows:
                assert r["match_type"] == "broad"
                assert r["notes"] == "derived:sector_anchor:v1"

            # NAICS -> domain edges present for both anchor codes, both root_a and root_b
            forward = [
                (r["source_code"], r["target_code"])
                for r in rows
                if r["source_system"] == "naics_2022" and r["target_system"] == "domain_test_fake"
            ]
            assert ("62", "root_a") in forward
            assert ("62", "root_b") in forward
            assert ("6211", "root_a") in forward
            assert ("6211", "root_b") in forward

            # Reverse edges for bidirectional traversal
            reverse = [
                (r["source_code"], r["target_code"])
                for r in rows
                if r["source_system"] == "domain_test_fake" and r["target_system"] == "naics_2022"
            ]
            assert ("root_a", "62") in reverse
            assert ("root_b", "6211") in reverse

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_is_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            await _seed_test_domain(conn, "domain_test_idem", "Test Idem Domain")
            anchors = {"domain_test_idem": {"naics": ["62"]}}
            count1 = await ingest_crosswalk_domain_anchors(conn, anchors=anchors)
            count2 = await ingest_crosswalk_domain_anchors(conn, anchors=anchors)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_skips_missing_naics_codes(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            await _seed_test_domain(conn, "domain_test_skip", "Test Skip Domain")
            anchors = {"domain_test_skip": {"naics": ["99999_nonexistent"]}}
            count = await ingest_crosswalk_domain_anchors(conn, anchors=anchors)
            assert count == 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_skips_missing_domain_system(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            anchors = {"domain_not_loaded": {"naics": ["62"]}}
            count = await ingest_crosswalk_domain_anchors(conn, anchors=anchors)
            assert count == 0

    asyncio.get_event_loop().run_until_complete(_run())
