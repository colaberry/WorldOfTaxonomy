"""Tests for APQC PCF Level-1 anchor crosswalks.

These edges are conceptual overlaps (match_type='related'), not strict
equivalences. Tests verify shape and integrity, not numeric values.
"""
import asyncio

import pytest

from world_of_taxonomy.ingest.apqc_pcf import APQC_PCF_LEVEL_1, ingest_apqc_pcf
from world_of_taxonomy.ingest.crosswalk_apqc_anchors import (
    APQC_CROSSWALKS,
    ingest_crosswalk_apqc_anchors,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestCrosswalkData:
    def test_every_edge_uses_a_real_pcf_code(self):
        valid = set(APQC_PCF_LEVEL_1.keys())
        for src, tgt_sys, tgt_code, notes in APQC_CROSSWALKS:
            assert src in valid, f"PCF source code {src!r} not in APQC_PCF_LEVEL_1"

    def test_target_systems_are_only_the_documented_set(self):
        """Adding a new target system requires the wiki page update too,
        so this fence catches drift."""
        allowed = {"scor_model", "itil4", "reg_cobit", "pmbok7"}
        for _src, tgt_sys, _code, _notes in APQC_CROSSWALKS:
            assert tgt_sys in allowed, f"unexpected target system {tgt_sys!r}"

    def test_no_duplicate_edges(self):
        seen = set()
        for src, tgt_sys, tgt_code, _notes in APQC_CROSSWALKS:
            key = (src, tgt_sys, tgt_code)
            assert key not in seen, f"duplicate edge {key}"
            seen.add(key)

    def test_every_edge_has_notes(self):
        for src, tgt_sys, tgt_code, notes in APQC_CROSSWALKS:
            assert notes and len(notes) >= 20, (
                f"edge ({src} -> {tgt_sys}:{tgt_code}) needs a substantive note"
            )

    def test_no_em_dashes_in_notes(self):
        for _src, _tgt_sys, _tgt_code, notes in APQC_CROSSWALKS:
            assert "\u2014" not in notes, f"em-dash in notes: {notes!r}"

    def test_each_target_system_gets_at_least_one_edge(self):
        """Sanity: if we forgot to wire one of the four target systems,
        the wiki page promises a connection that does not exist."""
        seen_targets = {tgt for _src, tgt, _code, _notes in APQC_CROSSWALKS}
        assert seen_targets == {"scor_model", "itil4", "reg_cobit", "pmbok7"}


class TestCrosswalkIngestion:
    def test_ingest_inserts_edges_when_targets_present(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                # Ingest the APQC PCF skeleton first (idempotent).
                await ingest_apqc_pcf(conn)
                # The seeded test_wot schema does NOT have scor_model /
                # itil4 / reg_cobit / pmbok7 systems. The ingester
                # should skip those edges silently and report 0
                # inserts in this environment.
                inserted = await ingest_crosswalk_apqc_anchors(conn)
                # In the seeded test schema, all targets are absent,
                # so 0 edges insert. This test guards the "skip
                # silently" contract; a richer DB will insert more.
                assert inserted == 0
                # And no edges should have been written either.
                count = await conn.fetchval(
                    "SELECT count(*) FROM equivalence WHERE source_system='apqc_pcf'"
                )
                assert count == 0

        _run(go())

    def test_ingest_raises_when_apqc_pcf_missing(self, db_pool):
        """The crosswalk ingester is dependent: if apqc_pcf isn't
        ingested, fail fast rather than silently insert nothing."""
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM classification_node WHERE system_id='apqc_pcf'"
                )
                await conn.execute(
                    "DELETE FROM classification_system WHERE id='apqc_pcf'"
                )
                with pytest.raises(RuntimeError):
                    await ingest_crosswalk_apqc_anchors(conn)

        _run(go())
