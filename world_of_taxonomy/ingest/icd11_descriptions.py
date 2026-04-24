"""Parser for the WHO ICD-11 MMS Simple Tabulation file.

WHO publishes the Mortality and Morbidity Statistics linearization as
``SimpleTabulation-ICD-11-MMS-en.txt`` (tab-delimited, UTF-8 with BOM,
also shipped as ``.xlsx`` and inside a ZIP). The structural ingester
keeps only Code and Title; this module surfaces the ``CodingNote``
column -- free-text guidance like "Use additional code if desired, to
identify any associated condition" -- into
``classification_node.description``.

Coverage from this source is intentionally thin (~1.6% of codes) since
the tabulation does not carry the formal Definition / Inclusion /
Exclusion fields that live only in the WHO ICD-11 API. Those are
deferred to a separate API-based backfill.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Iterable

_EM_DASH = "\u2014"
_BOM = "\ufeff"


def parse_icd11_simple_tabulation(path: Path) -> Dict[str, str]:
    """Return ``{code: markdown_description}`` for every row that has
    both a ``Code`` and a non-empty ``CodingNote``.

    Accepts either the raw ``.txt`` or the WHO-style ZIP.
    """
    out: Dict[str, str] = {}
    for header, row in _iter_rows(path):
        code = _col(row, header, "Code").strip()
        if not code:
            continue
        note = _col(row, header, "CodingNote").strip()
        if not note:
            continue
        rendered = f"**Coding note:** {note}".replace(_EM_DASH, "-")
        out[code] = rendered
    return out


def _col(row: list[str], header: list[str], name: str) -> str:
    try:
        idx = header.index(name)
    except ValueError:
        return ""
    if idx >= len(row):
        return ""
    return row[idx]


def _iter_rows(path: Path) -> Iterable[tuple[list[str], list[str]]]:
    for raw in _iter_text(path):
        lines = raw.splitlines()
        if not lines:
            continue
        header_line = lines[0].lstrip(_BOM)
        header = header_line.split("\t")
        for line in lines[1:]:
            if not line.strip():
                continue
            yield header, line.split("\t")


def _iter_text(path: Path) -> Iterable[str]:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            members = [
                n for n in z.namelist()
                if n.lower().endswith(".txt") and "icd-11" in n.lower()
            ]
            for name in members:
                with z.open(name) as fh:
                    yield fh.read().decode("utf-8", errors="replace")
        return
    yield p.read_text(encoding="utf-8", errors="replace")
