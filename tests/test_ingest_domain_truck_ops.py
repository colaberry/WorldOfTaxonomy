"""Tests for Truck Carrier Operations domain taxonomy ingester.

RED tests - written before any implementation exists.

Operations taxonomy covers:
  Carrier Type  (dto_type*)  - for-hire, private, owner-operator, broker
  Fleet Size    (dto_fleet*)  - fleet size tiers
  Business Model (dto_biz*)  - dispatch model, contract type
  Route         (dto_route*) - route pattern, geographic scope

Source: FMCSA carrier classification. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_ops import (
    OPS_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_ops,
)


class TestDetermineLevel:
    def test_type_category_is_level_1(self):
        assert _determine_level("dto_type") == 1

    def test_type_subtype_is_level_2(self):
        assert _determine_level("dto_type_forhire") == 2

    def test_fleet_category_is_level_1(self):
        assert _determine_level("dto_fleet") == 1

    def test_fleet_size_is_level_2(self):
        assert _determine_level("dto_fleet_small") == 2

    def test_biz_category_is_level_1(self):
        assert _determine_level("dto_biz") == 1

    def test_biz_type_is_level_2(self):
        assert _determine_level("dto_biz_dedicated") == 2


class TestDetermineParent:
    def test_type_category_has_no_parent(self):
        assert _determine_parent("dto_type") is None

    def test_type_subtype_parent_is_type(self):
        assert _determine_parent("dto_type_forhire") == "dto_type"

    def test_fleet_size_parent_is_fleet(self):
        assert _determine_parent("dto_fleet_small") == "dto_fleet"

    def test_biz_type_parent_is_biz(self):
        assert _determine_parent("dto_biz_dedicated") == "dto_biz"


class TestOpsNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(OPS_NODES) > 0

    def test_has_type_category(self):
        codes = [n[0] for n in OPS_NODES]
        assert "dto_type" in codes

    def test_has_fleet_category(self):
        codes = [n[0] for n in OPS_NODES]
        assert "dto_fleet" in codes

    def test_has_forhire_type(self):
        codes = [n[0] for n in OPS_NODES]
        assert "dto_type_forhire" in codes

    def test_has_owner_operator(self):
        codes = [n[0] for n in OPS_NODES]
        assert "dto_type_owner_op" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in OPS_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in OPS_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in OPS_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in OPS_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(OPS_NODES) >= 20


def test_domain_truck_ops_module_importable():
    assert callable(ingest_domain_truck_ops)
    assert isinstance(OPS_NODES, list)


def test_ingest_domain_truck_ops(db_pool):
    """Integration test: ops taxonomy rows + NAICS links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_ops(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_ops'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_ops'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_ops_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_ops(conn)
            count2 = await ingest_domain_truck_ops(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
