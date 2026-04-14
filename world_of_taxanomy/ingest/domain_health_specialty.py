"""Healthcare Clinical Specialty and Service Line Types domain taxonomy ingester.

Healthcare clinical specialty and service line classification - cardiac, oncology, orthopedic, neurology, women's health, primary care.

Code prefix: dhssl_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
HEALTH_SPECIALTY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Cardiovascular Service Line --
    ("dhssl_cardiac", "Cardiovascular Service Line", 1, None),
    ("dhssl_cardiac_intervention", "Interventional Cardiology (cath lab, PCI, TAVR)", 2, 'dhssl_cardiac'),
    ("dhssl_cardiac_surgery", "Cardiac Surgery (CABG, valve, LVAD, transplant)", 2, 'dhssl_cardiac'),
    ("dhssl_cardiac_ep", "Electrophysiology (ablation, device implant, heart failure)", 2, 'dhssl_cardiac'),
    # -- Oncology Service Line --
    ("dhssl_onco", "Oncology Service Line", 1, None),
    ("dhssl_onco_med", "Medical Oncology (chemotherapy, immunotherapy, targeted)", 2, 'dhssl_onco'),
    ("dhssl_onco_rad", "Radiation Oncology (EBRT, SBRT, brachytherapy)", 2, 'dhssl_onco'),
    ("dhssl_onco_surgical", "Surgical Oncology (tumor resection, minimally invasive)", 2, 'dhssl_onco'),
    # -- Orthopedic and Musculoskeletal Service Line --
    ("dhssl_ortho", "Orthopedic and Musculoskeletal Service Line", 1, None),
    ("dhssl_ortho_joint", "Total Joint Replacement (hip, knee, shoulder arthroplasty)", 2, 'dhssl_ortho'),
    ("dhssl_ortho_spine", "Spine Surgery (lumbar, cervical, fusion, decompression)", 2, 'dhssl_ortho'),
    ("dhssl_ortho_sports", "Sports Medicine and Arthroscopic Surgery", 2, 'dhssl_ortho'),
    # -- Neuroscience and Behavioral Health Service Line --
    ("dhssl_neuro", "Neuroscience and Behavioral Health Service Line", 1, None),
    ("dhssl_neuro_stroke", "Comprehensive Stroke Center (IV tPA, thrombectomy)", 2, 'dhssl_neuro'),
    ("dhssl_neuro_psych", "Inpatient Psychiatric and Behavioral Health", 2, 'dhssl_neuro'),
    # -- Primary and Preventive Care --
    ("dhssl_primary", "Primary and Preventive Care", 1, None),
    ("dhssl_primary_pcp", "Primary Care / Family Medicine Practice", 2, 'dhssl_primary'),
    ("dhssl_primary_women", "Women's Health and OB/GYN Service Line", 2, 'dhssl_primary'),
    ("dhssl_primary_peds", "Pediatrics and Children's Health Service Line", 2, 'dhssl_primary'),
    ("dhssl_primary_geriatric", "Geriatrics and Senior Health Service Line", 2, 'dhssl_primary'),
]

_DOMAIN_ROW = (
    "domain_health_specialty",
    "Healthcare Clinical Specialty and Service Line Types",
    "Healthcare clinical specialty and service line classification - cardiac, oncology, orthopedic, neurology, women's health, primary care",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['62']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_health_specialty(conn) -> int:
    """Ingest Healthcare Clinical Specialty and Service Line Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_health_specialty",
        "Healthcare Clinical Specialty and Service Line Types",
        "Healthcare clinical specialty and service line classification - cardiac, oncology, orthopedic, neurology, women's health, primary care",
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

    parent_codes = {parent for _, _, _, parent in HEALTH_SPECIALTY_NODES if parent is not None}

    rows = [
        (
            "domain_health_specialty",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in HEALTH_SPECIALTY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(HEALTH_SPECIALTY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_health_specialty'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_health_specialty'",
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
            [("naics_2022", code, "domain_health_specialty", "primary") for code in naics_codes],
        )

    return count
