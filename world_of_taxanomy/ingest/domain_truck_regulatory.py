"""Truck Regulatory / Compliance Domains taxonomy ingester.

Classifies the regulatory compliance domains that govern truck operations.
Orthogonal to freight mode, vehicle class, cargo type, carrier ops, pricing,
and lane geography: a carrier may be subject to HOS + ELD + CDL Class A +
hazmat endorsement + CARB emissions + FSMA food transport simultaneously,
each managed by different regulators and compliance systems.

Code prefix: dtr_
Categories: Hours of Service, Electronic Logging, CDL/Licensing,
Hazmat Compliance, Emissions Standards, Food Safety Transport.

Stakeholders: safety directors, compliance officers, DOT/FMCSA auditors,
insurance underwriters, fleet managers, shippers vetting carrier compliance.
Source: 49 CFR Parts 390-399 (FMCSA), 49 CFR Parts 171-180 (hazmat),
EPA 40 CFR Parts 86/1036/1037, CARB ATCM, FDA FSMA 21 CFR Part 1. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
REGULATORY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Hours of Service (HOS) --
    ("dtr_hos",           "Hours of Service (HOS) Regulations",                  1, None),
    ("dtr_hos_prop",      "HOS Property-Carrying Rules (11-hr drive / 14-hr on-duty)", 2, "dtr_hos"),
    ("dtr_hos_pass",      "HOS Passenger-Carrying Rules (10-hr drive / 15-hr on-duty)", 2, "dtr_hos"),
    ("dtr_hos_short",     "HOS Short-Haul Exemption (150 air-mile radius)",      2, "dtr_hos"),
    ("dtr_hos_ag",        "HOS Agricultural Exemption (150 air-mile, harvest)",  2, "dtr_hos"),
    ("dtr_hos_adverse",   "HOS Adverse Driving Conditions Exception",            2, "dtr_hos"),
    ("dtr_hos_34hr",      "HOS 34-Hour Restart Provision",                       2, "dtr_hos"),
    ("dtr_hos_sleeper",   "HOS Sleeper Berth Provision (split sleeper)",         2, "dtr_hos"),

    # -- Electronic Logging Device (ELD) --
    ("dtr_eld",           "Electronic Logging Device (ELD) Rules",               1, None),
    ("dtr_eld_mandate",   "ELD Mandate Compliance (FMCSA ELD Rule, 49 CFR 395)", 2, "dtr_eld"),
    ("dtr_eld_exempt",    "ELD Exemptions (short-haul, driveaway-towaway, pre-2000)", 2, "dtr_eld"),
    ("dtr_eld_aobrd",     "AOBRD Legacy (grandfathered Automatic On-Board Recording)", 2, "dtr_eld"),
    ("dtr_eld_paper",     "Paper Logbook (HOS exemption, 8-day/short-haul)",     2, "dtr_eld"),

    # -- Commercial Driver's License / Endorsements --
    ("dtr_cdl",           "Commercial Driver's License (CDL) and Endorsements",  1, None),
    ("dtr_cdl_class_a",   "CDL Class A (combination vehicles > 26,001 lbs GCWR)", 2, "dtr_cdl"),
    ("dtr_cdl_class_b",   "CDL Class B (single vehicle > 26,001 lbs GVWR)",     2, "dtr_cdl"),
    ("dtr_cdl_class_c",   "CDL Class C (hazmat transport / 16+ passengers)",     2, "dtr_cdl"),
    ("dtr_cdl_haz",       "Hazmat Endorsement - H (49 CFR 383.93)",              2, "dtr_cdl"),
    ("dtr_cdl_tank",      "Tank Vehicle Endorsement - N",                        2, "dtr_cdl"),
    ("dtr_cdl_doub",      "Double/Triple Trailer Endorsement - T",               2, "dtr_cdl"),
    ("dtr_cdl_pass",      "Passenger Endorsement - P",                           2, "dtr_cdl"),
    ("dtr_cdl_school",    "School Bus Endorsement - S",                          2, "dtr_cdl"),
    ("dtr_cdl_twic",      "TWIC Card (Transportation Worker ID, port access)",   2, "dtr_cdl"),

    # -- Hazardous Materials (DOT) --
    ("dtr_haz",           "Hazardous Materials Compliance (DOT)",                 1, None),
    ("dtr_haz_49cfr",     "DOT 49 CFR Parts 171-180 Hazmat Regulations",         2, "dtr_haz"),
    ("dtr_haz_placard",   "Hazmat Placard and Marking Requirements",              2, "dtr_haz"),
    ("dtr_haz_train",     "Hazmat Employee Training Requirements (49 CFR 172.700)", 2, "dtr_haz"),
    ("dtr_haz_security",  "Hazmat Security Plan Requirements (49 CFR 172.800)",   2, "dtr_haz"),
    ("dtr_haz_incident",  "Hazmat Incident Reporting (49 CFR 171.15/171.16)",    2, "dtr_haz"),

    # -- Emissions Standards --
    ("dtr_emiss",         "Emissions Standards",                                  1, None),
    ("dtr_emiss_epa",     "EPA Heavy-Duty Emissions Standards (40 CFR 86/1036)", 2, "dtr_emiss"),
    ("dtr_emiss_carb",    "CARB Emissions Standards (CA Advanced Clean Trucks)", 2, "dtr_emiss"),
    ("dtr_emiss_ghg1",    "GHG Phase 1 Truck Standards (MY 2014-2018)",         2, "dtr_emiss"),
    ("dtr_emiss_ghg2",    "GHG Phase 2 Truck Standards (MY 2018+)",             2, "dtr_emiss"),
    ("dtr_emiss_zev",     "Zero Emission Vehicle (ZEV) Mandate Requirements",   2, "dtr_emiss"),
    ("dtr_emiss_idle",    "Anti-Idling Regulations (state / local)",             2, "dtr_emiss"),

    # -- Food Safety Transport --
    ("dtr_food",          "Food Safety Transport Regulations",                    1, None),
    ("dtr_food_fsma",     "FDA FSMA Sanitary Transportation Rule (21 CFR 1.900)", 2, "dtr_food"),
    ("dtr_food_temp",     "Temperature-Controlled Transport Requirements",        2, "dtr_food"),
    ("dtr_food_clean",    "Vehicle Cleaning and Sanitization Requirements",       2, "dtr_food"),
    ("dtr_food_trace",    "Food Traceability Documentation (FSMA Rule 204)",      2, "dtr_food"),
    ("dtr_food_audit",    "Third-Party Food Safety Audit (SQF, BRC, AIB)",       2, "dtr_food"),
]

_DOMAIN_ROW = (
    "domain_truck_regulatory",
    "Truck Regulatory and Compliance Domains",
    "Classifies regulatory compliance domains for truck operations: hours of service, "
    "ELD, CDL/endorsements, hazmat, emissions, and food safety transport",
    "WorldOfTaxanomy",
    None,
)

# NAICS 484: Truck Transportation (all sub-sectors)
_NAICS_PREFIXES = ["484"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories (dtr_xxx), 2 for specific rules (dtr_xxx_yyy)."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_truck_regulatory(conn) -> int:
    """Ingest Truck Regulatory / Compliance Domains taxonomy.

    Registers in classification_system and domain_taxonomy, stores nodes
    in classification_node (system_id='domain_truck_regulatory'), and links
    all NAICS 484xxx nodes via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_truck_regulatory",
        "Truck Regulatory and Compliance Domains",
        "Classifies regulatory compliance domains for truck operations: hours of service, "
        "ELD, CDL/endorsements, hazmat, emissions, and food safety transport",
        "1.0",
        "United States",
        "WorldOfTaxanomy",
    )

    await conn.execute(
        """INSERT INTO domain_taxonomy
               (id, name, full_name, authority, url, code_count)
           VALUES ($1, $2, $3, $4, $5, 0)
           ON CONFLICT (id) DO UPDATE SET code_count = 0""",
        *_DOMAIN_ROW,
    )

    parent_codes = {parent for _, _, _, parent in REGULATORY_NODES if parent is not None}

    rows = [
        (
            "domain_truck_regulatory",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in REGULATORY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(REGULATORY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_truck_regulatory'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_truck_regulatory'",
        count,
    )

    naics_codes = [
        row["code"]
        for prefix in _NAICS_PREFIXES
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE $1",
            prefix + "%",
        )
    ]

    if naics_codes:
        await conn.executemany(
            """INSERT INTO node_taxonomy_link
                   (system_id, node_code, taxonomy_id, relevance)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
            [("naics_2022", code, "domain_truck_regulatory", "primary") for code in naics_codes],
        )

    return count
