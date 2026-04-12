"""Tests for CFR Title 49 / FMCSA -> NAICS crosswalk ingester.

RED tests - written before any implementation exists.

This crosswalk links FMCSA regulatory categories and CFR Title 49 parts
to the NAICS codes they govern (primarily truck/transit transportation).

Key mappings:
  fmcsa_hos   -> naics_2022:484 (Truck Transportation)    match_type='broad'
  fmcsa_cdl   -> naics_2022:484 (Truck Transportation)    match_type='broad'
  fmcsa_eld   -> naics_2022:484 (Truck Transportation)    match_type='broad'
  fmcsa_hazmat -> naics_2022:484                           match_type='broad'
  cfr_title_49:49_395 -> naics_2022:484                   match_type='broad'
  cfr_title_49:49_395 -> naics_2022:485 (Transit)         match_type='broad'

Source: derived (fmcsa.dot.gov governs NAICS 484/485 carriers)
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.crosswalk_cfr_naics import ingest_crosswalk_cfr_naics


def test_crosswalk_cfr_naics_module_importable():
    assert callable(ingest_crosswalk_cfr_naics)


def test_ingest_crosswalk_cfr_naics(db_pool):
    """Integration test: FMCSA/CFR categories link to NAICS transportation codes."""
    async def _run():
        from world_of_taxanomy.ingest.cfr_title49 import ingest_cfr_title49
        from world_of_taxanomy.ingest.fmcsa_regs import ingest_fmcsa_regs
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_cfr_title49(conn)
            await ingest_fmcsa_regs(conn)
            await ingest_naics_2022(conn)

            count = await ingest_crosswalk_cfr_naics(conn)
            assert count >= 10, f"Expected >= 10 edges, got {count}"

            # FMCSA HOS should link to NAICS 484 (Truck Transportation)
            edge = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'fmcsa_regs' AND source_code = 'fmcsa_hos' "
                "AND target_system = 'naics_2022' AND target_code LIKE '484%'"
            )
            assert edge is not None, "fmcsa_hos -> naics 484xxx edge missing"
            assert edge["match_type"] == "broad"

            # CFR 49_395 (HOS) should link to NAICS 484
            cfr_edge = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'cfr_title_49' AND source_code = '49_395' "
                "AND target_system = 'naics_2022'"
            )
            assert cfr_edge is not None, "49_395 -> naics edge missing"

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_cfr_naics_idempotent(db_pool):
    """Running ingest twice returns same count."""
    async def _run():
        from world_of_taxanomy.ingest.cfr_title49 import ingest_cfr_title49
        from world_of_taxanomy.ingest.fmcsa_regs import ingest_fmcsa_regs
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_cfr_title49(conn)
            await ingest_fmcsa_regs(conn)
            await ingest_naics_2022(conn)
            count1 = await ingest_crosswalk_cfr_naics(conn)
            count2 = await ingest_crosswalk_cfr_naics(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
