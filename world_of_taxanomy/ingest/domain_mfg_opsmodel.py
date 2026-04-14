"""Manufacturing Operations Model Types domain taxonomy ingester.

Manufacturing operations and production planning model classification - MTS, MTO, ATO, ETO.

Code prefix: dfpm_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MFG_OPSMODEL_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Make-to-Stock (MTS) --
    ("dfpm_mts", "Make-to-Stock (MTS)", 1, None),
    ("dfpm_mts_batch", "Batch Production (fixed runs, scheduled changeover)", 2, 'dfpm_mts'),
    ("dfpm_mts_continuous", "Continuous Flow Production (high volume, low mix)", 2, 'dfpm_mts'),
    ("dfpm_mts_discrete", "Discrete Repetitive Production (standard products, fixed BOMs)", 2, 'dfpm_mts'),
    # -- Make-to-Order (MTO) --
    ("dfpm_mto", "Make-to-Order (MTO)", 1, None),
    ("dfpm_mto_custom", "Custom Manufacturing (unique spec per order)", 2, 'dfpm_mto'),
    ("dfpm_mto_semicustom", "Semi-Custom (standard platform, configured to order)", 2, 'dfpm_mto'),
    ("dfpm_mto_jop", "Job Order Production (small batch, high mix)", 2, 'dfpm_mto'),
    # -- Engineer-to-Order (ETO) --
    ("dfpm_eto", "Engineer-to-Order (ETO)", 1, None),
    ("dfpm_eto_project", "Project-Based Engineering (one-off capital equipment)", 2, 'dfpm_eto'),
    ("dfpm_eto_defense", "Defense and Aerospace ETO (mil-spec, CDRL deliverables)", 2, 'dfpm_eto'),
    # -- Assemble-to-Order (ATO) --
    ("dfpm_ato", "Assemble-to-Order (ATO)", 1, None),
    ("dfpm_ato_modular", "Modular Assembly (configure from standard sub-assemblies)", 2, 'dfpm_ato'),
    ("dfpm_ato_bto", "Build-to-Order (BTO) - consumer electronics, PCs", 2, 'dfpm_ato'),
    # -- Flow and Pull Production Systems --
    ("dfpm_flow", "Flow and Pull Production Systems", 1, None),
    ("dfpm_flow_kanban", "Kanban Pull System (demand-driven replenishment)", 2, 'dfpm_flow'),
    ("dfpm_flow_jit", "Just-in-Time (JIT) Production", 2, 'dfpm_flow'),
    ("dfpm_flow_onepiece", "One-Piece Flow (cellular manufacturing)", 2, 'dfpm_flow'),
]

_DOMAIN_ROW = (
    "domain_mfg_opsmodel",
    "Manufacturing Operations Model Types",
    "Manufacturing operations and production planning model classification - MTS, MTO, ATO, ETO",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['31', '32', '33']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_mfg_opsmodel(conn) -> int:
    """Ingest Manufacturing Operations Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_mfg_opsmodel",
        "Manufacturing Operations Model Types",
        "Manufacturing operations and production planning model classification - MTS, MTO, ATO, ETO",
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

    parent_codes = {parent for _, _, _, parent in MFG_OPSMODEL_NODES if parent is not None}

    rows = [
        (
            "domain_mfg_opsmodel",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MFG_OPSMODEL_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MFG_OPSMODEL_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_mfg_opsmodel'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_mfg_opsmodel'",
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
            [("naics_2022", code, "domain_mfg_opsmodel", "primary") for code in naics_codes],
        )

    return count
