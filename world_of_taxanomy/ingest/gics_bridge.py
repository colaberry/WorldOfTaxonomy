"""GICS Bridge ingester.

Global Industry Classification Standard (GICS) - MSCI / S&P Dow Jones.

IMPORTANT DISCLAIMER: GICS is a proprietary classification system owned by
MSCI Inc. and S&P Dow Jones Indices LLC. This module stores ONLY the 11
top-level sector names that are publicly available in the financial press.
No GICS hierarchy data (industry groups, industries, sub-industries) is
stored or redistributed here.

Source: publicly known sector names (financial press, Wikipedia, SEC filings)
License: n/a - only publicly known names stored, no GICS data redistributed

Flat structure: 11 sectors, level=1, parent=None, is_leaf=True.
Codes are the 2-digit GICS sector codes (publicly known).
"""
from __future__ import annotations

# The 11 GICS sectors - codes and names are publicly available
# in financial press, SEC filings, and Wikipedia.
# DO NOT add sub-levels: industry groups, industries, or sub-industries
# are proprietary and must not be redistributed.
GICS_SECTORS: list[tuple[str, str]] = [
    ("10", "Energy"),
    ("15", "Materials"),
    ("20", "Industrials"),
    ("25", "Consumer Discretionary"),
    ("30", "Consumer Staples"),
    ("35", "Health Care"),
    ("40", "Financials"),
    ("45", "Information Technology"),
    ("50", "Communication Services"),
    ("55", "Utilities"),
    ("60", "Real Estate"),
]

_SYSTEM_ROW = (
    "gics_bridge",
    "GICS Bridge",
    "Global Industry Classification Standard - Top Sectors Only (MSCI/S&P)",
    "2023",
    "Global",
    "MSCI / S&P Dow Jones Indices",
)


async def ingest_gics_bridge(conn) -> int:
    """Ingest 11 GICS sector stubs into classification_system + classification_node.

    Only the 11 publicly known top-level sector names are stored.
    No GICS hierarchy data is redistributed (proprietary).

    Returns 11 (always).
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    rows = [
        (
            "gics_bridge",
            code,
            title,
            1,      # level: flat
            None,   # parent_code: none
            code,   # sector_code: itself
            True,   # is_leaf: always True
        )
        for code, title in GICS_SECTORS
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(GICS_SECTORS)
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'gics_bridge'",
        count,
    )

    return count
