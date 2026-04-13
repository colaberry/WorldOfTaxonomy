"""Tests for domain_arts_content ingester (Phase 24 - NAICS 71)."""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.domain_arts_content import (
    ARTS_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_arts_content,
)


class TestArtsDetermineLevel:
    def test_top_level_category(self):
        assert _determine_level("dac_content") == 1

    def test_sub_level_node(self):
        assert _determine_level("dac_content_film") == 2

    def test_another_top_level(self):
        assert _determine_level("dac_venue") == 1

    def test_another_sub_level(self):
        assert _determine_level("dac_venue_theater") == 2

    def test_rights_top(self):
        assert _determine_level("dac_rights") == 1

    def test_rights_sub(self):
        assert _determine_level("dac_rights_sync") == 2


class TestArtsDetermineParent:
    def test_top_level_has_no_parent(self):
        assert _determine_parent("dac_content") is None

    def test_sub_level_returns_parent(self):
        assert _determine_parent("dac_content_film") == "dac_content"

    def test_another_top_level_none(self):
        assert _determine_parent("dac_venue") is None

    def test_another_sub_returns_parent(self):
        assert _determine_parent("dac_venue_theater") == "dac_venue"

    def test_rights_sub_returns_parent(self):
        assert _determine_parent("dac_rights_sync") == "dac_rights"

    def test_format_sub_returns_parent(self):
        assert _determine_parent("dac_format_live") == "dac_format"


class TestArtsNodes:
    def test_nodes_is_list(self):
        assert isinstance(ARTS_NODES, list)

    def test_at_least_15_nodes(self):
        assert len(ARTS_NODES) >= 15

    def test_all_tuples_four_elements(self):
        for node in ARTS_NODES:
            assert len(node) == 4

    def test_top_level_nodes_have_no_parent(self):
        for code, _title, level, parent in ARTS_NODES:
            if level == 1:
                assert parent is None, f"{code} level 1 should have no parent"

    def test_sub_nodes_have_parent(self):
        for code, _title, level, parent in ARTS_NODES:
            if level == 2:
                assert parent is not None, f"{code} level 2 should have a parent"

    def test_no_em_dashes(self):
        for code, title, _level, _parent in ARTS_NODES:
            assert "\u2014" not in title, f"em-dash found in title: {title}"
            assert "\u2014" not in code, f"em-dash found in code: {code}"


def test_ingest_domain_arts_content(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_arts_content(conn)
            assert count == len(ARTS_NODES)
            assert count >= 15
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_arts_content'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_arts_content_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_arts_content(conn)
            count2 = await ingest_domain_arts_content(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
