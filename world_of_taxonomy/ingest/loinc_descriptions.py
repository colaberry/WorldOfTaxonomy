"""Parser for LOINC descriptions from the Regenstrief LoincTable CSV.

LOINC codes are defined by a six-axis structure: Component, Property,
Time aspect, System, Scale type, and (optionally) Method type. The
``LONG_COMMON_NAME`` column that the structural ingester uses for the
node title is a concatenation of those axes plus some glue; surfacing
the axes separately is the whole point of a description backfill.

This parser composes a markdown narrative with the six axes, the
short name (Regenstrief's compact label), and -- when present -- the
free-text ``DefinitionDescription`` prose. Deprecated and discouraged
codes are skipped to match the structural ingester.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Optional


_AXIS_COLUMNS: list[tuple[str, str]] = [
    ("COMPONENT", "Component"),
    ("PROPERTY", "Property"),
    ("TIME_ASPCT", "Time aspect"),
    ("SYSTEM", "System"),
    ("SCALE_TYP", "Scale"),
    ("METHOD_TYP", "Method"),
]


def parse_loinc_descriptions_csv(path: Path) -> Dict[str, str]:
    """Return ``{loinc_num: markdown_description}`` for every active code.

    Skips DEPRECATED and DISCOURAGED rows, plus rows with neither any
    six-axis value nor a free-text definition.
    """
    out: Dict[str, str] = {}
    for row in _iter_rows(path):
        code = (row.get("LOINC_NUM") or "").strip()
        if not code:
            continue
        status = (row.get("STATUS") or "").strip().upper()
        if status in ("DEPRECATED", "DISCOURAGED") or not status:
            continue

        desc = _render_row(row)
        if desc:
            out[code] = desc
    return out


def _render_row(row: dict) -> Optional[str]:
    lines: list[str] = []
    for col, label in _AXIS_COLUMNS:
        value = (row.get(col) or "").strip()
        if value:
            lines.append(f"**{label}:** {value}")

    short = (row.get("SHORTNAME") or "").strip()
    defn = (row.get("DefinitionDescription") or "").strip()

    if not lines and not defn:
        return None

    blocks: list[str] = []
    if lines:
        blocks.append("\n".join(lines))
    if short:
        blocks.append(f"**Short name:** {short}")
    if defn:
        blocks.append(f"**Definition:**\n{defn}")
    return "\n\n".join(blocks)


def _iter_rows(path: Path) -> Iterable[dict]:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            member = next(
                (n for n in z.namelist() if n.endswith("LoincTable/Loinc.csv")),
                None,
            )
            if member is None:
                raise FileNotFoundError(f"No LoincTable/Loinc.csv inside {p}")
            with z.open(member) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8-sig")
                yield from csv.DictReader(text)
        return
    with open(p, newline="", encoding="utf-8-sig") as fh:
        yield from csv.DictReader(fh)
