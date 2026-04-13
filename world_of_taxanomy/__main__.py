"""CLI entry point for WorldOfTaxanomy.

Usage:
    python -m world_of_taxanomy init
    python -m world_of_taxanomy ingest {naics,isic,nic,nace,sic,anzsic,jsic,wz,onace,noga,crosswalk,all}
    python -m world_of_taxanomy browse <system_id> [code]
    python -m world_of_taxanomy search <query> [--system SYSTEM] [--limit N]
    python -m world_of_taxanomy equiv <system_id> <code> [--target TARGET]
    python -m world_of_taxanomy stats
"""

import argparse
import sys


def _run(coro):
    """Run an async coroutine synchronously."""
    import asyncio
    return asyncio.run(coro)


# ── Commands ──────────────────────────────────────────────────


def cmd_init(args):
    """Initialize the database schema."""
    from world_of_taxanomy.db import init_db
    print("Initializing database schema...")
    _run(init_db())
    print("Done. Tables created.")


def cmd_init_auth(args):
    """Initialize the auth database schema."""
    from world_of_taxanomy.db import init_auth_db
    print("Initializing auth database schema...")
    _run(init_auth_db())
    print("Done. Auth tables created.")


def cmd_reset(args):
    """Drop and recreate all tables."""
    from world_of_taxanomy.db import reset_db
    print("Resetting database (dropping all tables)...")
    _run(reset_db())
    print("Done. Fresh schema ready.")


