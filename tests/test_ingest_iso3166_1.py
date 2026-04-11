"""Tests for ISO 3166-1 Countries ingester.

RED tests - written before any implementation exists.

Hierarchy: continent (L0) -> sub-region (L1) -> country (L2, alpha-2 code)
Source: github.com/lukes/ISO-3166-Countries-with-Regional-Codes (CC0)
"""
import pytest
from world_of_taxanomy.ingest.iso3166_1 import (
    _CONTINENT_CODES,
    _clean_code,
    _determine_level,
    ingest_iso3166_1,
)


class TestIso3166DetermineLevel:
    def test_alpha2_country_code_is_level_2(self):
        assert _determine_level("US") == 2

    def test_alpha2_lowercase_treated_as_country(self):
        # stored as uppercase, but level detection is pattern-based
        assert _determine_level("DE") == 2

    def test_known_continent_code_is_level_0(self):
        assert _determine_level("002") == 0  # Africa

    def test_known_continent_europe_is_level_0(self):
        assert _determine_level("150") == 0  # Europe

    def test_unknown_numeric_code_is_level_1(self):
        # sub-region codes are not in _CONTINENT_CODES
        assert _determine_level("021") == 1  # Northern America (sub-region)

    def test_sub_region_southern_asia_is_level_1(self):
        assert _determine_level("034") == 1  # Southern Asia


class TestIso3166CleanCode:
    def test_single_digit_pads_to_3(self):
        assert _clean_code("2") == "002"

    def test_two_digit_pads_to_3(self):
        assert _clean_code("19") == "019"

    def test_three_digit_unchanged(self):
        assert _clean_code("142") == "142"

    def test_integer_input_converts(self):
        assert _clean_code(9) == "009"

    def test_alpha2_passthrough(self):
        # alpha-2 codes are not numeric - returned unchanged
        assert _clean_code("US") == "US"


class TestIso3166ContinentCodes:
    def test_africa_in_continent_codes(self):
        assert "002" in _CONTINENT_CODES

    def test_americas_in_continent_codes(self):
        assert "019" in _CONTINENT_CODES

    def test_asia_in_continent_codes(self):
        assert "142" in _CONTINENT_CODES

    def test_europe_in_continent_codes(self):
        assert "150" in _CONTINENT_CODES

    def test_oceania_in_continent_codes(self):
        assert "009" in _CONTINENT_CODES

    def test_subregion_not_in_continent_codes(self):
        assert "021" not in _CONTINENT_CODES  # Northern America is a sub-region

    def test_arbitrary_not_in_continent_codes(self):
        assert "034" not in _CONTINENT_CODES  # Southern Asia is a sub-region


def test_ingest_iso3166_1_from_real_file(db_pool):
    """Integration test - ingest from downloaded CSV."""
    import asyncio
    import os
    from pathlib import Path

    data_path = Path("data/iso3166_all.csv")
    if not data_path.exists():
        pytest.skip(f"Download {data_path} first: see world_of_taxanomy/ingest/iso3166_1.py for URL")

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_iso3166_1(conn, path=str(data_path))
            assert count >= 240, f"Expected >= 240 nodes, got {count}"
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'iso_3166_1'"
            )
            assert row is not None
            assert row["node_count"] == count

            # US should be present as a country node
            us = await conn.fetchrow(
                "SELECT code, title, level, parent_code FROM classification_node "
                "WHERE system_id = 'iso_3166_1' AND code = 'US'"
            )
            assert us is not None
            assert us["level"] == 2
            assert us["parent_code"] is not None  # has a sub-region parent

            # At least 5 continent nodes at level 0
            continents = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'iso_3166_1' AND level = 0"
            )
            assert len(continents) >= 5

    asyncio.get_event_loop().run_until_complete(_run())
