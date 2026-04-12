"""Tests for ISO 3166-2 Subdivisions ingester.

RED tests - written before any implementation exists.

Hierarchy: country (L0, alpha-2) -> subdivision (L1, e.g. "US-CA")
Source: pycountry library (wraps ISO 3166-2 data, LGPL)
Codes: ~5,000 subdivisions across all countries
"""
import pytest
from world_of_taxanomy.ingest.iso3166_2 import (
    _determine_level,
    _determine_parent,
    _extract_country,
    ingest_iso3166_2,
)


class TestIso3166_2DetermineLevel:
    def test_subdivision_code_is_level_1(self):
        assert _determine_level("US-CA") == 1

    def test_subdivision_with_numbers_is_level_1(self):
        assert _determine_level("DE-BY") == 1

    def test_country_code_is_level_0(self):
        assert _determine_level("US") == 0

    def test_two_letter_country_is_level_0(self):
        assert _determine_level("GB") == 0

    def test_subdivision_three_part_is_level_1(self):
        # some codes like GB-ENG have 3-char suffix
        assert _determine_level("GB-ENG") == 1

    def test_subdivision_numeric_suffix_is_level_1(self):
        assert _determine_level("CN-11") == 1


class TestIso3166_2DetermineParent:
    def test_subdivision_parent_is_country(self):
        assert _determine_parent("US-CA") == "US"

    def test_de_subdivision_parent_is_de(self):
        assert _determine_parent("DE-BY") == "DE"

    def test_gb_subdivision_parent_is_gb(self):
        assert _determine_parent("GB-ENG") == "GB"

    def test_country_has_no_parent(self):
        assert _determine_parent("US") is None

    def test_cn_numeric_subdivision_parent_is_cn(self):
        assert _determine_parent("CN-11") == "CN"


class TestIso3166_2ExtractCountry:
    def test_us_ca_returns_us(self):
        assert _extract_country("US-CA") == "US"

    def test_de_by_returns_de(self):
        assert _extract_country("DE-BY") == "DE"

    def test_gb_eng_returns_gb(self):
        assert _extract_country("GB-ENG") == "GB"

    def test_two_letter_passthrough(self):
        assert _extract_country("US") == "US"


def test_ingest_iso3166_2_requires_pycountry(db_pool):
    """Integration test - ingest from pycountry library."""
    try:
        import pycountry  # noqa: F401
    except ImportError:
        pytest.skip("Install pycountry first: pip install pycountry")

    import asyncio

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_iso3166_2(conn)
            assert count >= 4000, f"Expected >= 4000 subdivision nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'iso_3166_2'"
            )
            assert row is not None
            assert row["node_count"] == count

            # California should exist
            ca = await conn.fetchrow(
                "SELECT code, title, level, parent_code FROM classification_node "
                "WHERE system_id = 'iso_3166_2' AND code = 'US-CA'"
            )
            assert ca is not None
            assert ca["level"] == 1
            assert ca["parent_code"] == "US"

            # US country node should exist at level 0
            us = await conn.fetchrow(
                "SELECT code, level FROM classification_node "
                "WHERE system_id = 'iso_3166_2' AND code = 'US'"
            )
            assert us is not None
            assert us["level"] == 0

    asyncio.get_event_loop().run_until_complete(_run())
