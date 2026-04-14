"""Construction Project Delivery Method domain taxonomy ingester.

Classifies HOW a construction project is contracted and organized -
orthogonal to trade type and building type. The same office tower can be
delivered via design-bid-build with the lowest bidder, a design-build team,
a CM at risk with GMP, or a public-private partnership. The delivery method
determines risk allocation, schedule, cost certainty, and contractor selection.

Code prefix: dcpd_
Categories: Traditional Design-Bid-Build, Design-Build and Integrated
Delivery, Construction Management Models, Public-Private Partnership,
Specialty and Alternative Delivery.

Stakeholders: owners selecting delivery method, construction attorneys
drafting AIA/DBIA contracts, surety bond underwriters, public agency
procurement officers, project finance lenders evaluating risk allocation.
Source: AIA (American Institute of Architects) contract families, DBIA
(Design-Build Institute of America), CMAA (Construction Management
Association of America) standards. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
CONST_DELIVERY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Traditional Design-Bid-Build --
    ("dcpd_dbb",             "Traditional Design-Bid-Build (DBB)",              1, None),
    ("dcpd_dbb_lowbid",      "Low-Bid (public sector price-only selection)",    2, "dcpd_dbb"),
    ("dcpd_dbb_bestvalue",   "Best-Value Selection (price and qualifications)", 2, "dcpd_dbb"),
    ("dcpd_dbb_qbs",         "Qualifications-Based Selection (QBS - Brooks Act)", 2, "dcpd_dbb"),

    # -- Design-Build and Integrated Delivery --
    ("dcpd_db",              "Design-Build (DB) and Integrated Delivery",       1, None),
    ("dcpd_db_lumpsum",      "Lump Sum Design-Build (fixed price, owner risk)", 2, "dcpd_db"),
    ("dcpd_db_bridging",     "Bridging Design-Build (owner design criteria doc)", 2, "dcpd_db"),
    ("dcpd_db_ipd",          "Integrated Project Delivery (IPD - shared risk/reward)", 2, "dcpd_db"),
    ("dcpd_db_epcm",         "EPC/EPCM (Engineering, Procurement, Construction)", 2, "dcpd_db"),

    # -- Construction Management Models --
    ("dcpd_cm",              "Construction Management Models",                   1, None),
    ("dcpd_cm_atrisk",       "CM at Risk (CMR - GMP with open book)",           2, "dcpd_cm"),
    ("dcpd_cm_gmp",          "Guaranteed Maximum Price (GMP) Contract",         2, "dcpd_cm"),
    ("dcpd_cm_agency",       "CM as Agent (owner's rep, no financial risk)",    2, "dcpd_cm"),
    ("dcpd_cm_multiPrime",   "Multiple Prime Contracts (owner holds all subs)", 2, "dcpd_cm"),

    # -- Public-Private Partnership --
    ("dcpd_p3",              "Public-Private Partnership (P3)",                  1, None),
    ("dcpd_p3_dbfom",        "DBFOM (Design-Build-Finance-Operate-Maintain)",   2, "dcpd_p3"),
    ("dcpd_p3_dbf",          "DBF (Design-Build-Finance - public operations)",  2, "dcpd_p3"),
    ("dcpd_p3_availability", "Availability Payment P3 (service payment model)", 2, "dcpd_p3"),

    # -- Specialty and Alternative Delivery --
    ("dcpd_alt",             "Specialty and Alternative Delivery Methods",       1, None),
    ("dcpd_alt_joc",         "Job Order Contracting (JOC - indefinite delivery)", 2, "dcpd_alt"),
    ("dcpd_alt_idiq",        "IDIQ / MATOC (indefinite delivery, multiple award)", 2, "dcpd_alt"),
    ("dcpd_alt_modular",     "Modular and Prefabricated Off-Site Construction", 2, "dcpd_alt"),
]

_DOMAIN_ROW = (
    "domain_const_delivery",
    "Construction Project Delivery Method Types",
    "Construction project delivery method classification - design-bid-build, "
    "design-build, CM at risk, public-private partnership, and alternative delivery",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["23"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific delivery method types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_const_delivery(conn) -> int:
    """Ingest Construction Project Delivery Method domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_const_delivery'), and links NAICS 23 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_const_delivery",
        "Construction Project Delivery Method Types",
        "Construction project delivery method classification - design-bid-build, "
        "design-build, CM at risk, public-private partnership, and alternative delivery",
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

    parent_codes = {parent for _, _, _, parent in CONST_DELIVERY_NODES if parent is not None}

    rows = [
        (
            "domain_const_delivery",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in CONST_DELIVERY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(CONST_DELIVERY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_const_delivery'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_const_delivery'",
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
            [("naics_2022", code, "domain_const_delivery", "primary") for code in naics_codes],
        )

    return count
