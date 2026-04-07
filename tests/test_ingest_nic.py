"""Tests for NIC 2008 ingester.

Covers unit logic for level/parent/sector determination and
integration test with the real Excel data file.
"""

import asyncio
import pytest

from world_of_taxanomy.ingest.nic import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    SECTION_NAMES,
)
from world_of_taxanomy.ingest.isic import _DIV_TO_SECTION


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _determine_level ──────────────────────────────


class TestNicDetermineLevel:
    def test_letter_section_is_level_0(self):
        assert _determine_level("A") == 0
        assert _determine_level("C") == 0
        assert _determine_level("U") == 0

    def test_two_digit_division_is_level_1(self):
        assert _determine_level("01") == 1
        assert _determine_level("86") == 1

    def test_three_digit_group_is_level_2(self):
        assert _determine_level("011") == 2
        assert _determine_level("862") == 2

    def test_four_digit_class_is_level_3(self):
        assert _determine_level("0111") == 3
        assert _determine_level("8620") == 3

    def test_five_digit_subclass_is_level_4(self):
        """NIC adds a 5th digit for India-specific sub-classes."""
        assert _determine_level("01111") == 4
        assert _determine_level("86201") == 4


# ── Unit tests: _determine_parent ─────────────────────────────


class TestNicDetermineParent:
    def test_section_has_no_parent(self):
        assert _determine_parent("A") is None
        assert _determine_parent("Q") is None

    def test_division_parent_is_section(self):
        assert _determine_parent("01") == "A"
        assert _determine_parent("86") == "Q"
        assert _determine_parent("10") == "C"

    def test_group_parent_is_division(self):
        assert _determine_parent("011") == "01"
        assert _determine_parent("862") == "86"

    def test_class_parent_is_group(self):
        assert _determine_parent("0111") == "011"
        assert _determine_parent("8620") == "862"

    def test_subclass_parent_is_class(self):
        """5-digit sub-class parent should be the 4-digit class."""
        assert _determine_parent("01111") == "0111"
        assert _determine_parent("86201") == "8620"


# ── Unit tests: _determine_sector ─────────────────────────────


class TestNicDetermineSector:
    def test_section_is_its_own_sector(self):
        assert _determine_sector("A") == "A"
        assert _determine_sector("Q") == "Q"

    def test_deep_code_resolves_to_section(self):
        assert _determine_sector("0111") == "A"
        assert _determine_sector("8620") == "Q"
        assert _determine_sector("10") == "C"

    def test_five_digit_resolves_to_section(self):
        assert _determine_sector("01111") == "A"
        assert _determine_sector("86201") == "Q"

    def test_all_divisions_resolve(self):
        """Every division in the mapping should resolve to a valid section."""
        for div_num, section in _DIV_TO_SECTION.items():
            code = str(div_num).zfill(2)
            assert _determine_sector(code) == section


# ── Unit tests: section names ─────────────────────────────────


class TestNicSectionNames:
    def test_all_21_sections_have_names(self):
        expected = set("ABCDEFGHIJKLMNOPQRSTU")
        assert set(SECTION_NAMES.keys()) == expected

    def test_section_names_non_empty(self):
        for section, name in SECTION_NAMES.items():
            assert len(name) > 0, f"Section {section} has empty name"


# ── Integration test: full ingestion ──────────────────────────


def test_ingest_nic_2008_from_real_file(db_pool):
    """Integration test: ingest from the real MOSPI Excel file.

    Skips if the data file hasn't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.nic import ingest_nic_2008, _get_project_root

    xlsx_path = _get_project_root() / "data/nic/NIC_2008.xlsx"
    if not xlsx_path.exists():
        pytest.skip("NIC data file not downloaded — run ingest first")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing data for clean ingestion
            await conn.execute("DELETE FROM equivalence")
            await conn.execute("DELETE FROM classification_node WHERE system_id = 'nic_2008'")
            await conn.execute("DELETE FROM classification_system WHERE id = 'nic_2008'")

            count = await ingest_nic_2008(conn, xlsx_path=xlsx_path)

            # Should have 2049 numeric codes + 21 section nodes = ~2070
            assert count > 2000, f"Expected 2000+ NIC codes, got {count}"

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'nic_2008'"
            )
            assert row is not None
            assert row["node_count"] == count
            assert row["tint_color"] == "#FF6B35"

            # Verify all 21 sections exist
            sections = await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id = 'nic_2008' AND level = 0"
            )
            section_codes = {r["code"] for r in sections}
            expected_sections = set("ABCDEFGHIJKLMNOPQRSTU")
            assert section_codes == expected_sections, (
                f"Missing sections: {expected_sections - section_codes}"
            )

            # Verify hierarchy: division 01 should have parent A
            node_01 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'nic_2008' AND code = '01'"
            )
            assert node_01 is not None
            assert node_01["parent_code"] == "A"
            assert node_01["level"] == 1

            # Verify 5-digit sub-class nodes exist at level 4
            subclass_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'nic_2008' AND level = 4"
            )
            assert subclass_count > 1000, f"Expected 1000+ sub-class codes, got {subclass_count}"

            # Verify leaf nodes exist
            leaf_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'nic_2008' AND is_leaf = TRUE"
            )
            assert leaf_count > 0, "Should have leaf nodes"

            # Verify sector_code is always a section letter
            bad_sectors = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'nic_2008' AND sector_code NOT IN ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U')"
            )
            assert bad_sectors == 0, f"Found {bad_sectors} nodes with invalid sector codes"

    _run(_test())
