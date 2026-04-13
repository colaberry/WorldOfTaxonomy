"""Tests for domain_prof_services ingester (Phase 21 - NAICS 54)."""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.domain_prof_services import (
    PROF_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_prof_services,
)


class TestProfDetermineLevel:
    def test_top_level_category(self):
        assert _determine_level("dps_line") == 1

    def test_sub_level_node(self):
        assert _determine_level("dps_line_legal") == 2

    def test_another_top_level(self):
        assert _determine_level("dps_engage") == 1

    def test_another_sub_level(self):
        assert _determine_level("dps_engage_project") == 2

    def test_billing_top(self):
        assert _determine_level("dps_bill") == 1

    def test_billing_sub(self):
        assert _determine_level("dps_bill_hourly") == 2


class TestProfDetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("dps_line") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("dps_line_legal") == "dps_line"

    def test_another_top_level_none(self):
        assert _determine_parent("dps_engage") is None

    def test_another_sub_returns_parent(self):
        assert _determine_parent("dps_engage_project") == "dps_engage"

    def test_billing_sub_returns_parent(self):
        assert _determine_parent("dps_bill_hourly") == "dps_bill"

    def test_cert_sub_returns_parent(self):
        assert _determine_parent("dps_cert_cpa") == "dps_cert"


class TestProfNodes:
    def test_nodes_is_list(self):
        assert isinstance(PROF_NODES, list)

    def test_at_least_15_nodes(self):
        assert len(PROF_NODES) >= 15

    def test_all_tuples_four_elements(self):
        for node in PROF_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in PROF_NODES:
            if level == 1:
                assert parent is None, f"{code} level 1 should have no parent"

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in PROF_NODES:
            if level == 2:
                assert parent is not None, f"{code} level 2 should have a parent"

    def test_no_em_dashes(self):
        for code, title, _level, _parent in PROF_NODES:
            assert "\u2014" not in title, f"em-dash found in title: {title}"
            assert "\u2014" not in code, f"em-dash found in code: {code}"


def test_ingest_domain_prof_services(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_prof_services(conn)
            assert count == len(PROF_NODES)
            assert count >= 15
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_prof_services'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_prof_services_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_prof_services(conn)
            count2 = await ingest_domain_prof_services(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
