"""Education Funding and Governance Model Types domain taxonomy ingester.

Education funding source and governance model classification - public, private non-profit, for-profit, charter, cooperative.

Code prefix: detfund_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
EDU_FUNDING_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Public and Government-Funded Education --
    ("detfund_public", "Public and Government-Funded Education", 1, None),
    ("detfund_public_k12", "Public K-12 (LEA - Local Education Agency, state funded)", 2, 'detfund_public'),
    ("detfund_public_higher", "Public Higher Education (state university, community college)", 2, 'detfund_public'),
    ("detfund_public_tribal", "Tribal College and Federally-Operated School", 2, 'detfund_public'),
    # -- Private Non-Profit Education Institutions --
    ("detfund_privnp", "Private Non-Profit Education Institutions", 1, None),
    ("detfund_privnp_research", "Private Research University (R1, R2 Carnegie)", 2, 'detfund_privnp'),
    ("detfund_privnp_liberal", "Private Liberal Arts College", 2, 'detfund_privnp'),
    ("detfund_privnp_religious", "Faith-Based and Religious School or College", 2, 'detfund_privnp'),
    # -- For-Profit Education Providers --
    ("detfund_forprofit", "For-Profit Education Providers", 1, None),
    ("detfund_forprofit_corp", "Corporate For-Profit College (University of Phoenix tier)", 2, 'detfund_forprofit'),
    ("detfund_forprofit_bootcamp", "Coding Bootcamp and Vocational For-Profit Program", 2, 'detfund_forprofit'),
    # -- Charter and Alternative Governance Models --
    ("detfund_charter", "Charter and Alternative Governance Models", 1, None),
    ("detfund_charter_school", "Charter School (publicly funded, independently operated)", 2, 'detfund_charter'),
    ("detfund_charter_home", "Home School and Microschool Programs", 2, 'detfund_charter'),
    # -- Corporate and Employer-Funded Training --
    ("detfund_corporate", "Corporate and Employer-Funded Training", 1, None),
    ("detfund_corporate_tuition", "Employer Tuition Assistance Program (TAP)", 2, 'detfund_corporate'),
    ("detfund_corporate_academy", "Corporate Academy and Internal University", 2, 'detfund_corporate'),
    ("detfund_corporate_apprentice", "Registered Apprenticeship and Earn-and-Learn Program", 2, 'detfund_corporate'),
]

_DOMAIN_ROW = (
    "domain_education_funding",
    "Education Funding and Governance Model Types",
    "Education funding source and governance model classification - public, private non-profit, for-profit, charter, cooperative",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['61']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_education_funding(conn) -> int:
    """Ingest Education Funding and Governance Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_education_funding",
        "Education Funding and Governance Model Types",
        "Education funding source and governance model classification - public, private non-profit, for-profit, charter, cooperative",
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

    parent_codes = {parent for _, _, _, parent in EDU_FUNDING_NODES if parent is not None}

    rows = [
        (
            "domain_education_funding",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in EDU_FUNDING_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(EDU_FUNDING_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_education_funding'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_education_funding'",
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
            [("naics_2022", code, "domain_education_funding", "primary") for code in naics_codes],
        )

    return count
