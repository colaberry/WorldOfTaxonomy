"""Parser for Patent CPC Scheme XML notes-and-warnings.

The ``CPCSchemeXML202601.zip`` archive ships one XML file per
subclass (~800 files). Most ``<classification-item>`` entries are
title-only, but ~6,000 carry a ``<notes-and-warnings>`` block with
explanatory text (this-subclass-covers / does-not-cover, references
to other CPC codes, etc.). This module extracts those notes.

DB code format note: Patent CPC subgroup codes are stored with a
single space between the 4-char subclass and the rest
(``A01B 1/022``) while the XML uses no space (``A01B1/022``);
:func:`db_code_for_symbol` performs the conversion.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Dict

_EM_DASH = "\u2014"
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# Find all symbol declarations and all notes blocks separately. The
# previous regex tried to match symbol + notes in a single pattern,
# which caused catastrophic backtracking on items lacking notes.
_SYMBOL_RE = re.compile(r"<classification-symbol>([^<]+)</classification-symbol>")
_NOTES_RE = re.compile(r"<notes-and-warnings>([\s\S]*?)</notes-and-warnings>")


def db_code_for_symbol(symbol: str) -> str:
    """Convert an XML ``<classification-symbol>`` into the DB key.

    The first 4 characters identify the subclass; if anything follows
    we insert a single space between the subclass and the remainder.
    """
    s = (symbol or "").strip()
    if len(s) <= 4:
        return s
    return f"{s[:4]} {s[4:]}"


def extract_notes_text(raw: str) -> str:
    """Strip XML tags from a notes-and-warnings body and clean text."""
    if not (raw or "").strip():
        return ""
    s = _TAG_RE.sub(" ", raw)
    s = _WS_RE.sub(" ", s).strip()
    return s.replace(_EM_DASH, "-")


def _split_into_items(xml_text: str) -> list[str]:
    """Split the raw XML text on ``<classification-item`` boundaries
    into per-item chunks. Each chunk starts with ``<classification-item``
    or is the leading prologue (which we discard).
    """
    parts = xml_text.split("<classification-item")
    if len(parts) <= 1:
        return []
    # Drop the prologue and re-prepend the marker to each remaining part.
    return [f"<classification-item{p}" for p in parts[1:]]


def parse_scheme_zip(zip_path: Path) -> Dict[str, str]:
    """Return ``{db_code: notes_text}`` for every classification item
    in the CPC Scheme XML zip that carries a non-empty
    notes-and-warnings block.

    Avoids catastrophic-backtracking by splitting each XML file on
    ``<classification-item`` boundaries first and then checking each
    chunk for symbol + notes independently.
    """
    out: Dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if not name.endswith(".xml"):
                continue
            text = z.read(name).decode("utf-8", errors="replace")
            for chunk in _split_into_items(text):
                if "<notes-and-warnings>" not in chunk:
                    continue
                sym_m = _SYMBOL_RE.search(chunk)
                notes_m = _NOTES_RE.search(chunk)
                if not (sym_m and notes_m):
                    continue
                symbol = sym_m.group(1).strip()
                notes = extract_notes_text(notes_m.group(1))
                if not notes:
                    continue
                code = db_code_for_symbol(symbol)
                if code not in out:
                    out[code] = notes
    return out
