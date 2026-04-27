"""Parser for O*NET-SOC Occupation Data descriptions.

The U.S. Department of Labor publishes ``onet_occupation_data.txt`` as
a tab-separated file with three columns: ``O*NET-SOC Code``, ``Title``,
``Description``. The Description is a clean 2-3 sentence occupation
profile that our structural ingester does not persist. This parser
reads the file and returns ``{code: description}``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

_EM_DASH = "\u2014"


def parse_onet_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{onet_soc_code: description}`` for every non-empty row."""
    out: Dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            code = (row.get("O*NET-SOC Code") or "").strip()
            desc = (row.get("Description") or "").strip()
            if not code or not desc:
                continue
            out[code] = desc.replace(_EM_DASH, "-")
    return out
