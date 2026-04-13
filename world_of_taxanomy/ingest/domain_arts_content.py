"""Arts, Entertainment and Recreation domain taxonomy ingester.

Arts/entertainment taxonomy organizes content types (NAICS 71):
  Content Type  (dac_content*) - film, music, gaming, visual art, sports, live performance
  Venue Type    (dac_venue*)   - theater, stadium, museum, club, arena, park
  Rights Type   (dac_rights*)  - sync, master, publishing, performance, broadcast
  Format        (dac_format*)  - live event, recorded, streaming, interactive

Source: NAICS 71 subsectors + ISAN (International Standard Audiovisual Number) media types.
Public domain. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
ARTS_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Content Type category --
    ("dac_content",          "Arts and Entertainment Content Type",              1, None),
    ("dac_content_film",     "Film, TV and Video Production",                  2, "dac_content"),
    ("dac_content_music",    "Music Recording, Publishing and Performance",    2, "dac_content"),
    ("dac_content_gaming",   "Video Games, Interactive and eSports",           2, "dac_content"),
    ("dac_content_visual",   "Visual Art, Photography and Design",             2, "dac_content"),
    ("dac_content_sports",   "Professional and Spectator Sports",              2, "dac_content"),
    ("dac_content_live",     "Live Theater, Comedy and Performing Arts",       2, "dac_content"),

    # -- Venue Type category --
    ("dac_venue",          "Entertainment Venue Type",                          1, None),
    ("dac_venue_theater",  "Theater and Performing Arts Center",               2, "dac_venue"),
    ("dac_venue_stadium",  "Stadium and Sports Arena",                         2, "dac_venue"),
    ("dac_venue_museum",   "Museum, Gallery and Cultural Institution",         2, "dac_venue"),
    ("dac_venue_club",     "Nightclub, Music Club and Comedy Club",            2, "dac_venue"),
    ("dac_venue_park",     "Amusement Park, Theme Park and Attraction",        2, "dac_venue"),

    # -- Rights Type category --
    ("dac_rights",         "Intellectual Property and Rights Type",             1, None),
    ("dac_rights_sync",    "Synchronization License (music + visual media)",   2, "dac_rights"),
    ("dac_rights_master",  "Master Recording Rights (sound recording owner)",  2, "dac_rights"),
    ("dac_rights_pub",     "Publishing Rights (songwriter, composer)",         2, "dac_rights"),
    ("dac_rights_perf",    "Performance Rights (PRO: ASCAP, BMI, SESAC)",     2, "dac_rights"),
    ("dac_rights_broad",   "Broadcast License (TV, radio, streaming)",         2, "dac_rights"),

    # -- Format category --
    ("dac_format",         "Content Delivery Format",                           1, None),
    ("dac_format_live",    "Live and In-Person Event",                         2, "dac_format"),
    ("dac_format_record",  "Recorded and Packaged Media (DVD, Blu-ray, vinyl)",2, "dac_format"),
    ("dac_format_stream",  "Digital Streaming (on-demand, subscription)",      2, "dac_format"),
]

_DOMAIN_ROW = (
    "domain_arts_content",
    "Arts and Entertainment Content Types",
    "Content type, venue, rights and format taxonomy for NAICS 71 arts and entertainment sector",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["71"]


def _determine_level(code: str) -> int:
    """Return level: 1 for top categories, 2 for specific arts types."""
    parts = code.split("_")
    if len(parts) == 2:
        return 1
    return 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_arts_content(conn) -> int:
    """Ingest Arts and Entertainment Content Type domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_arts_content'), and links NAICS 71xxx nodes
    via node_taxonomy_link.

    Returns total arts content node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_arts_content",
        "Arts and Entertainment Content Types",
        "Content type, venue, rights and format taxonomy for NAICS 71 arts and entertainment sector",
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

    parent_codes = {parent for _, _, _, parent in ARTS_NODES if parent is not None}

    rows = [
        (
            "domain_arts_content",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in ARTS_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(ARTS_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_arts_content'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_arts_content'",
        count,
    )

    naics_codes = [
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE '71%'"
        )
    ]

    await conn.executemany(
        """INSERT INTO node_taxonomy_link
               (system_id, node_code, taxonomy_id, relevance)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
        [("naics_2022", code, "domain_arts_content", "primary") for code in naics_codes],
    )

    return count
