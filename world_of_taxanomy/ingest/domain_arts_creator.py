"""Arts and Entertainment Creator and Rights Holder Structure Types domain taxonomy ingester.

Arts and entertainment creator structure and rights holder classification - major, independent, self-published, collective.

Code prefix: dacstruct_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
ARTS_CREATOR_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Major Studio and Label Structures --
    ("dacstruct_major", "Major Studio and Label Structures", 1, None),
    ("dacstruct_major_label", "Major Record Label (Universal, Sony, Warner Music)", 2, 'dacstruct_major'),
    ("dacstruct_major_studio", "Major Film Studio (Warner Bros, Disney, Universal Pictures)", 2, 'dacstruct_major'),
    ("dacstruct_major_publisher", "Major Music Publisher (UMPG, Sony Music Publishing)", 2, 'dacstruct_major'),
    # -- Independent and Alternative Structures --
    ("dacstruct_indie", "Independent and Alternative Structures", 1, None),
    ("dacstruct_indie_label", "Independent Record Label (A24, Domino, Sub Pop)", 2, 'dacstruct_indie'),
    ("dacstruct_indie_film", "Independent Film Production Company", 2, 'dacstruct_indie'),
    ("dacstruct_indie_games", "Independent Game Developer (indie studio)", 2, 'dacstruct_indie'),
    # -- Self-Published and Direct-to-Fan --
    ("dacstruct_self", "Self-Published and Direct-to-Fan", 1, None),
    ("dacstruct_self_artist", "Self-Released Artist (DistroKid, TuneCore, CD Baby)", 2, 'dacstruct_self'),
    ("dacstruct_self_creator", "Independent Creator Economy (YouTube, TikTok, Twitch)", 2, 'dacstruct_self'),
    # -- Artist Collectives and Cooperatives --
    ("dacstruct_collective", "Artist Collectives and Cooperatives", 1, None),
    ("dacstruct_collective_coop", "Artist-Owned Cooperative and Collective", 2, 'dacstruct_collective'),
    ("dacstruct_collective_writer", "Writers Room and Showrunner Production Entity", 2, 'dacstruct_collective'),
    ("dacstruct_collective_improv", "Improv and Sketch Comedy Ensemble", 2, 'dacstruct_collective'),
]

_DOMAIN_ROW = (
    "domain_arts_creator",
    "Arts and Entertainment Creator and Rights Holder Structure Types",
    "Arts and entertainment creator structure and rights holder classification - major, independent, self-published, collective",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['71']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_arts_creator(conn) -> int:
    """Ingest Arts and Entertainment Creator and Rights Holder Structure Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_arts_creator",
        "Arts and Entertainment Creator and Rights Holder Structure Types",
        "Arts and entertainment creator structure and rights holder classification - major, independent, self-published, collective",
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

    parent_codes = {parent for _, _, _, parent in ARTS_CREATOR_NODES if parent is not None}

    rows = [
        (
            "domain_arts_creator",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in ARTS_CREATOR_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(ARTS_CREATOR_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_arts_creator'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_arts_creator'",
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
            [("naics_2022", code, "domain_arts_creator", "primary") for code in naics_codes],
        )

    return count
