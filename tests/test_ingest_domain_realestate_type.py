"""Tests for Real Estate Property Type domain taxonomy ingester.

RED tests - written before any implementation exists.

Real estate taxonomy organizes property types (NAICS 53):
  Residential    (drt_resid*)  - SFR, multifamily, condo, manufactured
  Commercial     (drt_comm*)   - office, retail, industrial, hospitality
  Special Purpose (drt_spec*)  - healthcare, senior housing, self-storage, data center
  Land           (drt_land*)   - farmland, timberland, development, mineral rights

Source: CoStar / NCREIF property type classifications. Public domain concepts.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_realestate_type import (
    REALESTATE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_realestate_type,
)


class TestDetermineLevel:
    def test_residential_category_is_level_1(self):
        assert _determine_level("drt_resid") == 1

    def test_sfr_is_level_2(self):
        assert _determine_level("drt_resid_sfr") == 2

    def test_commercial_category_is_level_1(self):
        assert _determine_level("drt_comm") == 1

    def test_office_is_level_2(self):
        assert _determine_level("drt_comm_office") == 2


class TestDetermineParent:
    def test_residential_category_has_no_parent(self):
        assert _determine_parent("drt_resid") is None

    def test_sfr_parent_is_resid(self):
        assert _determine_parent("drt_resid_sfr") == "drt_resid"

    def test_office_parent_is_comm(self):
        assert _determine_parent("drt_comm_office") == "drt_comm"


class TestRealEstateNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(REALESTATE_NODES) > 0

    def test_has_residential_category(self):
        codes = [n[0] for n in REALESTATE_NODES]
        assert "drt_resid" in codes

    def test_has_commercial_category(self):
        codes = [n[0] for n in REALESTATE_NODES]
        assert "drt_comm" in codes

    def test_has_special_purpose_category(self):
        codes = [n[0] for n in REALESTATE_NODES]
        assert "drt_spec" in codes

    def test_has_sfr(self):
        codes = [n[0] for n in REALESTATE_NODES]
        assert "drt_resid_sfr" in codes

    def test_has_office(self):
        codes = [n[0] for n in REALESTATE_NODES]
        assert "drt_comm_office" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in REALESTATE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in REALESTATE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in REALESTATE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in REALESTATE_NODES:
            if level == 2:
                assert parent is not None


def test_domain_realestate_type_module_importable():
    assert callable(ingest_domain_realestate_type)
    assert isinstance(REALESTATE_NODES, list)


def test_ingest_domain_realestate_type(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_realestate_type(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_realestate_type'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_realestate_type_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_realestate_type(conn)
            count2 = await ingest_domain_realestate_type(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
