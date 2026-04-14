"""Tests for Workforce Safety Management System Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_workforce_sms import (
    WORKFORCE_SMS_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_workforce_sms,
)


class TestDetermineLevel:
    def test_iso45001_category_is_level_1(self):
        assert _determine_level("dwssms_iso45001") == 1

    def test_cert_is_level_2(self):
        assert _determine_level("dwssms_iso45001_cert") == 2

    def test_vpp_category_is_level_1(self):
        assert _determine_level("dwssms_vpp") == 1


class TestDetermineParent:
    def test_iso45001_has_no_parent(self):
        assert _determine_parent("dwssms_iso45001") is None

    def test_cert_parent_is_iso45001(self):
        assert _determine_parent("dwssms_iso45001_cert") == "dwssms_iso45001"

    def test_star_parent_is_vpp(self):
        assert _determine_parent("dwssms_vpp_star") == "dwssms_vpp"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(WORKFORCE_SMS_NODES) > 0

    def test_has_iso45001_category(self):
        codes = [n[0] for n in WORKFORCE_SMS_NODES]
        assert "dwssms_iso45001" in codes

    def test_has_vpp_category(self):
        codes = [n[0] for n in WORKFORCE_SMS_NODES]
        assert "dwssms_vpp" in codes

    def test_has_behavbased_category(self):
        codes = [n[0] for n in WORKFORCE_SMS_NODES]
        assert "dwssms_behavbased" in codes

    def test_has_cert_node(self):
        codes = [n[0] for n in WORKFORCE_SMS_NODES]
        assert "dwssms_iso45001_cert" in codes

    def test_has_star_node(self):
        codes = [n[0] for n in WORKFORCE_SMS_NODES]
        assert "dwssms_vpp_star" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in WORKFORCE_SMS_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in WORKFORCE_SMS_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in WORKFORCE_SMS_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in WORKFORCE_SMS_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(WORKFORCE_SMS_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in WORKFORCE_SMS_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_workforce_sms)
    assert isinstance(WORKFORCE_SMS_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_workforce_sms(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_workforce_sms'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_workforce_sms(conn)
            count2 = await ingest_domain_workforce_sms(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
