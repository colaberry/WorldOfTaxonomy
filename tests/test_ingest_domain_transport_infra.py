"""Tests for Transportation Infrastructure and Terminal Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_transport_infra import (
    TRANSPORT_INFRA_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_transport_infra,
)


class TestDetermineLevel:
    def test_airport_category_is_level_1(self):
        assert _determine_level("dtinfra_airport") == 1

    def test_hub_is_level_2(self):
        assert _determine_level("dtinfra_airport_hub") == 2

    def test_seaport_category_is_level_1(self):
        assert _determine_level("dtinfra_seaport") == 1


class TestDetermineParent:
    def test_airport_has_no_parent(self):
        assert _determine_parent("dtinfra_airport") is None

    def test_hub_parent_is_airport(self):
        assert _determine_parent("dtinfra_airport_hub") == "dtinfra_airport"

    def test_container_parent_is_seaport(self):
        assert _determine_parent("dtinfra_seaport_container") == "dtinfra_seaport"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(TRANSPORT_INFRA_NODES) > 0

    def test_has_airport_category(self):
        codes = [n[0] for n in TRANSPORT_INFRA_NODES]
        assert "dtinfra_airport" in codes

    def test_has_seaport_category(self):
        codes = [n[0] for n in TRANSPORT_INFRA_NODES]
        assert "dtinfra_seaport" in codes

    def test_has_rail_category(self):
        codes = [n[0] for n in TRANSPORT_INFRA_NODES]
        assert "dtinfra_rail" in codes

    def test_has_hub_node(self):
        codes = [n[0] for n in TRANSPORT_INFRA_NODES]
        assert "dtinfra_airport_hub" in codes

    def test_has_container_node(self):
        codes = [n[0] for n in TRANSPORT_INFRA_NODES]
        assert "dtinfra_seaport_container" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in TRANSPORT_INFRA_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in TRANSPORT_INFRA_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in TRANSPORT_INFRA_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in TRANSPORT_INFRA_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(TRANSPORT_INFRA_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in TRANSPORT_INFRA_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_transport_infra)
    assert isinstance(TRANSPORT_INFRA_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_transport_infra(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_transport_infra'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_transport_infra(conn)
            count2 = await ingest_domain_transport_infra(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
