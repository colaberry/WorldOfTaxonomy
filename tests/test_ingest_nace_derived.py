"""Tests for NACE-derived classification ingesters (WZ, ONACE, NOGA).

These tests rely on the conftest.py session fixtures (db_pool, setup_and_teardown)
which create a test_wot schema and seed NAICS, ISIC, and SIC data.

Since the derived ingesters require nace_rev2 data, each test seeds a small
set of NACE Rev 2 nodes before running the ingester under test.
"""

import asyncio
import pytest


def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ── NACE Rev 2 seed data ───────────────────────────────────────

NACE_NODES = [
    # (code, title, description, level, parent_code, sector_code, is_leaf, seq_order)
    ("A", "Agriculture, forestry and fishing", None, 0, None, "A", False, 1),
    ("C", "Manufacturing", None, 0, None, "C", False, 2),
    ("01", "Crop and animal production", None, 1, "A", "A", False, 3),
    ("10", "Manufacture of food products", None, 1, "C", "C", False, 4),
    ("01.1", "Growing of non-perennial crops", None, 2, "01", "A", False, 5),
    ("10.1", "Processing and preserving of meat", None, 2, "10", "C", False, 6),
    ("01.11", "Growing of cereals", None, 3, "01.1", "A", True, 7),
    ("10.11", "Processing and preserving of meat", None, 3, "10.1", "C", True, 8),
]


