"""Quantum Computing domain taxonomy ingester.

Organizes quantum computing sector types aligned with
NAICS 334 (Computer/electronic mfg), NAICS 5417 (R&D),
and NAICS 5415 (Computer systems design).

Code prefix: dqc_
Categories: qubit technologies, error correction, quantum sensing,
quantum networking, quantum software, quantum platforms.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
QUANTUM_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Qubit Technologies --
    ("dqc_qubit",           "Qubit Technologies",                                    1, None),
    ("dqc_qubit_sc",        "Superconducting Qubits (IBM, Google, Rigetti)",        2, "dqc_qubit"),
    ("dqc_qubit_ion",       "Trapped Ion Qubits (IonQ, Quantinuum, Oxford Ionics)", 2, "dqc_qubit"),
    ("dqc_qubit_photon",    "Photonic Qubits (PsiQuantum, QuiX Quantum)",           2, "dqc_qubit"),
    ("dqc_qubit_topo",      "Topological Qubits (Microsoft Station Q)",             2, "dqc_qubit"),

    # -- Error Correction --
    ("dqc_ecc",             "Quantum Error Correction",                              1, None),
    ("dqc_ecc_surface",     "Surface Code and Topological Error Correction",        2, "dqc_ecc"),
    ("dqc_ecc_fault",       "Fault-Tolerant Quantum Computing Architectures",       2, "dqc_ecc"),

    # -- Quantum Sensing --
    ("dqc_sense",           "Quantum Sensing and Metrology",                         1, None),
    ("dqc_sense_grav",      "Quantum Gravimetry and Inertial Navigation",           2, "dqc_sense"),
    ("dqc_sense_mag",       "Quantum Magnetometry (NV centers, SQUIDs)",            2, "dqc_sense"),
    ("dqc_sense_clock",     "Atomic Clocks and Precision Timekeeping",              2, "dqc_sense"),

    # -- Quantum Networking --
    ("dqc_net",             "Quantum Networking and Communications",                 1, None),
    ("dqc_net_qkd",         "Quantum Key Distribution (QKD) Networks",              2, "dqc_net"),
    ("dqc_net_repeat",      "Quantum Repeaters and Entanglement Distribution",      2, "dqc_net"),
    ("dqc_net_internet",    "Quantum Internet and Long-Distance Entanglement",      2, "dqc_net"),

    # -- Quantum Software --
    ("dqc_soft",            "Quantum Software and Algorithms",                       1, None),
    ("dqc_soft_algo",       "Quantum Algorithms (Shor, Grover, VQE, QAOA)",         2, "dqc_soft"),
    ("dqc_soft_compiler",   "Quantum Compilers and Circuit Optimization",           2, "dqc_soft"),
    ("dqc_soft_sim",        "Quantum Simulators and Classical Emulators",           2, "dqc_soft"),

    # -- Quantum Platforms --
    ("dqc_plat",            "Quantum Platforms and Cloud Access",                    1, None),
    ("dqc_plat_cloud",      "Quantum Cloud Services (IBM Quantum, AWS Braket)",     2, "dqc_plat"),
    ("dqc_plat_hybrid",     "Hybrid Quantum-Classical Computing Platforms",         2, "dqc_plat"),
]

_DOMAIN_ROW = (
    "domain_quantum",
    "Quantum Computing Types",
    "Qubit technologies, error correction, quantum sensing, "
    "quantum networking, quantum software and quantum platforms taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 334 (Computer/electronic mfg), 5417 (R&D), 5415 (Computer design)
_NAICS_PREFIXES = ["334", "5417", "5415"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific quantum types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_quantum(conn) -> int:
    """Ingest Quantum Computing domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_quantum'), and links NAICS 334/5417/5415 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_quantum",
        "Quantum Computing Types",
        "Qubit technologies, error correction, quantum sensing, "
        "quantum networking, quantum software and quantum platforms taxonomy",
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

    parent_codes = {parent for _, _, _, parent in QUANTUM_NODES if parent is not None}

    rows = [
        (
            "domain_quantum",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in QUANTUM_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(QUANTUM_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_quantum'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_quantum'",
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
            [("naics_2022", code, "domain_quantum", "primary") for code in naics_codes],
        )

    return count
