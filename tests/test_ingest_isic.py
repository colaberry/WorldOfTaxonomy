"""Tests for ISIC Rev 4 ingester.

Retroactive TDD — covering the unit logic and integration behavior
that should have been tested before implementation.
"""

import asyncio
import pytest

from world_of_taxanomy.ingest.isic import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    ISIC_SECTION_DIVISIONS,
    _DIV_TO_SECTION,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _determine_level ──────────────────────────────


class TestIsicDetermineLevel:
    def test_letter_section_is_level_0(self):
        assert _determine_level("A") == 0
        assert _determine_level("Q") == 0
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


# ── Unit tests: _determine_parent ─────────────────────────────


class TestIsicDetermineParent:
    def test_section_has_no_parent(self):
        assert _determine_parent("A") is None
        assert _determine_parent("Q") is None

    def test_division_parent_is_section(self):
        assert _determine_parent("01") == "A"
        assert _determine_parent("86") == "Q"
        assert _determine_parent("10") == "C"  # Manufacturing

    def test_group_parent_is_division(self):
        assert _determine_parent("011") == "01"
        assert _determine_parent("862") == "86"

    def test_class_parent_is_group(self):
        assert _determine_parent("0111") == "011"
        assert _determine_parent("8620") == "862"


# ── Unit tests: _determine_sector ─────────────────────────────


class TestIsicDetermineSector:
    def test_section_is_its_own_sector(self):
        assert _determine_sector("A") == "A"
        assert _determine_sector("Q") == "Q"

    def test_deep_code_resolves_to_section(self):
        assert _determine_sector("0111") == "A"
        assert _determine_sector("8620") == "Q"
        assert _determine_sector("10") == "C"

    def test_all_sections_covered(self):
        """Every division in the mapping should resolve to a valid section."""
        for div_num, section in _DIV_TO_SECTION.items():
            code = str(div_num).zfill(2)
            assert _determine_sector(code) == section, f"Division {code} should map to section {section}"


# ── Unit tests: section-division mapping ──────────────────────


class TestIsicSectionDivisions:
    def test_all_21_sections_present(self):
        """ISIC Rev 4 has 21 sections (A through U)."""
        expected = set("ABCDEFGHIJKLMNOPQRSTU")
        assert set(ISIC_SECTION_DIVISIONS.keys()) == expected

    def test_no_division_gaps(self):
        """Divisions 01-99 should be fully covered with no overlaps."""
        all_divs = []
        for divs in ISIC_SECTION_DIVISIONS.values():
            all_divs.extend(divs)
        # Check no duplicates
        assert len(all_divs) == len(set(all_divs)), "Division overlap detected"
        # Check coverage: 1 through 99
        assert min(all_divs) == 1
        assert max(all_divs) == 99

    def test_reverse_lookup_complete(self):
        """Every division should have a reverse lookup entry."""
        for section, divs in ISIC_SECTION_DIVISIONS.items():
            for d in divs:
                assert _DIV_TO_SECTION[d] == section


# ── Integration test: full ingestion ──────────────────────────


def test_ingest_isic_rev4_from_real_file(db_pool):
    """Integration test: ingest from the real UN text file.

    Skips if the data file hasn't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.isic import ingest_isic_rev4, _get_project_root

    txt_path = _get_project_root() / "data/isic/ISIC_Rev_4_structure.txt"
    if not txt_path.exists():
        pytest.skip("ISIC data file not downloaded — run 'python -m world_of_taxanomy ingest isic' first")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing seed data for clean ingestion
            await conn.execute("DELETE FROM equivalence")
            await conn.execute("DELETE FROM classification_node WHERE system_id = 'isic_rev4'")
            await conn.execute("DELETE FROM classification_system WHERE id = 'isic_rev4'")

            count = await ingest_isic_rev4(conn, file_path=txt_path)

            # Should have ~600+ codes
            assert count > 600, f"Expected 600+ ISIC codes, got {count}"

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'isic_rev4'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Verify all 21 sections exist
            sections = await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id = 'isic_rev4' AND level = 0"
            )
            section_codes = {r["code"] for r in sections}
            expected_sections = set("ABCDEFGHIJKLMNOPQRSTU")
            assert section_codes == expected_sections, f"Missing sections: {expected_sections - section_codes}"

            # Verify hierarchy: division 86 should have parent Q
            node_86 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'isic_rev4' AND code = '86'"
            )
            assert node_86 is not None
            assert node_86["parent_code"] == "Q"

            # Verify leaf nodes exist
            leaf_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'isic_rev4' AND is_leaf = TRUE"
            )
            assert leaf_count > 0, "Should have leaf nodes"

    _run(_test())
