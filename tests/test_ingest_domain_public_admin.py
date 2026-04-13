"""Tests for domain_public_admin ingester (Phase 27 - NAICS 92)."""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.domain_public_admin import (
    PUBLIC_ADMIN_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_public_admin,
)


class TestPublicAdminDetermineLevel:
    def test_top_level_category(self):
        assert _determine_level("dpa_level") == 1

    def test_sub_level_node(self):
        assert _determine_level("dpa_level_federal") == 2

    def test_another_top_level(self):
        assert _determine_level("dpa_func") == 1

    def test_another_sub_level(self):
        assert _determine_level("dpa_func_defense") == 2

    def test_agency_top(self):
        assert _determine_level("dpa_agency") == 1

    def test_agency_sub(self):
        assert _determine_level("dpa_agency_exec") == 2


class TestPublicAdminDetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("dpa_level") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("dpa_level_federal") == "dpa_level"

    def test_another_top_level_none(self):
        assert _determine_parent("dpa_func") is None

    def test_another_sub_returns_parent(self):
        assert _determine_parent("dpa_func_defense") == "dpa_func"

    def test_agency_sub_returns_parent(self):
        assert _determine_parent("dpa_agency_exec") == "dpa_agency"

    def test_proc_sub_returns_parent(self):
        assert _determine_parent("dpa_proc_rulemaking") == "dpa_proc"


class TestPublicAdminNodes:
    def test_nodes_is_list(self):
        assert isinstance(PUBLIC_ADMIN_NODES, list)

    def test_at_least_15_nodes(self):
        assert len(PUBLIC_ADMIN_NODES) >= 15

    def test_all_tuples_four_elements(self):
        for node in PUBLIC_ADMIN_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in PUBLIC_ADMIN_NODES:
            if level == 1:
                assert parent is None, f"{code} level 1 should have no parent"

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in PUBLIC_ADMIN_NODES:
            if level == 2:
                assert parent is not None, f"{code} level 2 should have a parent"

    def test_no_em_dashes(self):
        for code, title, _level, _parent in PUBLIC_ADMIN_NODES:
            assert "\u2014" not in title, f"em-dash found in title: {title}"
            assert "\u2014" not in code, f"em-dash found in code: {code}"


def test_ingest_domain_public_admin(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_public_admin(conn)
            assert count == len(PUBLIC_ADMIN_NODES)
            assert count >= 15
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_public_admin'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_public_admin_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_public_admin(conn)
            count2 = await ingest_domain_public_admin(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
