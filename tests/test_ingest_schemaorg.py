"""Tests for schema.org type tree ingester.

Source: https://schema.org/version/latest/schemaorg-current-https.jsonld
The schema.org consortium publishes ~926 rdfs:Class definitions covering
web vocabulary types (Article, Person, Restaurant, MedicalCondition...).
We ingest the type hierarchy only; properties are out of scope per
inclusion policy (pure property vocabularies excluded).

Multi-parent classes (~57 of them) keep their first listed parent as the
canonical hierarchy edge; alternative parents are noted in the description.
"""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.schemaorg import (
    parse_schemaorg_jsonld,
    ingest_schemaorg,
    THING_ROOT,
)


DATA_FILE = "data/schemaorg-current-https.jsonld"
HAS_DATA = os.path.exists(DATA_FILE)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.skipif(not HAS_DATA, reason="schema.org JSON-LD not found")
class TestParser:
    def test_parses_at_least_700_types(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        # Verified count is ~926; floor at 700 (~75% of expected)
        assert len(nodes) >= 700, f"Expected >=700 nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        codes = [code for code, _t, _l, _p, _d in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        for code, title, _l, _p, _d in nodes:
            assert title and len(title) > 0, f"Empty title for {code}"

    def test_no_em_dashes_in_titles_or_descriptions(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        for code, title, _l, _p, desc in nodes:
            assert "\u2014" not in title, f"Em-dash in title of {code}"
            if desc:
                assert "\u2014" not in desc, f"Em-dash in description of {code}"

    def test_thing_is_level_1_root(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        thing_rows = [n for n in nodes if n[0] == THING_ROOT]
        assert len(thing_rows) == 1, "Thing should appear exactly once"
        code, _t, level, parent, _d = thing_rows[0]
        assert level == 1
        assert parent is None

    def test_parent_validity(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        codes = {n[0] for n in nodes}
        for code, _t, _l, parent, _d in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in node set"

    def test_codes_use_schema_local_name(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        for code, _t, _l, _p, _d in nodes:
            # Codes should be the schema.org local name with no prefix
            assert ":" not in code, f"Code {code} contains colon (should be unprefixed)"
            assert "/" not in code, f"Code {code} contains slash (should be unprefixed)"

    def test_descriptions_present_for_almost_all(self):
        nodes = parse_schemaorg_jsonld(DATA_FILE)
        with_desc = sum(1 for n in nodes if n[4] and len(n[4]) > 0)
        # schema.org publishes rdfs:comment for every class -> expect 100%
        coverage = with_desc / len(nodes) if nodes else 0
        assert coverage >= 0.99, f"Description coverage {coverage:.2%} below 99%"


@pytest.mark.skipif(not HAS_DATA, reason="schema.org JSON-LD not found")
class TestIngestIntegration:
    def test_ingest_writes_system_with_provenance(self, db_pool):
        async def _go():
            await ingest_schemaorg()
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "select id, data_provenance, source_file_hash, node_count "
                    "from classification_system where id='schema_org'"
                )
                assert row is not None
                assert row["data_provenance"] == "official_download"
                assert row["source_file_hash"] is not None
                assert row["node_count"] >= 700
        _run(_go())

    def test_ingest_idempotent(self, db_pool):
        async def _go():
            await ingest_schemaorg()
            async with db_pool.acquire() as conn:
                first = await conn.fetchval(
                    "select count(*) from classification_node where system_id='schema_org'"
                )
            await ingest_schemaorg()
            async with db_pool.acquire() as conn:
                second = await conn.fetchval(
                    "select count(*) from classification_node where system_id='schema_org'"
                )
            assert first == second
        _run(_go())
