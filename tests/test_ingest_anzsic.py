"""Tests for ANZSIC 2006 ingester.

Covers unit logic for level/parent/sector determination,
XLS parsing, and integration test with the real data file.
"""

import asyncio
import pytest

from world_of_taxanomy.ingest.anzsic import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    parse_anzsic_xls,
    SYSTEM_ID,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _determine_level ──────────────────────────────


class TestAnzsicDetermineLevel:
    def test_letter_division_is_level_0(self):
        assert _determine_level("A") == 0
        assert _determine_level("S") == 0
        assert _determine_level("M") == 0

    def test_two_digit_subdivision_is_level_1(self):
        assert _determine_level("01") == 1
        assert _determine_level("69") == 1

    def test_three_digit_group_is_level_2(self):
        assert _determine_level("011") == 2
        assert _determine_level("691") == 2

    def test_four_digit_class_is_level_3(self):
        assert _determine_level("0111") == 3
        assert _determine_level("6910") == 3

    def test_non_code_returns_negative(self):
        assert _determine_level("AB") == -1
        assert _determine_level("1A") == -1


# ── Unit tests: _determine_parent ─────────────────────────────


class TestAnzsicDetermineParent:
    def test_division_has_no_parent(self):
        assert _determine_parent("A", None, None) is None
        assert _determine_parent("S", "S", None) is None

    def test_subdivision_parent_is_division(self):
        assert _determine_parent("01", "A", None) == "A"
        assert _determine_parent("69", "M", None) == "M"

    def test_group_parent_is_subdivision(self):
        assert _determine_parent("011", "A", "01") == "01"
        assert _determine_parent("691", "M", "69") == "69"

    def test_class_parent_is_group(self):
        assert _determine_parent("0111", "A", "01") == "011"
        assert _determine_parent("6910", "M", "69") == "691"

    def test_group_parent_derived_from_code(self):
        """Group parent uses first 2 digits, not current_subdivision."""
        assert _determine_parent("012", "A", "01") == "01"
        assert _determine_parent("139", "C", "13") == "13"

    def test_class_parent_derived_from_code(self):
        """Class parent uses first 3 digits, not tracked state."""
        assert _determine_parent("0121", "A", "01") == "012"
        assert _determine_parent("1391", "C", "13") == "139"


# ── Unit tests: _determine_sector ─────────────────────────────


class TestAnzsicDetermineSector:
    def test_division_is_its_own_sector(self):
        assert _determine_sector("A", "A") == "A"
        assert _determine_sector("S", "S") == "S"

    def test_numeric_code_uses_current_division(self):
        assert _determine_sector("01", "A") == "A"
        assert _determine_sector("011", "A") == "A"
        assert _determine_sector("0111", "A") == "A"
        assert _determine_sector("69", "M") == "M"

    def test_no_division_gives_question_mark(self):
        assert _determine_sector("01", None) == "?"


# ── Unit tests: SYSTEM_ID constant ────────────────────────────


class TestAnzsicConstants:
    def test_system_id(self):
        assert SYSTEM_ID == "anzsic_2006"


# ── Integration test: XLS parsing ─────────────────────────────


