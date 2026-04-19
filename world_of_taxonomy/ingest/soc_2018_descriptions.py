"""Parser for SOC 2018 descriptions via the O*NET occupation data file.

BLS publishes SOC 2018 definitions as an XLSX that is not directly
downloadable without a browser-level request. O*NET (the National
Center for O*NET Development, funded by BLS) publishes the same
occupation descriptions as a tab-delimited file under an O*NET-SOC
code scheme:

    11-1011.00 -> SOC 11-1011 (base row, applies to the 6-digit code)
    11-1011.03 -> O*NET extension (more specific than SOC, not used here)

Only base rows (`.00` suffix) contribute descriptions so the 6-digit
SOC code's description is not overwritten by extension-specific prose.

Source (tab-delimited):
    https://www.onetcenter.org/dl_files/database/db_XX_0_text/Occupation%20Data.txt
Locally cached at: data/onet_occupation_data.txt
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict


def parse_soc_2018_descriptions_txt(path: Path) -> Dict[str, str]:
    """Return `{soc_code: description}` from O*NET occupation data.

    Only rows whose O*NET-SOC code ends in `.00` contribute, because
    those map 1:1 to the 6-digit SOC code. Rows with empty descriptions
    are skipped.
    """
    out: Dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            onet_code = (row.get("O*NET-SOC Code") or "").strip()
            desc = (row.get("Description") or "").strip()
            if not onet_code or not desc:
                continue
            if "." not in onet_code:
                continue
            soc_code, suffix = onet_code.rsplit(".", 1)
            if suffix != "00":
                continue
            out[soc_code] = desc
    return out