def cmd_ingest(args):
    """Ingest classification data."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _ingest():
        pool = await get_pool()
        async with pool.acquire() as conn:
            target = args.target

            if target in ("naics", "all"):
                from world_of_taxanomy.ingest.naics import ingest_naics_2022
                print("\n── NAICS 2022 ──")
                await ingest_naics_2022(conn)

            if target in ("isic", "all"):
                from world_of_taxanomy.ingest.isic import ingest_isic_rev4
                print("\n── ISIC Rev 4 ──")
                await ingest_isic_rev4(conn)

            if target in ("nic", "all"):
                from world_of_taxanomy.ingest.nic import ingest_nic_2008
                print("\n── NIC 2008 ──")
                await ingest_nic_2008(conn)

            if target in ("nace", "all"):
                from world_of_taxanomy.ingest.nace import ingest_nace_rev2, ingest_nace_isic_crosswalk
                print("\n── NACE Rev 2 ──")
                await ingest_nace_rev2(conn)
                print("\n── Crosswalk (NACE ↔ ISIC) ──")
                await ingest_nace_isic_crosswalk(conn)

            if target in ("sic", "all"):
                from world_of_taxanomy.ingest.sic import ingest_sic_1987
                print("\n── SIC 1987 ──")
                await ingest_sic_1987(conn)

            if target in ("anzsic", "all"):
                from world_of_taxanomy.ingest.anzsic import ingest_anzsic_2006
                print("\n── ANZSIC 2006 ──")
                await ingest_anzsic_2006(conn)

            if target in ("jsic", "all"):
                from world_of_taxanomy.ingest.jsic import ingest_jsic_2013
                print("\n── JSIC 2013 ──")
                await ingest_jsic_2013(conn)

            if target in ("wz", "all"):
                from world_of_taxanomy.ingest.nace_derived import ingest_wz_2008
                print("\n── WZ 2008 (derived from NACE) ──")
                await ingest_wz_2008(conn)

            if target in ("onace", "all"):
                from world_of_taxanomy.ingest.nace_derived import ingest_onace_2008
                print("\n── ÖNACE 2008 (derived from NACE) ──")
                await ingest_onace_2008(conn)

            if target in ("noga", "all"):
                from world_of_taxanomy.ingest.nace_derived import ingest_noga_2008
                print("\n── NOGA 2008 (derived from NACE) ──")
                await ingest_noga_2008(conn)

            if target in ("crosswalk", "all"):
                from world_of_taxanomy.ingest.crosswalk import ingest_crosswalk
                print("\n-- Crosswalk (NAICS / ISIC) --")
                await ingest_crosswalk(conn)

            if target in ("iso3166_1", "all"):
                from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1
                print("\n-- ISO 3166-1 Countries --")
                n = await ingest_iso3166_1(conn)
                print(f"  {n} nodes")

            if target in ("iso3166_2", "all"):
                from world_of_taxanomy.ingest.iso3166_2 import ingest_iso3166_2
                print("\n-- ISO 3166-2 Subdivisions --")
                n = await ingest_iso3166_2(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_iso3166", "all"):
                from world_of_taxanomy.ingest.crosswalk_iso3166 import ingest_crosswalk_iso3166
                print("\n-- Crosswalk (ISO 3166-1 / ISO 3166-2) --")
                n = await ingest_crosswalk_iso3166(conn)
                print(f"  {n} edges")

            if target in ("un_m49", "all"):
                from world_of_taxanomy.ingest.un_m49 import ingest_un_m49
                print("\n-- UN M.49 Geographic Regions --")
                n = await ingest_un_m49(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_un_m49_iso3166", "all"):
                from world_of_taxanomy.ingest.crosswalk_un_m49_iso3166 import ingest_crosswalk_un_m49_iso3166
                print("\n-- Crosswalk (UN M.49 / ISO 3166-1) --")
                n = await ingest_crosswalk_un_m49_iso3166(conn)
                print(f"  {n} edges")

            if target in ("hs2022", "all"):
                from world_of_taxanomy.ingest.hs2022 import ingest_hs2022
                print("\n-- HS 2022 Harmonized System --")
                n = await ingest_hs2022(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_hs_isic", "all"):
                from world_of_taxanomy.ingest.crosswalk_hs_isic import ingest_crosswalk_hs_isic
                print("\n-- Crosswalk (HS 2022 / ISIC Rev 4) --")
                n = await ingest_crosswalk_hs_isic(conn)
                print(f"  {n} edges")

            if target in ("cpc_v21", "all"):
                from world_of_taxanomy.ingest.cpc_v21 import ingest_cpc_v21
                print("\n-- CPC v2.1 Central Product Classification --")
                n = await ingest_cpc_v21(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cpc_isic", "all"):
                from world_of_taxanomy.ingest.crosswalk_cpc import ingest_crosswalk_cpc_isic
                print("\n-- Crosswalk (CPC v2.1 / ISIC Rev 4) --")
                n = await ingest_crosswalk_cpc_isic(conn)
                print(f"  {n} edges")

            if target in ("crosswalk_cpc_hs", "all"):
                from world_of_taxanomy.ingest.crosswalk_cpc import ingest_crosswalk_cpc_hs
                print("\n-- Crosswalk (HS 2022 / CPC v2.1) --")
                n = await ingest_crosswalk_cpc_hs(conn)
                print(f"  {n} edges")

            if target in ("unspsc_v24", "all"):
                from world_of_taxanomy.ingest.unspsc import ingest_unspsc
                print("\n-- UNSPSC v24 --")
                n = await ingest_unspsc(conn)
                print(f"  {n} nodes")

            if target in ("soc_2018", "all"):
                from world_of_taxanomy.ingest.soc_2018 import ingest_soc_2018
                print("\n-- SOC 2018 --")
                n = await ingest_soc_2018(conn)
                print(f"  {n} nodes")

            if target in ("isco_08", "all"):
                from world_of_taxanomy.ingest.isco_08 import ingest_isco_08
                print("\n-- ISCO-08 --")
                n = await ingest_isco_08(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_soc_isco", "all"):
                from world_of_taxanomy.ingest.crosswalk_soc_isco import ingest_crosswalk_soc_isco
                print("\n-- Crosswalk (SOC 2018 / ISCO-08) --")
                n = await ingest_crosswalk_soc_isco(conn)
                print(f"  {n} edges")

            if target in ("cip_2020", "all"):
                from world_of_taxanomy.ingest.cip_2020 import ingest_cip_2020
                print("\n-- CIP 2020 --")
                n = await ingest_cip_2020(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cip_soc", "all"):
                from world_of_taxanomy.ingest.crosswalk_cip_soc import ingest_crosswalk_cip_soc
                print("\n-- Crosswalk (CIP 2020 / SOC 2018) --")
                n = await ingest_crosswalk_cip_soc(conn)
                print(f"  {n} edges")

            if target in ("isced_2011", "all"):
                from world_of_taxanomy.ingest.isced_2011 import ingest_isced_2011
                print("\n-- ISCED 2011 (Education Levels) --")
                n = await ingest_isced_2011(conn)
                print(f"  {n} nodes")

            if target in ("iscedf_2013", "all"):
                from world_of_taxanomy.ingest.iscedf_2013 import ingest_iscedf_2013
                print("\n-- ISCED-F 2013 (Fields of Education) --")
                n = await ingest_iscedf_2013(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cip_iscedf", "all"):
                from world_of_taxanomy.ingest.crosswalk_cip_iscedf import ingest_crosswalk_cip_iscedf
                print("\n-- Crosswalk (CIP 2020 / ISCED-F 2013) --")
                n = await ingest_crosswalk_cip_iscedf(conn)
                print(f"  {n} edges")

            if target in ("atc_who", "all"):
                from world_of_taxanomy.ingest.atc_who import ingest_atc_who
                print("\n-- ATC WHO 2021 (Drug Classification) --")
                n = await ingest_atc_who(conn)
                print(f"  {n} nodes")

            if target in ("icd_11", "all"):
                from world_of_taxanomy.ingest.icd_11 import ingest_icd_11
                print("\n-- ICD-11 MMS (WHO, requires manual download) --")
                n = await ingest_icd_11(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_icd_isic", "all"):
                from world_of_taxanomy.ingest.crosswalk_icd_isic import ingest_crosswalk_icd_isic
                print("\n-- Crosswalk (ICD-11 / ISIC Rev 4) --")
                n = await ingest_crosswalk_icd_isic(conn)
                print(f"  {n} edges")

            if target in ("loinc", "all"):
                from world_of_taxanomy.ingest.loinc import ingest_loinc
                print("\n-- LOINC (requires manual download from loinc.org) --")
                n = await ingest_loinc(conn)
                print(f"  {n} nodes")

            if target in ("cofog", "all"):
                from world_of_taxanomy.ingest.cofog import ingest_cofog
                print("\n-- COFOG (Classification of the Functions of Government) --")
                n = await ingest_cofog(conn)
                print(f"  {n} nodes")

            if target in ("gics_bridge", "all"):
                from world_of_taxanomy.ingest.gics_bridge import ingest_gics_bridge
                print("\n-- GICS Bridge (11 public sector names only, MSCI/S&P proprietary) --")
                n = await ingest_gics_bridge(conn)
                print(f"  {n} nodes")

            if target in ("ghg_protocol", "all"):
                from world_of_taxanomy.ingest.ghg_protocol import ingest_ghg_protocol
                print("\n-- GHG Protocol (Scope 1/2/3 framework, WRI/WBCSD) --")
                n = await ingest_ghg_protocol(conn)
                print(f"  {n} nodes")

            if target in ("esco_occupations", "all"):
                from world_of_taxanomy.ingest.esco_occupations import ingest_esco_occupations
                print("\n-- ESCO Occupations (EU Commission, CC BY 4.0) --")
                n = await ingest_esco_occupations(conn)
                print(f"  {n} nodes")

            if target in ("esco_skills", "all"):
                from world_of_taxanomy.ingest.esco_skills import ingest_esco_skills
                print("\n-- ESCO Skills (EU Commission, CC BY 4.0) --")
                n = await ingest_esco_skills(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_esco_isco", "all"):
                from world_of_taxanomy.ingest.crosswalk_esco_isco import ingest_crosswalk_esco_isco
                print("\n-- Crosswalk (ESCO Occupations / ISCO-08) --")
                n = await ingest_crosswalk_esco_isco(conn)
                print(f"  {n} edges")

            if target in ("onet_soc", "all"):
                from world_of_taxanomy.ingest.onet_soc import ingest_onet_soc
                print("\n-- O*NET-SOC (US DOL, CC BY 4.0) --")
                n = await ingest_onet_soc(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_onet_soc", "all"):
                from world_of_taxanomy.ingest.crosswalk_onet_soc import ingest_crosswalk_onet_soc
                print("\n-- Crosswalk (O*NET-SOC / SOC 2018) --")
                n = await ingest_crosswalk_onet_soc(conn)
                print(f"  {n} edges")

            if target in ("patent_cpc", "all"):
                from world_of_taxanomy.ingest.patent_cpc import ingest_patent_cpc
                print("\n-- Patent CPC (~260K codes, EPO/USPTO, open) --")
                n = await ingest_patent_cpc(conn)
                print(f"  {n} nodes")

            if target in ("cfr_title_49", "all"):
                from world_of_taxanomy.ingest.cfr_title49 import ingest_cfr_title49
                print("\n-- CFR Title 49 - Transportation (hand-coded, public domain) --")
                n = await ingest_cfr_title49(conn)
                print(f"  {n} nodes")

            if target in ("fmcsa_regs", "all"):
                from world_of_taxanomy.ingest.fmcsa_regs import ingest_fmcsa_regs
                print("\n-- FMCSA Regulatory Codes (hand-coded, public domain) --")
                n = await ingest_fmcsa_regs(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cfr_naics", "all"):
                from world_of_taxanomy.ingest.crosswalk_cfr_naics import ingest_crosswalk_cfr_naics
                print("\n-- Crosswalk (CFR Title 49 + FMCSA / NAICS) --")
                n = await ingest_crosswalk_cfr_naics(conn)
                print(f"  {n} edges")

            if target in ("gdpr", "all"):
                from world_of_taxanomy.ingest.gdpr import ingest_gdpr
                print("\n-- GDPR Articles (EU 2016/679, hand-coded, open) --")
                n = await ingest_gdpr(conn)
                print(f"  {n} nodes")

            if target in ("iso_31000", "all"):
                from world_of_taxanomy.ingest.iso31000 import ingest_iso31000
                print("\n-- ISO 31000 Risk Framework (hand-coded, open) --")
                n = await ingest_iso31000(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_freight", "all"):
                from world_of_taxanomy.ingest.domain_truck_freight import ingest_domain_truck_freight
                print("\n-- Domain: Truck Freight Types (hand-coded, open) --")
                n = await ingest_domain_truck_freight(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_vehicle", "all"):
                from world_of_taxanomy.ingest.domain_truck_vehicle import ingest_domain_truck_vehicle
                print("\n-- Domain: Truck Vehicle Classes (DOT GVWR + body types, public domain) --")
                n = await ingest_domain_truck_vehicle(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_cargo", "all"):
                from world_of_taxanomy.ingest.domain_truck_cargo import ingest_domain_truck_cargo
                print("\n-- Domain: Truck Cargo Classification (NMFC + DOT hazmat, public domain) --")
                n = await ingest_domain_truck_cargo(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_fmcsa_truck", "all"):
                from world_of_taxanomy.ingest.crosswalk_fmcsa_truck import ingest_crosswalk_fmcsa_truck
                print("\n-- Crosswalk: FMCSA Regs -> Truck Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_fmcsa_truck(conn)
                print(f"  {n} edges")

            if target in ("domain_truck_ops", "all"):
                from world_of_taxanomy.ingest.domain_truck_ops import ingest_domain_truck_ops
                print("\n-- Domain: Truck Carrier Operations (FMCSA classifications, public domain) --")
                n = await ingest_domain_truck_ops(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics484_domains", "all"):
                from world_of_taxanomy.ingest.crosswalk_naics484_domains import ingest_crosswalk_naics484_domains
                print("\n-- Crosswalk: NAICS 484 -> Truck Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics484_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_ag_crop", "all"):
                from world_of_taxanomy.ingest.domain_ag_crop import ingest_domain_ag_crop
                print("\n-- Domain: Agricultural Crop Types (FAO/USDA, hand-coded, open) --")
                n = await ingest_domain_ag_crop(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_livestock", "all"):
                from world_of_taxanomy.ingest.domain_ag_livestock import ingest_domain_ag_livestock
                print("\n-- Domain: Agricultural Livestock Categories (USDA NASS, hand-coded, open) --")
                n = await ingest_domain_ag_livestock(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_method", "all"):
                from world_of_taxanomy.ingest.domain_ag_method import ingest_domain_ag_method
                print("\n-- Domain: Agricultural Farming Methods (USDA NASS/NOP, hand-coded, open) --")
                n = await ingest_domain_ag_method(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_grade", "all"):
                from world_of_taxanomy.ingest.domain_ag_grade import ingest_domain_ag_grade
                print("\n-- Domain: Agricultural Commodity Grades (USDA AMS, hand-coded, open) --")
                n = await ingest_domain_ag_grade(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics11_domains", "all"):
                from world_of_taxanomy.ingest.crosswalk_naics11_domains import ingest_crosswalk_naics11_domains
                print("\n-- Crosswalk: NAICS 11 -> Agriculture Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics11_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_mining_mineral", "all"):
                from world_of_taxanomy.ingest.domain_mining_mineral import ingest_domain_mining_mineral
                print("\n-- Domain: Mining Mineral Types (USGS/SPE, hand-coded, open) --")
                n = await ingest_domain_mining_mineral(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_method", "all"):
                from world_of_taxanomy.ingest.domain_mining_method import ingest_domain_mining_method
                print("\n-- Domain: Mining Extraction Methods (SME, hand-coded, open) --")
                n = await ingest_domain_mining_method(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_reserve", "all"):
                from world_of_taxanomy.ingest.domain_mining_reserve import ingest_domain_mining_reserve
                print("\n-- Domain: Mining Reserve Classification (SPE-PRMS, hand-coded, open) --")
                n = await ingest_domain_mining_reserve(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics21_domains", "all"):
                from world_of_taxanomy.ingest.crosswalk_naics21_domains import ingest_crosswalk_naics21_domains
                print("\n-- Crosswalk: NAICS 21 -> Mining Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics21_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_util_energy", "all"):
                from world_of_taxanomy.ingest.domain_util_energy import ingest_domain_util_energy
                print("\n-- Domain: Utility Energy Sources (IEA/EIA, hand-coded, open) --")
                n = await ingest_domain_util_energy(conn)
                print(f"  {n} nodes")

            if target in ("domain_util_grid", "all"):
                from world_of_taxanomy.ingest.domain_util_grid import ingest_domain_util_grid
                print("\n-- Domain: Utility Grid Regions (NERC, hand-coded, open) --")
                n = await ingest_domain_util_grid(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics22_domains", "all"):
                from world_of_taxanomy.ingest.crosswalk_naics22_domains import ingest_crosswalk_naics22_domains
                print("\n-- Crosswalk: NAICS 22 -> Utility Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics22_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_const_trade", "all"):
                from world_of_taxanomy.ingest.domain_const_trade import ingest_domain_const_trade
                print("\n-- Domain: Construction Trade Types (CSI MasterFormat, hand-coded, open) --")
                n = await ingest_domain_const_trade(conn)
                print(f"  {n} nodes")

            if target in ("domain_const_building", "all"):
                from world_of_taxanomy.ingest.domain_const_building import ingest_domain_const_building
                print("\n-- Domain: Construction Building Types (IBC, hand-coded, open) --")
                n = await ingest_domain_const_building(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics23_domains", "all"):
                from world_of_taxanomy.ingest.crosswalk_naics23_domains import ingest_crosswalk_naics23_domains
                print("\n-- Crosswalk: NAICS 23 -> Construction Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics23_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_mfg_process", "all"):
                from world_of_taxanomy.ingest.domain_mfg_process import ingest_domain_mfg_process
                print("\n-- Domain: Manufacturing Process Types (NIST, hand-coded, open) --")
                n = await ingest_domain_mfg_process(conn)
                print(f"  {n} nodes")

            if target in ("domain_retail_channel", "all"):
                from world_of_taxanomy.ingest.domain_retail_channel import ingest_domain_retail_channel
                print("\n-- Domain: Retail Channel Types (NRF, hand-coded, open) --")
                n = await ingest_domain_retail_channel(conn)
                print(f"  {n} nodes")

            if target in ("domain_finance_instrument", "all"):
                from world_of_taxanomy.ingest.domain_finance_instrument import ingest_domain_finance_instrument
                print("\n-- Domain: Finance Instrument Types (FIGI framework, hand-coded, open) --")
                n = await ingest_domain_finance_instrument(conn)
                print(f"  {n} nodes")

            if target in ("domain_health_setting", "all"):
                from world_of_taxanomy.ingest.domain_health_setting import ingest_domain_health_setting
                print("\n-- Domain: Health Care Settings (CMS facility types, hand-coded, open) --")
                n = await ingest_domain_health_setting(conn)
                print(f"  {n} nodes")

            if target in ("domain_transport_mode", "all"):
                from world_of_taxanomy.ingest.domain_transport_mode import ingest_domain_transport_mode
                print("\n-- Domain: Transportation Modes (DOT modal categories, hand-coded, open) --")
                n = await ingest_domain_transport_mode(conn)
                print(f"  {n} nodes")

            if target in ("domain_info_media", "all"):
                from world_of_taxanomy.ingest.domain_info_media import ingest_domain_info_media
                print("\n-- Domain: Information and Media Types (NAB/NAICS 51, hand-coded, open) --")
                n = await ingest_domain_info_media(conn)
                print(f"  {n} nodes")

            if target in ("domain_realestate_type", "all"):
                from world_of_taxanomy.ingest.domain_realestate_type import ingest_domain_realestate_type
                print("\n-- Domain: Real Estate Property Types (CoStar/NCREIF, hand-coded, open) --")
                n = await ingest_domain_realestate_type(conn)
                print(f"  {n} nodes")

            if target in ("domain_food_service", "all"):
                from world_of_taxanomy.ingest.domain_food_service import ingest_domain_food_service
                print("\n-- Domain: Food Service and Accommodation (STR/NRA, hand-coded, open) --")
                n = await ingest_domain_food_service(conn)
                print(f"  {n} nodes")

            if target in ("domain_wholesale_channel", "all"):
                from world_of_taxanomy.ingest.domain_wholesale_channel import ingest_domain_wholesale_channel
                print("\n-- Domain: Wholesale Trade Channels (CSCMP, hand-coded, open) --")
                n = await ingest_domain_wholesale_channel(conn)
                print(f"  {n} nodes")

            if target in ("domain_prof_services", "all"):
                from world_of_taxanomy.ingest.domain_prof_services import ingest_domain_prof_services
                print("\n-- Domain: Professional Services Types (AICPA/ABA, hand-coded, open) --")
                n = await ingest_domain_prof_services(conn)
                print(f"  {n} nodes")

            if target in ("domain_education_type", "all"):
                from world_of_taxanomy.ingest.domain_education_type import ingest_domain_education_type
                print("\n-- Domain: Education Program Types (NCES, hand-coded, open) --")
                n = await ingest_domain_education_type(conn)
                print(f"  {n} nodes")

            if target in ("domain_arts_content", "all"):
                from world_of_taxanomy.ingest.domain_arts_content import ingest_domain_arts_content
                print("\n-- Domain: Arts and Entertainment Content Types (ISAN, hand-coded, open) --")
                n = await ingest_domain_arts_content(conn)
                print(f"  {n} nodes")

            if target in ("domain_other_services", "all"):
                from world_of_taxanomy.ingest.domain_other_services import ingest_domain_other_services
                print("\n-- Domain: Other Services Types (SBA, hand-coded, open) --")
                n = await ingest_domain_other_services(conn)
                print(f"  {n} nodes")

            if target in ("domain_public_admin", "all"):
                from world_of_taxanomy.ingest.domain_public_admin import ingest_domain_public_admin
                print("\n-- Domain: Public Administration Types (COFOG/NAICS 92, hand-coded, open) --")
                n = await ingest_domain_public_admin(conn)
                print(f"  {n} nodes")

            if target in ("domain_supply_chain", "all"):
                from world_of_taxanomy.ingest.domain_supply_chain import ingest_domain_supply_chain
                print("\n-- Domain: Supply Chain and Trade Terms (ICC Incoterms 2020, hand-coded, open) --")
                n = await ingest_domain_supply_chain(conn)
                print(f"  {n} nodes")

            if target in ("domain_workforce_safety", "all"):
                from world_of_taxanomy.ingest.domain_workforce_safety import ingest_domain_workforce_safety
                print("\n-- Domain: Workforce Safety and Health (OSHA 29 CFR, hand-coded, open) --")
                n = await ingest_domain_workforce_safety(conn)
                print(f"  {n} nodes")

            if target in ("anzsco_2022", "all"):
                from world_of_taxanomy.ingest.anzsco_2022 import ingest_anzsco_2022
                print("\n-- ANZSCO 2022 (ABS SDMX API, CC BY 4.0) --")
                n = await ingest_anzsco_2022(conn)
                print(f"  {n} codes")

            if target in ("icd_11", "all"):
                from world_of_taxanomy.ingest.icd_11 import ingest_icd_11_from_parquet, ingest_icd_11
                import os
                parquet_path = "data/icd11_synonyms.parquet"
                csv_path = "data/icd_11.csv"
                if os.path.exists(parquet_path):
                    print("\n-- ICD-11 MMS (from parquet, WHO CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11_from_parquet(conn, path=parquet_path)
                    print(f"  {n} nodes (from parquet)")
                elif os.path.exists(csv_path):
                    print("\n-- ICD-11 MMS (from CSV, WHO CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11(conn, path=csv_path)
                    print(f"  {n} codes (from CSV)")
                else:
                    print("\n-- ICD-11: skipped (no data file; download from icd.who.int/icdapi) --")

        await close_pool()

    _run(_ingest())
    print("\nIngestion complete.")


def cmd_browse(args):
    """Browse classification hierarchy."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _browse():
        pool = await get_pool()
        async with pool.acquire() as conn:
            if args.code:
                # Show specific node and its children
                from world_of_taxanomy.query.browse import get_node, get_children, get_ancestors
                node = await get_node(conn, args.system_id, args.code)
                ancestors = await get_ancestors(conn, args.system_id, args.code)
                children = await get_children(conn, args.system_id, args.code)

                # Print breadcrumb
                if len(ancestors) > 1:
                    breadcrumb = " → ".join(f"{a.code}" for a in ancestors)
                    print(f"Path: {breadcrumb}")
                    print()

                # Print node
                leaf_marker = " 🍂" if node.is_leaf else ""
                print(f"[{node.code}] {node.title}{leaf_marker}")
                print(f"  System: {node.system_id} | Level: {node.level} | Sector: {node.sector_code}")

                if children:
                    print(f"\n  Children ({len(children)}):")
                    for child in children:
                        leaf = " 🍂" if child.is_leaf else ""
                        print(f"    [{child.code}] {child.title}{leaf}")
            else:
                # Show system roots
                from world_of_taxanomy.query.browse import get_system, get_roots
                try:
                    system = await get_system(conn, args.system_id)
                    print(f"\n{system.name} - {system.full_name}")
                    print(f"  Region: {system.region} | Version: {system.version}")
                    print(f"  Nodes: {system.node_count}")
                except Exception:
                    pass

                roots = await get_roots(conn, args.system_id)
                print(f"\nTop-level codes ({len(roots)}):")
                for root in roots:
                    print(f"  [{root.code}] {root.title}")

        await close_pool()

    _run(_browse())


