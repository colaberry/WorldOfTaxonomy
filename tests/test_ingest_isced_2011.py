"""Tests for ISCED 2011 ingester (Phase 4-A).

ISCED 2011: International Standard Classification of Education, 2011 edition.
UNESCO. 9 levels (0-8) with sub-categories. ~25 codes total.
Hand-coded (no download required).
"""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.isced_2011 import (
    ISCED_NODES,
    _determine_level,
    _determine_parent,
    ingest_isced_2011,
)


class TestIsced2011DetermineLevel:
    def test_level_0_is_level_1(self):
        assert _determine_level("ISCED0") == 1

    def test_sub_level_is_2(self):
        assert _determine_level("ISCED0a") == 2

    def test_level_8_is_level_1(self):
        assert _determine_level("ISCED8") == 1

    def test_another_sub_level(self):
        assert _determine_level("ISCED3b") == 2


class TestIsced2011DetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("ISCED0") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("ISCED0a") == "ISCED0"

    def test_level_8_no_parent(self):
        assert _determine_parent("ISCED8") is None

    def test_level_3_sub_returns_parent(self):
        assert _determine_parent("ISCED3a") == "ISCED3"


class TestIsced2011Nodes:
    def test_nodes_is_list(self):
        assert isinstance(ISCED_NODES, list)

    def test_at_least_9_levels(self):
        top = [n for n in ISCED_NODES if _determine_parent(n[0]) is None]
        assert len(top) >= 9

    def test_all_tuples_four_elements(self):
        for node in ISCED_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in ISCED_NODES:
            if level == 1:
                assert parent is None

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in ISCED_NODES:
            if level == 2:
                assert parent is not None

    def test_no_em_dashes(self):
        for code, title, _level, _parent in ISCED_NODES:
            assert "\u2014" not in title


def test_ingest_isced_2011(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_isced_2011(conn)
            assert count >= 9
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'isced_2011'"
            )
            assert row is not None
            assert row["node_count"] == count
            # Check a known level
            node = await conn.fetchrow(
                "SELECT code, title FROM classification_node "
                "WHERE system_id = 'isced_2011' AND code = 'ISCED8'"
            )
            assert node is not None
            assert "Doctoral" in node["title"] or "doctoral" in node["title"].lower()
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_isced_2011_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_isced_2011(conn)
            count2 = await ingest_isced_2011(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
