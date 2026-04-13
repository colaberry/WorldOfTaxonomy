"""Tests for domain_wholesale_channel ingester (Phase 15 - NAICS 42)."""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.domain_wholesale_channel import (
    WHOLESALE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_wholesale_channel,
)


class TestWholesaleDetermineLevel:
    def test_top_level_category(self):
        assert _determine_level("dwc_dist") == 1

    def test_sub_level_node(self):
        assert _determine_level("dwc_dist_direct") == 2

    def test_another_top_level(self):
        assert _determine_level("dwc_fulfill") == 1

    def test_another_sub_level(self):
        assert _determine_level("dwc_fulfill_3pl") == 2

    def test_buyer_top(self):
        assert _determine_level("dwc_buyer") == 1

    def test_buyer_sub(self):
        assert _determine_level("dwc_buyer_retail") == 2


class TestWholesaleDetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("dwc_dist") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("dwc_dist_direct") == "dwc_dist"

    def test_another_top_level_none(self):
        assert _determine_parent("dwc_fulfill") is None

    def test_another_sub_returns_parent(self):
        assert _determine_parent("dwc_fulfill_3pl") == "dwc_fulfill"

    def test_buyer_sub_returns_parent(self):
        assert _determine_parent("dwc_buyer_retail") == "dwc_buyer"

    def test_channel_sub_returns_parent(self):
        assert _determine_parent("dwc_cold_fresh") == "dwc_cold"


class TestWholesaleNodes:
    def test_nodes_is_list(self):
        assert isinstance(WHOLESALE_NODES, list)

    def test_at_least_15_nodes(self):
        assert len(WHOLESALE_NODES) >= 15

    def test_all_tuples_four_elements(self):
        for node in WHOLESALE_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in WHOLESALE_NODES:
            if level == 1:
                assert parent is None, f"{code} level 1 should have no parent"

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in WHOLESALE_NODES:
            if level == 2:
                assert parent is not None, f"{code} level 2 should have a parent"

    def test_no_em_dashes(self):
        for code, title, _level, _parent in WHOLESALE_NODES:
            assert "\u2014" not in title, f"em-dash found in title: {title}"
            assert "\u2014" not in code, f"em-dash found in code: {code}"


def test_ingest_domain_wholesale_channel(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_wholesale_channel(conn)
            assert count == len(WHOLESALE_NODES)
            assert count >= 15
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_wholesale_channel'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_wholesale_channel_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_wholesale_channel(conn)
            count2 = await ingest_domain_wholesale_channel(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
