"""Tests for NAICS 2022 ingester.

Retroactive TDD - covering the unit logic and integration behavior
that should have been tested before implementation.
"""

import asyncio
import pytest

from world_of_taxonomy.ingest.naics import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    RANGE_SECTORS,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _determine_level ──────────────────────────────


class TestNaicsDetermineLevel:
    def test_two_digit_is_level_1(self):
        assert _determine_level("11") == 1
        assert _determine_level("62") == 1

    def test_range_sector_is_level_1(self):
        assert _determine_level("31-33") == 1
        assert _determine_level("44-45") == 1
        assert _determine_level("48-49") == 1

    def test_three_digit_is_level_2(self):
        assert _determine_level("111") == 2
        assert _determine_level("621") == 2

    def test_four_digit_is_level_3(self):
        assert _determine_level("1111") == 3
        assert _determine_level("6211") == 3

    def test_five_digit_is_level_4(self):
        assert _determine_level("11111") == 4
        assert _determine_level("62111") == 4

    def test_six_digit_is_level_5(self):
        assert _determine_level("111110") == 5
        assert _determine_level("621111") == 5


# ── Unit tests: _determine_parent ─────────────────────────────


class TestNaicsDetermineParent:
    def test_two_digit_sector_has_no_parent(self):
        assert _determine_parent("11") is None
        assert _determine_parent("62") is None

    def test_range_sector_has_no_parent(self):
        assert _determine_parent("31-33") is None
        assert _determine_parent("44-45") is None
        assert _determine_parent("48-49") is None

    def test_subsector_parent_is_sector(self):
        assert _determine_parent("111") == "11"
        assert _determine_parent("621") == "62"

    def test_subsector_parent_resolves_range_sector(self):
        """Codes starting with 31, 32, 33 should map to parent '31-33'."""
        assert _determine_parent("311") == "31-33"
        assert _determine_parent("321") == "31-33"
        assert _determine_parent("332") == "31-33"
        assert _determine_parent("441") == "44-45"
        assert _determine_parent("452") == "44-45"
        assert _determine_parent("481") == "48-49"
        assert _determine_parent("492") == "48-49"

    def test_four_digit_parent_is_three_digit(self):
        assert _determine_parent("1111") == "111"
        assert _determine_parent("6211") == "621"

    def test_five_digit_parent_is_four_digit(self):
        assert _determine_parent("11111") == "1111"
        assert _determine_parent("62111") == "6211"

    def test_six_digit_parent_is_five_digit(self):
        assert _determine_parent("111110") == "11111"
        assert _determine_parent("621111") == "62111"


# ── Unit tests: _determine_sector ─────────────────────────────


class TestNaicsDetermineSector:
    def test_range_sector_is_itself(self):
        assert _determine_sector("31-33") == "31-33"
        assert _determine_sector("44-45") == "44-45"

    def test_two_digit_sector(self):
        assert _determine_sector("11") == "11"
        assert _determine_sector("62") == "62"

    def test_deep_code_resolves_to_sector(self):
        assert _determine_sector("111110") == "11"
        assert _determine_sector("621111") == "62"

    def test_manufacturing_code_resolves_to_range(self):
        assert _determine_sector("311") == "31-33"
        assert _determine_sector("3254") == "31-33"
        assert _determine_sector("44111") == "44-45"


# ── Integration test: full ingestion ──────────────────────────


def test_ingest_naics_2022_from_real_file(db_pool):
    """Integration test: ingest from the real Census Bureau Excel file.

    Skips if the data file hasn't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxonomy.ingest.naics import ingest_naics_2022, _get_project_root

    xlsx_path = _get_project_root() / "data/naics/2022_NAICS_Codes.xlsx"
    if not xlsx_path.exists():
        pytest.skip("NAICS data file not downloaded - run 'python -m world_of_taxonomy ingest naics' first")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing seed data for clean ingestion
            await conn.execute("DELETE FROM equivalence")
            await conn.execute("DELETE FROM classification_node WHERE system_id = 'naics_2022'")
            await conn.execute("DELETE FROM classification_system WHERE id = 'naics_2022'")

            count = await ingest_naics_2022(conn, xlsx_path=xlsx_path)

            # Should have ~2000+ codes
            assert count > 2000, f"Expected 2000+ NAICS codes, got {count}"

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'naics_2022'"
            )
            assert row is not None
            assert row["node_count"] == count
            # Per-code authority deep link template so the frontend can
            # link every node to its Census Bureau page.
            assert row["node_url_template"] == (
                "https://www.census.gov/naics/?input={code}&year=2022"
            )

            # Verify specific well-known codes exist
            for code in ["11", "62", "31-33", "621", "6211"]:
                node = await conn.fetchrow(
                    "SELECT * FROM classification_node WHERE system_id = 'naics_2022' AND code = $1",
                    code,
                )
                assert node is not None, f"Expected NAICS code {code} to exist"

            # Verify hierarchy: 621's parent should be 62
            node_621 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'naics_2022' AND code = '621'"
            )
            assert node_621["parent_code"] == "62"

            # Verify leaf nodes exist (6-digit codes should be leaves)
            leaf_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'naics_2022' AND is_leaf = TRUE"
            )
            assert leaf_count > 0, "Should have leaf nodes"

    _run(_test())
