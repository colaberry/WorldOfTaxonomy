"""Parser for the NCES CIP 2020 descriptions CSV.

Source:
    https://nces.ed.gov/ipeds/cipcode/Files/CIPCode2020.csv

Columns: CIPFamily, CIPCode, Action, TextChange, CIPTitle, CIPDefinition, ...

The structural ingester at `cip_2020.py` reads the same file but only
pulls the title column; this module extracts the `CIPDefinition` prose
for the description backfill. Codes use an Excel-escape prefix
(`="01.0101"`) that is stripped before use.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict


def parse_cip_2020_descriptions_csv(path: Path) -> Dict[str, str]:
    """Return `{code: definition}` for every non-deleted row with a definition.

    Rows whose `Action` column contains "deleted" are skipped so the
    backfill does not persist definitions for retired codes. Empty
    definitions are also dropped.
    """
    out: Dict[str, str] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            code = _clean_code(row.get("CIPCode", ""))
            action = (row.get("Action") or "").strip().lower()
            defn = (row.get("CIPDefinition") or "").strip()
            if not code or not defn or action == "deleted":
                continue
            out[code] = defn
    return out


def _clean_code(raw: str) -> str:
    """Strip Excel-escape prefix ='...' from CIP code strings."""
    return re.sub(r'^=?"?|"$', "", raw).strip()
