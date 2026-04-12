"""Tests for FMCSA Regulatory Codes ingester.

RED tests - written before any implementation exists.

FMCSA = Federal Motor Carrier Safety Administration.
Published by US DOT/FMCSA. Public domain.
Reference: https://www.fmcsa.dot.gov/regulations

Hand-coded regulatory categories covering the major FMCSA program areas:
  - Hours of Service (HOS)
  - Electronic Logging Devices (ELD)
  - Commercial Driver's License (CDL)
  - Drug and Alcohol Testing (DAT)
  - Vehicle Inspection and Maintenance (VIM)
  - Hazardous Materials (HAZMAT)
  - Financial Responsibility (FR)
  - Operating Authority (OA)
  - Carrier Safety Fitness (CSF)

Hierarchy (2 levels):
  Category    (level 1, e.g. 'fmcsa_hos')     - regulatory program area
  Requirement (level 2, e.g. 'fmcsa_hos_1')   - specific requirement (leaf)

Codes: 'fmcsa_{category}' and 'fmcsa_{category}_{number}'
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.fmcsa_regs import (
    FMCSA_NODES,
    _determine_level,
    _determine_parent,
    ingest_fmcsa_regs,
)


class TestDetermineLevel:
    def test_category_code_is_level_1(self):
        # 'fmcsa_hos' = category
        assert _determine_level("fmcsa_hos") == 1

    def test_requirement_code_is_level_2(self):
        # 'fmcsa_hos_1' = specific requirement
        assert _determine_level("fmcsa_hos_1") == 2

    def test_eld_category_is_level_1(self):
        assert _determine_level("fmcsa_eld") == 1

    def test_eld_requirement_is_level_2(self):
        assert _determine_level("fmcsa_eld_3") == 2


class TestDetermineParent:
    def test_category_has_no_parent(self):
        assert _determine_parent("fmcsa_hos") is None

    def test_requirement_parent_is_category(self):
        assert _determine_parent("fmcsa_hos_1") == "fmcsa_hos"

    def test_eld_requirement_parent(self):
        assert _determine_parent("fmcsa_eld_3") == "fmcsa_eld"

    def test_cdl_requirement_parent(self):
        assert _determine_parent("fmcsa_cdl_2") == "fmcsa_cdl"


class TestFmcsaNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(FMCSA_NODES) > 0

    def test_all_codes_start_with_fmcsa(self):
        for code, title, level, parent in FMCSA_NODES:
            assert code.startswith("fmcsa_"), f"Code '{code}' does not start with 'fmcsa_'"

    def test_all_titles_non_empty(self):
        for code, title, level, parent in FMCSA_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in FMCSA_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_nodes_have_no_parent(self):
        for code, title, level, parent in FMCSA_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_nodes_have_parent(self):
        for code, title, level, parent in FMCSA_NODES:
            if level == 2:
                assert parent is not None


def test_fmcsa_regs_module_importable():
    assert callable(ingest_fmcsa_regs)
    assert isinstance(FMCSA_NODES, list)


def test_ingest_fmcsa_regs(db_pool):
    """Integration test: ingest FMCSA regulatory nodes."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_fmcsa_regs(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system "
                "WHERE id = 'fmcsa_regs'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Level 1 nodes have no parent and are not leaves
            cat = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'fmcsa_regs' AND level = 1 LIMIT 1"
            )
            assert cat is not None
            assert cat["level"] == 1
            assert cat["parent_code"] is None
            assert cat["is_leaf"] is False

            # Level 2 nodes are leaves
            req = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'fmcsa_regs' AND level = 2 LIMIT 1"
            )
            assert req is not None
            assert req["is_leaf"] is True

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_fmcsa_regs_idempotent(db_pool):
    """Running ingest twice returns same count."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_fmcsa_regs(conn)
            count2 = await ingest_fmcsa_regs(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
