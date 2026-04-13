"""Tests for domain_other_services ingester (Phase 26 - NAICS 81)."""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.domain_other_services import (
    OTHER_SVC_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_other_services,
)


class TestOtherSvcDetermineLevel:
    def test_top_level_category(self):
        assert _determine_level("dos_cat") == 1

    def test_sub_level_node(self):
        assert _determine_level("dos_cat_repair") == 2

    def test_another_top_level(self):
        assert _determine_level("dos_segment") == 1

    def test_another_sub_level(self):
        assert _determine_level("dos_segment_consumer") == 2

    def test_appt_top(self):
        assert _determine_level("dos_appt") == 1

    def test_appt_sub(self):
        assert _determine_level("dos_appt_walkin") == 2


class TestOtherSvcDetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("dos_cat") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("dos_cat_repair") == "dos_cat"

    def test_another_top_level_none(self):
        assert _determine_parent("dos_segment") is None

    def test_another_sub_returns_parent(self):
        assert _determine_parent("dos_segment_consumer") == "dos_segment"

    def test_appt_sub_returns_parent(self):
        assert _determine_parent("dos_appt_walkin") == "dos_appt"

    def test_cert_sub_returns_parent(self):
        assert _determine_parent("dos_cert_licensed") == "dos_cert"


class TestOtherSvcNodes:
    def test_nodes_is_list(self):
        assert isinstance(OTHER_SVC_NODES, list)

    def test_at_least_15_nodes(self):
        assert len(OTHER_SVC_NODES) >= 15

    def test_all_tuples_four_elements(self):
        for node in OTHER_SVC_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in OTHER_SVC_NODES:
            if level == 1:
                assert parent is None, f"{code} level 1 should have no parent"

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in OTHER_SVC_NODES:
            if level == 2:
                assert parent is not None, f"{code} level 2 should have a parent"

    def test_no_em_dashes(self):
        for code, title, _level, _parent in OTHER_SVC_NODES:
            assert "\u2014" not in title, f"em-dash found in title: {title}"
            assert "\u2014" not in code, f"em-dash found in code: {code}"


def test_ingest_domain_other_services(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_other_services(conn)
            assert count == len(OTHER_SVC_NODES)
            assert count >= 15
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_other_services'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_other_services_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_other_services(conn)
            count2 = await ingest_domain_other_services(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
