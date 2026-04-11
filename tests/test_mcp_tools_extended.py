"""Tests for 12 new MCP tool handlers - RED phase.

Each test defines the contract for a new tool before implementation exists.
Run these first to confirm RED, then implement handlers to go GREEN.
"""

import asyncio
import pytest

from world_of_taxanomy.mcp.handlers import (
    handle_translate_across_all_systems,
    handle_compare_sector,
    handle_find_by_keyword_all_systems,
    handle_get_crosswalk_coverage,
    handle_get_system_diff,
    handle_get_siblings,
    handle_get_subtree_summary,
    handle_resolve_ambiguous_code,
    handle_get_leaf_count,
    handle_get_region_mapping,
    handle_describe_match_types,
    handle_explore_industry_tree,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Tool 1: translate_across_all_systems ─────────────────────


def test_translate_across_all_systems(db_pool):
    """NAICS 6211 → every other system in one call."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_translate_across_all_systems(conn, {
                "system_id": "naics_2022",
                "code": "6211",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
            # Each entry must have target_system and target_code
            for entry in result:
                assert "target_system" in entry
                assert "target_code" in entry
                assert "match_type" in entry
                assert "target_title" in entry
            # isic_rev4 must be present
            target_systems = {e["target_system"] for e in result}
            assert "isic_rev4" in target_systems
    _run(_test())


def test_translate_across_all_systems_no_mappings(db_pool):
    """Code with no crosswalk edges returns empty list, not an error."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_translate_across_all_systems(conn, {
                "system_id": "naics_2022",
                "code": "62",  # division level - no crosswalk edges in seed
            })
            assert isinstance(result, list)
    _run(_test())


# ── Tool 2: compare_sector ────────────────────────────────────


def test_compare_sector(db_pool):
    """Side-by-side top-level sectors for two systems."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_compare_sector(conn, {
                "system_id_a": "naics_2022",
                "system_id_b": "isic_rev4",
            })
            assert "system_a" in result
            assert "system_b" in result
            assert isinstance(result["system_a"], list)
            assert isinstance(result["system_b"], list)
            # system_a should list NAICS top-level nodes
            assert len(result["system_a"]) >= 1
            assert len(result["system_b"]) >= 1
            for sector in result["system_a"]:
                assert "code" in sector
                assert "title" in sector
    _run(_test())


# ── Tool 3: find_by_keyword_all_systems ───────────────────────


def test_find_by_keyword_all_systems(db_pool):
    """Search returns results grouped by system."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_find_by_keyword_all_systems(conn, {
                "query": "agriculture",
            })
            assert isinstance(result, dict)
            # Keys are system IDs; values are lists of matching nodes
            for system_id, matches in result.items():
                assert isinstance(matches, list)
                for match in matches:
                    assert "code" in match
                    assert "title" in match
                    assert match["system_id"] == system_id
            # naics_2022 should match (Agriculture, Forestry...)
            assert "naics_2022" in result
    _run(_test())


def test_find_by_keyword_all_systems_with_limit(db_pool):
    """Per-system limit is respected."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_find_by_keyword_all_systems(conn, {
                "query": "production",
                "limit_per_system": 1,
            })
            for system_id, matches in result.items():
                assert len(matches) <= 1
    _run(_test())


# ── Tool 4: get_crosswalk_coverage ───────────────────────────


def test_get_crosswalk_coverage(db_pool):
    """Returns per-system-pair edge counts."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_crosswalk_coverage(conn, {})
            assert isinstance(result, list)
            assert len(result) >= 1
            for entry in result:
                assert "source_system" in entry
                assert "target_system" in entry
                assert "edge_count" in entry
                assert entry["edge_count"] > 0
    _run(_test())


def test_get_crosswalk_coverage_filtered(db_pool):
    """Filter to a specific system."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_crosswalk_coverage(conn, {
                "system_id": "naics_2022",
            })
            for entry in result:
                assert entry["source_system"] == "naics_2022" or \
                       entry["target_system"] == "naics_2022"
    _run(_test())


# ── Tool 5: get_system_diff ───────────────────────────────────


def test_get_system_diff(db_pool):
    """Codes in system A with no equivalence to system B."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_system_diff(conn, {
                "system_id_a": "naics_2022",
                "system_id_b": "isic_rev4",
            })
            assert isinstance(result, list)
            # Each entry is a NAICS node with no ISIC mapping
            for entry in result:
                assert "code" in entry
                assert "title" in entry
                assert entry["system_id"] == "naics_2022"
    _run(_test())


# ── Tool 6: get_siblings ──────────────────────────────────────


