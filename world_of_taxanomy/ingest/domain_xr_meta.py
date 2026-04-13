"""Extended Reality and Metaverse domain taxonomy ingester.

Organizes extended reality and metaverse sector types aligned with
NAICS 5112 (Software publishers), NAICS 5415 (Computer systems design),
and NAICS 3342 (Communications equipment mfg).

Code prefix: dxr_
Categories: virtual reality, augmented reality, mixed reality,
XR hardware, XR platforms, XR content, digital twins.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
XR_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Virtual Reality --
    ("dxr_vr",              "Virtual Reality (VR)",                                  1, None),
    ("dxr_vr_standalone",   "Standalone VR Headsets (Meta Quest, PICO, HTC Vive)",  2, "dxr_vr"),
    ("dxr_vr_tethered",     "Tethered VR Headsets (PC VR, PlayStation VR)",         2, "dxr_vr"),
    ("dxr_vr_cave",         "CAVE and Room-Scale VR (enterprise, training, sim)",    2, "dxr_vr"),

    # -- Augmented Reality --
    ("dxr_ar",              "Augmented Reality (AR)",                                1, None),
    ("dxr_ar_glasses",      "AR Smart Glasses (industrial - RealWear, Google Glass)",2, "dxr_ar"),
    ("dxr_ar_mobile",       "Mobile AR (ARKit, ARCore, Snapchat, Instagram lenses)", 2, "dxr_ar"),
    ("dxr_ar_hud",          "Heads-Up Displays (HUD) for Vehicles and Aviation",    2, "dxr_ar"),

    # -- Mixed Reality --
    ("dxr_mr",              "Mixed Reality (MR) and Spatial Computing",              1, None),
    ("dxr_mr_headset",      "Mixed Reality Headsets (HoloLens, Apple Vision Pro)",  2, "dxr_mr"),
    ("dxr_mr_spatial",      "Spatial Computing Platforms and Frameworks",            2, "dxr_mr"),

    # -- XR Hardware --
    ("dxr_hw",              "XR Hardware and Components",                            1, None),
    ("dxr_hw_display",      "XR Displays (micro-OLED, micro-LED, waveguide optics)",2, "dxr_hw"),
    ("dxr_hw_track",        "Tracking and Sensing (inside-out, eye-tracking, hand)",2, "dxr_hw"),
    ("dxr_hw_haptic",       "Haptics and Force Feedback Devices",                   2, "dxr_hw"),

    # -- XR Platforms --
    ("dxr_plat",            "XR Platforms and App Ecosystems",                       1, None),
    ("dxr_plat_meta",       "Open Metaverse Platforms (Horizon Worlds, Decentraland)",2, "dxr_plat"),
    ("dxr_plat_sdk",        "XR Developer SDKs and Toolkits (OpenXR, WebXR)",       2, "dxr_plat"),
    ("dxr_plat_store",      "XR App Stores and Content Marketplaces",               2, "dxr_plat"),

    # -- XR Content --
    ("dxr_content",         "XR Content and Experiences",                            1, None),
    ("dxr_content_game",    "XR Gaming and Entertainment",                           2, "dxr_content"),
    ("dxr_content_train",   "Enterprise XR Training and Simulation",                2, "dxr_content"),
    ("dxr_content_event",   "Virtual Events, Concerts and Social XR",               2, "dxr_content"),

    # -- Digital Twins --
    ("dxr_dt",              "Digital Twins",                                         1, None),
    ("dxr_dt_industrial",   "Industrial Digital Twins (factory, asset, process)",   2, "dxr_dt"),
    ("dxr_dt_city",         "City and Infrastructure Digital Twins",                2, "dxr_dt"),
    ("dxr_dt_product",      "Product and Lifecycle Digital Twins (PLM, simulation)",2, "dxr_dt"),
]

_DOMAIN_ROW = (
    "domain_xr_meta",
    "Extended Reality and Metaverse Types",
    "Virtual reality, augmented reality, mixed reality, XR hardware, "
    "XR platforms, XR content and digital twins taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 5112 (Software publishers), 5415 (Computer design), 3342 (Comms equip)
_NAICS_PREFIXES = ["5112", "5415", "3342"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific XR/metaverse types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_xr_meta(conn) -> int:
    """Ingest Extended Reality and Metaverse domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_xr_meta'), and links NAICS 5112/5415/3342 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_xr_meta",
        "Extended Reality and Metaverse Types",
        "Virtual reality, augmented reality, mixed reality, XR hardware, "
        "XR platforms, XR content and digital twins taxonomy",
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

    parent_codes = {parent for _, _, _, parent in XR_NODES if parent is not None}

    rows = [
        (
            "domain_xr_meta",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in XR_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(XR_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_xr_meta'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_xr_meta'",
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
            [("naics_2022", code, "domain_xr_meta", "primary") for code in naics_codes],
        )

    return count
