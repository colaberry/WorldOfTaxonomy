"""Tests for Nation-Sector Geographic Synergy crosswalk ingester.

RED tests - written before any implementation exists.

Maps ISO 3166-1 alpha-2 country codes to NAICS 2-digit sector codes
showing nation-sector leadership/strength relationships.
~100 hand-coded edges covering major economies.

match_type values: 'leadership' (established strength) or 'emerging' (growing strength)
"""
from __future__ import annotations

import asyncio
import pytest

from world_of_taxanomy.ingest.crosswalk_geo_sector import (
    GEO_SECTOR_EDGES,
    ingest_crosswalk_geo_sector,
)


class TestGeoSectorEdges:
    def test_edges_is_list(self):
        assert isinstance(GEO_SECTOR_EDGES, list)

    def test_at_least_80_edges(self):
        assert len(GEO_SECTOR_EDGES) >= 80

    def test_each_edge_is_four_tuple(self):
        for edge in GEO_SECTOR_EDGES:
            assert len(edge) == 4, f"Expected 4-tuple, got {len(edge)}: {edge}"

    def test_country_codes_are_two_chars(self):
        for country_code, _sector, _match_type, _note in GEO_SECTOR_EDGES:
            assert len(country_code) == 2, f"Country code should be 2 chars: {country_code}"
            assert country_code.isupper(), f"Country code should be uppercase: {country_code}"

    def test_naics_sector_codes_are_valid(self):
        """NAICS 2-digit sector codes are numeric strings."""
        for _country, sector_code, _match_type, _note in GEO_SECTOR_EDGES:
            assert sector_code.isdigit() or sector_code in (
                "11", "21", "22", "23", "31", "32", "33",
                "42", "44", "45", "48", "49", "51", "52",
                "53", "54", "55", "56", "61", "62", "71",
                "72", "81", "92",
            ), f"Unexpected NAICS sector code: {sector_code}"

    def test_match_types_are_valid(self):
        valid = {"leadership", "emerging", "broad", "partial"}
        for _country, _sector, match_type, _note in GEO_SECTOR_EDGES:
            assert match_type in valid, f"Invalid match_type: {match_type}"

    def test_usa_leads_technology(self):
        """US should link to NAICS 54 (Professional/Tech Services) or 51 (Information)."""
        usa_edges = [e for e in GEO_SECTOR_EDGES if e[0] == "US"]
        sector_codes = {e[1] for e in usa_edges}
        assert "54" in sector_codes or "51" in sector_codes, \
            "US should have a tech sector link"

    def test_germany_leads_manufacturing(self):
        """Germany should link to NAICS 31-33 (Manufacturing)."""
        deu_edges = [e for e in GEO_SECTOR_EDGES if e[0] == "DE"]
        sector_codes = {e[1] for e in deu_edges}
        assert any(s in sector_codes for s in ("31", "32", "33")), \
            "Germany should link to manufacturing"

    def test_no_em_dashes_in_notes(self):
        for _country, _sector, _mt, note in GEO_SECTOR_EDGES:
            if note:
                assert "\u2014" not in note, f"Em-dash in note: {note}"

    def test_no_duplicate_edges(self):
        pairs = [(e[0], e[1]) for e in GEO_SECTOR_EDGES]
        assert len(pairs) == len(set(pairs)), "Duplicate country-sector pairs found"


def test_ingest_crosswalk_geo_sector(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            await ingest_iso3166_1(conn)

            count = await ingest_crosswalk_geo_sector(conn)
            assert count >= 80

            rows = await conn.fetch(
                """SELECT * FROM equivalence
                   WHERE source_system = 'iso_3166_1' AND target_system = 'naics_2022'
                   LIMIT 5"""
            )
            assert len(rows) > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_geo_sector_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            await ingest_iso3166_1(conn)

            count1 = await ingest_crosswalk_geo_sector(conn)
            count2 = await ingest_crosswalk_geo_sector(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
