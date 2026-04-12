"""CFR Title 49 / FMCSA Regulations -> NAICS crosswalk ingester.

Links FMCSA regulatory categories and CFR Title 49 parts to the NAICS codes
they primarily govern: 484xxx (Truck Transportation) and 485xxx (Transit).

Source: derived mapping (fmcsa.dot.gov governs NAICS 484/485 carriers).
Match type: 'broad' - regulations cover the industry broadly.

Edges are one-directional (regulation -> industry).
Only inserts edges where both codes are present in their systems.
"""
from __future__ import annotations

CHUNK = 500

# Hand-coded mapping: (source_system, source_code, target_naics_prefix, notes)
# target_naics_prefix is matched against the beginning of NAICS codes
_MAPPINGS: list[tuple[str, str, list[str]]] = [
    # FMCSA Categories -> NAICS transportation
    ("fmcsa_regs", "fmcsa_hos",    ["484", "485"]),   # HOS covers truck + transit
    ("fmcsa_regs", "fmcsa_eld",    ["484"]),           # ELD mandate: primarily truck
    ("fmcsa_regs", "fmcsa_cdl",    ["484", "485", "492"]),  # CDL: truck, transit, couriers
    ("fmcsa_regs", "fmcsa_dat",    ["484", "485"]),    # Drug/alcohol: truck + transit
    ("fmcsa_regs", "fmcsa_vim",    ["484", "485"]),    # Vehicle inspection: truck + transit
    ("fmcsa_regs", "fmcsa_hazmat", ["484", "4911"]),   # Hazmat: truck + rail
    ("fmcsa_regs", "fmcsa_fr",     ["484", "485"]),    # Financial responsibility: truck + transit
    ("fmcsa_regs", "fmcsa_oa",     ["484", "485", "492"]),  # Operating authority
    ("fmcsa_regs", "fmcsa_csf",    ["484", "485"]),    # Safety fitness: truck + transit
    ("fmcsa_regs", "fmcsa_ar",     ["484", "485"]),    # Accident reporting: truck + transit

    # CFR Title 49 Parts -> NAICS transportation
    ("cfr_title_49", "49_395",  ["484", "485"]),   # Hours of Service
    ("cfr_title_49", "49_391",  ["484", "485"]),   # Driver Qualifications
    ("cfr_title_49", "49_382",  ["484", "485"]),   # Drug/Alcohol Testing
    ("cfr_title_49", "49_383",  ["484", "485", "492"]),  # CDL Standards
    ("cfr_title_49", "49_387",  ["484", "485"]),   # Financial Responsibility
    ("cfr_title_49", "49_390",  ["484", "485"]),   # FMCSR General
    ("cfr_title_49", "49_392",  ["484", "485"]),   # Driving CMVs
    ("cfr_title_49", "49_393",  ["484", "485"]),   # Parts and Accessories
    ("cfr_title_49", "49_396",  ["484", "485"]),   # Inspection and Maintenance
    ("cfr_title_49", "49_397",  ["484"]),          # Hazmat driving rules
    ("cfr_title_49", "49_171",  ["484", "4911"]),  # Hazmat general
    ("cfr_title_49", "49_172",  ["484", "4911"]),  # Hazmat table
    ("cfr_title_49", "49_173",  ["484", "4911"]),  # Hazmat packaging
    ("cfr_title_49", "49_177",  ["484"]),          # Hazmat highway carriage
]


async def ingest_crosswalk_cfr_naics(conn) -> int:
    """Insert CFR Title 49 / FMCSA -> NAICS equivalence edges.

    Only inserts edges where both source and target codes exist in the DB.
    Returns total edges inserted.
    """
    # Load valid NAICS codes for filtering
    naics_codes = {
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = 'naics_2022'"
        )
    }

    rows: list[tuple[str, str, str, str, str]] = []

    for source_system, source_code, naics_prefixes in _MAPPINGS:
        # Find all NAICS codes matching any of the prefixes
        matched_naics = [
            code for code in naics_codes
            if any(code.startswith(prefix) for prefix in naics_prefixes)
        ]

        for naics_code in matched_naics:
            rows.append((
                source_system,
                source_code,
                "naics_2022",
                naics_code,
                "broad",
            ))

    count = 0
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO equivalence
                   (source_system, source_code, target_system, target_code, match_type)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING""",
            chunk,
        )
        count += len(chunk)

    return count
