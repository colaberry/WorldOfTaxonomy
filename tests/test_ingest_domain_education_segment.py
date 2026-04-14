"""Tests for Education Student Demographic Segment Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_education_segment import (
    EDU_SEGMENT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_education_segment,
)


class TestDetermineLevel:
    def test_trad_category_is_level_1(self):
        assert _determine_level("detseg_trad") == 1

    def test_fulltime_is_level_2(self):
        assert _determine_level("detseg_trad_fulltime") == 2

    def test_adult_category_is_level_1(self):
        assert _determine_level("detseg_adult") == 1


class TestDetermineParent:
    def test_trad_has_no_parent(self):
        assert _determine_parent("detseg_trad") is None

    def test_fulltime_parent_is_trad(self):
        assert _determine_parent("detseg_trad_fulltime") == "detseg_trad"

    def test_workforce_parent_is_adult(self):
        assert _determine_parent("detseg_adult_workforce") == "detseg_adult"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(EDU_SEGMENT_NODES) > 0

    def test_has_trad_category(self):
        codes = [n[0] for n in EDU_SEGMENT_NODES]
        assert "detseg_trad" in codes

    def test_has_adult_category(self):
        codes = [n[0] for n in EDU_SEGMENT_NODES]
        assert "detseg_adult" in codes

    def test_has_professional_category(self):
        codes = [n[0] for n in EDU_SEGMENT_NODES]
        assert "detseg_professional" in codes

    def test_has_fulltime_node(self):
        codes = [n[0] for n in EDU_SEGMENT_NODES]
        assert "detseg_trad_fulltime" in codes

    def test_has_workforce_node(self):
        codes = [n[0] for n in EDU_SEGMENT_NODES]
        assert "detseg_adult_workforce" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in EDU_SEGMENT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in EDU_SEGMENT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in EDU_SEGMENT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in EDU_SEGMENT_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(EDU_SEGMENT_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in EDU_SEGMENT_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_education_segment)
    assert isinstance(EDU_SEGMENT_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_education_segment(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_education_segment'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_education_segment(conn)
            count2 = await ingest_domain_education_segment(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
