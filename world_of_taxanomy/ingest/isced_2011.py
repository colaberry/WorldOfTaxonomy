"""ISCED 2011 ingester.

International Standard Classification of Education (ISCED) 2011.
Source: UNESCO Institute for Statistics - uis.unesco.org
  https://uis.unesco.org/en/topic/international-standard-classification-education-isced

License: Open (UNESCO public domain)

ISCED 2011 classifies education programs by LEVEL (0-8).
This is distinct from ISCED-F 2013 which classifies by FIELD of study.

9 main levels (0-8) with sub-categories = ~25 codes total.
Hand-coded from the official UNESCO ISCED 2011 structure document.

Hierarchy:
  Level 1: Main level (ISCED0 through ISCED8)
  Level 2: Sub-categories (ISCED0a, ISCED3a, ISCED3b, ISCED3c, ISCED4a, ISCED4b, ISCED5a, ISCED5b)
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
ISCED_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # Level 0 - Early Childhood Education
    ("ISCED0",  "Level 0: Early Childhood Education",                           1, None),
    ("ISCED0a", "Level 0a: Early Childhood Educational Development (< age 3)", 2, "ISCED0"),
    ("ISCED0b", "Level 0b: Pre-primary Education (age 3 to primary start)",    2, "ISCED0"),

    # Level 1 - Primary Education
    ("ISCED1",  "Level 1: Primary Education",                                   1, None),

    # Level 2 - Lower Secondary Education
    ("ISCED2",  "Level 2: Lower Secondary Education",                          1, None),
    ("ISCED2a", "Level 2a: Lower Secondary, general programmes",               2, "ISCED2"),
    ("ISCED2b", "Level 2b: Lower Secondary, vocational programmes",            2, "ISCED2"),

    # Level 3 - Upper Secondary Education
    ("ISCED3",  "Level 3: Upper Secondary Education",                          1, None),
    ("ISCED3a", "Level 3a: Upper Secondary, general programmes",               2, "ISCED3"),
    ("ISCED3b", "Level 3b: Upper Secondary, vocational programmes",            2, "ISCED3"),
    ("ISCED3c", "Level 3c: Upper Secondary, pre-vocational programmes",        2, "ISCED3"),

    # Level 4 - Post-Secondary Non-Tertiary Education
    ("ISCED4",  "Level 4: Post-Secondary Non-Tertiary Education",              1, None),
    ("ISCED4a", "Level 4a: Post-Secondary Non-Tertiary, general",              2, "ISCED4"),
    ("ISCED4b", "Level 4b: Post-Secondary Non-Tertiary, vocational",           2, "ISCED4"),

    # Level 5 - Short-Cycle Tertiary Education
    ("ISCED5",  "Level 5: Short-Cycle Tertiary Education",                     1, None),
    ("ISCED5a", "Level 5a: Short-Cycle Tertiary, academic-oriented",           2, "ISCED5"),
    ("ISCED5b", "Level 5b: Short-Cycle Tertiary, professionally-oriented",    2, "ISCED5"),

    # Level 6 - Bachelor's or Equivalent Level
    ("ISCED6",  "Level 6: Bachelor's or Equivalent Level",                     1, None),

    # Level 7 - Master's or Equivalent Level
    ("ISCED7",  "Level 7: Master's or Equivalent Level",                       1, None),

    # Level 8 - Doctoral or Equivalent Level
    ("ISCED8",  "Level 8: Doctoral or Equivalent Level",                       1, None),
]

_SYSTEM_ROW = (
    "isced_2011",
    "ISCED 2011",
    "International Standard Classification of Education 2011 - Education Levels",
    "2011",
    "Global",
    "UNESCO Institute for Statistics",
)


def _determine_level(code: str) -> int:
    """Return level: 1 for main ISCED levels (ISCED0-ISCED8), 2 for sub-categories."""
    if not code.startswith("ISCED"):
        return 0
    suffix = code[5:]  # strip 'ISCED'
    if len(suffix) == 1 and suffix.isdigit():
        return 1
    if len(suffix) == 2 and suffix[0].isdigit() and suffix[1].isalpha():
        return 2
    return 0


def _determine_parent(code: str) -> Optional[str]:
    """Return parent code or None.

    ISCED0a -> ISCED0
    ISCED3b -> ISCED3
    ISCED0, ISCED8, etc. -> None
    """
    if not code.startswith("ISCED"):
        return None
    suffix = code[5:]
    if len(suffix) == 2 and suffix[0].isdigit() and suffix[1].isalpha():
        return f"ISCED{suffix[0]}"
    return None


async def ingest_isced_2011(conn) -> int:
    """Ingest ISCED 2011 education level taxonomy.

    Hand-coded from UNESCO ISCED 2011 structure.
    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    parent_codes = {parent for _, _, _, parent in ISCED_NODES if parent is not None}

    rows = [
        (
            "isced_2011",
            code,
            title,
            level,
            parent,
            "ISCED",
            code not in parent_codes,
        )
        for code, title, level, parent in ISCED_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(ISCED_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'isced_2011'",
        count,
    )

    return count
