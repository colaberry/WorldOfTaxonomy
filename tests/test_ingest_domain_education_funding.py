"""Tests for Education Funding and Governance Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_education_funding import (
    EDU_FUNDING_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_education_funding,
)


class TestDetermineLevel:
    def test_public_category_is_level_1(self):
        assert _determine_level("detfund_public") == 1

    def test_k12_is_level_2(self):
        assert _determine_level("detfund_public_k12") == 2

    def test_privnp_category_is_level_1(self):
        assert _determine_level("detfund_privnp") == 1


class TestDetermineParent:
    def test_public_has_no_parent(self):
        assert _determine_parent("detfund_public") is None

    def test_k12_parent_is_public(self):
        assert _determine_parent("detfund_public_k12") == "detfund_public"

    def test_research_parent_is_privnp(self):
        assert _determine_parent("detfund_privnp_research") == "detfund_privnp"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(EDU_FUNDING_NODES) > 0

    def test_has_public_category(self):
        codes = [n[0] for n in EDU_FUNDING_NODES]
        assert "detfund_public" in codes

    def test_has_privnp_category(self):
        codes = [n[0] for n in EDU_FUNDING_NODES]
        assert "detfund_privnp" in codes

    def test_has_forprofit_category(self):
        codes = [n[0] for n in EDU_FUNDING_NODES]
        assert "detfund_forprofit" in codes

    def test_has_k12_node(self):
        codes = [n[0] for n in EDU_FUNDING_NODES]
        assert "detfund_public_k12" in codes

    def test_has_research_node(self):
        codes = [n[0] for n in EDU_FUNDING_NODES]
        assert "detfund_privnp_research" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in EDU_FUNDING_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in EDU_FUNDING_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in EDU_FUNDING_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in EDU_FUNDING_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(EDU_FUNDING_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in EDU_FUNDING_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_education_funding)
    assert isinstance(EDU_FUNDING_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_education_funding(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_education_funding'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_education_funding(conn)
            count2 = await ingest_domain_education_funding(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
