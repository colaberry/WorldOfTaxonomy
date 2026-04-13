"""Biotechnology and Genomics domain taxonomy ingester.

Organizes biotechnology and genomics sector types aligned with
NAICS 5417 (R&D), NAICS 3254 (Pharmaceutical mfg),
and NAICS 3391 (Medical device mfg).

Code prefix: dbt_
Categories: drug discovery, biomanufacturing, genomics, cell/gene therapy,
diagnostics, ag-biotech, industrial biotech.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
BIOTECH_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Drug Discovery --
    ("dbt_drug",            "Drug Discovery",                                        1, None),
    ("dbt_drug_target",     "Target Identification and Validation",                  2, "dbt_drug"),
    ("dbt_drug_screen",     "High-Throughput Screening (HTS) and Hit-to-Lead",      2, "dbt_drug"),
    ("dbt_drug_opt",        "Lead Optimization and Medicinal Chemistry",             2, "dbt_drug"),

    # -- Biomanufacturing --
    ("dbt_mfg",             "Biomanufacturing",                                      1, None),
    ("dbt_mfg_upstream",    "Upstream Processing (cell culture, fermentation)",      2, "dbt_mfg"),
    ("dbt_mfg_downstream",  "Downstream Processing (purification, filtration)",      2, "dbt_mfg"),
    ("dbt_mfg_fill",        "Fill-Finish and Packaging (aseptic fill, lyophilization)",2, "dbt_mfg"),

    # -- Genomics and Sequencing --
    ("dbt_gen",             "Genomics and Sequencing",                               1, None),
    ("dbt_gen_seq",         "DNA/RNA Sequencing (NGS, long-read, single-cell)",      2, "dbt_gen"),
    ("dbt_gen_assemble",    "Genome Assembly and Annotation",                        2, "dbt_gen"),
    ("dbt_gen_inform",      "Bioinformatics and Computational Biology",              2, "dbt_gen"),

    # -- Cell and Gene Therapy --
    ("dbt_cgt",             "Cell and Gene Therapy",                                 1, None),
    ("dbt_cgt_cart",        "CAR-T and TCR-T Cell Therapy",                         2, "dbt_cgt"),
    ("dbt_cgt_edit",        "Gene Editing (CRISPR, ZFN, TALEN)",                    2, "dbt_cgt"),
    ("dbt_cgt_vector",      "Viral Vectors (AAV, lentiviral, adenoviral)",           2, "dbt_cgt"),

    # -- Diagnostics --
    ("dbt_diag",            "Diagnostics",                                           1, None),
    ("dbt_diag_mol",        "Molecular Diagnostics (PCR, NGS-based, digital PCR)",  2, "dbt_diag"),
    ("dbt_diag_immuno",     "Immunoassay Diagnostics (ELISA, lateral flow, LFA)",   2, "dbt_diag"),
    ("dbt_diag_poc",        "Point-of-Care Diagnostics (rapid tests, wearables)",   2, "dbt_diag"),

    # -- Agricultural Biotechnology --
    ("dbt_ag",              "Agricultural Biotechnology",                            1, None),
    ("dbt_ag_gm",           "Genetically Modified Crops and Trait Stacking",        2, "dbt_ag"),
    ("dbt_ag_biopest",      "Biopesticides and Biocontrol Agents",                  2, "dbt_ag"),

    # -- Industrial Biotechnology --
    ("dbt_ind",             "Industrial Biotechnology",                              1, None),
    ("dbt_ind_enzyme",      "Industrial Enzymes and Biocatalysis",                  2, "dbt_ind"),
    ("dbt_ind_bioplastic",  "Bioplastics and Bio-based Chemicals",                  2, "dbt_ind"),
]

_DOMAIN_ROW = (
    "domain_biotech",
    "Biotechnology and Genomics Types",
    "Drug discovery, biomanufacturing, genomics, cell/gene therapy, "
    "diagnostics, agricultural biotech and industrial biotech taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 5417 (R&D), 3254 (Pharma mfg), 3391 (Medical devices)
_NAICS_PREFIXES = ["5417", "3254", "3391"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific biotech types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_biotech(conn) -> int:
    """Ingest Biotechnology and Genomics domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_biotech'), and links NAICS 5417/3254/3391 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_biotech",
        "Biotechnology and Genomics Types",
        "Drug discovery, biomanufacturing, genomics, cell/gene therapy, "
        "diagnostics, agricultural biotech and industrial biotech taxonomy",
        "1.0",
        "Global",
        "WorldOfTaxanomy",
    )

    await conn.execute(
        """INSERT INTO domain_taxonomy
               (id, name, full_name, authority, url, code_count)
           VALUES ($1, $2, $3, $4, $5, 0)
           ON CONFLICT (id) DO UPDATE SET code_count = 0""",
        *_DOMAIN_ROW,
    )

    parent_codes = {parent for _, _, _, parent in BIOTECH_NODES if parent is not None}

    rows = [
        (
            "domain_biotech",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in BIOTECH_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(BIOTECH_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_biotech'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_biotech'",
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
            [("naics_2022", code, "domain_biotech", "primary") for code in naics_codes],
        )

    return count
