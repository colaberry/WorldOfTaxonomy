"""Tests for Professional Services Firm Size and Market Segment Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_prof_firm import (
    PROF_FIRM_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_prof_firm,
)


class TestDetermineLevel:
    def test_big_category_is_level_1(self):
        assert _determine_level("dpsfirm_big") == 1

    def test_four_is_level_2(self):
        assert _determine_level("dpsfirm_big_four") == 2

    def test_regional_category_is_level_1(self):
        assert _determine_level("dpsfirm_regional") == 1


class TestDetermineParent:
    def test_big_has_no_parent(self):
        assert _determine_parent("dpsfirm_big") is None

    def test_four_parent_is_big(self):
        assert _determine_parent("dpsfirm_big_four") == "dpsfirm_big"

    def test_specialist_parent_is_regional(self):
        assert _determine_parent("dpsfirm_boutique_specialist") == "dpsfirm_boutique"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(PROF_FIRM_NODES) > 0

    def test_has_big_category(self):
        codes = [n[0] for n in PROF_FIRM_NODES]
        assert "dpsfirm_big" in codes

    def test_has_regional_category(self):
        codes = [n[0] for n in PROF_FIRM_NODES]
        assert "dpsfirm_regional" in codes

    def test_has_boutique_category(self):
        codes = [n[0] for n in PROF_FIRM_NODES]
        assert "dpsfirm_boutique" in codes

    def test_has_four_node(self):
        codes = [n[0] for n in PROF_FIRM_NODES]
        assert "dpsfirm_big_four" in codes

    def test_has_specialist_node(self):
        codes = [n[0] for n in PROF_FIRM_NODES]
        assert "dpsfirm_boutique_specialist" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in PROF_FIRM_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in PROF_FIRM_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in PROF_FIRM_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in PROF_FIRM_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(PROF_FIRM_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in PROF_FIRM_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_prof_firm)
    assert isinstance(PROF_FIRM_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_prof_firm(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_prof_firm'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_prof_firm(conn)
            count2 = await ingest_domain_prof_firm(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
