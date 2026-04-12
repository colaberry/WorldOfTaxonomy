"""UN M.49 Geographic Regions ingester.

Source: Derived from ISO 3166-1 CSV (lukes/ISO-3166-Countries-with-Regional-Codes)
        which includes UN M.49 region/sub-region/country codes.
        Primary source: unstats.un.org/unsd/methodology/m49/overview
License: open (UN Statistics Division)

Hierarchy:
  L0 - World (code "001")
  L1 - Region (e.g. "002" Africa, "019" Americas, "142" Asia)
  L2 - Sub-region (e.g. "014" Eastern Africa, "021" Northern America)
  L3 - Country (M.49 numeric code, e.g. "840" United States)

Uses the same data/iso3166_all.csv already downloaded by the iso3166_1 ingester.
The CSV has both "sub-region-code" and "intermediate-region-code" columns; both
map to L2 in the UN M.49 standard.
"""
import csv
from typing import Optional

from world_of_taxanomy.ingest.base import ensure_data_file

DATA_URL = (
    "https://raw.githubusercontent.com/lukes/"
    "ISO-3166-Countries-with-Regional-Codes/master/all/all.csv"
)
DATA_PATH = "data/iso3166_all.csv"

_WORLD_CODE = "001"
_WORLD_NAME = "World"

# Top-level geographic regions (L1) per UN M.49
_REGION_CODES = frozenset({"002", "009", "019", "142", "150"})

# Geographic sub-regions and intermediate regions (L2) per UN M.49
# Derived from both "sub-region-code" and "intermediate-region-code" columns
_SUBREGION_CODES = frozenset({
    "005", "011", "013", "014", "015", "017", "018", "021", "029",
    "030", "034", "035", "039", "053", "054", "057", "061",
    "143", "145", "151", "154", "155", "202", "419",
})


def _determine_level(code: str, level: int = None) -> int:
    """Return hierarchy level. If level is provided directly, return it.

    World = 0, Region = 1, Sub-region = 2, Country = 3.
    """
    if level is not None:
        return level
    if code == _WORLD_CODE:
        return 0
    if code in _REGION_CODES:
        return 1
    if code in _SUBREGION_CODES:
        return 2
    return 3  # numeric country code


def _determine_parent(
    code: str,
    level: int,
    region_code: Optional[str] = None,
    subregion_code: Optional[str] = None,
) -> Optional[str]:
    """Return parent code based on level.

    L0 (World): no parent
    L1 (Region): parent is World (001)
    L2 (Sub-region): parent is region_code (or World if missing)
    L3 (Country): parent is subregion_code (or World if missing)
    """
    if level == 0:
        return None
    if level == 1:
        return _WORLD_CODE
    if level == 2:
        return region_code if region_code else _WORLD_CODE
    if level == 3:
        return subregion_code if subregion_code else _WORLD_CODE
    return None


async def ingest_un_m49(conn, path=None) -> int:
    """Ingest UN M.49 geographic hierarchy into the database.

    Returns total number of nodes inserted.
    """
    path = path or DATA_PATH
    ensure_data_file(DATA_URL, path)

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "un_m49",
        "UN M.49",
        "UN M.49 Standard Country or Area Codes for Statistical Use",
        "2023",
        "Global",
        "United Nations Statistics Division",
    )

    # Parse CSV - reuses the iso3166_all.csv file
    # The CSV has "sub-region-code" and "intermediate-region-code" columns;
    # both are treated as L2 sub-regions per UN M.49.
    regions: dict[str, str] = {}        # code -> name
    subregions: dict[str, tuple] = {}   # code -> (name, region_code)
    countries: list[tuple] = []         # (m49_code, name, nearest_subregion_code)

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            rc = row.get("region-code", "").strip()
            src = row.get("sub-region-code", "").strip()
            irc = row.get("intermediate-region-code", "").strip()
            cc = row.get("country-code", "").strip()
            region_name = row.get("region", "").strip()
            subregion_name = row.get("sub-region", "").strip()
            intermediate_name = row.get("intermediate-region", "").strip()

            if rc:
                r = str(int(rc)).zfill(3)
                regions.setdefault(r, region_name)
            if src and rc:
                s = str(int(src)).zfill(3)
                r = str(int(rc)).zfill(3)
                subregions.setdefault(s, (subregion_name, r))
            if irc and rc:
                # intermediate region is a child of sub-region (or region if no sub-region)
                i = str(int(irc)).zfill(3)
                parent_sr = str(int(src)).zfill(3) if src else str(int(rc)).zfill(3)
                if i not in subregions:
                    subregions[i] = (intermediate_name, str(int(rc)).zfill(3))
            if cc:
                c = str(int(cc)).zfill(3)
                # prefer intermediate-region as parent, then sub-region
                nearest = irc or src
                s = str(int(nearest)).zfill(3) if nearest else None
                countries.append((c, name, s))

    seq = 0
    count = 0

    # -- Insert World node (L0) --
    seq += 1
    await conn.execute(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
           ON CONFLICT DO NOTHING""",
        "un_m49", _WORLD_CODE, _WORLD_NAME, 0, None, _WORLD_CODE, False, seq,
    )
    count += 1

    # -- Insert Region nodes (L1) --
    for code, title in sorted(regions.items()):
        seq += 1
        await conn.execute(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT DO NOTHING""",
            "un_m49", code, title, 1, _WORLD_CODE, code, False, seq,
        )
        count += 1

    # -- Insert Sub-region nodes (L2) --
    for code, (title, region_code) in sorted(subregions.items()):
        seq += 1
        parent = _determine_parent(code, level=2, region_code=region_code)
        await conn.execute(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT DO NOTHING""",
            "un_m49", code, title, 2, parent, region_code, False, seq,
        )
        count += 1

    # -- Insert Country nodes (L3) --
    for m49_code, name, subregion_code in sorted(countries):
        seq += 1
        parent = _determine_parent(m49_code, level=3, subregion_code=subregion_code)
        region_code = subregions[subregion_code][1] if subregion_code and subregion_code in subregions else _WORLD_CODE
        await conn.execute(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT DO NOTHING""",
            "un_m49", m49_code, name, 3, parent, region_code, True, seq,
        )
        count += 1

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, "un_m49",
    )
    return count
