"""Construction Material Types domain taxonomy ingester.

Classifies the primary structural material systems used in a building or
infrastructure project - orthogonal to trade type, building type, and
delivery method. A high-rise office building, a hospital, and an industrial
warehouse all use structural steel differently; the same material is designed,
fabricated, and erected by the same specialty trade under any delivery method.

Code prefix: dcmt_
Categories: Structural Wood and Mass Timber, Structural Steel, Concrete and
Masonry, Prefabricated and Modular Systems, Specialty and Advanced Materials.

Stakeholders: structural engineers specifying material systems, material
suppliers and fabricators (AISC, PCI, WoodWorks), building code officials
(IBC fire and structural), sustainable building certification bodies (LEED
material credits), construction cost estimators.
Source: IBC structural material chapters, AISC steel construction classifications,
ACI concrete standards, AWC wood frame construction manual. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
CONST_MATERIAL_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Structural Wood and Mass Timber --
    ("dcmt_wood",             "Structural Wood and Mass Timber",                 1, None),
    ("dcmt_wood_lightframe",  "Light Wood Frame (2x stud, platform frame)",     2, "dcmt_wood"),
    ("dcmt_wood_heavy",       "Heavy Timber and Post-and-Beam Construction",    2, "dcmt_wood"),
    ("dcmt_wood_clt",         "Cross-Laminated Timber (CLT) and Mass Timber",  2, "dcmt_wood"),
    ("dcmt_wood_glulam",      "Glulam and Structural Composite Lumber (SCL)",  2, "dcmt_wood"),

    # -- Structural Steel --
    ("dcmt_steel",            "Structural Steel",                                1, None),
    ("dcmt_steel_moment",     "Moment Frame (SMRF, OMRF - lateral resistance)", 2, "dcmt_steel"),
    ("dcmt_steel_braced",     "Braced Frame (CBF, EBF, SCBF)",                 2, "dcmt_steel"),
    ("dcmt_steel_joist",      "Steel Joist and Deck (open web, composite deck)", 2, "dcmt_steel"),
    ("dcmt_steel_light",      "Light Gauge Steel Framing (cold-formed, metal stud)", 2, "dcmt_steel"),

    # -- Concrete and Masonry --
    ("dcmt_concrete",         "Concrete and Masonry",                            1, None),
    ("dcmt_concrete_cast",    "Cast-in-Place Concrete (forming, poured-in-place)", 2, "dcmt_concrete"),
    ("dcmt_concrete_precast", "Precast Concrete (tilt-up, precast panel)",      2, "dcmt_concrete"),
    ("dcmt_concrete_pt",      "Post-Tensioned Concrete (PT slab, PT beam)",     2, "dcmt_concrete"),
    ("dcmt_concrete_cmu",     "Concrete Masonry Unit (CMU) and Block Construction", 2, "dcmt_concrete"),
    ("dcmt_concrete_brick",   "Brick and Stone Masonry (historic and new)",     2, "dcmt_concrete"),

    # -- Prefabricated and Modular Systems --
    ("dcmt_prefab",           "Prefabricated and Modular Systems",               1, None),
    ("dcmt_prefab_modular",   "Volumetric Modular (off-site room modules)",     2, "dcmt_prefab"),
    ("dcmt_prefab_panel",     "Panelized Construction (wall and floor panels)", 2, "dcmt_prefab"),
    ("dcmt_prefab_hybrid",    "Hybrid Construction (on-site with prefab pods)", 2, "dcmt_prefab"),

    # -- Specialty and Advanced Materials --
    ("dcmt_specialty",        "Specialty and Advanced Construction Materials",   1, None),
    ("dcmt_specialty_fiber",  "Fiber-Reinforced Polymer (FRP, GFRP, CFRP)",    2, "dcmt_specialty"),
    ("dcmt_specialty_earthen","Earthen and Adobe Construction (rammed earth)",  2, "dcmt_specialty"),
    ("dcmt_specialty_icf",    "Insulated Concrete Form (ICF) Wall System",      2, "dcmt_specialty"),
]

_DOMAIN_ROW = (
    "domain_const_material",
    "Construction Material System Types",
    "Construction structural material system classification - wood and mass timber, "
    "structural steel, concrete and masonry, prefabricated, and specialty materials",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["23"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific material system types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_const_material(conn) -> int:
    """Ingest Construction Material Types domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_const_material'), and links NAICS 23 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_const_material",
        "Construction Material System Types",
        "Construction structural material system classification - wood and mass timber, "
        "structural steel, concrete and masonry, prefabricated, and specialty materials",
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

    parent_codes = {parent for _, _, _, parent in CONST_MATERIAL_NODES if parent is not None}

    rows = [
        (
            "domain_const_material",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in CONST_MATERIAL_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(CONST_MATERIAL_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_const_material'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_const_material'",
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
            [("naics_2022", code, "domain_const_material", "primary") for code in naics_codes],
        )

    return count
