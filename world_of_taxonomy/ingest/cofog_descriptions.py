"""Parser for COFOG (UN Classification of the Functions of Government)
explanatory notes.

The file ``data/cofog.csv`` is the canonical UN publication with columns
``Code``, ``Description_EN``, ``Description_FR``, ``Description_ES``,
``ExplanatoryNote``. The note text is typically the title followed by
bulleted items separated by the minus sign ``U+2212`` and an optional
"Excludes :" section. We strip the redundant title prefix, normalize
``U+2212`` to a hyphen, and collapse whitespace.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict

_EM_DASH = "\u2014"
_MINUS = "\u2212"
_WS = re.compile(r"\s+")


def render_note(note: str, *, title: str) -> str:
    """Return a cleaned markdown description for one COFOG row.

    Strips a leading-title prefix (COFOG repeats the title at the start
    of many notes), normalizes ``U+2212`` minus signs to hyphens, and
    collapses runs of whitespace.
    """
    s = (note or "").strip()
    if not s:
        return ""
    t = (title or "").strip()
    if t and s.startswith(t):
        s = s[len(t):].strip()
    s = s.replace(_MINUS, "-").replace(_EM_DASH, "-")
    s = _WS.sub(" ", s)
    return s.strip()


def parse_cofog_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{code: markdown_description}`` for every COFOG row with a
    non-empty ExplanatoryNote."""
    out: Dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            code = (row.get("Code") or "").strip()
            title = (row.get("Description_EN") or "").strip()
            note = (row.get("ExplanatoryNote") or "").strip()
            if not code or not note:
                continue
            rendered = render_note(note, title=title)
            if rendered:
                out[code] = rendered
    return out
