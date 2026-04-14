"""Agricultural Input Supply domain taxonomy ingester.

Classifies what consumable inputs are purchased and applied to produce
farm output - orthogonal to crop type, livestock, equipment, farming
method, business structure, and market channel. The same soybean field
can receive conventional or organic-approved seed, synthetic or biological
fertilizer, and herbicide or mechanical weed control independently.

Code prefix: daip_ (ag input - avoids collision with dai_ from domain_ai_data)
Categories: Seed and Planting Material, Crop Protection Products,
Fertilizers and Soil Amendments, Livestock Feed and Nutrition,
Veterinary Inputs and Animal Health.

Stakeholders: input dealers and distributors (Corteva, Bayer, Nutrien),
crop consultants writing prescriptions, USDA AMS pesticide data program,
EPA FIFRA registrants, organic certifiers auditing allowed inputs,
precision ag platforms managing application records.
Source: EPA FIFRA pesticide registration categories, USDA AMS pesticide
data program, AAPFCO fertilizer tonnage reports, USDA NOP allowed
materials list. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_INPUT_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Seed and Planting Material --
    ("daip_seed",              "Seed and Planting Material",                          1, None),
    ("daip_seed_gmo",          "Genetically Modified (GM/Biotech) Seed",             2, "daip_seed"),
    ("daip_seed_organic",      "Certified Organic Seed",                             2, "daip_seed"),
    ("daip_seed_conv",         "Conventional Non-GM Seed",                           2, "daip_seed"),
    ("daip_seed_hybrid",       "Hybrid Seed (F1 crosses, licensed genetics)",        2, "daip_seed"),
    ("daip_seed_cover",        "Cover Crop and Forage Seed Mixes",                   2, "daip_seed"),
    ("daip_seed_transplant",   "Transplants, Plugs, and Vegetative Starts",          2, "daip_seed"),

    # -- Crop Protection Products --
    ("daip_protect",           "Crop Protection Products",                            1, None),
    ("daip_protect_herb",      "Herbicides (pre-emergent and post-emergent)",        2, "daip_protect"),
    ("daip_protect_insect",    "Insecticides (organophosphate, pyrethroid, bioinsect)", 2, "daip_protect"),
    ("daip_protect_fung",      "Fungicides (DMI, SDHI, biologicals)",               2, "daip_protect"),
    ("daip_protect_bio",       "Biological Crop Protection (biopesticides, BCAs)",   2, "daip_protect"),
    ("daip_protect_rodent",    "Rodenticides and Vertebrate Pest Control",           2, "daip_protect"),

    # -- Fertilizers and Soil Amendments --
    ("daip_fert",              "Fertilizers and Soil Amendments",                     1, None),
    ("daip_fert_npk",          "Synthetic NPK Fertilizers (urea, MAP, DAP, potash)", 2, "daip_fert"),
    ("daip_fert_org",          "Organic and Biological Fertilizers (manure, compost)", 2, "daip_fert"),
    ("daip_fert_micro",        "Micronutrient Products (zinc, boron, sulfur, iron)", 2, "daip_fert"),
    ("daip_fert_lime",         "Lime and pH Amendment Products",                     2, "daip_fert"),
    ("daip_fert_biochar",      "Biochar and Soil Carbon Amendments",                 2, "daip_fert"),
    ("daip_fert_biostim",      "Biostimulants (humic acids, amino acids, seaweed)",  2, "daip_fert"),

    # -- Livestock Feed and Nutrition --
    ("daip_feed",              "Livestock Feed and Nutrition",                        1, None),
    ("daip_feed_grain",        "Grain and Oilseed Feed Ingredients (corn, SBM)",     2, "daip_feed"),
    ("daip_feed_roughage",     "Roughage and Forage (hay, silage, distillers grains)", 2, "daip_feed"),
    ("daip_feed_premix",       "Feed Premixes and Supplements (vitamins, minerals)", 2, "daip_feed"),
    ("daip_feed_additive",     "Feed Additives (ionophores, enzymes, probiotics)",   2, "daip_feed"),

    # -- Veterinary Inputs and Animal Health --
    ("daip_vet",               "Veterinary Inputs and Animal Health",                 1, None),
    ("daip_vet_vaccine",       "Livestock Vaccines (BRD, viral, clostridial)",       2, "daip_vet"),
    ("daip_vet_antibiotic",    "Veterinary Antibiotics and Antimicrobials (VFD)",    2, "daip_vet"),
    ("daip_vet_parasite",      "Parasiticides (dewormers, pour-ons, ear tags)",      2, "daip_vet"),
    ("daip_vet_hormone",       "Growth Promotants and Hormone Implants",             2, "daip_vet"),
]

_DOMAIN_ROW = (
    "domain_ag_input",
    "Agricultural Input Supply Types",
    "Agricultural consumable input classification - seed, crop protection, "
    "fertilizer, livestock feed, and veterinary inputs",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific input types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_input(conn) -> int:
    """Ingest Agricultural Input Supply domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_input'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_input",
        "Agricultural Input Supply Types",
        "Agricultural consumable input classification - seed, crop protection, "
        "fertilizer, livestock feed, and veterinary inputs",
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

    parent_codes = {parent for _, _, _, parent in AG_INPUT_NODES if parent is not None}

    rows = [
        (
            "domain_ag_input",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_INPUT_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_INPUT_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_input'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_input'",
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
            [("naics_2022", code, "domain_ag_input", "primary") for code in naics_codes],
        )

    return count