async def _seed_nace_rev2(conn):
    """Insert a minimal nace_rev2 system and sample nodes."""
    await conn.execute("""
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, tint_color)
        VALUES ('nace_rev2', 'NACE Rev 2',
                'Statistical Classification of Economic Activities in the European Community, Rev. 2',
                'European Union (27 countries)', 'Rev 2', 'Eurostat', '#1E40AF')
    """)
    for code, title, desc, level, parent, sector, leaf, seq in NACE_NODES:
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, description, level,
                 parent_code, sector_code, is_leaf, seq_order)
            VALUES ('nace_rev2', $1, $2, $3, $4, $5, $6, $7, $8)
        """, code, title, desc, level, parent, sector, leaf, seq)
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'nace_rev2'",
        len(NACE_NODES),
    )


@pytest.fixture
def seed_nace(db_pool):
    """Seed NACE Rev 2 data for tests that need it."""
    async def _seed():
        async with db_pool.acquire() as conn:
            await _seed_nace_rev2(conn)
    _run(_seed())


# ── Helpers ─────────────────────────────────────────────────────


async def _get_system(conn, system_id: str):
    return await conn.fetchrow(
        "SELECT * FROM classification_system WHERE id = $1", system_id
    )


async def _count_nodes(conn, system_id: str) -> int:
    row = await conn.fetchrow(
        "SELECT count(*) AS cnt FROM classification_node WHERE system_id = $1",
        system_id,
    )
    return row["cnt"]


async def _count_equivalences(conn, source_system: str, target_system: str) -> int:
    row = await conn.fetchrow(
        """SELECT count(*) AS cnt FROM equivalence
           WHERE source_system = $1 AND target_system = $2""",
        source_system,
        target_system,
    )
    return row["cnt"]


async def _get_node(conn, system_id: str, code: str):
    return await conn.fetchrow(
        "SELECT * FROM classification_node WHERE system_id = $1 AND code = $2",
        system_id,
        code,
    )


# ── WZ 2008 Tests ──────────────────────────────────────────────


class TestIngestWZ2008:

    def test_creates_system(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_wz_2008

        async def _test():
            async with db_pool.acquire() as conn:
                count = await ingest_wz_2008(conn)
                assert count == len(NACE_NODES)

                sys = await _get_system(conn, "wz_2008")
                assert sys is not None
                assert sys["name"] == "WZ 2008"
                assert sys["region"] == "Germany"
                assert sys["authority"] == "Statistisches Bundesamt (Destatis)"
                assert sys["tint_color"] == "#EF4444"
                assert sys["node_count"] == len(NACE_NODES)

        _run(_test())

    def test_copies_all_nodes(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_wz_2008

        async def _test():
            async with db_pool.acquire() as conn:
                await ingest_wz_2008(conn)

                node_count = await _count_nodes(conn, "wz_2008")
                assert node_count == len(NACE_NODES)

                # Verify a specific node was copied correctly
                node = await _get_node(conn, "wz_2008", "01.11")
                assert node is not None
                assert node["title"] == "Growing of cereals"
                assert node["level"] == 3
                assert node["parent_code"] == "01.1"
                assert node["sector_code"] == "A"
                assert node["is_leaf"] is True

        _run(_test())

    def test_creates_equivalence_edges(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_wz_2008

        async def _test():
            async with db_pool.acquire() as conn:
                await ingest_wz_2008(conn)

                # Forward edges: wz_2008 -> nace_rev2
                fwd = await _count_equivalences(conn, "wz_2008", "nace_rev2")
                assert fwd == len(NACE_NODES)

                # Reverse edges: nace_rev2 -> wz_2008
                rev = await _count_equivalences(conn, "nace_rev2", "wz_2008")
                assert rev == len(NACE_NODES)

                # All edges should be exact match
                row = await conn.fetchrow("""
                    SELECT count(*) AS cnt FROM equivalence
                    WHERE source_system = 'wz_2008'
                      AND target_system = 'nace_rev2'
                      AND match_type = 'exact'
                """)
                assert row["cnt"] == len(NACE_NODES)

        _run(_test())


# ── ONACE 2008 Tests ────────────────────────────────────────────


class TestIngestONACE2008:

    def test_creates_system(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_onace_2008

        async def _test():
            async with db_pool.acquire() as conn:
                count = await ingest_onace_2008(conn)
                assert count == len(NACE_NODES)

                sys = await _get_system(conn, "onace_2008")
                assert sys is not None
                assert sys["name"] == "ÖNACE 2008"
                assert sys["region"] == "Austria"
                assert sys["authority"] == "Statistik Austria"
                assert sys["tint_color"] == "#DC2626"

        _run(_test())

    def test_copies_all_nodes(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_onace_2008

        async def _test():
            async with db_pool.acquire() as conn:
                await ingest_onace_2008(conn)

                node_count = await _count_nodes(conn, "onace_2008")
                assert node_count == len(NACE_NODES)

                # Verify section node
                node = await _get_node(conn, "onace_2008", "A")
                assert node is not None
                assert node["title"] == "Agriculture, forestry and fishing"
                assert node["level"] == 0
                assert node["is_leaf"] is False

        _run(_test())

    def test_creates_equivalence_edges(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_onace_2008

        async def _test():
            async with db_pool.acquire() as conn:
                await ingest_onace_2008(conn)

                fwd = await _count_equivalences(conn, "onace_2008", "nace_rev2")
                assert fwd == len(NACE_NODES)

                rev = await _count_equivalences(conn, "nace_rev2", "onace_2008")
                assert rev == len(NACE_NODES)

        _run(_test())


# ── NOGA 2008 Tests ─────────────────────────────────────────────


class TestIngestNOGA2008:

    def test_creates_system(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_noga_2008

        async def _test():
            async with db_pool.acquire() as conn:
                count = await ingest_noga_2008(conn)
                assert count == len(NACE_NODES)

                sys = await _get_system(conn, "noga_2008")
                assert sys is not None
                assert sys["name"] == "NOGA 2008"
                assert sys["region"] == "Switzerland"
                assert sys["authority"] == "Swiss Federal Statistical Office (BFS)"
                assert sys["tint_color"] == "#B91C1C"

        _run(_test())

    def test_copies_all_nodes(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_noga_2008

        async def _test():
            async with db_pool.acquire() as conn:
                await ingest_noga_2008(conn)

                node_count = await _count_nodes(conn, "noga_2008")
                assert node_count == len(NACE_NODES)

                # Verify a leaf node
                node = await _get_node(conn, "noga_2008", "10.11")
                assert node is not None
                assert node["title"] == "Processing and preserving of meat"
                assert node["level"] == 3
                assert node["parent_code"] == "10.1"
                assert node["is_leaf"] is True

        _run(_test())

    def test_creates_equivalence_edges(self, db_pool, seed_nace):
        from world_of_taxanomy.ingest.nace_derived import ingest_noga_2008

        async def _test():
            async with db_pool.acquire() as conn:
                await ingest_noga_2008(conn)

                fwd = await _count_equivalences(conn, "noga_2008", "nace_rev2")
                assert fwd == len(NACE_NODES)

                rev = await _count_equivalences(conn, "nace_rev2", "noga_2008")
                assert rev == len(NACE_NODES)

        _run(_test())


# ── Edge case: no NACE data ─────────────────────────────────────


class TestDerivedWithoutNACE:

    def test_returns_zero_when_no_nace_data(self, db_pool):
        """Ingester should return 0 if nace_rev2 has no nodes."""
        from world_of_taxanomy.ingest.nace_derived import ingest_wz_2008

        async def _test():
            async with db_pool.acquire() as conn:
                # nace_rev2 system doesn't exist, so no nodes to copy
                count = await ingest_wz_2008(conn)
                assert count == 0

                # System should still be registered
                sys = await _get_system(conn, "wz_2008")
                assert sys is not None
                assert sys["node_count"] == 0

        _run(_test())
