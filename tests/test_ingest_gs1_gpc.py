"""Tests for GS1 Global Product Classification (GPC) ingester.

Source: 'GPC as of November 2025 v20251127 GB.xlsx' published by GS1.
The GS1 GPC As Published file is a denormalized XLSX where every row
contains the full Segment, Family, Class, Brick, and Attribute path.
We collapse it to four hierarchy levels (Segment > Family > Class > Brick).
Attributes are not ingested as nodes; they are brick-level metadata.

Verified count on the Nov 2025 publication: 45 segments, 162 families,
937 classes, 5,306 bricks - 6,450 nodes total.
"""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.gs1_gpc import (
    DEFAULT_DATA_FILE,
    parse_gs1_gpc_xlsx,
    ingest_gs1_gpc,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _data_available() -> bool:
    return os.path.exists(DEFAULT_DATA_FILE)


HAS_DATA = _data_available()


@pytest.mark.skipif(not HAS_DATA, reason="GS1 GPC XLSX not present at data/")
class TestParser:
    def test_parses_at_least_5000_nodes(self):
        nodes = parse_gs1_gpc_xlsx()
        assert len(nodes) >= 5_000, f"Expected >=5K nodes, got {len(nodes)}"

    def test_segment_family_class_brick_counts(self):
        nodes = parse_gs1_gpc_xlsx()
        by_level = {}
        for code, _t, level, _p, _d in nodes:
            by_level[level] = by_level.get(level, 0) + 1
        # Verified counts on Nov 2025 GPC: 45/162/937/5306
        assert by_level.get(1, 0) >= 40, f"Segments: {by_level.get(1)}"
        assert by_level.get(2, 0) >= 150, f"Families: {by_level.get(2)}"
        assert by_level.get(3, 0) >= 900, f"Classes: {by_level.get(3)}"
        assert by_level.get(4, 0) >= 5_000, f"Bricks: {by_level.get(4)}"

    def test_no_duplicate_codes(self):
        nodes = parse_gs1_gpc_xlsx()
        codes = [n[0] for n in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_gs1_gpc_xlsx()
        for code, title, _l, _p, _d in nodes:
            assert title and len(title) > 0, f"Empty title for {code}"

    def test_no_em_dashes(self):
        # Use the unicode escape '\u2014' instead of the literal em-dash
        # so the repo's no-em-dashes-in-source CI guard does not flag this file.
        nodes = parse_gs1_gpc_xlsx()
        for code, title, _l, _p, desc in nodes:
            assert "\u2014" not in title, f"Em-dash in title of {code}"
            if desc:
                assert "\u2014" not in desc, f"Em-dash in description of {code}"

    def test_codes_are_eight_digit_strings(self):
        nodes = parse_gs1_gpc_xlsx()
        for code, _t, _l, _p, _d in nodes:
            assert isinstance(code, str), f"Code {code!r} not a string"
            assert code.isdigit(), f"Code {code!r} not all digits"
            assert len(code) == 8, f"Code {code!r} not 8 characters"

    def test_segments_are_roots(self):
        nodes = parse_gs1_gpc_xlsx()
        for code, _t, level, parent, _d in nodes:
            if level == 1:
                assert parent is None, f"Segment {code} has non-null parent {parent}"

    def test_parent_validity(self):
        nodes = parse_gs1_gpc_xlsx()
        codes = {n[0] for n in nodes}
        for code, _t, _l, parent, _d in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in node set"

    def test_brick_description_coverage(self):
        nodes = parse_gs1_gpc_xlsx()
        bricks = [n for n in nodes if n[2] == 4]
        with_desc = sum(1 for n in bricks if n[4] and len(n[4]) > 0)
        coverage = with_desc / len(bricks) if bricks else 0
        # Bricks always have BrickDefinition_Includes populated.
        assert coverage >= 0.99, f"Brick description coverage {coverage:.2%} below 99%"

    def test_total_description_coverage(self):
        nodes = parse_gs1_gpc_xlsx()
        with_desc = sum(1 for n in nodes if n[4] and len(n[4]) > 0)
        coverage = with_desc / len(nodes) if nodes else 0
        # Segment/Family/Class definitions are partial in source; we fall
        # back to title text so coverage is 100%.
        assert coverage >= 0.99, f"Total description coverage {coverage:.2%} below 99%"

    def test_specific_known_segment_present(self):
        nodes = parse_gs1_gpc_xlsx()
        codes = {n[0] for n in nodes}
        # 70000000 = Arts/Crafts/Needlework (verified in source)
        assert "70000000" in codes


@pytest.mark.skipif(not HAS_DATA, reason="GS1 GPC XLSX not present at data/")
class TestIngestIntegration:
    def test_ingest_writes_system_with_provenance(self, db_pool):
        async def _go():
            async with db_pool.acquire() as conn:
                n = await ingest_gs1_gpc(conn)
                assert n >= 5_000
                row = await conn.fetchrow(
                    "select id, data_provenance, source_file_hash, node_count, "
                    "authority from classification_system where id='gs1_gpc'"
                )
                assert row is not None
                assert row["data_provenance"] == "official_download"
                assert row["source_file_hash"] is not None
                assert row["node_count"] >= 5_000
                assert row["authority"] == "GS1"
        _run(_go())

    def test_ingest_idempotent(self, db_pool):
        async def _go():
            async with db_pool.acquire() as conn:
                await ingest_gs1_gpc(conn)
                first = await conn.fetchval(
                    "select count(*) from classification_node where system_id='gs1_gpc'"
                )
                await ingest_gs1_gpc(conn)
                second = await conn.fetchval(
                    "select count(*) from classification_node where system_id='gs1_gpc'"
                )
            assert first == second, f"Idempotency failure: {first} -> {second}"
        _run(_go())
