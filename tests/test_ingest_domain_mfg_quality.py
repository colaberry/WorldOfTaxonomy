"""Tests for Manufacturing Quality and Compliance Framework domain taxonomy ingester.

RED tests - written before any implementation exists.

Manufacturing Quality taxonomy classifies what quality management and
regulatory compliance framework applies - orthogonal to process type and
industry vertical. ISO 9001 applies to any manufacturing process in any
industry; AS9100 applies specifically to aerospace regardless of whether
the process is machining, composites, or electronics.

Code prefix: dfpq_
Categories: General Quality Management Systems, Industry-Specific Quality
Standards, Regulatory and Product Safety Compliance, Statistical and Process
Control Methods.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mfg_quality import (
    MFG_QUALITY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mfg_quality,
)


class TestDetermineLevel:
    def test_qms_category_is_level_1(self):
        assert _determine_level("dfpq_qms") == 1

    def test_iso9001_is_level_2(self):
        assert _determine_level("dfpq_qms_iso9001") == 2

    def test_industry_category_is_level_1(self):
        assert _determine_level("dfpq_industry") == 1

    def test_as9100_is_level_2(self):
        assert _determine_level("dfpq_industry_as9100") == 2


class TestDetermineParent:
    def test_qms_has_no_parent(self):
        assert _determine_parent("dfpq_qms") is None

    def test_iso9001_parent_is_qms(self):
        assert _determine_parent("dfpq_qms_iso9001") == "dfpq_qms"

    def test_as9100_parent_is_industry(self):
        assert _determine_parent("dfpq_industry_as9100") == "dfpq_industry"


class TestMfgQualityNodes:
    def test_nodes_non_empty(self):
        assert len(MFG_QUALITY_NODES) > 0

    def test_has_qms_category(self):
        codes = [n[0] for n in MFG_QUALITY_NODES]
        assert "dfpq_qms" in codes

    def test_has_industry_category(self):
        codes = [n[0] for n in MFG_QUALITY_NODES]
        assert "dfpq_industry" in codes

    def test_has_regulatory_category(self):
        codes = [n[0] for n in MFG_QUALITY_NODES]
        assert "dfpq_regulatory" in codes

    def test_has_iso9001_node(self):
        codes = [n[0] for n in MFG_QUALITY_NODES]
        assert "dfpq_qms_iso9001" in codes

    def test_has_as9100_node(self):
        codes = [n[0] for n in MFG_QUALITY_NODES]
        assert "dfpq_industry_as9100" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MFG_QUALITY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MFG_QUALITY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MFG_QUALITY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MFG_QUALITY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(MFG_QUALITY_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in MFG_QUALITY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_mfg_quality_module_importable():
    assert callable(ingest_domain_mfg_quality)
    assert isinstance(MFG_QUALITY_NODES, list)


def test_ingest_domain_mfg_quality(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mfg_quality(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mfg_quality'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mfg_quality_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mfg_quality(conn)
            count2 = await ingest_domain_mfg_quality(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
