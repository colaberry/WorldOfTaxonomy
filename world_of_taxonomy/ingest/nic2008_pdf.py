"""Parser for MOSPI NIC 2008 publication PDF.

The Central Statistical Organisation of the Government of India
publishes the National Industrial Classification 2008 as a 193-page
PDF at
``https://www.mospi.gov.in/sites/default/files/main_menu/national_industrial_classification/nic_2008_17apr09.pdf``.
The "Detailed Structure" section (roughly pages 35+) carries 4-digit
class explanatory notes that ISIC's English notes do not cover when
NACE/ISIC split a class 1:N.

This module operates on the already-extracted plain text of that
structured section and emits ``{4-digit-code: notes}`` keyed by the
NIC class code. The 5-digit Indian-specific subclasses are
intentionally skipped because their titles already carry the full
descriptive content.
"""

from __future__ import annotations

import re
from typing import Dict

_EM_DASH = "\u2014"
_BLANKS = re.compile(r"\n\s*\n\s*\n+")
# A 4-digit class block: ``NNNN <title>\n<notes>...`` ending at the
# next 3, 4 or 5-digit code line, or a Division / Section header,
# or the end of the text.
_CLASS_RE = re.compile(
    r"^(\d{4})\s+(.+?)(?=\n\d{3,5}\s|\nDiv|\nSECTION|\Z)",
    re.MULTILINE | re.DOTALL,
)


def render_notes(s: str) -> str:
    """Clean whitespace and normalize em-dashes in an extracted notes
    block. Returns ``""`` if the input has no real content.
    """
    if not (s or "").strip():
        return ""
    out = s.replace(_EM_DASH, "-")
    out = _BLANKS.sub("\n\n", out)
    return out.strip()


def extract_class_notes(structured_text: str) -> Dict[str, str]:
    """Return ``{4-digit-code: notes}`` for every 4-digit class block
    in the structured-section text. The first occurrence wins (later
    occurrences in correspondence tables are ignored). Blocks where
    only the title appears (no notes) are skipped.
    """
    out: Dict[str, str] = {}
    for code, body in _CLASS_RE.findall(structured_text):
        if code in out:
            continue
        # Validate code: NIC division must be 01..99
        try:
            div = int(code[:2])
        except ValueError:
            continue
        if not (0 < div <= 99):
            continue
        # Drop the first line (title) and keep the remainder as notes
        lines = body.split("\n", 1)
        if len(lines) < 2:
            continue
        notes = render_notes(lines[1])
        if notes:
            out[code] = notes
    return out
