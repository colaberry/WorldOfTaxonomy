"""Digital Assets and Web3 domain taxonomy ingester.

Organizes digital assets and Web3 sector types aligned with
NAICS 522390 (Other nondepository credit), NAICS 5415 (Computer systems design),
and NAICS 5239 (Investment/securities activities).

Code prefix: dda_
Categories: blockchain infrastructure, DeFi protocols, digital tokens,
stablecoins/CBDC, crypto services, Web3 infrastructure.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
DIGITAL_ASSETS_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Blockchain Infrastructure --
    ("dda_chain",           "Blockchain Infrastructure",                             1, None),
    ("dda_chain_l1",        "Layer 1 Blockchains (Ethereum, Bitcoin, Solana, etc)", 2, "dda_chain"),
    ("dda_chain_l2",        "Layer 2 and Rollup Solutions (Arbitrum, Optimism, zk)", 2, "dda_chain"),
    ("dda_chain_bridge",    "Cross-Chain Bridges and Interoperability Protocols",   2, "dda_chain"),

    # -- DeFi Protocols --
    ("dda_defi",            "Decentralized Finance (DeFi) Protocols",               1, None),
    ("dda_defi_dex",        "Decentralized Exchanges (Uniswap, Curve, dYdX)",       2, "dda_defi"),
    ("dda_defi_lend",       "DeFi Lending and Borrowing (Aave, Compound, MakerDAO)",2, "dda_defi"),
    ("dda_defi_yield",      "Yield Farming and Liquidity Mining",                   2, "dda_defi"),
    ("dda_defi_deriv",      "On-Chain Derivatives and Structured Products",         2, "dda_defi"),

    # -- Digital Tokens and NFTs --
    ("dda_token",           "Digital Tokens and NFTs",                               1, None),
    ("dda_token_nft",       "Non-Fungible Tokens (art, gaming, real-world assets)", 2, "dda_token"),
    ("dda_token_utility",   "Utility and Governance Tokens",                        2, "dda_token"),
    ("dda_token_rwa",       "Tokenized Real-World Assets (bonds, equities, real estate)",2, "dda_token"),

    # -- Stablecoins and CBDC --
    ("dda_stable",          "Stablecoins and Central Bank Digital Currencies",       1, None),
    ("dda_stable_fiat",     "Fiat-Backed Stablecoins (USDC, USDT, BUSD)",           2, "dda_stable"),
    ("dda_stable_algo",     "Algorithmic and Overcollateralized Stablecoins",        2, "dda_stable"),
    ("dda_stable_cbdc",     "Central Bank Digital Currencies (CBDC) - retail/wholesale",2, "dda_stable"),

    # -- Crypto Services --
    ("dda_svc",             "Crypto Services and Infrastructure",                    1, None),
    ("dda_svc_exchange",    "Centralized Crypto Exchanges (Coinbase, Binance)",      2, "dda_svc"),
    ("dda_svc_custody",     "Digital Asset Custody and Prime Brokerage",            2, "dda_svc"),
    ("dda_svc_wallet",      "Wallets and Payment Solutions",                        2, "dda_svc"),

    # -- Web3 Infrastructure --
    ("dda_web3",            "Web3 Infrastructure",                                   1, None),
    ("dda_web3_identity",   "Decentralized Identity (DID, verifiable credentials)", 2, "dda_web3"),
    ("dda_web3_oracle",     "Oracles and Off-Chain Data Feeds (Chainlink)",         2, "dda_web3"),
    ("dda_web3_storage",    "Decentralized Storage (IPFS, Filecoin, Arweave)",      2, "dda_web3"),
]

_DOMAIN_ROW = (
    "domain_digital_assets",
    "Digital Assets and Web3 Types",
    "Blockchain infrastructure, DeFi, digital tokens, stablecoins, "
    "crypto services and Web3 infrastructure taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 522390 (Other nondepository), 5415 (Computer design), 5239 (Securities)
_NAICS_PREFIXES = ["522390", "5415", "5239"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific digital asset types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_digital_assets(conn) -> int:
    """Ingest Digital Assets and Web3 domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_digital_assets'), and links NAICS 522390/5415/5239 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_digital_assets",
        "Digital Assets and Web3 Types",
        "Blockchain infrastructure, DeFi, digital tokens, stablecoins, "
        "crypto services and Web3 infrastructure taxonomy",
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

    parent_codes = {parent for _, _, _, parent in DIGITAL_ASSETS_NODES if parent is not None}

    rows = [
        (
            "domain_digital_assets",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in DIGITAL_ASSETS_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(DIGITAL_ASSETS_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_digital_assets'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_digital_assets'",
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
            [("naics_2022", code, "domain_digital_assets", "primary") for code in naics_codes],
        )

    return count
