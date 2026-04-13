"""Advanced Materials domain taxonomy ingester.

Organizes advanced materials sector types aligned with
NAICS 325 (Chemical mfg), NAICS 327 (Non-metallic mineral products),
and NAICS 3315 (Steel products).

Code prefix: dam_
Categories: composites, biomaterials, smart materials, nanomaterials,
high-performance alloys, ceramics/glass, semiconducting materials, coatings/surfaces.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MATERIALS_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Composites --
    ("dam_comp",            "Composite Materials",                                   1, None),
    ("dam_comp_cfrp",       "Carbon Fiber Reinforced Polymer (CFRP)",               2, "dam_comp"),
    ("dam_comp_gfrp",       "Glass Fiber Reinforced Polymer (GFRP, fiberglass)",    2, "dam_comp"),
    ("dam_comp_mmc",        "Metal Matrix Composites (MMC) and Ceramic Matrix",     2, "dam_comp"),

    # -- Biomaterials --
    ("dam_bio",             "Biomaterials",                                          1, None),
    ("dam_bio_implant",     "Implant Biomaterials (Ti, Co-Cr, UHMWPE, hydroxyapatite)",2, "dam_bio"),
    ("dam_bio_scaffold",    "Tissue Engineering Scaffolds (hydrogels, bioprinted)", 2, "dam_bio"),
    ("dam_bio_drug",        "Drug Delivery Materials (nanoparticles, microspheres)", 2, "dam_bio"),

    # -- Smart Materials --
    ("dam_smart",           "Smart and Functional Materials",                        1, None),
    ("dam_smart_sma",       "Shape Memory Alloys (Nitinol, Cu-Zn-Al, Fe-Mn-Si)",   2, "dam_smart"),
    ("dam_smart_piezo",     "Piezoelectric Materials (PZT, PVDF, BaTiO3)",         2, "dam_smart"),
    ("dam_smart_mag",       "Magnetostrictive and Magnetocaloric Materials",        2, "dam_smart"),

    # -- Nanomaterials --
    ("dam_nano",            "Nanomaterials",                                         1, None),
    ("dam_nano_cnt",        "Carbon Nanotubes and Graphene",                        2, "dam_nano"),
    ("dam_nano_qdot",       "Quantum Dots and Nanoparticles",                       2, "dam_nano"),
    ("dam_nano_nanocomp",   "Nanocomposites and Nanocoatings",                     2, "dam_nano"),

    # -- High-Performance Alloys --
    ("dam_alloy",           "High-Performance Alloys",                               1, None),
    ("dam_alloy_super",     "Superalloys (Inconel, Hastelloy, cobalt-based)",       2, "dam_alloy"),
    ("dam_alloy_ti",        "Titanium and Titanium Alloys (aerospace, medical)",    2, "dam_alloy"),
    ("dam_alloy_hea",       "High-Entropy Alloys (multi-principal element)",        2, "dam_alloy"),

    # -- Ceramics and Glass --
    ("dam_cer",             "Ceramics and Glass",                                    1, None),
    ("dam_cer_tech",        "Technical Ceramics (alumina, zirconia, SiC, Si3N4)",   2, "dam_cer"),
    ("dam_cer_glass",       "Specialty Glass (optical, chemically strengthened)",   2, "dam_cer"),
    ("dam_cer_refract",     "Refractory Materials (high-temp furnace linings)",     2, "dam_cer"),

    # -- Semiconducting Materials --
    ("dam_semi",            "Semiconducting Materials",                              1, None),
    ("dam_semi_wbg",        "Wide-Bandgap Semiconductors (SiC, GaN, diamond)",      2, "dam_semi"),
    ("dam_semi_compound",   "Compound Semiconductors (GaAs, InP, InGaN)",           2, "dam_semi"),
]

_DOMAIN_ROW = (
    "domain_adv_materials",
    "Advanced Materials Types",
    "Composites, biomaterials, smart materials, nanomaterials, "
    "high-performance alloys, ceramics, semiconducting materials taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 325 (Chemical mfg), 327 (Non-metallic mineral), 3315 (Steel)
_NAICS_PREFIXES = ["325", "327", "3315"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific material types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_adv_materials(conn) -> int:
    """Ingest Advanced Materials domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_adv_materials'), and links NAICS 325/327/3315 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_adv_materials",
        "Advanced Materials Types",
        "Composites, biomaterials, smart materials, nanomaterials, "
        "high-performance alloys, ceramics, semiconducting materials taxonomy",
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

    parent_codes = {parent for _, _, _, parent in MATERIALS_NODES if parent is not None}

    rows = [
        (
            "domain_adv_materials",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MATERIALS_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MATERIALS_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_adv_materials'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_adv_materials'",
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
            [("naics_2022", code, "domain_adv_materials", "primary") for code in naics_codes],
        )

    return count
