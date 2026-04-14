"""Tests for Arts and Entertainment Creator and Rights Holder Structure Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_arts_creator import (
    ARTS_CREATOR_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_arts_creator,
)


class TestDetermineLevel:
    def test_major_category_is_level_1(self):
        assert _determine_level("dacstruct_major") == 1

    def test_label_is_level_2(self):
        assert _determine_level("dacstruct_major_label") == 2

    def test_indie_category_is_level_1(self):
        assert _determine_level("dacstruct_indie") == 1


class TestDetermineParent:
    def test_major_has_no_parent(self):
        assert _determine_parent("dacstruct_major") is None

    def test_label_parent_is_major(self):
        assert _determine_parent("dacstruct_major_label") == "dacstruct_major"

    def test_label_parent_is_indie(self):
        assert _determine_parent("dacstruct_indie_label") == "dacstruct_indie"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(ARTS_CREATOR_NODES) > 0

    def test_has_major_category(self):
        codes = [n[0] for n in ARTS_CREATOR_NODES]
        assert "dacstruct_major" in codes

    def test_has_indie_category(self):
        codes = [n[0] for n in ARTS_CREATOR_NODES]
        assert "dacstruct_indie" in codes

    def test_has_self_category(self):
        codes = [n[0] for n in ARTS_CREATOR_NODES]
        assert "dacstruct_self" in codes

    def test_has_label_node(self):
        codes = [n[0] for n in ARTS_CREATOR_NODES]
        assert "dacstruct_major_label" in codes

    def test_has_label_node(self):
        codes = [n[0] for n in ARTS_CREATOR_NODES]
        assert "dacstruct_indie_label" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in ARTS_CREATOR_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in ARTS_CREATOR_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in ARTS_CREATOR_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in ARTS_CREATOR_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(ARTS_CREATOR_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in ARTS_CREATOR_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_arts_creator)
    assert isinstance(ARTS_CREATOR_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_arts_creator(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_arts_creator'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_arts_creator(conn)
            count2 = await ingest_domain_arts_creator(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
