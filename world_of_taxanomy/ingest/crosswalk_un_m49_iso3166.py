"""Crosswalk between UN M.49 and ISO 3166-1 country codes.

Links un_m49 numeric country codes (e.g. "840" = USA)
to iso_3166_1 alpha-2 country codes (e.g. "US").

Source: data/iso3166_all.csv already has both country-code (M.49 numeric)
        and alpha-2 columns side by side.
Match type: exact (same country, different code format/system).

~249 countries x 2 directions = ~498 edges.
"""
import csv

DATA_PATH = "data/iso3166_all.csv"


async def ingest_crosswalk_un_m49_iso3166(conn, path=None) -> int:
    """Insert bidirectional equivalence edges between un_m49 and iso_3166_1.

    Returns total number of edges inserted.
    """
    path = path or DATA_PATH

    # Build mapping: m49_numeric_code -> alpha2, filtered to rows that have both
    mapping: list[tuple[str, str]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        seen = set()
        for row in reader:
            cc = row.get("country-code", "").strip()
            a2 = row.get("alpha-2", "").strip()
            if cc and a2:
                m49 = str(int(cc)).zfill(3)
                key = (m49, a2)
                if key not in seen:
                    seen.add(key)
                    mapping.append((m49, a2))

    # Only insert edges where both nodes exist in the DB
    m49_codes = {r["code"] for r in await conn.fetch(
        "SELECT code FROM classification_node WHERE system_id = 'un_m49'"
    )}
    iso_codes = {r["code"] for r in await conn.fetch(
        "SELECT code FROM classification_node WHERE system_id = 'iso_3166_1'"
    )}

    count = 0
    for m49_code, alpha2 in sorted(mapping):
        if m49_code not in m49_codes or alpha2 not in iso_codes:
            continue

        # Forward: un_m49 -> iso_3166_1
        await conn.execute(
            """INSERT INTO equivalence
                   (source_system, source_code, target_system, target_code, match_type)
               VALUES ($1,$2,$3,$4,$5)
               ON CONFLICT DO NOTHING""",
            "un_m49", m49_code, "iso_3166_1", alpha2, "exact",
        )
        count += 1

        # Reverse: iso_3166_1 -> un_m49
        await conn.execute(
            """INSERT INTO equivalence
                   (source_system, source_code, target_system, target_code, match_type)
               VALUES ($1,$2,$3,$4,$5)
               ON CONFLICT DO NOTHING""",
            "iso_3166_1", alpha2, "un_m49", m49_code, "exact",
        )
        count += 1

    return count
