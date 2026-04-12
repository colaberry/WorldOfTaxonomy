"""Tests for Truck Cargo Classification domain taxonomy ingester.

RED tests - written before any implementation exists.

Cargo taxonomy organizes truck cargo into categories:
  Commodity   (dtc_com*)  - general commodity groups
  Hazmat      (dtc_haz*)  - DOT hazardous materials classes 1-9
  Handling    (dtc_hdl*)  - special handling requirements
  Regulatory  (dtc_reg*)  - regulatory/permit categories

Source: NMFC commodity code patterns + DOT hazmat classes. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_cargo import (
    CARGO_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_cargo,
)


class TestDetermineLevel:
    def test_commodity_category_is_level_1(self):
        assert _determine_level("dtc_com") == 1

    def test_commodity_type_is_level_2(self):
        assert _determine_level("dtc_com_general") == 2

    def test_hazmat_category_is_level_1(self):
        assert _determine_level("dtc_haz") == 1

    def test_hazmat_class_is_level_2(self):
        assert _determine_level("dtc_haz_1") == 2

    def test_handling_category_is_level_1(self):
        assert _determine_level("dtc_hdl") == 1

    def test_handling_type_is_level_2(self):
        assert _determine_level("dtc_hdl_temp") == 2


class TestDetermineParent:
    def test_commodity_category_has_no_parent(self):
        assert _determine_parent("dtc_com") is None

    def test_commodity_type_parent_is_com(self):
        assert _determine_parent("dtc_com_general") == "dtc_com"

    def test_hazmat_class_parent_is_haz(self):
        assert _determine_parent("dtc_haz_1") == "dtc_haz"

    def test_handling_type_parent_is_hdl(self):
        assert _determine_parent("dtc_hdl_temp") == "dtc_hdl"


class TestCargoNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(CARGO_NODES) > 0

    def test_has_commodity_category(self):
        codes = [n[0] for n in CARGO_NODES]
        assert "dtc_com" in codes

    def test_has_hazmat_category(self):
        codes = [n[0] for n in CARGO_NODES]
        assert "dtc_haz" in codes

    def test_has_handling_category(self):
        codes = [n[0] for n in CARGO_NODES]
        assert "dtc_hdl" in codes

    def test_has_hazmat_class_1_explosives(self):
        codes = [n[0] for n in CARGO_NODES]
        assert "dtc_haz_1" in codes

    def test_has_hazmat_class_9(self):
        codes = [n[0] for n in CARGO_NODES]
        assert "dtc_haz_9" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in CARGO_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in CARGO_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in CARGO_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in CARGO_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(CARGO_NODES) >= 30


def test_domain_truck_cargo_module_importable():
    assert callable(ingest_domain_truck_cargo)
    assert isinstance(CARGO_NODES, list)


def test_ingest_domain_truck_cargo(db_pool):
    """Integration test: cargo taxonomy rows + NAICS links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_cargo(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_cargo'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_cargo'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_cargo_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_cargo(conn)
            count2 = await ingest_domain_truck_cargo(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
