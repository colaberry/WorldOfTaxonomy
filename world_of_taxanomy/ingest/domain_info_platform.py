"""Information and Media Platform Type Classification domain taxonomy ingester.

Information and media platform type classification - owned media, social, search, marketplace, app store, streaming.

Code prefix: dimplt_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
INFO_PLATFORM_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Owned and Operated Media Platforms --
    ("dimplt_owned", "Owned and Operated Media Platforms", 1, None),
    ("dimplt_owned_web", "Owned Website and App (publisher, brand direct)", 2, 'dimplt_owned'),
    ("dimplt_owned_ott", "Owned OTT and CTV Platform (Peacock, Paramount+)", 2, 'dimplt_owned'),
    # -- Social and User-Generated Content Platforms --
    ("dimplt_social", "Social and User-Generated Content Platforms", 1, None),
    ("dimplt_social_ump", "Universal Social Platform (Meta, TikTok, YouTube)", 2, 'dimplt_social'),
    ("dimplt_social_prof", "Professional Network Platform (LinkedIn, GitHub)", 2, 'dimplt_social'),
    ("dimplt_social_messaging", "Messaging and Chat Platform (WhatsApp, Telegram)", 2, 'dimplt_social'),
    # -- Search and Discovery Platforms --
    ("dimplt_search", "Search and Discovery Platforms", 1, None),
    ("dimplt_search_general", "General Search Engine (Google, Bing)", 2, 'dimplt_search'),
    ("dimplt_search_vertical", "Vertical Search (Zillow, Indeed, Expedia)", 2, 'dimplt_search'),
    # -- Marketplace and Commerce Platforms --
    ("dimplt_marketplace", "Marketplace and Commerce Platforms", 1, None),
    ("dimplt_marketplace_gen", "General Marketplace (Amazon, eBay, Etsy)", 2, 'dimplt_marketplace'),
    ("dimplt_marketplace_app", "App Store and Software Marketplace (Apple, Google Play)", 2, 'dimplt_marketplace'),
    # -- Audio and Video Streaming Platforms --
    ("dimplt_streaming", "Audio and Video Streaming Platforms", 1, None),
    ("dimplt_streaming_music", "Music Streaming (Spotify, Apple Music)", 2, 'dimplt_streaming'),
    ("dimplt_streaming_podcast", "Podcast and Spoken Word Platform", 2, 'dimplt_streaming'),
    ("dimplt_streaming_video", "Video-on-Demand and SVOD (Netflix, HBO Max)", 2, 'dimplt_streaming'),
    ("dimplt_gaming", "Gaming and Interactive Entertainment Platforms", 1, None),
]

_DOMAIN_ROW = (
    "domain_info_platform",
    "Information and Media Platform Type Classification",
    "Information and media platform type classification - owned media, social, search, marketplace, app store, streaming",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['51']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_info_platform(conn) -> int:
    """Ingest Information and Media Platform Type Classification.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_info_platform",
        "Information and Media Platform Type Classification",
        "Information and media platform type classification - owned media, social, search, marketplace, app store, streaming",
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

    parent_codes = {parent for _, _, _, parent in INFO_PLATFORM_NODES if parent is not None}

    rows = [
        (
            "domain_info_platform",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in INFO_PLATFORM_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(INFO_PLATFORM_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_info_platform'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_info_platform'",
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
            [("naics_2022", code, "domain_info_platform", "primary") for code in naics_codes],
        )

    return count
