"""Tests for Agricultural Post-harvest / Value Chain Processing taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Post-harvest taxonomy classifies what happens to farm output
AFTER it leaves the field - orthogonal to crop type, farming method, and
market channel. The same corn bushel can go to an on-farm bin, a commercial
elevator, wet mill, dry mill, ethanol plant, or export terminal - each step
adding value and changing the regulatory and logistical requirements.

Code prefix: daph_
Categories: On-Farm Storage, Commercial Storage and Handling, Primary
Processing, Secondary / Value-Added Processing, Cold Chain and Perishable
Handling, Packaging and Labeling, Traceability and Certification.

Stakeholders: food processors, grain merchandisers, cold chain logistics
providers, USDA FSIS/AMS inspection staff, retailers requiring supply chain
transparency, carbon offset registries tracking stored carbon.
Source: USDA AMS, USDA NASS grain storage surveys, FDA FSMA Rule 204,
GS1 traceability standards. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_postharvest import (
    AG_POSTHARVEST_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_postharvest,
)


class TestDetermineLevel:
    def test_onfarm_storage_category_is_level_1(self):
        assert _determine_level("daph_storage") == 1

    def test_grain_bin_is_level_2(self):
        assert _determine_level("daph_storage_bin") == 2

    def test_primary_processing_category_is_level_1(self):
        assert _determine_level("daph_primary") == 1

    def test_milling_is_level_2(self):
        assert _determine_level("daph_primary_mill") == 2

    def test_coldchain_category_is_level_1(self):
        assert _determine_level("daph_cold") == 1


class TestDetermineParent:
    def test_storage_category_has_no_parent(self):
        assert _determine_parent("daph_storage") is None

    def test_bin_parent_is_storage(self):
        assert _determine_parent("daph_storage_bin") == "daph_storage"

    def test_mill_parent_is_primary(self):
        assert _determine_parent("daph_primary_mill") == "daph_primary"

    def test_cold_reefer_parent_is_cold(self):
        assert _determine_parent("daph_cold_reefer") == "daph_cold"


class TestAgPostharvestNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_POSTHARVEST_NODES) > 0

    def test_has_storage_category(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_storage" in codes

    def test_has_primary_processing_category(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_primary" in codes

    def test_has_value_added_category(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_valueadd" in codes

    def test_has_cold_chain_category(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_cold" in codes

    def test_has_packaging_category(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_pack" in codes

    def test_has_grain_bin_node(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_storage_bin" in codes

    def test_has_milling_node(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert "daph_primary_mill" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_POSTHARVEST_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_POSTHARVEST_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_POSTHARVEST_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_POSTHARVEST_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_POSTHARVEST_NODES) >= 25

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_POSTHARVEST_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_postharvest_module_importable():
    assert callable(ingest_domain_ag_postharvest)
    assert isinstance(AG_POSTHARVEST_NODES, list)


def test_ingest_domain_ag_postharvest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_postharvest(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_postharvest'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_postharvest'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_postharvest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_postharvest(conn)
            count2 = await ingest_domain_ag_postharvest(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
