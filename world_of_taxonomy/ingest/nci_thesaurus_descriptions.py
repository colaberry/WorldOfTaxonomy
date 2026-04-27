"""Parser for NCI Thesaurus descriptions from the EVS flat file.

The structural ingester at :mod:`world_of_taxonomy.ingest.nci_thesaurus`
persists only the code, first synonym, and first parent. The flat file
also carries, on the same row:

* Column 4 (``cols[3]``) -- pipe-delimited synonyms (first = display
  name, rest = alternate labels worth surfacing as aliases).
* Column 5 (``cols[4]``) -- free-text definition.
* Column 7 (``cols[6]``) -- concept status (e.g., ``Retired_Concept``,
  ``Header_Concept``). Used as a fallback description when no other
  content is present so retired/obsolete concepts still get a non-empty
  description.
* Column 8 (``cols[7]``) -- semantic type (e.g., ``Disease or Syndrome``).

This parser composes those pieces into a markdown narrative for the
description backfill. Em-dashes are replaced with hyphens to comply
with the project-wide em-dash prohibition.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Iterable


_EM_DASH = "\u2014"


def parse_nci_thesaurus_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{concept_code: markdown_description}`` for every row with content.

    Skips only rows with no synonyms, no definition, no semantic type,
    AND no concept status. Rows that have only a concept status fall
    back to a status-only description.
    """
    out: Dict[str, str] = {}
    for code, syns, defn, status, sem in _iter_rows(path):
        desc = _render(syns, defn, status, sem)
        if desc:
            out[code] = desc
    return out


def _render(
    syns: list[str], defn: str, status: str, sem: str,
) -> str | None:
    alt_synonyms = [s for s in syns[1:] if s]
    blocks: list[str] = []
    if sem:
        blocks.append(f"**Semantic type:** {sem}")
    if defn:
        blocks.append(f"**Definition:**\n{defn}")
    if alt_synonyms:
        lines = ["**Synonyms:**"] + [f"- {s}" for s in alt_synonyms]
        blocks.append("\n".join(lines))
    # Concept status is shown as a fallback when nothing richer is
    # present; otherwise it would clutter the typical record.
    if status and not blocks:
        blocks.append(f"**Concept status:** {status}")
    if not blocks:
        return None
    return "\n\n".join(blocks).replace(_EM_DASH, "-")


def _iter_rows(
    path: Path,
) -> Iterable[tuple[str, list[str], str, str, str]]:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            member = next(
                (n for n in z.namelist() if n.endswith(".txt")),
                None,
            )
            if member is None:
                raise FileNotFoundError(f"No Thesaurus.txt inside {p}")
            raw = z.read(member).decode("utf-8", errors="replace")
    else:
        raw = p.read_text(encoding="utf-8", errors="replace")

    for line in raw.splitlines():
        cols = line.split("\t")
        if len(cols) < 5:
            continue
        code = cols[0].strip()
        if not code:
            continue
        syns = [s.strip() for s in cols[3].split("|")]
        defn = cols[4].strip()
        status = cols[6].strip() if len(cols) > 6 else ""
        sem = cols[7].strip() if len(cols) > 7 else ""
        yield code, syns, defn, status, sem