def cmd_search(args):
    """Search classification codes."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _search():
        pool = await get_pool()
        async with pool.acquire() as conn:
            from world_of_taxanomy.query.search import search_nodes
            results = await search_nodes(
                conn, args.query,
                system_id=args.system,
                limit=args.limit,
            )

            if not results:
                print(f"No results for '{args.query}'")
                return

            print(f"Search results for '{args.query}' ({len(results)} found):\n")
            for node in results:
                print(f"  [{node.system_id}] {node.code} - {node.title}")

        await close_pool()

    _run(_search())


def cmd_equiv(args):
    """Show equivalences for a code."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _equiv():
        pool = await get_pool()
        async with pool.acquire() as conn:
            if args.target:
                from world_of_taxanomy.query.equivalence import translate_code
                results = await translate_code(
                    conn, args.system_id, args.code, args.target,
                )
            else:
                from world_of_taxanomy.query.equivalence import get_equivalences
                results = await get_equivalences(conn, args.system_id, args.code)

            if not results:
                print(f"No equivalences for {args.system_id}:{args.code}")
                return

            print(f"Equivalences for {args.system_id}:{args.code}:\n")
            for eq in results:
                arrow = "→"
                match_label = f"({eq.match_type})"
                target_title = f" - {eq.target_title}" if eq.target_title else ""
                print(f"  {arrow} [{eq.target_system}] {eq.target_code}{target_title} {match_label}")

        await close_pool()

    _run(_equiv())