def test_get_siblings(db_pool):
    """Other nodes at the same level under the same parent."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_siblings(conn, {
                "system_id": "naics_2022",
                "code": "621",  # parent is 62 - sibling is none in seed (only child)
            })
            assert isinstance(result, list)
            # The node itself should NOT appear in siblings
            codes = [s["code"] for s in result]
            assert "621" not in codes
    _run(_test())


def test_get_siblings_multiple(db_pool):
    """Node with actual siblings returns them."""
    async def _test():
        async with db_pool.acquire() as conn:
            # ISIC 011 and 862 are both level-1 children under their section roots
            # 86 has 862 as child; let's use 8620 which has parent 862
            result = await handle_get_siblings(conn, {
                "system_id": "isic_rev4",
                "code": "0111",  # parent is 011 - only child in seed
            })
            assert isinstance(result, list)
    _run(_test())


# ── Tool 7: get_subtree_summary ───────────────────────────────


def test_get_subtree_summary(db_pool):
    """Returns count and leaf count for all nodes under a code."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_subtree_summary(conn, {
                "system_id": "naics_2022",
                "code": "62",
            })
            assert "code" in result
            assert "title" in result
            assert "total_nodes" in result
            assert "leaf_count" in result
            assert "max_depth" in result
            assert result["total_nodes"] >= 1
            assert result["leaf_count"] >= 1
    _run(_test())


# ── Tool 8: resolve_ambiguous_code ───────────────────────────


def test_resolve_ambiguous_code(db_pool):
    """Code '0111' exists in ISIC, SIC, and NAICS - lists all three."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_resolve_ambiguous_code(conn, {"code": "0111"})
            assert isinstance(result, list)
            assert len(result) >= 2  # exists in isic_rev4 and sic_1987
            system_ids = {entry["system_id"] for entry in result}
            assert "isic_rev4" in system_ids
            assert "sic_1987" in system_ids
            for entry in result:
                assert "code" in entry
                assert "title" in entry
                assert "system_id" in entry
    _run(_test())


def test_resolve_ambiguous_code_unique(db_pool):
    """Code that exists in only one system returns single-item list."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_resolve_ambiguous_code(conn, {"code": "6211"})
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["system_id"] == "naics_2022"
    _run(_test())


# ── Tool 9: get_leaf_count ────────────────────────────────────


def test_get_leaf_count(db_pool):
    """Returns leaf and total node counts per system."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_leaf_count(conn, {})
            assert isinstance(result, list)
            assert len(result) >= 2
            for entry in result:
                assert "system_id" in entry
                assert "total_nodes" in entry
                assert "leaf_nodes" in entry
                assert entry["leaf_nodes"] <= entry["total_nodes"]
    _run(_test())


def test_get_leaf_count_single_system(db_pool):
    """Filter to one system."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_leaf_count(conn, {"system_id": "naics_2022"})
            assert len(result) == 1
            assert result[0]["system_id"] == "naics_2022"
    _run(_test())


# ── Tool 10: get_region_mapping ───────────────────────────────


def test_get_region_mapping(db_pool):
    """Systems grouped by region."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_region_mapping(conn, {})
            assert isinstance(result, dict)
            # Keys are region names; values are lists of system summaries
            for region, systems in result.items():
                assert isinstance(systems, list)
                for s in systems:
                    assert "id" in s
                    assert "name" in s
            # Seed has North America (NAICS), Global (ISIC), USA/UK (SIC)
            all_ids = [s["id"] for systems in result.values() for s in systems]
            assert "naics_2022" in all_ids
            assert "isic_rev4" in all_ids
    _run(_test())


# ── Tool 11: describe_match_types ────────────────────────────


def test_describe_match_types(db_pool):
    """Returns static definitions for exact, partial, broad."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_describe_match_types(conn, {})
            assert isinstance(result, dict)
            assert "exact" in result
            assert "partial" in result
            assert "broad" in result
            for match_type, description in result.items():
                assert isinstance(description, str)
                assert len(description) > 10
    _run(_test())


# ── Tool 12: explore_industry_tree ───────────────────────────


def test_explore_industry_tree(db_pool):
    """Keyword → matches with ancestors + children context."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_explore_industry_tree(conn, {
                "query": "physician",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
            for entry in result:
                assert "system_id" in entry
                assert "code" in entry
                assert "title" in entry
                assert "ancestors" in entry
                assert "children" in entry
                assert isinstance(entry["ancestors"], list)
                assert isinstance(entry["children"], list)
    _run(_test())


def test_explore_industry_tree_with_system_filter(db_pool):
    """Filter tree exploration to a specific system."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_explore_industry_tree(conn, {
                "query": "farming",
                "system_id": "naics_2022",
            })
            for entry in result:
                assert entry["system_id"] == "naics_2022"
    _run(_test())


def test_explore_industry_tree_ancestors_ordered_root_first(db_pool):
    """Ancestors are ordered from root to parent (not reversed)."""
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_explore_industry_tree(conn, {
                "query": "soybean",
                "system_id": "naics_2022",
            })
            assert len(result) >= 1
            # soybean farming (111110) has ancestors: 11 → 111 → 1111 → 11111
            entry = next(e for e in result if e["code"] == "111110")
            ancestors = entry["ancestors"]
            assert len(ancestors) >= 2
            # Root has the lowest level number
            assert ancestors[0]["level"] <= ancestors[-1]["level"]
    _run(_test())
