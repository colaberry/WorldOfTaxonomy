"""Tests for Mining Project Lifecycle Phase domain taxonomy ingester.

RED tests - written before any implementation exists.

Mining Lifecycle taxonomy classifies what stage of its operational life a
mine is in - orthogonal to mineral type, extraction method, reserve
classification, and equipment. A copper mine and a gold mine both pass
through greenfield exploration, feasibility, development, production,
and eventually closure - different asset values, regulatory obligations,
and workforce compositions at each stage.

Code prefix: dmlc_
Categories: Exploration and Discovery, Feasibility and Permitting,
Development and Construction, Operations and Production, Care and
Maintenance, Closure and Rehabilitation.

Stakeholders: mining project finance lenders (IFC, export credit agencies),
ESG investors tracking mine lifecycle risk, government permitting agencies,
mine rehabilitation bond administrators, royalty streaming companies.
Source: JORC Code lifecycle phases, IFC Performance Standards on mining,
MAC (Mining Association of Canada) lifecycle guidance. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mining_lifecycle import (
    MINING_LIFECYCLE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mining_lifecycle,
)


class TestDetermineLevel:
    def test_exploration_category_is_level_1(self):
        assert _determine_level("dmlc_explore") == 1

    def test_grassroots_is_level_2(self):
        assert _determine_level("dmlc_explore_grass") == 2

    def test_production_category_is_level_1(self):
        assert _determine_level("dmlc_produce") == 1

    def test_ramp_up_is_level_2(self):
        assert _determine_level("dmlc_produce_ramp") == 2

    def test_closure_category_is_level_1(self):
        assert _determine_level("dmlc_closure") == 1


class TestDetermineParent:
    def test_explore_category_has_no_parent(self):
        assert _determine_parent("dmlc_explore") is None

    def test_grassroots_parent_is_explore(self):
        assert _determine_parent("dmlc_explore_grass") == "dmlc_explore"

    def test_ramp_parent_is_produce(self):
        assert _determine_parent("dmlc_produce_ramp") == "dmlc_produce"

    def test_rehab_parent_is_closure(self):
        assert _determine_parent("dmlc_closure_rehab") == "dmlc_closure"


class TestMiningLifecycleNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(MINING_LIFECYCLE_NODES) > 0

    def test_has_exploration_category(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_explore" in codes

    def test_has_feasibility_category(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_feasibility" in codes

    def test_has_development_category(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_develop" in codes

    def test_has_production_category(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_produce" in codes

    def test_has_closure_category(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_closure" in codes

    def test_has_grassroots_node(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_explore_grass" in codes

    def test_has_ramp_up_node(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert "dmlc_produce_ramp" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MINING_LIFECYCLE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MINING_LIFECYCLE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MINING_LIFECYCLE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MINING_LIFECYCLE_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(MINING_LIFECYCLE_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in MINING_LIFECYCLE_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_mining_lifecycle_module_importable():
    assert callable(ingest_domain_mining_lifecycle)
    assert isinstance(MINING_LIFECYCLE_NODES, list)


def test_ingest_domain_mining_lifecycle(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mining_lifecycle(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mining_lifecycle'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_mining_lifecycle'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mining_lifecycle_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mining_lifecycle(conn)
            count2 = await ingest_domain_mining_lifecycle(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
