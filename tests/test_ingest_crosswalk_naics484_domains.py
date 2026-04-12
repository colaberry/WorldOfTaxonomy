"""Tests for NAICS 484 -> all truck domain taxonomies crosswalk ingester.

RED tests - written before any implementation exists.

Links all NAICS 484xxx nodes to all five truck domain taxonomies
(freight, vehicle, cargo, ops) plus also extends links to NAICS 485xxx
(transit/ground transportation), 492xxx (couriers/messengers), 4911xx (rail).

Source: Derived from NAICS industry scope. Open.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.crosswalk_naics484_domains import (
    NAICS_DOMAIN_LINKS,
    ingest_crosswalk_naics484_domains,
)


class TestNaicsDomainLinks:
    def test_links_is_non_empty(self):
        assert len(NAICS_DOMAIN_LINKS) > 0

    def test_links_are_tuples_of_four(self):
        for m in NAICS_DOMAIN_LINKS:
            assert len(m) == 4, f"Expected 4-tuple, got {len(m)}: {m}"

    def test_has_naics484_to_truck_freight(self):
        targets = [(naics, domain) for naics, naics_sys, domain, domain_sys in NAICS_DOMAIN_LINKS]
        freight_links = [t for t in targets if t[1] == "domain_truck_freight"]
        assert len(freight_links) > 0

    def test_has_naics484_to_truck_vehicle(self):
        targets = [(naics, domain) for naics, naics_sys, domain, domain_sys in NAICS_DOMAIN_LINKS]
        vehicle_links = [t for t in targets if t[1] == "domain_truck_vehicle"]
        assert len(vehicle_links) > 0

    def test_has_naics484_to_truck_cargo(self):
        targets = [(naics, domain) for naics, naics_sys, domain, domain_sys in NAICS_DOMAIN_LINKS]
        cargo_links = [t for t in targets if t[1] == "domain_truck_cargo"]
        assert len(cargo_links) > 0

    def test_has_naics484_to_truck_ops(self):
        targets = [(naics, domain) for naics, naics_sys, domain, domain_sys in NAICS_DOMAIN_LINKS]
        ops_links = [t for t in targets if t[1] == "domain_truck_ops"]
        assert len(ops_links) > 0

    def test_all_naics_systems_are_naics_2022(self):
        for naics, naics_sys, domain, domain_sys in NAICS_DOMAIN_LINKS:
            assert naics_sys == "naics_2022", f"Unexpected NAICS system: {naics_sys}"

    def test_no_duplicate_pairs(self):
        pairs = [(naics, domain) for naics, naics_sys, domain, domain_sys in NAICS_DOMAIN_LINKS]
        assert len(pairs) == len(set(pairs))


def test_crosswalk_naics484_domains_module_importable():
    assert callable(ingest_crosswalk_naics484_domains)
    assert isinstance(NAICS_DOMAIN_LINKS, list)


def test_ingest_crosswalk_naics484_domains(db_pool):
    """Integration test: edges linking NAICS 484 to all truck domain taxonomies."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        from world_of_taxanomy.ingest.domain_truck_freight import ingest_domain_truck_freight
        from world_of_taxanomy.ingest.domain_truck_vehicle import ingest_domain_truck_vehicle
        from world_of_taxanomy.ingest.domain_truck_cargo import ingest_domain_truck_cargo
        from world_of_taxanomy.ingest.domain_truck_ops import ingest_domain_truck_ops
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            await ingest_domain_truck_freight(conn)
            await ingest_domain_truck_vehicle(conn)
            await ingest_domain_truck_cargo(conn)
            await ingest_domain_truck_ops(conn)
            count = await ingest_crosswalk_naics484_domains(conn)
            assert count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_naics484_domains_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        from world_of_taxanomy.ingest.domain_truck_freight import ingest_domain_truck_freight
        from world_of_taxanomy.ingest.domain_truck_vehicle import ingest_domain_truck_vehicle
        from world_of_taxanomy.ingest.domain_truck_cargo import ingest_domain_truck_cargo
        from world_of_taxanomy.ingest.domain_truck_ops import ingest_domain_truck_ops
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            await ingest_domain_truck_freight(conn)
            await ingest_domain_truck_vehicle(conn)
            await ingest_domain_truck_cargo(conn)
            await ingest_domain_truck_ops(conn)
            count1 = await ingest_crosswalk_naics484_domains(conn)
            count2 = await ingest_crosswalk_naics484_domains(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
