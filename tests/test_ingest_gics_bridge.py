"""Tests for GICS Bridge ingester.

RED tests - written before any implementation exists.

GICS = Global Industry Classification Standard (MSCI / S&P Dow Jones).
GICS is PROPRIETARY. This module stores ONLY the 11 top-level sector names
that appear in public financial press. No GICS hierarchy data is redistributed.

Source: publicly known sector names (financial press, Wikipedia)
License: n/a - only public names stored, no GICS data redistributed

Flat structure: 11 sectors, all level=1, all leaves, parent=None.
Sector code = the code itself.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.gics_bridge import (
    GICS_SECTORS,
    ingest_gics_bridge,
)


class TestGicsSectors:
    def test_exactly_11_sectors(self):
        assert len(GICS_SECTORS) == 11

    def test_energy_present(self):
        codes = [s[0] for s in GICS_SECTORS]
        assert "10" in codes

    def test_health_care_present(self):
        codes = [s[0] for s in GICS_SECTORS]
        assert "35" in codes

    def test_information_technology_present(self):
        codes = [s[0] for s in GICS_SECTORS]
        assert "45" in codes

    def test_real_estate_present(self):
        codes = [s[0] for s in GICS_SECTORS]
        assert "60" in codes

    def test_all_codes_are_two_digits(self):
        for code, title in GICS_SECTORS:
            assert len(code) == 2, f"Expected 2-digit code, got '{code}'"

    def test_all_titles_non_empty(self):
        for code, title in GICS_SECTORS:
            assert title.strip(), f"Empty title for code '{code}'"

    def test_no_duplicate_codes(self):
        codes = [s[0] for s in GICS_SECTORS]
        assert len(codes) == len(set(codes))


def test_gics_bridge_module_importable():
    assert callable(ingest_gics_bridge)
    assert isinstance(GICS_SECTORS, list)


def test_ingest_gics_bridge(db_pool):
    """Integration test: ingest 11 GICS sector stubs."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_gics_bridge(conn)
            assert count == 11, f"Expected 11 GICS sectors, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system "
                "WHERE id = 'gics_bridge'"
            )
            assert row is not None
            assert row["node_count"] == 11

            # All nodes are flat - level 1, no parent, is_leaf
            node = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf, sector_code "
                "FROM classification_node "
                "WHERE system_id = 'gics_bridge' AND code = '10'"
            )
            assert node["level"] == 1
            assert node["parent_code"] is None
            assert node["is_leaf"] is True
            assert node["sector_code"] == "10"

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_gics_bridge_idempotent(db_pool):
    """Running ingest twice returns 11 both times."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_gics_bridge(conn)
            count2 = await ingest_gics_bridge(conn)
            assert count1 == count2 == 11

    asyncio.get_event_loop().run_until_complete(_run())
