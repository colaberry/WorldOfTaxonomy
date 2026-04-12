"""FMCSA Regulations -> Truck Domain Taxonomies crosswalk ingester.

Links FMCSA regulation nodes to domain truck taxonomy nodes:
  fmcsa_regs -> domain_truck_freight  (regulation -> freight type)
  fmcsa_regs -> domain_truck_cargo    (regulation -> cargo type)
  fmcsa_regs -> domain_truck_vehicle  (regulation -> vehicle class)

All edges use match_type='broad' (regulation governs/applies to the domain concept).
Derived from regulatory scope analysis. Open.
"""
from __future__ import annotations

# (fmcsa_code, fmcsa_system, domain_code, domain_system)
# Each tuple represents: this FMCSA regulation governs/applies to this domain concept
FMCSA_TRUCK_MAPPINGS: list[tuple[str, str, str, str]] = [
    # -- Hours of Service -> Service level (affects all long-haul and OTR operations) --
    ("fmcsa_hos",    "fmcsa_regs", "dtf_svc_longhaul",  "domain_truck_freight"),
    ("fmcsa_hos",    "fmcsa_regs", "dtf_svc_otr",        "domain_truck_freight"),
    ("fmcsa_hos",    "fmcsa_regs", "dtf_svc_regional",   "domain_truck_freight"),
    ("fmcsa_hos_7",  "fmcsa_regs", "dtf_svc_local",      "domain_truck_freight"),
    ("fmcsa_hos_7",  "fmcsa_regs", "dtf_svc_dedicated",  "domain_truck_freight"),
    ("fmcsa_hos",    "fmcsa_regs", "dtf_svc_owner_op",   "domain_truck_freight"),

    # -- ELD Mandate -> Service levels (tracking applies to OTR and regional) --
    ("fmcsa_eld",    "fmcsa_regs", "dtf_svc_longhaul",   "domain_truck_freight"),
    ("fmcsa_eld",    "fmcsa_regs", "dtf_svc_otr",        "domain_truck_freight"),
    ("fmcsa_eld_5",  "fmcsa_regs", "dtf_svc_local",      "domain_truck_freight"),

    # -- CDL -> Vehicle classes (CDL required for Class 8, Class 7+ often) --
    ("fmcsa_cdl",    "fmcsa_regs", "dtv_dot_8",          "domain_truck_vehicle"),
    ("fmcsa_cdl",    "fmcsa_regs", "dtv_dot_7",          "domain_truck_vehicle"),
    ("fmcsa_cdl",    "fmcsa_regs", "dtv_dot_6",          "domain_truck_vehicle"),
    ("fmcsa_cdl_1",  "fmcsa_regs", "dtv_body_semi",      "domain_truck_vehicle"),
    ("fmcsa_cdl_2",  "fmcsa_regs", "dtv_body_tanker",    "domain_truck_vehicle"),
    ("fmcsa_cdl_2",  "fmcsa_regs", "dtv_body_flatbed",   "domain_truck_vehicle"),

    # -- HAZMAT regulations -> Hazmat cargo classes --
    ("fmcsa_hazmat",   "fmcsa_regs", "dtc_haz",   "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_1", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_2", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_3", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_4", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_5", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_6", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_7", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_8", "domain_truck_cargo"),
    ("fmcsa_hazmat_3", "fmcsa_regs", "dtc_haz_9", "domain_truck_cargo"),
    ("fmcsa_hazmat_6", "fmcsa_regs", "dtc_reg_hazmat_pl", "domain_truck_cargo"),
    ("fmcsa_hazmat_2", "fmcsa_regs", "dtc_reg_hazmat_pl", "domain_truck_cargo"),

    # -- Vehicle Inspection -> Body types and vehicle classes --
    ("fmcsa_vim",    "fmcsa_regs", "dtv_dot",            "domain_truck_vehicle"),
    ("fmcsa_vim_9",  "fmcsa_regs", "dtc_hdl_strapping",  "domain_truck_cargo"),
    ("fmcsa_vim_9",  "fmcsa_regs", "dtc_hdl_tarp",       "domain_truck_cargo"),

    # -- Financial Responsibility -> Freight modes --
    ("fmcsa_fr",     "fmcsa_regs", "dtf_mode_ftl",       "domain_truck_freight"),
    ("fmcsa_fr",     "fmcsa_regs", "dtf_mode_ltl",       "domain_truck_freight"),
    ("fmcsa_fr_2",   "fmcsa_regs", "dtf_svc_crossborder","domain_truck_freight"),
    ("fmcsa_fr_5",   "fmcsa_regs", "dtc_com_highvalue",  "domain_truck_cargo"),

    # -- Operating Authority -> Service types --
    ("fmcsa_oa",     "fmcsa_regs", "dtf_svc_dedicated",  "domain_truck_freight"),
    ("fmcsa_oa",     "fmcsa_regs", "dtf_svc_owner_op",   "domain_truck_freight"),
    ("fmcsa_oa_4",   "fmcsa_regs", "dtf_mode_ltl",       "domain_truck_freight"),
    ("fmcsa_oa_5",   "fmcsa_regs", "dtf_mode_intermodal","domain_truck_freight"),

    # -- Carrier Safety Fitness -> all heavy duty operations --
    ("fmcsa_csf",    "fmcsa_regs", "dtv_dot_8",          "domain_truck_vehicle"),
    ("fmcsa_csf",    "fmcsa_regs", "dtv_dot_7",          "domain_truck_vehicle"),
    ("fmcsa_csf",    "fmcsa_regs", "dtf_mode_ftl",       "domain_truck_freight"),
    ("fmcsa_csf",    "fmcsa_regs", "dtf_mode_ltl",       "domain_truck_freight"),

    # -- Accident Reporting -> all freight modes --
    ("fmcsa_ar",     "fmcsa_regs", "dtc_com_general",    "domain_truck_cargo"),
    ("fmcsa_ar",     "fmcsa_regs", "dtf_mode_ftl",       "domain_truck_freight"),
    ("fmcsa_ar",     "fmcsa_regs", "dtf_mode_ltl",       "domain_truck_freight"),

    # -- Drug/Alcohol Testing -> driver operations --
    ("fmcsa_dat",    "fmcsa_regs", "dtf_svc_owner_op",   "domain_truck_freight"),
    ("fmcsa_dat",    "fmcsa_regs", "dtf_svc_dedicated",  "domain_truck_freight"),
    ("fmcsa_dat",    "fmcsa_regs", "dtf_svc_otr",        "domain_truck_freight"),
]


async def ingest_crosswalk_fmcsa_truck(conn) -> int:
    """Ingest FMCSA -> Truck Domain crosswalk edges.

    Inserts into the equivalence table linking fmcsa_regs nodes to
    domain truck taxonomy nodes (freight, cargo, vehicle).
    All edges use match_type='broad'.

    Returns total edge count inserted.
    """
    # Collect valid codes from each system to filter mappings
    fmcsa_codes = {
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = 'fmcsa_regs'"
        )
    }

    domain_systems = {
        "domain_truck_freight": set(),
        "domain_truck_cargo": set(),
        "domain_truck_vehicle": set(),
    }
    for sys_id in domain_systems:
        domain_systems[sys_id] = {
            row["code"]
            for row in await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id = $1", sys_id
            )
        }

    rows = []
    for fmcsa_code, fmcsa_sys, domain_code, domain_sys in FMCSA_TRUCK_MAPPINGS:
        if fmcsa_code not in fmcsa_codes:
            continue
        if domain_code not in domain_systems.get(domain_sys, set()):
            continue
        rows.append((fmcsa_sys, fmcsa_code, domain_sys, domain_code, "broad"))

    await conn.executemany(
        """INSERT INTO equivalence
               (source_system, source_code, target_system, target_code, match_type)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING""",
        rows,
    )

    return len(rows)
