"""Tests for NAICS-ISIC crosswalk ingester.

Retroactive TDD — covering the match type logic and integration behavior
that should have been tested before implementation.
"""

import asyncio
import pytest

from world_of_taxanomy.ingest.crosswalk import _determine_match_type


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _determine_match_type ─────────────────────────


class TestDetermineMatchType:
    def test_both_none_is_exact(self):
        assert _determine_match_type(None, None) == "exact"

    def test_both_empty_is_exact(self):
        assert _determine_match_type("", "") == "exact"

    def test_naics_marker_is_partial(self):
        assert _determine_match_type("*", None) == "partial"
        assert _determine_match_type("Part", None) == "partial"

    def test_isic_marker_is_partial(self):
        assert _determine_match_type(None, "*") == "partial"
        assert _determine_match_type(None, "Part") == "partial"

    def test_both_markers_is_partial(self):
        assert _determine_match_type("*", "*") == "partial"

    def test_whitespace_only_is_exact(self):
        assert _determine_match_type("  ", "  ") == "exact"


# ── Integration test: full crosswalk ingestion ────────────────


def test_ingest_crosswalk_from_real_file(db_pool):
    """Integration test: ingest from the real Census Bureau crosswalk file.

    Requires both NAICS and ISIC systems to exist (registered during ingestion).
    Skips if the data file hasn't been downloaded yet.
    """
    from pathlib import Path
    from world_of_taxanomy.ingest.crosswalk import ingest_crosswalk, _get_project_root

    xlsx_path = _get_project_root() / "data/crosswalk/2022_NAICS_to_ISIC_Rev_4.xlsx"
    if not xlsx_path.exists():
        pytest.skip("Crosswalk data file not downloaded — run 'python -m world_of_taxanomy ingest crosswalk' first")

    async def _test():
        async with db_pool.acquire() as conn:
            # Clear existing crosswalk data
            await conn.execute("DELETE FROM equivalence")

            count = await ingest_crosswalk(conn, file_path=xlsx_path)

            # Should have significant number of edges (bidirectional)
            assert count > 1000, f"Expected 1000+ crosswalk edges, got {count}"

            # Should be even (every forward edge has a reverse)
            assert count % 2 == 0, "Crosswalk edges should be even (bidirectional)"

            # Verify bidirectionality: pick a known pair
            forward = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'naics_2022' AND target_system = 'isic_rev4'
                   LIMIT 1"""
            )
            assert forward is not None

            # Reverse should exist
            reverse = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'isic_rev4' AND source_code = $1
                     AND target_system = 'naics_2022' AND target_code = $2""",
                forward["target_code"], forward["source_code"],
            )
            assert reverse is not None, "Reverse edge should exist for every forward edge"

            # Verify match types are valid
            invalid = await conn.fetchval(
                "SELECT COUNT(*) FROM equivalence WHERE match_type NOT IN ('exact', 'partial', 'broad', 'narrow')"
            )
            assert invalid == 0, "All match types should be valid"

            # Verify both exact and partial matches exist
            exact_count = await conn.fetchval(
                "SELECT COUNT(*) FROM equivalence WHERE match_type = 'exact'"
            )
            partial_count = await conn.fetchval(
                "SELECT COUNT(*) FROM equivalence WHERE match_type = 'partial'"
            )
            assert exact_count > 0, "Should have some exact matches"
            assert partial_count > 0, "Should have some partial matches"

    _run(_test())
