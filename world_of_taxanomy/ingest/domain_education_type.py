"""Education Type domain taxonomy ingester.

Education taxonomy organizes program types (NAICS 61):
  Program Type     (det_prog*)     - K-12, higher ed, vocational, continuing ed, early childhood
  Delivery Mode    (det_delivery*) - in-person, online, hybrid, self-paced
  Credential Level (det_cred*)     - certificate, associate, bachelor, master, doctoral
  Accreditation    (det_accred*)   - regional, national, programmatic, international

Source: NCES (National Center for Education Statistics) + NAICS 61 subsectors.
Public domain. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
EDUCATION_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Program Type category --
    ("det_prog",          "Education Program Type",                              1, None),
    ("det_prog_k12",      "K-12 Primary and Secondary Education",              2, "det_prog"),
    ("det_prog_higher",   "Higher Education (college and university)",         2, "det_prog"),
    ("det_prog_voc",      "Vocational and Technical Training (CTE, trade)",    2, "det_prog"),
    ("det_prog_cont",     "Continuing Education and Professional Development", 2, "det_prog"),
    ("det_prog_early",    "Early Childhood Education (pre-K, daycare, Head Start)",2, "det_prog"),
    ("det_prog_special",  "Special Education and Remedial Programs",           2, "det_prog"),

    # -- Delivery Mode category --
    ("det_delivery",         "Instructional Delivery Mode",                     1, None),
    ("det_delivery_inperson","In-Person and Campus-Based Instruction",         2, "det_delivery"),
    ("det_delivery_online",  "Online and Distance Learning (asynchronous)",    2, "det_delivery"),
    ("det_delivery_hybrid",  "Hybrid and Blended Learning",                    2, "det_delivery"),
    ("det_delivery_selfpace","Self-Paced and Competency-Based Education",      2, "det_delivery"),

    # -- Credential Level category --
    ("det_cred",           "Credential and Degree Level",                       1, None),
    ("det_cred_cert",      "Certificate and Diploma (non-degree, short-term)", 2, "det_cred"),
    ("det_cred_assoc",     "Associate Degree (2-year)",                        2, "det_cred"),
    ("det_cred_degree",    "Bachelor Degree (4-year undergraduate)",           2, "det_cred"),
    ("det_cred_grad",      "Graduate Degree (master, professional)",           2, "det_cred"),
    ("det_cred_doctoral",  "Doctoral Degree (PhD, EdD, professional doctorate)",2, "det_cred"),

    # -- Accreditation category --
    ("det_accred",           "Accreditation Type",                              1, None),
    ("det_accred_regional",  "Regional Accreditation (HLC, SACSCOC, WASC)",   2, "det_accred"),
    ("det_accred_national",  "National Accreditation (DEAC, ACICS)",           2, "det_accred"),
    ("det_accred_prog",      "Programmatic Accreditation (ABET, ABA, LCME)",  2, "det_accred"),
]

_DOMAIN_ROW = (
    "domain_education_type",
    "Education Program Types",
    "Program type, delivery mode, credential level and accreditation taxonomy for NAICS 61",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["61"]


def _determine_level(code: str) -> int:
    """Return level: 1 for top categories, 2 for specific education types."""
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


async def ingest_domain_education_type(conn) -> int:
    """Ingest Education Type domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_education_type'), and links NAICS 61xxx nodes
    via node_taxonomy_link.

    Returns total education type node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_education_type",
        "Education Program Types",
        "Program type, delivery mode, credential level and accreditation taxonomy for NAICS 61",
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

    parent_codes = {parent for _, _, _, parent in EDUCATION_NODES if parent is not None}

    rows = [
        (
            "domain_education_type",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in EDUCATION_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(EDUCATION_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_education_type'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_education_type'",
        count,
    )

    naics_codes = [
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE '61%'"
        )
    ]

    await conn.executemany(
        """INSERT INTO node_taxonomy_link
               (system_id, node_code, taxonomy_id, relevance)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
        [("naics_2022", code, "domain_education_type", "primary") for code in naics_codes],
    )

    return count
