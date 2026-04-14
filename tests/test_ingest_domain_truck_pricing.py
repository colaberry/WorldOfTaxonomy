"""Tests for Truck Pricing / Rate Structure domain taxonomy ingester.

RED tests - written before any implementation exists.

Trucking Pricing taxonomy organizes how freight is priced - orthogonal to
mode, vehicle, cargo, and carrier operations:
  Rate Structure  (dtp_rate*)  - spot, contract, tariff, quoted
  Fuel Surcharge  (dtp_fsc*)   - DOE index, flat per-mile, percentage, all-in
  Accessorial Charges (dtp_acc*) - liftgate, detention, residential, hazmat, etc.
  Rating Basis    (dtp_unit*)  - per-mile, per-cwt, per-pallet, per-lane

Stakeholders: rate desks, TMS rating engines, shippers, freight auditors.
Source: NMFC, UPS/FedEx tariff structures, DAT rate analytics. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_pricing import (
    PRICING_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_pricing,
)


class TestDetermineLevel:
    def test_rate_category_is_level_1(self):
        assert _determine_level("dtp_rate") == 1

    def test_spot_rate_is_level_2(self):
        assert _determine_level("dtp_rate_spot") == 2

    def test_fsc_category_is_level_1(self):
        assert _determine_level("dtp_fsc") == 1

    def test_fsc_doe_is_level_2(self):
        assert _determine_level("dtp_fsc_doe") == 2

    def test_acc_category_is_level_1(self):
        assert _determine_level("dtp_acc") == 1

    def test_liftgate_is_level_2(self):
        assert _determine_level("dtp_acc_lift") == 2

    def test_unit_category_is_level_1(self):
        assert _determine_level("dtp_unit") == 1

    def test_per_mile_is_level_2(self):
        assert _determine_level("dtp_unit_mile") == 2


class TestDetermineParent:
    def test_rate_category_has_no_parent(self):
        assert _determine_parent("dtp_rate") is None

    def test_spot_parent_is_rate(self):
        assert _determine_parent("dtp_rate_spot") == "dtp_rate"

    def test_fsc_doe_parent_is_fsc(self):
        assert _determine_parent("dtp_fsc_doe") == "dtp_fsc"

    def test_acc_lift_parent_is_acc(self):
        assert _determine_parent("dtp_acc_lift") == "dtp_acc"

    def test_unit_mile_parent_is_unit(self):
        assert _determine_parent("dtp_unit_mile") == "dtp_unit"


class TestPricingNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(PRICING_NODES) > 0

    def test_has_rate_structure_category(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_rate" in codes

    def test_has_fuel_surcharge_category(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_fsc" in codes

    def test_has_accessorial_category(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_acc" in codes

    def test_has_rating_basis_category(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_unit" in codes

    def test_has_spot_rate_node(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_rate_spot" in codes

    def test_has_contract_rate_node(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_rate_contract" in codes

    def test_has_liftgate_accessorial(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_acc_lift" in codes

    def test_has_detention_accessorial(self):
        codes = [n[0] for n in PRICING_NODES]
        assert "dtp_acc_det" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in PRICING_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in PRICING_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in PRICING_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in PRICING_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(PRICING_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in PRICING_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_truck_pricing_module_importable():
    assert callable(ingest_domain_truck_pricing)
    assert isinstance(PRICING_NODES, list)


def test_ingest_domain_truck_pricing(db_pool):
    """Integration test: pricing taxonomy rows + NAICS 484 links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_pricing(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_pricing'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_pricing'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_pricing_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_pricing(conn)
            count2 = await ingest_domain_truck_pricing(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
