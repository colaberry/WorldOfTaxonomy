"""CLI entry point for WorldOfTaxonomy.

Usage:
    python -m world_of_taxonomy init
    python -m world_of_taxonomy ingest {naics,isic,nic,nace,sic,anzsic,jsic,wz,onace,noga,crosswalk,all}
    python -m world_of_taxonomy browse <system_id> [code]
    python -m world_of_taxonomy search <query> [--system SYSTEM] [--limit N]
    python -m world_of_taxonomy equiv <system_id> <code> [--target TARGET]
    python -m world_of_taxonomy stats
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
    from world_of_taxonomy.db import init_db
    print("Initializing database schema...")
    _run(init_db())
    print("Done. Tables created.")


def cmd_init_auth(args):
    """Initialize the auth database schema."""
    from world_of_taxonomy.db import init_auth_db
    print("Initializing auth database schema...")
    _run(init_auth_db())
    print("Done. Auth tables created.")


def cmd_reset(args):
    """Drop and recreate all tables."""
    from world_of_taxonomy.db import reset_db
    print("Resetting database (dropping all tables)...")
    _run(reset_db())
    print("Done. Fresh schema ready.")


def cmd_ingest(args):
    """Ingest classification data."""
    from world_of_taxonomy.db import get_pool, close_pool

    async def _ingest():
        pool = await get_pool()
        async with pool.acquire() as conn:
            target = args.target

            if target in ("naics", "all"):
                from world_of_taxonomy.ingest.naics import ingest_naics_2022
                print("\n── NAICS 2022 ──")
                await ingest_naics_2022(conn)

            if target in ("isic", "all"):
                from world_of_taxonomy.ingest.isic import ingest_isic_rev4
                print("\n── ISIC Rev 4 ──")
                await ingest_isic_rev4(conn)

            if target in ("nic", "all"):
                from world_of_taxonomy.ingest.nic import ingest_nic_2008
                print("\n── NIC 2008 ──")
                await ingest_nic_2008(conn)

            if target in ("nace", "all"):
                from world_of_taxonomy.ingest.nace import ingest_nace_rev2, ingest_nace_isic_crosswalk
                print("\n── NACE Rev 2 ──")
                await ingest_nace_rev2(conn)
                print("\n── Crosswalk (NACE ↔ ISIC) ──")
                await ingest_nace_isic_crosswalk(conn)

            if target in ("sic", "all"):
                from world_of_taxonomy.ingest.sic import ingest_sic_1987
                print("\n── SIC 1987 ──")
                await ingest_sic_1987(conn)

            if target in ("anzsic", "all"):
                from world_of_taxonomy.ingest.anzsic import ingest_anzsic_2006
                print("\n── ANZSIC 2006 ──")
                await ingest_anzsic_2006(conn)

            if target in ("jsic", "all"):
                from world_of_taxonomy.ingest.jsic import ingest_jsic_2013
                print("\n── JSIC 2013 ──")
                await ingest_jsic_2013(conn)

            if target in ("wz", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_wz_2008
                print("\n── WZ 2008 (derived from NACE) ──")
                await ingest_wz_2008(conn)

            if target in ("onace", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_onace_2008
                print("\n── ÖNACE 2008 (derived from NACE) ──")
                await ingest_onace_2008(conn)

            if target in ("noga", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_noga_2008
                print("\n── NOGA 2008 (derived from NACE) ──")
                await ingest_noga_2008(conn)

            if target in ("crosswalk", "all"):
                from world_of_taxonomy.ingest.crosswalk import ingest_crosswalk
                print("\n-- Crosswalk (NAICS / ISIC) --")
                await ingest_crosswalk(conn)

            if target in ("iso3166_1", "all"):
                from world_of_taxonomy.ingest.iso3166_1 import ingest_iso3166_1
                print("\n-- ISO 3166-1 Countries --")
                n = await ingest_iso3166_1(conn)
                print(f"  {n} nodes")

            if target in ("iso3166_2", "all"):
                from world_of_taxonomy.ingest.iso3166_2 import ingest_iso3166_2
                print("\n-- ISO 3166-2 Subdivisions --")
                n = await ingest_iso3166_2(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_iso3166", "all"):
                from world_of_taxonomy.ingest.crosswalk_iso3166 import ingest_crosswalk_iso3166
                print("\n-- Crosswalk (ISO 3166-1 / ISO 3166-2) --")
                n = await ingest_crosswalk_iso3166(conn)
                print(f"  {n} edges")

            if target in ("un_m49", "all"):
                from world_of_taxonomy.ingest.un_m49 import ingest_un_m49
                print("\n-- UN M.49 Geographic Regions --")
                n = await ingest_un_m49(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_un_m49_iso3166", "all"):
                from world_of_taxonomy.ingest.crosswalk_un_m49_iso3166 import ingest_crosswalk_un_m49_iso3166
                print("\n-- Crosswalk (UN M.49 / ISO 3166-1) --")
                n = await ingest_crosswalk_un_m49_iso3166(conn)
                print(f"  {n} edges")

            if target in ("hs2022", "all"):
                from world_of_taxonomy.ingest.hs2022 import ingest_hs2022
                print("\n-- HS 2022 Harmonized System --")
                n = await ingest_hs2022(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_hs_isic", "all"):
                from world_of_taxonomy.ingest.crosswalk_hs_isic import ingest_crosswalk_hs_isic
                print("\n-- Crosswalk (HS 2022 / ISIC Rev 4) --")
                n = await ingest_crosswalk_hs_isic(conn)
                print(f"  {n} edges")

            if target in ("cpc_v21", "all"):
                from world_of_taxonomy.ingest.cpc_v21 import ingest_cpc_v21
                print("\n-- CPC v2.1 Central Product Classification --")
                n = await ingest_cpc_v21(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cpc_isic", "all"):
                from world_of_taxonomy.ingest.crosswalk_cpc import ingest_crosswalk_cpc_isic
                print("\n-- Crosswalk (CPC v2.1 / ISIC Rev 4) --")
                n = await ingest_crosswalk_cpc_isic(conn)
                print(f"  {n} edges")

            if target in ("crosswalk_cpc_hs", "all"):
                from world_of_taxonomy.ingest.crosswalk_cpc import ingest_crosswalk_cpc_hs
                print("\n-- Crosswalk (HS 2022 / CPC v2.1) --")
                n = await ingest_crosswalk_cpc_hs(conn)
                print(f"  {n} edges")

            if target in ("unspsc_v24", "all"):
                from world_of_taxonomy.ingest.unspsc import ingest_unspsc
                print("\n-- UNSPSC v24 --")
                n = await ingest_unspsc(conn)
                print(f"  {n} nodes")

            if target in ("soc_2018", "all"):
                from world_of_taxonomy.ingest.soc_2018 import ingest_soc_2018
                print("\n-- SOC 2018 --")
                n = await ingest_soc_2018(conn)
                print(f"  {n} nodes")

            if target in ("isco_08", "all"):
                from world_of_taxonomy.ingest.isco_08 import ingest_isco_08
                print("\n-- ISCO-08 --")
                n = await ingest_isco_08(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_soc_naics", "all"):
                from world_of_taxonomy.ingest.crosswalk_soc_naics import ingest_crosswalk_soc_naics
                print("\n-- Crosswalk (SOC 2018 / NAICS 2022) --")
                n = await ingest_crosswalk_soc_naics(conn)
                print(f"  {n} edges")

            if target in ("crosswalk_soc_isco", "all"):
                from world_of_taxonomy.ingest.crosswalk_soc_isco import ingest_crosswalk_soc_isco
                print("\n-- Crosswalk (SOC 2018 / ISCO-08) --")
                n = await ingest_crosswalk_soc_isco(conn)
                print(f"  {n} edges")

            if target in ("crosswalk_isco_isic", "all"):
                from world_of_taxonomy.ingest.crosswalk_isco_isic import ingest_crosswalk_isco_isic
                print("\n-- Crosswalk (ISCO-08 / ISIC Rev 4) --")
                n = await ingest_crosswalk_isco_isic(conn)
                print(f"  {n} edges")

            if target in ("cip_2020", "all"):
                from world_of_taxonomy.ingest.cip_2020 import ingest_cip_2020
                print("\n-- CIP 2020 --")
                n = await ingest_cip_2020(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cip_soc", "all"):
                from world_of_taxonomy.ingest.crosswalk_cip_soc import ingest_crosswalk_cip_soc
                print("\n-- Crosswalk (CIP 2020 / SOC 2018) --")
                n = await ingest_crosswalk_cip_soc(conn)
                print(f"  {n} edges")

            if target in ("isced_2011", "all"):
                from world_of_taxonomy.ingest.isced_2011 import ingest_isced_2011
                print("\n-- ISCED 2011 (Education Levels) --")
                n = await ingest_isced_2011(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_isced_isco", "all"):
                from world_of_taxonomy.ingest.crosswalk_isced_isco import ingest_crosswalk_isced_isco
                print("\n-- Crosswalk (ISCED 2011 / ISCO-08) --")
                n = await ingest_crosswalk_isced_isco(conn)
                print(f"  {n} edges")

            if target in ("iscedf_2013", "all"):
                from world_of_taxonomy.ingest.iscedf_2013 import ingest_iscedf_2013
                print("\n-- ISCED-F 2013 (Fields of Education) --")
                n = await ingest_iscedf_2013(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cip_iscedf", "all"):
                from world_of_taxonomy.ingest.crosswalk_cip_iscedf import ingest_crosswalk_cip_iscedf
                print("\n-- Crosswalk (CIP 2020 / ISCED-F 2013) --")
                n = await ingest_crosswalk_cip_iscedf(conn)
                print(f"  {n} edges")

            if target in ("atc_who", "all"):
                from world_of_taxonomy.ingest.atc_who import ingest_atc_who
                print("\n-- ATC WHO 2021 (Drug Classification) --")
                n = await ingest_atc_who(conn)
                print(f"  {n} nodes")


            if target in ("ateco_2007", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_ateco_2007
                print("\n-- Italian ATECO 2007 (NACE Rev 2 derived) --")
                n = await ingest_ateco_2007(conn)
                print(f"  {n} nodes")

            if target in ("naf_rev2", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_naf_rev2
                print("\n-- French NAF Rev 2 (NACE Rev 2 derived) --")
                n = await ingest_naf_rev2(conn)
                print(f"  {n} nodes")

            if target in ("pkd_2007", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_pkd_2007
                print("\n-- Polish PKD 2007 (NACE Rev 2 derived) --")
                n = await ingest_pkd_2007(conn)
                print(f"  {n} nodes")

            if target in ("sbi_2008", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_sbi_2008
                print("\n-- Dutch SBI 2008 (NACE Rev 2 derived) --")
                n = await ingest_sbi_2008(conn)
                print(f"  {n} nodes")

            if target in ("sni_2007", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_sni_2007
                print("\n-- Swedish SNI 2007 (NACE Rev 2 derived) --")
                n = await ingest_sni_2007(conn)
                print(f"  {n} nodes")

            if target in ("db07", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_db07
                print("\n-- Danish DB07 (NACE Rev 2 derived) --")
                n = await ingest_db07(conn)
                print(f"  {n} nodes")

            if target in ("tol_2008", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_tol_2008
                print("\n-- Finnish TOL 2008 (NACE Rev 2 derived) --")
                n = await ingest_tol_2008(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_co", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_co
                print("\n-- Colombian CIIU Rev 4 AC (ISIC Rev 4 derived) --")
                n = await ingest_ciiu_co(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_ar", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_ar
                print("\n-- Argentine CLANAE Rev 4 (ISIC Rev 4 derived) --")
                n = await ingest_ciiu_ar(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_cl", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_cl
                print("\n-- Chilean CIIU Rev 4 (ISIC Rev 4 derived) --")
                n = await ingest_ciiu_cl(conn)
                print(f"  {n} nodes")

            if target in ("arxiv_taxonomy", "all"):
                from world_of_taxonomy.ingest.arxiv_taxonomy import ingest_arxiv_taxonomy
                print("\n-- arXiv Subject Classification Taxonomy --")
                n = await ingest_arxiv_taxonomy(conn)
                print(f"  {n} nodes")

            if target in ("sdg", "all"):
                from world_of_taxonomy.ingest.sdg import ingest_sdg
                print("\n-- UN Sustainable Development Goals 2030 --")
                n = await ingest_sdg(conn)
                print(f"  {n} nodes")

            if target in ("oecd_dac", "all"):
                from world_of_taxonomy.ingest.oecd_dac import ingest_oecd_dac
                print("\n-- OECD DAC Sector Purpose Codes --")
                n = await ingest_oecd_dac(conn)
                print(f"  {n} nodes")

            if target in ("gri_standards", "all"):
                from world_of_taxonomy.ingest.gri_standards import ingest_gri_standards
                print("\n-- Global Reporting Initiative Standards --")
                n = await ingest_gri_standards(conn)
                print(f"  {n} nodes")

            if target in ("icb", "all"):
                from world_of_taxonomy.ingest.icb import ingest_icb
                print("\n-- Industry Classification Benchmark (FTSE Russell) --")
                n = await ingest_icb(conn)
                print(f"  {n} nodes")

            if target in ("basel_exposure", "all"):
                from world_of_taxonomy.ingest.basel_exposure import ingest_basel_exposure
                print("\n-- Basel III/IV Exposure Category Classification --")
                n = await ingest_basel_exposure(conn)
                print(f"  {n} nodes")

            if target in ("wb_income", "all"):
                from world_of_taxonomy.ingest.wb_income import ingest_wb_income
                print("\n-- World Bank Country Income Classification --")
                n = await ingest_wb_income(conn)
                print(f"  {n} nodes")

            if target in ("adb_sector", "all"):
                from world_of_taxonomy.ingest.adb_sector import ingest_adb_sector
                print("\n-- Asian Development Bank Sector Classification --")
                n = await ingest_adb_sector(conn)
                print(f"  {n} nodes")

            if target in ("tnfd", "all"):
                from world_of_taxonomy.ingest.tnfd import ingest_tnfd
                print("\n-- TNFD Nature-related Financial Disclosures --")
                n = await ingest_tnfd(conn)
                print(f"  {n} nodes")

            if target in ("sfdr", "all"):
                from world_of_taxonomy.ingest.sfdr import ingest_sfdr
                print("\n-- EU SFDR Sustainable Finance Disclosure Regulation --")
                n = await ingest_sfdr(conn)
                print(f"  {n} nodes")

            if target in ("msc_2020", "all"):
                from world_of_taxonomy.ingest.msc_2020 import ingest_msc_2020
                print("\n-- Mathematics Subject Classification 2020 --")
                n = await ingest_msc_2020(conn)
                print(f"  {n} nodes")

            if target in ("pacs", "all"):
                from world_of_taxonomy.ingest.pacs import ingest_pacs
                print("\n-- Physics and Astronomy Classification System --")
                n = await ingest_pacs(conn)
                print(f"  {n} nodes")

            if target in ("lcc", "all"):
                from world_of_taxonomy.ingest.lcc import ingest_lcc
                print("\n-- Library of Congress Classification skeleton --")
                n = await ingest_lcc(conn)
                print(f"  {n} nodes")

            if target in ("eccn", "all"):
                from world_of_taxonomy.ingest.eccn import ingest_eccn
                print("\n-- Export Control Classification Number (ECCN/CCL) --")
                n = await ingest_eccn(conn)
                print(f"  {n} nodes")

            if target in ("schedule_b", "all"):
                from world_of_taxonomy.ingest.schedule_b import ingest_schedule_b
                print("\n-- US Schedule B Export Classification --")
                n = await ingest_schedule_b(conn)
                print(f"  {n} nodes")

            if target in ("icd10_pcs", "all"):
                from world_of_taxonomy.ingest.icd10_pcs import ingest_icd10_pcs
                print("\n-- ICD-10-PCS Procedure Coding System skeleton --")
                n = await ingest_icd10_pcs(conn)
                print(f"  {n} nodes")

            if target in ("icdo3", "all"):
                from world_of_taxonomy.ingest.icdo3 import ingest_icdo3
                print("\n-- ICD-O-3 Classification of Diseases for Oncology --")
                n = await ingest_icdo3(conn)
                print(f"  {n} nodes")

            if target in ("icf", "all"):
                from world_of_taxonomy.ingest.icf import ingest_icf
                print("\n-- ICF International Classification of Functioning --")
                n = await ingest_icf(conn)
                print(f"  {n} nodes")


            if target in ("cae_rev3", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_cae_rev3
                print("\n-- CAE Rev 3 (Portugal) - NACE Rev 2 derived --")
                n = await ingest_cae_rev3(conn)
                print(f"  {n} nodes")

            if target in ("cz_nace", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_cz_nace
                print("\n-- CZ-NACE (Czech Republic) - NACE Rev 2 derived --")
                n = await ingest_cz_nace(conn)
                print(f"  {n} nodes")

            if target in ("teaor_2008", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_teaor_2008
                print("\n-- TEAOR 2008 (Hungary) - NACE Rev 2 derived --")
                n = await ingest_teaor_2008(conn)
                print(f"  {n} nodes")

            if target in ("caen_rev2", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_caen_rev2
                print("\n-- CAEN Rev 2 (Romania) - NACE Rev 2 derived --")
                n = await ingest_caen_rev2(conn)
                print(f"  {n} nodes")

            if target in ("nkd_2007", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nkd_2007
                print("\n-- NKD 2007 (Croatia) - NACE Rev 2 derived --")
                n = await ingest_nkd_2007(conn)
                print(f"  {n} nodes")

            if target in ("sk_nace", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_sk_nace
                print("\n-- SK NACE Rev 2 (Slovakia) - NACE Rev 2 derived --")
                n = await ingest_sk_nace(conn)
                print(f"  {n} nodes")

            if target in ("nkid", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nkid
                print("\n-- NKID (Bulgaria) - NACE Rev 2 derived --")
                n = await ingest_nkid(conn)
                print(f"  {n} nodes")

            if target in ("emtak", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_emtak
                print("\n-- EMTAK (Estonia) - NACE Rev 2 derived --")
                n = await ingest_emtak(conn)
                print(f"  {n} nodes")

            if target in ("nace_lt", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_lt
                print("\n-- EVRK (Lithuania) - NACE Rev 2 derived --")
                n = await ingest_nace_lt(conn)
                print(f"  {n} nodes")

            if target in ("nk_lv", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nk_lv
                print("\n-- NK (Latvia) - NACE Rev 2 derived --")
                n = await ingest_nk_lv(conn)
                print(f"  {n} nodes")

            if target in ("nace_tr", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_tr
                print("\n-- NACE (Turkey) - NACE Rev 2 derived --")
                n = await ingest_nace_tr(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_pe", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_pe
                print("\n-- CIIU Rev 4 (Peru) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_pe(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_ec", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_ec
                print("\n-- CIIU Rev 4 (Ecuador) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_ec(conn)
                print(f"  {n} nodes")

            if target in ("caeb", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_caeb
                print("\n-- CAEB (Bolivia) - ISIC Rev 4 derived --")
                n = await ingest_caeb(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_ve", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_ve
                print("\n-- CIIU Rev 4 (Venezuela) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_ve(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_cr", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_cr
                print("\n-- CIIU Rev 4 (Costa Rica) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_cr(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_gt", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_gt
                print("\n-- CIIU Rev 4 (Guatemala) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_gt(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_pa", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_pa
                print("\n-- CIIU Rev 4 (Panama) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_pa(conn)
                print(f"  {n} nodes")

            if target in ("vsic_2018", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_vsic_2018
                print("\n-- VSIC 2018 (Vietnam) - ISIC Rev 4 derived --")
                n = await ingest_vsic_2018(conn)
                print(f"  {n} nodes")

            if target in ("bsic", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_bsic
                print("\n-- BSIC (Bangladesh) - ISIC Rev 4 derived --")
                n = await ingest_bsic(conn)
                print(f"  {n} nodes")

            if target in ("psic_pk", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_psic_pk
                print("\n-- PSIC (Pakistan) - ISIC Rev 4 derived --")
                n = await ingest_psic_pk(conn)
                print(f"  {n} nodes")

            if target in ("isic_ng", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ng
                print("\n-- ISIC Rev 4 (Nigeria) - ISIC Rev 4 derived --")
                n = await ingest_isic_ng(conn)
                print(f"  {n} nodes")

            if target in ("isic_ke", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ke
                print("\n-- ISIC Rev 4 (Kenya) - ISIC Rev 4 derived --")
                n = await ingest_isic_ke(conn)
                print(f"  {n} nodes")

            if target in ("isic_eg", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_eg
                print("\n-- ISIC Rev 4 (Egypt) - ISIC Rev 4 derived --")
                n = await ingest_isic_eg(conn)
                print(f"  {n} nodes")

            if target in ("isic_sa", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sa
                print("\n-- ISIC Rev 4 (Saudi Arabia) - ISIC Rev 4 derived --")
                n = await ingest_isic_sa(conn)
                print(f"  {n} nodes")

            if target in ("isic_ae", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ae
                print("\n-- ISIC Rev 4 (UAE) - ISIC Rev 4 derived --")
                n = await ingest_isic_ae(conn)
                print(f"  {n} nodes")

            if target in ("coicop", "all"):
                from world_of_taxonomy.ingest.coicop import ingest_coicop
                print("\n-- COICOP 2018 (Classification of Individual Consumption by Purpose) --")
                n = await ingest_coicop(conn)
                print(f"  {n} nodes")

            if target in ("cfi_iso10962", "all"):
                from world_of_taxonomy.ingest.cfi_iso10962 import ingest_cfi_iso10962
                print("\n-- CFI ISO 10962 (Classification of Financial Instruments) --")
                n = await ingest_cfi_iso10962(conn)
                print(f"  {n} nodes")

            if target in ("ford_frascati", "all"):
                from world_of_taxonomy.ingest.ford_frascati import ingest_ford_frascati
                print("\n-- FORD Frascati 2015 (OECD Fields of Research and Development) --")
                n = await ingest_ford_frascati(conn)
                print(f"  {n} nodes")

            if target in ("cn_2024", "all"):
                from world_of_taxonomy.ingest.cn_2024 import ingest_cn_2024
                print("\n-- CN 2024 (EU Combined Nomenclature 2024) --")
                n = await ingest_cn_2024(conn)
                print(f"  {n} nodes")

            if target in ("anzsrc_for_2020", "all"):
                from world_of_taxonomy.ingest.anzsrc_for_2020 import ingest_anzsrc_for_2020
                print("\n-- ANZSRC FOR 2020 (Fields of Research - Australia/NZ) --")
                n = await ingest_anzsrc_for_2020(conn)
                print(f"  {n} nodes")

            if target in ("icd10_gm", "all"):
                from world_of_taxonomy.ingest.icd10_gm import ingest_icd10_gm
                print("\n-- ICD-10-GM (German Modification) --")
                n = await ingest_icd10_gm(conn)
                print(f"  {n} nodes")

            if target in ("icd10_am", "all"):
                from world_of_taxonomy.ingest.icd10_am import ingest_icd10_am
                print("\n-- ICD-10-AM (Australian Modification) --")
                n = await ingest_icd10_am(conn)
                print(f"  {n} nodes")

            if target in ("seea", "all"):
                from world_of_taxonomy.ingest.seea import ingest_seea
                print("\n-- SEEA (UN System of Environmental-Economic Accounting) --")
                n = await ingest_seea(conn)
                print(f"  {n} nodes")

            if target in ("icd_11", "all"):
                from world_of_taxonomy.ingest.icd_11 import (
                    ingest_icd_11_from_zip,
                    ingest_icd_11_from_parquet,
                    ingest_icd_11,
                )
                import os as _os
                _zip = "data/SimpleTabulation-ICD-11-MMS-en.zip"
                _parquet = "data/icd11_synonyms.parquet"
                _csv = "data/icd_11.csv"
                if _os.path.exists(_zip):
                    print("\n-- ICD-11 MMS (from WHO SimpleTabulation zip, ~37K nodes, CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11_from_zip(conn, path=_zip)
                    print(f"  {n} nodes (chapters + blocks + categories)")
                elif _os.path.exists(_parquet):
                    print("\n-- ICD-11 MMS (from parquet, WHO CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11_from_parquet(conn, path=_parquet)
                    print(f"  {n} nodes (from parquet)")
                elif _os.path.exists(_csv):
                    print("\n-- ICD-11 MMS (from CSV, WHO CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11(conn, path=_csv)
                    print(f"  {n} codes (from CSV)")
                else:
                    print("\n-- ICD-11: skipped (no data file found) --")

            if target in ("crosswalk_icd_isic", "all"):
                from world_of_taxonomy.ingest.crosswalk_icd_isic import ingest_crosswalk_icd_isic
                print("\n-- Crosswalk (ICD-11 / ISIC Rev 4) --")
                n = await ingest_crosswalk_icd_isic(conn)
                print(f"  {n} edges")

            if target in ("loinc", "all"):
                from world_of_taxonomy.ingest.loinc import ingest_loinc
                print("\n-- LOINC (requires manual download from loinc.org) --")
                n = await ingest_loinc(conn)
                print(f"  {n} nodes")

            if target in ("cofog", "all"):
                from world_of_taxonomy.ingest.cofog import ingest_cofog
                print("\n-- COFOG (Classification of the Functions of Government) --")
                n = await ingest_cofog(conn)
                print(f"  {n} nodes")

            if target in ("gics_bridge", "all"):
                from world_of_taxonomy.ingest.gics_bridge import ingest_gics_bridge
                print("\n-- GICS Bridge (11 public sector names only, MSCI/S&P proprietary) --")
                n = await ingest_gics_bridge(conn)
                print(f"  {n} nodes")

            if target in ("ghg_protocol", "all"):
                from world_of_taxonomy.ingest.ghg_protocol import ingest_ghg_protocol
                print("\n-- GHG Protocol (Scope 1/2/3 framework, WRI/WBCSD) --")
                n = await ingest_ghg_protocol(conn)
                print(f"  {n} nodes")

            if target in ("esco_occupations", "all"):
                from world_of_taxonomy.ingest.esco_occupations import ingest_esco_occupations
                print("\n-- ESCO Occupations (EU Commission, CC BY 4.0) --")
                n = await ingest_esco_occupations(conn)
                print(f"  {n} nodes")

            if target in ("esco_skills", "all"):
                from world_of_taxonomy.ingest.esco_skills import ingest_esco_skills
                print("\n-- ESCO Skills (EU Commission, CC BY 4.0) --")
                n = await ingest_esco_skills(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_esco_isco", "all"):
                from world_of_taxonomy.ingest.crosswalk_esco_isco import ingest_crosswalk_esco_isco
                print("\n-- Crosswalk (ESCO Occupations / ISCO-08) --")
                n = await ingest_crosswalk_esco_isco(conn)
                print(f"  {n} edges")

            if target in ("onet_soc", "all"):
                from world_of_taxonomy.ingest.onet_soc import ingest_onet_soc
                print("\n-- O*NET-SOC (US DOL, CC BY 4.0) --")
                n = await ingest_onet_soc(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_onet_soc", "all"):
                from world_of_taxonomy.ingest.crosswalk_onet_soc import ingest_crosswalk_onet_soc
                print("\n-- Crosswalk (O*NET-SOC / SOC 2018) --")
                n = await ingest_crosswalk_onet_soc(conn)
                print(f"  {n} edges")

            if target in ("patent_cpc", "all"):
                from world_of_taxonomy.ingest.patent_cpc import ingest_patent_cpc
                print("\n-- Patent CPC (~260K codes, EPO/USPTO, open) --")
                n = await ingest_patent_cpc(conn)
                print(f"  {n} nodes")

            if target in ("cfr_title_49", "all"):
                from world_of_taxonomy.ingest.cfr_title49 import ingest_cfr_title49
                print("\n-- CFR Title 49 - Transportation (hand-coded, public domain) --")
                n = await ingest_cfr_title49(conn)
                print(f"  {n} nodes")

            if target in ("fmcsa_regs", "all"):
                from world_of_taxonomy.ingest.fmcsa_regs import ingest_fmcsa_regs
                print("\n-- FMCSA Regulatory Codes (hand-coded, public domain) --")
                n = await ingest_fmcsa_regs(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_cfr_naics", "all"):
                from world_of_taxonomy.ingest.crosswalk_cfr_naics import ingest_crosswalk_cfr_naics
                print("\n-- Crosswalk (CFR Title 49 + FMCSA / NAICS) --")
                n = await ingest_crosswalk_cfr_naics(conn)
                print(f"  {n} edges")

            if target in ("gdpr", "all"):
                from world_of_taxonomy.ingest.gdpr import ingest_gdpr
                print("\n-- GDPR Articles (EU 2016/679, hand-coded, open) --")
                n = await ingest_gdpr(conn)
                print(f"  {n} nodes")

            if target in ("iso_31000", "all"):
                from world_of_taxonomy.ingest.iso31000 import ingest_iso31000
                print("\n-- ISO 31000 Risk Framework (hand-coded, open) --")
                n = await ingest_iso31000(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_freight", "all"):
                from world_of_taxonomy.ingest.domain_truck_freight import ingest_domain_truck_freight
                print("\n-- Domain: Truck Freight Types (hand-coded, open) --")
                n = await ingest_domain_truck_freight(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_vehicle", "all"):
                from world_of_taxonomy.ingest.domain_truck_vehicle import ingest_domain_truck_vehicle
                print("\n-- Domain: Truck Vehicle Classes (DOT GVWR + body types, public domain) --")
                n = await ingest_domain_truck_vehicle(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_cargo", "all"):
                from world_of_taxonomy.ingest.domain_truck_cargo import ingest_domain_truck_cargo
                print("\n-- Domain: Truck Cargo Classification (NMFC + DOT hazmat, public domain) --")
                n = await ingest_domain_truck_cargo(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_fmcsa_truck", "all"):
                from world_of_taxonomy.ingest.crosswalk_fmcsa_truck import ingest_crosswalk_fmcsa_truck
                print("\n-- Crosswalk: FMCSA Regs -> Truck Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_fmcsa_truck(conn)
                print(f"  {n} edges")

            if target in ("domain_truck_ops", "all"):
                from world_of_taxonomy.ingest.domain_truck_ops import ingest_domain_truck_ops
                print("\n-- Domain: Truck Carrier Operations (FMCSA classifications, public domain) --")
                n = await ingest_domain_truck_ops(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics484_domains", "all"):
                from world_of_taxonomy.ingest.crosswalk_naics484_domains import ingest_crosswalk_naics484_domains
                print("\n-- Crosswalk: NAICS 484 -> Truck Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics484_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_truck_pricing", "all"):
                from world_of_taxonomy.ingest.domain_truck_pricing import ingest_domain_truck_pricing
                print("\n-- Domain: Truck Pricing / Rate Structure (NMFC/DAT, hand-coded, open) --")
                n = await ingest_domain_truck_pricing(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_truck_regulatory import ingest_domain_truck_regulatory
                print("\n-- Domain: Truck Regulatory / Compliance Domains (49 CFR/FMCSA, hand-coded, open) --")
                n = await ingest_domain_truck_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_tech", "all"):
                from world_of_taxonomy.ingest.domain_truck_tech import ingest_domain_truck_tech
                print("\n-- Domain: Truck Technology / Digitization Level (ATA/SAE, hand-coded, open) --")
                n = await ingest_domain_truck_tech(conn)
                print(f"  {n} nodes")

            if target in ("domain_truck_lane", "all"):
                from world_of_taxonomy.ingest.domain_truck_lane import ingest_domain_truck_lane
                print("\n-- Domain: Truck Geographic Lane Classification (DAT/FMCSA FAF, hand-coded, open) --")
                n = await ingest_domain_truck_lane(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_crop", "all"):
                from world_of_taxonomy.ingest.domain_ag_crop import ingest_domain_ag_crop
                print("\n-- Domain: Agricultural Crop Types (FAO/USDA, hand-coded, open) --")
                n = await ingest_domain_ag_crop(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_livestock", "all"):
                from world_of_taxonomy.ingest.domain_ag_livestock import ingest_domain_ag_livestock
                print("\n-- Domain: Agricultural Livestock Categories (USDA NASS, hand-coded, open) --")
                n = await ingest_domain_ag_livestock(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_method", "all"):
                from world_of_taxonomy.ingest.domain_ag_method import ingest_domain_ag_method
                print("\n-- Domain: Agricultural Farming Methods (USDA NASS/NOP, hand-coded, open) --")
                n = await ingest_domain_ag_method(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_grade", "all"):
                from world_of_taxonomy.ingest.domain_ag_grade import ingest_domain_ag_grade
                print("\n-- Domain: Agricultural Commodity Grades (USDA AMS, hand-coded, open) --")
                n = await ingest_domain_ag_grade(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_equipment", "all"):
                from world_of_taxonomy.ingest.domain_ag_equipment import ingest_domain_ag_equipment
                print("\n-- Domain: Agricultural Equipment Types (hand-coded, open) --")
                n = await ingest_domain_ag_equipment(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_input", "all"):
                from world_of_taxonomy.ingest.domain_ag_input import ingest_domain_ag_input
                print("\n-- Domain: Agricultural Input Supply Types (hand-coded, open) --")
                n = await ingest_domain_ag_input(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_business", "all"):
                from world_of_taxonomy.ingest.domain_ag_business import ingest_domain_ag_business
                print("\n-- Domain: Agricultural Farm Business Structure Types (hand-coded, open) --")
                n = await ingest_domain_ag_business(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_market", "all"):
                from world_of_taxonomy.ingest.domain_ag_market import ingest_domain_ag_market
                print("\n-- Domain: Agricultural Market Channel Types (hand-coded, open) --")
                n = await ingest_domain_ag_market(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_ag_regulatory import ingest_domain_ag_regulatory
                print("\n-- Domain: Agricultural Regulatory Compliance Types (hand-coded, open) --")
                n = await ingest_domain_ag_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_land", "all"):
                from world_of_taxonomy.ingest.domain_ag_land import ingest_domain_ag_land
                print("\n-- Domain: Agricultural Land and Soil Classification Types (hand-coded, open) --")
                n = await ingest_domain_ag_land(conn)
                print(f"  {n} nodes")

            if target in ("domain_ag_postharvest", "all"):
                from world_of_taxonomy.ingest.domain_ag_postharvest import ingest_domain_ag_postharvest
                print("\n-- Domain: Agricultural Post-harvest Processing Types (hand-coded, open) --")
                n = await ingest_domain_ag_postharvest(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics11_domains", "all"):
                from world_of_taxonomy.ingest.crosswalk_naics11_domains import ingest_crosswalk_naics11_domains
                print("\n-- Crosswalk: NAICS 11 -> Agriculture Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics11_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_mining_mineral", "all"):
                from world_of_taxonomy.ingest.domain_mining_mineral import ingest_domain_mining_mineral
                print("\n-- Domain: Mining Mineral Types (USGS/SPE, hand-coded, open) --")
                n = await ingest_domain_mining_mineral(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_method", "all"):
                from world_of_taxonomy.ingest.domain_mining_method import ingest_domain_mining_method
                print("\n-- Domain: Mining Extraction Methods (SME, hand-coded, open) --")
                n = await ingest_domain_mining_method(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_reserve", "all"):
                from world_of_taxonomy.ingest.domain_mining_reserve import ingest_domain_mining_reserve
                print("\n-- Domain: Mining Reserve Classification (SPE-PRMS, hand-coded, open) --")
                n = await ingest_domain_mining_reserve(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_equipment", "all"):
                from world_of_taxonomy.ingest.domain_mining_equipment import ingest_domain_mining_equipment
                print("\n-- Domain: Mining Equipment Types (hand-coded, open) --")
                n = await ingest_domain_mining_equipment(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_lifecycle", "all"):
                from world_of_taxonomy.ingest.domain_mining_lifecycle import ingest_domain_mining_lifecycle
                print("\n-- Domain: Mining Project Lifecycle Phase Types (hand-coded, open) --")
                n = await ingest_domain_mining_lifecycle(conn)
                print(f"  {n} nodes")

            if target in ("domain_mining_safety", "all"):
                from world_of_taxonomy.ingest.domain_mining_safety import ingest_domain_mining_safety
                print("\n-- Domain: Mining Safety and Regulatory Compliance Types (hand-coded, open) --")
                n = await ingest_domain_mining_safety(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics21_domains", "all"):
                from world_of_taxonomy.ingest.crosswalk_naics21_domains import ingest_crosswalk_naics21_domains
                print("\n-- Crosswalk: NAICS 21 -> Mining Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics21_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_util_energy", "all"):
                from world_of_taxonomy.ingest.domain_util_energy import ingest_domain_util_energy
                print("\n-- Domain: Utility Energy Sources (IEA/EIA, hand-coded, open) --")
                n = await ingest_domain_util_energy(conn)
                print(f"  {n} nodes")

            if target in ("domain_util_grid", "all"):
                from world_of_taxonomy.ingest.domain_util_grid import ingest_domain_util_grid
                print("\n-- Domain: Utility Grid Regions (NERC, hand-coded, open) --")
                n = await ingest_domain_util_grid(conn)
                print(f"  {n} nodes")

            if target in ("domain_util_tariff", "all"):
                from world_of_taxonomy.ingest.domain_util_tariff import ingest_domain_util_tariff
                print("\n-- Domain: Utility Tariff and Rate Structure Types (hand-coded, open) --")
                n = await ingest_domain_util_tariff(conn)
                print(f"  {n} nodes")

            if target in ("domain_util_asset", "all"):
                from world_of_taxonomy.ingest.domain_util_asset import ingest_domain_util_asset
                print("\n-- Domain: Utility Infrastructure Asset Types (hand-coded, open) --")
                n = await ingest_domain_util_asset(conn)
                print(f"  {n} nodes")

            if target in ("domain_util_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_util_regulatory import ingest_domain_util_regulatory
                print("\n-- Domain: Utility Regulatory Framework Types (hand-coded, open) --")
                n = await ingest_domain_util_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics22_domains", "all"):
                from world_of_taxonomy.ingest.crosswalk_naics22_domains import ingest_crosswalk_naics22_domains
                print("\n-- Crosswalk: NAICS 22 -> Utility Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics22_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_const_trade", "all"):
                from world_of_taxonomy.ingest.domain_const_trade import ingest_domain_const_trade
                print("\n-- Domain: Construction Trade Types (CSI MasterFormat, hand-coded, open) --")
                n = await ingest_domain_const_trade(conn)
                print(f"  {n} nodes")

            if target in ("domain_const_building", "all"):
                from world_of_taxonomy.ingest.domain_const_building import ingest_domain_const_building
                print("\n-- Domain: Construction Building Types (IBC, hand-coded, open) --")
                n = await ingest_domain_const_building(conn)
                print(f"  {n} nodes")

            if target in ("domain_const_delivery", "all"):
                from world_of_taxonomy.ingest.domain_const_delivery import ingest_domain_const_delivery
                print("\n-- Domain: Construction Project Delivery Method Types (hand-coded, open) --")
                n = await ingest_domain_const_delivery(conn)
                print(f"  {n} nodes")

            if target in ("domain_const_material", "all"):
                from world_of_taxonomy.ingest.domain_const_material import ingest_domain_const_material
                print("\n-- Domain: Construction Material System Types (hand-coded, open) --")
                n = await ingest_domain_const_material(conn)
                print(f"  {n} nodes")

            if target in ("domain_const_sustainability", "all"):
                from world_of_taxonomy.ingest.domain_const_sustainability import ingest_domain_const_sustainability
                print("\n-- Domain: Construction Sustainability and Green Building Types (hand-coded, open) --")
                n = await ingest_domain_const_sustainability(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_naics23_domains", "all"):
                from world_of_taxonomy.ingest.crosswalk_naics23_domains import ingest_crosswalk_naics23_domains
                print("\n-- Crosswalk: NAICS 23 -> Construction Domain Taxonomies (derived, open) --")
                n = await ingest_crosswalk_naics23_domains(conn)
                print(f"  {n} edges")

            if target in ("domain_mfg_process", "all"):
                from world_of_taxonomy.ingest.domain_mfg_process import ingest_domain_mfg_process
                print("\n-- Domain: Manufacturing Process Types (NIST, hand-coded, open) --")
                n = await ingest_domain_mfg_process(conn)
                print(f"  {n} nodes")
            if target in ("domain_mfg_industry", "all"):
                from world_of_taxonomy.ingest.domain_mfg_industry import ingest_domain_mfg_industry
                print("\n-- Domain: Manufacturing Industry Vertical (hand-coded, open) --")
                n = await ingest_domain_mfg_industry(conn)
                print(f"  {n} nodes")

            if target in ("domain_mfg_quality", "all"):
                from world_of_taxonomy.ingest.domain_mfg_quality import ingest_domain_mfg_quality
                print("\n-- Domain: Manufacturing Quality and Compliance (hand-coded, open) --")
                n = await ingest_domain_mfg_quality(conn)
                print(f"  {n} nodes")

            if target in ("domain_mfg_opsmodel", "all"):
                from world_of_taxonomy.ingest.domain_mfg_opsmodel import ingest_domain_mfg_opsmodel
                print("\n-- Domain: Manufacturing Operations Model Types (hand-coded, open) --")
                n = await ingest_domain_mfg_opsmodel(conn)
                print(f"  {n} nodes")

            if target in ("domain_retail_channel", "all"):
                from world_of_taxonomy.ingest.domain_retail_channel import ingest_domain_retail_channel
                print("\n-- Domain: Retail Channel Types (NRF, hand-coded, open) --")
                n = await ingest_domain_retail_channel(conn)
                print(f"  {n} nodes")
            if target in ("domain_retail_merchandise", "all"):
                from world_of_taxonomy.ingest.domain_retail_merchandise import ingest_domain_retail_merchandise
                print("\n-- Domain: Retail Merchandise Category Types (hand-coded, open) --")
                n = await ingest_domain_retail_merchandise(conn)
                print(f"  {n} nodes")

            if target in ("domain_retail_fulfillment", "all"):
                from world_of_taxonomy.ingest.domain_retail_fulfillment import ingest_domain_retail_fulfillment
                print("\n-- Domain: Retail Fulfillment and Last-Mile Delivery (hand-coded, open) --")
                n = await ingest_domain_retail_fulfillment(conn)
                print(f"  {n} nodes")

            if target in ("domain_finance_instrument", "all"):
                from world_of_taxonomy.ingest.domain_finance_instrument import ingest_domain_finance_instrument
                print("\n-- Domain: Finance Instrument Types (FIGI framework, hand-coded, open) --")
                n = await ingest_domain_finance_instrument(conn)
                print(f"  {n} nodes")
            if target in ("domain_finance_market", "all"):
                from world_of_taxonomy.ingest.domain_finance_market import ingest_domain_finance_market
                print("\n-- Domain: Finance Market Structure Types (hand-coded, open) --")
                n = await ingest_domain_finance_market(conn)
                print(f"  {n} nodes")

            if target in ("domain_finance_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_finance_regulatory import ingest_domain_finance_regulatory
                print("\n-- Domain: Finance Regulatory Framework Types (hand-coded, open) --")
                n = await ingest_domain_finance_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_health_setting", "all"):
                from world_of_taxonomy.ingest.domain_health_setting import ingest_domain_health_setting
                print("\n-- Domain: Health Care Settings (CMS facility types, hand-coded, open) --")
                n = await ingest_domain_health_setting(conn)
                print(f"  {n} nodes")
            if target in ("domain_health_specialty", "all"):
                from world_of_taxonomy.ingest.domain_health_specialty import ingest_domain_health_specialty
                print("\n-- Domain: Health Care Specialty Service Lines (hand-coded, open) --")
                n = await ingest_domain_health_specialty(conn)
                print(f"  {n} nodes")

            if target in ("domain_health_payer", "all"):
                from world_of_taxonomy.ingest.domain_health_payer import ingest_domain_health_payer
                print("\n-- Domain: Health Care Payer Types (hand-coded, open) --")
                n = await ingest_domain_health_payer(conn)
                print(f"  {n} nodes")

            if target in ("domain_transport_mode", "all"):
                from world_of_taxonomy.ingest.domain_transport_mode import ingest_domain_transport_mode
                print("\n-- Domain: Transportation Modes (DOT modal categories, hand-coded, open) --")
                n = await ingest_domain_transport_mode(conn)
                print(f"  {n} nodes")
            if target in ("domain_transport_service", "all"):
                from world_of_taxonomy.ingest.domain_transport_service import ingest_domain_transport_service
                print("\n-- Domain: Transportation Service Class Types (hand-coded, open) --")
                n = await ingest_domain_transport_service(conn)
                print(f"  {n} nodes")

            if target in ("domain_transport_infra", "all"):
                from world_of_taxonomy.ingest.domain_transport_infra import ingest_domain_transport_infra
                print("\n-- Domain: Transportation Infrastructure Types (hand-coded, open) --")
                n = await ingest_domain_transport_infra(conn)
                print(f"  {n} nodes")

            if target in ("domain_info_media", "all"):
                from world_of_taxonomy.ingest.domain_info_media import ingest_domain_info_media
                print("\n-- Domain: Information and Media Types (NAB/NAICS 51, hand-coded, open) --")
                n = await ingest_domain_info_media(conn)
                print(f"  {n} nodes")
            if target in ("domain_info_revenue", "all"):
                from world_of_taxonomy.ingest.domain_info_revenue import ingest_domain_info_revenue
                print("\n-- Domain: Information and Media Revenue Model Types (hand-coded, open) --")
                n = await ingest_domain_info_revenue(conn)
                print(f"  {n} nodes")

            if target in ("domain_info_platform", "all"):
                from world_of_taxonomy.ingest.domain_info_platform import ingest_domain_info_platform
                print("\n-- Domain: Information Platform and Distribution Types (hand-coded, open) --")
                n = await ingest_domain_info_platform(conn)
                print(f"  {n} nodes")

            if target in ("domain_realestate_type", "all"):
                from world_of_taxonomy.ingest.domain_realestate_type import ingest_domain_realestate_type
                print("\n-- Domain: Real Estate Property Types (CoStar/NCREIF, hand-coded, open) --")
                n = await ingest_domain_realestate_type(conn)
                print(f"  {n} nodes")
            if target in ("domain_realestate_transaction", "all"):
                from world_of_taxonomy.ingest.domain_realestate_transaction import ingest_domain_realestate_transaction
                print("\n-- Domain: Real Estate Transaction Types (hand-coded, open) --")
                n = await ingest_domain_realestate_transaction(conn)
                print(f"  {n} nodes")

            if target in ("domain_realestate_capital", "all"):
                from world_of_taxonomy.ingest.domain_realestate_capital import ingest_domain_realestate_capital
                print("\n-- Domain: Real Estate Capital Structure Types (hand-coded, open) --")
                n = await ingest_domain_realestate_capital(conn)
                print(f"  {n} nodes")

            if target in ("domain_food_service", "all"):
                from world_of_taxonomy.ingest.domain_food_service import ingest_domain_food_service
                print("\n-- Domain: Food Service and Accommodation (STR/NRA, hand-coded, open) --")
                n = await ingest_domain_food_service(conn)
                print(f"  {n} nodes")
            if target in ("domain_food_revenue", "all"):
                from world_of_taxonomy.ingest.domain_food_revenue import ingest_domain_food_revenue
                print("\n-- Domain: Food Service Revenue Mix and Accommodation Types (hand-coded, open) --")
                n = await ingest_domain_food_revenue(conn)
                print(f"  {n} nodes")

            if target in ("domain_food_ownership", "all"):
                from world_of_taxonomy.ingest.domain_food_ownership import ingest_domain_food_ownership
                print("\n-- Domain: Food Service Ownership and Business Model Types (hand-coded, open) --")
                n = await ingest_domain_food_ownership(conn)
                print(f"  {n} nodes")

            if target in ("domain_wholesale_channel", "all"):
                from world_of_taxonomy.ingest.domain_wholesale_channel import ingest_domain_wholesale_channel
                print("\n-- Domain: Wholesale Trade Channels (CSCMP, hand-coded, open) --")
                n = await ingest_domain_wholesale_channel(conn)
                print(f"  {n} nodes")
            if target in ("domain_wholesale_product", "all"):
                from world_of_taxonomy.ingest.domain_wholesale_product import ingest_domain_wholesale_product
                print("\n-- Domain: Wholesale Product Category Types (hand-coded, open) --")
                n = await ingest_domain_wholesale_product(conn)
                print(f"  {n} nodes")

            if target in ("domain_wholesale_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_wholesale_regulatory import ingest_domain_wholesale_regulatory
                print("\n-- Domain: Wholesale Trade Regulatory Framework Types (hand-coded, open) --")
                n = await ingest_domain_wholesale_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_prof_services", "all"):
                from world_of_taxonomy.ingest.domain_prof_services import ingest_domain_prof_services
                print("\n-- Domain: Professional Services Types (AICPA/ABA, hand-coded, open) --")
                n = await ingest_domain_prof_services(conn)
                print(f"  {n} nodes")
            if target in ("domain_prof_firm", "all"):
                from world_of_taxonomy.ingest.domain_prof_firm import ingest_domain_prof_firm
                print("\n-- Domain: Professional Services Firm Size and Structure (hand-coded, open) --")
                n = await ingest_domain_prof_firm(conn)
                print(f"  {n} nodes")

            if target in ("domain_prof_delivery", "all"):
                from world_of_taxonomy.ingest.domain_prof_delivery import ingest_domain_prof_delivery
                print("\n-- Domain: Professional Services Delivery Model Types (hand-coded, open) --")
                n = await ingest_domain_prof_delivery(conn)
                print(f"  {n} nodes")

            if target in ("domain_education_type", "all"):
                from world_of_taxonomy.ingest.domain_education_type import ingest_domain_education_type
                print("\n-- Domain: Education Program Types (NCES, hand-coded, open) --")
                n = await ingest_domain_education_type(conn)
                print(f"  {n} nodes")
            if target in ("domain_education_funding", "all"):
                from world_of_taxonomy.ingest.domain_education_funding import ingest_domain_education_funding
                print("\n-- Domain: Education Funding Source and Governance Types (hand-coded, open) --")
                n = await ingest_domain_education_funding(conn)
                print(f"  {n} nodes")

            if target in ("domain_education_segment", "all"):
                from world_of_taxonomy.ingest.domain_education_segment import ingest_domain_education_segment
                print("\n-- Domain: Education Learner Segment Types (hand-coded, open) --")
                n = await ingest_domain_education_segment(conn)
                print(f"  {n} nodes")

            if target in ("domain_arts_content", "all"):
                from world_of_taxonomy.ingest.domain_arts_content import ingest_domain_arts_content
                print("\n-- Domain: Arts and Entertainment Content Types (ISAN, hand-coded, open) --")
                n = await ingest_domain_arts_content(conn)
                print(f"  {n} nodes")
            if target in ("domain_arts_monetization", "all"):
                from world_of_taxonomy.ingest.domain_arts_monetization import ingest_domain_arts_monetization
                print("\n-- Domain: Arts and Entertainment Monetization Types (hand-coded, open) --")
                n = await ingest_domain_arts_monetization(conn)
                print(f"  {n} nodes")

            if target in ("domain_arts_creator", "all"):
                from world_of_taxonomy.ingest.domain_arts_creator import ingest_domain_arts_creator
                print("\n-- Domain: Arts and Entertainment Creator Structure Types (hand-coded, open) --")
                n = await ingest_domain_arts_creator(conn)
                print(f"  {n} nodes")

            if target in ("domain_other_services", "all"):
                from world_of_taxonomy.ingest.domain_other_services import ingest_domain_other_services
                print("\n-- Domain: Other Services Types (SBA, hand-coded, open) --")
                n = await ingest_domain_other_services(conn)
                print(f"  {n} nodes")
            if target in ("domain_other_pricing", "all"):
                from world_of_taxonomy.ingest.domain_other_pricing import ingest_domain_other_pricing
                print("\n-- Domain: Other Services Pricing and Delivery Model Types (hand-coded, open) --")
                n = await ingest_domain_other_pricing(conn)
                print(f"  {n} nodes")

            if target in ("domain_public_admin", "all"):
                from world_of_taxonomy.ingest.domain_public_admin import ingest_domain_public_admin
                print("\n-- Domain: Public Administration Types (COFOG/NAICS 92, hand-coded, open) --")
                n = await ingest_domain_public_admin(conn)
                print(f"  {n} nodes")
            if target in ("domain_public_funding", "all"):
                from world_of_taxonomy.ingest.domain_public_funding import ingest_domain_public_funding
                print("\n-- Domain: Public Administration Funding Source Types (hand-coded, open) --")
                n = await ingest_domain_public_funding(conn)
                print(f"  {n} nodes")

            if target in ("domain_supply_chain", "all"):
                from world_of_taxonomy.ingest.domain_supply_chain import ingest_domain_supply_chain
                print("\n-- Domain: Supply Chain and Trade Terms (ICC Incoterms 2020, hand-coded, open) --")
                n = await ingest_domain_supply_chain(conn)
                print(f"  {n} nodes")
            if target in ("domain_supply_tech", "all"):
                from world_of_taxonomy.ingest.domain_supply_tech import ingest_domain_supply_tech
                print("\n-- Domain: Supply Chain Technology Platform Types (hand-coded, open) --")
                n = await ingest_domain_supply_tech(conn)
                print(f"  {n} nodes")

            if target in ("domain_supply_risk", "all"):
                from world_of_taxonomy.ingest.domain_supply_risk import ingest_domain_supply_risk
                print("\n-- Domain: Supply Chain Risk Category Types (hand-coded, open) --")
                n = await ingest_domain_supply_risk(conn)
                print(f"  {n} nodes")

            if target in ("domain_workforce_safety", "all"):
                from world_of_taxonomy.ingest.domain_workforce_safety import ingest_domain_workforce_safety
                print("\n-- Domain: Workforce Safety and Health (OSHA 29 CFR, hand-coded, open) --")
                n = await ingest_domain_workforce_safety(conn)
                print(f"  {n} nodes")
            if target in ("domain_workforce_training", "all"):
                from world_of_taxonomy.ingest.domain_workforce_training import ingest_domain_workforce_training
                print("\n-- Domain: Workforce Training and Development Types (hand-coded, open) --")
                n = await ingest_domain_workforce_training(conn)
                print(f"  {n} nodes")

            if target in ("domain_workforce_sms", "all"):
                from world_of_taxonomy.ingest.domain_workforce_sms import ingest_domain_workforce_sms
                print("\n-- Domain: Workforce Safety Management System Types (hand-coded, open) --")
                n = await ingest_domain_workforce_sms(conn)
                print(f"  {n} nodes")

            if target in ("anzsco_2022", "all"):
                from world_of_taxonomy.ingest.anzsco_2022 import ingest_anzsco_2022
                print("\n-- ANZSCO 2022 (ABS SDMX API, CC BY 4.0) --")
                n = await ingest_anzsco_2022(conn)
                print(f"  {n} codes")

            if target in ("crosswalk_anzsco_anzsic", "all"):
                from world_of_taxonomy.ingest.crosswalk_anzsco_anzsic import ingest_crosswalk_anzsco_anzsic
                print("\n-- Crosswalk (ANZSCO 2022 / ANZSIC 2006) --")
                n = await ingest_crosswalk_anzsco_anzsic(conn)
                print(f"  {n} edges")

            if target in ("domain_chemical_type", "all"):
                from world_of_taxonomy.ingest.domain_chemical_type import ingest_domain_chemical_type
                print("\n-- Domain: Chemical Industry Types (hand-coded) --")
                n = await ingest_domain_chemical_type(conn)
                print(f"  {n} nodes")

            if target in ("domain_defence_type", "all"):
                from world_of_taxonomy.ingest.domain_defence_type import ingest_domain_defence_type
                print("\n-- Domain: Defence and Security Types (hand-coded) --")
                n = await ingest_domain_defence_type(conn)
                print(f"  {n} nodes")

            if target in ("domain_water_env", "all"):
                from world_of_taxonomy.ingest.domain_water_env import ingest_domain_water_env
                print("\n-- Domain: Water and Environment Types (hand-coded) --")
                n = await ingest_domain_water_env(conn)
                print(f"  {n} nodes")

            if target in ("domain_ai_data", "all"):
                from world_of_taxonomy.ingest.domain_ai_data import ingest_domain_ai_data
                print("\n-- Domain: AI and Data Types (hand-coded) --")
                n = await ingest_domain_ai_data(conn)
                print(f"  {n} nodes")

            if target in ("domain_biotech", "all"):
                from world_of_taxonomy.ingest.domain_biotech import ingest_domain_biotech
                print("\n-- Domain: Biotechnology and Genomics Types (hand-coded) --")
                n = await ingest_domain_biotech(conn)
                print(f"  {n} nodes")

            if target in ("domain_space", "all"):
                from world_of_taxonomy.ingest.domain_space import ingest_domain_space
                print("\n-- Domain: Space and Satellite Economy Types (hand-coded) --")
                n = await ingest_domain_space(conn)
                print(f"  {n} nodes")

            if target in ("domain_climate_tech", "all"):
                from world_of_taxonomy.ingest.domain_climate_tech import ingest_domain_climate_tech
                print("\n-- Domain: Climate Technology Types (hand-coded) --")
                n = await ingest_domain_climate_tech(conn)
                print(f"  {n} nodes")

            if target in ("domain_adv_materials", "all"):
                from world_of_taxonomy.ingest.domain_adv_materials import ingest_domain_adv_materials
                print("\n-- Domain: Advanced Materials Types (hand-coded) --")
                n = await ingest_domain_adv_materials(conn)
                print(f"  {n} nodes")

            if target in ("domain_quantum", "all"):
                from world_of_taxonomy.ingest.domain_quantum import ingest_domain_quantum
                print("\n-- Domain: Quantum Computing Types (hand-coded) --")
                n = await ingest_domain_quantum(conn)
                print(f"  {n} nodes")

            if target in ("domain_digital_assets", "all"):
                from world_of_taxonomy.ingest.domain_digital_assets import ingest_domain_digital_assets
                print("\n-- Domain: Digital Assets and Web3 Types (hand-coded) --")
                n = await ingest_domain_digital_assets(conn)
                print(f"  {n} nodes")

            if target in ("domain_robotics", "all"):
                from world_of_taxonomy.ingest.domain_robotics import ingest_domain_robotics
                print("\n-- Domain: Autonomous Systems and Robotics Types (hand-coded) --")
                n = await ingest_domain_robotics(conn)
                print(f"  {n} nodes")

            if target in ("domain_energy_storage", "all"):
                from world_of_taxonomy.ingest.domain_energy_storage import ingest_domain_energy_storage
                print("\n-- Domain: New Energy Storage Types (hand-coded) --")
                n = await ingest_domain_energy_storage(conn)
                print(f"  {n} nodes")

            if target in ("domain_semiconductor", "all"):
                from world_of_taxonomy.ingest.domain_semiconductor import ingest_domain_semiconductor
                print("\n-- Domain: Next-Generation Semiconductor Types (hand-coded) --")
                n = await ingest_domain_semiconductor(conn)
                print(f"  {n} nodes")

            if target in ("domain_synbio", "all"):
                from world_of_taxonomy.ingest.domain_synbio import ingest_domain_synbio
                print("\n-- Domain: Synthetic Biology Types (hand-coded) --")
                n = await ingest_domain_synbio(conn)
                print(f"  {n} nodes")

            if target in ("domain_xr_meta", "all"):
                from world_of_taxonomy.ingest.domain_xr_meta import ingest_domain_xr_meta
                print("\n-- Domain: Extended Reality and Metaverse Types (hand-coded) --")
                n = await ingest_domain_xr_meta(conn)
                print(f"  {n} nodes")

            if target in ("cnae_2012", "all"):
                from world_of_taxonomy.ingest.cnae_2012 import ingest_cnae_2012
                print("\n-- CNAE 2.0 (Brazil) --")
                n = await ingest_cnae_2012(conn)
                print(f"  {n} nodes")

            if target in ("csic_2017", "all"):
                from world_of_taxonomy.ingest.csic_2017 import ingest_csic_2017
                print("\n-- CSIC 2017 (China) --")
                n = await ingest_csic_2017(conn)
                print(f"  {n} nodes")

            if target in ("okved_2", "all"):
                from world_of_taxonomy.ingest.okved_2 import ingest_okved_2
                print("\n-- OKVED-2 (Russia) --")
                n = await ingest_okved_2(conn)
                print(f"  {n} nodes")

            if target in ("kbli_2020", "all"):
                from world_of_taxonomy.ingest.kbli_2020 import ingest_kbli_2020
                print("\n-- KBLI 2020 (Indonesia) --")
                n = await ingest_kbli_2020(conn)
                print(f"  {n} nodes")

            if target in ("scian_2018", "all"):
                from world_of_taxonomy.ingest.scian_2018 import ingest_scian_2018
                print("\n-- SCIAN 2018 (Mexico) --")
                n = await ingest_scian_2018(conn)
                print(f"  {n} nodes")

            if target in ("sic_sa", "all"):
                from world_of_taxonomy.ingest.sic_sa import ingest_sic_sa
                print("\n-- SIC-SA (South Africa) --")
                n = await ingest_sic_sa(conn)
                print(f"  {n} nodes")

            if target in ("crosswalk_geo_sector", "all"):
                from world_of_taxonomy.ingest.crosswalk_geo_sector import ingest_crosswalk_geo_sector
                print("\n-- Crosswalk (Nation-Sector Geographic Synergy) --")
                n = await ingest_crosswalk_geo_sector(conn)
                print(f"  {n} edges")

            if target in ("crosswalk_country_system", "all"):
                from world_of_taxonomy.ingest.crosswalk_country_system import ingest_crosswalk_country_system
                print("\n-- Crosswalk (Country -> Classification System applicability) --")
                n = await ingest_crosswalk_country_system(conn)
                print(f"  {n} links")

            if target in ("gbt_4754", "all"):
                from world_of_taxonomy.ingest.gbt_4754 import ingest_gbt_4754
                print("\n-- GB/T 4754-2017 (China national industrial classification) --")
                n = await ingest_gbt_4754(conn)
                print(f"  {n} nodes")

            if target in ("ksic_2017", "all"):
                from world_of_taxonomy.ingest.ksic_2017 import ingest_ksic_2017
                print("\n-- KSIC 2017 (Korean Standard Industry Classification) --")
                n = await ingest_ksic_2017(conn)
                print(f"  {n} nodes")

            if target in ("ssic_2020", "all"):
                from world_of_taxonomy.ingest.ssic_2020 import ingest_ssic_2020
                print("\n-- SSIC 2020 (Singapore Standard Industrial Classification) --")
                n = await ingest_ssic_2020(conn)
                print(f"  {n} nodes")

            if target in ("msic_2008", "all"):
                from world_of_taxonomy.ingest.msic_2008 import ingest_msic_2008
                print("\n-- MSIC 2008 (Malaysia Standard Industrial Classification) --")
                n = await ingest_msic_2008(conn)
                print(f"  {n} nodes")

            if target in ("tsic_2009", "all"):
                from world_of_taxonomy.ingest.tsic_2009 import ingest_tsic_2009
                print("\n-- TSIC 2009 (Thailand Standard Industrial Classification) --")
                n = await ingest_tsic_2009(conn)
                print(f"  {n} nodes")

            if target in ("psic_2009", "all"):
                from world_of_taxonomy.ingest.psic_2009 import ingest_psic_2009
                print("\n-- PSIC 2009 (Philippines Standard Industrial Classification) --")
                n = await ingest_psic_2009(conn)
                print(f"  {n} nodes")

            if target in ("sitc_rev4", "all"):
                from world_of_taxonomy.ingest.sitc_rev4 import ingest_sitc_rev4
                print("\n-- SITC Rev 4 (Standard International Trade Classification) --")
                n = await ingest_sitc_rev4(conn)
                print(f"  {n} nodes")

            if target in ("bec_rev5", "all"):
                from world_of_taxonomy.ingest.bec_rev5 import ingest_bec_rev5
                print("\n-- BEC Rev 5 (Classification by Broad Economic Categories) --")
                n = await ingest_bec_rev5(conn)
                print(f"  {n} nodes")

            if target in ("noc_2021", "all"):
                from world_of_taxonomy.ingest.noc_2021 import ingest_noc_2021
                print("\n-- NOC 2021 (National Occupational Classification Canada) --")
                n = await ingest_noc_2021(conn)
                print(f"  {n} nodes")

            if target in ("uksoc_2020", "all"):
                from world_of_taxonomy.ingest.uksoc_2020 import ingest_uksoc_2020
                print("\n-- UK SOC 2020 (Standard Occupational Classification UK) --")
                n = await ingest_uksoc_2020(conn)
                print(f"  {n} nodes")

            if target in ("kldb_2010", "all"):
                from world_of_taxonomy.ingest.kldb_2010 import ingest_kldb_2010
                print("\n-- KldB 2010 (Klassifikation der Berufe Germany) --")
                n = await ingest_kldb_2010(conn)
                print(f"  {n} nodes")

            if target in ("rome_v4", "all"):
                from world_of_taxonomy.ingest.rome_v4 import ingest_rome_v4
                print("\n-- ROME v4 (Repertoire Operationnel des Metiers France) --")
                n = await ingest_rome_v4(conn)
                print(f"  {n} nodes")

            if target in ("nucc_hcpt", "all"):
                from world_of_taxonomy.ingest.nucc_hcpt import ingest_nucc_hcpt
                print("\n-- NUCC HCPT (Health Care Provider Taxonomy) --")
                n = await ingest_nucc_hcpt(conn)
                print(f"  {n} nodes")

            if target in ("ms_drg", "all"):
                from world_of_taxonomy.ingest.ms_drg import ingest_ms_drg
                print("\n-- MS-DRG (Medicare Severity Diagnosis Related Groups) --")
                n = await ingest_ms_drg(conn)
                print(f"  {n} nodes")

            if target in ("hcpcs_l2", "all"):
                from world_of_taxonomy.ingest.hcpcs_l2 import ingest_hcpcs_l2
                print("\n-- HCPCS Level II (Healthcare Common Procedure Coding System) --")
                n = await ingest_hcpcs_l2(conn)
                print(f"  {n} nodes")

            if target in ("sasb_sics", "all"):
                from world_of_taxonomy.ingest.sasb_sics import ingest_sasb_sics
                print("\n-- SASB SICS (Sustainable Industry Classification System) --")
                n = await ingest_sasb_sics(conn)
                print(f"  {n} nodes")

            if target in ("eu_taxonomy", "all"):
                from world_of_taxonomy.ingest.eu_taxonomy import ingest_eu_taxonomy
                print("\n-- EU Taxonomy for Sustainable Finance --")
                n = await ingest_eu_taxonomy(conn)
                print(f"  {n} nodes")

            if target in ("eu_nuts_2021", "all"):
                from world_of_taxonomy.ingest.eu_nuts_2021 import ingest_eu_nuts_2021
                print("\n-- EU NUTS 2021 (Nomenclature of Territorial Units for Statistics) --")
                n = await ingest_eu_nuts_2021(conn)
                print(f"  {n} nodes")

            if target in ("us_fips", "all"):
                from world_of_taxonomy.ingest.us_fips import ingest_us_fips
                print("\n-- US FIPS (Federal Information Processing Standards state/county codes) --")
                n = await ingest_us_fips(conn)
                print(f"  {n} nodes")

            if target in ("hts_us", "all"):
                from world_of_taxonomy.ingest.hts_us import ingest_hts_us
                print("\n-- HTS (US Harmonized Tariff Schedule) --")
                n = await ingest_hts_us(conn)
                print(f"  {n} nodes")

            if target in ("icd10cm", "all"):
                from world_of_taxonomy.ingest.icd10cm import ingest_icd10cm
                print("\n-- ICD-10-CM (International Classification of Diseases, Clinical Modification US) --")
                n = await ingest_icd10cm(conn)
                print(f"  {n} nodes")

            if target in ("mesh", "all"):
                from world_of_taxonomy.ingest.mesh import ingest_mesh
                print("\n-- MeSH (Medical Subject Headings - NLM) --")
                n = await ingest_mesh(conn)
                print(f"  {n} nodes")

            if target in ("geonames_features", "all"):
                from world_of_taxonomy.ingest.geonames_features import ingest_geonames_features
                print("\n-- GeoNames Feature Codes (CC BY 4.0) --")
                n = await ingest_geonames_features(conn)
                print(f"  {n} nodes")

            if target in ("schema_org", "all"):
                from world_of_taxonomy.ingest.schemaorg import ingest_schemaorg
                print("\n-- schema.org Type Vocabulary (CC BY-SA 3.0) --")
                n = await ingest_schemaorg(conn)
                print(f"  {n} nodes")

            if target in ("fibo", "all"):
                from world_of_taxonomy.ingest.fibo import ingest_fibo
                print("\n-- FIBO (Financial Industry Business Ontology, MIT) --")
                n = await ingest_fibo(conn)
                print(f"  {n} nodes")

            if target in ("wordnet_nouns", "all"):
                from world_of_taxonomy.ingest.wordnet_nouns import ingest_wordnet_nouns
                print("\n-- WordNet Nouns (Princeton WordNet 3.1, BSD-style license) --")
                n = await ingest_wordnet_nouns(conn)
                print(f"  {n} nodes")

            if target in ("prodcom", "all"):
                from world_of_taxonomy.ingest.prodcom import ingest_prodcom
                print("\n-- PRODCOM (EU Industrial Production Survey Classification) --")
                n = await ingest_prodcom(conn)
                print(f"  {n} nodes")

            if target in ("cpv_2008", "all"):
                from world_of_taxonomy.ingest.cpv_2008 import ingest_cpv_2008
                print("\n-- CPV 2008 (EU Common Procurement Vocabulary) --")
                n = await ingest_cpv_2008(conn)
                print(f"  {n} nodes")

            if target in ("acm_ccs", "all"):
                from world_of_taxonomy.ingest.acm_ccs import ingest_acm_ccs
                print("\n-- ACM CCS 2012 (ACM Computing Classification System) --")
                n = await ingest_acm_ccs(conn)
                print(f"  {n} nodes")

            if target in ("jel", "all"):
                from world_of_taxonomy.ingest.jel import ingest_jel
                print("\n-- JEL Codes (Journal of Economic Literature Classification) --")
                n = await ingest_jel(conn)
                print(f"  {{n}} nodes")

            if target in ("domain_chemical_hazard", "all"):
                from world_of_taxonomy.ingest.domain_chemical_hazard import ingest_domain_chemical_hazard
                print("\n-- Chemical Hazard Classification (GHS physical, health, environmental) --")
                n = await ingest_domain_chemical_hazard(conn)
                print(f"  {n} nodes")

            if target in ("domain_chemical_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_chemical_regulatory import ingest_domain_chemical_regulatory
                print("\n-- Chemical Regulatory Frameworks (REACH, TSCA, GHS, transport) --")
                n = await ingest_domain_chemical_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_defence_acquisition", "all"):
                from world_of_taxonomy.ingest.domain_defence_acquisition import ingest_domain_defence_acquisition
                print("\n-- Defence Acquisition Programme Types (ACAT, contract types) --")
                n = await ingest_domain_defence_acquisition(conn)
                print(f"  {n} nodes")

            if target in ("domain_defence_trl", "all"):
                from world_of_taxonomy.ingest.domain_defence_trl import ingest_domain_defence_trl
                print("\n-- Defence Technology Readiness Levels (TRL 1-9) --")
                n = await ingest_domain_defence_trl(conn)
                print(f"  {n} nodes")

            if target in ("domain_water_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_water_regulatory import ingest_domain_water_regulatory
                print("\n-- Water and Environment Regulatory Framework Types --")
                n = await ingest_domain_water_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_water_ecosystem", "all"):
                from world_of_taxonomy.ingest.domain_water_ecosystem import ingest_domain_water_ecosystem
                print("\n-- Water Ecosystem Service Types (CICES, TEEB) --")
                n = await ingest_domain_water_ecosystem(conn)
                print(f"  {n} nodes")

            if target in ("domain_ai_deployment", "all"):
                from world_of_taxonomy.ingest.domain_ai_deployment import ingest_domain_ai_deployment
                print("\n-- AI Deployment Infrastructure Types (cloud, edge, on-premise) --")
                n = await ingest_domain_ai_deployment(conn)
                print(f"  {n} nodes")

            if target in ("domain_ai_governance", "all"):
                from world_of_taxonomy.ingest.domain_ai_governance import ingest_domain_ai_governance
                print("\n-- AI Ethics and Governance Framework Types (EU AI Act, NIST) --")
                n = await ingest_domain_ai_governance(conn)
                print(f"  {n} nodes")

            if target in ("domain_biotech_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_biotech_regulatory import ingest_domain_biotech_regulatory
                print("\n-- Biotechnology Regulatory Pathway Types (FDA, EMA, ATMP) --")
                n = await ingest_domain_biotech_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_biotech_business", "all"):
                from world_of_taxonomy.ingest.domain_biotech_business import ingest_domain_biotech_business
                print("\n-- Biotechnology Business Model Types (platform, licensing, CRO) --")
                n = await ingest_domain_biotech_business(conn)
                print(f"  {n} nodes")

            if target in ("domain_space_orbital", "all"):
                from world_of_taxonomy.ingest.domain_space_orbital import ingest_domain_space_orbital
                print("\n-- Space Orbital Classification Types (LEO, MEO, GEO, HEO, deep) --")
                n = await ingest_domain_space_orbital(conn)
                print(f"  {n} nodes")

            if target in ("domain_space_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_space_regulatory import ingest_domain_space_regulatory
                print("\n-- Space Regulatory and Licensing Framework Types (ITU, FAA, FCC) --")
                n = await ingest_domain_space_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_climate_finance", "all"):
                from world_of_taxonomy.ingest.domain_climate_finance import ingest_domain_climate_finance
                print("\n-- Climate Finance Instrument Types (green bonds, carbon, blended) --")
                n = await ingest_domain_climate_finance(conn)
                print(f"  {n} nodes")

            if target in ("domain_climate_policy", "all"):
                from world_of_taxonomy.ingest.domain_climate_policy import ingest_domain_climate_policy
                print("\n-- Climate Policy Mechanism Types (ETS, standards, subsidies) --")
                n = await ingest_domain_climate_policy(conn)
                print(f"  {n} nodes")

            if target in ("domain_materials_application", "all"):
                from world_of_taxonomy.ingest.domain_materials_application import ingest_domain_materials_application
                print("\n-- Advanced Materials Application Sector Types --")
                n = await ingest_domain_materials_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_materials_process", "all"):
                from world_of_taxonomy.ingest.domain_materials_process import ingest_domain_materials_process
                print("\n-- Advanced Materials Manufacturing Process Types --")
                n = await ingest_domain_materials_process(conn)
                print(f"  {n} nodes")

            if target in ("domain_quantum_application", "all"):
                from world_of_taxonomy.ingest.domain_quantum_application import ingest_domain_quantum_application
                print("\n-- Quantum Computing Application Domain Types --")
                n = await ingest_domain_quantum_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_quantum_stage", "all"):
                from world_of_taxonomy.ingest.domain_quantum_stage import ingest_domain_quantum_stage
                print("\n-- Quantum Technology Commercialization Stage Types --")
                n = await ingest_domain_quantum_stage(conn)
                print(f"  {n} nodes")

            if target in ("domain_digital_assets_regulatory", "all"):
                from world_of_taxonomy.ingest.domain_digital_assets_regulatory import ingest_domain_digital_assets_regulatory
                print("\n-- Digital Assets Regulatory Framework Types (MiCA, FATF) --")
                n = await ingest_domain_digital_assets_regulatory(conn)
                print(f"  {n} nodes")

            if target in ("domain_digital_assets_infra", "all"):
                from world_of_taxonomy.ingest.domain_digital_assets_infra import ingest_domain_digital_assets_infra
                print("\n-- Digital Assets Infrastructure Layer Types (custody, exchange) --")
                n = await ingest_domain_digital_assets_infra(conn)
                print(f"  {n} nodes")

            if target in ("domain_robotics_application", "all"):
                from world_of_taxonomy.ingest.domain_robotics_application import ingest_domain_robotics_application
                print("\n-- Robotics Application Domain Types (industrial, logistics, medical) --")
                n = await ingest_domain_robotics_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_robotics_sensing", "all"):
                from world_of_taxonomy.ingest.domain_robotics_sensing import ingest_domain_robotics_sensing
                print("\n-- Robotics Sensing and Perception Technology Types --")
                n = await ingest_domain_robotics_sensing(conn)
                print(f"  {n} nodes")

            if target in ("domain_energy_storage_application", "all"):
                from world_of_taxonomy.ingest.domain_energy_storage_application import ingest_domain_energy_storage_application
                print("\n-- Energy Storage Application Use Case Types (grid, EV, BTM) --")
                n = await ingest_domain_energy_storage_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_energy_storage_perf", "all"):
                from world_of_taxonomy.ingest.domain_energy_storage_perf import ingest_domain_energy_storage_perf
                print("\n-- Energy Storage Performance and Specification Types --")
                n = await ingest_domain_energy_storage_perf(conn)
                print(f"  {n} nodes")

            if target in ("domain_semiconductor_application", "all"):
                from world_of_taxonomy.ingest.domain_semiconductor_application import ingest_domain_semiconductor_application
                print("\n-- Semiconductor Application End-Market Types --")
                n = await ingest_domain_semiconductor_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_semiconductor_ip", "all"):
                from world_of_taxonomy.ingest.domain_semiconductor_ip import ingest_domain_semiconductor_ip
                print("\n-- Semiconductor IP and Business Model Types (fabless, IDM, OSAT) --")
                n = await ingest_domain_semiconductor_ip(conn)
                print(f"  {n} nodes")

            if target in ("domain_synbio_application", "all"):
                from world_of_taxonomy.ingest.domain_synbio_application import ingest_domain_synbio_application
                print("\n-- Synthetic Biology Application Sector Types --")
                n = await ingest_domain_synbio_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_synbio_biosafety", "all"):
                from world_of_taxonomy.ingest.domain_synbio_biosafety import ingest_domain_synbio_biosafety
                print("\n-- Synthetic Biology Biosafety and Containment Level Types (BSL 1-4) --")
                n = await ingest_domain_synbio_biosafety(conn)
                print(f"  {n} nodes")

            if target in ("domain_xr_application", "all"):
                from world_of_taxonomy.ingest.domain_xr_application import ingest_domain_xr_application
                print("\n-- Extended Reality Application Domain Types --")
                n = await ingest_domain_xr_application(conn)
                print(f"  {n} nodes")

            if target in ("domain_xr_business", "all"):
                from world_of_taxonomy.ingest.domain_xr_business import ingest_domain_xr_business
                print("\n-- Extended Reality Business Model Types --")
                n = await ingest_domain_xr_business(conn)
                print(f"  {n} nodes")

            if target in ("domain_mfg_supply_chain", "all"):
                from world_of_taxonomy.ingest.domain_mfg_supply_chain import ingest_domain_mfg_supply_chain
                print("\n-- Manufacturing Supply Chain Integration Model Types --")
                n = await ingest_domain_mfg_supply_chain(conn)
                print(f"  {n} nodes")

            if target in ("domain_mfg_facility", "all"):
                from world_of_taxonomy.ingest.domain_mfg_facility import ingest_domain_mfg_facility
                print("\n-- Manufacturing Facility and Production Configuration Types --")
                n = await ingest_domain_mfg_facility(conn)
                print(f"  {n} nodes")

            if target in ("domain_retail_pricing", "all"):
                from world_of_taxonomy.ingest.domain_retail_pricing import ingest_domain_retail_pricing
                print("\n-- Retail Pricing Strategy Types (EDLP, hi-lo, premium, dynamic) --")
                n = await ingest_domain_retail_pricing(conn)
                print(f"  {n} nodes")

            if target in ("domain_retail_format", "all"):
                from world_of_taxonomy.ingest.domain_retail_format import ingest_domain_retail_format
                print("\n-- Retail Store Format and Size Types (mass, grocery, specialty) --")
                n = await ingest_domain_retail_format(conn)
                print(f"  {n} nodes")

            if target in ("domain_finance_client", "all"):
                from world_of_taxonomy.ingest.domain_finance_client import ingest_domain_finance_client
                print("\n-- Finance Client and Investor Segment Types (retail, HNW, institutional) --")
                n = await ingest_domain_finance_client(conn)
                print(f"  {n} nodes")

            if target in ("domain_health_delivery", "all"):
                from world_of_taxonomy.ingest.domain_health_delivery import ingest_domain_health_delivery
                print("\n-- Health Care Delivery and Payment Model Types (FFS, VBC, capitation) --")
                n = await ingest_domain_health_delivery(conn)
                print(f"  {n} nodes")

            if target in ("domain_health_it", "all"):
                from world_of_taxonomy.ingest.domain_health_it import ingest_domain_health_it
                print("\n-- Health Information Technology System Types (EHR, RCM, CDSS) --")
                n = await ingest_domain_health_it(conn)
                print(f"  {n} nodes")

            if target in ("domain_transport_fare", "all"):
                from world_of_taxonomy.ingest.domain_transport_fare import ingest_domain_transport_fare
                print("\n-- Transportation Fare and Pricing Model Types --")
                n = await ingest_domain_transport_fare(conn)
                print(f"  {n} nodes")

            if target in ("domain_transport_fleet", "all"):
                from world_of_taxonomy.ingest.domain_transport_fleet import ingest_domain_transport_fleet
                print("\n-- Transportation Fleet Ownership and Operating Model Types --")
                n = await ingest_domain_transport_fleet(conn)
                print(f"  {n} nodes")

            if target in ("domain_info_content", "all"):
                from world_of_taxonomy.ingest.domain_info_content import ingest_domain_info_content
                print("\n-- Information and Media Content Format Types (video, audio, text) --")
                n = await ingest_domain_info_content(conn)
                print(f"  {n} nodes")

            if target in ("domain_realestate_grade", "all"):
                from world_of_taxonomy.ingest.domain_realestate_grade import ingest_domain_realestate_grade
                print("\n-- Real Estate Property Class and Grade Types (A/B/C, core, value-add) --")
                n = await ingest_domain_realestate_grade(conn)
                print(f"  {n} nodes")

            if target in ("domain_realestate_lease", "all"):
                from world_of_taxonomy.ingest.domain_realestate_lease import ingest_domain_realestate_lease
                print("\n-- Real Estate Leasing Structure Types (gross, NNN, ground, percentage) --")
                n = await ingest_domain_realestate_lease(conn)
                print(f"  {n} nodes")

            if target in ("domain_food_cuisine", "all"):
                from world_of_taxonomy.ingest.domain_food_cuisine import ingest_domain_food_cuisine
                print("\n-- Food Service Cuisine and Menu Category Types --")
                n = await ingest_domain_food_cuisine(conn)
                print(f"  {n} nodes")

            if target in ("domain_education_delivery", "all"):
                from world_of_taxonomy.ingest.domain_education_delivery import ingest_domain_education_delivery
                print("\n-- Education Delivery Format and Modality Types (in-person, online, hybrid) --")
                n = await ingest_domain_education_delivery(conn)
                print(f"  {n} nodes")

            if target in ("domain_education_credential", "all"):
                from world_of_taxonomy.ingest.domain_education_credential import ingest_domain_education_credential
                print("\n-- Education Credential and Award Types (certificate through doctorate) --")
                n = await ingest_domain_education_credential(conn)
                print(f"  {n} nodes")

            if target in ("domain_prof_billing", "all"):
                from world_of_taxonomy.ingest.domain_prof_billing import ingest_domain_prof_billing
                print("\n-- Professional Services Billing and Fee Arrangement Types --")
                n = await ingest_domain_prof_billing(conn)
                print(f"  {n} nodes")

            if target in ("domain_arts_venue", "all"):
                from world_of_taxonomy.ingest.domain_arts_venue import ingest_domain_arts_venue
                print("\n-- Arts and Entertainment Venue and Distribution Platform Types --")
                n = await ingest_domain_arts_venue(conn)
                print(f"  {n} nodes")

            if target in ("domain_public_procurement", "all"):
                from world_of_taxonomy.ingest.domain_public_procurement import ingest_domain_public_procurement
                print("\n-- Public Administration Procurement Method Types (competitive, sole-source, PPP) --")
                n = await ingest_domain_public_procurement(conn)
                print(f"  {n} nodes")

            if target in ("domain_supply_logistics", "all"):
                from world_of_taxonomy.ingest.domain_supply_logistics import ingest_domain_supply_logistics
                print("\n-- Supply Chain Logistics Service Model Types (1PL through 5PL) --")
                n = await ingest_domain_supply_logistics(conn)
                print(f"  {n} nodes")

            if target in ("domain_workforce_incident", "all"):
                from world_of_taxonomy.ingest.domain_workforce_incident import ingest_domain_workforce_incident
                print("\n-- Workforce Safety Incident Classification Types (OSHA recordables, near miss) --")
                n = await ingest_domain_workforce_incident(conn)
                print(f"  {n} nodes")

            if target in ("domain_workforce_ppe", "all"):
                from world_of_taxonomy.ingest.domain_workforce_ppe import ingest_domain_workforce_ppe
                print("\n-- Personal Protective Equipment (PPE) Category Types --")
                n = await ingest_domain_workforce_ppe(conn)
                print(f"  {n} nodes")

            if target in ("domain_wholesale_distribution", "all"):
                from world_of_taxonomy.ingest.domain_wholesale_distribution import ingest_domain_wholesale_distribution
                print("\n-- Wholesale Distribution Strategy and Model Types --")
                n = await ingest_domain_wholesale_distribution(conn)
                print(f"  {n} nodes")

            if target in ("icd_11", "all"):
                from world_of_taxonomy.ingest.icd_11 import (
                    ingest_icd_11_from_zip,
                    ingest_icd_11_from_parquet,
                    ingest_icd_11,
                )
                import os
                zip_path = "data/SimpleTabulation-ICD-11-MMS-en.zip"
                parquet_path = "data/icd11_synonyms.parquet"
                csv_path = "data/icd_11.csv"
                if os.path.exists(zip_path):
                    print("\n-- ICD-11 MMS (from WHO SimpleTabulation zip, ~37K nodes, CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11_from_zip(conn, path=zip_path)
                    print(f"  {n} nodes (chapters + blocks + categories)")
                elif os.path.exists(parquet_path):
                    print("\n-- ICD-11 MMS (from parquet, WHO CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11_from_parquet(conn, path=parquet_path)
                    print(f"  {n} nodes (from parquet)")
                elif os.path.exists(csv_path):
                    print("\n-- ICD-11 MMS (from CSV, WHO CC BY-ND 3.0 IGO) --")
                    n = await ingest_icd_11(conn, path=csv_path)
                    print(f"  {n} codes (from CSV)")
                else:
                    print("\n-- ICD-11: skipped (no data file; download from icd.who.int/icdapi) --")

            # ── New NACE-derived EU/EEA (Phase 1) ──

            if target in ("cnae_2009", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_cnae_2009
                print("\n-- CNAE 2009 (Spain) - NACE Rev 2 derived --")
                n = await ingest_cnae_2009(conn)
                print(f"  {n} nodes")

            if target in ("nace_bel", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_bel
                print("\n-- NACE-BEL 2008 (Belgium) - NACE Rev 2 derived --")
                n = await ingest_nace_bel(conn)
                print(f"  {n} nodes")

            if target in ("nace_lu", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_lu
                print("\n-- NACE-LU 2008 (Luxembourg) - NACE Rev 2 derived --")
                n = await ingest_nace_lu(conn)
                print(f"  {n} nodes")

            if target in ("nace_ie", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_ie
                print("\n-- NACE Rev 2 (Ireland) - NACE Rev 2 derived --")
                n = await ingest_nace_ie(conn)
                print(f"  {n} nodes")

            if target in ("stakod_08", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_stakod_08
                print("\n-- STAKOD 08 (Greece) - NACE Rev 2 derived --")
                n = await ingest_stakod_08(conn)
                print(f"  {n} nodes")

            if target in ("nace_cy", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_cy
                print("\n-- NACE Rev 2 (Cyprus) - NACE Rev 2 derived --")
                n = await ingest_nace_cy(conn)
                print(f"  {n} nodes")

            if target in ("nace_mt", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_mt
                print("\n-- NACE Rev 2 (Malta) - NACE Rev 2 derived --")
                n = await ingest_nace_mt(conn)
                print(f"  {n} nodes")

            if target in ("skd_2008", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_skd_2008
                print("\n-- SKD 2008 (Slovenia) - NACE Rev 2 derived --")
                n = await ingest_skd_2008(conn)
                print(f"  {n} nodes")

            if target in ("sn_2007", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_sn_2007
                print("\n-- SN 2007 (Norway) - NACE Rev 2 derived --")
                n = await ingest_sn_2007(conn)
                print(f"  {n} nodes")

            if target in ("isat_2008", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_isat_2008
                print("\n-- ISAT 2008 (Iceland) - NACE Rev 2 derived --")
                n = await ingest_isat_2008(conn)
                print(f"  {n} nodes")

            # ── New NACE-derived Balkans/Eastern (Phase 4a) ──

            if target in ("kd_rs", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_kd_rs
                print("\n-- KD 2010 (Serbia) - NACE Rev 2 derived --")
                n = await ingest_kd_rs(conn)
                print(f"  {n} nodes")

            if target in ("nkd_mk", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nkd_mk
                print("\n-- NKD Rev 2 (North Macedonia) - NACE Rev 2 derived --")
                n = await ingest_nkd_mk(conn)
                print(f"  {n} nodes")

            if target in ("kd_ba", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_kd_ba
                print("\n-- KD BiH 2010 (Bosnia) - NACE Rev 2 derived --")
                n = await ingest_kd_ba(conn)
                print(f"  {n} nodes")

            if target in ("kd_me", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_kd_me
                print("\n-- KD 2010 (Montenegro) - NACE Rev 2 derived --")
                n = await ingest_kd_me(conn)
                print(f"  {n} nodes")

            if target in ("nve_al", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nve_al
                print("\n-- NVE Rev 2 (Albania) - NACE Rev 2 derived --")
                n = await ingest_nve_al(conn)
                print(f"  {n} nodes")

            if target in ("kd_xk", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_kd_xk
                print("\n-- KD 2010 (Kosovo) - NACE Rev 2 derived --")
                n = await ingest_kd_xk(conn)
                print(f"  {n} nodes")

            if target in ("caem_md", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_caem_md
                print("\n-- CAEM Rev 2 (Moldova) - NACE Rev 2 derived --")
                n = await ingest_caem_md(conn)
                print(f"  {n} nodes")

            if target in ("kved_ua", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_kved_ua
                print("\n-- KVED 2010 (Ukraine) - NACE Rev 2 derived --")
                n = await ingest_kved_ua(conn)
                print(f"  {n} nodes")

            if target in ("nace_ge", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_ge
                print("\n-- NACE Rev 2 (Georgia) - NACE Rev 2 derived --")
                n = await ingest_nace_ge(conn)
                print(f"  {n} nodes")

            if target in ("nace_am", "all"):
                from world_of_taxonomy.ingest.nace_derived import ingest_nace_am
                print("\n-- NACE Rev 2 (Armenia) - NACE Rev 2 derived --")
                n = await ingest_nace_am(conn)
                print(f"  {n} nodes")

            # ── New ISIC-derived Phase 2 (25 countries) ──

            if target in ("kbli_id", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_kbli_id
                print("\n-- KBLI 2020 (Indonesia) - ISIC Rev 4 derived --")
                n = await ingest_kbli_id(conn)
                print(f"  {n} nodes")

            if target in ("slsic", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_slsic
                print("\n-- SLSIC (Sri Lanka) - ISIC Rev 4 derived --")
                n = await ingest_slsic(conn)
                print(f"  {n} nodes")

            if target in ("isic_mm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mm
                print("\n-- ISIC Rev 4 (Myanmar) - ISIC Rev 4 derived --")
                n = await ingest_isic_mm(conn)
                print(f"  {n} nodes")

            if target in ("isic_kh", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_kh
                print("\n-- ISIC Rev 4 (Cambodia) - ISIC Rev 4 derived --")
                n = await ingest_isic_kh(conn)
                print(f"  {n} nodes")

            if target in ("isic_la", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_la
                print("\n-- ISIC Rev 4 (Laos) - ISIC Rev 4 derived --")
                n = await ingest_isic_la(conn)
                print(f"  {n} nodes")

            if target in ("isic_np", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_np
                print("\n-- ISIC Rev 4 (Nepal) - ISIC Rev 4 derived --")
                n = await ingest_isic_np(conn)
                print(f"  {n} nodes")

            if target in ("isic_et", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_et
                print("\n-- ISIC Rev 4 (Ethiopia) - ISIC Rev 4 derived --")
                n = await ingest_isic_et(conn)
                print(f"  {n} nodes")

            if target in ("isic_tz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tz
                print("\n-- ISIC Rev 4 (Tanzania) - ISIC Rev 4 derived --")
                n = await ingest_isic_tz(conn)
                print(f"  {n} nodes")

            if target in ("isic_gh", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gh
                print("\n-- ISIC Rev 4 (Ghana) - ISIC Rev 4 derived --")
                n = await ingest_isic_gh(conn)
                print(f"  {n} nodes")

            if target in ("isic_ma", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ma
                print("\n-- ISIC Rev 4 (Morocco) - ISIC Rev 4 derived --")
                n = await ingest_isic_ma(conn)
                print(f"  {n} nodes")

            if target in ("isic_tn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tn
                print("\n-- ISIC Rev 4 (Tunisia) - ISIC Rev 4 derived --")
                n = await ingest_isic_tn(conn)
                print(f"  {n} nodes")

            if target in ("isic_dz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_dz
                print("\n-- ISIC Rev 4 (Algeria) - ISIC Rev 4 derived --")
                n = await ingest_isic_dz(conn)
                print(f"  {n} nodes")

            if target in ("isic_sn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sn
                print("\n-- ISIC Rev 4 (Senegal) - ISIC Rev 4 derived --")
                n = await ingest_isic_sn(conn)
                print(f"  {n} nodes")

            if target in ("isic_cm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_cm
                print("\n-- ISIC Rev 4 (Cameroon) - ISIC Rev 4 derived --")
                n = await ingest_isic_cm(conn)
                print(f"  {n} nodes")

            if target in ("isic_ug", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ug
                print("\n-- ISIC Rev 4 (Uganda) - ISIC Rev 4 derived --")
                n = await ingest_isic_ug(conn)
                print(f"  {n} nodes")

            if target in ("isic_mz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mz
                print("\n-- ISIC Rev 4 (Mozambique) - ISIC Rev 4 derived --")
                n = await ingest_isic_mz(conn)
                print(f"  {n} nodes")

            if target in ("isic_iq", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_iq
                print("\n-- ISIC Rev 4 (Iraq) - ISIC Rev 4 derived --")
                n = await ingest_isic_iq(conn)
                print(f"  {n} nodes")

            if target in ("isic_jo", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_jo
                print("\n-- ISIC Rev 4 (Jordan) - ISIC Rev 4 derived --")
                n = await ingest_isic_jo(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_py", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_py
                print("\n-- CIIU Rev 4 (Paraguay) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_py(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_uy", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_uy
                print("\n-- CIIU Rev 4 (Uruguay) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_uy(conn)
                print(f"  {n} nodes")

            if target in ("ciiu_do", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_ciiu_do
                print("\n-- CIIU Rev 4 (Dominican Republic) - ISIC Rev 4 derived --")
                n = await ingest_ciiu_do(conn)
                print(f"  {n} nodes")

            if target in ("isic_hn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_hn
                print("\n-- ISIC Rev 4 (Honduras) - ISIC Rev 4 derived --")
                n = await ingest_isic_hn(conn)
                print(f"  {n} nodes")

            if target in ("isic_sv", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sv
                print("\n-- ISIC Rev 4 (El Salvador) - ISIC Rev 4 derived --")
                n = await ingest_isic_sv(conn)
                print(f"  {n} nodes")

            if target in ("isic_ni", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ni
                print("\n-- ISIC Rev 4 (Nicaragua) - ISIC Rev 4 derived --")
                n = await ingest_isic_ni(conn)
                print(f"  {n} nodes")

            if target in ("isic_zw", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_zw
                print("\n-- ISIC Rev 4 (Zimbabwe) - ISIC Rev 4 derived --")
                n = await ingest_isic_zw(conn)
                print(f"  {n} nodes")

            # ── New ISIC-derived Phase 4b (20 countries) ──

            if target in ("isic_tt", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tt
                print("\n-- ISIC Rev 4 (Trinidad and Tobago) - ISIC Rev 4 derived --")
                n = await ingest_isic_tt(conn)
                print(f"  {n} nodes")

            if target in ("isic_jm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_jm
                print("\n-- ISIC Rev 4 (Jamaica) - ISIC Rev 4 derived --")
                n = await ingest_isic_jm(conn)
                print(f"  {n} nodes")

            if target in ("isic_ht", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ht
                print("\n-- ISIC Rev 4 (Haiti) - ISIC Rev 4 derived --")
                n = await ingest_isic_ht(conn)
                print(f"  {n} nodes")

            if target in ("isic_fj", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_fj
                print("\n-- ISIC Rev 4 (Fiji) - ISIC Rev 4 derived --")
                n = await ingest_isic_fj(conn)
                print(f"  {n} nodes")

            if target in ("isic_pg", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_pg
                print("\n-- ISIC Rev 4 (Papua New Guinea) - ISIC Rev 4 derived --")
                n = await ingest_isic_pg(conn)
                print(f"  {n} nodes")

            if target in ("isic_mn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mn
                print("\n-- ISIC Rev 4 (Mongolia) - ISIC Rev 4 derived --")
                n = await ingest_isic_mn(conn)
                print(f"  {n} nodes")

            if target in ("isic_kz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_kz
                print("\n-- ISIC Rev 4 (Kazakhstan) - ISIC Rev 4 derived --")
                n = await ingest_isic_kz(conn)
                print(f"  {n} nodes")

            if target in ("isic_uz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_uz
                print("\n-- ISIC Rev 4 (Uzbekistan) - ISIC Rev 4 derived --")
                n = await ingest_isic_uz(conn)
                print(f"  {n} nodes")

            if target in ("isic_az", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_az
                print("\n-- ISIC Rev 4 (Azerbaijan) - ISIC Rev 4 derived --")
                n = await ingest_isic_az(conn)
                print(f"  {n} nodes")

            if target in ("isic_ci", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ci
                print("\n-- ISIC Rev 4 (Ivory Coast) - ISIC Rev 4 derived --")
                n = await ingest_isic_ci(conn)
                print(f"  {n} nodes")

            if target in ("isic_rw", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_rw
                print("\n-- ISIC Rev 4 (Rwanda) - ISIC Rev 4 derived --")
                n = await ingest_isic_rw(conn)
                print(f"  {n} nodes")

            if target in ("isic_zm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_zm
                print("\n-- ISIC Rev 4 (Zambia) - ISIC Rev 4 derived --")
                n = await ingest_isic_zm(conn)
                print(f"  {n} nodes")

            if target in ("isic_bw", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bw
                print("\n-- ISIC Rev 4 (Botswana) - ISIC Rev 4 derived --")
                n = await ingest_isic_bw(conn)
                print(f"  {n} nodes")

            if target in ("isic_na_country", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_na
                print("\n-- ISIC Rev 4 (Namibia) - ISIC Rev 4 derived --")
                n = await ingest_isic_na(conn)
                print(f"  {n} nodes")

            if target in ("isic_mg", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mg
                print("\n-- ISIC Rev 4 (Madagascar) - ISIC Rev 4 derived --")
                n = await ingest_isic_mg(conn)
                print(f"  {n} nodes")

            if target in ("isic_mu", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mu
                print("\n-- ISIC Rev 4 (Mauritius) - ISIC Rev 4 derived --")
                n = await ingest_isic_mu(conn)
                print(f"  {n} nodes")

            if target in ("isic_bf", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bf
                print("\n-- ISIC Rev 4 (Burkina Faso) - ISIC Rev 4 derived --")
                n = await ingest_isic_bf(conn)
                print(f"  {n} nodes")

            if target in ("isic_ml", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ml
                print("\n-- ISIC Rev 4 (Mali) - ISIC Rev 4 derived --")
                n = await ingest_isic_ml(conn)
                print(f"  {n} nodes")

            if target in ("isic_mw", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mw
                print("\n-- ISIC Rev 4 (Malawi) - ISIC Rev 4 derived --")
                n = await ingest_isic_mw(conn)
                print(f"  {n} nodes")

            if target in ("isic_af", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_af
                print("\n-- ISIC Rev 4 (Afghanistan) - ISIC Rev 4 derived --")
                n = await ingest_isic_af(conn)
                print(f"  {n} nodes")

            # ── New Domain Taxonomies (Batch 1: Insurance, Legal, Telecom, Cyber) ──

            if target in ("domain_insurance_product", "all"):
                from world_of_taxonomy.ingest.domain_insurance_product import ingest_domain_insurance_product
                print("\n-- Domain: Insurance Product Types (hand-coded) --")
                n = await ingest_domain_insurance_product(conn)
                print(f"  {n} nodes")

            if target in ("domain_insurance_risk", "all"):
                from world_of_taxonomy.ingest.domain_insurance_risk import ingest_domain_insurance_risk
                print("\n-- Domain: Insurance Risk Classification Types (hand-coded) --")
                n = await ingest_domain_insurance_risk(conn)
                print(f"  {n} nodes")

            if target in ("domain_legal_practice", "all"):
                from world_of_taxonomy.ingest.domain_legal_practice import ingest_domain_legal_practice
                print("\n-- Domain: Legal Practice Area Types (hand-coded) --")
                n = await ingest_domain_legal_practice(conn)
                print(f"  {n} nodes")

            if target in ("domain_telecom_service", "all"):
                from world_of_taxonomy.ingest.domain_telecom_service import ingest_domain_telecom_service
                print("\n-- Domain: Telecom Service Types (hand-coded) --")
                n = await ingest_domain_telecom_service(conn)
                print(f"  {n} nodes")

            if target in ("domain_telecom_network", "all"):
                from world_of_taxonomy.ingest.domain_telecom_network import ingest_domain_telecom_network
                print("\n-- Domain: Telecom Network Technology Types (hand-coded) --")
                n = await ingest_domain_telecom_network(conn)
                print(f"  {n} nodes")

            if target in ("domain_cyber_threat", "all"):
                from world_of_taxonomy.ingest.domain_cyber_threat import ingest_domain_cyber_threat
                print("\n-- Domain: Cybersecurity Threat Types (hand-coded) --")
                n = await ingest_domain_cyber_threat(conn)
                print(f"  {n} nodes")

            if target in ("domain_cyber_framework", "all"):
                from world_of_taxonomy.ingest.domain_cyber_framework import ingest_domain_cyber_framework
                print("\n-- Domain: Cybersecurity Framework Types (hand-coded) --")
                n = await ingest_domain_cyber_framework(conn)
                print(f"  {n} nodes")

            # ── New Domain Taxonomies (Batch 2: Gaming, Waste, Textile, Tourism, Maritime, Aviation, Forestry) ──

            if target in ("domain_gaming_esports", "all"):
                from world_of_taxonomy.ingest.domain_gaming_esports import ingest_domain_gaming_esports
                print("\n-- Domain: Gaming and Esports Types (hand-coded) --")
                n = await ingest_domain_gaming_esports(conn)
                print(f"  {n} nodes")

            if target in ("domain_waste_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_waste_mgmt import ingest_domain_waste_mgmt
                print("\n-- Domain: Waste Management Types (hand-coded) --")
                n = await ingest_domain_waste_mgmt(conn)
                print(f"  {n} nodes")

            if target in ("domain_textile_fashion", "all"):
                from world_of_taxonomy.ingest.domain_textile_fashion import ingest_domain_textile_fashion
                print("\n-- Domain: Textile and Fashion Types (hand-coded) --")
                n = await ingest_domain_textile_fashion(conn)
                print(f"  {n} nodes")

            if target in ("domain_tourism_travel", "all"):
                from world_of_taxonomy.ingest.domain_tourism_travel import ingest_domain_tourism_travel
                print("\n-- Domain: Tourism and Travel Types (hand-coded) --")
                n = await ingest_domain_tourism_travel(conn)
                print(f"  {n} nodes")

            if target in ("domain_maritime_shipping", "all"):
                from world_of_taxonomy.ingest.domain_maritime_shipping import ingest_domain_maritime_shipping
                print("\n-- Domain: Maritime Shipping Types (hand-coded) --")
                n = await ingest_domain_maritime_shipping(conn)
                print(f"  {n} nodes")

            if target in ("domain_aviation_service", "all"):
                from world_of_taxonomy.ingest.domain_aviation_service import ingest_domain_aviation_service
                print("\n-- Domain: Aviation Service Types (hand-coded) --")
                n = await ingest_domain_aviation_service(conn)
                print(f"  {n} nodes")

            if target in ("domain_forestry_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_forestry_mgmt import ingest_domain_forestry_mgmt
                print("\n-- Domain: Forestry Management Types (hand-coded) --")
                n = await ingest_domain_forestry_mgmt(conn)
                print(f"  {n} nodes")

            # ── New Domain Taxonomies (Batch 3: Fishing, Wine, Nuclear, Hydrogen, Pet, Sports, Nonprofit) ──

            if target in ("domain_fishing_aqua", "all"):
                from world_of_taxonomy.ingest.domain_fishing_aqua import ingest_domain_fishing_aqua
                print("\n-- Domain: Fishing and Aquaculture Types (hand-coded) --")
                n = await ingest_domain_fishing_aqua(conn)
                print(f"  {n} nodes")

            if target in ("domain_wine_spirits", "all"):
                from world_of_taxonomy.ingest.domain_wine_spirits import ingest_domain_wine_spirits
                print("\n-- Domain: Wine and Spirits Types (hand-coded) --")
                n = await ingest_domain_wine_spirits(conn)
                print(f"  {n} nodes")

            if target in ("domain_nuclear_energy", "all"):
                from world_of_taxonomy.ingest.domain_nuclear_energy import ingest_domain_nuclear_energy
                print("\n-- Domain: Nuclear Energy Types (hand-coded) --")
                n = await ingest_domain_nuclear_energy(conn)
                print(f"  {n} nodes")

            if target in ("domain_hydrogen_economy", "all"):
                from world_of_taxonomy.ingest.domain_hydrogen_economy import ingest_domain_hydrogen_economy
                print("\n-- Domain: Hydrogen Economy Types (hand-coded) --")
                n = await ingest_domain_hydrogen_economy(conn)
                print(f"  {n} nodes")

            if target in ("domain_pet_animal", "all"):
                from world_of_taxonomy.ingest.domain_pet_animal import ingest_domain_pet_animal
                print("\n-- Domain: Pet and Animal Care Types (hand-coded) --")
                n = await ingest_domain_pet_animal(conn)
                print(f"  {n} nodes")

            if target in ("domain_sports_recreation", "all"):
                from world_of_taxonomy.ingest.domain_sports_recreation import ingest_domain_sports_recreation
                print("\n-- Domain: Sports and Recreation Types (hand-coded) --")
                n = await ingest_domain_sports_recreation(conn)
                print(f"  {n} nodes")

            if target in ("domain_nonprofit_social", "all"):
                from world_of_taxonomy.ingest.domain_nonprofit_social import ingest_domain_nonprofit_social
                print("\n-- Domain: Nonprofit and Social Impact Types (hand-coded) --")
                n = await ingest_domain_nonprofit_social(conn)
                print(f"  {n} nodes")

            # ── New Domain Taxonomies (Batch 4: Childcare, Senior, Advertising, Datacenter, Ecommerce, Fintech, Edtech) ──

            if target in ("domain_childcare_early", "all"):
                from world_of_taxonomy.ingest.domain_childcare_early import ingest_domain_childcare_early
                print("\n-- Domain: Childcare and Early Education Types (hand-coded) --")
                n = await ingest_domain_childcare_early(conn)
                print(f"  {n} nodes")

            if target in ("domain_senior_care", "all"):
                from world_of_taxonomy.ingest.domain_senior_care import ingest_domain_senior_care
                print("\n-- Domain: Senior Care Types (hand-coded) --")
                n = await ingest_domain_senior_care(conn)
                print(f"  {n} nodes")

            if target in ("domain_advertising_mktg", "all"):
                from world_of_taxonomy.ingest.domain_advertising_mktg import ingest_domain_advertising_mktg
                print("\n-- Domain: Advertising and Marketing Types (hand-coded) --")
                n = await ingest_domain_advertising_mktg(conn)
                print(f"  {n} nodes")

            if target in ("domain_datacenter_cloud", "all"):
                from world_of_taxonomy.ingest.domain_datacenter_cloud import ingest_domain_datacenter_cloud
                print("\n-- Domain: Datacenter and Cloud Infrastructure Types (hand-coded) --")
                n = await ingest_domain_datacenter_cloud(conn)
                print(f"  {n} nodes")

            if target in ("domain_ecommerce_platform", "all"):
                from world_of_taxonomy.ingest.domain_ecommerce_platform import ingest_domain_ecommerce_platform
                print("\n-- Domain: E-Commerce Platform Types (hand-coded) --")
                n = await ingest_domain_ecommerce_platform(conn)
                print(f"  {n} nodes")

            if target in ("domain_fintech_service", "all"):
                from world_of_taxonomy.ingest.domain_fintech_service import ingest_domain_fintech_service
                print("\n-- Domain: Fintech Service Types (hand-coded) --")
                n = await ingest_domain_fintech_service(conn)
                print(f"  {n} nodes")

            if target in ("domain_edtech_platform", "all"):
                from world_of_taxonomy.ingest.domain_edtech_platform import ingest_domain_edtech_platform
                print("\n-- Domain: EdTech Platform Types (hand-coded) --")
                n = await ingest_domain_edtech_platform(conn)
                print(f"  {n} nodes")

            # ── New Domain Taxonomies (Batch 5: PropTech, AgriTech, HealthTech, CleanTech, LegalTech, InsurTech, RegTech) ──

            if target in ("domain_proptech", "all"):
                from world_of_taxonomy.ingest.domain_proptech import ingest_domain_proptech
                print("\n-- Domain: PropTech Types (hand-coded) --")
                n = await ingest_domain_proptech(conn)
                print(f"  {n} nodes")

            if target in ("domain_agritech", "all"):
                from world_of_taxonomy.ingest.domain_agritech import ingest_domain_agritech
                print("\n-- Domain: AgriTech Types (hand-coded) --")
                n = await ingest_domain_agritech(conn)
                print(f"  {n} nodes")

            if target in ("domain_healthtech", "all"):
                from world_of_taxonomy.ingest.domain_healthtech import ingest_domain_healthtech
                print("\n-- Domain: HealthTech Types (hand-coded) --")
                n = await ingest_domain_healthtech(conn)
                print(f"  {n} nodes")

            if target in ("domain_cleantech", "all"):
                from world_of_taxonomy.ingest.domain_cleantech import ingest_domain_cleantech
                print("\n-- Domain: CleanTech Types (hand-coded) --")
                n = await ingest_domain_cleantech(conn)
                print(f"  {n} nodes")

            if target in ("domain_legaltech", "all"):
                from world_of_taxonomy.ingest.domain_legaltech import ingest_domain_legaltech
                print("\n-- Domain: LegalTech Types (hand-coded) --")
                n = await ingest_domain_legaltech(conn)
                print(f"  {n} nodes")

            if target in ("domain_insurtech", "all"):
                from world_of_taxonomy.ingest.domain_insurtech import ingest_domain_insurtech
                print("\n-- Domain: InsurTech Types (hand-coded) --")
                n = await ingest_domain_insurtech(conn)
                print(f"  {n} nodes")

            if target in ("domain_regtech", "all"):
                from world_of_taxonomy.ingest.domain_regtech import ingest_domain_regtech
                print("\n-- Domain: RegTech Types (hand-coded) --")
                n = await ingest_domain_regtech(conn)
                print(f"  {n} nodes")

            # ── Phase 1-3: 59 additional ISIC-derived systems ──────────────
            if target in ("isic_lb", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_lb
                print("\n-- ISIC Rev 4 (Lebanon) - ISIC Rev 4 derived --")
                n = await ingest_isic_lb(conn)
                print(f"  {n} nodes")
            if target in ("isic_om", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_om
                print("\n-- ISIC Rev 4 (Oman) - ISIC Rev 4 derived --")
                n = await ingest_isic_om(conn)
                print(f"  {n} nodes")
            if target in ("isic_qa", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_qa
                print("\n-- ISIC Rev 4 (Qatar) - ISIC Rev 4 derived --")
                n = await ingest_isic_qa(conn)
                print(f"  {n} nodes")
            if target in ("isic_bh", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bh
                print("\n-- ISIC Rev 4 (Bahrain) - ISIC Rev 4 derived --")
                n = await ingest_isic_bh(conn)
                print(f"  {n} nodes")
            if target in ("isic_kw", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_kw
                print("\n-- ISIC Rev 4 (Kuwait) - ISIC Rev 4 derived --")
                n = await ingest_isic_kw(conn)
                print(f"  {n} nodes")
            if target in ("isic_ye", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ye
                print("\n-- ISIC Rev 4 (Yemen) - ISIC Rev 4 derived --")
                n = await ingest_isic_ye(conn)
                print(f"  {n} nodes")
            if target in ("isic_ir", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ir
                print("\n-- ISIC Rev 4 (Iran) - ISIC Rev 4 derived --")
                n = await ingest_isic_ir(conn)
                print(f"  {n} nodes")
            if target in ("isic_ly", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ly
                print("\n-- ISIC Rev 4 (Libya) - ISIC Rev 4 derived --")
                n = await ingest_isic_ly(conn)
                print(f"  {n} nodes")
            if target in ("isic_il", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_il
                print("\n-- ISIC Rev 4 (Israel) - ISIC Rev 4 derived --")
                n = await ingest_isic_il(conn)
                print(f"  {n} nodes")
            if target in ("isic_ps", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ps
                print("\n-- ISIC Rev 4 (Palestine) - ISIC Rev 4 derived --")
                n = await ingest_isic_ps(conn)
                print(f"  {n} nodes")
            if target in ("isic_sy", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sy
                print("\n-- ISIC Rev 4 (Syria) - ISIC Rev 4 derived --")
                n = await ingest_isic_sy(conn)
                print(f"  {n} nodes")
            if target in ("isic_kg", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_kg
                print("\n-- ISIC Rev 4 (Kyrgyzstan) - ISIC Rev 4 derived --")
                n = await ingest_isic_kg(conn)
                print(f"  {n} nodes")
            if target in ("isic_tj", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tj
                print("\n-- ISIC Rev 4 (Tajikistan) - ISIC Rev 4 derived --")
                n = await ingest_isic_tj(conn)
                print(f"  {n} nodes")
            if target in ("isic_tm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tm
                print("\n-- ISIC Rev 4 (Turkmenistan) - ISIC Rev 4 derived --")
                n = await ingest_isic_tm(conn)
                print(f"  {n} nodes")
            if target in ("isic_cu", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_cu
                print("\n-- ISIC Rev 4 (Cuba) - ISIC Rev 4 derived --")
                n = await ingest_isic_cu(conn)
                print(f"  {n} nodes")
            if target in ("isic_bb", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bb
                print("\n-- ISIC Rev 4 (Barbados) - ISIC Rev 4 derived --")
                n = await ingest_isic_bb(conn)
                print(f"  {n} nodes")
            if target in ("isic_bs", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bs
                print("\n-- ISIC Rev 4 (Bahamas) - ISIC Rev 4 derived --")
                n = await ingest_isic_bs(conn)
                print(f"  {n} nodes")
            if target in ("isic_gy", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gy
                print("\n-- ISIC Rev 4 (Guyana) - ISIC Rev 4 derived --")
                n = await ingest_isic_gy(conn)
                print(f"  {n} nodes")
            if target in ("isic_sr", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sr
                print("\n-- ISIC Rev 4 (Suriname) - ISIC Rev 4 derived --")
                n = await ingest_isic_sr(conn)
                print(f"  {n} nodes")
            if target in ("isic_bz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bz
                print("\n-- ISIC Rev 4 (Belize) - ISIC Rev 4 derived --")
                n = await ingest_isic_bz(conn)
                print(f"  {n} nodes")
            if target in ("isic_ag", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ag
                print("\n-- ISIC Rev 4 (Antigua and Barbuda) - ISIC Rev 4 derived --")
                n = await ingest_isic_ag(conn)
                print(f"  {n} nodes")
            if target in ("isic_lc", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_lc
                print("\n-- ISIC Rev 4 (Saint Lucia) - ISIC Rev 4 derived --")
                n = await ingest_isic_lc(conn)
                print(f"  {n} nodes")
            if target in ("isic_gd", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gd
                print("\n-- ISIC Rev 4 (Grenada) - ISIC Rev 4 derived --")
                n = await ingest_isic_gd(conn)
                print(f"  {n} nodes")
            if target in ("isic_vc", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_vc
                print("\n-- ISIC Rev 4 (Saint Vincent) - ISIC Rev 4 derived --")
                n = await ingest_isic_vc(conn)
                print(f"  {n} nodes")
            if target in ("isic_dm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_dm
                print("\n-- ISIC Rev 4 (Dominica) - ISIC Rev 4 derived --")
                n = await ingest_isic_dm(conn)
                print(f"  {n} nodes")
            if target in ("isic_kn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_kn
                print("\n-- ISIC Rev 4 (Saint Kitts) - ISIC Rev 4 derived --")
                n = await ingest_isic_kn(conn)
                print(f"  {n} nodes")
            if target in ("isic_ss", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ss
                print("\n-- ISIC Rev 4 (South Sudan) - ISIC Rev 4 derived --")
                n = await ingest_isic_ss(conn)
                print(f"  {n} nodes")
            if target in ("isic_so", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_so
                print("\n-- ISIC Rev 4 (Somalia) - ISIC Rev 4 derived --")
                n = await ingest_isic_so(conn)
                print(f"  {n} nodes")
            if target in ("isic_gn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gn
                print("\n-- ISIC Rev 4 (Guinea) - ISIC Rev 4 derived --")
                n = await ingest_isic_gn(conn)
                print(f"  {n} nodes")
            if target in ("isic_sl", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sl
                print("\n-- ISIC Rev 4 (Sierra Leone) - ISIC Rev 4 derived --")
                n = await ingest_isic_sl(conn)
                print(f"  {n} nodes")
            if target in ("isic_lr", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_lr
                print("\n-- ISIC Rev 4 (Liberia) - ISIC Rev 4 derived --")
                n = await ingest_isic_lr(conn)
                print(f"  {n} nodes")
            if target in ("isic_tg", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tg
                print("\n-- ISIC Rev 4 (Togo) - ISIC Rev 4 derived --")
                n = await ingest_isic_tg(conn)
                print(f"  {n} nodes")
            if target in ("isic_bj", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bj
                print("\n-- ISIC Rev 4 (Benin) - ISIC Rev 4 derived --")
                n = await ingest_isic_bj(conn)
                print(f"  {n} nodes")
            if target in ("isic_ne", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ne
                print("\n-- ISIC Rev 4 (Niger) - ISIC Rev 4 derived --")
                n = await ingest_isic_ne(conn)
                print(f"  {n} nodes")
            if target in ("isic_td", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_td
                print("\n-- ISIC Rev 4 (Chad) - ISIC Rev 4 derived --")
                n = await ingest_isic_td(conn)
                print(f"  {n} nodes")
            if target in ("isic_cd", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_cd
                print("\n-- ISIC Rev 4 (DRC) - ISIC Rev 4 derived --")
                n = await ingest_isic_cd(conn)
                print(f"  {n} nodes")
            if target in ("isic_ao", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ao
                print("\n-- ISIC Rev 4 (Angola) - ISIC Rev 4 derived --")
                n = await ingest_isic_ao(conn)
                print(f"  {n} nodes")
            if target in ("isic_ga", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ga
                print("\n-- ISIC Rev 4 (Gabon) - ISIC Rev 4 derived --")
                n = await ingest_isic_ga(conn)
                print(f"  {n} nodes")
            if target in ("isic_gq", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gq
                print("\n-- ISIC Rev 4 (Equatorial Guinea) - ISIC Rev 4 derived --")
                n = await ingest_isic_gq(conn)
                print(f"  {n} nodes")
            if target in ("isic_cg", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_cg
                print("\n-- ISIC Rev 4 (Congo Republic) - ISIC Rev 4 derived --")
                n = await ingest_isic_cg(conn)
                print(f"  {n} nodes")
            if target in ("isic_km", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_km
                print("\n-- ISIC Rev 4 (Comoros) - ISIC Rev 4 derived --")
                n = await ingest_isic_km(conn)
                print(f"  {n} nodes")
            if target in ("isic_dj", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_dj
                print("\n-- ISIC Rev 4 (Djibouti) - ISIC Rev 4 derived --")
                n = await ingest_isic_dj(conn)
                print(f"  {n} nodes")
            if target in ("isic_cv", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_cv
                print("\n-- ISIC Rev 4 (Cabo Verde) - ISIC Rev 4 derived --")
                n = await ingest_isic_cv(conn)
                print(f"  {n} nodes")
            if target in ("isic_gm", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gm
                print("\n-- ISIC Rev 4 (Gambia) - ISIC Rev 4 derived --")
                n = await ingest_isic_gm(conn)
                print(f"  {n} nodes")
            if target in ("isic_gw", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_gw
                print("\n-- ISIC Rev 4 (Guinea-Bissau) - ISIC Rev 4 derived --")
                n = await ingest_isic_gw(conn)
                print(f"  {n} nodes")
            if target in ("isic_mr", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mr
                print("\n-- ISIC Rev 4 (Mauritania) - ISIC Rev 4 derived --")
                n = await ingest_isic_mr(conn)
                print(f"  {n} nodes")
            if target in ("isic_sz", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sz
                print("\n-- ISIC Rev 4 (Eswatini) - ISIC Rev 4 derived --")
                n = await ingest_isic_sz(conn)
                print(f"  {n} nodes")
            if target in ("isic_ls", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ls
                print("\n-- ISIC Rev 4 (Lesotho) - ISIC Rev 4 derived --")
                n = await ingest_isic_ls(conn)
                print(f"  {n} nodes")
            if target in ("isic_bi", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bi
                print("\n-- ISIC Rev 4 (Burundi) - ISIC Rev 4 derived --")
                n = await ingest_isic_bi(conn)
                print(f"  {n} nodes")
            if target in ("isic_er", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_er
                print("\n-- ISIC Rev 4 (Eritrea) - ISIC Rev 4 derived --")
                n = await ingest_isic_er(conn)
                print(f"  {n} nodes")
            if target in ("isic_sc", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sc
                print("\n-- ISIC Rev 4 (Seychelles) - ISIC Rev 4 derived --")
                n = await ingest_isic_sc(conn)
                print(f"  {n} nodes")
            if target in ("isic_ws", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_ws
                print("\n-- ISIC Rev 4 (Samoa) - ISIC Rev 4 derived --")
                n = await ingest_isic_ws(conn)
                print(f"  {n} nodes")
            if target in ("isic_to", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_to
                print("\n-- ISIC Rev 4 (Tonga) - ISIC Rev 4 derived --")
                n = await ingest_isic_to(conn)
                print(f"  {n} nodes")
            if target in ("isic_vu", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_vu
                print("\n-- ISIC Rev 4 (Vanuatu) - ISIC Rev 4 derived --")
                n = await ingest_isic_vu(conn)
                print(f"  {n} nodes")
            if target in ("isic_sb", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_sb
                print("\n-- ISIC Rev 4 (Solomon Islands) - ISIC Rev 4 derived --")
                n = await ingest_isic_sb(conn)
                print(f"  {n} nodes")
            if target in ("isic_bn", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bn
                print("\n-- ISIC Rev 4 (Brunei) - ISIC Rev 4 derived --")
                n = await ingest_isic_bn(conn)
                print(f"  {n} nodes")
            if target in ("isic_tl", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_tl
                print("\n-- ISIC Rev 4 (East Timor) - ISIC Rev 4 derived --")
                n = await ingest_isic_tl(conn)
                print(f"  {n} nodes")
            if target in ("isic_bt", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_bt
                print("\n-- ISIC Rev 4 (Bhutan) - ISIC Rev 4 derived --")
                n = await ingest_isic_bt(conn)
                print(f"  {n} nodes")
            if target in ("isic_mv", "all"):
                from world_of_taxonomy.ingest.isic_derived import ingest_isic_mv
                print("\n-- ISIC Rev 4 (Maldives) - ISIC Rev 4 derived --")
                n = await ingest_isic_mv(conn)
                print(f"  {n} nodes")

            # ── Phase 4: US Federal Regulatory Standards ──
            if target in ("reg_hipaa", "all"):
                from world_of_taxonomy.ingest.reg_hipaa import ingest_reg_hipaa
                count = await ingest_reg_hipaa(conn)
                print(f"  reg_hipaa: {count} nodes")
            if target in ("reg_sox", "all"):
                from world_of_taxonomy.ingest.reg_sox import ingest_reg_sox
                count = await ingest_reg_sox(conn)
                print(f"  reg_sox: {count} nodes")
            if target in ("reg_glba", "all"):
                from world_of_taxonomy.ingest.reg_glba import ingest_reg_glba
                count = await ingest_reg_glba(conn)
                print(f"  reg_glba: {count} nodes")
            if target in ("reg_ferpa", "all"):
                from world_of_taxonomy.ingest.reg_ferpa import ingest_reg_ferpa
                count = await ingest_reg_ferpa(conn)
                print(f"  reg_ferpa: {count} nodes")
            if target in ("reg_coppa", "all"):
                from world_of_taxonomy.ingest.reg_coppa import ingest_reg_coppa
                count = await ingest_reg_coppa(conn)
                print(f"  reg_coppa: {count} nodes")
            if target in ("reg_fcra", "all"):
                from world_of_taxonomy.ingest.reg_fcra import ingest_reg_fcra
                count = await ingest_reg_fcra(conn)
                print(f"  reg_fcra: {count} nodes")
            if target in ("reg_ada", "all"):
                from world_of_taxonomy.ingest.reg_ada import ingest_reg_ada
                count = await ingest_reg_ada(conn)
                print(f"  reg_ada: {count} nodes")
            if target in ("reg_osha_1910", "all"):
                from world_of_taxonomy.ingest.reg_osha_1910 import ingest_reg_osha_1910
                count = await ingest_reg_osha_1910(conn)
                print(f"  reg_osha_1910: {count} nodes")
            if target in ("reg_osha_1926", "all"):
                from world_of_taxonomy.ingest.reg_osha_1926 import ingest_reg_osha_1926
                count = await ingest_reg_osha_1926(conn)
                print(f"  reg_osha_1926: {count} nodes")
            if target in ("reg_nerc_cip", "all"):
                from world_of_taxonomy.ingest.reg_nerc_cip import ingest_reg_nerc_cip
                count = await ingest_reg_nerc_cip(conn)
                print(f"  reg_nerc_cip: {count} nodes")
            if target in ("reg_fisma", "all"):
                from world_of_taxonomy.ingest.reg_fisma import ingest_reg_fisma
                count = await ingest_reg_fisma(conn)
                print(f"  reg_fisma: {count} nodes")
            if target in ("reg_fedramp", "all"):
                from world_of_taxonomy.ingest.reg_fedramp import ingest_reg_fedramp
                count = await ingest_reg_fedramp(conn)
                print(f"  reg_fedramp: {count} nodes")
            if target in ("reg_ccpa", "all"):
                from world_of_taxonomy.ingest.reg_ccpa import ingest_reg_ccpa
                count = await ingest_reg_ccpa(conn)
                print(f"  reg_ccpa: {count} nodes")
            if target in ("reg_cfpb", "all"):
                from world_of_taxonomy.ingest.reg_cfpb import ingest_reg_cfpb
                count = await ingest_reg_cfpb(conn)
                print(f"  reg_cfpb: {count} nodes")
            if target in ("reg_sec", "all"):
                from world_of_taxonomy.ingest.reg_sec import ingest_reg_sec
                count = await ingest_reg_sec(conn)
                print(f"  reg_sec: {count} nodes")
            if target in ("reg_finra", "all"):
                from world_of_taxonomy.ingest.reg_finra import ingest_reg_finra
                count = await ingest_reg_finra(conn)
                print(f"  reg_finra: {count} nodes")
            if target in ("reg_far", "all"):
                from world_of_taxonomy.ingest.reg_far import ingest_reg_far
                count = await ingest_reg_far(conn)
                print(f"  reg_far: {count} nodes")
            if target in ("reg_dfars", "all"):
                from world_of_taxonomy.ingest.reg_dfars import ingest_reg_dfars
                count = await ingest_reg_dfars(conn)
                print(f"  reg_dfars: {count} nodes")
            if target in ("reg_itar", "all"):
                from world_of_taxonomy.ingest.reg_itar import ingest_reg_itar
                count = await ingest_reg_itar(conn)
                print(f"  reg_itar: {count} nodes")
            if target in ("reg_ear", "all"):
                from world_of_taxonomy.ingest.reg_ear import ingest_reg_ear
                count = await ingest_reg_ear(conn)
                print(f"  reg_ear: {count} nodes")
            if target in ("reg_clean_air", "all"):
                from world_of_taxonomy.ingest.reg_clean_air import ingest_reg_clean_air
                count = await ingest_reg_clean_air(conn)
                print(f"  reg_clean_air: {count} nodes")
            if target in ("reg_clean_water", "all"):
                from world_of_taxonomy.ingest.reg_clean_water import ingest_reg_clean_water
                count = await ingest_reg_clean_water(conn)
                print(f"  reg_clean_water: {count} nodes")
            if target in ("reg_cercla", "all"):
                from world_of_taxonomy.ingest.reg_cercla import ingest_reg_cercla
                count = await ingest_reg_cercla(conn)
                print(f"  reg_cercla: {count} nodes")
            if target in ("reg_rcra", "all"):
                from world_of_taxonomy.ingest.reg_rcra import ingest_reg_rcra
                count = await ingest_reg_rcra(conn)
                print(f"  reg_rcra: {count} nodes")
            if target in ("reg_tsca", "all"):
                from world_of_taxonomy.ingest.reg_tsca import ingest_reg_tsca
                count = await ingest_reg_tsca(conn)
                print(f"  reg_tsca: {count} nodes")

            # ── Phase 5: US Industry Standards + Frameworks ──
            if target in ("reg_pci_dss", "all"):
                from world_of_taxonomy.ingest.reg_pci_dss import ingest_reg_pci_dss
                count = await ingest_reg_pci_dss(conn)
                print(f"  reg_pci_dss: {count} nodes")
            if target in ("reg_soc2", "all"):
                from world_of_taxonomy.ingest.reg_soc2 import ingest_reg_soc2
                count = await ingest_reg_soc2(conn)
                print(f"  reg_soc2: {count} nodes")
            if target in ("reg_hitrust", "all"):
                from world_of_taxonomy.ingest.reg_hitrust import ingest_reg_hitrust
                count = await ingest_reg_hitrust(conn)
                print(f"  reg_hitrust: {count} nodes")
            if target in ("reg_cmmc", "all"):
                from world_of_taxonomy.ingest.reg_cmmc import ingest_reg_cmmc
                count = await ingest_reg_cmmc(conn)
                print(f"  reg_cmmc: {count} nodes")
            if target in ("reg_nist_csf", "all"):
                from world_of_taxonomy.ingest.reg_nist_csf import ingest_reg_nist_csf
                count = await ingest_reg_nist_csf(conn)
                print(f"  reg_nist_csf: {count} nodes")
            if target in ("reg_nist_800_53", "all"):
                from world_of_taxonomy.ingest.reg_nist_800_53 import ingest_reg_nist_800_53
                count = await ingest_reg_nist_800_53(conn)
                print(f"  reg_nist_800_53: {count} nodes")
            if target in ("reg_nist_800_171", "all"):
                from world_of_taxonomy.ingest.reg_nist_800_171 import ingest_reg_nist_800_171
                count = await ingest_reg_nist_800_171(conn)
                print(f"  reg_nist_800_171: {count} nodes")
            if target in ("reg_cis_controls", "all"):
                from world_of_taxonomy.ingest.reg_cis_controls import ingest_reg_cis_controls
                count = await ingest_reg_cis_controls(conn)
                print(f"  reg_cis_controls: {count} nodes")
            if target in ("reg_cobit", "all"):
                from world_of_taxonomy.ingest.reg_cobit import ingest_reg_cobit
                count = await ingest_reg_cobit(conn)
                print(f"  reg_cobit: {count} nodes")
            if target in ("reg_coso", "all"):
                from world_of_taxonomy.ingest.reg_coso import ingest_reg_coso
                count = await ingest_reg_coso(conn)
                print(f"  reg_coso: {count} nodes")
            if target in ("reg_ffiec", "all"):
                from world_of_taxonomy.ingest.reg_ffiec import ingest_reg_ffiec
                count = await ingest_reg_ffiec(conn)
                print(f"  reg_ffiec: {count} nodes")
            if target in ("reg_ftc_safeguards", "all"):
                from world_of_taxonomy.ingest.reg_ftc_safeguards import ingest_reg_ftc_safeguards
                count = await ingest_reg_ftc_safeguards(conn)
                print(f"  reg_ftc_safeguards: {count} nodes")
            if target in ("reg_naic", "all"):
                from world_of_taxonomy.ingest.reg_naic import ingest_reg_naic
                count = await ingest_reg_naic(conn)
                print(f"  reg_naic: {count} nodes")
            if target in ("reg_us_gaap", "all"):
                from world_of_taxonomy.ingest.reg_us_gaap import ingest_reg_us_gaap
                count = await ingest_reg_us_gaap(conn)
                print(f"  reg_us_gaap: {count} nodes")
            if target in ("reg_fasb", "all"):
                from world_of_taxonomy.ingest.reg_fasb import ingest_reg_fasb
                count = await ingest_reg_fasb(conn)
                print(f"  reg_fasb: {count} nodes")
            if target in ("reg_pcaob", "all"):
                from world_of_taxonomy.ingest.reg_pcaob import ingest_reg_pcaob
                count = await ingest_reg_pcaob(conn)
                print(f"  reg_pcaob: {count} nodes")
            if target in ("reg_aicpa", "all"):
                from world_of_taxonomy.ingest.reg_aicpa import ingest_reg_aicpa
                count = await ingest_reg_aicpa(conn)
                print(f"  reg_aicpa: {count} nodes")
            if target in ("reg_joint_commission", "all"):
                from world_of_taxonomy.ingest.reg_joint_commission import ingest_reg_joint_commission
                count = await ingest_reg_joint_commission(conn)
                print(f"  reg_joint_commission: {count} nodes")
            if target in ("reg_cap", "all"):
                from world_of_taxonomy.ingest.reg_cap import ingest_reg_cap
                count = await ingest_reg_cap(conn)
                print(f"  reg_cap: {count} nodes")
            if target in ("reg_clia", "all"):
                from world_of_taxonomy.ingest.reg_clia import ingest_reg_clia
                count = await ingest_reg_clia(conn)
                print(f"  reg_clia: {count} nodes")
            if target in ("reg_fda_21cfr", "all"):
                from world_of_taxonomy.ingest.reg_fda_21cfr import ingest_reg_fda_21cfr
                count = await ingest_reg_fda_21cfr(conn)
                print(f"  reg_fda_21cfr: {count} nodes")
            if target in ("reg_dea", "all"):
                from world_of_taxonomy.ingest.reg_dea import ingest_reg_dea
                count = await ingest_reg_dea(conn)
                print(f"  reg_dea: {count} nodes")
            if target in ("reg_usp", "all"):
                from world_of_taxonomy.ingest.reg_usp import ingest_reg_usp
                count = await ingest_reg_usp(conn)
                print(f"  reg_usp: {count} nodes")
            if target in ("reg_ashrae", "all"):
                from world_of_taxonomy.ingest.reg_ashrae import ingest_reg_ashrae
                count = await ingest_reg_ashrae(conn)
                print(f"  reg_ashrae: {count} nodes")
            if target in ("reg_asme", "all"):
                from world_of_taxonomy.ingest.reg_asme import ingest_reg_asme
                count = await ingest_reg_asme(conn)
                print(f"  reg_asme: {count} nodes")
            if target in ("reg_dora", "all"):
                from world_of_taxonomy.ingest.reg_dora import ingest_reg_dora
                count = await ingest_reg_dora(conn)
                print(f"  reg_dora: {count} nodes")
            if target in ("reg_nis2", "all"):
                from world_of_taxonomy.ingest.reg_nis2 import ingest_reg_nis2
                count = await ingest_reg_nis2(conn)
                print(f"  reg_nis2: {count} nodes")
            if target in ("reg_eu_ai_act", "all"):
                from world_of_taxonomy.ingest.reg_eu_ai_act import ingest_reg_eu_ai_act
                count = await ingest_reg_eu_ai_act(conn)
                print(f"  reg_eu_ai_act: {count} nodes")
            if target in ("reg_eprivacy", "all"):
                from world_of_taxonomy.ingest.reg_eprivacy import ingest_reg_eprivacy
                count = await ingest_reg_eprivacy(conn)
                print(f"  reg_eprivacy: {count} nodes")
            if target in ("reg_mifid2", "all"):
                from world_of_taxonomy.ingest.reg_mifid2 import ingest_reg_mifid2
                count = await ingest_reg_mifid2(conn)
                print(f"  reg_mifid2: {count} nodes")
            if target in ("reg_solvency2", "all"):
                from world_of_taxonomy.ingest.reg_solvency2 import ingest_reg_solvency2
                count = await ingest_reg_solvency2(conn)
                print(f"  reg_solvency2: {count} nodes")
            if target in ("reg_psd2", "all"):
                from world_of_taxonomy.ingest.reg_psd2 import ingest_reg_psd2
                count = await ingest_reg_psd2(conn)
                print(f"  reg_psd2: {count} nodes")
            if target in ("reg_reach", "all"):
                from world_of_taxonomy.ingest.reg_reach import ingest_reg_reach
                count = await ingest_reg_reach(conn)
                print(f"  reg_reach: {count} nodes")
            if target in ("reg_rohs", "all"):
                from world_of_taxonomy.ingest.reg_rohs import ingest_reg_rohs
                count = await ingest_reg_rohs(conn)
                print(f"  reg_rohs: {count} nodes")
            if target in ("reg_mdr", "all"):
                from world_of_taxonomy.ingest.reg_mdr import ingest_reg_mdr
                count = await ingest_reg_mdr(conn)
                print(f"  reg_mdr: {count} nodes")
            if target in ("reg_ivdr", "all"):
                from world_of_taxonomy.ingest.reg_ivdr import ingest_reg_ivdr
                count = await ingest_reg_ivdr(conn)
                print(f"  reg_ivdr: {count} nodes")
            if target in ("reg_eu_whistleblower", "all"):
                from world_of_taxonomy.ingest.reg_eu_whistleblower import ingest_reg_eu_whistleblower
                count = await ingest_reg_eu_whistleblower(conn)
                print(f"  reg_eu_whistleblower: {count} nodes")
            if target in ("reg_csrd", "all"):
                from world_of_taxonomy.ingest.reg_csrd import ingest_reg_csrd
                count = await ingest_reg_csrd(conn)
                print(f"  reg_csrd: {count} nodes")
            if target in ("reg_cbam", "all"):
                from world_of_taxonomy.ingest.reg_cbam import ingest_reg_cbam
                count = await ingest_reg_cbam(conn)
                print(f"  reg_cbam: {count} nodes")
            if target in ("reg_weee", "all"):
                from world_of_taxonomy.ingest.reg_weee import ingest_reg_weee
                count = await ingest_reg_weee(conn)
                print(f"  reg_weee: {count} nodes")
            if target in ("reg_eu_packaging", "all"):
                from world_of_taxonomy.ingest.reg_eu_packaging import ingest_reg_eu_packaging
                count = await ingest_reg_eu_packaging(conn)
                print(f"  reg_eu_packaging: {count} nodes")
            if target in ("reg_eu_batteries", "all"):
                from world_of_taxonomy.ingest.reg_eu_batteries import ingest_reg_eu_batteries
                count = await ingest_reg_eu_batteries(conn)
                print(f"  reg_eu_batteries: {count} nodes")
            if target in ("reg_sfdr_detail", "all"):
                from world_of_taxonomy.ingest.reg_sfdr_detail import ingest_reg_sfdr_detail
                count = await ingest_reg_sfdr_detail(conn)
                print(f"  reg_sfdr_detail: {count} nodes")
            if target in ("reg_eu_deforestation", "all"):
                from world_of_taxonomy.ingest.reg_eu_deforestation import ingest_reg_eu_deforestation
                count = await ingest_reg_eu_deforestation(conn)
                print(f"  reg_eu_deforestation: {count} nodes")
            if target in ("reg_dsa", "all"):
                from world_of_taxonomy.ingest.reg_dsa import ingest_reg_dsa
                count = await ingest_reg_dsa(conn)
                print(f"  reg_dsa: {count} nodes")
            if target in ("reg_dma", "all"):
                from world_of_taxonomy.ingest.reg_dma import ingest_reg_dma
                count = await ingest_reg_dma(conn)
                print(f"  reg_dma: {count} nodes")
            if target in ("reg_eu_cra", "all"):
                from world_of_taxonomy.ingest.reg_eu_cra import ingest_reg_eu_cra
                count = await ingest_reg_eu_cra(conn)
                print(f"  reg_eu_cra: {count} nodes")
            if target in ("reg_eu_data_act", "all"):
                from world_of_taxonomy.ingest.reg_eu_data_act import ingest_reg_eu_data_act
                count = await ingest_reg_eu_data_act(conn)
                print(f"  reg_eu_data_act: {count} nodes")
            if target in ("reg_eu_machinery", "all"):
                from world_of_taxonomy.ingest.reg_eu_machinery import ingest_reg_eu_machinery
                count = await ingest_reg_eu_machinery(conn)
                print(f"  reg_eu_machinery: {count} nodes")
            if target in ("reg_emas", "all"):
                from world_of_taxonomy.ingest.reg_emas import ingest_reg_emas
                count = await ingest_reg_emas(conn)
                print(f"  reg_emas: {count} nodes")
            if target in ("reg_iso_9001", "all"):
                from world_of_taxonomy.ingest.reg_iso_9001 import ingest_reg_iso_9001
                count = await ingest_reg_iso_9001(conn)
                print(f"  reg_iso_9001: {count} nodes")
            if target in ("reg_iso_14001", "all"):
                from world_of_taxonomy.ingest.reg_iso_14001 import ingest_reg_iso_14001
                count = await ingest_reg_iso_14001(conn)
                print(f"  reg_iso_14001: {count} nodes")
            if target in ("reg_iso_27001", "all"):
                from world_of_taxonomy.ingest.reg_iso_27001 import ingest_reg_iso_27001
                count = await ingest_reg_iso_27001(conn)
                print(f"  reg_iso_27001: {count} nodes")
            if target in ("reg_iso_22000", "all"):
                from world_of_taxonomy.ingest.reg_iso_22000 import ingest_reg_iso_22000
                count = await ingest_reg_iso_22000(conn)
                print(f"  reg_iso_22000: {count} nodes")
            if target in ("reg_iso_45001", "all"):
                from world_of_taxonomy.ingest.reg_iso_45001 import ingest_reg_iso_45001
                count = await ingest_reg_iso_45001(conn)
                print(f"  reg_iso_45001: {count} nodes")
            if target in ("reg_iso_50001", "all"):
                from world_of_taxonomy.ingest.reg_iso_50001 import ingest_reg_iso_50001
                count = await ingest_reg_iso_50001(conn)
                print(f"  reg_iso_50001: {count} nodes")
            if target in ("reg_iso_13485", "all"):
                from world_of_taxonomy.ingest.reg_iso_13485 import ingest_reg_iso_13485
                count = await ingest_reg_iso_13485(conn)
                print(f"  reg_iso_13485: {count} nodes")
            if target in ("reg_iso_22301", "all"):
                from world_of_taxonomy.ingest.reg_iso_22301 import ingest_reg_iso_22301
                count = await ingest_reg_iso_22301(conn)
                print(f"  reg_iso_22301: {count} nodes")
            if target in ("reg_iso_20000", "all"):
                from world_of_taxonomy.ingest.reg_iso_20000 import ingest_reg_iso_20000
                count = await ingest_reg_iso_20000(conn)
                print(f"  reg_iso_20000: {count} nodes")
            if target in ("reg_iso_26000", "all"):
                from world_of_taxonomy.ingest.reg_iso_26000 import ingest_reg_iso_26000
                count = await ingest_reg_iso_26000(conn)
                print(f"  reg_iso_26000: {count} nodes")
            if target in ("reg_iso_37001", "all"):
                from world_of_taxonomy.ingest.reg_iso_37001 import ingest_reg_iso_37001
                count = await ingest_reg_iso_37001(conn)
                print(f"  reg_iso_37001: {count} nodes")
            if target in ("reg_iso_42001", "all"):
                from world_of_taxonomy.ingest.reg_iso_42001 import ingest_reg_iso_42001
                count = await ingest_reg_iso_42001(conn)
                print(f"  reg_iso_42001: {count} nodes")
            if target in ("reg_iso_28000", "all"):
                from world_of_taxonomy.ingest.reg_iso_28000 import ingest_reg_iso_28000
                count = await ingest_reg_iso_28000(conn)
                print(f"  reg_iso_28000: {count} nodes")
            if target in ("reg_iso_55001", "all"):
                from world_of_taxonomy.ingest.reg_iso_55001 import ingest_reg_iso_55001
                count = await ingest_reg_iso_55001(conn)
                print(f"  reg_iso_55001: {count} nodes")
            if target in ("reg_iso_41001", "all"):
                from world_of_taxonomy.ingest.reg_iso_41001 import ingest_reg_iso_41001
                count = await ingest_reg_iso_41001(conn)
                print(f"  reg_iso_41001: {count} nodes")
            if target in ("reg_iso_30401", "all"):
                from world_of_taxonomy.ingest.reg_iso_30401 import ingest_reg_iso_30401
                count = await ingest_reg_iso_30401(conn)
                print(f"  reg_iso_30401: {count} nodes")
            if target in ("reg_iso_21001", "all"):
                from world_of_taxonomy.ingest.reg_iso_21001 import ingest_reg_iso_21001
                count = await ingest_reg_iso_21001(conn)
                print(f"  reg_iso_21001: {count} nodes")
            if target in ("reg_iso_39001", "all"):
                from world_of_taxonomy.ingest.reg_iso_39001 import ingest_reg_iso_39001
                count = await ingest_reg_iso_39001(conn)
                print(f"  reg_iso_39001: {count} nodes")
            if target in ("reg_iso_37101", "all"):
                from world_of_taxonomy.ingest.reg_iso_37101 import ingest_reg_iso_37101
                count = await ingest_reg_iso_37101(conn)
                print(f"  reg_iso_37101: {count} nodes")
            if target in ("reg_iso_14064", "all"):
                from world_of_taxonomy.ingest.reg_iso_14064 import ingest_reg_iso_14064
                count = await ingest_reg_iso_14064(conn)
                print(f"  reg_iso_14064: {count} nodes")
            if target in ("reg_iso_14040", "all"):
                from world_of_taxonomy.ingest.reg_iso_14040 import ingest_reg_iso_14040
                count = await ingest_reg_iso_14040(conn)
                print(f"  reg_iso_14040: {count} nodes")
            if target in ("reg_iso_19011", "all"):
                from world_of_taxonomy.ingest.reg_iso_19011 import ingest_reg_iso_19011
                count = await ingest_reg_iso_19011(conn)
                print(f"  reg_iso_19011: {count} nodes")
            if target in ("reg_iso_31010", "all"):
                from world_of_taxonomy.ingest.reg_iso_31010 import ingest_reg_iso_31010
                count = await ingest_reg_iso_31010(conn)
                print(f"  reg_iso_31010: {count} nodes")
            if target in ("reg_iso_22313", "all"):
                from world_of_taxonomy.ingest.reg_iso_22313 import ingest_reg_iso_22313
                count = await ingest_reg_iso_22313(conn)
                print(f"  reg_iso_22313: {count} nodes")
            if target in ("reg_iso_27701", "all"):
                from world_of_taxonomy.ingest.reg_iso_27701 import ingest_reg_iso_27701
                count = await ingest_reg_iso_27701(conn)
                print(f"  reg_iso_27701: {count} nodes")
            if target in ("reg_basel3", "all"):
                from world_of_taxonomy.ingest.reg_basel3 import ingest_reg_basel3
                count = await ingest_reg_basel3(conn)
                print(f"  reg_basel3: {count} nodes")
            if target in ("reg_fatf", "all"):
                from world_of_taxonomy.ingest.reg_fatf import ingest_reg_fatf
                count = await ingest_reg_fatf(conn)
                print(f"  reg_fatf: {count} nodes")
            if target in ("reg_ilo_core", "all"):
                from world_of_taxonomy.ingest.reg_ilo_core import ingest_reg_ilo_core
                count = await ingest_reg_ilo_core(conn)
                print(f"  reg_ilo_core: {count} nodes")
            if target in ("reg_ungp", "all"):
                from world_of_taxonomy.ingest.reg_ungp import ingest_reg_ungp
                count = await ingest_reg_ungp(conn)
                print(f"  reg_ungp: {count} nodes")
            if target in ("reg_oecd_mne", "all"):
                from world_of_taxonomy.ingest.reg_oecd_mne import ingest_reg_oecd_mne
                count = await ingest_reg_oecd_mne(conn)
                print(f"  reg_oecd_mne: {count} nodes")
            if target in ("reg_wto_sps", "all"):
                from world_of_taxonomy.ingest.reg_wto_sps import ingest_reg_wto_sps
                count = await ingest_reg_wto_sps(conn)
                print(f"  reg_wto_sps: {count} nodes")
            if target in ("reg_wto_tbt", "all"):
                from world_of_taxonomy.ingest.reg_wto_tbt import ingest_reg_wto_tbt
                count = await ingest_reg_wto_tbt(conn)
                print(f"  reg_wto_tbt: {count} nodes")
            if target in ("reg_codex", "all"):
                from world_of_taxonomy.ingest.reg_codex import ingest_reg_codex
                count = await ingest_reg_codex(conn)
                print(f"  reg_codex: {count} nodes")
            if target in ("reg_who_fctc", "all"):
                from world_of_taxonomy.ingest.reg_who_fctc import ingest_reg_who_fctc
                count = await ingest_reg_who_fctc(conn)
                print(f"  reg_who_fctc: {count} nodes")
            if target in ("reg_uncitral", "all"):
                from world_of_taxonomy.ingest.reg_uncitral import ingest_reg_uncitral
                count = await ingest_reg_uncitral(conn)
                print(f"  reg_uncitral: {count} nodes")
            if target in ("reg_unclos", "all"):
                from world_of_taxonomy.ingest.reg_unclos import ingest_reg_unclos
                count = await ingest_reg_unclos(conn)
                print(f"  reg_unclos: {count} nodes")
            if target in ("reg_montreal", "all"):
                from world_of_taxonomy.ingest.reg_montreal import ingest_reg_montreal
                count = await ingest_reg_montreal(conn)
                print(f"  reg_montreal: {count} nodes")
            if target in ("reg_paris", "all"):
                from world_of_taxonomy.ingest.reg_paris import ingest_reg_paris
                count = await ingest_reg_paris(conn)
                print(f"  reg_paris: {count} nodes")
            if target in ("reg_kimberley", "all"):
                from world_of_taxonomy.ingest.reg_kimberley import ingest_reg_kimberley
                count = await ingest_reg_kimberley(conn)
                print(f"  reg_kimberley: {count} nodes")
            if target in ("reg_equator", "all"):
                from world_of_taxonomy.ingest.reg_equator import ingest_reg_equator
                count = await ingest_reg_equator(conn)
                print(f"  reg_equator: {count} nodes")
            if target in ("reg_ifc_ps", "all"):
                from world_of_taxonomy.ingest.reg_ifc_ps import ingest_reg_ifc_ps
                count = await ingest_reg_ifc_ps(conn)
                print(f"  reg_ifc_ps: {count} nodes")
            if target in ("reg_icao_annex", "all"):
                from world_of_taxonomy.ingest.reg_icao_annex import ingest_reg_icao_annex
                count = await ingest_reg_icao_annex(conn)
                print(f"  reg_icao_annex: {count} nodes")
            if target in ("reg_marpol", "all"):
                from world_of_taxonomy.ingest.reg_marpol import ingest_reg_marpol
                count = await ingest_reg_marpol(conn)
                print(f"  reg_marpol: {count} nodes")
            if target in ("reg_solas", "all"):
                from world_of_taxonomy.ingest.reg_solas import ingest_reg_solas
                count = await ingest_reg_solas(conn)
                print(f"  reg_solas: {count} nodes")
            if target in ("reg_berne", "all"):
                from world_of_taxonomy.ingest.reg_berne import ingest_reg_berne
                count = await ingest_reg_berne(conn)
                print(f"  reg_berne: {count} nodes")
            if target in ("domain_pharma_drug_class", "all"):
                from world_of_taxonomy.ingest.domain_pharma_drug_class import ingest_domain_pharma_drug_class
                count = await ingest_domain_pharma_drug_class(conn)
                print(f"  domain_pharma_drug_class: {count} nodes")
            if target in ("domain_medical_device", "all"):
                from world_of_taxonomy.ingest.domain_medical_device import ingest_domain_medical_device
                count = await ingest_domain_medical_device(conn)
                print(f"  domain_medical_device: {count} nodes")
            if target in ("domain_clinical_trial", "all"):
                from world_of_taxonomy.ingest.domain_clinical_trial import ingest_domain_clinical_trial
                count = await ingest_domain_clinical_trial(conn)
                print(f"  domain_clinical_trial: {count} nodes")
            if target in ("domain_mental_health", "all"):
                from world_of_taxonomy.ingest.domain_mental_health import ingest_domain_mental_health
                count = await ingest_domain_mental_health(conn)
                print(f"  domain_mental_health: {count} nodes")
            if target in ("domain_dental", "all"):
                from world_of_taxonomy.ingest.domain_dental import ingest_domain_dental
                count = await ingest_domain_dental(conn)
                print(f"  domain_dental: {count} nodes")
            if target in ("domain_veterinary", "all"):
                from world_of_taxonomy.ingest.domain_veterinary import ingest_domain_veterinary
                count = await ingest_domain_veterinary(conn)
                print(f"  domain_veterinary: {count} nodes")
            if target in ("domain_credit_rating", "all"):
                from world_of_taxonomy.ingest.domain_credit_rating import ingest_domain_credit_rating
                count = await ingest_domain_credit_rating(conn)
                print(f"  domain_credit_rating: {count} nodes")
            if target in ("domain_derivatives", "all"):
                from world_of_taxonomy.ingest.domain_derivatives import ingest_domain_derivatives
                count = await ingest_domain_derivatives(conn)
                print(f"  domain_derivatives: {count} nodes")
            if target in ("domain_pe_stage", "all"):
                from world_of_taxonomy.ingest.domain_pe_stage import ingest_domain_pe_stage
                count = await ingest_domain_pe_stage(conn)
                print(f"  domain_pe_stage: {count} nodes")
            if target in ("domain_digital_banking", "all"):
                from world_of_taxonomy.ingest.domain_digital_banking import ingest_domain_digital_banking
                count = await ingest_domain_digital_banking(conn)
                print(f"  domain_digital_banking: {count} nodes")
            if target in ("domain_payment_proc", "all"):
                from world_of_taxonomy.ingest.domain_payment_proc import ingest_domain_payment_proc
                count = await ingest_domain_payment_proc(conn)
                print(f"  domain_payment_proc: {count} nodes")
            if target in ("domain_trade_finance", "all"):
                from world_of_taxonomy.ingest.domain_trade_finance import ingest_domain_trade_finance
                count = await ingest_domain_trade_finance(conn)
                print(f"  domain_trade_finance: {count} nodes")
            if target in ("domain_reinsurance", "all"):
                from world_of_taxonomy.ingest.domain_reinsurance import ingest_domain_reinsurance
                count = await ingest_domain_reinsurance(conn)
                print(f"  domain_reinsurance: {count} nodes")
            if target in ("domain_microfinance", "all"):
                from world_of_taxonomy.ingest.domain_microfinance import ingest_domain_microfinance
                count = await ingest_domain_microfinance(conn)
                print(f"  domain_microfinance: {count} nodes")
            if target in ("domain_auto_vehicle_level", "all"):
                from world_of_taxonomy.ingest.domain_auto_vehicle_level import ingest_domain_auto_vehicle_level
                count = await ingest_domain_auto_vehicle_level(conn)
                print(f"  domain_auto_vehicle_level: {count} nodes")
            if target in ("domain_ev_charging", "all"):
                from world_of_taxonomy.ingest.domain_ev_charging import ingest_domain_ev_charging
                count = await ingest_domain_ev_charging(conn)
                print(f"  domain_ev_charging: {count} nodes")
            if target in ("domain_fleet_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_fleet_mgmt import ingest_domain_fleet_mgmt
                count = await ingest_domain_fleet_mgmt(conn)
                print(f"  domain_fleet_mgmt: {count} nodes")
            if target in ("domain_rail_service", "all"):
                from world_of_taxonomy.ingest.domain_rail_service import ingest_domain_rail_service
                count = await ingest_domain_rail_service(conn)
                print(f"  domain_rail_service: {count} nodes")
            if target in ("domain_last_mile", "all"):
                from world_of_taxonomy.ingest.domain_last_mile import ingest_domain_last_mile
                count = await ingest_domain_last_mile(conn)
                print(f"  domain_last_mile: {count} nodes")
            if target in ("domain_solar_energy", "all"):
                from world_of_taxonomy.ingest.domain_solar_energy import ingest_domain_solar_energy
                count = await ingest_domain_solar_energy(conn)
                print(f"  domain_solar_energy: {count} nodes")
            if target in ("domain_wind_energy", "all"):
                from world_of_taxonomy.ingest.domain_wind_energy import ingest_domain_wind_energy
                count = await ingest_domain_wind_energy(conn)
                print(f"  domain_wind_energy: {count} nodes")
            if target in ("domain_battery_tech", "all"):
                from world_of_taxonomy.ingest.domain_battery_tech import ingest_domain_battery_tech
                count = await ingest_domain_battery_tech(conn)
                print(f"  domain_battery_tech: {count} nodes")
            if target in ("domain_smart_grid", "all"):
                from world_of_taxonomy.ingest.domain_smart_grid import ingest_domain_smart_grid
                count = await ingest_domain_smart_grid(conn)
                print(f"  domain_smart_grid: {count} nodes")
            if target in ("domain_carbon_credit", "all"):
                from world_of_taxonomy.ingest.domain_carbon_credit import ingest_domain_carbon_credit
                count = await ingest_domain_carbon_credit(conn)
                print(f"  domain_carbon_credit: {count} nodes")
            if target in ("domain_cloud_service", "all"):
                from world_of_taxonomy.ingest.domain_cloud_service import ingest_domain_cloud_service
                count = await ingest_domain_cloud_service(conn)
                print(f"  domain_cloud_service: {count} nodes")
            if target in ("domain_devops", "all"):
                from world_of_taxonomy.ingest.domain_devops import ingest_domain_devops
                count = await ingest_domain_devops(conn)
                print(f"  domain_devops: {count} nodes")
            if target in ("domain_saas_category", "all"):
                from world_of_taxonomy.ingest.domain_saas_category import ingest_domain_saas_category
                count = await ingest_domain_saas_category(conn)
                print(f"  domain_saas_category: {count} nodes")
            if target in ("domain_iot_device", "all"):
                from world_of_taxonomy.ingest.domain_iot_device import ingest_domain_iot_device
                count = await ingest_domain_iot_device(conn)
                print(f"  domain_iot_device: {count} nodes")
            if target in ("domain_organic_cert", "all"):
                from world_of_taxonomy.ingest.domain_organic_cert import ingest_domain_organic_cert
                count = await ingest_domain_organic_cert(conn)
                print(f"  domain_organic_cert: {count} nodes")
            if target in ("domain_crop_protection", "all"):
                from world_of_taxonomy.ingest.domain_crop_protection import ingest_domain_crop_protection
                count = await ingest_domain_crop_protection(conn)
                print(f"  domain_crop_protection: {count} nodes")
            if target in ("domain_soil_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_soil_mgmt import ingest_domain_soil_mgmt
                count = await ingest_domain_soil_mgmt(conn)
                print(f"  domain_soil_mgmt: {count} nodes")
            if target in ("domain_precision_ag", "all"):
                from world_of_taxonomy.ingest.domain_precision_ag import ingest_domain_precision_ag
                count = await ingest_domain_precision_ag(conn)
                print(f"  domain_precision_ag: {count} nodes")
            if target in ("domain_digital_twin", "all"):
                from world_of_taxonomy.ingest.domain_digital_twin import ingest_domain_digital_twin
                count = await ingest_domain_digital_twin(conn)
                print(f"  domain_digital_twin: {count} nodes")
            if target in ("domain_edge_computing", "all"):
                from world_of_taxonomy.ingest.domain_edge_computing import ingest_domain_edge_computing
                count = await ingest_domain_edge_computing(conn)
                print(f"  domain_edge_computing: {count} nodes")
            if target in ("domain_coworking", "all"):
                from world_of_taxonomy.ingest.domain_coworking import ingest_domain_coworking
                count = await ingest_domain_coworking(conn)
                print(f"  domain_coworking: {count} nodes")
            if target in ("domain_event_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_event_mgmt import ingest_domain_event_mgmt
                count = await ingest_domain_event_mgmt(conn)
                print(f"  domain_event_mgmt: {count} nodes")
            if target in ("domain_franchise", "all"):
                from world_of_taxonomy.ingest.domain_franchise import ingest_domain_franchise
                count = await ingest_domain_franchise(conn)
                print(f"  domain_franchise: {count} nodes")
            if target in ("domain_subscription", "all"):
                from world_of_taxonomy.ingest.domain_subscription import ingest_domain_subscription
                count = await ingest_domain_subscription(conn)
                print(f"  domain_subscription: {count} nodes")
            if target in ("domain_circular_econ", "all"):
                from world_of_taxonomy.ingest.domain_circular_econ import ingest_domain_circular_econ
                count = await ingest_domain_circular_econ(conn)
                print(f"  domain_circular_econ: {count} nodes")
            if target in ("domain_sharing_econ", "all"):
                from world_of_taxonomy.ingest.domain_sharing_econ import ingest_domain_sharing_econ
                count = await ingest_domain_sharing_econ(conn)
                print(f"  domain_sharing_econ: {count} nodes")
            if target in ("domain_hr_tech", "all"):
                from world_of_taxonomy.ingest.domain_hr_tech import ingest_domain_hr_tech
                count = await ingest_domain_hr_tech(conn)
                print(f"  domain_hr_tech: {count} nodes")
            if target in ("domain_talent_market", "domain_insurance_underwriting", "domain_insurance_claims", "domain_actuarial_method", "domain_commercial_lending", "domain_mortgage_type", "domain_wealth_mgmt", "domain_hedge_fund", "domain_commodity_trading", "domain_forex", "domain_bond_rating", "domain_muni_bond", "domain_securitization", "domain_reit_type", "domain_property_val", "domain_zoning", "domain_construction_permit", "domain_building_code", "domain_fire_protection", "domain_elevator", "domain_plumbing_code", "domain_electrical_code", "domain_hvac_system", "domain_roofing_type", "domain_foundation_type", "domain_structural", "domain_facade", "domain_landscape", "domain_parking", "domain_signage", "domain_accessibility", "domain_env_remediation", "domain_brownfield", "domain_green_material", "domain_modular_const", "domain_prefab", "domain_smart_building", "domain_building_auto", "domain_energy_audit", "domain_commissioning", "domain_retro_cx", "domain_facility_bench", "domain_lease_abstract", "domain_api_architecture", "domain_database_type", "domain_prog_paradigm", "domain_sw_license", "domain_oss_governance", "domain_version_control", "domain_cicd_pipeline", "domain_container_orch", "domain_serverless", "domain_microservices", "domain_event_arch", "domain_data_mesh", "domain_data_lakehouse", "domain_mlops", "domain_feature_store", "domain_model_registry", "domain_data_catalog", "domain_data_quality", "domain_data_governance", "domain_data_lineage", "domain_master_data", "domain_ref_data", "domain_synthetic_data", "domain_pet", "domain_zero_trust", "domain_identity_gov", "domain_siem", "domain_soar", "domain_threat_intel", "domain_vuln_mgmt", "domain_pentest", "domain_incident_resp", "domain_dr", "domain_backup", "domain_encryption", "domain_key_mgmt", "domain_cert_authority", "domain_pki", "domain_hsm", "domain_red_team", "domain_blue_team", "domain_purple_team", "domain_hospital_dept", "domain_nursing_spec", "domain_allied_health", "domain_lab_test", "domain_imaging", "domain_surgical_spec", "domain_anesthesia", "domain_pathology_sub", "domain_pharma_practice", "domain_formulary", "domain_drug_interaction", "domain_adverse_event", "domain_clinical_endpoint", "domain_biomarker", "domain_companion_dx", "domain_orphan_drug", "domain_biosimilar", "domain_gene_therapy", "domain_cell_therapy", "domain_radiopharm", "domain_med_gas", "domain_surgical_inst", "domain_implant", "domain_wound_care", "domain_infection_ctrl", "domain_sterilization", "domain_cleanroom", "domain_biobank", "domain_clinical_reg", "domain_pro", "domain_telemedicine", "domain_remote_monitor", "domain_cds", "domain_sdoh", "domain_pop_health", "domain_vbc_model", "domain_bundled_pay", "domain_capitation", "domain_global_budget", "domain_prosthetic", "domain_orthotic", "domain_health_literacy", "domain_oil_grade", "domain_nat_gas", "domain_lng_terminal", "domain_pipeline", "domain_refinery", "domain_petrochem", "domain_biofuel", "domain_geothermal", "domain_tidal", "domain_wave_energy", "domain_district_heat", "domain_cogeneration", "domain_microgrid_type", "domain_vpp", "domain_demand_resp", "domain_ancillary", "domain_capacity_mkt", "domain_rec", "domain_carbon_offset", "domain_emission_factor", "domain_air_quality", "domain_water_quality", "domain_soil_contam", "domain_biodiv_offset", "domain_wetland", "domain_seed_variety", "domain_irrigation", "domain_greenhouse", "domain_aquaponics", "domain_vertical_farm", "domain_cold_chain", "domain_warehouse", "domain_cross_dock", "domain_freight_class", "domain_incoterm_detail", "domain_customs_proc", "domain_ftz", "domain_noise_pollution", "domain_light_pollution", "domain_invasive_sp", "domain_coral_reef", "domain_mangrove", "domain_univ_ranking", "domain_accreditation", "domain_student_assess", "domain_curriculum", "domain_learning_outcome", "domain_competency", "domain_micro_cred", "domain_apprentice", "domain_gig_worker", "domain_employee_benefit", "domain_comp_structure", "domain_labor_union", "domain_eeo_category", "domain_diversity_metric", "domain_gov_contract", "domain_grant_type", "domain_municipal_svc", "domain_emergency_svc", "domain_court_type", "domain_adr", "domain_trademark", "domain_patent_type", "domain_copyright", "domain_trade_secret", "domain_antitrust", "domain_consumer_prot", "domain_sanctions", "domain_export_ctrl", "domain_customs_class", "domain_internship", "domain_workplace_med", "domain_coll_bargain", "domain_product_liab", "domain_law_enforce", "domain_corrections", "domain_notary", "domain_class_action", "domain_freelance_plat", "domain_digital_badge", "domain_arb_type", "icd10_ca", "snomed_ct", "cpt_ama", "g_drg", "rxnorm", "ndc_fda", "dsm5", "icpc2", "ichi_who", "gbd_cause", "gmdn", "who_essential_med", "cdc_vaccine", "nci_thesaurus", "ctcae", "ifrs", "bloomberg_bics", "refinitiv_trbc", "sfia_v8", "digcomp_22", "ecf_v4", "scopus_asjc", "wos_categories", "eqf", "aqf", "onet_knowledge", "onet_abilities", "iucn_red_list", "cites", "eu_waste_cat", "stockholm_pops", "rotterdam_pic", "minamata", "iata_aircraft", "imo_vessel", "ietf_rfc", "w3c_standards", "ieee_standards", "usb_classes", "bluetooth_profiles", "all"):
                from world_of_taxonomy.ingest.domain_talent_market import ingest_domain_talent_market
                count = await ingest_domain_talent_market(conn)
                print(f"  domain_talent_market: {count} nodes")
            if target in ("domain_insurance_underwriting", "all"):
                from world_of_taxonomy.ingest.domain_insurance_underwriting import ingest_domain_insurance_underwriting
                count = await ingest_domain_insurance_underwriting(conn)
                print(f"  domain_insurance_underwriting: {count} nodes")
            if target in ("domain_insurance_claims", "all"):
                from world_of_taxonomy.ingest.domain_insurance_claims import ingest_domain_insurance_claims
                count = await ingest_domain_insurance_claims(conn)
                print(f"  domain_insurance_claims: {count} nodes")
            if target in ("domain_actuarial_method", "all"):
                from world_of_taxonomy.ingest.domain_actuarial_method import ingest_domain_actuarial_method
                count = await ingest_domain_actuarial_method(conn)
                print(f"  domain_actuarial_method: {count} nodes")
            if target in ("domain_commercial_lending", "all"):
                from world_of_taxonomy.ingest.domain_commercial_lending import ingest_domain_commercial_lending
                count = await ingest_domain_commercial_lending(conn)
                print(f"  domain_commercial_lending: {count} nodes")
            if target in ("domain_mortgage_type", "all"):
                from world_of_taxonomy.ingest.domain_mortgage_type import ingest_domain_mortgage_type
                count = await ingest_domain_mortgage_type(conn)
                print(f"  domain_mortgage_type: {count} nodes")
            if target in ("domain_wealth_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_wealth_mgmt import ingest_domain_wealth_mgmt
                count = await ingest_domain_wealth_mgmt(conn)
                print(f"  domain_wealth_mgmt: {count} nodes")
            if target in ("domain_hedge_fund", "all"):
                from world_of_taxonomy.ingest.domain_hedge_fund import ingest_domain_hedge_fund
                count = await ingest_domain_hedge_fund(conn)
                print(f"  domain_hedge_fund: {count} nodes")
            if target in ("domain_commodity_trading", "all"):
                from world_of_taxonomy.ingest.domain_commodity_trading import ingest_domain_commodity_trading
                count = await ingest_domain_commodity_trading(conn)
                print(f"  domain_commodity_trading: {count} nodes")
            if target in ("domain_forex", "all"):
                from world_of_taxonomy.ingest.domain_forex import ingest_domain_forex
                count = await ingest_domain_forex(conn)
                print(f"  domain_forex: {count} nodes")
            if target in ("domain_bond_rating", "all"):
                from world_of_taxonomy.ingest.domain_bond_rating import ingest_domain_bond_rating
                count = await ingest_domain_bond_rating(conn)
                print(f"  domain_bond_rating: {count} nodes")
            if target in ("domain_muni_bond", "all"):
                from world_of_taxonomy.ingest.domain_muni_bond import ingest_domain_muni_bond
                count = await ingest_domain_muni_bond(conn)
                print(f"  domain_muni_bond: {count} nodes")
            if target in ("domain_securitization", "all"):
                from world_of_taxonomy.ingest.domain_securitization import ingest_domain_securitization
                count = await ingest_domain_securitization(conn)
                print(f"  domain_securitization: {count} nodes")
            if target in ("domain_reit_type", "all"):
                from world_of_taxonomy.ingest.domain_reit_type import ingest_domain_reit_type
                count = await ingest_domain_reit_type(conn)
                print(f"  domain_reit_type: {count} nodes")
            if target in ("domain_property_val", "all"):
                from world_of_taxonomy.ingest.domain_property_val import ingest_domain_property_val
                count = await ingest_domain_property_val(conn)
                print(f"  domain_property_val: {count} nodes")
            if target in ("domain_zoning", "all"):
                from world_of_taxonomy.ingest.domain_zoning import ingest_domain_zoning
                count = await ingest_domain_zoning(conn)
                print(f"  domain_zoning: {count} nodes")
            if target in ("domain_construction_permit", "all"):
                from world_of_taxonomy.ingest.domain_construction_permit import ingest_domain_construction_permit
                count = await ingest_domain_construction_permit(conn)
                print(f"  domain_construction_permit: {count} nodes")
            if target in ("domain_building_code", "all"):
                from world_of_taxonomy.ingest.domain_building_code import ingest_domain_building_code
                count = await ingest_domain_building_code(conn)
                print(f"  domain_building_code: {count} nodes")
            if target in ("domain_fire_protection", "all"):
                from world_of_taxonomy.ingest.domain_fire_protection import ingest_domain_fire_protection
                count = await ingest_domain_fire_protection(conn)
                print(f"  domain_fire_protection: {count} nodes")
            if target in ("domain_elevator", "all"):
                from world_of_taxonomy.ingest.domain_elevator import ingest_domain_elevator
                count = await ingest_domain_elevator(conn)
                print(f"  domain_elevator: {count} nodes")
            if target in ("domain_plumbing_code", "all"):
                from world_of_taxonomy.ingest.domain_plumbing_code import ingest_domain_plumbing_code
                count = await ingest_domain_plumbing_code(conn)
                print(f"  domain_plumbing_code: {count} nodes")
            if target in ("domain_electrical_code", "all"):
                from world_of_taxonomy.ingest.domain_electrical_code import ingest_domain_electrical_code
                count = await ingest_domain_electrical_code(conn)
                print(f"  domain_electrical_code: {count} nodes")
            if target in ("domain_hvac_system", "all"):
                from world_of_taxonomy.ingest.domain_hvac_system import ingest_domain_hvac_system
                count = await ingest_domain_hvac_system(conn)
                print(f"  domain_hvac_system: {count} nodes")
            if target in ("domain_roofing_type", "all"):
                from world_of_taxonomy.ingest.domain_roofing_type import ingest_domain_roofing_type
                count = await ingest_domain_roofing_type(conn)
                print(f"  domain_roofing_type: {count} nodes")
            if target in ("domain_foundation_type", "all"):
                from world_of_taxonomy.ingest.domain_foundation_type import ingest_domain_foundation_type
                count = await ingest_domain_foundation_type(conn)
                print(f"  domain_foundation_type: {count} nodes")
            if target in ("domain_structural", "all"):
                from world_of_taxonomy.ingest.domain_structural import ingest_domain_structural
                count = await ingest_domain_structural(conn)
                print(f"  domain_structural: {count} nodes")
            if target in ("domain_facade", "all"):
                from world_of_taxonomy.ingest.domain_facade import ingest_domain_facade
                count = await ingest_domain_facade(conn)
                print(f"  domain_facade: {count} nodes")
            if target in ("domain_landscape", "all"):
                from world_of_taxonomy.ingest.domain_landscape import ingest_domain_landscape
                count = await ingest_domain_landscape(conn)
                print(f"  domain_landscape: {count} nodes")
            if target in ("domain_parking", "all"):
                from world_of_taxonomy.ingest.domain_parking import ingest_domain_parking
                count = await ingest_domain_parking(conn)
                print(f"  domain_parking: {count} nodes")
            if target in ("domain_signage", "all"):
                from world_of_taxonomy.ingest.domain_signage import ingest_domain_signage
                count = await ingest_domain_signage(conn)
                print(f"  domain_signage: {count} nodes")
            if target in ("domain_accessibility", "all"):
                from world_of_taxonomy.ingest.domain_accessibility import ingest_domain_accessibility
                count = await ingest_domain_accessibility(conn)
                print(f"  domain_accessibility: {count} nodes")
            if target in ("domain_env_remediation", "all"):
                from world_of_taxonomy.ingest.domain_env_remediation import ingest_domain_env_remediation
                count = await ingest_domain_env_remediation(conn)
                print(f"  domain_env_remediation: {count} nodes")
            if target in ("domain_brownfield", "all"):
                from world_of_taxonomy.ingest.domain_brownfield import ingest_domain_brownfield
                count = await ingest_domain_brownfield(conn)
                print(f"  domain_brownfield: {count} nodes")
            if target in ("domain_green_material", "all"):
                from world_of_taxonomy.ingest.domain_green_material import ingest_domain_green_material
                count = await ingest_domain_green_material(conn)
                print(f"  domain_green_material: {count} nodes")
            if target in ("domain_modular_const", "all"):
                from world_of_taxonomy.ingest.domain_modular_const import ingest_domain_modular_const
                count = await ingest_domain_modular_const(conn)
                print(f"  domain_modular_const: {count} nodes")
            if target in ("domain_prefab", "all"):
                from world_of_taxonomy.ingest.domain_prefab import ingest_domain_prefab
                count = await ingest_domain_prefab(conn)
                print(f"  domain_prefab: {count} nodes")
            if target in ("domain_smart_building", "all"):
                from world_of_taxonomy.ingest.domain_smart_building import ingest_domain_smart_building
                count = await ingest_domain_smart_building(conn)
                print(f"  domain_smart_building: {count} nodes")
            if target in ("domain_building_auto", "all"):
                from world_of_taxonomy.ingest.domain_building_auto import ingest_domain_building_auto
                count = await ingest_domain_building_auto(conn)
                print(f"  domain_building_auto: {count} nodes")
            if target in ("domain_energy_audit", "all"):
                from world_of_taxonomy.ingest.domain_energy_audit import ingest_domain_energy_audit
                count = await ingest_domain_energy_audit(conn)
                print(f"  domain_energy_audit: {count} nodes")
            if target in ("domain_commissioning", "all"):
                from world_of_taxonomy.ingest.domain_commissioning import ingest_domain_commissioning
                count = await ingest_domain_commissioning(conn)
                print(f"  domain_commissioning: {count} nodes")
            if target in ("domain_retro_cx", "all"):
                from world_of_taxonomy.ingest.domain_retro_cx import ingest_domain_retro_cx
                count = await ingest_domain_retro_cx(conn)
                print(f"  domain_retro_cx: {count} nodes")
            if target in ("domain_facility_bench", "all"):
                from world_of_taxonomy.ingest.domain_facility_bench import ingest_domain_facility_bench
                count = await ingest_domain_facility_bench(conn)
                print(f"  domain_facility_bench: {count} nodes")
            if target in ("domain_lease_abstract", "domain_api_architecture", "domain_database_type", "domain_prog_paradigm", "domain_sw_license", "domain_oss_governance", "domain_version_control", "domain_cicd_pipeline", "domain_container_orch", "domain_serverless", "domain_microservices", "domain_event_arch", "domain_data_mesh", "domain_data_lakehouse", "domain_mlops", "domain_feature_store", "domain_model_registry", "domain_data_catalog", "domain_data_quality", "domain_data_governance", "domain_data_lineage", "domain_master_data", "domain_ref_data", "domain_synthetic_data", "domain_pet", "domain_zero_trust", "domain_identity_gov", "domain_siem", "domain_soar", "domain_threat_intel", "domain_vuln_mgmt", "domain_pentest", "domain_incident_resp", "domain_dr", "domain_backup", "domain_encryption", "domain_key_mgmt", "domain_cert_authority", "domain_pki", "domain_hsm", "domain_red_team", "domain_blue_team", "domain_purple_team", "domain_hospital_dept", "domain_nursing_spec", "domain_allied_health", "domain_lab_test", "domain_imaging", "domain_surgical_spec", "domain_anesthesia", "domain_pathology_sub", "domain_pharma_practice", "domain_formulary", "domain_drug_interaction", "domain_adverse_event", "domain_clinical_endpoint", "domain_biomarker", "domain_companion_dx", "domain_orphan_drug", "domain_biosimilar", "domain_gene_therapy", "domain_cell_therapy", "domain_radiopharm", "domain_med_gas", "domain_surgical_inst", "domain_implant", "domain_wound_care", "domain_infection_ctrl", "domain_sterilization", "domain_cleanroom", "domain_biobank", "domain_clinical_reg", "domain_pro", "domain_telemedicine", "domain_remote_monitor", "domain_cds", "domain_sdoh", "domain_pop_health", "domain_vbc_model", "domain_bundled_pay", "domain_capitation", "domain_global_budget", "domain_prosthetic", "domain_orthotic", "domain_health_literacy", "domain_oil_grade", "domain_nat_gas", "domain_lng_terminal", "domain_pipeline", "domain_refinery", "domain_petrochem", "domain_biofuel", "domain_geothermal", "domain_tidal", "domain_wave_energy", "domain_district_heat", "domain_cogeneration", "domain_microgrid_type", "domain_vpp", "domain_demand_resp", "domain_ancillary", "domain_capacity_mkt", "domain_rec", "domain_carbon_offset", "domain_emission_factor", "domain_air_quality", "domain_water_quality", "domain_soil_contam", "domain_biodiv_offset", "domain_wetland", "domain_seed_variety", "domain_irrigation", "domain_greenhouse", "domain_aquaponics", "domain_vertical_farm", "domain_cold_chain", "domain_warehouse", "domain_cross_dock", "domain_freight_class", "domain_incoterm_detail", "domain_customs_proc", "domain_ftz", "domain_noise_pollution", "domain_light_pollution", "domain_invasive_sp", "domain_coral_reef", "domain_mangrove", "domain_univ_ranking", "domain_accreditation", "domain_student_assess", "domain_curriculum", "domain_learning_outcome", "domain_competency", "domain_micro_cred", "domain_apprentice", "domain_gig_worker", "domain_employee_benefit", "domain_comp_structure", "domain_labor_union", "domain_eeo_category", "domain_diversity_metric", "domain_gov_contract", "domain_grant_type", "domain_municipal_svc", "domain_emergency_svc", "domain_court_type", "domain_adr", "domain_trademark", "domain_patent_type", "domain_copyright", "domain_trade_secret", "domain_antitrust", "domain_consumer_prot", "domain_sanctions", "domain_export_ctrl", "domain_customs_class", "domain_internship", "domain_workplace_med", "domain_coll_bargain", "domain_product_liab", "domain_law_enforce", "domain_corrections", "domain_notary", "domain_class_action", "domain_freelance_plat", "domain_digital_badge", "domain_arb_type", "all"):
                from world_of_taxonomy.ingest.domain_lease_abstract import ingest_domain_lease_abstract
                count = await ingest_domain_lease_abstract(conn)
                print(f"  domain_lease_abstract: {count} nodes")
            if target in ("domain_api_architecture", "all"):
                from world_of_taxonomy.ingest.domain_api_architecture import ingest_domain_api_architecture
                count = await ingest_domain_api_architecture(conn)
                print(f"  domain_api_architecture: {count} nodes")
            if target in ("domain_database_type", "all"):
                from world_of_taxonomy.ingest.domain_database_type import ingest_domain_database_type
                count = await ingest_domain_database_type(conn)
                print(f"  domain_database_type: {count} nodes")
            if target in ("domain_prog_paradigm", "all"):
                from world_of_taxonomy.ingest.domain_prog_paradigm import ingest_domain_prog_paradigm
                count = await ingest_domain_prog_paradigm(conn)
                print(f"  domain_prog_paradigm: {count} nodes")
            if target in ("domain_sw_license", "all"):
                from world_of_taxonomy.ingest.domain_sw_license import ingest_domain_sw_license
                count = await ingest_domain_sw_license(conn)
                print(f"  domain_sw_license: {count} nodes")
            if target in ("domain_oss_governance", "all"):
                from world_of_taxonomy.ingest.domain_oss_governance import ingest_domain_oss_governance
                count = await ingest_domain_oss_governance(conn)
                print(f"  domain_oss_governance: {count} nodes")
            if target in ("domain_version_control", "all"):
                from world_of_taxonomy.ingest.domain_version_control import ingest_domain_version_control
                count = await ingest_domain_version_control(conn)
                print(f"  domain_version_control: {count} nodes")
            if target in ("domain_cicd_pipeline", "all"):
                from world_of_taxonomy.ingest.domain_cicd_pipeline import ingest_domain_cicd_pipeline
                count = await ingest_domain_cicd_pipeline(conn)
                print(f"  domain_cicd_pipeline: {count} nodes")
            if target in ("domain_container_orch", "all"):
                from world_of_taxonomy.ingest.domain_container_orch import ingest_domain_container_orch
                count = await ingest_domain_container_orch(conn)
                print(f"  domain_container_orch: {count} nodes")
            if target in ("domain_serverless", "all"):
                from world_of_taxonomy.ingest.domain_serverless import ingest_domain_serverless
                count = await ingest_domain_serverless(conn)
                print(f"  domain_serverless: {count} nodes")
            if target in ("domain_microservices", "all"):
                from world_of_taxonomy.ingest.domain_microservices import ingest_domain_microservices
                count = await ingest_domain_microservices(conn)
                print(f"  domain_microservices: {count} nodes")
            if target in ("domain_event_arch", "all"):
                from world_of_taxonomy.ingest.domain_event_arch import ingest_domain_event_arch
                count = await ingest_domain_event_arch(conn)
                print(f"  domain_event_arch: {count} nodes")
            if target in ("domain_data_mesh", "all"):
                from world_of_taxonomy.ingest.domain_data_mesh import ingest_domain_data_mesh
                count = await ingest_domain_data_mesh(conn)
                print(f"  domain_data_mesh: {count} nodes")
            if target in ("domain_data_lakehouse", "all"):
                from world_of_taxonomy.ingest.domain_data_lakehouse import ingest_domain_data_lakehouse
                count = await ingest_domain_data_lakehouse(conn)
                print(f"  domain_data_lakehouse: {count} nodes")
            if target in ("domain_mlops", "all"):
                from world_of_taxonomy.ingest.domain_mlops import ingest_domain_mlops
                count = await ingest_domain_mlops(conn)
                print(f"  domain_mlops: {count} nodes")
            if target in ("domain_feature_store", "all"):
                from world_of_taxonomy.ingest.domain_feature_store import ingest_domain_feature_store
                count = await ingest_domain_feature_store(conn)
                print(f"  domain_feature_store: {count} nodes")
            if target in ("domain_model_registry", "all"):
                from world_of_taxonomy.ingest.domain_model_registry import ingest_domain_model_registry
                count = await ingest_domain_model_registry(conn)
                print(f"  domain_model_registry: {count} nodes")
            if target in ("domain_data_catalog", "all"):
                from world_of_taxonomy.ingest.domain_data_catalog import ingest_domain_data_catalog
                count = await ingest_domain_data_catalog(conn)
                print(f"  domain_data_catalog: {count} nodes")
            if target in ("domain_data_quality", "all"):
                from world_of_taxonomy.ingest.domain_data_quality import ingest_domain_data_quality
                count = await ingest_domain_data_quality(conn)
                print(f"  domain_data_quality: {count} nodes")
            if target in ("domain_data_governance", "all"):
                from world_of_taxonomy.ingest.domain_data_governance import ingest_domain_data_governance
                count = await ingest_domain_data_governance(conn)
                print(f"  domain_data_governance: {count} nodes")
            if target in ("domain_data_lineage", "all"):
                from world_of_taxonomy.ingest.domain_data_lineage import ingest_domain_data_lineage
                count = await ingest_domain_data_lineage(conn)
                print(f"  domain_data_lineage: {count} nodes")
            if target in ("domain_master_data", "all"):
                from world_of_taxonomy.ingest.domain_master_data import ingest_domain_master_data
                count = await ingest_domain_master_data(conn)
                print(f"  domain_master_data: {count} nodes")
            if target in ("domain_ref_data", "all"):
                from world_of_taxonomy.ingest.domain_ref_data import ingest_domain_ref_data
                count = await ingest_domain_ref_data(conn)
                print(f"  domain_ref_data: {count} nodes")
            if target in ("domain_synthetic_data", "all"):
                from world_of_taxonomy.ingest.domain_synthetic_data import ingest_domain_synthetic_data
                count = await ingest_domain_synthetic_data(conn)
                print(f"  domain_synthetic_data: {count} nodes")
            if target in ("domain_pet", "all"):
                from world_of_taxonomy.ingest.domain_pet import ingest_domain_pet
                count = await ingest_domain_pet(conn)
                print(f"  domain_pet: {count} nodes")
            if target in ("domain_zero_trust", "all"):
                from world_of_taxonomy.ingest.domain_zero_trust import ingest_domain_zero_trust
                count = await ingest_domain_zero_trust(conn)
                print(f"  domain_zero_trust: {count} nodes")
            if target in ("domain_identity_gov", "all"):
                from world_of_taxonomy.ingest.domain_identity_gov import ingest_domain_identity_gov
                count = await ingest_domain_identity_gov(conn)
                print(f"  domain_identity_gov: {count} nodes")
            if target in ("domain_siem", "all"):
                from world_of_taxonomy.ingest.domain_siem import ingest_domain_siem
                count = await ingest_domain_siem(conn)
                print(f"  domain_siem: {count} nodes")
            if target in ("domain_soar", "all"):
                from world_of_taxonomy.ingest.domain_soar import ingest_domain_soar
                count = await ingest_domain_soar(conn)
                print(f"  domain_soar: {count} nodes")
            if target in ("domain_threat_intel", "all"):
                from world_of_taxonomy.ingest.domain_threat_intel import ingest_domain_threat_intel
                count = await ingest_domain_threat_intel(conn)
                print(f"  domain_threat_intel: {count} nodes")
            if target in ("domain_vuln_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_vuln_mgmt import ingest_domain_vuln_mgmt
                count = await ingest_domain_vuln_mgmt(conn)
                print(f"  domain_vuln_mgmt: {count} nodes")
            if target in ("domain_pentest", "all"):
                from world_of_taxonomy.ingest.domain_pentest import ingest_domain_pentest
                count = await ingest_domain_pentest(conn)
                print(f"  domain_pentest: {count} nodes")
            if target in ("domain_incident_resp", "all"):
                from world_of_taxonomy.ingest.domain_incident_resp import ingest_domain_incident_resp
                count = await ingest_domain_incident_resp(conn)
                print(f"  domain_incident_resp: {count} nodes")
            if target in ("domain_dr", "all"):
                from world_of_taxonomy.ingest.domain_dr import ingest_domain_dr
                count = await ingest_domain_dr(conn)
                print(f"  domain_dr: {count} nodes")
            if target in ("domain_backup", "all"):
                from world_of_taxonomy.ingest.domain_backup import ingest_domain_backup
                count = await ingest_domain_backup(conn)
                print(f"  domain_backup: {count} nodes")
            if target in ("domain_encryption", "all"):
                from world_of_taxonomy.ingest.domain_encryption import ingest_domain_encryption
                count = await ingest_domain_encryption(conn)
                print(f"  domain_encryption: {count} nodes")
            if target in ("domain_key_mgmt", "all"):
                from world_of_taxonomy.ingest.domain_key_mgmt import ingest_domain_key_mgmt
                count = await ingest_domain_key_mgmt(conn)
                print(f"  domain_key_mgmt: {count} nodes")
            if target in ("domain_cert_authority", "all"):
                from world_of_taxonomy.ingest.domain_cert_authority import ingest_domain_cert_authority
                count = await ingest_domain_cert_authority(conn)
                print(f"  domain_cert_authority: {count} nodes")
            if target in ("domain_pki", "all"):
                from world_of_taxonomy.ingest.domain_pki import ingest_domain_pki
                count = await ingest_domain_pki(conn)
                print(f"  domain_pki: {count} nodes")
            if target in ("domain_hsm", "all"):
                from world_of_taxonomy.ingest.domain_hsm import ingest_domain_hsm
                count = await ingest_domain_hsm(conn)
                print(f"  domain_hsm: {count} nodes")
            if target in ("domain_red_team", "all"):
                from world_of_taxonomy.ingest.domain_red_team import ingest_domain_red_team
                count = await ingest_domain_red_team(conn)
                print(f"  domain_red_team: {count} nodes")
            if target in ("domain_blue_team", "all"):
                from world_of_taxonomy.ingest.domain_blue_team import ingest_domain_blue_team
                count = await ingest_domain_blue_team(conn)
                print(f"  domain_blue_team: {count} nodes")
            if target in ("domain_purple_team", "domain_hospital_dept", "domain_nursing_spec", "domain_allied_health", "domain_lab_test", "domain_imaging", "domain_surgical_spec", "domain_anesthesia", "domain_pathology_sub", "domain_pharma_practice", "domain_formulary", "domain_drug_interaction", "domain_adverse_event", "domain_clinical_endpoint", "domain_biomarker", "domain_companion_dx", "domain_orphan_drug", "domain_biosimilar", "domain_gene_therapy", "domain_cell_therapy", "domain_radiopharm", "domain_med_gas", "domain_surgical_inst", "domain_implant", "domain_wound_care", "domain_infection_ctrl", "domain_sterilization", "domain_cleanroom", "domain_biobank", "domain_clinical_reg", "domain_pro", "domain_telemedicine", "domain_remote_monitor", "domain_cds", "domain_sdoh", "domain_pop_health", "domain_vbc_model", "domain_bundled_pay", "domain_capitation", "domain_global_budget", "domain_prosthetic", "domain_orthotic", "domain_health_literacy", "domain_oil_grade", "domain_nat_gas", "domain_lng_terminal", "domain_pipeline", "domain_refinery", "domain_petrochem", "domain_biofuel", "domain_geothermal", "domain_tidal", "domain_wave_energy", "domain_district_heat", "domain_cogeneration", "domain_microgrid_type", "domain_vpp", "domain_demand_resp", "domain_ancillary", "domain_capacity_mkt", "domain_rec", "domain_carbon_offset", "domain_emission_factor", "domain_air_quality", "domain_water_quality", "domain_soil_contam", "domain_biodiv_offset", "domain_wetland", "domain_seed_variety", "domain_irrigation", "domain_greenhouse", "domain_aquaponics", "domain_vertical_farm", "domain_cold_chain", "domain_warehouse", "domain_cross_dock", "domain_freight_class", "domain_incoterm_detail", "domain_customs_proc", "domain_ftz", "domain_noise_pollution", "domain_light_pollution", "domain_invasive_sp", "domain_coral_reef", "domain_mangrove", "domain_univ_ranking", "domain_accreditation", "domain_student_assess", "domain_curriculum", "domain_learning_outcome", "domain_competency", "domain_micro_cred", "domain_apprentice", "domain_gig_worker", "domain_employee_benefit", "domain_comp_structure", "domain_labor_union", "domain_eeo_category", "domain_diversity_metric", "domain_gov_contract", "domain_grant_type", "domain_municipal_svc", "domain_emergency_svc", "domain_court_type", "domain_adr", "domain_trademark", "domain_patent_type", "domain_copyright", "domain_trade_secret", "domain_antitrust", "domain_consumer_prot", "domain_sanctions", "domain_export_ctrl", "domain_customs_class", "domain_internship", "domain_workplace_med", "domain_coll_bargain", "domain_product_liab", "domain_law_enforce", "domain_corrections", "domain_notary", "domain_class_action", "domain_freelance_plat", "domain_digital_badge", "domain_arb_type", "all"):
                from world_of_taxonomy.ingest.domain_purple_team import ingest_domain_purple_team
                count = await ingest_domain_purple_team(conn)
                print(f"  domain_purple_team: {count} nodes")
            if target in ("domain_hospital_dept", "all"):
                from world_of_taxonomy.ingest.domain_hospital_dept import ingest_domain_hospital_dept
                count = await ingest_domain_hospital_dept(conn)
                print(f"  domain_hospital_dept: {count} nodes")
            if target in ("domain_nursing_spec", "all"):
                from world_of_taxonomy.ingest.domain_nursing_spec import ingest_domain_nursing_spec
                count = await ingest_domain_nursing_spec(conn)
                print(f"  domain_nursing_spec: {count} nodes")
            if target in ("domain_allied_health", "all"):
                from world_of_taxonomy.ingest.domain_allied_health import ingest_domain_allied_health
                count = await ingest_domain_allied_health(conn)
                print(f"  domain_allied_health: {count} nodes")
            if target in ("domain_lab_test", "all"):
                from world_of_taxonomy.ingest.domain_lab_test import ingest_domain_lab_test
                count = await ingest_domain_lab_test(conn)
                print(f"  domain_lab_test: {count} nodes")
            if target in ("domain_imaging", "all"):
                from world_of_taxonomy.ingest.domain_imaging import ingest_domain_imaging
                count = await ingest_domain_imaging(conn)
                print(f"  domain_imaging: {count} nodes")
            if target in ("domain_surgical_spec", "all"):
                from world_of_taxonomy.ingest.domain_surgical_spec import ingest_domain_surgical_spec
                count = await ingest_domain_surgical_spec(conn)
                print(f"  domain_surgical_spec: {count} nodes")
            if target in ("domain_anesthesia", "all"):
                from world_of_taxonomy.ingest.domain_anesthesia import ingest_domain_anesthesia
                count = await ingest_domain_anesthesia(conn)
                print(f"  domain_anesthesia: {count} nodes")
            if target in ("domain_pathology_sub", "all"):
                from world_of_taxonomy.ingest.domain_pathology_sub import ingest_domain_pathology_sub
                count = await ingest_domain_pathology_sub(conn)
                print(f"  domain_pathology_sub: {count} nodes")
            if target in ("domain_pharma_practice", "all"):
                from world_of_taxonomy.ingest.domain_pharma_practice import ingest_domain_pharma_practice
                count = await ingest_domain_pharma_practice(conn)
                print(f"  domain_pharma_practice: {count} nodes")
            if target in ("domain_formulary", "all"):
                from world_of_taxonomy.ingest.domain_formulary import ingest_domain_formulary
                count = await ingest_domain_formulary(conn)
                print(f"  domain_formulary: {count} nodes")
            if target in ("domain_drug_interaction", "all"):
                from world_of_taxonomy.ingest.domain_drug_interaction import ingest_domain_drug_interaction
                count = await ingest_domain_drug_interaction(conn)
                print(f"  domain_drug_interaction: {count} nodes")
            if target in ("domain_adverse_event", "all"):
                from world_of_taxonomy.ingest.domain_adverse_event import ingest_domain_adverse_event
                count = await ingest_domain_adverse_event(conn)
                print(f"  domain_adverse_event: {count} nodes")
            if target in ("domain_clinical_endpoint", "all"):
                from world_of_taxonomy.ingest.domain_clinical_endpoint import ingest_domain_clinical_endpoint
                count = await ingest_domain_clinical_endpoint(conn)
                print(f"  domain_clinical_endpoint: {count} nodes")
            if target in ("domain_biomarker", "all"):
                from world_of_taxonomy.ingest.domain_biomarker import ingest_domain_biomarker
                count = await ingest_domain_biomarker(conn)
                print(f"  domain_biomarker: {count} nodes")
            if target in ("domain_companion_dx", "all"):
                from world_of_taxonomy.ingest.domain_companion_dx import ingest_domain_companion_dx
                count = await ingest_domain_companion_dx(conn)
                print(f"  domain_companion_dx: {count} nodes")
            if target in ("domain_orphan_drug", "all"):
                from world_of_taxonomy.ingest.domain_orphan_drug import ingest_domain_orphan_drug
                count = await ingest_domain_orphan_drug(conn)
                print(f"  domain_orphan_drug: {count} nodes")
            if target in ("domain_biosimilar", "all"):
                from world_of_taxonomy.ingest.domain_biosimilar import ingest_domain_biosimilar
                count = await ingest_domain_biosimilar(conn)
                print(f"  domain_biosimilar: {count} nodes")
            if target in ("domain_gene_therapy", "all"):
                from world_of_taxonomy.ingest.domain_gene_therapy import ingest_domain_gene_therapy
                count = await ingest_domain_gene_therapy(conn)
                print(f"  domain_gene_therapy: {count} nodes")
            if target in ("domain_cell_therapy", "all"):
                from world_of_taxonomy.ingest.domain_cell_therapy import ingest_domain_cell_therapy
                count = await ingest_domain_cell_therapy(conn)
                print(f"  domain_cell_therapy: {count} nodes")
            if target in ("domain_radiopharm", "all"):
                from world_of_taxonomy.ingest.domain_radiopharm import ingest_domain_radiopharm
                count = await ingest_domain_radiopharm(conn)
                print(f"  domain_radiopharm: {count} nodes")
            if target in ("domain_med_gas", "all"):
                from world_of_taxonomy.ingest.domain_med_gas import ingest_domain_med_gas
                count = await ingest_domain_med_gas(conn)
                print(f"  domain_med_gas: {count} nodes")
            if target in ("domain_surgical_inst", "all"):
                from world_of_taxonomy.ingest.domain_surgical_inst import ingest_domain_surgical_inst
                count = await ingest_domain_surgical_inst(conn)
                print(f"  domain_surgical_inst: {count} nodes")
            if target in ("domain_implant", "all"):
                from world_of_taxonomy.ingest.domain_implant import ingest_domain_implant
                count = await ingest_domain_implant(conn)
                print(f"  domain_implant: {count} nodes")
            if target in ("domain_wound_care", "all"):
                from world_of_taxonomy.ingest.domain_wound_care import ingest_domain_wound_care
                count = await ingest_domain_wound_care(conn)
                print(f"  domain_wound_care: {count} nodes")
            if target in ("domain_infection_ctrl", "all"):
                from world_of_taxonomy.ingest.domain_infection_ctrl import ingest_domain_infection_ctrl
                count = await ingest_domain_infection_ctrl(conn)
                print(f"  domain_infection_ctrl: {count} nodes")
            if target in ("domain_sterilization", "all"):
                from world_of_taxonomy.ingest.domain_sterilization import ingest_domain_sterilization
                count = await ingest_domain_sterilization(conn)
                print(f"  domain_sterilization: {count} nodes")
            if target in ("domain_cleanroom", "all"):
                from world_of_taxonomy.ingest.domain_cleanroom import ingest_domain_cleanroom
                count = await ingest_domain_cleanroom(conn)
                print(f"  domain_cleanroom: {count} nodes")
            if target in ("domain_biobank", "all"):
                from world_of_taxonomy.ingest.domain_biobank import ingest_domain_biobank
                count = await ingest_domain_biobank(conn)
                print(f"  domain_biobank: {count} nodes")
            if target in ("domain_clinical_reg", "all"):
                from world_of_taxonomy.ingest.domain_clinical_reg import ingest_domain_clinical_reg
                count = await ingest_domain_clinical_reg(conn)
                print(f"  domain_clinical_reg: {count} nodes")
            if target in ("domain_pro", "all"):
                from world_of_taxonomy.ingest.domain_pro import ingest_domain_pro
                count = await ingest_domain_pro(conn)
                print(f"  domain_pro: {count} nodes")
            if target in ("domain_telemedicine", "all"):
                from world_of_taxonomy.ingest.domain_telemedicine import ingest_domain_telemedicine
                count = await ingest_domain_telemedicine(conn)
                print(f"  domain_telemedicine: {count} nodes")
            if target in ("domain_remote_monitor", "all"):
                from world_of_taxonomy.ingest.domain_remote_monitor import ingest_domain_remote_monitor
                count = await ingest_domain_remote_monitor(conn)
                print(f"  domain_remote_monitor: {count} nodes")
            if target in ("domain_cds", "all"):
                from world_of_taxonomy.ingest.domain_cds import ingest_domain_cds
                count = await ingest_domain_cds(conn)
                print(f"  domain_cds: {count} nodes")
            if target in ("domain_sdoh", "all"):
                from world_of_taxonomy.ingest.domain_sdoh import ingest_domain_sdoh
                count = await ingest_domain_sdoh(conn)
                print(f"  domain_sdoh: {count} nodes")
            if target in ("domain_pop_health", "all"):
                from world_of_taxonomy.ingest.domain_pop_health import ingest_domain_pop_health
                count = await ingest_domain_pop_health(conn)
                print(f"  domain_pop_health: {count} nodes")
            if target in ("domain_vbc_model", "all"):
                from world_of_taxonomy.ingest.domain_vbc_model import ingest_domain_vbc_model
                count = await ingest_domain_vbc_model(conn)
                print(f"  domain_vbc_model: {count} nodes")
            if target in ("domain_bundled_pay", "all"):
                from world_of_taxonomy.ingest.domain_bundled_pay import ingest_domain_bundled_pay
                count = await ingest_domain_bundled_pay(conn)
                print(f"  domain_bundled_pay: {count} nodes")
            if target in ("domain_capitation", "all"):
                from world_of_taxonomy.ingest.domain_capitation import ingest_domain_capitation
                count = await ingest_domain_capitation(conn)
                print(f"  domain_capitation: {count} nodes")
            if target in ("domain_global_budget", "all"):
                from world_of_taxonomy.ingest.domain_global_budget import ingest_domain_global_budget
                count = await ingest_domain_global_budget(conn)
                print(f"  domain_global_budget: {count} nodes")
            if target in ("domain_prosthetic", "all"):
                from world_of_taxonomy.ingest.domain_prosthetic import ingest_domain_prosthetic
                count = await ingest_domain_prosthetic(conn)
                print(f"  domain_prosthetic: {count} nodes")
            if target in ("domain_orthotic", "all"):
                from world_of_taxonomy.ingest.domain_orthotic import ingest_domain_orthotic
                count = await ingest_domain_orthotic(conn)
                print(f"  domain_orthotic: {count} nodes")
            if target in ("domain_health_literacy", "domain_oil_grade", "domain_nat_gas", "domain_lng_terminal", "domain_pipeline", "domain_refinery", "domain_petrochem", "domain_biofuel", "domain_geothermal", "domain_tidal", "domain_wave_energy", "domain_district_heat", "domain_cogeneration", "domain_microgrid_type", "domain_vpp", "domain_demand_resp", "domain_ancillary", "domain_capacity_mkt", "domain_rec", "domain_carbon_offset", "domain_emission_factor", "domain_air_quality", "domain_water_quality", "domain_soil_contam", "domain_biodiv_offset", "domain_wetland", "domain_seed_variety", "domain_irrigation", "domain_greenhouse", "domain_aquaponics", "domain_vertical_farm", "domain_cold_chain", "domain_warehouse", "domain_cross_dock", "domain_freight_class", "domain_incoterm_detail", "domain_customs_proc", "domain_ftz", "domain_noise_pollution", "domain_light_pollution", "domain_invasive_sp", "domain_coral_reef", "domain_mangrove", "domain_univ_ranking", "domain_accreditation", "domain_student_assess", "domain_curriculum", "domain_learning_outcome", "domain_competency", "domain_micro_cred", "domain_apprentice", "domain_gig_worker", "domain_employee_benefit", "domain_comp_structure", "domain_labor_union", "domain_eeo_category", "domain_diversity_metric", "domain_gov_contract", "domain_grant_type", "domain_municipal_svc", "domain_emergency_svc", "domain_court_type", "domain_adr", "domain_trademark", "domain_patent_type", "domain_copyright", "domain_trade_secret", "domain_antitrust", "domain_consumer_prot", "domain_sanctions", "domain_export_ctrl", "domain_customs_class", "domain_internship", "domain_workplace_med", "domain_coll_bargain", "domain_product_liab", "domain_law_enforce", "domain_corrections", "domain_notary", "domain_class_action", "domain_freelance_plat", "domain_digital_badge", "domain_arb_type", "all"):
                from world_of_taxonomy.ingest.domain_health_literacy import ingest_domain_health_literacy
                count = await ingest_domain_health_literacy(conn)
                print(f"  domain_health_literacy: {count} nodes")
            if target in ("domain_oil_grade", "all"):
                from world_of_taxonomy.ingest.domain_oil_grade import ingest_domain_oil_grade
                count = await ingest_domain_oil_grade(conn)
                print(f"  domain_oil_grade: {count} nodes")
            if target in ("domain_nat_gas", "all"):
                from world_of_taxonomy.ingest.domain_nat_gas import ingest_domain_nat_gas
                count = await ingest_domain_nat_gas(conn)
                print(f"  domain_nat_gas: {count} nodes")
            if target in ("domain_lng_terminal", "all"):
                from world_of_taxonomy.ingest.domain_lng_terminal import ingest_domain_lng_terminal
                count = await ingest_domain_lng_terminal(conn)
                print(f"  domain_lng_terminal: {count} nodes")
            if target in ("domain_pipeline", "all"):
                from world_of_taxonomy.ingest.domain_pipeline import ingest_domain_pipeline
                count = await ingest_domain_pipeline(conn)
                print(f"  domain_pipeline: {count} nodes")
            if target in ("domain_refinery", "all"):
                from world_of_taxonomy.ingest.domain_refinery import ingest_domain_refinery
                count = await ingest_domain_refinery(conn)
                print(f"  domain_refinery: {count} nodes")
            if target in ("domain_petrochem", "all"):
                from world_of_taxonomy.ingest.domain_petrochem import ingest_domain_petrochem
                count = await ingest_domain_petrochem(conn)
                print(f"  domain_petrochem: {count} nodes")
            if target in ("domain_biofuel", "all"):
                from world_of_taxonomy.ingest.domain_biofuel import ingest_domain_biofuel
                count = await ingest_domain_biofuel(conn)
                print(f"  domain_biofuel: {count} nodes")
            if target in ("domain_geothermal", "all"):
                from world_of_taxonomy.ingest.domain_geothermal import ingest_domain_geothermal
                count = await ingest_domain_geothermal(conn)
                print(f"  domain_geothermal: {count} nodes")
            if target in ("domain_tidal", "all"):
                from world_of_taxonomy.ingest.domain_tidal import ingest_domain_tidal
                count = await ingest_domain_tidal(conn)
                print(f"  domain_tidal: {count} nodes")
            if target in ("domain_wave_energy", "all"):
                from world_of_taxonomy.ingest.domain_wave_energy import ingest_domain_wave_energy
                count = await ingest_domain_wave_energy(conn)
                print(f"  domain_wave_energy: {count} nodes")
            if target in ("domain_district_heat", "all"):
                from world_of_taxonomy.ingest.domain_district_heat import ingest_domain_district_heat
                count = await ingest_domain_district_heat(conn)
                print(f"  domain_district_heat: {count} nodes")
            if target in ("domain_cogeneration", "all"):
                from world_of_taxonomy.ingest.domain_cogeneration import ingest_domain_cogeneration
                count = await ingest_domain_cogeneration(conn)
                print(f"  domain_cogeneration: {count} nodes")
            if target in ("domain_microgrid_type", "all"):
                from world_of_taxonomy.ingest.domain_microgrid_type import ingest_domain_microgrid_type
                count = await ingest_domain_microgrid_type(conn)
                print(f"  domain_microgrid_type: {count} nodes")
            if target in ("domain_vpp", "all"):
                from world_of_taxonomy.ingest.domain_vpp import ingest_domain_vpp
                count = await ingest_domain_vpp(conn)
                print(f"  domain_vpp: {count} nodes")
            if target in ("domain_demand_resp", "all"):
                from world_of_taxonomy.ingest.domain_demand_resp import ingest_domain_demand_resp
                count = await ingest_domain_demand_resp(conn)
                print(f"  domain_demand_resp: {count} nodes")
            if target in ("domain_ancillary", "all"):
                from world_of_taxonomy.ingest.domain_ancillary import ingest_domain_ancillary
                count = await ingest_domain_ancillary(conn)
                print(f"  domain_ancillary: {count} nodes")
            if target in ("domain_capacity_mkt", "all"):
                from world_of_taxonomy.ingest.domain_capacity_mkt import ingest_domain_capacity_mkt
                count = await ingest_domain_capacity_mkt(conn)
                print(f"  domain_capacity_mkt: {count} nodes")
            if target in ("domain_rec", "all"):
                from world_of_taxonomy.ingest.domain_rec import ingest_domain_rec
                count = await ingest_domain_rec(conn)
                print(f"  domain_rec: {count} nodes")
            if target in ("domain_carbon_offset", "all"):
                from world_of_taxonomy.ingest.domain_carbon_offset import ingest_domain_carbon_offset
                count = await ingest_domain_carbon_offset(conn)
                print(f"  domain_carbon_offset: {count} nodes")
            if target in ("domain_emission_factor", "all"):
                from world_of_taxonomy.ingest.domain_emission_factor import ingest_domain_emission_factor
                count = await ingest_domain_emission_factor(conn)
                print(f"  domain_emission_factor: {count} nodes")
            if target in ("domain_air_quality", "all"):
                from world_of_taxonomy.ingest.domain_air_quality import ingest_domain_air_quality
                count = await ingest_domain_air_quality(conn)
                print(f"  domain_air_quality: {count} nodes")
            if target in ("domain_water_quality", "all"):
                from world_of_taxonomy.ingest.domain_water_quality import ingest_domain_water_quality
                count = await ingest_domain_water_quality(conn)
                print(f"  domain_water_quality: {count} nodes")
            if target in ("domain_soil_contam", "all"):
                from world_of_taxonomy.ingest.domain_soil_contam import ingest_domain_soil_contam
                count = await ingest_domain_soil_contam(conn)
                print(f"  domain_soil_contam: {count} nodes")
            if target in ("domain_biodiv_offset", "all"):
                from world_of_taxonomy.ingest.domain_biodiv_offset import ingest_domain_biodiv_offset
                count = await ingest_domain_biodiv_offset(conn)
                print(f"  domain_biodiv_offset: {count} nodes")
            if target in ("domain_wetland", "all"):
                from world_of_taxonomy.ingest.domain_wetland import ingest_domain_wetland
                count = await ingest_domain_wetland(conn)
                print(f"  domain_wetland: {count} nodes")
            if target in ("domain_seed_variety", "all"):
                from world_of_taxonomy.ingest.domain_seed_variety import ingest_domain_seed_variety
                count = await ingest_domain_seed_variety(conn)
                print(f"  domain_seed_variety: {count} nodes")
            if target in ("domain_irrigation", "all"):
                from world_of_taxonomy.ingest.domain_irrigation import ingest_domain_irrigation
                count = await ingest_domain_irrigation(conn)
                print(f"  domain_irrigation: {count} nodes")
            if target in ("domain_greenhouse", "all"):
                from world_of_taxonomy.ingest.domain_greenhouse import ingest_domain_greenhouse
                count = await ingest_domain_greenhouse(conn)
                print(f"  domain_greenhouse: {count} nodes")
            if target in ("domain_aquaponics", "all"):
                from world_of_taxonomy.ingest.domain_aquaponics import ingest_domain_aquaponics
                count = await ingest_domain_aquaponics(conn)
                print(f"  domain_aquaponics: {count} nodes")
            if target in ("domain_vertical_farm", "all"):
                from world_of_taxonomy.ingest.domain_vertical_farm import ingest_domain_vertical_farm
                count = await ingest_domain_vertical_farm(conn)
                print(f"  domain_vertical_farm: {count} nodes")
            if target in ("domain_cold_chain", "all"):
                from world_of_taxonomy.ingest.domain_cold_chain import ingest_domain_cold_chain
                count = await ingest_domain_cold_chain(conn)
                print(f"  domain_cold_chain: {count} nodes")
            if target in ("domain_warehouse", "all"):
                from world_of_taxonomy.ingest.domain_warehouse import ingest_domain_warehouse
                count = await ingest_domain_warehouse(conn)
                print(f"  domain_warehouse: {count} nodes")
            if target in ("domain_cross_dock", "all"):
                from world_of_taxonomy.ingest.domain_cross_dock import ingest_domain_cross_dock
                count = await ingest_domain_cross_dock(conn)
                print(f"  domain_cross_dock: {count} nodes")
            if target in ("domain_freight_class", "all"):
                from world_of_taxonomy.ingest.domain_freight_class import ingest_domain_freight_class
                count = await ingest_domain_freight_class(conn)
                print(f"  domain_freight_class: {count} nodes")
            if target in ("domain_incoterm_detail", "all"):
                from world_of_taxonomy.ingest.domain_incoterm_detail import ingest_domain_incoterm_detail
                count = await ingest_domain_incoterm_detail(conn)
                print(f"  domain_incoterm_detail: {count} nodes")
            if target in ("domain_customs_proc", "all"):
                from world_of_taxonomy.ingest.domain_customs_proc import ingest_domain_customs_proc
                count = await ingest_domain_customs_proc(conn)
                print(f"  domain_customs_proc: {count} nodes")
            if target in ("domain_ftz", "all"):
                from world_of_taxonomy.ingest.domain_ftz import ingest_domain_ftz
                count = await ingest_domain_ftz(conn)
                print(f"  domain_ftz: {count} nodes")
            if target in ("domain_noise_pollution", "all"):
                from world_of_taxonomy.ingest.domain_noise_pollution import ingest_domain_noise_pollution
                count = await ingest_domain_noise_pollution(conn)
                print(f"  domain_noise_pollution: {count} nodes")
            if target in ("domain_light_pollution", "all"):
                from world_of_taxonomy.ingest.domain_light_pollution import ingest_domain_light_pollution
                count = await ingest_domain_light_pollution(conn)
                print(f"  domain_light_pollution: {count} nodes")
            if target in ("domain_invasive_sp", "all"):
                from world_of_taxonomy.ingest.domain_invasive_sp import ingest_domain_invasive_sp
                count = await ingest_domain_invasive_sp(conn)
                print(f"  domain_invasive_sp: {count} nodes")
            if target in ("domain_coral_reef", "all"):
                from world_of_taxonomy.ingest.domain_coral_reef import ingest_domain_coral_reef
                count = await ingest_domain_coral_reef(conn)
                print(f"  domain_coral_reef: {count} nodes")
            if target in ("domain_mangrove", "domain_univ_ranking", "domain_accreditation", "domain_student_assess", "domain_curriculum", "domain_learning_outcome", "domain_competency", "domain_micro_cred", "domain_apprentice", "domain_gig_worker", "domain_employee_benefit", "domain_comp_structure", "domain_labor_union", "domain_eeo_category", "domain_diversity_metric", "domain_gov_contract", "domain_grant_type", "domain_municipal_svc", "domain_emergency_svc", "domain_court_type", "domain_adr", "domain_trademark", "domain_patent_type", "domain_copyright", "domain_trade_secret", "domain_antitrust", "domain_consumer_prot", "domain_sanctions", "domain_export_ctrl", "domain_customs_class", "domain_internship", "domain_workplace_med", "domain_coll_bargain", "domain_product_liab", "domain_law_enforce", "domain_corrections", "domain_notary", "domain_class_action", "domain_freelance_plat", "domain_digital_badge", "domain_arb_type", "all"):
                from world_of_taxonomy.ingest.domain_mangrove import ingest_domain_mangrove
                count = await ingest_domain_mangrove(conn)
                print(f"  domain_mangrove: {count} nodes")
            if target in ("domain_univ_ranking", "all"):
                from world_of_taxonomy.ingest.domain_univ_ranking import ingest_domain_univ_ranking
                count = await ingest_domain_univ_ranking(conn)
                print(f"  domain_univ_ranking: {count} nodes")
            if target in ("domain_accreditation", "all"):
                from world_of_taxonomy.ingest.domain_accreditation import ingest_domain_accreditation
                count = await ingest_domain_accreditation(conn)
                print(f"  domain_accreditation: {count} nodes")
            if target in ("domain_student_assess", "all"):
                from world_of_taxonomy.ingest.domain_student_assess import ingest_domain_student_assess
                count = await ingest_domain_student_assess(conn)
                print(f"  domain_student_assess: {count} nodes")
            if target in ("domain_curriculum", "all"):
                from world_of_taxonomy.ingest.domain_curriculum import ingest_domain_curriculum
                count = await ingest_domain_curriculum(conn)
                print(f"  domain_curriculum: {count} nodes")
            if target in ("domain_learning_outcome", "all"):
                from world_of_taxonomy.ingest.domain_learning_outcome import ingest_domain_learning_outcome
                count = await ingest_domain_learning_outcome(conn)
                print(f"  domain_learning_outcome: {count} nodes")
            if target in ("domain_competency", "all"):
                from world_of_taxonomy.ingest.domain_competency import ingest_domain_competency
                count = await ingest_domain_competency(conn)
                print(f"  domain_competency: {count} nodes")
            if target in ("domain_micro_cred", "all"):
                from world_of_taxonomy.ingest.domain_micro_cred import ingest_domain_micro_cred
                count = await ingest_domain_micro_cred(conn)
                print(f"  domain_micro_cred: {count} nodes")
            if target in ("domain_apprentice", "all"):
                from world_of_taxonomy.ingest.domain_apprentice import ingest_domain_apprentice
                count = await ingest_domain_apprentice(conn)
                print(f"  domain_apprentice: {count} nodes")
            if target in ("domain_gig_worker", "all"):
                from world_of_taxonomy.ingest.domain_gig_worker import ingest_domain_gig_worker
                count = await ingest_domain_gig_worker(conn)
                print(f"  domain_gig_worker: {count} nodes")
            if target in ("domain_employee_benefit", "all"):
                from world_of_taxonomy.ingest.domain_employee_benefit import ingest_domain_employee_benefit
                count = await ingest_domain_employee_benefit(conn)
                print(f"  domain_employee_benefit: {count} nodes")
            if target in ("domain_comp_structure", "all"):
                from world_of_taxonomy.ingest.domain_comp_structure import ingest_domain_comp_structure
                count = await ingest_domain_comp_structure(conn)
                print(f"  domain_comp_structure: {count} nodes")
            if target in ("domain_labor_union", "all"):
                from world_of_taxonomy.ingest.domain_labor_union import ingest_domain_labor_union
                count = await ingest_domain_labor_union(conn)
                print(f"  domain_labor_union: {count} nodes")
            if target in ("domain_eeo_category", "all"):
                from world_of_taxonomy.ingest.domain_eeo_category import ingest_domain_eeo_category
                count = await ingest_domain_eeo_category(conn)
                print(f"  domain_eeo_category: {count} nodes")
            if target in ("domain_diversity_metric", "all"):
                from world_of_taxonomy.ingest.domain_diversity_metric import ingest_domain_diversity_metric
                count = await ingest_domain_diversity_metric(conn)
                print(f"  domain_diversity_metric: {count} nodes")
            if target in ("domain_gov_contract", "all"):
                from world_of_taxonomy.ingest.domain_gov_contract import ingest_domain_gov_contract
                count = await ingest_domain_gov_contract(conn)
                print(f"  domain_gov_contract: {count} nodes")
            if target in ("domain_grant_type", "all"):
                from world_of_taxonomy.ingest.domain_grant_type import ingest_domain_grant_type
                count = await ingest_domain_grant_type(conn)
                print(f"  domain_grant_type: {count} nodes")
            if target in ("domain_municipal_svc", "all"):
                from world_of_taxonomy.ingest.domain_municipal_svc import ingest_domain_municipal_svc
                count = await ingest_domain_municipal_svc(conn)
                print(f"  domain_municipal_svc: {count} nodes")
            if target in ("domain_emergency_svc", "all"):
                from world_of_taxonomy.ingest.domain_emergency_svc import ingest_domain_emergency_svc
                count = await ingest_domain_emergency_svc(conn)
                print(f"  domain_emergency_svc: {count} nodes")
            if target in ("domain_court_type", "all"):
                from world_of_taxonomy.ingest.domain_court_type import ingest_domain_court_type
                count = await ingest_domain_court_type(conn)
                print(f"  domain_court_type: {count} nodes")
            if target in ("domain_adr", "all"):
                from world_of_taxonomy.ingest.domain_adr import ingest_domain_adr
                count = await ingest_domain_adr(conn)
                print(f"  domain_adr: {count} nodes")
            if target in ("domain_trademark", "all"):
                from world_of_taxonomy.ingest.domain_trademark import ingest_domain_trademark
                count = await ingest_domain_trademark(conn)
                print(f"  domain_trademark: {count} nodes")
            if target in ("domain_patent_type", "all"):
                from world_of_taxonomy.ingest.domain_patent_type import ingest_domain_patent_type
                count = await ingest_domain_patent_type(conn)
                print(f"  domain_patent_type: {count} nodes")
            if target in ("domain_copyright", "all"):
                from world_of_taxonomy.ingest.domain_copyright import ingest_domain_copyright
                count = await ingest_domain_copyright(conn)
                print(f"  domain_copyright: {count} nodes")
            if target in ("domain_trade_secret", "all"):
                from world_of_taxonomy.ingest.domain_trade_secret import ingest_domain_trade_secret
                count = await ingest_domain_trade_secret(conn)
                print(f"  domain_trade_secret: {count} nodes")
            if target in ("domain_antitrust", "all"):
                from world_of_taxonomy.ingest.domain_antitrust import ingest_domain_antitrust
                count = await ingest_domain_antitrust(conn)
                print(f"  domain_antitrust: {count} nodes")
            if target in ("domain_consumer_prot", "all"):
                from world_of_taxonomy.ingest.domain_consumer_prot import ingest_domain_consumer_prot
                count = await ingest_domain_consumer_prot(conn)
                print(f"  domain_consumer_prot: {count} nodes")
            if target in ("domain_sanctions", "all"):
                from world_of_taxonomy.ingest.domain_sanctions import ingest_domain_sanctions
                count = await ingest_domain_sanctions(conn)
                print(f"  domain_sanctions: {count} nodes")
            if target in ("domain_export_ctrl", "all"):
                from world_of_taxonomy.ingest.domain_export_ctrl import ingest_domain_export_ctrl
                count = await ingest_domain_export_ctrl(conn)
                print(f"  domain_export_ctrl: {count} nodes")
            if target in ("domain_customs_class", "all"):
                from world_of_taxonomy.ingest.domain_customs_class import ingest_domain_customs_class
                count = await ingest_domain_customs_class(conn)
                print(f"  domain_customs_class: {count} nodes")
            if target in ("domain_internship", "all"):
                from world_of_taxonomy.ingest.domain_internship import ingest_domain_internship
                count = await ingest_domain_internship(conn)
                print(f"  domain_internship: {count} nodes")
            if target in ("domain_workplace_med", "all"):
                from world_of_taxonomy.ingest.domain_workplace_med import ingest_domain_workplace_med
                count = await ingest_domain_workplace_med(conn)
                print(f"  domain_workplace_med: {count} nodes")
            if target in ("domain_coll_bargain", "all"):
                from world_of_taxonomy.ingest.domain_coll_bargain import ingest_domain_coll_bargain
                count = await ingest_domain_coll_bargain(conn)
                print(f"  domain_coll_bargain: {count} nodes")
            if target in ("domain_product_liab", "all"):
                from world_of_taxonomy.ingest.domain_product_liab import ingest_domain_product_liab
                count = await ingest_domain_product_liab(conn)
                print(f"  domain_product_liab: {count} nodes")
            if target in ("domain_law_enforce", "all"):
                from world_of_taxonomy.ingest.domain_law_enforce import ingest_domain_law_enforce
                count = await ingest_domain_law_enforce(conn)
                print(f"  domain_law_enforce: {count} nodes")
            if target in ("domain_corrections", "all"):
                from world_of_taxonomy.ingest.domain_corrections import ingest_domain_corrections
                count = await ingest_domain_corrections(conn)
                print(f"  domain_corrections: {count} nodes")
            if target in ("domain_notary", "all"):
                from world_of_taxonomy.ingest.domain_notary import ingest_domain_notary
                count = await ingest_domain_notary(conn)
                print(f"  domain_notary: {count} nodes")
            if target in ("domain_class_action", "all"):
                from world_of_taxonomy.ingest.domain_class_action import ingest_domain_class_action
                count = await ingest_domain_class_action(conn)
                print(f"  domain_class_action: {count} nodes")
            if target in ("domain_freelance_plat", "all"):
                from world_of_taxonomy.ingest.domain_freelance_plat import ingest_domain_freelance_plat
                count = await ingest_domain_freelance_plat(conn)
                print(f"  domain_freelance_plat: {count} nodes")
            if target in ("domain_digital_badge", "all"):
                from world_of_taxonomy.ingest.domain_digital_badge import ingest_domain_digital_badge
                count = await ingest_domain_digital_badge(conn)
                print(f"  domain_digital_badge: {count} nodes")
            if target in ("domain_arb_type", "all"):
                from world_of_taxonomy.ingest.domain_arb_type import ingest_domain_arb_type
                count = await ingest_domain_arb_type(conn)
                print(f"  domain_arb_type: {count} nodes")
            if target in ("icd10_ca", "all"):
                from world_of_taxonomy.ingest.icd10_ca import ingest_icd10_ca
                count = await ingest_icd10_ca(conn)
                print(f"  icd10_ca: {count} nodes")
            if target in ("snomed_ct", "all"):
                from world_of_taxonomy.ingest.snomed_ct import ingest_snomed_ct
                count = await ingest_snomed_ct(conn)
                print(f"  snomed_ct: {count} nodes")
            if target in ("cpt_ama", "all"):
                from world_of_taxonomy.ingest.cpt_ama import ingest_cpt_ama
                count = await ingest_cpt_ama(conn)
                print(f"  cpt_ama: {count} nodes")
            if target in ("g_drg", "all"):
                from world_of_taxonomy.ingest.g_drg import ingest_g_drg
                count = await ingest_g_drg(conn)
                print(f"  g_drg: {count} nodes")
            if target in ("rxnorm", "all"):
                from world_of_taxonomy.ingest.rxnorm import ingest_rxnorm
                count = await ingest_rxnorm(conn)
                print(f"  rxnorm: {count} nodes")
            if target in ("ndc_fda", "all"):
                from world_of_taxonomy.ingest.ndc_fda import ingest_ndc_fda
                count = await ingest_ndc_fda(conn)
                print(f"  ndc_fda: {count} nodes")
            if target in ("dsm5", "all"):
                from world_of_taxonomy.ingest.dsm5 import ingest_dsm5
                count = await ingest_dsm5(conn)
                print(f"  dsm5: {count} nodes")
            if target in ("icpc2", "all"):
                from world_of_taxonomy.ingest.icpc2 import ingest_icpc2
                count = await ingest_icpc2(conn)
                print(f"  icpc2: {count} nodes")
            if target in ("ichi_who", "all"):
                from world_of_taxonomy.ingest.ichi_who import ingest_ichi_who
                count = await ingest_ichi_who(conn)
                print(f"  ichi_who: {count} nodes")
            if target in ("gbd_cause", "all"):
                from world_of_taxonomy.ingest.gbd_cause import ingest_gbd_cause
                count = await ingest_gbd_cause(conn)
                print(f"  gbd_cause: {count} nodes")
            if target in ("gmdn", "all"):
                from world_of_taxonomy.ingest.gmdn import ingest_gmdn
                count = await ingest_gmdn(conn)
                print(f"  gmdn: {count} nodes")
            if target in ("who_essential_med", "all"):
                from world_of_taxonomy.ingest.who_essential_med import ingest_who_essential_med
                count = await ingest_who_essential_med(conn)
                print(f"  who_essential_med: {count} nodes")
            if target in ("cdc_vaccine", "all"):
                from world_of_taxonomy.ingest.cdc_vaccine import ingest_cdc_vaccine
                count = await ingest_cdc_vaccine(conn)
                print(f"  cdc_vaccine: {count} nodes")
            if target in ("nci_thesaurus", "all"):
                from world_of_taxonomy.ingest.nci_thesaurus import ingest_nci_thesaurus
                count = await ingest_nci_thesaurus(conn)
                print(f"  nci_thesaurus: {count} nodes")
            if target in ("ctcae", "all"):
                from world_of_taxonomy.ingest.ctcae import ingest_ctcae
                count = await ingest_ctcae(conn)
                print(f"  ctcae: {count} nodes")
            if target in ("ifrs", "all"):
                from world_of_taxonomy.ingest.ifrs import ingest_ifrs
                count = await ingest_ifrs(conn)
                print(f"  ifrs: {count} nodes")
            if target in ("bloomberg_bics", "all"):
                from world_of_taxonomy.ingest.bloomberg_bics import ingest_bloomberg_bics
                count = await ingest_bloomberg_bics(conn)
                print(f"  bloomberg_bics: {count} nodes")
            if target in ("refinitiv_trbc", "all"):
                from world_of_taxonomy.ingest.refinitiv_trbc import ingest_refinitiv_trbc
                count = await ingest_refinitiv_trbc(conn)
                print(f"  refinitiv_trbc: {count} nodes")
            if target in ("sfia_v8", "all"):
                from world_of_taxonomy.ingest.sfia_v8 import ingest_sfia_v8
                count = await ingest_sfia_v8(conn)
                print(f"  sfia_v8: {count} nodes")
            if target in ("digcomp_22", "all"):
                from world_of_taxonomy.ingest.digcomp_22 import ingest_digcomp_22
                count = await ingest_digcomp_22(conn)
                print(f"  digcomp_22: {count} nodes")
            if target in ("ecf_v4", "all"):
                from world_of_taxonomy.ingest.ecf_v4 import ingest_ecf_v4
                count = await ingest_ecf_v4(conn)
                print(f"  ecf_v4: {count} nodes")
            if target in ("scopus_asjc", "all"):
                from world_of_taxonomy.ingest.scopus_asjc import ingest_scopus_asjc
                count = await ingest_scopus_asjc(conn)
                print(f"  scopus_asjc: {count} nodes")
            if target in ("wos_categories", "all"):
                from world_of_taxonomy.ingest.wos_categories import ingest_wos_categories
                count = await ingest_wos_categories(conn)
                print(f"  wos_categories: {count} nodes")
            if target in ("eqf", "all"):
                from world_of_taxonomy.ingest.eqf import ingest_eqf
                count = await ingest_eqf(conn)
                print(f"  eqf: {count} nodes")
            if target in ("aqf", "all"):
                from world_of_taxonomy.ingest.aqf import ingest_aqf
                count = await ingest_aqf(conn)
                print(f"  aqf: {count} nodes")
            if target in ("onet_knowledge", "all"):
                from world_of_taxonomy.ingest.onet_knowledge import ingest_onet_knowledge
                count = await ingest_onet_knowledge(conn)
                print(f"  onet_knowledge: {count} nodes")
            if target in ("onet_abilities", "all"):
                from world_of_taxonomy.ingest.onet_abilities import ingest_onet_abilities
                count = await ingest_onet_abilities(conn)
                print(f"  onet_abilities: {count} nodes")
            if target in ("iucn_red_list", "all"):
                from world_of_taxonomy.ingest.iucn_red_list import ingest_iucn_red_list
                count = await ingest_iucn_red_list(conn)
                print(f"  iucn_red_list: {count} nodes")
            if target in ("cites", "all"):
                from world_of_taxonomy.ingest.cites import ingest_cites
                count = await ingest_cites(conn)
                print(f"  cites: {count} nodes")
            if target in ("eu_waste_cat", "all"):
                from world_of_taxonomy.ingest.eu_waste_cat import ingest_eu_waste_cat
                count = await ingest_eu_waste_cat(conn)
                print(f"  eu_waste_cat: {count} nodes")
            if target in ("stockholm_pops", "all"):
                from world_of_taxonomy.ingest.stockholm_pops import ingest_stockholm_pops
                count = await ingest_stockholm_pops(conn)
                print(f"  stockholm_pops: {count} nodes")
            if target in ("rotterdam_pic", "all"):
                from world_of_taxonomy.ingest.rotterdam_pic import ingest_rotterdam_pic
                count = await ingest_rotterdam_pic(conn)
                print(f"  rotterdam_pic: {count} nodes")
            if target in ("minamata", "all"):
                from world_of_taxonomy.ingest.minamata import ingest_minamata
                count = await ingest_minamata(conn)
                print(f"  minamata: {count} nodes")
            if target in ("iata_aircraft", "all"):
                from world_of_taxonomy.ingest.iata_aircraft import ingest_iata_aircraft
                count = await ingest_iata_aircraft(conn)
                print(f"  iata_aircraft: {count} nodes")
            if target in ("imo_vessel", "all"):
                from world_of_taxonomy.ingest.imo_vessel import ingest_imo_vessel
                count = await ingest_imo_vessel(conn)
                print(f"  imo_vessel: {count} nodes")
            if target in ("ietf_rfc", "all"):
                from world_of_taxonomy.ingest.ietf_rfc import ingest_ietf_rfc
                count = await ingest_ietf_rfc(conn)
                print(f"  ietf_rfc: {count} nodes")
            if target in ("w3c_standards", "all"):
                from world_of_taxonomy.ingest.w3c_standards import ingest_w3c_standards
                count = await ingest_w3c_standards(conn)
                print(f"  w3c_standards: {count} nodes")
            if target in ("ieee_standards", "all"):
                from world_of_taxonomy.ingest.ieee_standards import ingest_ieee_standards
                count = await ingest_ieee_standards(conn)
                print(f"  ieee_standards: {count} nodes")
            if target in ("usb_classes", "all"):
                from world_of_taxonomy.ingest.usb_classes import ingest_usb_classes
                count = await ingest_usb_classes(conn)
                print(f"  usb_classes: {count} nodes")
            if target in ("bluetooth_profiles", "all"):
                from world_of_taxonomy.ingest.bluetooth_profiles import ingest_bluetooth_profiles
                count = await ingest_bluetooth_profiles(conn)
                print(f"  bluetooth_profiles: {count} nodes")
            if target in ("esco_qualifications", "all"):
                from world_of_taxonomy.ingest.esco_qualifications import ingest_esco_qualifications
                count = await ingest_esco_qualifications(conn)
                print(f"  esco_qualifications: {count} nodes")
            if target in ("worldskills", "all"):
                from world_of_taxonomy.ingest.worldskills import ingest_worldskills
                count = await ingest_worldskills(conn)
                print(f"  worldskills: {count} nodes")
            if target in ("onet_work_activities", "all"):
                from world_of_taxonomy.ingest.onet_work_activities import ingest_onet_work_activities
                count = await ingest_onet_work_activities(conn)
                print(f"  onet_work_activities: {count} nodes")
            if target in ("onet_work_context", "all"):
                from world_of_taxonomy.ingest.onet_work_context import ingest_onet_work_context
                count = await ingest_onet_work_context(conn)
                print(f"  onet_work_context: {count} nodes")
            if target in ("onet_interests", "all"):
                from world_of_taxonomy.ingest.onet_interests import ingest_onet_interests
                count = await ingest_onet_interests(conn)
                print(f"  onet_interests: {count} nodes")
            if target in ("onet_work_values", "all"):
                from world_of_taxonomy.ingest.onet_work_values import ingest_onet_work_values
                count = await ingest_onet_work_values(conn)
                print(f"  onet_work_values: {count} nodes")
            if target in ("linkedin_skills", "all"):
                from world_of_taxonomy.ingest.linkedin_skills import ingest_linkedin_skills
                count = await ingest_linkedin_skills(conn)
                print(f"  linkedin_skills: {count} nodes")
            if target in ("nqf_uk", "all"):
                from world_of_taxonomy.ingest.nqf_uk import ingest_nqf_uk
                count = await ingest_nqf_uk(conn)
                print(f"  nqf_uk: {count} nodes")
            if target in ("naics_2017", "all"):
                from world_of_taxonomy.ingest.naics_2017 import ingest_naics_2017
                count = await ingest_naics_2017(conn)
                print(f"  naics_2017: {count} nodes")
            if target in ("naics_2012", "all"):
                from world_of_taxonomy.ingest.naics_2012 import ingest_naics_2012
                count = await ingest_naics_2012(conn)
                print(f"  naics_2012: {count} nodes")
            if target in ("isic_rev3", "all"):
                from world_of_taxonomy.ingest.isic_rev3 import ingest_isic_rev3
                count = await ingest_isic_rev3(conn)
                print(f"  isic_rev3: {count} nodes")
            if target in ("eu_taric", "all"):
                from world_of_taxonomy.ingest.eu_taric import ingest_eu_taric
                count = await ingest_eu_taric(conn)
                print(f"  eu_taric: {count} nodes")
            if target in ("uk_trade_tariff", "all"):
                from world_of_taxonomy.ingest.uk_trade_tariff import ingest_uk_trade_tariff
                count = await ingest_uk_trade_tariff(conn)
                print(f"  uk_trade_tariff: {count} nodes")
            if target in ("asean_tariff", "all"):
                from world_of_taxonomy.ingest.asean_tariff import ingest_asean_tariff
                count = await ingest_asean_tariff(conn)
                print(f"  asean_tariff: {count} nodes")
            if target in ("mercosur_tariff", "all"):
                from world_of_taxonomy.ingest.mercosur_tariff import ingest_mercosur_tariff
                count = await ingest_mercosur_tariff(conn)
                print(f"  mercosur_tariff: {count} nodes")
            if target in ("afcfta_tariff", "all"):
                from world_of_taxonomy.ingest.afcfta_tariff import ingest_afcfta_tariff
                count = await ingest_afcfta_tariff(conn)
                print(f"  afcfta_tariff: {count} nodes")
            if target in ("gcc_tariff", "all"):
                from world_of_taxonomy.ingest.gcc_tariff import ingest_gcc_tariff
                count = await ingest_gcc_tariff(conn)
                print(f"  gcc_tariff: {count} nodes")
            if target in ("ecowas_cet", "all"):
                from world_of_taxonomy.ingest.ecowas_cet import ingest_ecowas_cet
                count = await ingest_ecowas_cet(conn)
                print(f"  ecowas_cet: {count} nodes")
            if target in ("dewey_decimal", "all"):
                from world_of_taxonomy.ingest.dewey_decimal import ingest_dewey_decimal
                count = await ingest_dewey_decimal(conn)
                print(f"  dewey_decimal: {count} nodes")
            if target in ("udc", "all"):
                from world_of_taxonomy.ingest.udc import ingest_udc
                count = await ingest_udc(conn)
                print(f"  udc: {count} nodes")
            if target in ("lcsh", "all"):
                from world_of_taxonomy.ingest.lcsh import ingest_lcsh
                count = await ingest_lcsh(conn)
                print(f"  lcsh: {count} nodes")
            if target in ("era_for", "all"):
                from world_of_taxonomy.ingest.era_for import ingest_era_for
                count = await ingest_era_for(conn)
                print(f"  era_for: {count} nodes")
            if target in ("unesco_thesaurus", "all"):
                from world_of_taxonomy.ingest.unesco_thesaurus import ingest_unesco_thesaurus
                count = await ingest_unesco_thesaurus(conn)
                print(f"  unesco_thesaurus: {count} nodes")
            if target in ("getty_aat", "all"):
                from world_of_taxonomy.ingest.getty_aat import ingest_getty_aat
                count = await ingest_getty_aat(conn)
                print(f"  getty_aat: {count} nodes")
            if target in ("aacsb", "all"):
                from world_of_taxonomy.ingest.aacsb import ingest_aacsb
                count = await ingest_aacsb(conn)
                print(f"  aacsb: {count} nodes")
            if target in ("abet", "all"):
                from world_of_taxonomy.ingest.abet import ingest_abet
                count = await ingest_abet(conn)
                print(f"  abet: {count} nodes")
            if target in ("epa_rcra_waste", "all"):
                from world_of_taxonomy.ingest.epa_rcra_waste import ingest_epa_rcra_waste
                count = await ingest_epa_rcra_waste(conn)
                print(f"  epa_rcra_waste: {count} nodes")
            if target in ("ramsar", "all"):
                from world_of_taxonomy.ingest.ramsar import ingest_ramsar
                count = await ingest_ramsar(conn)
                print(f"  ramsar: {count} nodes")
            if target in ("cbd_targets", "all"):
                from world_of_taxonomy.ingest.cbd_targets import ingest_cbd_targets
                count = await ingest_cbd_targets(conn)
                print(f"  cbd_targets: {count} nodes")
            if target in ("unep_chemicals", "all"):
                from world_of_taxonomy.ingest.unep_chemicals import ingest_unep_chemicals
                count = await ingest_unep_chemicals(conn)
                print(f"  unep_chemicals: {count} nodes")
            if target in ("nato_codification", "all"):
                from world_of_taxonomy.ingest.nato_codification import ingest_nato_codification
                count = await ingest_nato_codification(conn)
                print(f"  nato_codification: {count} nodes")
            if target in ("faa_aircraft_cat", "all"):
                from world_of_taxonomy.ingest.faa_aircraft_cat import ingest_faa_aircraft_cat
                count = await ingest_faa_aircraft_cat(conn)
                print(f"  faa_aircraft_cat: {count} nodes")
            if target in ("uic_railway", "all"):
                from world_of_taxonomy.ingest.uic_railway import ingest_uic_railway
                count = await ingest_uic_railway(conn)
                print(f"  uic_railway: {count} nodes")
            if target in ("icao_airport", "all"):
                from world_of_taxonomy.ingest.icao_airport import ingest_icao_airport
                count = await ingest_icao_airport(conn)
                print(f"  icao_airport: {count} nodes")
            if target in ("dod_mil_std", "all"):
                from world_of_taxonomy.ingest.dod_mil_std import ingest_dod_mil_std
                count = await ingest_dod_mil_std(conn)
                print(f"  dod_mil_std: {count} nodes")
            if target in ("itu_t", "all"):
                from world_of_taxonomy.ingest.itu_t import ingest_itu_t
                count = await ingest_itu_t(conn)
                print(f"  itu_t: {count} nodes")
            if target in ("tgpp_specs", "all"):
                from world_of_taxonomy.ingest.tgpp_specs import ingest_tgpp_specs
                count = await ingest_tgpp_specs(conn)
                print(f"  tgpp_specs: {count} nodes")
            if target in ("pci_sig", "all"):
                from world_of_taxonomy.ingest.pci_sig import ingest_pci_sig
                count = await ingest_pci_sig(conn)
                print(f"  pci_sig: {count} nodes")
            if target in ("jedec", "all"):
                from world_of_taxonomy.ingest.jedec import ingest_jedec
                count = await ingest_jedec(conn)
                print(f"  jedec: {count} nodes")
            if target in ("semi_standards", "all"):
                from world_of_taxonomy.ingest.semi_standards import ingest_semi_standards
                count = await ingest_semi_standards(conn)
                print(f"  semi_standards: {count} nodes")
            if target in ("vesa_standards", "all"):
                from world_of_taxonomy.ingest.vesa_standards import ingest_vesa_standards
                count = await ingest_vesa_standards(conn)
                print(f"  vesa_standards: {count} nodes")
            if target in ("hcpcs_l3", "all"):
                from world_of_taxonomy.ingest.hcpcs_l3 import ingest_hcpcs_l3
                count = await ingest_hcpcs_l3(conn)
                print(f"  hcpcs_l3: {count} nodes")
            if target in ("icn_nursing", "all"):
                from world_of_taxonomy.ingest.icn_nursing import ingest_icn_nursing
                count = await ingest_icn_nursing(conn)
                print(f"  icn_nursing: {count} nodes")
            if target in ("edqm_dosage", "all"):
                from world_of_taxonomy.ingest.edqm_dosage import ingest_edqm_dosage
                count = await ingest_edqm_dosage(conn)
                print(f"  edqm_dosage: {count} nodes")
            if target in ("omim", "all"):
                from world_of_taxonomy.ingest.omim import ingest_omim
                count = await ingest_omim(conn)
                print(f"  omim: {count} nodes")
            if target in ("orphanet", "all"):
                from world_of_taxonomy.ingest.orphanet import ingest_orphanet
                count = await ingest_orphanet(conn)
                print(f"  orphanet: {count} nodes")
            if target in ("ftse_icb_detail", "all"):
                from world_of_taxonomy.ingest.ftse_icb_detail import ingest_ftse_icb_detail
                count = await ingest_ftse_icb_detail(conn)
                print(f"  ftse_icb_detail: {count} nodes")
            if target in ("cbd_aichi", "all"):
                from world_of_taxonomy.ingest.cbd_aichi import ingest_cbd_aichi
                count = await ingest_cbd_aichi(conn)
                print(f"  cbd_aichi: {count} nodes")
            if target in ("un_ammo", "all"):
                from world_of_taxonomy.ingest.un_ammo import ingest_un_ammo
                count = await ingest_un_ammo(conn)
                print(f"  un_ammo: {count} nodes")
            if target in ("stanag", "all"):
                from world_of_taxonomy.ingest.stanag import ingest_stanag
                count = await ingest_stanag(conn)
                print(f"  stanag: {count} nodes")
            if target in ("anzsrc_seo", "all"):
                from world_of_taxonomy.ingest.anzsrc_seo import ingest_anzsrc_seo
                count = await ingest_anzsrc_seo(conn)
                print(f"  anzsrc_seo: {count} nodes")
            if target in ("onet_work_styles", "all"):
                from world_of_taxonomy.ingest.onet_work_styles import ingest_onet_work_styles
                count = await ingest_onet_work_styles(conn)
                print(f"  onet_work_styles: {count} nodes")
            if target in ("ibc_2021", "all"):
                from world_of_taxonomy.ingest.ibc_2021 import ingest_ibc_2021
                count = await ingest_ibc_2021(conn)
                print(f"  ibc_2021: {count} nodes")
            if target in ("nfpa_codes", "all"):
                from world_of_taxonomy.ingest.nfpa_codes import ingest_nfpa_codes
                count = await ingest_nfpa_codes(conn)
                print(f"  nfpa_codes: {count} nodes")
            if target in ("nuts_candidate", "all"):
                from world_of_taxonomy.ingest.nuts_candidate import ingest_nuts_candidate
                count = await ingest_nuts_candidate(conn)
                print(f"  nuts_candidate: {count} nodes")
            if target in ("opec_basket", "all"):
                from world_of_taxonomy.ingest.opec_basket import ingest_opec_basket
                count = await ingest_opec_basket(conn)
                print(f"  opec_basket: {count} nodes")
            if target in ("lme_metals", "all"):
                from world_of_taxonomy.ingest.lme_metals import ingest_lme_metals
                count = await ingest_lme_metals(conn)
                print(f"  lme_metals: {count} nodes")
            if target in ("nmfc", "all"):
                from world_of_taxonomy.ingest.nmfc import ingest_nmfc
                count = await ingest_nmfc(conn)
                print(f"  nmfc: {count} nodes")
            if target in ("stcc", "all"):
                from world_of_taxonomy.ingest.stcc import ingest_stcc
                count = await ingest_stcc(conn)
                print(f"  stcc: {count} nodes")
            if target in ("naic_lines", "all"):
                from world_of_taxonomy.ingest.naic_lines import ingest_naic_lines
                count = await ingest_naic_lines(conn)
                print(f"  naic_lines: {count} nodes")
            if target in ("ngss", "all"):
                from world_of_taxonomy.ingest.ngss import ingest_ngss
                count = await ingest_ngss(conn)
                print(f"  ngss: {count} nodes")
            if target in ("ccss", "all"):
                from world_of_taxonomy.ingest.ccss import ingest_ccss
                count = await ingest_ccss(conn)
                print(f"  ccss: {count} nodes")
            if target in ("bloom_taxonomy", "all"):
                from world_of_taxonomy.ingest.bloom_taxonomy import ingest_bloom_taxonomy
                count = await ingest_bloom_taxonomy(conn)
                print(f"  bloom_taxonomy: {count} nodes")
            if target in ("gdpr_basis", "all"):
                from world_of_taxonomy.ingest.gdpr_basis import ingest_gdpr_basis
                count = await ingest_gdpr_basis(conn)
                print(f"  gdpr_basis: {count} nodes")
            if target in ("data_retention", "all"):
                from world_of_taxonomy.ingest.data_retention import ingest_data_retention
                count = await ingest_data_retention(conn)
                print(f"  data_retention: {count} nodes")
            if target in ("codex_committees", "all"):
                from world_of_taxonomy.ingest.codex_committees import ingest_codex_committees
                count = await ingest_codex_committees(conn)
                print(f"  codex_committees: {count} nodes")
            if target in ("hedis", "all"):
                from world_of_taxonomy.ingest.hedis import ingest_hedis
                count = await ingest_hedis(conn)
                print(f"  hedis: {count} nodes")
            if target in ("cms_star", "all"):
                from world_of_taxonomy.ingest.cms_star import ingest_cms_star
                count = await ingest_cms_star(conn)
                print(f"  cms_star: {count} nodes")
            if target in ("mitre_attack", "all"):
                from world_of_taxonomy.ingest.mitre_attack import ingest_mitre_attack
                count = await ingest_mitre_attack(conn)
                print(f"  mitre_attack: {count} nodes")
            if target in ("cve_types", "all"):
                from world_of_taxonomy.ingest.cve_types import ingest_cve_types
                count = await ingest_cve_types(conn)
                print(f"  cve_types: {count} nodes")
            if target in ("owasp_top10", "all"):
                from world_of_taxonomy.ingest.owasp_top10 import ingest_owasp_top10
                count = await ingest_owasp_top10(conn)
                print(f"  owasp_top10: {count} nodes")
            if target in ("tcfd", "all"):
                from world_of_taxonomy.ingest.tcfd import ingest_tcfd
                count = await ingest_tcfd(conn)
                print(f"  tcfd: {count} nodes")
            if target in ("issb_s1_s2", "all"):
                from world_of_taxonomy.ingest.issb_s1_s2 import ingest_issb_s1_s2
                count = await ingest_issb_s1_s2(conn)
                print(f"  issb_s1_s2: {count} nodes")
            if target in ("sbti", "all"):
                from world_of_taxonomy.ingest.sbti import ingest_sbti
                count = await ingest_sbti(conn)
                print(f"  sbti: {count} nodes")
            if target in ("cfr_titles", "all"):
                from world_of_taxonomy.ingest.cfr_titles import ingest_cfr_titles
                count = await ingest_cfr_titles(conn)
                print(f"  cfr_titles: {count} nodes")
            if target in ("usc_titles", "all"):
                from world_of_taxonomy.ingest.usc_titles import ingest_usc_titles
                count = await ingest_usc_titles(conn)
                print(f"  usc_titles: {count} nodes")
            if target in ("swift_mt", "all"):
                from world_of_taxonomy.ingest.swift_mt import ingest_swift_mt
                count = await ingest_swift_mt(conn)
                print(f"  swift_mt: {count} nodes")
            if target in ("iso20022_msg", "all"):
                from world_of_taxonomy.ingest.iso20022_msg import ingest_iso20022_msg
                count = await ingest_iso20022_msg(conn)
                print(f"  iso20022_msg: {count} nodes")
            if target in ("card_schemes", "all"):
                from world_of_taxonomy.ingest.card_schemes import ingest_card_schemes
                count = await ingest_card_schemes(conn)
                print(f"  card_schemes: {count} nodes")
            if target in ("gs1_standards", "all"):
                from world_of_taxonomy.ingest.gs1_standards import ingest_gs1_standards
                count = await ingest_gs1_standards(conn)
                print(f"  gs1_standards: {count} nodes")
            if target in ("edi_standards", "all"):
                from world_of_taxonomy.ingest.edi_standards import ingest_edi_standards
                count = await ingest_edi_standards(conn)
                print(f"  edi_standards: {count} nodes")
            if target in ("scor_model", "all"):
                from world_of_taxonomy.ingest.scor_model import ingest_scor_model
                count = await ingest_scor_model(conn)
                print(f"  scor_model: {count} nodes")
            if target in ("shrm_competency", "all"):
                from world_of_taxonomy.ingest.shrm_competency import ingest_shrm_competency
                count = await ingest_shrm_competency(conn)
                print(f"  shrm_competency: {count} nodes")
            if target in ("job_family", "all"):
                from world_of_taxonomy.ingest.job_family import ingest_job_family
                count = await ingest_job_family(conn)
                print(f"  job_family: {count} nodes")
            if target in ("rics_valuation", "all"):
                from world_of_taxonomy.ingest.rics_valuation import ingest_rics_valuation
                count = await ingest_rics_valuation(conn)
                print(f"  rics_valuation: {count} nodes")
            if target in ("breeam", "all"):
                from world_of_taxonomy.ingest.breeam import ingest_breeam
                count = await ingest_breeam(conn)
                print(f"  breeam: {count} nodes")
            if target in ("leed_v4_1", "all"):
                from world_of_taxonomy.ingest.leed_v4_1 import ingest_leed_v4_1
                count = await ingest_leed_v4_1(conn)
                print(f"  leed_v4_1: {count} nodes")
            if target in ("fao_aquastat", "all"):
                from world_of_taxonomy.ingest.fao_aquastat import ingest_fao_aquastat
                count = await ingest_fao_aquastat(conn)
                print(f"  fao_aquastat: {count} nodes")
            if target in ("fao_stat_domain", "all"):
                from world_of_taxonomy.ingest.fao_stat_domain import ingest_fao_stat_domain
                count = await ingest_fao_stat_domain(conn)
                print(f"  fao_stat_domain: {count} nodes")
            if target in ("iea_energy_bal", "all"):
                from world_of_taxonomy.ingest.iea_energy_bal import ingest_iea_energy_bal
                count = await ingest_iea_energy_bal(conn)
                print(f"  iea_energy_bal: {count} nodes")
            if target in ("irena_re", "all"):
                from world_of_taxonomy.ingest.irena_re import ingest_irena_re
                count = await ingest_irena_re(conn)
                print(f"  irena_re: {count} nodes")
            if target in ("fhir_resources", "all"):
                from world_of_taxonomy.ingest.fhir_resources import ingest_fhir_resources
                count = await ingest_fhir_resources(conn)
                print(f"  fhir_resources: {count} nodes")
            if target in ("dicom_modality", "all"):
                from world_of_taxonomy.ingest.dicom_modality import ingest_dicom_modality
                count = await ingest_dicom_modality(conn)
                print(f"  dicom_modality: {count} nodes")
            if target in ("itu_r_bands", "all"):
                from world_of_taxonomy.ingest.itu_r_bands import ingest_itu_r_bands
                count = await ingest_itu_r_bands(conn)
                print(f"  itu_r_bands: {count} nodes")
            if target in ("si_units", "all"):
                from world_of_taxonomy.ingest.si_units import ingest_si_units
                count = await ingest_si_units(conn)
                print(f"  si_units: {count} nodes")
            if target in ("board_committee", "all"):
                from world_of_taxonomy.ingest.board_committee import ingest_board_committee
                count = await ingest_board_committee(conn)
                print(f"  board_committee: {count} nodes")
            if target in ("corporate_action", "all"):
                from world_of_taxonomy.ingest.corporate_action import ingest_corporate_action
                count = await ingest_corporate_action(conn)
                print(f"  corporate_action: {count} nodes")
            if target in ("pmbok7", "all"):
                from world_of_taxonomy.ingest.pmbok7 import ingest_pmbok7
                count = await ingest_pmbok7(conn)
                print(f"  pmbok7: {count} nodes")
            if target in ("prince2", "all"):
                from world_of_taxonomy.ingest.prince2 import ingest_prince2
                count = await ingest_prince2(conn)
                print(f"  prince2: {count} nodes")
            if target in ("itil4", "all"):
                from world_of_taxonomy.ingest.itil4 import ingest_itil4
                count = await ingest_itil4(conn)
                print(f"  itil4: {count} nodes")
            if target in ("isa_standards", "all"):
                from world_of_taxonomy.ingest.isa_standards import ingest_isa_standards
                count = await ingest_isa_standards(conn)
                print(f"  isa_standards: {count} nodes")
            if target in ("wco_safe", "all"):
                from world_of_taxonomy.ingest.wco_safe import ingest_wco_safe
                count = await ingest_wco_safe(conn)
                print(f"  wco_safe: {count} nodes")
            if target in ("skos", "all"):
                from world_of_taxonomy.ingest.skos import ingest_skos
                count = await ingest_skos(conn)
                print(f"  skos: {count} nodes")
            if target in ("xbrl_taxonomy", "all"):
                from world_of_taxonomy.ingest.xbrl_taxonomy import ingest_xbrl_taxonomy
                count = await ingest_xbrl_taxonomy(conn)
                print(f"  xbrl_taxonomy: {count} nodes")
            if target in ("token_standard", "all"):
                from world_of_taxonomy.ingest.token_standard import ingest_token_standard
                count = await ingest_token_standard(conn)
                print(f"  token_standard: {count} nodes")
            if target in ("defi_protocol", "all"):
                from world_of_taxonomy.ingest.defi_protocol import ingest_defi_protocol
                count = await ingest_defi_protocol(conn)
                print(f"  defi_protocol: {count} nodes")
            if target in ("iab_content", "all"):
                from world_of_taxonomy.ingest.iab_content import ingest_iab_content
                count = await ingest_iab_content(conn)
                print(f"  iab_content: {count} nodes")
            if target in ("togaf_adm", "all"):
                from world_of_taxonomy.ingest.togaf_adm import ingest_togaf_adm
                count = await ingest_togaf_adm(conn)
                print(f"  togaf_adm: {count} nodes")
            if target in ("archimate", "all"):
                from world_of_taxonomy.ingest.archimate import ingest_archimate
                count = await ingest_archimate(conn)
                print(f"  archimate: {count} nodes")
            if target in ("irs_forms", "all"):
                from world_of_taxonomy.ingest.irs_forms import ingest_irs_forms
                count = await ingest_irs_forms(conn)
                print(f"  irs_forms: {count} nodes")
            if target in ("vat_rates", "all"):
                from world_of_taxonomy.ingest.vat_rates import ingest_vat_rates
                count = await ingest_vat_rates(conn)
                print(f"  vat_rates: {count} nodes")
            if target in ("gdpr_rights", "all"):
                from world_of_taxonomy.ingest.gdpr_rights import ingest_gdpr_rights
                count = await ingest_gdpr_rights(conn)
                print(f"  gdpr_rights: {count} nodes")
            if target in ("contract_types", "all"):
                from world_of_taxonomy.ingest.contract_types import ingest_contract_types
                count = await ingest_contract_types(conn)
                print(f"  contract_types: {count} nodes")
            if target in ("imo_ship_type", "all"):
                from world_of_taxonomy.ingest.imo_ship_type import ingest_imo_ship_type
                count = await ingest_imo_ship_type(conn)
                print(f"  imo_ship_type: {count} nodes")
            if target in ("container_iso", "all"):
                from world_of_taxonomy.ingest.container_iso import ingest_container_iso
                count = await ingest_container_iso(conn)
                print(f"  container_iso: {count} nodes")
            if target in ("nanda_nursing_dx", "all"):
                from world_of_taxonomy.ingest.nanda_nursing_dx import ingest_nanda_nursing_dx
                count = await ingest_nanda_nursing_dx(conn)
                print(f"  nanda_nursing_dx: {count} nodes")
            if target in ("nic_nursing_intv", "all"):
                from world_of_taxonomy.ingest.nic_nursing_intv import ingest_nic_nursing_intv
                count = await ingest_nic_nursing_intv(conn)
                print(f"  nic_nursing_intv: {count} nodes")
            if target in ("mime_types", "all"):
                from world_of_taxonomy.ingest.mime_types import ingest_mime_types
                count = await ingest_mime_types(conn)
                print(f"  mime_types: {count} nodes")
            if target in ("http_status", "all"):
                from world_of_taxonomy.ingest.http_status import ingest_http_status
                count = await ingest_http_status(conn)
                print(f"  http_status: {count} nodes")
            if target in ("spdx_licenses", "all"):
                from world_of_taxonomy.ingest.spdx_licenses import ingest_spdx_licenses
                count = await ingest_spdx_licenses(conn)
                print(f"  spdx_licenses: {count} nodes")
            if target in ("periodic_table", "all"):
                from world_of_taxonomy.ingest.periodic_table import ingest_periodic_table
                count = await ingest_periodic_table(conn)
                print(f"  periodic_table: {count} nodes")
            if target in ("geological_time", "all"):
                from world_of_taxonomy.ingest.geological_time import ingest_geological_time
                count = await ingest_geological_time(conn)
                print(f"  geological_time: {count} nodes")
            if target in ("beaufort_scale", "all"):
                from world_of_taxonomy.ingest.beaufort_scale import ingest_beaufort_scale
                count = await ingest_beaufort_scale(conn)
                print(f"  beaufort_scale: {count} nodes")
            if target in ("mohs_hardness", "all"):
                from world_of_taxonomy.ingest.mohs_hardness import ingest_mohs_hardness
                count = await ingest_mohs_hardness(conn)
                print(f"  mohs_hardness: {count} nodes")
            if target in ("pantone_families", "all"):
                from world_of_taxonomy.ingest.pantone_families import ingest_pantone_families
                count = await ingest_pantone_families(conn)
                print(f"  pantone_families: {count} nodes")
            if target in ("ral_colors", "all"):
                from world_of_taxonomy.ingest.ral_colors import ingest_ral_colors
                count = await ingest_ral_colors(conn)
                print(f"  ral_colors: {count} nodes")
            if target in ("isrc_format", "all"):
                from world_of_taxonomy.ingest.isrc_format import ingest_isrc_format
                count = await ingest_isrc_format(conn)
                print(f"  isrc_format: {count} nodes")
            if target in ("isbn_groups", "all"):
                from world_of_taxonomy.ingest.isbn_groups import ingest_isbn_groups
                count = await ingest_isbn_groups(conn)
                print(f"  isbn_groups: {count} nodes")
            if target in ("usda_soil", "all"):
                from world_of_taxonomy.ingest.usda_soil import ingest_usda_soil
                count = await ingest_usda_soil(conn)
                print(f"  usda_soil: {count} nodes")
            if target in ("koppen_climate", "all"):
                from world_of_taxonomy.ingest.koppen_climate import ingest_koppen_climate
                count = await ingest_koppen_climate(conn)
                print(f"  koppen_climate: {count} nodes")
            if target in ("icao_doc4444", "all"):
                from world_of_taxonomy.ingest.icao_doc4444 import ingest_icao_doc4444
                count = await ingest_icao_doc4444(conn)
                print(f"  icao_doc4444: {count} nodes")
            if target in ("olympic_sports", "all"):
                from world_of_taxonomy.ingest.olympic_sports import ingest_olympic_sports
                count = await ingest_olympic_sports(conn)
                print(f"  olympic_sports: {count} nodes")
            if target in ("fifa_confederations", "all"):
                from world_of_taxonomy.ingest.fifa_confederations import ingest_fifa_confederations
                count = await ingest_fifa_confederations(conn)
                print(f"  fifa_confederations: {count} nodes")
            if target in ("haccp", "all"):
                from world_of_taxonomy.ingest.haccp import ingest_haccp
                count = await ingest_haccp(conn)
                print(f"  haccp: {count} nodes")
            if target in ("allergen_list", "all"):
                from world_of_taxonomy.ingest.allergen_list import ingest_allergen_list
                count = await ingest_allergen_list(conn)
                print(f"  allergen_list: {count} nodes")
            if target in ("wcag", "all"):
                from world_of_taxonomy.ingest.wcag import ingest_wcag
                count = await ingest_wcag(conn)
                print(f"  wcag: {count} nodes")
            if target in ("six_sigma", "all"):
                from world_of_taxonomy.ingest.six_sigma import ingest_six_sigma
                count = await ingest_six_sigma(conn)
                print(f"  six_sigma: {count} nodes")
            if target in ("lean_tools", "all"):
                from world_of_taxonomy.ingest.lean_tools import ingest_lean_tools
                count = await ingest_lean_tools(conn)
                print(f"  lean_tools: {count} nodes")
            if target in ("ai_model_type", "all"):
                from world_of_taxonomy.ingest.ai_model_type import ingest_ai_model_type
                count = await ingest_ai_model_type(conn)
                print(f"  ai_model_type: {count} nodes")
            if target in ("cloud_native", "all"):
                from world_of_taxonomy.ingest.cloud_native import ingest_cloud_native
                count = await ingest_cloud_native(conn)
                print(f"  cloud_native: {count} nodes")
            if target in ("un_sdg_indicators", "all"):
                from world_of_taxonomy.ingest.un_sdg_indicators import ingest_un_sdg_indicators
                count = await ingest_un_sdg_indicators(conn)
                print(f"  un_sdg_indicators: {count} nodes")
            if target in ("emoji_categories", "all"):
                from world_of_taxonomy.ingest.emoji_categories import ingest_emoji_categories
                count = await ingest_emoji_categories(conn)
                print(f"  emoji_categories: {count} nodes")
            if target in ("blood_types", "all"):
                from world_of_taxonomy.ingest.blood_types import ingest_blood_types
                count = await ingest_blood_types(conn)
                print(f"  blood_types: {count} nodes")
            if target in ("richter_scale", "all"):
                from world_of_taxonomy.ingest.richter_scale import ingest_richter_scale
                count = await ingest_richter_scale(conn)
                print(f"  richter_scale: {count} nodes")
            if target in ("saffir_simpson", "all"):
                from world_of_taxonomy.ingest.saffir_simpson import ingest_saffir_simpson
                count = await ingest_saffir_simpson(conn)
                print(f"  saffir_simpson: {count} nodes")
            if target in ("fujita_tornado", "all"):
                from world_of_taxonomy.ingest.fujita_tornado import ingest_fujita_tornado
                count = await ingest_fujita_tornado(conn)
                print(f"  fujita_tornado: {count} nodes")
            if target in ("uv_index", "all"):
                from world_of_taxonomy.ingest.uv_index import ingest_uv_index
                count = await ingest_uv_index(conn)
                print(f"  uv_index: {count} nodes")
            if target in ("apgar_score", "all"):
                from world_of_taxonomy.ingest.apgar_score import ingest_apgar_score
                count = await ingest_apgar_score(conn)
                print(f"  apgar_score: {count} nodes")
            if target in ("bristol_stool", "all"):
                from world_of_taxonomy.ingest.bristol_stool import ingest_bristol_stool
                count = await ingest_bristol_stool(conn)
                print(f"  bristol_stool: {count} nodes")
            if target in ("pain_scale", "all"):
                from world_of_taxonomy.ingest.pain_scale import ingest_pain_scale
                count = await ingest_pain_scale(conn)
                print(f"  pain_scale: {count} nodes")
            if target in ("bmi_categories", "all"):
                from world_of_taxonomy.ingest.bmi_categories import ingest_bmi_categories
                count = await ingest_bmi_categories(conn)
                print(f"  bmi_categories: {count} nodes")
            if target in ("asa_physical", "all"):
                from world_of_taxonomy.ingest.asa_physical import ingest_asa_physical
                count = await ingest_asa_physical(conn)
                print(f"  asa_physical: {count} nodes")


        await close_pool()

    _run(_ingest())
    print("\nIngestion complete.")


def cmd_browse(args):
    """Browse classification hierarchy."""
    from world_of_taxonomy.db import get_pool, close_pool

    async def _browse():
        pool = await get_pool()
        async with pool.acquire() as conn:
            if args.code:
                # Show specific node and its children
                from world_of_taxonomy.query.browse import get_node, get_children, get_ancestors
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
                from world_of_taxonomy.query.browse import get_system, get_roots
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
    from world_of_taxonomy.db import get_pool, close_pool

    async def _search():
        pool = await get_pool()
        async with pool.acquire() as conn:
            from world_of_taxonomy.query.search import search_nodes
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
    from world_of_taxonomy.db import get_pool, close_pool

    async def _equiv():
        pool = await get_pool()
        async with pool.acquire() as conn:
            if args.target:
                from world_of_taxonomy.query.equivalence import translate_code
                results = await translate_code(
                    conn, args.system_id, args.code, args.target,
                )
            else:
                from world_of_taxonomy.query.equivalence import get_equivalences
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
    from world_of_taxonomy.db import get_pool, close_pool

    async def _stats():
        pool = await get_pool()
        async with pool.acquire() as conn:
            from world_of_taxonomy.query.browse import get_systems
            from world_of_taxonomy.query.equivalence import get_crosswalk_stats

            systems = await get_systems(conn)
            crosswalk = await get_crosswalk_stats(conn)

            print("╔═══════════════════════════════════════════════╗")
            print("║        WorldOfTaxonomy - Statistics           ║")
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
    from world_of_taxonomy.api.app import create_app
    from world_of_taxonomy.db import get_pool, close_pool

    app = create_app()

    @app.on_event("startup")
    async def startup():
        app.state.pool = await get_pool()
        print("Database pool ready.")

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()
        print("Database pool closed.")

    print(f"\nStarting WorldOfTaxonomy API server...")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs\n")
    uvicorn.run(app, host=args.host, port=args.port)


def cmd_mcp(args):
    """Start the MCP server (stdio transport)."""
    from world_of_taxonomy.mcp.server import main as mcp_main
    mcp_main()


# ── Argument Parser ───────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world_of_taxonomy",
        description="WorldOfTaxonomy - Unified Industry Classification Knowledge Graph",
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
        choices=["naics", "isic", "nic", "nace", "sic", "anzsic", "jsic", "wz", "onace", "noga", "crosswalk", "iso3166_1", "iso3166_2", "crosswalk_iso3166", "un_m49", "crosswalk_un_m49_iso3166", "hs2022", "crosswalk_hs_isic", "cpc_v21", "crosswalk_cpc_isic", "crosswalk_cpc_hs", "unspsc_v24", "soc_2018", "isco_08", "crosswalk_soc_naics", "crosswalk_soc_isco", "crosswalk_isco_isic", "cip_2020", "crosswalk_cip_soc", "isced_2011", "crosswalk_isced_isco", "iscedf_2013", "crosswalk_cip_iscedf", "atc_who", "icd_11", "crosswalk_icd_isic", "loinc", "cofog", "gics_bridge", "ghg_protocol", "esco_occupations", "esco_skills", "crosswalk_esco_isco", "onet_soc", "crosswalk_onet_soc", "patent_cpc", "cfr_title_49", "fmcsa_regs", "crosswalk_cfr_naics", "gdpr", "iso_31000", "domain_truck_freight", "domain_truck_vehicle", "domain_truck_cargo", "crosswalk_fmcsa_truck", "domain_truck_ops", "crosswalk_naics484_domains", "domain_truck_pricing", "domain_truck_regulatory", "domain_truck_tech", "domain_truck_lane", "domain_ag_crop", "domain_ag_livestock", "domain_ag_method", "domain_ag_grade", "domain_ag_equipment", "domain_ag_input", "domain_ag_business", "domain_ag_market", "domain_ag_regulatory", "domain_ag_land", "domain_ag_postharvest", "crosswalk_naics11_domains", "domain_mining_mineral", "domain_mining_method", "domain_mining_reserve", "domain_mining_equipment", "domain_mining_lifecycle", "domain_mining_safety", "crosswalk_naics21_domains", "domain_util_energy", "domain_util_grid", "domain_util_tariff", "domain_util_asset", "domain_util_regulatory", "crosswalk_naics22_domains", "domain_const_trade", "domain_const_building", "domain_const_delivery", "domain_const_material", "domain_const_sustainability", "crosswalk_naics23_domains", "domain_mfg_process", "domain_retail_channel", "domain_finance_instrument", "domain_health_setting", "domain_transport_mode", "domain_info_media", "domain_realestate_type", "domain_food_service", "domain_wholesale_channel", "domain_prof_services", "domain_education_type", "domain_arts_content", "domain_other_services", "domain_public_admin", "domain_supply_chain", "domain_workforce_safety", "domain_mfg_industry", "domain_mfg_quality", "domain_mfg_opsmodel", "domain_retail_merchandise", "domain_retail_fulfillment", "domain_finance_market", "domain_finance_regulatory", "domain_health_specialty", "domain_health_payer", "domain_transport_service", "domain_transport_infra", "domain_info_revenue", "domain_info_platform", "domain_realestate_transaction", "domain_realestate_capital", "domain_food_revenue", "domain_food_ownership", "domain_wholesale_product", "domain_wholesale_regulatory", "domain_prof_firm", "domain_prof_delivery", "domain_education_funding", "domain_education_segment", "domain_arts_monetization", "domain_arts_creator", "domain_other_pricing", "domain_public_funding", "domain_supply_tech", "domain_supply_risk", "domain_workforce_training", "domain_workforce_sms", "anzsco_2022", "crosswalk_anzsco_anzsic", "domain_chemical_type", "domain_defence_type", "domain_water_env", "domain_ai_data", "domain_biotech", "domain_space", "domain_climate_tech", "domain_adv_materials", "domain_quantum", "domain_digital_assets", "domain_robotics", "domain_energy_storage", "domain_semiconductor", "domain_synbio", "domain_xr_meta", "cnae_2012", "csic_2017", "okved_2", "kbli_2020", "scian_2018", "sic_sa", "crosswalk_geo_sector", "crosswalk_country_system", "gbt_4754", "ksic_2017", "ssic_2020", "msic_2008", "tsic_2009", "psic_2009", "sitc_rev4", "bec_rev5", "noc_2021", "uksoc_2020", "kldb_2010", "rome_v4", "nucc_hcpt", "ms_drg", "hcpcs_l2", "sasb_sics", "eu_taxonomy", "eu_nuts_2021", "us_fips", "hts_us", "icd10cm", "mesh", "geonames_features", "schema_org", "fibo", "wordnet_nouns", "prodcom", "cpv_2008", "acm_ccs", "jel", "domain_chemical_hazard", "domain_chemical_regulatory", "domain_defence_acquisition", "domain_defence_trl", "domain_water_regulatory", "domain_water_ecosystem", "domain_ai_deployment", "domain_ai_governance", "domain_biotech_regulatory", "domain_biotech_business", "domain_space_orbital", "domain_space_regulatory", "domain_climate_finance", "domain_climate_policy", "domain_materials_application", "domain_materials_process", "domain_quantum_application", "domain_quantum_stage", "domain_digital_assets_regulatory", "domain_digital_assets_infra", "domain_robotics_application", "domain_robotics_sensing", "domain_energy_storage_application", "domain_energy_storage_perf", "domain_semiconductor_application", "domain_semiconductor_ip", "domain_synbio_application", "domain_synbio_biosafety", "domain_xr_application", "domain_xr_business", "domain_mfg_supply_chain", "domain_mfg_facility", "domain_retail_pricing", "domain_retail_format", "domain_finance_client", "domain_health_delivery", "domain_health_it", "domain_transport_fare", "domain_transport_fleet", "domain_info_content", "domain_realestate_grade", "domain_realestate_lease", "domain_food_cuisine", "domain_education_delivery", "domain_education_credential", "domain_prof_billing", "domain_arts_venue", "domain_public_procurement", "domain_supply_logistics", "domain_workforce_incident", "domain_workforce_ppe", "domain_wholesale_distribution", "ateco_2007", "naf_rev2", "pkd_2007", "sbi_2008", "sni_2007", "db07", "tol_2008", "ciiu_co", "ciiu_ar", "ciiu_cl", "arxiv_taxonomy", "sdg", "oecd_dac", "gri_standards", "icb", "basel_exposure", "wb_income", "adb_sector", "tnfd", "sfdr", "msc_2020", "pacs", "lcc", "eccn", "schedule_b", "icd10_pcs", "icdo3", "icf", "cae_rev3", "cz_nace", "teaor_2008", "caen_rev2", "nkd_2007", "sk_nace", "nkid", "emtak", "nace_lt", "nk_lv", "nace_tr", "ciiu_pe", "ciiu_ec", "caeb", "ciiu_ve", "ciiu_cr", "ciiu_gt", "ciiu_pa", "vsic_2018", "bsic", "psic_pk", "isic_ng", "isic_ke", "isic_eg", "isic_sa", "isic_ae", "coicop", "cfi_iso10962", "ford_frascati", "cn_2024", "anzsrc_for_2020", "icd10_gm", "icd10_am", "seea", "cnae_2009", "nace_bel", "nace_lu", "nace_ie", "stakod_08", "nace_cy", "nace_mt", "skd_2008", "sn_2007", "isat_2008", "kd_rs", "nkd_mk", "kd_ba", "kd_me", "nve_al", "kd_xk", "caem_md", "kved_ua", "nace_ge", "nace_am", "kbli_id", "slsic", "isic_mm", "isic_kh", "isic_la", "isic_np", "isic_et", "isic_tz", "isic_gh", "isic_ma", "isic_tn", "isic_dz", "isic_sn", "isic_cm", "isic_ug", "isic_mz", "isic_iq", "isic_jo", "ciiu_py", "ciiu_uy", "ciiu_do", "isic_hn", "isic_sv", "isic_ni", "isic_zw", "isic_tt", "isic_jm", "isic_ht", "isic_fj", "isic_pg", "isic_mn", "isic_kz", "isic_uz", "isic_az", "isic_ci", "isic_rw", "isic_zm", "isic_bw", "isic_na_country", "isic_mg", "isic_mu", "isic_bf", "isic_ml", "isic_mw", "isic_af", "domain_insurance_product", "domain_insurance_risk", "domain_legal_practice", "domain_telecom_service", "domain_telecom_network", "domain_cyber_threat", "domain_cyber_framework", "domain_gaming_esports", "domain_waste_mgmt", "domain_textile_fashion", "domain_tourism_travel", "domain_maritime_shipping", "domain_aviation_service", "domain_forestry_mgmt", "domain_fishing_aqua", "domain_wine_spirits", "domain_nuclear_energy", "domain_hydrogen_economy", "domain_pet_animal", "domain_sports_recreation", "domain_nonprofit_social", "domain_childcare_early", "domain_senior_care", "domain_advertising_mktg", "domain_datacenter_cloud", "domain_ecommerce_platform", "domain_fintech_service", "domain_edtech_platform", "domain_proptech", "domain_agritech", "domain_healthtech", "domain_cleantech", "domain_legaltech", "domain_insurtech", "domain_regtech", "isic_lb","isic_om","isic_qa","isic_bh","isic_kw","isic_ye","isic_ir","isic_ly","isic_il","isic_ps","isic_sy","isic_kg","isic_tj","isic_tm","isic_cu","isic_bb","isic_bs","isic_gy","isic_sr","isic_bz","isic_ag","isic_lc","isic_gd","isic_vc","isic_dm","isic_kn","isic_ss","isic_so","isic_gn","isic_sl","isic_lr","isic_tg","isic_bj","isic_ne","isic_td","isic_cd","isic_ao","isic_ga","isic_gq","isic_cg","isic_km","isic_dj","isic_cv","isic_gm","isic_gw","isic_mr","isic_sz","isic_ls","isic_bi","isic_er","isic_sc","isic_ws","isic_to","isic_vu","isic_sb","isic_bn","isic_tl","isic_bt","isic_mv", "reg_hipaa", "reg_sox", "reg_glba", "reg_ferpa", "reg_coppa", "reg_fcra", "reg_ada", "reg_osha_1910", "reg_osha_1926", "reg_nerc_cip", "reg_fisma", "reg_fedramp", "reg_ccpa", "reg_cfpb", "reg_sec", "reg_finra", "reg_far", "reg_dfars", "reg_itar", "reg_ear", "reg_clean_air", "reg_clean_water", "reg_cercla", "reg_rcra", "reg_tsca", "reg_pci_dss", "reg_soc2", "reg_hitrust", "reg_cmmc", "reg_nist_csf", "reg_nist_800_53", "reg_nist_800_171", "reg_cis_controls", "reg_cobit", "reg_coso", "reg_ffiec", "reg_ftc_safeguards", "reg_naic", "reg_us_gaap", "reg_fasb", "reg_pcaob", "reg_aicpa", "reg_joint_commission", "reg_cap", "reg_clia", "reg_fda_21cfr", "reg_dea", "reg_usp", "reg_ashrae", "reg_asme", "reg_dora", "reg_nis2", "reg_eu_ai_act", "reg_eprivacy", "reg_mifid2", "reg_solvency2", "reg_psd2", "reg_reach", "reg_rohs", "reg_mdr", "reg_ivdr", "reg_eu_whistleblower", "reg_csrd", "reg_cbam", "reg_weee", "reg_eu_packaging", "reg_eu_batteries", "reg_sfdr_detail", "reg_eu_deforestation", "reg_dsa", "reg_dma", "reg_eu_cra", "reg_eu_data_act", "reg_eu_machinery", "reg_emas", "reg_iso_9001", "reg_iso_14001", "reg_iso_27001", "reg_iso_22000", "reg_iso_45001", "reg_iso_50001", "reg_iso_13485", "reg_iso_22301", "reg_iso_20000", "reg_iso_26000", "reg_iso_37001", "reg_iso_42001", "reg_iso_28000", "reg_iso_55001", "reg_iso_41001", "reg_iso_30401", "reg_iso_21001", "reg_iso_39001", "reg_iso_37101", "reg_iso_14064", "reg_iso_14040", "reg_iso_19011", "reg_iso_31010", "reg_iso_22313", "reg_iso_27701", "reg_basel3", "reg_fatf", "reg_ilo_core", "reg_ungp", "reg_oecd_mne", "reg_wto_sps", "reg_wto_tbt", "reg_codex", "reg_who_fctc", "reg_uncitral", "reg_unclos", "reg_montreal", "reg_paris", "reg_kimberley", "reg_equator", "reg_ifc_ps", "reg_icao_annex", "reg_marpol", "reg_solas", "reg_berne", "domain_pharma_drug_class", "domain_medical_device", "domain_clinical_trial", "domain_mental_health", "domain_dental", "domain_veterinary", "domain_credit_rating", "domain_derivatives", "domain_pe_stage", "domain_digital_banking", "domain_payment_proc", "domain_trade_finance", "domain_reinsurance", "domain_microfinance", "domain_auto_vehicle_level", "domain_ev_charging", "domain_fleet_mgmt", "domain_rail_service", "domain_last_mile", "domain_solar_energy", "domain_wind_energy", "domain_battery_tech", "domain_smart_grid", "domain_carbon_credit", "domain_cloud_service", "domain_devops", "domain_saas_category", "domain_iot_device", "domain_organic_cert", "domain_crop_protection", "domain_soil_mgmt", "domain_precision_ag", "domain_digital_twin", "domain_edge_computing", "domain_coworking", "domain_event_mgmt", "domain_franchise", "domain_subscription", "domain_circular_econ", "domain_sharing_econ", "domain_hr_tech", "domain_talent_market", "domain_insurance_underwriting", "domain_insurance_claims", "domain_actuarial_method", "domain_commercial_lending", "domain_mortgage_type", "domain_wealth_mgmt", "domain_hedge_fund", "domain_commodity_trading", "domain_forex", "domain_bond_rating", "domain_muni_bond", "domain_securitization", "domain_reit_type", "domain_property_val", "domain_zoning", "domain_construction_permit", "domain_building_code", "domain_fire_protection", "domain_elevator", "domain_plumbing_code", "domain_electrical_code", "domain_hvac_system", "domain_roofing_type", "domain_foundation_type", "domain_structural", "domain_facade", "domain_landscape", "domain_parking", "domain_signage", "domain_accessibility", "domain_env_remediation", "domain_brownfield", "domain_green_material", "domain_modular_const", "domain_prefab", "domain_smart_building", "domain_building_auto", "domain_energy_audit", "domain_commissioning", "domain_retro_cx", "domain_facility_bench", "domain_lease_abstract", "domain_api_architecture", "domain_database_type", "domain_prog_paradigm", "domain_sw_license", "domain_oss_governance", "domain_version_control", "domain_cicd_pipeline", "domain_container_orch", "domain_serverless", "domain_microservices", "domain_event_arch", "domain_data_mesh", "domain_data_lakehouse", "domain_mlops", "domain_feature_store", "domain_model_registry", "domain_data_catalog", "domain_data_quality", "domain_data_governance", "domain_data_lineage", "domain_master_data", "domain_ref_data", "domain_synthetic_data", "domain_pet", "domain_zero_trust", "domain_identity_gov", "domain_siem", "domain_soar", "domain_threat_intel", "domain_vuln_mgmt", "domain_pentest", "domain_incident_resp", "domain_dr", "domain_backup", "domain_encryption", "domain_key_mgmt", "domain_cert_authority", "domain_pki", "domain_hsm", "domain_red_team", "domain_blue_team", "domain_purple_team", "domain_hospital_dept", "domain_nursing_spec", "domain_allied_health", "domain_lab_test", "domain_imaging", "domain_surgical_spec", "domain_anesthesia", "domain_pathology_sub", "domain_pharma_practice", "domain_formulary", "domain_drug_interaction", "domain_adverse_event", "domain_clinical_endpoint", "domain_biomarker", "domain_companion_dx", "domain_orphan_drug", "domain_biosimilar", "domain_gene_therapy", "domain_cell_therapy", "domain_radiopharm", "domain_med_gas", "domain_surgical_inst", "domain_implant", "domain_wound_care", "domain_infection_ctrl", "domain_sterilization", "domain_cleanroom", "domain_biobank", "domain_clinical_reg", "domain_pro", "domain_telemedicine", "domain_remote_monitor", "domain_cds", "domain_sdoh", "domain_pop_health", "domain_vbc_model", "domain_bundled_pay", "domain_capitation", "domain_global_budget", "domain_prosthetic", "domain_orthotic", "domain_health_literacy", "domain_oil_grade", "domain_nat_gas", "domain_lng_terminal", "domain_pipeline", "domain_refinery", "domain_petrochem", "domain_biofuel", "domain_geothermal", "domain_tidal", "domain_wave_energy", "domain_district_heat", "domain_cogeneration", "domain_microgrid_type", "domain_vpp", "domain_demand_resp", "domain_ancillary", "domain_capacity_mkt", "domain_rec", "domain_carbon_offset", "domain_emission_factor", "domain_air_quality", "domain_water_quality", "domain_soil_contam", "domain_biodiv_offset", "domain_wetland", "domain_seed_variety", "domain_irrigation", "domain_greenhouse", "domain_aquaponics", "domain_vertical_farm", "domain_cold_chain", "domain_warehouse", "domain_cross_dock", "domain_freight_class", "domain_incoterm_detail", "domain_customs_proc", "domain_ftz", "domain_noise_pollution", "domain_light_pollution", "domain_invasive_sp", "domain_coral_reef", "domain_mangrove", "domain_univ_ranking", "domain_accreditation", "domain_student_assess", "domain_curriculum", "domain_learning_outcome", "domain_competency", "domain_micro_cred", "domain_apprentice", "domain_gig_worker", "domain_employee_benefit", "domain_comp_structure", "domain_labor_union", "domain_eeo_category", "domain_diversity_metric", "domain_gov_contract", "domain_grant_type", "domain_municipal_svc", "domain_emergency_svc", "domain_court_type", "domain_adr", "domain_trademark", "domain_patent_type", "domain_copyright", "domain_trade_secret", "domain_antitrust", "domain_consumer_prot", "domain_sanctions", "domain_export_ctrl", "domain_customs_class", "domain_internship", "domain_workplace_med", "domain_coll_bargain", "domain_product_liab", "domain_law_enforce", "domain_corrections", "domain_notary", "domain_class_action", "domain_freelance_plat", "domain_digital_badge", "domain_arb_type", "icd10_ca", "snomed_ct", "cpt_ama", "g_drg", "rxnorm", "ndc_fda", "dsm5", "icpc2", "ichi_who", "gbd_cause", "gmdn", "who_essential_med", "cdc_vaccine", "nci_thesaurus", "ctcae", "ifrs", "bloomberg_bics", "refinitiv_trbc", "sfia_v8", "digcomp_22", "ecf_v4", "scopus_asjc", "wos_categories", "eqf", "aqf", "onet_knowledge", "onet_abilities", "iucn_red_list", "cites", "eu_waste_cat", "stockholm_pops", "rotterdam_pic", "minamata", "iata_aircraft", "imo_vessel", "ietf_rfc", "w3c_standards", "ieee_standards", "usb_classes", "bluetooth_profiles", "esco_qualifications", "worldskills", "onet_work_activities", "onet_work_context", "onet_interests", "onet_work_values", "linkedin_skills", "nqf_uk", "naics_2017", "naics_2012", "isic_rev3", "eu_taric", "uk_trade_tariff", "asean_tariff", "mercosur_tariff", "afcfta_tariff", "gcc_tariff", "ecowas_cet", "dewey_decimal", "udc", "lcsh", "era_for", "unesco_thesaurus", "getty_aat", "aacsb", "abet", "epa_rcra_waste", "ramsar", "cbd_targets", "unep_chemicals", "nato_codification", "faa_aircraft_cat", "uic_railway", "icao_airport", "dod_mil_std", "itu_t", "tgpp_specs", "pci_sig", "jedec", "semi_standards", "vesa_standards", "hcpcs_l3", "icn_nursing", "edqm_dosage", "omim", "orphanet", "ftse_icb_detail", "cbd_aichi", "un_ammo", "stanag", "anzsrc_seo", "onet_work_styles", "ibc_2021", "nfpa_codes", "nuts_candidate", "opec_basket", "lme_metals", "nmfc", "stcc", "naic_lines", "ngss", "ccss", "bloom_taxonomy", "gdpr_basis", "data_retention", "codex_committees", "hedis", "cms_star", "mitre_attack", "cve_types", "owasp_top10", "tcfd", "issb_s1_s2", "sbti", "cfr_titles", "usc_titles", "swift_mt", "iso20022_msg", "card_schemes", "gs1_standards", "edi_standards", "scor_model", "shrm_competency", "job_family", "rics_valuation", "breeam", "leed_v4_1", "fao_aquastat", "fao_stat_domain", "iea_energy_bal", "irena_re", "fhir_resources", "dicom_modality", "itu_r_bands", "si_units", "board_committee", "corporate_action", "pmbok7", "prince2", "itil4", "isa_standards", "wco_safe", "skos", "xbrl_taxonomy", "token_standard", "defi_protocol", "iab_content", "togaf_adm", "archimate", "irs_forms", "vat_rates", "gdpr_rights", "contract_types", "imo_ship_type", "container_iso", "nanda_nursing_dx", "nic_nursing_intv", "mime_types", "http_status", "spdx_licenses", "periodic_table", "geological_time", "beaufort_scale", "mohs_hardness", "pantone_families", "ral_colors", "isrc_format", "isbn_groups", "usda_soil", "koppen_climate", "icao_doc4444", "olympic_sports", "fifa_confederations", "haccp", "allergen_list", "wcag", "six_sigma", "lean_tools", "ai_model_type", "cloud_native", "un_sdg_indicators", "emoji_categories", "blood_types", "richter_scale", "saffir_simpson", "fujita_tornado", "uv_index", "apgar_score", "bristol_stool", "pain_scale", "bmi_categories", "asa_physical", "all"],
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
