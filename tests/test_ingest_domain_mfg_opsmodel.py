"""Tests for Manufacturing Operations Model (make-to-stock, make-to-order, engineer-to-order) domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mfg_opsmodel import (
    MFG_OPSMODEL_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mfg_opsmodel,
)


class TestDetermineLevel:
    def test_mts_category_is_level_1(self):
        assert _determine_level("dfpm_mts") == 1

    def test_batch_is_level_2(self):
        assert _determine_level("dfpm_mts_batch") == 2

    def test_mto_category_is_level_1(self):
        assert _determine_level("dfpm_mto") == 1


class TestDetermineParent:
    def test_mts_has_no_parent(self):
        assert _determine_parent("dfpm_mts") is None

    def test_batch_parent_is_mts(self):
        assert _determine_parent("dfpm_mts_batch") == "dfpm_mts"

    def test_custom_parent_is_mto(self):
        assert _determine_parent("dfpm_mto_custom") == "dfpm_mto"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(MFG_OPSMODEL_NODES) > 0

    def test_has_mts_category(self):
        codes = [n[0] for n in MFG_OPSMODEL_NODES]
        assert "dfpm_mts" in codes

    def test_has_mto_category(self):
        codes = [n[0] for n in MFG_OPSMODEL_NODES]
        assert "dfpm_mto" in codes

    def test_has_eto_category(self):
        codes = [n[0] for n in MFG_OPSMODEL_NODES]
        assert "dfpm_eto" in codes

    def test_has_batch_node(self):
        codes = [n[0] for n in MFG_OPSMODEL_NODES]
        assert "dfpm_mts_batch" in codes

    def test_has_custom_node(self):
        codes = [n[0] for n in MFG_OPSMODEL_NODES]
        assert "dfpm_mto_custom" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MFG_OPSMODEL_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MFG_OPSMODEL_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MFG_OPSMODEL_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MFG_OPSMODEL_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(MFG_OPSMODEL_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in MFG_OPSMODEL_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_mfg_opsmodel)
    assert isinstance(MFG_OPSMODEL_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mfg_opsmodel(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mfg_opsmodel'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mfg_opsmodel(conn)
            count2 = await ingest_domain_mfg_opsmodel(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
