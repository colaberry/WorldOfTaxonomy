"""Crosswalk between HS 2022 and ISIC Rev 4.

Source: World Bank WITS HS 2012 -> ISIC Rev 3 concordance
        https://wits.worldbank.org/data/public/concordance/Concordance_H4_to_I3.zip
        Cached as data/hs_isic_wits.csv (hs_code, isic_code columns).
License: World Bank open data (CC BY 4.0)

Match type: 'broad' because the source is HS 2012 (not 2022) matched to
ISIC Rev 3 (not Rev 4). Edges are only inserted where both the HS code
exists in the hs_2022 system and the ISIC code exists in the isic_rev4
system, which provides structural compatibility.

~1,505 pairs -> ~3,010 bidirectional edges.
"""
import csv
import urllib.request
import zipfile
import io

DATA_URL = (
    "https://wits.worldbank.org/data/public/concordance/Concordance_H4_to_I3.zip"
)
DATA_PATH = "data/hs_isic_wits.csv"


def _download_concordance(path: str) -> None:
    """Download the WITS HS-ISIC concordance ZIP and extract to a flat CSV."""
    import os
    if os.path.exists(path):
        return
    req = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=30).read()
    z = zipfile.ZipFile(io.BytesIO(data))
    content = z.read(z.namelist()[0]).decode("utf-8", errors="replace")
    rows = list(csv.DictReader(content.splitlines()))
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hs_code", "isic_code"])
        for row in rows:
            writer.writerow([
                row["HS 2012 Product Code"],
                row["ISIC Revision 3 Product Code"],
            ])


async def ingest_crosswalk_hs_isic(conn, path=None) -> int:
    """Insert bidirectional equivalence edges between hs_2022 and isic_rev4.

    Only inserts edges where both the HS subheading and the ISIC code
    exist in the database. Uses match_type='broad' to indicate version
    differences (HS 2012 vs 2022, ISIC Rev 3 vs Rev 4).

    Returns total number of edges inserted (both directions).
    """
    path = path or DATA_PATH
    _download_concordance(path)

    # Load concordance pairs from CSV
    pairs = []
    seen = set()
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hs = row["hs_code"].strip()
            isic = row["isic_code"].strip()
            key = (hs, isic)
            if hs and isic and key not in seen:
                seen.add(key)
                pairs.append((hs, isic))

    # Get existing codes from DB (only insert where both nodes exist)
    hs_codes = {r["code"] for r in await conn.fetch(
        "SELECT code FROM classification_node WHERE system_id = 'hs_2022'"
    )}
    isic_codes = {r["code"] for r in await conn.fetch(
        "SELECT code FROM classification_node WHERE system_id = 'isic_rev4'"
    )}

    # Filter to valid pairs and build records
    forward = [
        ("hs_2022", hs, "isic_rev4", isic, "broad")
        for hs, isic in pairs
        if hs in hs_codes and isic in isic_codes
    ]
    reverse = [
        ("isic_rev4", isic, "hs_2022", hs, "broad")
        for hs, isic in pairs
        if hs in hs_codes and isic in isic_codes
    ]
    records = forward + reverse

    if not records:
        return 0

    # Batch insert
    CHUNK = 500
    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO equivalence
                   (source_system, source_code, target_system, target_code, match_type)
               VALUES ($1,$2,$3,$4,$5)
               ON CONFLICT DO NOTHING""",
            chunk,
        )
        count += len(chunk)

    return count
