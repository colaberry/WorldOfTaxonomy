"""Generate world_of_taxonomy/ingest/domain_anchors.json from a prefix rule table.

Reads every domain_* system from the DB, applies a deterministic prefix->NAICS
rule to assign 1-3 NAICS anchor codes, and writes a JSON file that
crosswalk_domain_anchors.py consumes.

Re-runnable: overwrites the JSON each time. Flag weak anchors with note='weak_anchor'.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import asyncpg


OUT_PATH = Path(__file__).parent.parent / "world_of_taxonomy" / "ingest" / "domain_anchors.json"


# Ordered list: first matching substring wins. Each rule is
# (substrings_any_match, naics_list, note?).
RULES: list[tuple[tuple[str, ...], list[str], str | None]] = [
    # Healthcare specific first (most specific)
    (("dental",), ["6212"], None),
    (("veterinary",), ["5419"], None),
    (("pharma", "drug_class", "rxnorm", "ndc"), ["3254", "44611"], None),
    (("biotech", "gene_therapy", "cell_therapy", "biosimilar", "orphan_drug", "synbio"), ["5417", "3254"], None),
    (("medical_device", "imaging_mod", "implant", "prosthet", "orthot", "surgical_inst"), ["3391", "3345"], None),
    (("clinical", "trial", "adverse_event", "biomarker", "biobank", "patient_report", "endpoint"), ["5417", "6215"], None),
    (("telehealth", "telemedicine", "remote_monitor", "telemed_modal"), ["6213", "5415"], None),
    (("nursing", "allied_health", "anesthesia", "pathology_sub", "surgical_spec"), ["6221", "6211"], None),
    (("hospital", "health_setting"), ["6221", "6222"], None),
    (("mental_health",), ["6214"], None),
    (("health_care", "health_info", "health_it", "health_deliv", "ehr", "hit_", "clinical_decision", "health_lit", "pop_health", "value_based", "capit", "bundled_pay", "global_budget"), ["6215", "5415"], None),
    (("dentistry",), ["6212"], None),
    (("insur", "reinsur", "actuarial", "underwriting", "claims"), ["524"], None),
    (("microfinance", "trade_finance"), ["522"], None),
    (("credit_rating", "bond_rating", "muni_bond", "asset_securitiz", "derivat", "forex", "commodity_trad", "hedge_fund", "wealth", "private_equity"), ["523"], None),
    (("digital_bank", "payment", "fintech"), ["522", "5223"], None),
    (("finance", "banking"), ["522", "523"], None),
    (("health", "clinical", "medical"), ["6215"], None),

    # Ag / food
    (("ag_postharvest", "cold_chain"), ["4931", "1151"], None),
    (("ag_equipment",), ["3331"], None),
    (("ag_input",), ["3253", "4245"], None),
    (("ag_business", "ag_regulatory", "ag_market", "ag_land", "ag_grade"), ["111", "112"], None),
    (("agritech",), ["5415", "111"], None),
    (("aquaponics", "vertical_farm", "greenhouse", "crop", "seed", "soil_mgmt", "irrigation", "organic_cert", "precision_ag", "crop_prot"), ["111"], None),
    (("livestock", "aquaculture", "fishing"), ["112", "1141"], None),
    (("forestry",), ["113"], None),
    (("ag_", "agri"), ["111", "112", "115"], None),
    (("food_service", "food_"), ["722"], None),

    # Mining / extraction
    (("mining_equipment",), ["3331"], None),
    (("mining_", "mineral_", "extraction"), ["212", "213"], None),

    # Energy / utilities
    (("oil_", "gas_", "lng", "pipeline", "refinery", "petrochem"), ["211", "2212", "4861"], None),
    (("nuclear",), ["2211"], None),
    (("solar", "wind", "geothermal", "tidal", "wave_energy", "biofuel", "renewable_cert"), ["2211"], None),
    (("cogeneration", "district_heat", "microgrid", "virtual_power", "demand_response", "smart_grid", "battery_tech", "energy_storage"), ["2211", "3359"], None),
    (("ev_charging", "hydrogen"), ["2211", "454"], None),
    (("carbon_credit", "carbon_offset", "emission", "air_quality", "water_quality", "biodiversity", "wetland", "invasive", "coral", "mangrove", "noise_poll", "light_poll"), ["5417", "924"], None),
    (("util_",), ["2211", "2213"], None),
    (("energy_",), ["2211"], None),

    # Construction / buildings
    (("const_project_delivery", "const_mat", "const_sustain", "const_trade", "const_building", "const_"), ["236", "237", "238"], None),
    (("building_", "roofing", "plumb_", "elec_code", "hvac", "foundation", "struct_sys", "facade", "landscape", "parking_type", "signage", "accessibility", "green_building", "modular", "prefab", "smart_build", "building_auto", "commission", "energy_audit", "facil_bench", "lease_abstr", "zoning", "permit_", "fire_prot", "elevator", "retrocomm"), ["236", "237", "238"], None),
    (("brownfield", "env_remed"), ["5629"], None),

    # Manufacturing / industrial
    # NAICS 2022 uses the range code "31-33" as the manufacturing root.
    (("mfg_process", "mfg_industry", "mfg_quality", "mfg_operations", "mfg_supply", "mfg_facility", "mfg_"), ["31-33"], None),
    (("manufacturing",), ["31-33"], None),
    (("adv_materials", "advanced_mat", "materials_"), ["325", "3261"], None),
    (("semiconductor", "semi_"), ["3344"], None),
    (("chemical", "chem_"), ["325"], None),
    (("textile", "fashion"), ["315", "4481"], None),

    # Transportation
    (("truck_",), ["484"], None),
    (("rail_",), ["482"], None),
    (("aviation", "aircraft"), ["481", "3364"], None),
    (("maritime", "ship", "imo"), ["483"], None),
    (("fleet_mgmt", "autonomous_veh", "last_mile", "transport_", "transit_"), ["485", "488"], None),

    # Real estate
    (("realestate_", "real_estate", "property_", "reit_", "zoning_class", "mortgage", "commercial_lend"), ["531"], None),
    (("proptech",), ["531", "5415"], None),

    # Retail / wholesale
    # NAICS 2022 uses the range code "44-45" as the retail root.
    (("retail_",), ["44-45"], None),
    (("wholesale_",), ["42"], None),
    (("ecommerce", "e_commerce", "subscription_model", "franchise"), ["44-45", "4541"], None),

    # Tech / data / AI
    (("ai_deployment", "ai_governance", "ai_ethics", "ai_data", "ai_"), ["5415", "518"], None),
    (("datacenter", "cloud_infra", "cloud_service", "serverless", "container", "edge_compute", "digital_twin", "saas"), ["5415", "518"], None),
    (("data_", "synth_data", "privacy_enhance"), ["5415", "518"], None),
    (("api_", "database_", "programming", "open_source", "software_lic", "version_ctrl", "ci_cd", "microservice", "event_driven", "devops"), ["5415"], None),
    (("iot_", "digital_asset", "web3", "token_std", "defi", "blockchain"), ["5415", "518"], None),
    (("xr_", "metaverse", "gaming", "esport"), ["7139", "5121"], None),
    (("cyber_", "siem", "soar", "threat_intel", "vuln_mgmt", "pentest", "incident_resp", "disaster_recov", "backup_strat", "encryption", "pki", "hsm", "zero_trust", "identity_gov", "red_team", "blue_team", "purple_team", "privacy_tech"), ["5415", "5417"], None),
    (("digital_",), ["5415", "518"], None),
    (("telecom_", "mobile_net"), ["517"], None),

    # Workforce / HR / education
    (("edtech",), ["611", "5415"], None),
    (("education_", "educ_", "student", "curriculum", "learn_outcome", "competency", "micro_cred", "apprentice", "univ_rank", "accreditation"), ["611"], None),
    (("hr_", "talent_", "gig_", "freelance", "employee", "compensation", "labor_union", "eeo", "diversity", "collective_barg", "workplace_med", "digital_badge", "internship"), ["5613", "5614"], None),
    (("workforce_",), ["5613", "622"], None),

    # Arts / entertainment
    (("arts_", "gaming_", "event_", "creator"), ["711", "713"], None),
    (("sports_rec",), ["7113", "7139"], None),

    # Professional services
    (("legal_", "trademark", "patent_type", "copyright", "trade_secret", "antitrust", "consumer_prot", "sanctions", "export_ctrl", "customs_class", "antitrust_type", "class_action", "arbitrat", "adr", "notary", "corrections", "court_"), ["5411"], None),
    (("law_enforcement",), ["9221"], None),
    (("prof_", "professional"), ["5411", "5412", "5416"], None),
    (("accounting",), ["5412"], None),
    (("advertising", "marketing", "advertising_mktg"), ["5418"], None),

    # Public admin / government
    (("public_", "gov_contract", "grant_type", "municipal_", "emergency_svc"), ["921", "922", "924"], None),

    # Other / specialty
    (("other_",), ["8131"], None),
    (("nonprofit",), ["8131", "6241"], None),
    (("childcare", "early_ed"), ["6244"], None),
    (("senior_care",), ["6231"], None),
    (("tourism", "travel"), ["5615"], None),
    (("wine", "spirits"), ["3121", "4248"], None),
    (("waste_",), ["5621", "5622"], None),
    (("water_env", "water_eco", "water_reg"), ["2213", "5629"], None),
    (("supply_", "logistics", "freight_class", "incoterm", "free_trade"), ["488", "493"], None),
    (("space_", "defence_", "defense_"), ["3364", "5415"], None),
    (("climate_",), ["5417", "2211"], None),
    (("quantum",), ["5415", "3344"], None),
    (("robotics",), ["3333", "5415"], None),
    (("pet_", "animal_care"), ["8129", "1152"], None),
    (("sharing_econ", "circular_econ"), ["5615", "5621"], None),
    (("coworking",), ["5311", "5321"], None),
    (("info_", "media_"), ["51", "515"], None),
    (("regtech", "insurtech", "healthtech", "cleantech", "legaltech"), ["5415"], None),

    # Compliance / frameworks (weak anchors)
    (("iso_", "gdpr_", "hipaa", "sox", "glba", "ferpa", "coppa", "fcra", "ada", "osha", "nerc", "fisma", "fedramp", "ccpa", "cfpb", "sec_", "finra", "far_", "dfars", "itar", "ear_", "clean_air", "clean_water", "cercla", "rcra", "tsca", "pci_dss", "soc2", "hitrust", "cmmc", "nist", "cis_", "cobit", "coso", "ffiec", "ftc_", "naic_", "gaap", "fasb", "pcaob", "aicpa", "joint_commission", "cap_accred", "clia", "fda_", "dea_", "usp_", "ashrae", "ansi", "dora", "nis2", "eu_ai", "eprivacy", "mifid", "solvency", "psd2", "reach_", "rohs", "mdr_", "ivdr", "whistle", "csrd", "cbam", "weee", "eu_pack", "eu_batt", "sfdr", "eu_defor", "dsa_", "dma_", "cyber_resil", "eu_data", "eu_mach", "emas"), ["5416"], "weak_anchor"),

    # Last resort domain anchors by sector-y prefix
    (("defense_", "defence_"), ["3364", "5415"], None),
]


# Explicit overrides for any domain ID that doesn't cleanly fit the rules
EXPLICIT: dict[str, dict] = {
    "domain_naics_truck": {"naics": ["484"]},
    "domain_naics_ag": {"naics": ["111"]},
    "domain_naics_mining": {"naics": ["212"]},
    "domain_naics_util": {"naics": ["2211"]},
    "domain_naics_const": {"naics": ["236", "237", "238"]},
}


def assign_anchors(domain_id: str) -> tuple[list[str], str | None]:
    """Return (naics_anchor_codes, note) for a domain system id.

    Strips the leading 'domain_' prefix, then matches against RULES in order.
    """
    if domain_id in EXPLICIT:
        e = EXPLICIT[domain_id]
        return e["naics"], e.get("note")

    stem = domain_id.removeprefix("domain_").lower()

    for substrings, naics, note in RULES:
        for sub in substrings:
            if sub in stem:
                return naics, note

    return ["5419"], "weak_anchor"


async def main() -> None:
    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn, statement_cache_size=0)
    try:
        rows = await conn.fetch(
            "SELECT id FROM classification_system WHERE id LIKE 'domain_%' ORDER BY id"
        )
    finally:
        await conn.close()

    anchors: dict[str, dict] = {}
    weak_count = 0
    for r in rows:
        did = r["id"]
        naics_list, note = assign_anchors(did)
        entry: dict = {"naics": naics_list}
        if note:
            entry["note"] = note
            weak_count += 1
        anchors[did] = entry

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(anchors, indent=2, sort_keys=True) + "\n")

    total = len(anchors)
    print(f"Wrote {OUT_PATH}")
    print(f"  Total domains: {total}")
    print(f"  Weak anchors (flagged for review): {weak_count}")
    print(f"  Clean anchors: {total - weak_count}")


if __name__ == "__main__":
    asyncio.run(main())
