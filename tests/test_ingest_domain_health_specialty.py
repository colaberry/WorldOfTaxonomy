"""Tests for Healthcare Clinical Specialty and Service Line Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_health_specialty import (
    HEALTH_SPECIALTY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_health_specialty,
)


class TestDetermineLevel:
    def test_cardiac_category_is_level_1(self):
        assert _determine_level("dhssl_cardiac") == 1

    def test_intervention_is_level_2(self):
        assert _determine_level("dhssl_cardiac_intervention") == 2

    def test_onco_category_is_level_1(self):
        assert _determine_level("dhssl_onco") == 1


class TestDetermineParent:
    def test_cardiac_has_no_parent(self):
        assert _determine_parent("dhssl_cardiac") is None

    def test_intervention_parent_is_cardiac(self):
        assert _determine_parent("dhssl_cardiac_intervention") == "dhssl_cardiac"

    def test_med_parent_is_onco(self):
        assert _determine_parent("dhssl_onco_med") == "dhssl_onco"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(HEALTH_SPECIALTY_NODES) > 0

    def test_has_cardiac_category(self):
        codes = [n[0] for n in HEALTH_SPECIALTY_NODES]
        assert "dhssl_cardiac" in codes

    def test_has_onco_category(self):
        codes = [n[0] for n in HEALTH_SPECIALTY_NODES]
        assert "dhssl_onco" in codes

    def test_has_ortho_category(self):
        codes = [n[0] for n in HEALTH_SPECIALTY_NODES]
        assert "dhssl_ortho" in codes

    def test_has_intervention_node(self):
        codes = [n[0] for n in HEALTH_SPECIALTY_NODES]
        assert "dhssl_cardiac_intervention" in codes

    def test_has_med_node(self):
        codes = [n[0] for n in HEALTH_SPECIALTY_NODES]
        assert "dhssl_onco_med" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in HEALTH_SPECIALTY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in HEALTH_SPECIALTY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in HEALTH_SPECIALTY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in HEALTH_SPECIALTY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(HEALTH_SPECIALTY_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in HEALTH_SPECIALTY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_health_specialty)
    assert isinstance(HEALTH_SPECIALTY_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_health_specialty(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_health_specialty'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_health_specialty(conn)
            count2 = await ingest_domain_health_specialty(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
