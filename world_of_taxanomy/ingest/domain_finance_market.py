"""Finance Market and Exchange Structure Types domain taxonomy ingester.

Finance market structure classification - exchange, OTC, private markets, dark pools, alternative trading.

Code prefix: dfimkt_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
FINANCE_MARKET_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Registered Exchange Markets --
    ("dfimkt_exchange", "Registered Exchange Markets", 1, None),
    ("dfimkt_exchange_nyse", "NYSE and NYSE American (equity, ETFs, options)", 2, 'dfimkt_exchange'),
    ("dfimkt_exchange_nasdaq", "NASDAQ Global Markets and Global Select Market", 2, 'dfimkt_exchange'),
    ("dfimkt_exchange_cme", "CME Group Derivatives (futures, options on futures)", 2, 'dfimkt_exchange'),
    ("dfimkt_exchange_cboe", "CBOE Options Exchange (equity, index options)", 2, 'dfimkt_exchange'),
    # -- Over-the-Counter (OTC) Markets --
    ("dfimkt_otc", "Over-the-Counter (OTC) Markets", 1, None),
    ("dfimkt_otc_dealer", "OTC Dealer Market (FOREX, UST, corporate bonds)", 2, 'dfimkt_otc'),
    ("dfimkt_otc_bb", "OTC Bulletin Board and Pink Sheets (small caps)", 2, 'dfimkt_otc'),
    ("dfimkt_otc_swap", "Bilateral Swap and Derivatives Market (ISDA)", 2, 'dfimkt_otc'),
    # -- Private Markets and Alternative Trading --
    ("dfimkt_private", "Private Markets and Alternative Trading", 1, None),
    ("dfimkt_private_pe", "Private Equity and Venture Capital Market", 2, 'dfimkt_private'),
    ("dfimkt_private_re", "Private Real Estate Market", 2, 'dfimkt_private'),
    ("dfimkt_private_credit", "Private Credit and Direct Lending Market", 2, 'dfimkt_private'),
    # -- Alternative Trading Systems (ATS) and Dark Pools --
    ("dfimkt_ats", "Alternative Trading Systems (ATS) and Dark Pools", 1, None),
    ("dfimkt_ats_dark", "Dark Pool ATS (block trading, anonymized)", 2, 'dfimkt_ats'),
    ("dfimkt_ats_ecn", "Electronic Communication Network (ECN - ARCA, BATS)", 2, 'dfimkt_ats'),
    ("dfimkt_ats_sip", "SIP and Consolidated Tape (NBBO, TRF reporting)", 2, 'dfimkt_ats'),
    ("dfimkt_ats_crypto", "Crypto Exchange and Digital Asset Market (CEX, DEX)", 2, 'dfimkt_ats'),
]

_DOMAIN_ROW = (
    "domain_finance_market",
    "Finance Market and Exchange Structure Types",
    "Finance market structure classification - exchange, OTC, private markets, dark pools, alternative trading",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['52']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_finance_market(conn) -> int:
    """Ingest Finance Market and Exchange Structure Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_finance_market",
        "Finance Market and Exchange Structure Types",
        "Finance market structure classification - exchange, OTC, private markets, dark pools, alternative trading",
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

    parent_codes = {parent for _, _, _, parent in FINANCE_MARKET_NODES if parent is not None}

    rows = [
        (
            "domain_finance_market",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in FINANCE_MARKET_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(FINANCE_MARKET_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_finance_market'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_finance_market'",
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
            [("naics_2022", code, "domain_finance_market", "primary") for code in naics_codes],
        )

    return count
