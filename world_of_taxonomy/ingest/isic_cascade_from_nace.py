"""Cascade NACE Rev 2 descriptions to ISIC Rev 4 codes.

NACE Rev 2 is a European breakdown of ISIC Rev 4 but does NOT always
preserve ISIC's 4-digit class numbering: when NACE subdivides an ISIC
class it often renumbers. For example ISIC ``4661`` ("Wholesale of
solid, liquid and gaseous fuels") maps to NACE ``46.71``, while NACE
``46.61`` is an unrelated class ("Wholesale of agricultural
machinery"). A naive key-by-suffix cascade would therefore attach the
wrong note to many ISIC codes.

This module uses the on-disk ISIC4 <-> NACE2 crosswalk
(``data/crosswalk/ISIC4_to_NACE2.txt``, shipped with the existing
NACE ingester) to build a correct mapping:

* Only ISIC codes that map to exactly one NACE code are kept.
* Both ``ISIC4part`` and ``NACE2part`` must be ``0`` (exact match).
* The NACE code (dots stripped) must have an English note in the RDF
  cache populated by ``scripts/backfill_nace_descriptions.py``.

The helper ``build_mapping_from_cache`` remains available for
diagnostics (it returns ``{uri_suffix: markdown}``).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

from world_of_taxonomy.ingest.nace_descriptions import (
    parse_concept_rdf,
    render_description,
)


def build_mapping_from_cache(cache_dir: Path) -> Dict[str, str]:
    """Walk ``cache_dir`` and return ``{uri_suffix: markdown}``.

    The filename stem is treated as the URI suffix. Malformed XML and
    files lacking English notes are silently skipped.
    """
    out: Dict[str, str] = {}
    for path in sorted(Path(cache_dir).glob("*.xml")):
        suffix = path.stem
        try:
            parts = parse_concept_rdf(path.read_bytes(), uri_suffix=suffix)
        except ET.ParseError:
            continue
        body = render_description(parts)
        if body:
            out[suffix] = body
    return out


def _load_crosswalk(path: Path) -> Dict[str, List[Tuple[str, str, str]]]:
    """Return ``{isic_code: [(nace_code, isic_part, nace_part), ...]}``."""
    out: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            isic = (row.get("ISIC4code") or "").strip()
            nace = (row.get("NACE2code") or "").strip()
            if not isic or not nace:
                continue
            ipart = (row.get("ISIC4part") or "").strip()
            npart = (row.get("NACE2part") or "").strip()
            out[isic].append((nace, ipart, npart))
    return dict(out)


def build_isic_mapping(
    *,
    cache_dir: Path,
    crosswalk_path: Path,
) -> Dict[str, str]:
    """Return ``{isic_code: markdown}`` for every ISIC code that maps 1:1
    to exactly one NACE code with a non-empty English note.

    Filters:

    * Skip ISIC codes that map to more than one NACE code (NACE split).
    * Skip rows where either ``ISIC4part`` or ``NACE2part`` is not
      ``"0"`` (partial correspondences are not safe to surface as a
      single description).
    * Skip when the target NACE code has no English note in the cache.
    """
    nace_notes = build_mapping_from_cache(cache_dir)
    crosswalk = _load_crosswalk(crosswalk_path)

    out: Dict[str, str] = {}
    for isic, rows in crosswalk.items():
        if len(rows) != 1:
            continue
        nace, ipart, npart = rows[0]
        if ipart != "0" or npart != "0":
            continue
        uri_suffix = nace.replace(".", "")
        body = nace_notes.get(uri_suffix)
        if not body:
            continue
        out[isic] = body
    return out
