"""Workforce Safety Training and Certification Program Types domain taxonomy ingester.

Workforce safety training and certification program classification - OSHA, HAZWOPER, specialized equipment, first aid.

Code prefix: dwstrain_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
WORKFORCE_TRAINING_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- OSHA Standard Training Programs --
    ("dwstrain_osha", "OSHA Standard Training Programs", 1, None),
    ("dwstrain_osha_10", "OSHA 10-Hour General Industry or Construction", 2, 'dwstrain_osha'),
    ("dwstrain_osha_30", "OSHA 30-Hour General Industry or Construction", 2, 'dwstrain_osha'),
    ("dwstrain_osha_ppe", "OSHA PPE Selection and Fit Training", 2, 'dwstrain_osha'),
    # -- Hazardous Materials and Emergency Response Training --
    ("dwstrain_hazmat", "Hazardous Materials and Emergency Response Training", 1, None),
    ("dwstrain_hazmat_hazwoper", "HAZWOPER (29 CFR 1910.120) 40-Hour Technician", 2, 'dwstrain_hazmat'),
    ("dwstrain_hazmat_8hr", "HAZWOPER 8-Hour Annual Refresher", 2, 'dwstrain_hazmat'),
    ("dwstrain_hazmat_firstresponder", "First Responder Awareness / Operations Level", 2, 'dwstrain_hazmat'),
    # -- Equipment Operation and Specialty Training --
    ("dwstrain_equipment", "Equipment Operation and Specialty Training", 1, None),
    ("dwstrain_equipment_forklift", "Powered Industrial Truck (Forklift) Operator Training", 2, 'dwstrain_equipment'),
    ("dwstrain_equipment_crane", "Crane and Rigging Operator Certification (NCCCO)", 2, 'dwstrain_equipment'),
    ("dwstrain_equipment_scaffold", "Scaffold Erector and User Training", 2, 'dwstrain_equipment'),
    # -- Emergency Medical and First Aid Training --
    ("dwstrain_medical", "Emergency Medical and First Aid Training", 1, None),
    ("dwstrain_medical_cpr", "CPR and AED Certification (AHA, Red Cross)", 2, 'dwstrain_medical'),
    ("dwstrain_medical_fa", "First Aid and Bloodborne Pathogen Training", 2, 'dwstrain_medical'),
    # -- Industry-Specific Safety Training --
    ("dwstrain_specialized", "Industry-Specific Safety Training", 1, None),
    ("dwstrain_specialized_mining", "MSHA Mining Safety Training (New Miner, Annual Refresher)", 2, 'dwstrain_specialized'),
    ("dwstrain_specialized_confined", "Confined Space Entry and Rescue Training", 2, 'dwstrain_specialized'),
]

_DOMAIN_ROW = (
    "domain_workforce_training",
    "Workforce Safety Training and Certification Program Types",
    "Workforce safety training and certification program classification - OSHA, HAZWOPER, specialized equipment, first aid",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11", "21", "22", "23", "31", "32", "33", "42", "44", "45", "48", "49", "51", "52", "53", "54", "55", "56", "61", "62", "71", "72", "81", "92"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_workforce_training(conn) -> int:
    """Ingest Workforce Safety Training and Certification Program Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_workforce_training",
        "Workforce Safety Training and Certification Program Types",
        "Workforce safety training and certification program classification - OSHA, HAZWOPER, specialized equipment, first aid",
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

    parent_codes = {parent for _, _, _, parent in WORKFORCE_TRAINING_NODES if parent is not None}

    rows = [
        (
            "domain_workforce_training",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in WORKFORCE_TRAINING_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(WORKFORCE_TRAINING_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_workforce_training'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_workforce_training'",
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
            [("naics_2022", code, "domain_workforce_training", "primary") for code in naics_codes],
        )

    return count
