"""Tests for APQC PCF (Cross-Industry Process Classification Framework).

This is a Level-1 skeleton: 13 top-level categories of the APQC
Cross-Industry PCF. Levels 2-5 (~1,500 detailed process elements)
require the official APQC spreadsheet (free with registration at
https://www.apqc.org/process-frameworks). When that file is available,
the existing ingester can be extended in place; the system_id stays
the same, so existing crosswalks to apqc_pcf level-1 codes survive
the expansion.

The 13 categories are stable across PCF revisions and authoritatively
published by APQC. The numeric codes (1.0 through 13.0) are APQC's
own identifiers, not WoT-minted.
"""
import pytest

from world_of_taxonomy.ingest.apqc_pcf import (
    parse_apqc_pcf,
    ingest_apqc_pcf,
    APQC_PCF_LEVEL_1,
)


class TestParser:
    def test_parses_thirteen_top_level_categories(self):
        nodes = parse_apqc_pcf()
        assert len(nodes) == 13, f"Expected 13 categories, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_apqc_pcf()
        codes = [n[0] for n in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_apqc_pcf()
        for code, title, _l, _p, _d in nodes:
            assert title and len(title) > 0, f"Empty title for {code}"

    def test_no_em_dashes(self):
        nodes = parse_apqc_pcf()
        for code, title, _l, _p, desc in nodes:
            assert "\u2014" not in title, f"Em-dash in title of {code}"
            if desc:
                assert "\u2014" not in desc, f"Em-dash in description of {code}"

    def test_codes_use_apqc_dot_zero_pattern(self):
        nodes = parse_apqc_pcf()
        for code, _t, _l, _p, _d in nodes:
            # APQC PCF Level-1 codes are "1.0", "2.0", ... "13.0"
            assert code.endswith(".0"), f"Code {code!r} not APQC-style"
            num_part = code.split(".")[0]
            assert num_part.isdigit(), f"Code {code!r} not numeric"

    def test_all_level_1(self):
        nodes = parse_apqc_pcf()
        for code, _t, level, parent, _d in nodes:
            assert level == 1, f"Skeleton must be Level-1 only, got level {level} for {code}"
            assert parent is None, f"Level-1 must have no parent, got {parent} for {code}"

    def test_all_have_descriptions(self):
        nodes = parse_apqc_pcf()
        for code, title, _l, _p, desc in nodes:
            assert desc and len(desc) > 0, f"Missing description for {code} {title}"

    def test_canonical_categories_present(self):
        """Canonical APQC PCF Cross-Industry top-level categories."""
        nodes = parse_apqc_pcf()
        codes = {n[0] for n in nodes}
        # Spot-check the first and last and a middle one
        assert "1.0" in codes
        assert "13.0" in codes
        assert "7.0" in codes  # Manage Information Technology

    def test_known_titles_match_apqc_publications(self):
        """Sanity check the published category names so a future
        renumbering or rename in the source code is caught."""
        nodes = parse_apqc_pcf()
        titles_by_code = {n[0]: n[1] for n in nodes}
        assert "Develop Vision and Strategy" in titles_by_code["1.0"]
        # Avoid asserting on the rest because APQC has revised wording
        # over PCF revisions; the structural test_codes_use_apqc_dot_zero_pattern
        # plus test_canonical_categories_present is the load-bearing pair.


class TestIngestIntegration:
    def test_ingest_writes_system_with_provenance(self, db_pool):
        import asyncio

        async def go():
            async with db_pool.acquire() as conn:
                n = await ingest_apqc_pcf(conn)
                assert n == 13
                row = await conn.fetchrow(
                    "select id, data_provenance, license, node_count, authority "
                    "from classification_system where id='apqc_pcf'"
                )
                assert row is not None
                assert row["data_provenance"] == "manual_transcription"
                assert "APQC" in (row["license"] or "")
                assert row["node_count"] == 13
                assert row["authority"] == "APQC"

        asyncio.get_event_loop().run_until_complete(go())

    def test_ingest_idempotent(self, db_pool):
        import asyncio

        async def go():
            async with db_pool.acquire() as conn:
                await ingest_apqc_pcf(conn)
                first = await conn.fetchval(
                    "select count(*) from classification_node where system_id='apqc_pcf'"
                )
                await ingest_apqc_pcf(conn)
                second = await conn.fetchval(
                    "select count(*) from classification_node where system_id='apqc_pcf'"
                )
            assert first == second == 13

        asyncio.get_event_loop().run_until_complete(go())


def test_module_exports_level_1_constant():
    """The skeleton's authoritative source is a module-level dict so
    contributors can extend it for Levels 2-5 without touching the
    parse function. This test guards that contract."""
    assert isinstance(APQC_PCF_LEVEL_1, dict)
    assert len(APQC_PCF_LEVEL_1) == 13
