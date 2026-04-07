"""Tests for NACE Rev 2 ingester.

Covers unit logic for code helpers, crosswalk parsing, and integration
with the database.
"""

import asyncio
import pytest

from world_of_taxanomy.ingest.nace import (
    _nace_level,
    _nace_parent,
    _nace_sector,
    _nace_to_isic,
    _determine_match_type,
    _sort_key,
    parse_crosswalk,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _nace_level ─────────────────────────────────────


class TestNaceLevel:
    def test_letter_section_is_level_0(self):
        assert _nace_level("A") == 0
        assert _nace_level("Q") == 0
        assert _nace_level("U") == 0

    def test_two_digit_division_is_level_1(self):
        assert _nace_level("01") == 1
        assert _nace_level("86") == 1
        assert _nace_level("99") == 1

    def test_dotted_group_is_level_2(self):
        assert _nace_level("01.1") == 2
        assert _nace_level("86.2") == 2
        assert _nace_level("10.7") == 2

    def test_dotted_class_is_level_3(self):
        assert _nace_level("01.11") == 3
        assert _nace_level("86.20") == 3
        assert _nace_level("96.09") == 3


# ── Unit tests: _nace_parent ────────────────────────────────────


class TestNaceParent:
    def test_section_has_no_parent(self):
        assert _nace_parent("A") is None
        assert _nace_parent("U") is None

    def test_division_parent_is_section(self):
        assert _nace_parent("01") == "A"
        assert _nace_parent("86") == "Q"
        assert _nace_parent("10") == "C"

    def test_group_parent_is_division(self):
        assert _nace_parent("01.1") == "01"
        assert _nace_parent("86.2") == "86"
        assert _nace_parent("10.7") == "10"

    def test_class_parent_is_group(self):
        assert _nace_parent("01.11") == "01.1"
        assert _nace_parent("86.20") == "86.2"
        assert _nace_parent("96.09") == "96.0"


# ── Unit tests: _nace_sector ────────────────────────────────────


class TestNaceSector:
    def test_section_is_its_own_sector(self):
        assert _nace_sector("A") == "A"
        assert _nace_sector("Q") == "Q"

    def test_division_maps_to_section(self):
        assert _nace_sector("01") == "A"
        assert _nace_sector("86") == "Q"
        assert _nace_sector("10") == "C"

    def test_dotted_code_maps_to_section(self):
        assert _nace_sector("01.11") == "A"
        assert _nace_sector("86.20") == "Q"
        assert _nace_sector("10.71") == "C"


# ── Unit tests: _nace_to_isic ───────────────────────────────────


class TestNaceToIsic:
    def test_section_unchanged(self):
        assert _nace_to_isic("A") == "A"

    def test_division_unchanged(self):
        assert _nace_to_isic("01") == "01"

    def test_group_dot_stripped(self):
        assert _nace_to_isic("01.1") == "011"
        assert _nace_to_isic("86.2") == "862"

    def test_class_dot_stripped(self):
        assert _nace_to_isic("01.11") == "0111"
        assert _nace_to_isic("86.20") == "8620"


# ── Unit tests: _determine_match_type ───────────────────────────


class TestDetermineMatchType:
    def test_both_zero_is_exact(self):
        assert _determine_match_type(0, 0) == "exact"

    def test_isic_part_nonzero_is_partial(self):
        assert _determine_match_type(1, 0) == "partial"

    def test_nace_part_nonzero_is_partial(self):
        assert _determine_match_type(0, 1) == "partial"

    def test_both_nonzero_is_partial(self):
        assert _determine_match_type(1, 1) == "partial"


# ── Unit tests: _sort_key ───────────────────────────────────────


class TestSortKey:
    def test_sections_before_numeric(self):
        codes = ["01", "A", "B", "10"]
        sorted_codes = sorted(codes, key=_sort_key)
        assert sorted_codes == ["A", "B", "01", "10"]

    def test_numeric_order(self):
        codes = ["10.71", "10.7", "10", "01.11", "01.1", "01"]
        sorted_codes = sorted(codes, key=_sort_key)
        assert sorted_codes == ["01", "01.1", "01.11", "10", "10.7", "10.71"]


# ── Unit tests: parse_crosswalk ─────────────────────────────────


class TestParseCrosswalk:
    def test_parse_real_file(self):
        from pathlib import Path
        from world_of_taxanomy.ingest.nace import _get_project_root

        csv_path = _get_project_root() / "data/crosswalk/ISIC4_to_NACE2.txt"
        if not csv_path.exists():
            pytest.skip("Crosswalk file not downloaded")

        rows = parse_crosswalk(csv_path)

        # Should have 996 entries (997 lines minus header)
        assert len(rows) == 996

        # First row: A -> A, both part=0
        assert rows[0]["isic_code"] == "A"
        assert rows[0]["nace_code"] == "A"
        assert rows[0]["isic_part"] == 0
        assert rows[0]["nace_part"] == 0

        # Check a partial entry exists (ISIC 0141 part=1 -> NACE 01.41, 01.42)
        partials = [r for r in rows if r["isic_code"] == "0141" and r["isic_part"] == 1]
        assert len(partials) == 2
        nace_targets = {r["nace_code"] for r in partials}
        assert nace_targets == {"01.41", "01.42"}


# ── Integration test: full NACE ingestion ───────────────────────


def test_ingest_nace_rev2_from_real_file(db_pool):
    """Integration test: ingest NACE Rev 2 from the real crosswalk file.

    Requires ISIC Rev 4 to be ingested first (for title lookups).
    Skips if data files haven't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.isic import ingest_isic_rev4, _get_project_root as isic_root
    from world_of_taxanomy.ingest.nace import ingest_nace_rev2, _get_project_root

    isic_path = isic_root() / "data/isic/ISIC_Rev_4_structure.txt"
    nace_crosswalk_path = _get_project_root() / "data/crosswalk/ISIC4_to_NACE2.txt"

    if not isic_path.exists():
        pytest.skip("ISIC data file not downloaded")
    if not nace_crosswalk_path.exists():
        pytest.skip("NACE crosswalk file not downloaded")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clean slate
            await conn.execute("DELETE FROM equivalence")
            await conn.execute("DELETE FROM classification_node WHERE system_id IN ('isic_rev4', 'nace_rev2')")
            await conn.execute("DELETE FROM classification_system WHERE id IN ('isic_rev4', 'nace_rev2')")

            # Ingest ISIC first (NACE depends on it for titles)
            await ingest_isic_rev4(conn, file_path=isic_path)

            # Ingest NACE
            count = await ingest_nace_rev2(conn, file_path=nace_crosswalk_path)

            # Should have a reasonable number of codes
            assert count > 500, f"Expected 500+ NACE codes, got {count}"

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'nace_rev2'"
            )
            assert row is not None
            assert row["node_count"] == count
            assert row["tint_color"] == "#1E40AF"

            # Verify all 21 sections exist
            sections = await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id = 'nace_rev2' AND level = 0"
            )
            section_codes = {r["code"] for r in sections}
            expected_sections = set("ABCDEFGHIJKLMNOPQRSTU")
            assert section_codes == expected_sections, f"Missing sections: {expected_sections - section_codes}"

            # Verify dotted codes exist
            node_0111 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'nace_rev2' AND code = '01.11'"
            )
            assert node_0111 is not None
            assert node_0111["level"] == 3
            assert node_0111["parent_code"] == "01.1"
            assert node_0111["sector_code"] == "A"

            # Verify hierarchy: division 01 should have parent A
            node_01 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'nace_rev2' AND code = '01'"
            )
            assert node_01 is not None
            assert node_01["parent_code"] == "A"

            # Verify leaf nodes exist
            leaf_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'nace_rev2' AND is_leaf = TRUE"
            )
            assert leaf_count > 0, "Should have leaf nodes"

            # Verify titles were resolved (not fallback "NACE X" titles)
            fallback_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'nace_rev2' AND title LIKE 'NACE %'"
            )
            # Most titles should come from ISIC; a few NACE-only codes may use fallback
            assert fallback_count < count * 0.1, f"Too many fallback titles: {fallback_count}/{count}"

    _run(_test())


# ── Integration test: NACE-ISIC crosswalk edges ────────────────


def test_ingest_nace_isic_crosswalk_from_real_file(db_pool):
    """Integration test: ingest NACE-ISIC equivalence edges.

    Skips if the crosswalk file hasn't been downloaded.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.nace import ingest_nace_isic_crosswalk, _get_project_root

    csv_path = _get_project_root() / "data/crosswalk/ISIC4_to_NACE2.txt"
    if not csv_path.exists():
        pytest.skip("NACE crosswalk file not downloaded")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing NACE-ISIC edges
            await conn.execute(
                "DELETE FROM equivalence WHERE source_system = 'nace_rev2' OR target_system = 'nace_rev2'"
            )

            count = await ingest_nace_isic_crosswalk(conn, file_path=csv_path)

            # Should have significant number of edges (bidirectional)
            assert count > 1000, f"Expected 1000+ crosswalk edges, got {count}"

            # Should be even (every forward edge has a reverse)
            assert count % 2 == 0, "Crosswalk edges should be even (bidirectional)"

            # Verify bidirectionality: pick a known pair (A -> A)
            forward = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'nace_rev2' AND source_code = 'A'
                     AND target_system = 'isic_rev4' AND target_code = 'A'"""
            )
            assert forward is not None
            assert forward["match_type"] == "exact"

            # Reverse should exist
            reverse = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'isic_rev4' AND source_code = 'A'
                     AND target_system = 'nace_rev2' AND target_code = 'A'"""
            )
            assert reverse is not None

            # Verify partial matches exist (ISIC 0141 -> NACE 01.41 and 01.42)
            partial_edges = await conn.fetch(
                """SELECT * FROM equivalence
                   WHERE source_system = 'isic_rev4' AND source_code = '0141'
                     AND target_system = 'nace_rev2'"""
            )
            assert len(partial_edges) == 2
            nace_targets = {r["target_code"] for r in partial_edges}
            assert nace_targets == {"01.41", "01.42"}
            assert all(r["match_type"] == "partial" for r in partial_edges)

            # Verify match types are valid
            invalid = await conn.fetchval(
                """SELECT COUNT(*) FROM equivalence
                   WHERE (source_system = 'nace_rev2' OR target_system = 'nace_rev2')
                     AND match_type NOT IN ('exact', 'partial', 'broad', 'narrow')"""
            )
            assert invalid == 0, "All match types should be valid"

    _run(_test())
