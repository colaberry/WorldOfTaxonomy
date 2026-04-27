"""Parser for OSHA SIC 1987 per-code description pages.

OSHA serves each SIC code at ``https://www.osha.gov/sic-manual/<code>``.
The page is Drupal-rendered HTML with the actual description in the
main content region, preceded by a heading of the form
``<code> <title>`` (e.g. ``0111 Wheat``). After this heading we find
a descriptive paragraph and, often, an example-activities list.

``extract_description`` pulls everything that follows the heading up
to the next major section boundary, strips HTML, decodes entities,
collapses whitespace, and normalizes em-dashes.
"""

from __future__ import annotations

import html
import re
from typing import Optional

_EM_DASH = "\u2014"
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(s: str) -> str:
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.IGNORECASE)
    s = _TAG_RE.sub(" ", s)
    s = html.unescape(s)
    return _WS_RE.sub(" ", s).strip()


def extract_description(
    page_html: str, *, code: str, title: str
) -> str:
    """Return the cleaned description body for one SIC code, or ``""``
    when the expected ``<code> <title>`` heading is not present.
    """
    if not page_html:
        return ""

    text = _strip_html(page_html)
    needle = f"{code} {title}"
    idx = text.find(needle)
    if idx < 0:
        return ""

    tail = text[idx + len(needle):].strip()
    # Cut off at known post-content markers that OSHA appends.
    for marker in (
        "Scroll to Top",
        "Home SIC Manual",
        "Contact OSHA",
        "OSHA Standards",
        "OSHA.gov",
        "U.S. Department of Labor",
        "United States Department of Labor",
    ):
        cut = tail.find(marker)
        if cut >= 0:
            tail = tail[:cut].strip()

    return tail.replace(_EM_DASH, "-").strip()