def cmd_stats(args):
    """Show database statistics."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _stats():
        pool = await get_pool()
        async with pool.acquire() as conn:
            from world_of_taxanomy.query.browse import get_systems
            from world_of_taxanomy.query.equivalence import get_crosswalk_stats

            systems = await get_systems(conn)
            crosswalk = await get_crosswalk_stats(conn)

            print("╔═══════════════════════════════════════════════╗")
            print("║        WorldOfTaxanomy - Statistics           ║")
            print("╚═══════════════════════════════════════════════╝\n")

            print("Classification Systems:")
            for s in systems:
                print(f"  • {s.name:20s}  {s.node_count:>6,} nodes  ({s.region})")

            total_nodes = sum(s.node_count for s in systems)
            print(f"\n  Total nodes: {total_nodes:,}")

            if crosswalk:
                print("\nCrosswalk Edges:")
                total_edges = 0
                for cw in crosswalk:
                    print(f"  • {cw['source_system']:15s} → {cw['target_system']:15s}"
                          f"  {cw['edge_count']:>5,} edges"
                          f"  ({cw['exact_count']} exact, {cw['partial_count']} partial)")
                    total_edges += cw["edge_count"]
                print(f"\n  Total edges: {total_edges:,}")

        await close_pool()

    _run(_stats())


def cmd_serve(args):
    """Start the FastAPI server."""
    import uvicorn
    from world_of_taxanomy.api.app import create_app
    from world_of_taxanomy.db import get_pool, close_pool

    app = create_app()

    @app.on_event("startup")
    async def startup():
        app.state.pool = await get_pool()
        print("Database pool ready.")

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()
        print("Database pool closed.")

    print(f"\nStarting WorldOfTaxanomy API server...")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs\n")
    uvicorn.run(app, host=args.host, port=args.port)


def cmd_mcp(args):
    """Start the MCP server (stdio transport)."""
    from world_of_taxanomy.mcp.server import main as mcp_main
    mcp_main()


# ── Argument Parser ───────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world_of_taxanomy",
        description="WorldOfTaxanomy - Unified Industry Classification Knowledge Graph",
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # init
    sub.add_parser("init", help="Initialize database schema")

    # init-auth
    sub.add_parser("init-auth", help="Initialize auth database schema")

    # reset
    sub.add_parser("reset", help="Drop and recreate all tables")

    # ingest
    p_ingest = sub.add_parser("ingest", help="Ingest classification data")
    p_ingest.add_argument(
        "target",
        choices=["naics", "isic", "nic", "nace", "sic", "anzsic", "jsic", "wz", "onace", "noga", "crosswalk", "iso3166_1", "iso3166_2", "crosswalk_iso3166", "un_m49", "crosswalk_un_m49_iso3166", "hs2022", "crosswalk_hs_isic", "cpc_v21", "crosswalk_cpc_isic", "crosswalk_cpc_hs", "unspsc_v24", "soc_2018", "isco_08", "crosswalk_soc_isco", "cip_2020", "crosswalk_cip_soc", "isced_2011", "iscedf_2013", "crosswalk_cip_iscedf", "atc_who", "icd_11", "crosswalk_icd_isic", "loinc", "cofog", "gics_bridge", "ghg_protocol", "esco_occupations", "esco_skills", "crosswalk_esco_isco", "onet_soc", "crosswalk_onet_soc", "patent_cpc", "cfr_title_49", "fmcsa_regs", "crosswalk_cfr_naics", "gdpr", "iso_31000", "domain_truck_freight", "domain_truck_vehicle", "domain_truck_cargo", "crosswalk_fmcsa_truck", "domain_truck_ops", "crosswalk_naics484_domains", "domain_ag_crop", "domain_ag_livestock", "domain_ag_method", "domain_ag_grade", "crosswalk_naics11_domains", "domain_mining_mineral", "domain_mining_method", "domain_mining_reserve", "crosswalk_naics21_domains", "domain_util_energy", "domain_util_grid", "crosswalk_naics22_domains", "domain_const_trade", "domain_const_building", "crosswalk_naics23_domains", "domain_mfg_process", "domain_retail_channel", "domain_finance_instrument", "domain_health_setting", "domain_transport_mode", "domain_info_media", "domain_realestate_type", "domain_food_service", "domain_wholesale_channel", "domain_prof_services", "domain_education_type", "domain_arts_content", "domain_other_services", "domain_public_admin", "domain_supply_chain", "domain_workforce_safety", "anzsco_2022", "all"],
        help="What to ingest",
    )

    # browse
    p_browse = sub.add_parser("browse", help="Browse classification hierarchy")
    p_browse.add_argument("system_id", help="Classification system ID (e.g., naics_2022)")
    p_browse.add_argument("code", nargs="?", help="Node code to inspect")

    # search
    p_search = sub.add_parser("search", help="Search classification codes")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--system", help="Filter by system ID")
    p_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # equiv
    p_equiv = sub.add_parser("equiv", help="Show equivalences for a code")
    p_equiv.add_argument("system_id", help="Source system ID")
    p_equiv.add_argument("code", help="Source code")
    p_equiv.add_argument("--target", help="Target system ID (optional filter)")

    # stats
    sub.add_parser("stats", help="Show database statistics")

    # serve
    p_serve = sub.add_parser("serve", help="Start the API server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    # mcp
    sub.add_parser("mcp", help="Start the MCP server (stdio transport)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "init-auth": cmd_init_auth,
        "reset": cmd_reset,
        "ingest": cmd_ingest,
        "browse": cmd_browse,
        "search": cmd_search,
        "equiv": cmd_equiv,
        "stats": cmd_stats,
        "serve": cmd_serve,
        "mcp": cmd_mcp,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
