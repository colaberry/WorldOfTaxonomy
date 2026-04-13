"""Other Services domain taxonomy ingester.

Other services taxonomy organizes service categories (NAICS 81):
  Service Category    (dos_cat*)     - repair, personal care, religious, civic, pet services
  Customer Segment    (dos_segment*) - consumer, business, institutional, community
  Appointment Model   (dos_appt*)    - appointment, walk-in, mobile, subscription
  Certification Body  (dos_cert*)    - licensed, certified, bonded, insured, franchise

Source: NAICS 81 subsectors + SBA small business service classifications.
Public domain. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
OTHER_SVC_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Service Category --
    ("dos_cat",           "Other Service Category",                              1, None),
    ("dos_cat_repair",    "Repair and Maintenance (auto, appliance, electronics)",2, "dos_cat"),
    ("dos_cat_personal",  "Personal Care Services (hair, nail, spa, laundry)",  2, "dos_cat"),
    ("dos_cat_religious", "Religious, Civic and Membership Organizations",      2, "dos_cat"),
    ("dos_cat_pet",       "Pet Care and Veterinary Support Services",           2, "dos_cat"),
    ("dos_cat_funeral",   "Funeral, Cemetery and Death-Care Services",          2, "dos_cat"),

    # -- Customer Segment --
    ("dos_segment",          "Customer Segment",                                 1, None),
    ("dos_segment_consumer", "Consumer and Household Client",                  2, "dos_segment"),
    ("dos_segment_biz",      "Small Business Client",                          2, "dos_segment"),
    ("dos_segment_inst",     "Institutional Client (school, govt, non-profit)",2, "dos_segment"),
    ("dos_segment_community","Community and Membership Organization",          2, "dos_segment"),

    # -- Appointment Model --
    ("dos_appt",          "Service Delivery and Appointment Model",             1, None),
    ("dos_appt_scheduled","Scheduled Appointment (advance booking required)",  2, "dos_appt"),
    ("dos_appt_walkin",   "Walk-In and On-Demand Service",                     2, "dos_appt"),
    ("dos_appt_mobile",   "Mobile and On-Site Service (technician dispatch)",  2, "dos_appt"),
    ("dos_appt_sub",      "Subscription and Membership Service Plan",          2, "dos_appt"),

    # -- Certification and Compliance --
    ("dos_cert",           "Certification and Compliance Status",               1, None),
    ("dos_cert_licensed",  "Licensed by State or Local Regulatory Body",       2, "dos_cert"),
    ("dos_cert_certified", "Professionally Certified (industry association)",  2, "dos_cert"),
    ("dos_cert_bonded",    "Bonded and Insured (contractor surety bond)",       2, "dos_cert"),
    ("dos_cert_franchise", "Franchise and Licensed Brand Operator",            2, "dos_cert"),
]

_DOMAIN_ROW = (
    "domain_other_services",
    "Other Services Types",
    "Service category, customer segment, appointment model and certification taxonomy for NAICS 81",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["81"]


def _determine_level(code: str) -> int:
    """Return level: 1 for top categories, 2 for specific service types."""
    parts = code.split("_")
    if len(parts) == 2:
        return 1
    return 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_other_services(conn) -> int:
    """Ingest Other Services domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_other_services'), and links NAICS 81xxx nodes
    via node_taxonomy_link.

    Returns total other service node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_other_services",
        "Other Services Types",
        "Service category, customer segment, appointment model and certification taxonomy for NAICS 81",
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

    parent_codes = {parent for _, _, _, parent in OTHER_SVC_NODES if parent is not None}

    rows = [
        (
            "domain_other_services",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in OTHER_SVC_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(OTHER_SVC_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_other_services'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_other_services'",
        count,
    )

    naics_codes = [
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE '81%'"
        )
    ]

    await conn.executemany(
        """INSERT INTO node_taxonomy_link
               (system_id, node_code, taxonomy_id, relevance)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
        [("naics_2022", code, "domain_other_services", "primary") for code in naics_codes],
    )

    return count
