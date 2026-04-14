"""Education Student Demographic Segment Types domain taxonomy ingester.

Education student demographic and learner segment classification.

Code prefix: detseg_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
EDU_SEGMENT_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Traditional College-Age Students (18-24) --
    ("detseg_trad", "Traditional College-Age Students (18-24)", 1, None),
    ("detseg_trad_fulltime", "Full-Time Traditional Residential Students", 2, 'detseg_trad'),
    ("detseg_trad_commuter", "Traditional Commuter Students (non-residential)", 2, 'detseg_trad'),
    # -- Adult and Non-Traditional Learners --
    ("detseg_adult", "Adult and Non-Traditional Learners", 1, None),
    ("detseg_adult_workforce", "Working Adult and Upskilling Learner (25+)", 2, 'detseg_adult'),
    ("detseg_adult_parttimer", "Part-Time Adult Learner (evening, weekend, online)", 2, 'detseg_adult'),
    ("detseg_adult_returning", "Returning Learner (stop-out, career transition)", 2, 'detseg_adult'),
    # -- Professional and Executive Development --
    ("detseg_professional", "Professional and Executive Development", 1, None),
    ("detseg_professional_exec", "Executive Education and MBA Programs", 2, 'detseg_professional'),
    ("detseg_professional_cert", "Professional Certification and CE (CPE, CLE, CME)", 2, 'detseg_professional'),
    # -- K-12 Student Population --
    ("detseg_k12", "K-12 Student Population", 1, None),
    ("detseg_k12_elementary", "Elementary School (K-5)", 2, 'detseg_k12'),
    ("detseg_k12_middle", "Middle School (6-8)", 2, 'detseg_k12'),
    ("detseg_k12_high", "High School (9-12) including dual enrollment", 2, 'detseg_k12'),
    # -- International and ESL/EFL Learners --
    ("detseg_international", "International and ESL/EFL Learners", 1, None),
    ("detseg_international_f1", "F-1 Visa International Students (higher ed)", 2, 'detseg_international'),
    ("detseg_international_esl", "ESL/ELL English Language Learners (domestic)", 2, 'detseg_international'),
    ("detseg_international_remote", "Remote and Online International Learners (cross-border enrollment)", 2, 'detseg_international'),
]

_DOMAIN_ROW = (
    "domain_education_segment",
    "Education Student Demographic Segment Types",
    "Education student demographic and learner segment classification",
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


async def ingest_domain_education_segment(conn) -> int:
    """Ingest Education Student Demographic Segment Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_education_segment",
        "Education Student Demographic Segment Types",
        "Education student demographic and learner segment classification",
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

    parent_codes = {parent for _, _, _, parent in EDU_SEGMENT_NODES if parent is not None}

    rows = [
        (
            "domain_education_segment",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in EDU_SEGMENT_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(EDU_SEGMENT_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_education_segment'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_education_segment'",
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
            [("naics_2022", code, "domain_education_segment", "primary") for code in naics_codes],
        )

    return count
