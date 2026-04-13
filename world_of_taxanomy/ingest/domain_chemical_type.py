"""Chemical Industry Type domain taxonomy ingester.

Organizes chemical industry types into categories aligned with
NAICS 325 (Chemical Manufacturing) and NAICS 324 (Petroleum Refining).

Code prefix: dch_
Categories: petrochemicals, specialty, agrochemicals, pharma intermediates,
industrial gases, polymers, coatings, cleaning compounds, flavors, explosives.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
CHEMICAL_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Petrochemicals --
    ("dch_petro",           "Petrochemicals",                                        1, None),
    ("dch_petro_basic",     "Basic Petrochemicals (ethylene, propylene, methanol)",  2, "dch_petro"),
    ("dch_petro_aromatic",  "Aromatic Hydrocarbons (benzene, toluene, xylene)",      2, "dch_petro"),
    ("dch_petro_olefin",    "Olefins and Derivatives (butadiene, butylene)",         2, "dch_petro"),

    # -- Specialty Chemicals --
    ("dch_spec",            "Specialty Chemicals",                                   1, None),
    ("dch_spec_elec",       "Electronic Chemicals (semiconductor-grade solvents)",   2, "dch_spec"),
    ("dch_spec_catalyst",   "Catalysts and Catalysis (zeolites, organometallics)",   2, "dch_spec"),
    ("dch_spec_surfact",    "Surfactants and Emulsifiers",                           2, "dch_spec"),
    ("dch_spec_biocide",    "Biocides and Preservatives",                            2, "dch_spec"),

    # -- Agrochemicals --
    ("dch_agroc",           "Agrochemicals",                                         1, None),
    ("dch_agroc_pest",      "Pesticides (herbicides, insecticides, fungicides)",     2, "dch_agroc"),
    ("dch_agroc_fert",      "Fertilizers (nitrogen, phosphate, potash)",             2, "dch_agroc"),
    ("dch_agroc_growth",    "Plant Growth Regulators and Soil Amendments",           2, "dch_agroc"),

    # -- Pharmaceutical Intermediates --
    ("dch_pharma",          "Pharmaceutical Intermediates",                          1, None),
    ("dch_pharma_api",      "Active Pharmaceutical Ingredients (APIs)",              2, "dch_pharma"),
    ("dch_pharma_excip",    "Pharmaceutical Excipients and Carriers",                2, "dch_pharma"),
    ("dch_pharma_bio",      "Biologics Intermediates (cell culture media, buffers)", 2, "dch_pharma"),

    # -- Industrial Gases --
    ("dch_gas",             "Industrial Gases",                                      1, None),
    ("dch_gas_indust",      "Industrial Gases (oxygen, nitrogen, argon, CO2)",       2, "dch_gas"),
    ("dch_gas_special",     "Specialty Gases (ultra-high purity, calibration mixes)",2, "dch_gas"),
    ("dch_gas_cryo",        "Cryogenic Gases (liquid nitrogen, liquid helium)",      2, "dch_gas"),

    # -- Polymers and Plastics --
    ("dch_poly",            "Polymers and Plastics",                                 1, None),
    ("dch_poly_therm",      "Thermoplastics (PE, PP, PVC, PET, ABS)",               2, "dch_poly"),
    ("dch_poly_thermo",     "Thermosets (epoxy, phenolic, polyurethane, silicone)",  2, "dch_poly"),
    ("dch_poly_elast",      "Elastomers and Synthetic Rubber (SBR, EPDM, NBR)",     2, "dch_poly"),

    # -- Coatings, Adhesives, Inks --
    ("dch_coat",            "Coatings, Adhesives and Inks",                          1, None),
    ("dch_coat_arch",       "Architectural and Decorative Coatings",                 2, "dch_coat"),
    ("dch_coat_indust",     "Industrial and Protective Coatings",                    2, "dch_coat"),
    ("dch_coat_adhesive",   "Adhesives and Sealants",                               2, "dch_coat"),
]

_DOMAIN_ROW = (
    "domain_chemical_type",
    "Chemical Industry Types",
    "Petrochemicals, specialty chemicals, agrochemicals, pharma intermediates, "
    "industrial gases, polymers, coatings and adhesives taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes to link: 325 (Chemical mfg), 324 (Petroleum refining)
_NAICS_PREFIXES = ["325", "324"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific chemical types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_chemical_type(conn) -> int:
    """Ingest Chemical Industry Type domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_chemical_type'), and links NAICS 325/324 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_chemical_type",
        "Chemical Industry Types",
        "Petrochemicals, specialty chemicals, agrochemicals, pharma intermediates, "
        "industrial gases, polymers, coatings and adhesives taxonomy",
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

    parent_codes = {parent for _, _, _, parent in CHEMICAL_NODES if parent is not None}

    rows = [
        (
            "domain_chemical_type",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in CHEMICAL_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(CHEMICAL_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_chemical_type'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_chemical_type'",
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
            [("naics_2022", code, "domain_chemical_type", "primary") for code in naics_codes],
        )

    return count
