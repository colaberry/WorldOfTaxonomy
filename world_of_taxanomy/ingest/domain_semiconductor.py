"""Next-Generation Semiconductor domain taxonomy ingester.

Organizes next-gen semiconductor sector types aligned with
NAICS 3344 (Semiconductor mfg), NAICS 5415 (Design services),
and NAICS 5417 (R&D).

Code prefix: dsc_
Categories: logic chips, memory, analog/mixed-signal, power semiconductors,
photonics ICs, MEMS, advanced packaging, foundry/process nodes.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
SEMICONDUCTOR_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Logic Chips --
    ("dsc_logic",           "Logic Chips",                                           1, None),
    ("dsc_logic_cpu",       "Central Processing Units (CPU - x86, ARM, RISC-V)",    2, "dsc_logic"),
    ("dsc_logic_gpu",       "Graphics and AI Accelerators (GPU, NPU, TPU)",         2, "dsc_logic"),
    ("dsc_logic_fpga",      "FPGAs and Programmable Logic Devices (Xilinx, Intel)", 2, "dsc_logic"),
    ("dsc_logic_asic",      "Custom ASICs and SoC (mobile, networking, crypto mining)",2, "dsc_logic"),

    # -- Memory --
    ("dsc_mem",             "Memory Semiconductors",                                  1, None),
    ("dsc_mem_dram",        "DRAM (DDR5, LPDDR5, HBM - Samsung, SK Hynix, Micron)", 2, "dsc_mem"),
    ("dsc_mem_nand",        "NAND Flash (3D NAND, QLC - enterprise and consumer)",  2, "dsc_mem"),
    ("dsc_mem_emerging",    "Emerging Memory (MRAM, PCM, ReRAM, 3D XPoint)",        2, "dsc_mem"),

    # -- Analog and Mixed-Signal --
    ("dsc_analog",          "Analog and Mixed-Signal ICs",                           1, None),
    ("dsc_analog_adc",      "Data Converters (ADC, DAC, sigma-delta)",              2, "dsc_analog"),
    ("dsc_analog_rf",       "RF and Microwave ICs (PA, LNA, transceivers)",         2, "dsc_analog"),
    ("dsc_analog_pmic",     "Power Management ICs (PMIC, voltage regulators, DCDC)",2, "dsc_analog"),

    # -- Power Semiconductors --
    ("dsc_power",           "Power Semiconductors",                                  1, None),
    ("dsc_power_sic",       "Silicon Carbide (SiC) MOSFETs and Diodes",             2, "dsc_power"),
    ("dsc_power_gan",       "Gallium Nitride (GaN) HEMTs and Power ICs",            2, "dsc_power"),
    ("dsc_power_igbt",      "IGBTs and High-Voltage Silicon Power Devices",         2, "dsc_power"),

    # -- Photonics ICs --
    ("dsc_phot",            "Photonics Integrated Circuits",                         1, None),
    ("dsc_phot_silicon",    "Silicon Photonics (optical interconnects, LiDAR)",     2, "dsc_phot"),
    ("dsc_phot_iii_v",      "III-V Photonics (GaAs, InP lasers, vertical cavity)",  2, "dsc_phot"),

    # -- MEMS --
    ("dsc_mems",            "MEMS and Microsensors",                                 1, None),
    ("dsc_mems_sensor",     "MEMS Sensors (inertial, pressure, microphone, flow)",  2, "dsc_mems"),
    ("dsc_mems_rf",         "RF MEMS (filters, switches, resonators)",              2, "dsc_mems"),

    # -- Advanced Packaging --
    ("dsc_pkg",             "Advanced Semiconductor Packaging",                      1, None),
    ("dsc_pkg_2d5",         "2.5D Packaging (interposer, CoWoS, EMIB chiplets)",    2, "dsc_pkg"),
    ("dsc_pkg_3d",          "3D IC Stacking (HBM, die stacking, face-to-face)",     2, "dsc_pkg"),
    ("dsc_pkg_chiplet",     "Chiplet and Multi-Die Module Architecture",            2, "dsc_pkg"),

    # -- Foundry and Process Technology --
    ("dsc_fab",             "Foundry and Fabrication Process Nodes",                 1, None),
    ("dsc_fab_leading",     "Leading-Edge Nodes (under 5nm - TSMC, Samsung, Intel)",2, "dsc_fab"),
    ("dsc_fab_mature",      "Mature Nodes (28nm and above - high-volume, mature)",  2, "dsc_fab"),
    ("dsc_fab_specialty",   "Specialty Process (BCD, SOI, SiGe, compound semi fab)",2, "dsc_fab"),
]

_DOMAIN_ROW = (
    "domain_semiconductor",
    "Next-Generation Semiconductor Types",
    "Logic chips, memory, analog/mixed-signal, power semiconductors, "
    "photonics, MEMS, advanced packaging and foundry process taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 3344 (Semiconductor mfg), 5415 (Design), 5417 (R&D)
_NAICS_PREFIXES = ["3344", "5415", "5417"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific semiconductor types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_semiconductor(conn) -> int:
    """Ingest Next-Generation Semiconductor domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_semiconductor'), and links NAICS 3344/5415/5417 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_semiconductor",
        "Next-Generation Semiconductor Types",
        "Logic chips, memory, analog/mixed-signal, power semiconductors, "
        "photonics, MEMS, advanced packaging and foundry process taxonomy",
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

    parent_codes = {parent for _, _, _, parent in SEMICONDUCTOR_NODES if parent is not None}

    rows = [
        (
            "domain_semiconductor",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in SEMICONDUCTOR_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(SEMICONDUCTOR_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_semiconductor'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_semiconductor'",
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
            [("naics_2022", code, "domain_semiconductor", "primary") for code in naics_codes],
        )

    return count
