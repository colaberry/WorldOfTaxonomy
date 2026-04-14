"""Tests for Information and Media Platform Type Classification domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_info_platform import (
    INFO_PLATFORM_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_info_platform,
)


class TestDetermineLevel:
    def test_owned_category_is_level_1(self):
        assert _determine_level("dimplt_owned") == 1

    def test_web_is_level_2(self):
        assert _determine_level("dimplt_owned_web") == 2

    def test_social_category_is_level_1(self):
        assert _determine_level("dimplt_social") == 1


class TestDetermineParent:
    def test_owned_has_no_parent(self):
        assert _determine_parent("dimplt_owned") is None

    def test_web_parent_is_owned(self):
        assert _determine_parent("dimplt_owned_web") == "dimplt_owned"

    def test_ump_parent_is_social(self):
        assert _determine_parent("dimplt_social_ump") == "dimplt_social"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(INFO_PLATFORM_NODES) > 0

    def test_has_owned_category(self):
        codes = [n[0] for n in INFO_PLATFORM_NODES]
        assert "dimplt_owned" in codes

    def test_has_social_category(self):
        codes = [n[0] for n in INFO_PLATFORM_NODES]
        assert "dimplt_social" in codes

    def test_has_marketplace_category(self):
        codes = [n[0] for n in INFO_PLATFORM_NODES]
        assert "dimplt_marketplace" in codes

    def test_has_web_node(self):
        codes = [n[0] for n in INFO_PLATFORM_NODES]
        assert "dimplt_owned_web" in codes

    def test_has_ump_node(self):
        codes = [n[0] for n in INFO_PLATFORM_NODES]
        assert "dimplt_social_ump" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in INFO_PLATFORM_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in INFO_PLATFORM_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in INFO_PLATFORM_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in INFO_PLATFORM_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(INFO_PLATFORM_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in INFO_PLATFORM_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_info_platform)
    assert isinstance(INFO_PLATFORM_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_info_platform(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_info_platform'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_info_platform(conn)
            count2 = await ingest_domain_info_platform(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
