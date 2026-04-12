"""Tests for CPC v2.1 crosswalk ingesters.

RED tests - written before any implementation exists.

Two crosswalks:
  1. cpc_v21 <-> isic_rev4 (from CPCv21_ISIC4/cpc21-isic4.txt, ~2,715 pairs)
  2. hs_2022 <-> cpc_v21 (from CPCv21_HS2017/CPC21-HS2017.csv, ~5,843 pairs)

Match type: 'exact' when both partial flags are 0, 'partial' otherwise.
"""
import pytest
from world_of_taxanomy.ingest.crosswalk_cpc import (
    ingest_crosswalk_cpc_isic,
    ingest_crosswalk_cpc_hs,
)


# --- importability ---

def test_crosswalk_cpc_module_importable():
    """Both functions are importable."""
    assert callable(ingest_crosswalk_cpc_isic)
    assert callable(ingest_crosswalk_cpc_hs)


# --- CPC / ISIC crosswalk ---

def test_ingest_crosswalk_cpc_isic(db_pool):
    """Integration test - inserts bidirectional CPC <-> ISIC edges."""
    import asyncio
    from pathlib import Path

    data_path = Path("data/cpc21_isic4.txt")
    if not data_path.exists():
        pytest.skip(f"Download {data_path} first: see world_of_taxanomy/ingest/crosswalk_cpc.py")

    async def _run():
        async with db_pool.acquire() as conn:
            # Seed both systems
            for sys_id, name in [("cpc_v21", "CPC v2.1"), ("isic_rev4", "ISIC Rev 4")]:
                await conn.execute(
                    """INSERT INTO classification_system
                           (id, name, full_name, version, region, authority, node_count)
                       VALUES ($1,$2,$3,$4,$5,$6,0) ON CONFLICT (id) DO NOTHING""",
                    sys_id, name, name, "1", "Global", "UN",
                )
            # Seed sample nodes: CPC 01111 -> ISIC 0111
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "cpc_v21", "01111", "Wheat, seed", 5, "0111", "0", True, 1,
            )
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "isic_rev4", "0111", "Growing of cereals", 4, "011", "A", True, 1,
            )

            count = await ingest_crosswalk_cpc_isic(conn, path=str(data_path))
            assert count >= 2, f"Expected >= 2 edges, got {count}"

            # Forward: cpc_v21:01111 -> isic_rev4:0111
            row = await conn.fetchrow(
                """SELECT match_type FROM equivalence
                   WHERE source_system='cpc_v21' AND source_code='01111'
                   AND target_system='isic_rev4' AND target_code='0111'"""
            )
            assert row is not None

            # Reverse: isic_rev4:0111 -> cpc_v21:01111
            row2 = await conn.fetchrow(
                """SELECT match_type FROM equivalence
                   WHERE source_system='isic_rev4' AND source_code='0111'
                   AND target_system='cpc_v21' AND target_code='01111'"""
            )
            assert row2 is not None

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_cpc_isic_idempotent(db_pool):
    """Running twice yields same count."""
    import asyncio
    from pathlib import Path

    data_path = Path("data/cpc21_isic4.txt")
    if not data_path.exists():
        pytest.skip("data/cpc21_isic4.txt not found")

    async def _run():
        async with db_pool.acquire() as conn:
            for sys_id, name in [("cpc_v21", "CPC v2.1"), ("isic_rev4", "ISIC Rev 4")]:
                await conn.execute(
                    """INSERT INTO classification_system
                           (id, name, full_name, version, region, authority, node_count)
                       VALUES ($1,$2,$3,$4,$5,$6,0) ON CONFLICT (id) DO NOTHING""",
                    sys_id, name, name, "1", "Global", "UN",
                )
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "cpc_v21", "01111", "Wheat, seed", 5, "0111", "0", True, 1,
            )
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "isic_rev4", "0111", "Growing of cereals", 4, "011", "A", True, 1,
            )
            c1 = await ingest_crosswalk_cpc_isic(conn, path=str(data_path))
            c2 = await ingest_crosswalk_cpc_isic(conn, path=str(data_path))
            assert c1 == c2

    asyncio.get_event_loop().run_until_complete(_run())


# --- HS / CPC crosswalk ---

def test_ingest_crosswalk_cpc_hs(db_pool):
    """Integration test - inserts bidirectional HS <-> CPC edges."""
    import asyncio
    from pathlib import Path

    data_path = Path("data/cpc21_hs2017.csv")
    if not data_path.exists():
        pytest.skip(f"Download {data_path} first: see world_of_taxanomy/ingest/crosswalk_cpc.py")

    async def _run():
        async with db_pool.acquire() as conn:
            for sys_id, name in [("hs_2022", "HS 2022"), ("cpc_v21", "CPC v2.1")]:
                await conn.execute(
                    """INSERT INTO classification_system
                           (id, name, full_name, version, region, authority, node_count)
                       VALUES ($1,$2,$3,$4,$5,$6,0) ON CONFLICT (id) DO NOTHING""",
                    sys_id, name, name, "1", "Global", "UN",
                )
            # HS 0101.21 (stripped: 010121) -> CPC 02131
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "hs_2022", "010121", "Pure-bred breeding horses", 4, "0101", "I", True, 1,
            )
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "cpc_v21", "02131", "Live horses", 5, "0213", "0", True, 1,
            )

            count = await ingest_crosswalk_cpc_hs(conn, path=str(data_path))
            assert count >= 2, f"Expected >= 2 edges, got {count}"

            # Forward: hs_2022:010121 -> cpc_v21:02131
            row = await conn.fetchrow(
                """SELECT match_type FROM equivalence
                   WHERE source_system='hs_2022' AND source_code='010121'
                   AND target_system='cpc_v21' AND target_code='02131'"""
            )
            assert row is not None

            # Reverse: cpc_v21:02131 -> hs_2022:010121
            row2 = await conn.fetchrow(
                """SELECT match_type FROM equivalence
                   WHERE source_system='cpc_v21' AND source_code='02131'
                   AND target_system='hs_2022' AND target_code='010121'"""
            )
            assert row2 is not None

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_cpc_hs_idempotent(db_pool):
    """Running twice yields same count."""
    import asyncio
    from pathlib import Path

    data_path = Path("data/cpc21_hs2017.csv")
    if not data_path.exists():
        pytest.skip("data/cpc21_hs2017.csv not found")

    async def _run():
        async with db_pool.acquire() as conn:
            for sys_id, name in [("hs_2022", "HS 2022"), ("cpc_v21", "CPC v2.1")]:
                await conn.execute(
                    """INSERT INTO classification_system
                           (id, name, full_name, version, region, authority, node_count)
                       VALUES ($1,$2,$3,$4,$5,$6,0) ON CONFLICT (id) DO NOTHING""",
                    sys_id, name, name, "1", "Global", "UN",
                )
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "hs_2022", "010121", "Pure-bred breeding horses", 4, "0101", "I", True, 1,
            )
            await conn.execute(
                """INSERT INTO classification_node
                       (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING""",
                "cpc_v21", "02131", "Live horses", 5, "0213", "0", True, 1,
            )
            c1 = await ingest_crosswalk_cpc_hs(conn, path=str(data_path))
            c2 = await ingest_crosswalk_cpc_hs(conn, path=str(data_path))
            assert c1 == c2

    asyncio.get_event_loop().run_until_complete(_run())
