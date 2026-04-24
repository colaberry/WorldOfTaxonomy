"""Tests for the SIC 1987 (OSHA Manual) description extractor.

OSHA serves each SIC code as a single page at
``https://www.osha.gov/sic-manual/<code>``. The page HTML carries the
description in the main content region. After the ``<code> <title>``
heading we find a descriptive paragraph followed by an optional list
of example activities. ``extract_description`` pulls the paragraph
(and optional examples) out of the raw HTML.
"""
from textwrap import dedent

from world_of_taxonomy.ingest.sic1987_descriptions import extract_description


_SAMPLE_HTML_0111 = """
<!DOCTYPE html>
<html><body>
<nav>Home / SIC Manual</nav>
<main>
<h1>Description for 0111: Wheat</h1>
<div class="content">
<p>0111 Wheat Establishments primarily engaged in the production of wheat.</p>
<p>Wheat farms</p>
</div>
</main>
</body></html>
"""

_SAMPLE_HTML_2411 = """
<html><body>
<main>
<p>2411 Logging Establishments primarily engaged in cutting timber and in producing rough, round, hewn, or riven primary forest or wood raw materials. Establishments primarily engaged in the collection of bark, sap, gum, and other forest products are classified in Forestry, Major Group 08.</p>
<p>Bolts, wood: e.g., handle, heading, shingle, stave; Burls, wood; Logs; Logging contractors; Peeler logs</p>
</main>
</body></html>
"""

_SAMPLE_HTML_MISSING = """
<html><body><main><p>Some unrelated content here.</p></main></body></html>
"""


def test_extract_description_pulls_text_after_code_title():
    out = extract_description(_SAMPLE_HTML_0111, code="0111", title="Wheat")
    assert "Establishments primarily engaged in the production of wheat" in out


def test_extract_description_handles_logging_example():
    out = extract_description(_SAMPLE_HTML_2411, code="2411", title="Logging")
    assert "cutting timber" in out
    assert "Bolts, wood" in out


def test_extract_description_returns_empty_when_code_not_on_page():
    out = extract_description(_SAMPLE_HTML_MISSING, code="0111", title="Wheat")
    assert out == ""


def test_extract_description_strips_html_tags():
    html = '<p>0111 Wheat <b>Establishments</b> primarily <em>engaged</em>.</p>'
    out = extract_description(html, code="0111", title="Wheat")
    assert "<" not in out
    assert "Establishments primarily engaged" in out


def test_extract_description_strips_em_dashes():
    html = "<p>0111 Wheat Description \u2014 with em-dash.</p>"
    out = extract_description(html, code="0111", title="Wheat")
    assert "\u2014" not in out


def test_extract_description_decodes_html_entities():
    html = "<p>0111 Wheat Some &amp; text &lt;here&gt;.</p>"
    out = extract_description(html, code="0111", title="Wheat")
    assert "&amp;" not in out
    assert "&" in out
    assert "<here>" in out


def test_extract_description_cuts_osha_footer():
    html = (
        "<p>0111 Wheat Establishments primarily engaged in wheat production."
        " Scroll to Top OSHA Standards Enforcement Topics</p>"
    )
    out = extract_description(html, code="0111", title="Wheat")
    assert "Establishments primarily engaged" in out
    assert "Scroll to Top" not in out
    assert "OSHA Standards" not in out


def test_extract_description_returns_empty_when_page_has_no_body():
    # SIC 9999 "Nonclassifiable Establishments" has no body content on
    # OSHA; the tail after the code+title is just the footer chrome.
    html = (
        "<nav>Home SIC Manual</nav>"
        "<h1>9999 Nonclassifiable Establishments</h1>"
        "<div>Scroll to Top OSHA Standards</div>"
    )
    out = extract_description(
        html, code="9999", title="Nonclassifiable Establishments",
    )
    assert out == ""
