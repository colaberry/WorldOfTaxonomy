"""Tests for CFR Title 49 ingester.

RED tests - written before any implementation exists.

CFR Title 49 = Code of Federal Regulations, Title 49 (Transportation).
Published by the US Government (ecfr.gov). Public domain.

Hierarchy (3 levels):
  Part      (level 1, e.g. '49_1')    - top-level part number
  Subpart   (level 2, e.g. '49_1_A')  - subpart letter
  Section   (level 3, e.g. '49_1_1')  - specific section (leaf)

Hand-coded: the most important parts of Title 49 related to transportation
safety, hours of service, vehicle standards, and hazmat.

Codes use underscores: '49_{part}', '49_{part}_{subpart}', '49_{part}_{section}'

Source: https://www.ecfr.gov/current/title-49 (public domain)
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.cfr_title49 import (
    CFR49_NODES,
    _determine_level,
    _determine_parent,
    ingest_cfr_title49,
)


class TestDetermineLevel:
    def test_part_only_is_level_1(self):
        # '49_395' = Title 49, Part 395 (Hours of Service)
        assert _determine_level("49_395") == 1

    def test_part_subpart_is_level_2(self):
        # '49_395_A' = Title 49, Part 395, Subpart A
        assert _determine_level("49_395_A") == 2

    def test_section_is_level_3(self):
        # '49_395_1' = Title 49, Part 395, Section 1
        assert _determine_level("49_395_1") == 3

    def test_another_part_is_level_1(self):
        assert _determine_level("49_382") == 1

    def test_section_with_letter_subpart(self):
        # Subpart code ends in a single uppercase letter
        assert _determine_level("49_382_B") == 2


class TestDetermineParent:
    def test_part_has_no_parent(self):
        assert _determine_parent("49_395") is None

    def test_subpart_parent_is_part(self):
        assert _determine_parent("49_395_A") == "49_395"

    def test_section_parent_is_part(self):
        # Sections belong directly to their part (or subpart if one exists)
        parent = _determine_parent("49_395_1")
        assert parent == "49_395"

    def test_another_part_no_parent(self):
        assert _determine_parent("49_382") is None


class TestCfr49Nodes:
    def test_nodes_list_is_non_empty(self):
        assert len(CFR49_NODES) > 0

    def test_all_codes_start_with_49(self):
        for code, title, level, parent in CFR49_NODES:
            assert code.startswith("49_"), f"Code '{code}' does not start with '49_'"

    def test_all_titles_non_empty(self):
        for code, title, level, parent in CFR49_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in CFR49_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_nodes_have_no_parent(self):
        for code, title, level, parent in CFR49_NODES:
            if level == 1:
                assert parent is None, f"Level 1 code '{code}' has parent '{parent}'"

    def test_level_2_and_3_nodes_have_parent(self):
        for code, title, level, parent in CFR49_NODES:
            if level > 1:
                assert parent is not None, f"Level {level} code '{code}' has no parent"


def test_cfr_title49_module_importable():
    assert callable(ingest_cfr_title49)
    assert isinstance(CFR49_NODES, list)


def test_ingest_cfr_title49(db_pool):
    """Integration test: ingest CFR Title 49 nodes."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_cfr_title49(conn)
            assert count > 0, "Expected at least 1 CFR Title 49 node"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system "
                "WHERE id = 'cfr_title_49'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Part-level node: level=1, no parent
            part = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf "
                "FROM classification_node "
                "WHERE system_id = 'cfr_title_49' AND level = 1 "
                "LIMIT 1"
            )
            assert part is not None
            assert part["level"] == 1
            assert part["parent_code"] is None

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_cfr_title49_idempotent(db_pool):
    """Running ingest twice returns the same count."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_cfr_title49(conn)
            count2 = await ingest_cfr_title49(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
