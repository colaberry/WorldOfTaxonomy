"""Tests for Information/Media Type domain taxonomy ingester.

RED tests - written before any implementation exists.

Information/media taxonomy organizes content and software types (NAICS 51):
  Media Type    (dim_media*)  - print, broadcast, streaming, digital/social
  Software Cat  (dim_soft*)   - enterprise, consumer, SaaS, embedded/OS
  Data Type     (dim_data*)   - structured, unstructured, real-time, geospatial
  Telecom       (dim_tele*)   - wireline, wireless, broadband, satellite

Source: NAB (National Association of Broadcasters) + SIC/NAICS media categories. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_info_media import (
    INFO_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_info_media,
)


class TestDetermineLevel:
    def test_media_category_is_level_1(self):
        assert _determine_level("dim_media") == 1

    def test_broadcast_is_level_2(self):
        assert _determine_level("dim_media_broadcast") == 2

    def test_software_category_is_level_1(self):
        assert _determine_level("dim_soft") == 1

    def test_saas_is_level_2(self):
        assert _determine_level("dim_soft_saas") == 2


class TestDetermineParent:
    def test_media_category_has_no_parent(self):
        assert _determine_parent("dim_media") is None

    def test_broadcast_parent_is_media(self):
        assert _determine_parent("dim_media_broadcast") == "dim_media"

    def test_saas_parent_is_soft(self):
        assert _determine_parent("dim_soft_saas") == "dim_soft"


class TestInfoNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(INFO_NODES) > 0

    def test_has_media_category(self):
        codes = [n[0] for n in INFO_NODES]
        assert "dim_media" in codes

    def test_has_software_category(self):
        codes = [n[0] for n in INFO_NODES]
        assert "dim_soft" in codes

    def test_has_data_category(self):
        codes = [n[0] for n in INFO_NODES]
        assert "dim_data" in codes

    def test_has_broadcast(self):
        codes = [n[0] for n in INFO_NODES]
        assert "dim_media_broadcast" in codes

    def test_has_saas(self):
        codes = [n[0] for n in INFO_NODES]
        assert "dim_soft_saas" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in INFO_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in INFO_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in INFO_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in INFO_NODES:
            if level == 2:
                assert parent is not None


def test_domain_info_media_module_importable():
    assert callable(ingest_domain_info_media)
    assert isinstance(INFO_NODES, list)


def test_ingest_domain_info_media(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_info_media(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_info_media'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_info_media_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_info_media(conn)
            count2 = await ingest_domain_info_media(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
