"""Tests for GeoNames feature codes ingester.

GeoNames publishes a hierarchical classification of geographic features
(populated places, administrative divisions, hydrographic features,
terrain, etc). Source format is TSV with columns:
    <class>.<code> TAB name TAB description

We model this as a 2-level hierarchy:
    Level 1: 9 feature classes (A, P, H, L, R, S, T, U, V)
    Level 2: ~684 individual feature codes

Source rows that are sentinel placeholders ("null\\tnot available") are
skipped at parse time.
"""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.geonames_features import (
    FEATURE_CLASSES,
    parse_feature_codes_file,
    ingest_geonames_features,
)


DATA_FILE = "data/geonames_featureCodes_en.txt"
HAS_DATA = os.path.exists(DATA_FILE)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Unit tests: FEATURE_CLASSES table
# ---------------------------------------------------------------------------


class TestFeatureClasses:
    def test_exactly_9_classes(self):
        assert len(FEATURE_CLASSES) == 9

    def test_class_codes_are_single_letters(self):
        for code in FEATURE_CLASSES:
            assert len(code) == 1
            assert code.isalpha()
            assert code.isupper()

    def test_classes_cover_publisher_set(self):
        expected = {"A", "P", "H", "L", "R", "S", "T", "U", "V"}
        assert set(FEATURE_CLASSES.keys()) == expected

    def test_all_titles_non_empty(self):
        for code, (title, _desc) in FEATURE_CLASSES.items():
            assert len(title) > 0, f"Class {code} has empty title"

    def test_no_em_dashes(self):
        for code, (title, desc) in FEATURE_CLASSES.items():
            assert "\u2014" not in title
            assert "\u2014" not in desc

    def test_specific_class_titles(self):
        assert FEATURE_CLASSES["A"][0].lower().startswith("country")
        assert FEATURE_CLASSES["P"][0].lower().startswith("city") or \
               FEATURE_CLASSES["P"][0].lower().startswith("populated")
        assert FEATURE_CLASSES["H"][0].lower().startswith("stream") or \
               FEATURE_CLASSES["H"][0].lower().startswith("hydrographic")


# ---------------------------------------------------------------------------
# Unit tests: parser (file-based, skipped if data file absent)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_DATA, reason="GeoNames data file not found")
class TestParser:
    def test_parses_at_least_600_codes(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        # 9 class roots + 684 feature codes = 693, allow 80% floor
        assert len(nodes) >= 600, f"Expected >=600 nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        codes = [code for code, _title, _level, _parent, _desc in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        for code, title, _level, _parent, _desc in nodes:
            assert title and len(title) > 0, f"Empty title for {code}"

    def test_no_em_dashes_in_titles_or_descriptions(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        for code, title, _level, _parent, desc in nodes:
            assert "\u2014" not in title, f"Em-dash in title of {code}"
            if desc:
                assert "\u2014" not in desc, f"Em-dash in description of {code}"

    def test_level_1_roots_have_no_parent(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        roots = [n for n in nodes if n[2] == 1]
        assert len(roots) == 9, f"Expected 9 class roots, got {len(roots)}"
        for code, _title, _level, parent, _desc in roots:
            assert parent is None, f"Root {code} has parent {parent}"

    def test_parent_validity(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        codes = {n[0] for n in nodes}
        for code, _title, _level, parent, _desc in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in node set"

    def test_level_2_codes_use_dot_notation(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        for code, _title, level, _parent, _desc in nodes:
            if level == 2:
                assert "." in code, f"Level-2 code {code} missing dot"
                cls = code.split(".", 1)[0]
                assert cls in FEATURE_CLASSES, f"Unknown class {cls} in {code}"

    def test_skips_null_sentinel_row(self):
        nodes = parse_feature_codes_file(DATA_FILE)
        codes = {n[0] for n in nodes}
        assert "null" not in codes, "Null sentinel row should be skipped"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_DATA, reason="GeoNames data file not found")
class TestIngestIntegration:
    def test_ingest_writes_system_with_provenance(self, db_pool):
        async def _go():
            await ingest_geonames_features()
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "select id, data_provenance, source_file_hash, node_count "
                    "from classification_system where id='geonames_features'"
                )
                assert row is not None
                assert row["data_provenance"] == "official_download"
                assert row["source_file_hash"] is not None
                assert row["node_count"] >= 600
        _run(_go())

    def test_ingest_idempotent(self, db_pool):
        async def _go():
            await ingest_geonames_features()
            async with db_pool.acquire() as conn:
                first = await conn.fetchval(
                    "select count(*) from classification_node where system_id='geonames_features'"
                )
            await ingest_geonames_features()
            async with db_pool.acquire() as conn:
                second = await conn.fetchval(
                    "select count(*) from classification_node where system_id='geonames_features'"
                )
            assert first == second, f"Idempotency failure: {first} -> {second}"
        _run(_go())
