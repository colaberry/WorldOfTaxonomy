"""Agricultural Post-harvest and Value Chain Processing domain taxonomy ingester.

Classifies what happens to farm output AFTER it leaves the field - orthogonal
to crop type, farming method, and market channel. The same corn bushel can go
to an on-farm bin, a commercial elevator, wet mill, dry mill, ethanol plant,
or export terminal - each step adding value and changing the regulatory and
logistical requirements.

Code prefix: daph_
Categories: On-Farm Storage, Commercial Storage and Handling, Primary
Processing, Secondary and Value-Added Processing, Cold Chain and Perishable
Handling, Packaging and Labeling, Traceability and Certification.

Stakeholders: food processors, grain merchandisers, cold chain logistics
providers, USDA FSIS/AMS inspection staff, retailers requiring supply chain
transparency, carbon offset registries tracking stored carbon.
Source: USDA AMS, USDA NASS grain storage surveys, FDA FSMA Rule 204,
GS1 traceability standards. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_POSTHARVEST_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- On-Farm Storage --
    ("daph_storage",          "On-Farm Storage",                                      1, None),
    ("daph_storage_bin",      "On-Farm Grain Bin (steel, hopper-bottom, flat-bottom)", 2, "daph_storage"),
    ("daph_storage_bag",      "Grain Bag Storage (temporary field storage)",          2, "daph_storage"),
    ("daph_storage_hay",      "Hay and Forage Storage (stack, shed, wrapped bale)",   2, "daph_storage"),
    ("daph_storage_root",     "Root Cellar and Controlled Atmosphere Storage",        2, "daph_storage"),

    # -- Commercial Storage and Handling --
    ("daph_commercial",       "Commercial Storage and Handling",                       1, None),
    ("daph_commercial_elev",  "Commercial Grain Elevator and Terminal",               2, "daph_commercial"),
    ("daph_commercial_silo",  "Commercial Silo and Flat Storage Facility",            2, "daph_commercial"),
    ("daph_commercial_cold",  "Public Refrigerated Warehouse (PRW)",                  2, "daph_commercial"),
    ("daph_commercial_pack",  "Packing House and Fresh Market Prep Facility",         2, "daph_commercial"),

    # -- Primary Processing --
    ("daph_primary",          "Primary Processing",                                    1, None),
    ("daph_primary_mill",     "Grain Milling (flour, cornmeal, semolina)",            2, "daph_primary"),
    ("daph_primary_crush",    "Oilseed Crush (soybean, canola, sunflower)",           2, "daph_primary"),
    ("daph_primary_ethanol",  "Dry-Mill Ethanol Plant (corn starch to ethanol)",      2, "daph_primary"),
    ("daph_primary_wetmill",  "Wet Milling (corn syrup, starch, gluten feed)",        2, "daph_primary"),
    ("daph_primary_slaughter","Livestock Slaughter and Harvest (USDA FSIS inspected)", 2, "daph_primary"),
    ("daph_primary_ginning",  "Cotton Ginning (lint separation, bale press)",         2, "daph_primary"),

    # -- Secondary and Value-Added Processing --
    ("daph_valueadd",         "Secondary and Value-Added Processing",                  1, None),
    ("daph_valueadd_food",    "Human Food Manufacturing (canning, freezing, baking)", 2, "daph_valueadd"),
    ("daph_valueadd_feed",    "Animal Feed Manufacturing (premix, pelleting)",        2, "daph_valueadd"),
    ("daph_valueadd_biorefine","Biorefinery and Industrial Use (plastics, chemicals)", 2, "daph_valueadd"),
    ("daph_valueadd_beverage","Beverage Processing (juice, beer, spirits)",           2, "daph_valueadd"),
    ("daph_valueadd_render",  "Rendering and By-Product Processing",                  2, "daph_valueadd"),

    # -- Cold Chain and Perishable Handling --
    ("daph_cold",             "Cold Chain and Perishable Handling",                    1, None),
    ("daph_cold_reefer",      "Refrigerated Transport (reefer truck, rail car)",      2, "daph_cold"),
    ("daph_cold_blast",       "Blast Freezing and Quick Freeze Processing",           2, "daph_cold"),
    ("daph_cold_ca",          "Controlled Atmosphere (CA) Storage (apples, pears)",   2, "daph_cold"),
    ("daph_cold_fresh",       "Fresh-Cut and Minimally Processed Produce",            2, "daph_cold"),

    # -- Packaging and Labeling --
    ("daph_pack",             "Packaging and Labeling",                                1, None),
    ("daph_pack_bulk",        "Bulk Commodity Packaging (railcar, hopper, flexi-bag)", 2, "daph_pack"),
    ("daph_pack_consumer",    "Consumer Unit Packaging (retail bags, clamshells)",    2, "daph_pack"),
    ("daph_pack_organic",     "Certified Organic Label and Handling Protocol",        2, "daph_pack"),
    ("daph_pack_trace",       "GS1 / Barcode and RFID Traceability Labeling",        2, "daph_pack"),

    # -- Traceability and Certification --
    ("daph_trace",            "Traceability and Certification Systems",                1, None),
    ("daph_trace_fsma204",    "FSMA Section 204 Food Traceability Record Keeping",   2, "daph_trace"),
    ("daph_trace_gs1",        "GS1 Global Traceability Standard (GTSv2)",            2, "daph_trace"),
    ("daph_trace_carbon",     "Scope 3 Carbon and Sustainability Audit Trail",       2, "daph_trace"),
]

_DOMAIN_ROW = (
    "domain_ag_postharvest",
    "Agricultural Post-harvest Processing Types",
    "Agricultural post-harvest and value chain processing classification - on-farm "
    "storage, commercial handling, primary processing, value-added, cold chain, "
    "packaging, and traceability",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific post-harvest processing types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_postharvest(conn) -> int:
    """Ingest Agricultural Post-harvest Processing domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_postharvest'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_postharvest",
        "Agricultural Post-harvest Processing Types",
        "Agricultural post-harvest and value chain processing classification - on-farm "
        "storage, commercial handling, primary processing, value-added, cold chain, "
        "packaging, and traceability",
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

    parent_codes = {parent for _, _, _, parent in AG_POSTHARVEST_NODES if parent is not None}

    rows = [
        (
            "domain_ag_postharvest",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_POSTHARVEST_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_POSTHARVEST_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_postharvest'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_postharvest'",
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
            [("naics_2022", code, "domain_ag_postharvest", "primary") for code in naics_codes],
        )

    return count
