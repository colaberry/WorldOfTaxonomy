"""ISO 31000 Risk Framework ingester.

ISO 31000:2018 - Risk Management - Guidelines.
Published by ISO. Hand-coded from publicly available standard structure.
Reference: https://www.iso.org/standard/65694.html

Hierarchy (2 levels):
  Clause     (level 1, code 'iso31000_cl_{N}')      - 5 main clauses
  Sub-clause (level 2, code 'iso31000_cl_{N}_{M}')  - all leaves

Total: 5 clauses + sub-clauses = ~48 nodes.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
ISO31000_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # ── Clause 4: Context of the organization ──
    ("iso31000_cl_4",     "Clause 4 - Context of the Organization", 1, None),
    ("iso31000_cl_4_1",   "4.1 Understanding the organization and its context", 2, "iso31000_cl_4"),
    ("iso31000_cl_4_2",   "4.2 Understanding the needs and expectations of interested parties", 2, "iso31000_cl_4"),
    ("iso31000_cl_4_3",   "4.3 Determining the scope of the risk management system", 2, "iso31000_cl_4"),
    ("iso31000_cl_4_4",   "4.4 Risk management system", 2, "iso31000_cl_4"),

    # ── Clause 5: Leadership ──
    ("iso31000_cl_5",     "Clause 5 - Leadership and Commitment", 1, None),
    ("iso31000_cl_5_1",   "5.1 Leadership and commitment", 2, "iso31000_cl_5"),
    ("iso31000_cl_5_2",   "5.2 Policy", 2, "iso31000_cl_5"),
    ("iso31000_cl_5_3",   "5.3 Organizational roles, responsibilities and authorities", 2, "iso31000_cl_5"),
    ("iso31000_cl_5_4",   "5.4 Consultation and participation of workers", 2, "iso31000_cl_5"),

    # ── Clause 6: Planning ──
    ("iso31000_cl_6",     "Clause 6 - Planning", 1, None),
    ("iso31000_cl_6_1",   "6.1 Actions to address risks and opportunities", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_2",   "6.2 Risk management objectives and planning to achieve them", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_3",   "6.3 Scope, context and criteria", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_4",   "6.4 Risk assessment", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_5",   "6.5 Risk treatment", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_6",   "6.6 Monitoring and review", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_7",   "6.7 Recording and reporting", 2, "iso31000_cl_6"),
    ("iso31000_cl_6_8",   "6.8 Communication and consultation", 2, "iso31000_cl_6"),

    # ── Clause 7: Support ──
    ("iso31000_cl_7",     "Clause 7 - Support", 1, None),
    ("iso31000_cl_7_1",   "7.1 Resources", 2, "iso31000_cl_7"),
    ("iso31000_cl_7_2",   "7.2 Competence", 2, "iso31000_cl_7"),
    ("iso31000_cl_7_3",   "7.3 Awareness", 2, "iso31000_cl_7"),
    ("iso31000_cl_7_4",   "7.4 Communication", 2, "iso31000_cl_7"),
    ("iso31000_cl_7_5",   "7.5 Documented information", 2, "iso31000_cl_7"),

    # ── Clause 8: Operation ──
    ("iso31000_cl_8",     "Clause 8 - Operation", 1, None),
    ("iso31000_cl_8_1",   "8.1 Operational planning and control", 2, "iso31000_cl_8"),
    ("iso31000_cl_8_2",   "8.2 Risk assessment", 2, "iso31000_cl_8"),
    ("iso31000_cl_8_3",   "8.3 Risk treatment", 2, "iso31000_cl_8"),

    # ── Clause 9: Performance evaluation ──
    ("iso31000_cl_9",     "Clause 9 - Performance Evaluation", 1, None),
    ("iso31000_cl_9_1",   "9.1 Monitoring, measurement, analysis and evaluation", 2, "iso31000_cl_9"),
    ("iso31000_cl_9_2",   "9.2 Internal audit", 2, "iso31000_cl_9"),
    ("iso31000_cl_9_3",   "9.3 Management review", 2, "iso31000_cl_9"),

    # ── Clause 10: Improvement ──
    ("iso31000_cl_10",    "Clause 10 - Improvement", 1, None),
    ("iso31000_cl_10_1",  "10.1 General", 2, "iso31000_cl_10"),
    ("iso31000_cl_10_2",  "10.2 Nonconformity and corrective action", 2, "iso31000_cl_10"),
    ("iso31000_cl_10_3",  "10.3 Continual improvement", 2, "iso31000_cl_10"),

    # ── Annex A: Risk management process (informative) ──
    ("iso31000_cl_A",     "Annex A - Risk Management Process (Informative)", 1, None),
    ("iso31000_cl_A_1",   "A.1 Communication and consultation", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_2",   "A.2 Scope, context and criteria", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_3",   "A.3 Risk assessment - General", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_4",   "A.4 Risk identification", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_5",   "A.5 Risk analysis", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_6",   "A.6 Risk evaluation", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_7",   "A.7 Risk treatment", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_8",   "A.8 Monitoring and review", 2, "iso31000_cl_A"),
    ("iso31000_cl_A_9",   "A.9 Recording and reporting", 2, "iso31000_cl_A"),
]

_SYSTEM_ROW = (
    "iso_31000",
    "ISO 31000",
    "ISO 31000:2018 - Risk Management - Guidelines",
    "2018",
    "Global",
    "International Organization for Standardization (ISO)",
)


def _determine_level(code: str) -> int:
    """Return level: 1 for top-level clauses, 2 for sub-clauses."""
    parts = code.split("_")
    # 'iso31000_cl_4'   -> parts = ['iso31000', 'cl', '4']     -> level 1
    # 'iso31000_cl_4_1' -> parts = ['iso31000', 'cl', '4', '1'] -> level 2
    if len(parts) == 3:
        return 1
    return 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent clause code, or None for top-level clauses."""
    parts = code.split("_")
    if len(parts) <= 3:
        return None
    return "_".join(parts[:3])


async def ingest_iso31000(conn) -> int:
    """Ingest ISO 31000:2018 risk management framework.

    Hand-coded from publicly available standard structure.
    Returns total node count inserted.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    clause_codes = {code for code, _, level, _ in ISO31000_NODES if level == 1}

    rows = [
        (
            "iso_31000",
            code,
            title,
            level,
            parent,
            code.split("_")[2],         # sector_code = clause number
            code not in clause_codes,   # is_leaf: sub-clauses are leaves
        )
        for code, title, level, parent in ISO31000_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(ISO31000_NODES)
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'iso_31000'",
        count,
    )

    return count
