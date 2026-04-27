"""Parser for the O*NET Content Model Reference file.

``Content Model Reference.txt`` (inside the O*NET bulk-download zip)
lists every element in the ONET content hierarchy (Worker Characteristics,
Worker Requirements, Occupational Requirements, etc.) with a clean
prose description. The structural ingester for the per-area taxonomies
(``onet_knowledge``, ``onet_abilities``, ``onet_skills``,
``onet_work_activities``, ``onet_work_context``, ``onet_work_styles``,
``onet_interests``) stores each element under a compact local code
(e.g. ``ONA.01``) while the title matches ONET's ``Element Name``.
We index by the normalized ``Element Name`` so callers can do a title
lookup to populate descriptions.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

_EM_DASH = "\u2014"


def normalize_title(s: str) -> str:
    return (s or "").strip().lower()


def parse_content_model_reference(path: Path) -> Dict[str, str]:
    """Return ``{normalized_title: description}`` for every real element.

    Rows whose ``Description`` duplicates the ``Element Name`` (placeholder
    top-level categories like ``Worker Characteristics``) are skipped so
    the backfill does not overwrite meaningful titles with tautologies.
    """
    out: Dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            title = (row.get("Element Name") or "").strip()
            desc = (row.get("Description") or "").strip()
            if not title or not desc:
                continue
            if desc == title:
                continue
            out[normalize_title(title)] = desc.replace(_EM_DASH, "-")
    return out
