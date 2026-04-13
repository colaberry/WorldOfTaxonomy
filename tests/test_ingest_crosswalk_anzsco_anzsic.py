"""Tests for ANZSCO 2022 / ANZSIC 2006 crosswalk (Phase 3-F).

Maps ANZSCO 2022 occupation major groups to ANZSIC 2006 industry divisions
where those occupations predominantly work.
~40+ hand-coded edges.
"""
from __future__ import annotations

import asyncio
import pytest
from world_of_taxanomy.ingest.crosswalk_anzsco_anzsic import (
    ANZSCO_ANZSIC_EDGES,
    ingest_crosswalk_anzsco_anzsic,
)


class TestAnzscoAnzsicEdges:
    def test_edges_is_list(self):
        assert isinstance(ANZSCO_ANZSIC_EDGES, list)

    def test_at_least_30_edges(self):
        assert len(ANZSCO_ANZSIC_EDGES) >= 30

    def test_each_edge_is_four_tuple(self):
        for edge in ANZSCO_ANZSIC_EDGES:
            assert len(edge) == 4, f"Expected 4-tuple, got {len(edge)}: {edge}"

    def test_anzsco_codes_are_digits(self):
        for anzsco_code, _anzsic_code, _match_type, _note in ANZSCO_ANZSIC_EDGES:
            assert anzsco_code.isdigit(), f"ANZSCO code should be numeric: {anzsco_code}"

    def test_anzsic_codes_are_valid(self):
        """ANZSIC codes are 1-char letter (division) or 2-4 char alphanumeric."""
        for _anzsco_code, anzsic_code, _match_type, _note in ANZSCO_ANZSIC_EDGES:
            assert len(anzsic_code) >= 1, f"Empty ANZSIC code"
            assert len(anzsic_code) <= 4, f"ANZSIC code too long: {anzsic_code}"

    def test_match_types_are_valid(self):
        valid = {"exact", "narrow", "broad", "partial"}
        for _anzsco, _anzsic, match_type, _note in ANZSCO_ANZSIC_EDGES:
            assert match_type in valid, f"Invalid match_type: {match_type}"

    def test_managers_link_to_multiple_industries(self):
        """ANZSCO major group 1 (Managers) should link to multiple divisions."""
        manager_edges = [e for e in ANZSCO_ANZSIC_EDGES if e[0] == "1"]
        assert len(manager_edges) >= 3, "Managers should link to at least 3 industries"

    def test_labourers_link_to_primary_industries(self):
        """ANZSCO 8 (Labourers) should link to Agriculture (A) or Mining (B)."""
        labourer_edges = [e for e in ANZSCO_ANZSIC_EDGES if e[0] == "8"]
        anzsic_codes = {e[1] for e in labourer_edges}
        assert ("A" in anzsic_codes or "B" in anzsic_codes), \
            "Labourers should link to primary industries"

    def test_no_em_dashes_in_notes(self):
        for _anzsco, _anzsic, _mt, note in ANZSCO_ANZSIC_EDGES:
            if note:
                assert "\u2014" not in note, f"Em-dash in note: {note}"


def test_ingest_crosswalk_anzsco_anzsic(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            from world_of_taxanomy.ingest.anzsco_2022 import ingest_anzsco_2022
            from world_of_taxanomy.ingest.anzsic import ingest_anzsic
            await ingest_anzsco_2022(conn)
            await ingest_anzsic(conn)

            count = await ingest_crosswalk_anzsco_anzsic(conn)
            assert count >= 30

            rows = await conn.fetch(
                """SELECT * FROM equivalence
                   WHERE source_system = 'anzsco_2022' AND target_system = 'anzsic_2006'
                   LIMIT 5"""
            )
            assert len(rows) > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_anzsco_anzsic_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            from world_of_taxanomy.ingest.anzsco_2022 import ingest_anzsco_2022
            from world_of_taxanomy.ingest.anzsic import ingest_anzsic
            await ingest_anzsco_2022(conn)
            await ingest_anzsic(conn)

            count1 = await ingest_crosswalk_anzsco_anzsic(conn)
            count2 = await ingest_crosswalk_anzsco_anzsic(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
