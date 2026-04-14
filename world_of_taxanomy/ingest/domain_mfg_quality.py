"""Manufacturing Quality and Compliance Types domain taxonomy ingester.

Manufacturing quality management and regulatory compliance framework classification.

Code prefix: dfpq_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MFG_QUALITY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- General Quality Management Systems --
    ("dfpq_qms", "General Quality Management Systems", 1, None),
    ("dfpq_qms_iso9001", "ISO 9001 Quality Management System", 2, 'dfpq_qms'),
    ("dfpq_qms_tpm", "Total Productive Maintenance (TPM)", 2, 'dfpq_qms'),
    ("dfpq_qms_lean", "Lean Manufacturing and Six Sigma (DMAIC)", 2, 'dfpq_qms'),
    # -- Industry-Specific Quality Standards --
    ("dfpq_industry", "Industry-Specific Quality Standards", 1, None),
    ("dfpq_industry_as9100", "AS9100 Aerospace Quality Management", 2, 'dfpq_industry'),
    ("dfpq_industry_iatf", "IATF 16949 Automotive Quality Standard", 2, 'dfpq_industry'),
    ("dfpq_industry_iso13485", "ISO 13485 Medical Device Quality System", 2, 'dfpq_industry'),
    ("dfpq_industry_gmp", "FDA cGMP (21 CFR 210/211/820 Good Manufacturing Practice)", 2, 'dfpq_industry'),
    # -- Regulatory and Product Safety Compliance --
    ("dfpq_regulatory", "Regulatory and Product Safety Compliance", 1, None),
    ("dfpq_regulatory_ul", "UL and Safety Certification (ETL, CSA, CE)", 2, 'dfpq_regulatory'),
    ("dfpq_regulatory_rohs", "RoHS and REACH Substance Restriction Compliance", 2, 'dfpq_regulatory'),
    ("dfpq_regulatory_fda510k", "FDA 510(k) Premarket Notification or PMA", 2, 'dfpq_regulatory'),
    # -- Statistical Process Control and Metrology --
    ("dfpq_spc", "Statistical Process Control and Metrology", 1, None),
    ("dfpq_spc_spc", "Statistical Process Control (SPC, control charts, Cpk)", 2, 'dfpq_spc'),
    ("dfpq_spc_msa", "Measurement System Analysis (MSA, GR&R)", 2, 'dfpq_spc'),
    ("dfpq_spc_fmea", "FMEA and APQP Advanced Product Quality Planning", 2, 'dfpq_spc'),
    ("dfpq_spc_ppap", "PPAP Production Part Approval Process", 2, 'dfpq_spc'),
]

_DOMAIN_ROW = (
    "domain_mfg_quality",
    "Manufacturing Quality and Compliance Types",
    "Manufacturing quality management and regulatory compliance framework classification",
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


async def ingest_domain_mfg_quality(conn) -> int:
    """Ingest Manufacturing Quality and Compliance Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_mfg_quality",
        "Manufacturing Quality and Compliance Types",
        "Manufacturing quality management and regulatory compliance framework classification",
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

    parent_codes = {parent for _, _, _, parent in MFG_QUALITY_NODES if parent is not None}

    rows = [
        (
            "domain_mfg_quality",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MFG_QUALITY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MFG_QUALITY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_mfg_quality'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_mfg_quality'",
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
            [("naics_2022", code, "domain_mfg_quality", "primary") for code in naics_codes],
        )

    return count
