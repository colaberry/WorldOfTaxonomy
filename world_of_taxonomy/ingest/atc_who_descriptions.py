"""Parser for WHO ATC defined-daily-dose + coding notes.

The structural ingester persists only ``atc_code`` and ``atc_name``
(which becomes the node title). The upstream WHO ATC/DDD file also
publishes a defined daily dose (``ddd`` + ``uom``), an administration
route (``adm_r``), and occasional coding notes for about 40% of codes
-- all useful context that clinical users look up. This module turns
each row into a small markdown block and keys it by ``atc_code``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Mapping

_EM_DASH = "\u2014"
_NA = "NA"

_ROUTE_CODES: Mapping[str, str] = {
    "O": "oral",
    "P": "parenteral",
    "R": "rectal",
    "N": "nasal",
    "V": "vaginal",
    "SL": "sublingual",
    "TD": "transdermal",
}


def route_label(code: str) -> str:
    """Return a human-readable route label.

    Single-letter WHO codes (``O``, ``P``, ...) expand to words;
    already-verbose strings (``Inhal.powder``, ``oral aerosol``) pass
    through unchanged. ``NA`` and empty return empty string.
    """
    if not code or code == _NA:
        return ""
    return _ROUTE_CODES.get(code, code)


def render_row(row: Mapping[str, str]) -> str:
    """Return a markdown description for one ATC CSV row, or ``""``
    when no DDD / route / note content is available.
    """
    parts: list[str] = []
    ddd = (row.get("ddd") or "").strip()
    uom = (row.get("uom") or "").strip()
    route = route_label((row.get("adm_r") or "").strip())
    note = (row.get("note") or "").strip()

    if ddd and ddd != _NA:
        dose = ddd
        if uom and uom != _NA:
            dose = f"{ddd} {uom}"
        if route:
            parts.append(f"**Defined daily dose:** {dose} ({route})")
        else:
            parts.append(f"**Defined daily dose:** {dose}")

    if note and note != _NA:
        parts.append(f"**Note:** {note}")

    return "\n\n".join(parts).replace(_EM_DASH, "-")


def parse_atc_who_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{atc_code: markdown_description}`` for every row with content."""
    out: Dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            code = (row.get("atc_code") or "").strip()
            if not code:
                continue
            rendered = render_row(row)
            if rendered:
                out[code] = rendered
    return out
