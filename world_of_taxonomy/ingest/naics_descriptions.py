"""Parser for the Census Bureau NAICS 2022 descriptions XLSX.

Source:
    https://www.census.gov/naics/2022NAICS/2022_NAICS_Descriptions.xlsx

Columns: Code | Title | Description. The structural ingester in
`naics.py` uses a different file (`2022_NAICS_Codes.xlsx`) that does
not carry the description prose, which is why descriptions need to be
backfilled separately.
"""

from pathlib import Path
from typing import Dict

import openpyxl


NAICS_2022_DESCRIPTIONS_URL = (
    "https://www.census.gov/naics/2022NAICS/2022_NAICS_Descriptions.xlsx"
)
NAICS_2022_DESCRIPTIONS_LOCAL = Path("data/naics/2022_NAICS_Descriptions.xlsx")


def parse_naics_descriptions_xlsx(path: Path) -> Dict[str, str]:
    """Return `{code: description}` for every row with a non-empty description.

    Numeric codes (Excel may load `111110` as a float) are coerced to
    their canonical string form. Rows without a description are skipped
    rather than mapped to empty strings, so the resulting dict can be
    passed straight to `apply_descriptions` without extra filtering.
    """
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb.active

    out: Dict[str, str] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if len(row) < 3:
            continue
        raw_code, _title, raw_desc = row[0], row[1], row[2]
        if raw_code is None or raw_desc is None:
            continue

        code = _stringify_code(raw_code)
        desc = str(raw_desc).strip()
        if not code or not desc:
            continue
        # Census source uses 'NULL' as a sentinel on codes that inherit
        # description from their parent level; treat as missing.
        if desc.upper() == "NULL":
            continue

        out[code] = desc

    wb.close()
    return out


def _stringify_code(raw) -> str:
    if isinstance(raw, float) and raw.is_integer():
        return str(int(raw))
    return str(raw).strip()
