"""Truck Technology / Digitization Level domain taxonomy ingester.

Classifies how freight operations are digitized and automated - orthogonal to
freight mode, vehicle class, cargo type, carrier ops, pricing, regulatory,
and lane geography. A carrier can operate an FTL dry van with Class A CDL
using only paper logs and phone brokerage, or the same load on a fully
TMS-integrated, ELD-tracked, API-connected digital freight platform.

Code prefix: dtt_
Categories: Load Booking/Matching, TMS Maturity, Fleet Telematics,
Automation/Autonomy Level, Digital Documentation.

Stakeholders: technology vendors, shippers assessing carrier digital maturity,
logistics investors, fleet managers, autonomous vehicle developers.
Source: FMCSA ELD adoption data, ATA Technology & Maintenance Council,
DAT/Truckstop market surveys, SAE J3016 automation levels. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
TECH_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Load Booking and Matching --
    ("dtt_book",          "Load Booking and Matching Method",                     1, None),
    ("dtt_book_manual",   "Manual / Phone and Email Brokerage",                   2, "dtt_book"),
    ("dtt_book_board",    "Load Board Posting (DAT, Truckstop, 123Loadboard)",    2, "dtt_book"),
    ("dtt_book_dfm",      "Digital Freight Matching (Uber Freight, Convoy, Loadsmart)", 2, "dtt_book"),
    ("dtt_book_api",      "API-Integrated Direct Shipper-Carrier Connection",     2, "dtt_book"),
    ("dtt_book_spot",     "Automated Spot Market Bidding (algorithmic pricing)",  2, "dtt_book"),
    ("dtt_book_auction",  "Reverse Auction / RFP Procurement Platform",           2, "dtt_book"),

    # -- Transportation Management System (TMS) Maturity --
    ("dtt_tms",           "Transportation Management System (TMS) Maturity",      1, None),
    ("dtt_tms_none",      "No TMS (manual dispatch, spreadsheet-based)",          2, "dtt_tms"),
    ("dtt_tms_basic",     "Basic TMS (dispatch and billing only)",                2, "dtt_tms"),
    ("dtt_tms_full",      "Full-Suite TMS (optimization, visibility, analytics)", 2, "dtt_tms"),
    ("dtt_tms_cloud",     "Cloud-Based SaaS TMS (McLeod, TMW, Samsara TMS)",     2, "dtt_tms"),
    ("dtt_tms_erp",       "ERP-Integrated TMS (SAP TM, Oracle OTM)",             2, "dtt_tms"),

    # -- Fleet Telematics and Monitoring --
    ("dtt_telem",         "Fleet Telematics and Monitoring",                      1, None),
    ("dtt_telem_gps",     "GPS Tracking and Location (basic position reporting)", 2, "dtt_telem"),
    ("dtt_telem_eld",     "ELD Telematics (HOS + real-time location combined)",   2, "dtt_telem"),
    ("dtt_telem_dash",    "Dashcam and Video Safety System (AI event detection)", 2, "dtt_telem"),
    ("dtt_telem_perf",    "Driver Performance Monitoring (ADAS coaching, scorecards)", 2, "dtt_telem"),
    ("dtt_telem_asset",   "Asset and Cargo Tracking (trailer, temp, door sensors)", 2, "dtt_telem"),
    ("dtt_telem_predict", "Predictive Maintenance Telematics (OBD diagnostics)",  2, "dtt_telem"),

    # -- Automation and Autonomy Level --
    ("dtt_auto",          "Automation and Autonomy Level",                        1, None),
    ("dtt_auto_none",     "No Automation (fully manual driver operation)",        2, "dtt_auto"),
    ("dtt_auto_adas",     "ADAS Safety Features (collision alert, lane departure, AEB)", 2, "dtt_auto"),
    ("dtt_auto_partial",  "Partial Automation (SAE Level 2-3, driver supervised)", 2, "dtt_auto"),
    ("dtt_auto_platooning", "Automated Truck Platooning (SAE Level 2, convoy tech)", 2, "dtt_auto"),
    ("dtt_auto_av",       "Autonomous Vehicle Operation (SAE Level 4, geofenced)", 2, "dtt_auto"),

    # -- Digital Documentation and Compliance --
    ("dtt_doc",           "Digital Documentation and Compliance",                 1, None),
    ("dtt_doc_paper",     "Paper Documents (BOL, POD, paper logbook)",            2, "dtt_doc"),
    ("dtt_doc_ebol",      "Electronic Bill of Lading (eBOL)",                    2, "dtt_doc"),
    ("dtt_doc_epod",      "Electronic Proof of Delivery (ePOD, signature capture)", 2, "dtt_doc"),
    ("dtt_doc_edi",       "EDI Data Exchange (EDI 204/210/214 standards)",        2, "dtt_doc"),
    ("dtt_doc_api",       "API-Based Real-Time Data Exchange (REST/JSON)",        2, "dtt_doc"),
    ("dtt_doc_blockchain","Blockchain-Based Document and Chain-of-Custody",       2, "dtt_doc"),
]

_DOMAIN_ROW = (
    "domain_truck_tech",
    "Truck Technology and Digitization Levels",
    "Classifies how truck freight operations are digitized and automated: load booking, "
    "TMS maturity, fleet telematics, automation level, and digital documentation",
    "WorldOfTaxanomy",
    None,
)

# NAICS 484: Truck Transportation (all sub-sectors)
_NAICS_PREFIXES = ["484"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories (dtt_xxx), 2 for specific types (dtt_xxx_yyy)."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_truck_tech(conn) -> int:
    """Ingest Truck Technology / Digitization Level domain taxonomy.

    Registers in classification_system and domain_taxonomy, stores nodes
    in classification_node (system_id='domain_truck_tech'), and links
    all NAICS 484xxx nodes via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_truck_tech",
        "Truck Technology and Digitization Levels",
        "Classifies how truck freight operations are digitized and automated: load booking, "
        "TMS maturity, fleet telematics, automation level, and digital documentation",
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

    parent_codes = {parent for _, _, _, parent in TECH_NODES if parent is not None}

    rows = [
        (
            "domain_truck_tech",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in TECH_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(TECH_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_truck_tech'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_truck_tech'",
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
            [("naics_2022", code, "domain_truck_tech", "primary") for code in naics_codes],
        )

    return count