def test_parse_anzsic_xls_from_real_file():
    """Test parsing the real XLS file without database.

    Skips if the data file hasn't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.anzsic import _get_project_root

    xls_path = _get_project_root() / "data/anzsic/ANZSIC_2006_codes_titles.xls"
    if not xls_path.exists():
        pytest.skip("ANZSIC data file not downloaded")

    nodes = parse_anzsic_xls(xls_path)

    # ANZSIC 2006 has 19 divisions (A-S), plus subdivisions, groups, classes
    assert len(nodes) > 400, f"Expected 400+ codes, got {len(nodes)}"

    # Extract by level
    divisions = [n for n in nodes if n[2] == 0]
    subdivisions = [n for n in nodes if n[2] == 1]
    groups = [n for n in nodes if n[2] == 2]
    classes = [n for n in nodes if n[2] == 3]

    # 19 divisions (A through S)
    assert len(divisions) == 19, f"Expected 19 divisions, got {len(divisions)}"
    div_letters = {n[0] for n in divisions}
    expected_letters = set("ABCDEFGHIJKLMNOPQRS")
    assert div_letters == expected_letters, (
        f"Missing divisions: {expected_letters - div_letters}, "
        f"Extra: {div_letters - expected_letters}"
    )

    # Should have subdivisions, groups, and classes
    assert len(subdivisions) > 50, f"Expected 50+ subdivisions, got {len(subdivisions)}"
    assert len(groups) > 100, f"Expected 100+ groups, got {len(groups)}"
    assert len(classes) > 200, f"Expected 200+ classes, got {len(classes)}"

    # Check first division: A = Agriculture, Forestry and Fishing
    first_div = nodes[0]
    assert first_div[0] == "A"
    assert "Agriculture" in first_div[1]
    assert first_div[2] == 0  # level
    assert first_div[3] is None  # parent

    # All codes should be unique
    codes = [n[0] for n in nodes]
    assert len(codes) == len(set(codes)), "Duplicate codes detected"

    # All numeric codes should have valid parents
    for code, title, level, parent, sector, seq in nodes:
        if level == 0:
            assert parent is None, f"Division {code} should have no parent"
            assert sector == code, f"Division {code} sector should be itself"
        elif level == 1:
            assert parent is not None and parent.isalpha(), (
                f"Subdivision {code} parent should be a letter, got {parent}"
            )
        elif level == 2:
            assert parent is not None and len(parent) == 2, (
                f"Group {code} parent should be 2-digit, got {parent}"
            )
        elif level == 3:
            assert parent is not None and len(parent) == 3, (
                f"Class {code} parent should be 3-digit, got {parent}"
            )

    # Sector should always be a letter
    for code, title, level, parent, sector, seq in nodes:
        assert sector.isalpha() and len(sector) == 1, (
            f"Code {code} has invalid sector: {sector}"
        )

    # Seq should be monotonically increasing
    seqs = [n[5] for n in nodes]
    assert seqs == sorted(seqs), "Sequence numbers should be monotonically increasing"
    assert seqs[0] == 1, "Sequence should start at 1"


# ── Integration test: full ingestion ──────────────────────────


def test_ingest_anzsic_2006_from_real_file(db_pool):
    """Integration test: ingest from the real ABS XLS file.

    Skips if the data file hasn't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.anzsic import ingest_anzsic_2006, _get_project_root

    xls_path = _get_project_root() / "data/anzsic/ANZSIC_2006_codes_titles.xls"
    if not xls_path.exists():
        pytest.skip("ANZSIC data file not downloaded — run ingest first")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing data for clean ingestion
            await conn.execute("DELETE FROM equivalence")
            await conn.execute(
                "DELETE FROM classification_node WHERE system_id = 'anzsic_2006'"
            )
            await conn.execute(
                "DELETE FROM classification_system WHERE id = 'anzsic_2006'"
            )

            count = await ingest_anzsic_2006(conn, file_path=xls_path)

            # Should have 400+ codes
            assert count > 400, f"Expected 400+ ANZSIC codes, got {count}"

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'anzsic_2006'"
            )
            assert row is not None
            assert row["node_count"] == count
            assert row["tint_color"] == "#14B8A6"

            # Verify all 19 divisions exist (A-S)
            divisions = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'anzsic_2006' AND level = 0"
            )
            div_codes = {r["code"] for r in divisions}
            expected_divs = set("ABCDEFGHIJKLMNOPQRS")
            assert div_codes == expected_divs, (
                f"Missing divisions: {expected_divs - div_codes}"
            )

            # Verify hierarchy: subdivision 01 should have parent A
            node_01 = await conn.fetchrow(
                "SELECT * FROM classification_node "
                "WHERE system_id = 'anzsic_2006' AND code = '01'"
            )
            assert node_01 is not None
            assert node_01["parent_code"] == "A"
            assert node_01["level"] == 1

            # Verify leaf nodes exist
            leaf_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                "WHERE system_id = 'anzsic_2006' AND is_leaf = TRUE"
            )
            assert leaf_count > 0, "Should have leaf nodes"

            # Verify sector_code is always a valid division letter
            bad_sectors = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                "WHERE system_id = 'anzsic_2006' "
                "AND sector_code NOT IN "
                "('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S')"
            )
            assert bad_sectors == 0, f"Found {bad_sectors} nodes with invalid sector codes"

    _run(_test())
