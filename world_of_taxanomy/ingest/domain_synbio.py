"""Synthetic Biology domain taxonomy ingester.

Organizes synthetic biology sector types aligned with
NAICS 5417 (R&D), NAICS 3254 (Pharmaceutical mfg),
and NAICS 3112 (Grain/oilseed processing).

Code prefix: dsb_
Categories: metabolic engineering, cell-free systems, DNA synthesis,
CRISPR/gene editing, chassis organisms, bioproducts, biosensors.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
SYNBIO_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Metabolic Engineering --
    ("dsb_meta",            "Metabolic Engineering",                                 1, None),
    ("dsb_meta_pathway",    "Metabolic Pathway Engineering and Optimization",        2, "dsb_meta"),
    ("dsb_meta_strain",     "Strain Development and Adaptive Laboratory Evolution", 2, "dsb_meta"),
    ("dsb_meta_model",      "Genome-Scale Metabolic Modeling (COBRA, FBA)",         2, "dsb_meta"),

    # -- Cell-Free Systems --
    ("dsb_cfs",             "Cell-Free Synthetic Biology",                           1, None),
    ("dsb_cfs_txtl",        "Transcription-Translation (TX-TL) Systems",            2, "dsb_cfs"),
    ("dsb_cfs_enzyme",      "Enzymatic Cell-Free Manufacturing",                    2, "dsb_cfs"),
    ("dsb_cfs_proto",       "Protocells and Minimal Cell Systems",                  2, "dsb_cfs"),

    # -- DNA Synthesis and Assembly --
    ("dsb_dna",             "DNA Synthesis and Assembly",                            1, None),
    ("dsb_dna_oligo",       "Oligonucleotide and Gene Synthesis",                   2, "dsb_dna"),
    ("dsb_dna_assemble",    "DNA Assembly Methods (Gibson, Golden Gate, SLIC)",     2, "dsb_dna"),
    ("dsb_dna_genome",      "Genome Writing and Chromosome Engineering",            2, "dsb_dna"),

    # -- CRISPR and Gene Editing --
    ("dsb_crispr",          "CRISPR and Gene Editing Technologies",                  1, None),
    ("dsb_crispr_cas9",     "CRISPR-Cas9 Genome Editing",                           2, "dsb_crispr"),
    ("dsb_crispr_base",     "Base Editing and Prime Editing",                       2, "dsb_crispr"),
    ("dsb_crispr_crispri",  "CRISPRi and CRISPRa (gene regulation)",               2, "dsb_crispr"),

    # -- Chassis Organisms --
    ("dsb_chassis",         "Chassis Organisms and Biological Platforms",            1, None),
    ("dsb_chassis_ecoli",   "Escherichia coli Chassis (industrial workhorse)",      2, "dsb_chassis"),
    ("dsb_chassis_yeast",   "Yeast Chassis (S. cerevisiae, Pichia, Yarrowia)",      2, "dsb_chassis"),
    ("dsb_chassis_mamm",    "Mammalian Cell Chassis (CHO, HEK293, stem cells)",     2, "dsb_chassis"),

    # -- Bioproducts --
    ("dsb_prod",            "Bioproducts and Bio-Based Outputs",                     1, None),
    ("dsb_prod_biofuel",    "Biofuels (cellulosic ethanol, farnesene, isobutanol)", 2, "dsb_prod"),
    ("dsb_prod_biochem",    "Bio-Based Chemicals (succinic acid, muconic acid)",    2, "dsb_prod"),
    ("dsb_prod_meat",       "Cultivated Meat and Precision Fermentation Proteins",  2, "dsb_prod"),
    ("dsb_prod_material",   "Living Materials and Bioplastics (PHA, PLA, mycelium)",2, "dsb_prod"),

    # -- Biosensors --
    ("dsb_sensor",          "Biosensors and Biological Detection",                   1, None),
    ("dsb_sensor_cell",     "Cell-Based Biosensors (reporter strains, whole-cell)", 2, "dsb_sensor"),
    ("dsb_sensor_molec",    "Molecular Biosensors (aptamers, riboswitches, FRET)",  2, "dsb_sensor"),
]

_DOMAIN_ROW = (
    "domain_synbio",
    "Synthetic Biology Types",
    "Metabolic engineering, cell-free systems, DNA synthesis, CRISPR, "
    "chassis organisms, bioproducts and biosensors taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 5417 (R&D), 3254 (Pharma mfg), 3112 (Grain/oilseed processing)
_NAICS_PREFIXES = ["5417", "3254", "3112"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific synbio types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_synbio(conn) -> int:
    """Ingest Synthetic Biology domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_synbio'), and links NAICS 5417/3254/3112 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_synbio",
        "Synthetic Biology Types",
        "Metabolic engineering, cell-free systems, DNA synthesis, CRISPR, "
        "chassis organisms, bioproducts and biosensors taxonomy",
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

    parent_codes = {parent for _, _, _, parent in SYNBIO_NODES if parent is not None}

    rows = [
        (
            "domain_synbio",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in SYNBIO_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(SYNBIO_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_synbio'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_synbio'",
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
            [("naics_2022", code, "domain_synbio", "primary") for code in naics_codes],
        )

    return count
