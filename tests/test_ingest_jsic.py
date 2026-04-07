"""Tests for JSIC 2013 (Rev 13) ingester.

Covers unit tests for division data and integration test
with the database.
"""

import asyncio
import pytest

from world_of_taxanomy.ingest.jsic import (
    JSIC_DIVISIONS,
    JSIC_TO_ISIC_MAPPING,
    ingest_jsic_2013,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: JSIC_DIVISIONS ───────────────────────────────────


class TestJsicDivisions:
    def test_exactly_20_divisions(self):
        assert len(JSIC_DIVISIONS) == 20

    def test_divisions_are_a_through_t(self):
        expected = set("ABCDEFGHIJKLMNOPQRST")
        assert set(JSIC_DIVISIONS.keys()) == expected

    def test_all_titles_non_empty(self):
        for code, title in JSIC_DIVISIONS.items():
            assert len(title) > 0, f"Division {code} has empty title"

    def test_specific_division_titles(self):
        assert JSIC_DIVISIONS["A"] == "Agriculture and Forestry"
        assert JSIC_DIVISIONS["E"] == "Manufacturing"
        assert JSIC_DIVISIONS["T"] == "Industries Unable to Classify"

    def test_no_duplicate_titles(self):
        titles = list(JSIC_DIVISIONS.values())
        assert len(titles) == len(set(titles)), "Division titles should be unique"


# ── Unit tests: JSIC_TO_ISIC_MAPPING ─────────────────────────────


class TestJsicToIsicMapping:
    def test_mapping_keys_are_valid_divisions(self):
        for code in JSIC_TO_ISIC_MAPPING:
            assert code in JSIC_DIVISIONS, f"Mapping key {code} is not a valid division"

    def test_mapping_has_16_entries(self):
        """16 divisions have clear ISIC mappings (N, Q, R, T are unmapped)."""
        assert len(JSIC_TO_ISIC_MAPPING) == 16

    def test_unmapped_divisions(self):
        """Divisions N, Q, R, T have no clear single ISIC equivalent."""
        unmapped = set(JSIC_DIVISIONS.keys()) - set(JSIC_TO_ISIC_MAPPING.keys())
        assert unmapped == {"N", "Q", "R", "T"}

    def test_match_types_are_broad(self):
        """All division-level mappings should be 'broad' since they are approximate."""
        for jsic_code, targets in JSIC_TO_ISIC_MAPPING.items():
            for isic_code, match_type in targets:
                assert match_type == "broad", (
                    f"JSIC {jsic_code} -> ISIC {isic_code} should be 'broad', got '{match_type}'"
                )

    def test_jsic_f_maps_to_two_isic_divisions(self):
        """JSIC F (Utilities) maps to both ISIC D and E."""
        targets = JSIC_TO_ISIC_MAPPING["F"]
        isic_codes = {t[0] for t in targets}
        assert isic_codes == {"D", "E"}

    def test_specific_mappings(self):
        """Verify key division-level mappings."""
        assert JSIC_TO_ISIC_MAPPING["A"] == [("A", "broad")]
        assert JSIC_TO_ISIC_MAPPING["C"] == [("B", "broad")]
        assert JSIC_TO_ISIC_MAPPING["E"] == [("C", "broad")]
        assert JSIC_TO_ISIC_MAPPING["I"] == [("G", "broad")]


# ── Integration test: full ingestion ─────────────────────────────


def test_ingest_jsic_2013(db_pool):
    """Integration test: ingest JSIC 2013 divisions into the database."""

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing JSIC data
            await conn.execute(
                "DELETE FROM equivalence WHERE source_system = 'jsic_2013' OR target_system = 'jsic_2013'"
            )
            await conn.execute(
                "DELETE FROM classification_node WHERE system_id = 'jsic_2013'"
            )
            await conn.execute(
                "DELETE FROM classification_system WHERE id = 'jsic_2013'"
            )

            count = await ingest_jsic_2013(conn)

            # Should have exactly 20 division codes
            assert count == 20

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'jsic_2013'"
            )
            assert row is not None
            assert row["name"] == "JSIC 2013"
            assert row["node_count"] == 20
            assert row["tint_color"] == "#F43F5E"
            assert row["region"] == "Japan"

            # Verify all 20 divisions exist
            divisions = await conn.fetch(
                "SELECT code, title FROM classification_node WHERE system_id = 'jsic_2013' AND level = 0"
            )
            assert len(divisions) == 20
            div_codes = {r["code"] for r in divisions}
            assert div_codes == set("ABCDEFGHIJKLMNOPQRST")

            # Verify division properties
            node_a = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'jsic_2013' AND code = 'A'"
            )
            assert node_a is not None
            assert node_a["title"] == "Agriculture and Forestry"
            assert node_a["level"] == 0
            assert node_a["parent_code"] is None
            assert node_a["sector_code"] == "A"
            assert node_a["is_leaf"] is True  # Leaf in skeleton (no children)

            # Verify equivalence edges exist
            forward_edges = await conn.fetch(
                "SELECT * FROM equivalence WHERE source_system = 'jsic_2013' AND target_system = 'isic_rev4'"
            )
            assert len(forward_edges) > 0

            reverse_edges = await conn.fetch(
                "SELECT * FROM equivalence WHERE source_system = 'isic_rev4' AND target_system = 'jsic_2013'"
            )
            assert len(reverse_edges) > 0

            # Forward and reverse should match (bidirectional)
            assert len(forward_edges) == len(reverse_edges)

            # Verify specific edge: JSIC A -> ISIC A
            edge_a = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'jsic_2013' AND source_code = 'A'
                     AND target_system = 'isic_rev4' AND target_code = 'A'"""
            )
            assert edge_a is not None
            assert edge_a["match_type"] == "broad"

            # Verify JSIC F -> ISIC D and ISIC E (one-to-many)
            f_edges = await conn.fetch(
                """SELECT target_code FROM equivalence
                   WHERE source_system = 'jsic_2013' AND source_code = 'F'
                     AND target_system = 'isic_rev4'"""
            )
            f_targets = {r["target_code"] for r in f_edges}
            assert f_targets == {"D", "E"}

            # Verify total edge count: 17 forward (16 mappings, but F has 2) + 17 reverse = 34
            total_edges = await conn.fetchval(
                """SELECT COUNT(*) FROM equivalence
                   WHERE source_system = 'jsic_2013' OR target_system = 'jsic_2013'"""
            )
            assert total_edges == 34  # 17 forward + 17 reverse

    _run(_test())


def test_ingest_jsic_2013_idempotent(db_pool):
    """Integration test: ingesting twice should not duplicate data."""

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing JSIC data
            await conn.execute(
                "DELETE FROM equivalence WHERE source_system = 'jsic_2013' OR target_system = 'jsic_2013'"
            )
            await conn.execute(
                "DELETE FROM classification_node WHERE system_id = 'jsic_2013'"
            )
            await conn.execute(
                "DELETE FROM classification_system WHERE id = 'jsic_2013'"
            )

            # Ingest twice
            count1 = await ingest_jsic_2013(conn)
            count2 = await ingest_jsic_2013(conn)

            assert count1 == 20
            assert count2 == 20

            # Should still have exactly 20 nodes
            node_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'jsic_2013'"
            )
            assert node_count == 20

    _run(_test())
