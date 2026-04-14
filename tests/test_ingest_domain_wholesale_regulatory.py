"""Tests for Wholesale Trade Regulatory Compliance Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_wholesale_regulatory import (
    WHOLESALE_REG_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_wholesale_regulatory,
)


class TestDetermineLevel:
    def test_fda_category_is_level_1(self):
        assert _determine_level("dwcreg_fda") == 1

    def test_drug_is_level_2(self):
        assert _determine_level("dwcreg_fda_drug") == 2

    def test_usda_category_is_level_1(self):
        assert _determine_level("dwcreg_usda") == 1


class TestDetermineParent:
    def test_fda_has_no_parent(self):
        assert _determine_parent("dwcreg_fda") is None

    def test_drug_parent_is_fda(self):
        assert _determine_parent("dwcreg_fda_drug") == "dwcreg_fda"

    def test_meat_parent_is_usda(self):
        assert _determine_parent("dwcreg_usda_meat") == "dwcreg_usda"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(WHOLESALE_REG_NODES) > 0

    def test_has_fda_category(self):
        codes = [n[0] for n in WHOLESALE_REG_NODES]
        assert "dwcreg_fda" in codes

    def test_has_usda_category(self):
        codes = [n[0] for n in WHOLESALE_REG_NODES]
        assert "dwcreg_usda" in codes

    def test_has_epa_category(self):
        codes = [n[0] for n in WHOLESALE_REG_NODES]
        assert "dwcreg_epa" in codes

    def test_has_drug_node(self):
        codes = [n[0] for n in WHOLESALE_REG_NODES]
        assert "dwcreg_fda_drug" in codes

    def test_has_meat_node(self):
        codes = [n[0] for n in WHOLESALE_REG_NODES]
        assert "dwcreg_usda_meat" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in WHOLESALE_REG_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in WHOLESALE_REG_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in WHOLESALE_REG_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in WHOLESALE_REG_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(WHOLESALE_REG_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in WHOLESALE_REG_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_wholesale_regulatory)
    assert isinstance(WHOLESALE_REG_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_wholesale_regulatory(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_wholesale_regulatory'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_wholesale_regulatory(conn)
            count2 = await ingest_domain_wholesale_regulatory(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
