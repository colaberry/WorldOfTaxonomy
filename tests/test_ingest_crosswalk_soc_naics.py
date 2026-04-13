"""Tests for SOC 2018 / NAICS 2022 crosswalk (Phase 3-D).

Maps SOC 2018 major occupation groups to NAICS 2022 sectors where
those occupations predominantly work. Hand-coded ~50 edges.
"""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.crosswalk_soc_naics import (
    SOC_NAICS_EDGES,
    ingest_crosswalk_soc_naics,
)


class TestSocNaicsEdges:
    def test_edges_is_list(self):
        assert isinstance(SOC_NAICS_EDGES, list)

    def test_at_least_40_edges(self):
        assert len(SOC_NAICS_EDGES) >= 40

    def test_each_edge_is_four_tuple(self):
        for edge in SOC_NAICS_EDGES:
            assert len(edge) == 4, f"Expected 4-tuple, got {len(edge)}: {edge}"

    def test_soc_codes_are_major_group_format(self):
        """SOC major group codes end in -0000."""
        for soc_code, _naics_code, _match_type, _note in SOC_NAICS_EDGES:
            assert soc_code.endswith("0000"), f"Expected major group code (XX-0000): {soc_code}"
            assert "-" in soc_code, f"SOC code missing hyphen: {soc_code}"

    def test_naics_codes_are_numeric(self):
        for _soc_code, naics_code, _match_type, _note in SOC_NAICS_EDGES:
            assert naics_code.isdigit(), f"NAICS code should be numeric: {naics_code}"

    def test_match_types_are_valid(self):
        valid = {"exact", "narrow", "broad", "partial"}
        for _soc, _naics, match_type, _note in SOC_NAICS_EDGES:
            assert match_type in valid, f"Invalid match_type: {match_type}"

    def test_healthcare_soc_links_to_naics_62(self):
        """Healthcare Practitioners (29-0000) should link to NAICS 62."""
        hc_edges = [e for e in SOC_NAICS_EDGES if e[0] == "29-0000"]
        naics_codes = {e[1] for e in hc_edges}
        assert "62" in naics_codes, "Healthcare practitioners should link to NAICS 62"

    def test_construction_soc_links_to_naics_23(self):
        """Construction and Extraction (47-0000) should link to NAICS 23."""
        const_edges = [e for e in SOC_NAICS_EDGES if e[0] == "47-0000"]
        naics_codes = {e[1] for e in const_edges}
        assert "23" in naics_codes, "Construction workers should link to NAICS 23"

    def test_no_em_dashes_in_notes(self):
        for _soc, _naics, _mt, note in SOC_NAICS_EDGES:
            if note:
                assert "\u2014" not in note, f"Em-dash in note: {note}"


def test_ingest_crosswalk_soc_naics(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            from world_of_taxanomy.ingest.soc_2018 import ingest_soc_2018
            from world_of_taxanomy.ingest.naics import ingest_naics_2022
            await ingest_soc_2018(conn)
            await ingest_naics_2022(conn)

            count = await ingest_crosswalk_soc_naics(conn)
            assert count >= 40

            rows = await conn.fetch(
                """SELECT * FROM equivalence
                   WHERE source_system = 'soc_2018' AND target_system = 'naics_2022'
                   LIMIT 5"""
            )
            assert len(rows) > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_soc_naics_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            from world_of_taxanomy.ingest.soc_2018 import ingest_soc_2018
            from world_of_taxanomy.ingest.naics import ingest_naics_2022
            await ingest_soc_2018(conn)
            await ingest_naics_2022(conn)

            count1 = await ingest_crosswalk_soc_naics(conn)
            count2 = await ingest_crosswalk_soc_naics(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
