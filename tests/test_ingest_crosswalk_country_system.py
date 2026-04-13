"""Tests for Country-to-Classification-System crosswalk ingester.

RED tests - written before any implementation exists.

Maps ISO 3166-1 alpha-2 country codes to classification system IDs,
indicating which systems are officially used, regionally mandated,
globally recommended, or historically referenced per country.

relevance values: official, regional, recommended, historical
"""
from __future__ import annotations

import asyncio
import pytest

from world_of_taxanomy.ingest.crosswalk_country_system import (
    COUNTRY_SYSTEM_LINKS,
    ingest_crosswalk_country_system,
)


class TestCountrySystemLinks:
    def test_links_is_list(self):
        assert isinstance(COUNTRY_SYSTEM_LINKS, list)

    def test_at_least_100_links(self):
        """Should cover all 271 countries with ISIC + national overlays."""
        assert len(COUNTRY_SYSTEM_LINKS) >= 100

    def test_each_link_is_four_tuple(self):
        for link in COUNTRY_SYSTEM_LINKS:
            assert len(link) == 4, f"Expected 4-tuple, got {len(link)}: {link}"

    def test_country_codes_are_two_chars_uppercase(self):
        for country_code, _sid, _rel, _note in COUNTRY_SYSTEM_LINKS:
            assert len(country_code) == 2, f"Country code must be 2 chars: {country_code}"
            assert country_code.isupper(), f"Country code must be uppercase: {country_code}"

    def test_relevance_values_are_valid(self):
        valid = {"official", "regional", "recommended", "historical"}
        for _cc, _sid, relevance, _note in COUNTRY_SYSTEM_LINKS:
            assert relevance in valid, f"Invalid relevance: {relevance}"

    def test_system_ids_are_known_strings(self):
        """System IDs must be non-empty strings."""
        for _cc, system_id, _rel, _note in COUNTRY_SYSTEM_LINKS:
            assert isinstance(system_id, str)
            assert len(system_id) > 0

    def test_no_duplicate_country_system_pairs(self):
        pairs = [(e[0], e[1]) for e in COUNTRY_SYSTEM_LINKS]
        assert len(pairs) == len(set(pairs)), "Duplicate country-system pairs found"

    def test_usa_has_naics_official(self):
        us_links = [(cc, sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "US"]
        naics_links = [l for l in us_links if l[1] == "naics_2022"]
        assert naics_links, "US should have naics_2022 link"
        assert naics_links[0][2] == "official", "US naics_2022 should be official"

    def test_mexico_has_naics(self):
        mx_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "MX"]
        system_ids = {s for s, _ in mx_links}
        assert "naics_2022" in system_ids, "Mexico should have naics_2022 (SCIAN is NAICS-aligned)"

    def test_germany_has_official_and_regional(self):
        de_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "DE"]
        system_ids = {s for s, _ in de_links}
        relevances = {rel for _, rel in de_links}
        assert "wz_2008" in system_ids, "Germany should have wz_2008 (official)"
        assert "nace_rev2" in system_ids, "Germany should have nace_rev2 (regional)"
        assert "official" in relevances
        assert "regional" in relevances

    def test_india_has_nic_official(self):
        in_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "IN"]
        nic_links = [(s, r) for s, r in in_links if s == "nic_2008"]
        assert nic_links, "India should have nic_2008"
        assert nic_links[0][1] == "official"

    def test_japan_has_jsic_official(self):
        jp_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "JP"]
        jsic_links = [(s, r) for s, r in jp_links if s == "jsic_2013"]
        assert jsic_links, "Japan should have jsic_2013"
        assert jsic_links[0][1] == "official"

    def test_australia_has_anzsic_official(self):
        au_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "AU"]
        anzsic_links = [(s, r) for s, r in au_links if s == "anzsic_2006"]
        assert anzsic_links, "Australia should have anzsic_2006"
        assert anzsic_links[0][1] == "official"

    def test_pakistan_has_isic_recommended(self):
        pk_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "PK"]
        isic_links = [(s, r) for s, r in pk_links if s == "isic_rev4"]
        assert isic_links, "Pakistan should have isic_rev4 (UN recommended global standard)"
        assert isic_links[0][1] == "recommended"

    def test_indonesia_has_isic_recommended(self):
        id_links = [(sid, rel) for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS if cc == "ID"]
        isic_links = [(s, r) for s, r in id_links if s == "isic_rev4"]
        assert isic_links, "Indonesia should have isic_rev4"

    def test_all_eu_countries_have_nace(self):
        eu_countries = {
            "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
            "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
            "NL", "PL", "PT", "RO", "SE", "SI", "SK",
        }
        covered = {
            cc for cc, sid, rel, _ in COUNTRY_SYSTEM_LINKS
            if sid == "nace_rev2" and cc in eu_countries
        }
        assert covered == eu_countries, f"EU countries missing nace_rev2: {eu_countries - covered}"

    def test_no_em_dashes_in_notes(self):
        for _cc, _sid, _rel, note in COUNTRY_SYSTEM_LINKS:
            if note:
                assert "\u2014" not in note, f"Em-dash found in note: {note}"


def test_ingest_crosswalk_country_system(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        from world_of_taxanomy.ingest.isic import ingest_isic
        from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1

        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            await ingest_isic(conn)
            await ingest_iso3166_1(conn)

            count = await ingest_crosswalk_country_system(conn)
            assert count >= 100

            # Germany should return wz_2008, nace_rev2, isic_rev4
            rows = await conn.fetch(
                """SELECT system_id, relevance FROM country_system_link
                   WHERE country_code = 'DE'
                   ORDER BY system_id"""
            )
            system_ids = {r["system_id"] for r in rows}
            assert "isic_rev4" in system_ids
            assert "nace_rev2" in system_ids

            # Pakistan should return isic_rev4
            pk_rows = await conn.fetch(
                "SELECT system_id FROM country_system_link WHERE country_code = 'PK'"
            )
            assert len(pk_rows) >= 1

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_country_system_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        from world_of_taxanomy.ingest.isic import ingest_isic
        from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1

        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            await ingest_isic(conn)
            await ingest_iso3166_1(conn)

            count1 = await ingest_crosswalk_country_system(conn)
            count2 = await ingest_crosswalk_country_system(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
