"""Parser for FullCPCDefinitionXML202601.zip.

The Full CPC Definition zip ships 24,233 XML files
(~935 MB uncompressed) keyed by subclass. Each file contains one or
more ``<definition-item>`` blocks with structured prose:

- ``<definition-statement>`` -- "This place covers: ..." narrative.
- ``<references>`` -- limiting and application-oriented references
  to other CPC codes.
- ``<glossary-of-terms>`` -- defined terms specific to this place.

This parser extracts those sections, combines them into a single
markdown body, and emits ``{db_code: body}`` (where ``db_code``
inserts a space after the 4-char subclass to match how the DB
stores subgroup codes -- same convention as PR #73).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

def db_code_for_symbol(symbol: str) -> str:
    """Convert an XML <classification-symbol> into the DB key.

    Inlined from patent_cpc_scheme so this module ships independently.
    The first 4 characters identify the subclass; if anything follows
    we insert a single space between the subclass and the remainder
    (so ``A01B1/022`` becomes ``A01B 1/022`` to match the DB).
    """
    s = (symbol or "").strip()
    if len(s) <= 4:
        return s
    return f"{s[:4]} {s[4:]}"

_EM_DASH = "\u2014"
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_MEDIA_RE = re.compile(r"<media\b[^/>]*/>", re.IGNORECASE)
_PARA_TYPE_BODY_RE = re.compile(
    r'<paragraph-text\s+type="body"[^>]*>([\s\S]*?)</paragraph-text>',
    re.IGNORECASE,
)

_DEFINITION_ITEM_RE = re.compile(
    r"<definition-item\b[\s\S]*?</definition-item>", re.IGNORECASE
)
_SYMBOL_RE = re.compile(
    r'<classification-symbol\b[^>]*>([^<]+)</classification-symbol>'
)
_DEFINITION_BODY_RE = re.compile(
    r"<definition-statement\b[\s\S]*?<section-body>([\s\S]*?)</section-body>",
    re.IGNORECASE,
)
_LIMITING_BODY_RE = re.compile(
    r"<limiting-references\b[\s\S]*?<section-body>([\s\S]*?)</section-body>",
    re.IGNORECASE,
)
_APPLICATION_BODY_RE = re.compile(
    r"<application-oriented-references\b[\s\S]*?<section-body>([\s\S]*?)</section-body>",
    re.IGNORECASE,
)
_GLOSSARY_BODY_RE = re.compile(
    r"<glossary-of-terms\b[\s\S]*?<section-body>([\s\S]*?)</section-body>",
    re.IGNORECASE,
)


def _strip_media_image_paragraphs(s: str) -> str:
    """Drop paragraph-text type='body' blocks that contain only an
    illustrative image reference (e.g. <media .../> US200516462).
    Keep only paragraphs that have substantive text after stripping
    media tags.
    """
    def _replace(m: re.Match) -> str:
        inner = _MEDIA_RE.sub(" ", m.group(1))
        text = _TAG_RE.sub(" ", inner)
        text = _WS_RE.sub(" ", text).strip()
        if not text:
            return ""
        # If the only remaining text is a patent number / short token
        # like "US200516462", drop it as well.
        if re.fullmatch(r"[A-Z]{2,3}\d{6,12}", text):
            return ""
        return m.group(0)

    return _PARA_TYPE_BODY_RE.sub(_replace, s)


def _clean_text(raw: str) -> str:
    s = _strip_media_image_paragraphs(raw)
    s = _MEDIA_RE.sub(" ", s)
    s = _TAG_RE.sub(" ", s)
    s = s.replace(_EM_DASH, "-")
    s = _WS_RE.sub(" ", s).strip()
    return s


def _section(raw_xml: str, regex: re.Pattern, header: str) -> str:
    m = regex.search(raw_xml)
    if not m:
        return ""
    text = _clean_text(m.group(1))
    if not text:
        return ""
    return f"**{header}** {text}"


def render_item(item_xml: str) -> str:
    """Render one ``<definition-item>`` XML block into markdown.

    Returns ``""`` when the item has only a title (no definition,
    references, or glossary content).
    """
    parts: list[str] = []
    parts.append(_section(item_xml, _DEFINITION_BODY_RE, "Definition:"))
    parts.append(_section(item_xml, _LIMITING_BODY_RE, "Limiting references (this place does not cover):"))
    parts.append(_section(item_xml, _APPLICATION_BODY_RE, "Application-oriented references:"))
    parts.append(_section(item_xml, _GLOSSARY_BODY_RE, "Glossary:"))
    out = "\n\n".join(p for p in parts if p)
    return out.strip()


def parse_definition_item(item_xml: str) -> Optional[Tuple[str, str]]:
    """Return ``(symbol, body)`` for a single definition-item block,
    or ``None`` if the symbol cannot be parsed or the body is empty.
    """
    sym_m = _SYMBOL_RE.search(item_xml)
    if not sym_m:
        return None
    body = render_item(item_xml)
    if not body:
        return None
    return (sym_m.group(1).strip(), body)


def parse_definition_zip(zip_path: Path) -> Dict[str, str]:
    """Stream the FullCPCDefinitionXML zip and return
    ``{db_code: body}`` for every definition-item with non-empty
    rendered content. First occurrence per db_code wins.
    """
    out: Dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".xml")]
        for name in names:
            text = z.read(name).decode("utf-8", errors="replace")
            for item_match in _DEFINITION_ITEM_RE.finditer(text):
                parsed = parse_definition_item(item_match.group(0))
                if not parsed:
                    continue
                symbol, body = parsed
                code = db_code_for_symbol(symbol)
                if code not in out:
                    out[code] = body
    return out
