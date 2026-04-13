"""Tests for domain_education_type ingester (Phase 22 - NAICS 61)."""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.domain_education_type import (
    EDUCATION_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_education_type,
)


class TestEducationDetermineLevel:
    def test_top_level_category(self):
        assert _determine_level("det_prog") == 1

    def test_sub_level_node(self):
        assert _determine_level("det_prog_k12") == 2

    def test_another_top_level(self):
        assert _determine_level("det_delivery") == 1

    def test_another_sub_level(self):
        assert _determine_level("det_delivery_online") == 2

    def test_cred_top(self):
        assert _determine_level("det_cred") == 1

    def test_cred_sub(self):
        assert _determine_level("det_cred_degree") == 2


class TestEducationDetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("det_prog") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("det_prog_k12") == "det_prog"

    def test_another_top_level_none(self):
        assert _determine_parent("det_delivery") is None

    def test_another_sub_returns_parent(self):
        assert _determine_parent("det_delivery_online") == "det_delivery"

    def test_cred_sub_returns_parent(self):
        assert _determine_parent("det_cred_degree") == "det_cred"

    def test_accred_sub_returns_parent(self):
        assert _determine_parent("det_accred_regional") == "det_accred"


class TestEducationNodes:
    def test_nodes_is_list(self):
        assert isinstance(EDUCATION_NODES, list)

    def test_at_least_15_nodes(self):
        assert len(EDUCATION_NODES) >= 15

    def test_all_tuples_four_elements(self):
        for node in EDUCATION_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in EDUCATION_NODES:
            if level == 1:
                assert parent is None, f"{code} level 1 should have no parent"

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in EDUCATION_NODES:
            if level == 2:
                assert parent is not None, f"{code} level 2 should have a parent"

    def test_no_em_dashes(self):
        for code, title, _level, _parent in EDUCATION_NODES:
            assert "\u2014" not in title, f"em-dash found in title: {title}"
            assert "\u2014" not in code, f"em-dash found in code: {code}"


def test_ingest_domain_education_type(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_education_type(conn)
            assert count == len(EDUCATION_NODES)
            assert count >= 15
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_education_type'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_education_type_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_education_type(conn)
            count2 = await ingest_domain_education_type(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
