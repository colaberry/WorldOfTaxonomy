"""Tests for Construction Trade Type domain taxonomy ingester.

RED tests - written before any implementation exists.

Trade taxonomy organizes construction work by specialty trade (CSI MasterFormat):
  Site Work     (dct_site*)   - excavation, concrete, paving
  Structural    (dct_struct*) - steel, carpentry, masonry
  MEP           (dct_mep*)    - electrical, plumbing, HVAC, fire protection
  Finish Trades (dct_finish*) - drywall, flooring, painting, glazing

Source: CSI MasterFormat (Construction Specifications Institute). Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_const_trade import (
    TRADE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_const_trade,
)


class TestDetermineLevel:
    def test_site_category_is_level_1(self):
        assert _determine_level("dct_site") == 1

    def test_excavation_is_level_2(self):
        assert _determine_level("dct_site_excav") == 2

    def test_mep_category_is_level_1(self):
        assert _determine_level("dct_mep") == 1

    def test_electrical_is_level_2(self):
        assert _determine_level("dct_mep_elec") == 2


class TestDetermineParent:
    def test_site_category_has_no_parent(self):
        assert _determine_parent("dct_site") is None

    def test_excav_parent_is_site(self):
        assert _determine_parent("dct_site_excav") == "dct_site"

    def test_electrical_parent_is_mep(self):
        assert _determine_parent("dct_mep_elec") == "dct_mep"


class TestTradeNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(TRADE_NODES) > 0

    def test_has_site_category(self):
        codes = [n[0] for n in TRADE_NODES]
        assert "dct_site" in codes

    def test_has_structural_category(self):
        codes = [n[0] for n in TRADE_NODES]
        assert "dct_struct" in codes

    def test_has_mep_category(self):
        codes = [n[0] for n in TRADE_NODES]
        assert "dct_mep" in codes

    def test_has_finish_category(self):
        codes = [n[0] for n in TRADE_NODES]
        assert "dct_finish" in codes

    def test_has_electrical(self):
        codes = [n[0] for n in TRADE_NODES]
        assert "dct_mep_elec" in codes

    def test_has_plumbing(self):
        codes = [n[0] for n in TRADE_NODES]
        assert "dct_mep_plumb" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in TRADE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in TRADE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in TRADE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in TRADE_NODES:
            if level == 2:
                assert parent is not None


def test_domain_const_trade_module_importable():
    assert callable(ingest_domain_const_trade)
    assert isinstance(TRADE_NODES, list)


def test_ingest_domain_const_trade(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_const_trade(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_const_trade'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_const_trade_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_const_trade(conn)
            count2 = await ingest_domain_const_trade(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
