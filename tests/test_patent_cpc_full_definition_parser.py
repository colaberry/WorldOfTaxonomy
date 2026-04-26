"""Tests for the FullCPCDefinitionXML parser.

The Full CPC Definition zip ships 24,000 XML files, each
containing per-item ``<definition-item>`` blocks. We extract the
``Definition statement`` body, the ``Limiting references`` table
and the ``Glossary of terms`` table into a single markdown body.
"""
from textwrap import dedent

from world_of_taxonomy.ingest.patent_cpc_full_definition import (
    parse_definition_item,
    render_item,
)


_SAMPLE_FULL = dedent("""\
<definition-item>
<classification-symbol scheme="cpc">A22B3/00</classification-symbol>
<definition-title>Slaughtering or stunning</definition-title>
<definition-statement>
  <section-title>Definition statement</section-title>
  <section-body>
    <paragraph-text type="preamble">This place covers:</paragraph-text>
    <paragraph-text>Slaughtering or stunning of animals.</paragraph-text>
  </section-body>
</definition-statement>
<references>
  <section-title>References</section-title>
  <limiting-references>
    <section-title>Limiting references</section-title>
    <section-body>
      <paragraph-text type="preamble">This place does not cover:</paragraph-text>
      <table>
        <table-row>
          <table-column><paragraph-text>Anaesthetising of animals</paragraph-text></table-column>
          <table-column><paragraph-text><class-ref scheme="cpc">A61D7/04</class-ref></paragraph-text></table-column>
        </table-row>
      </table>
    </section-body>
  </limiting-references>
</references>
<glossary-of-terms>
  <section-title>Glossary of terms</section-title>
  <section-body>
    <paragraph-text type="preamble">In this place, the following terms or expressions are used with the meaning indicated:</paragraph-text>
    <table>
      <table-row>
        <table-column><paragraph-text>Stunning</paragraph-text></table-column>
        <table-column><paragraph-text>Rendering animals immobile or unconscious.</paragraph-text></table-column>
      </table-row>
    </table>
  </section-body>
</glossary-of-terms>
</definition-item>
""")


def test_parse_definition_item_returns_symbol_and_blocks():
    out = parse_definition_item(_SAMPLE_FULL)
    assert out is not None
    symbol, body = out
    assert symbol == "A22B3/00"
    assert "**Definition:**" in body or "Slaughtering" in body


def test_render_item_includes_definition_statement():
    body = render_item(_SAMPLE_FULL)
    assert "Slaughtering or stunning of animals" in body


def test_render_item_includes_limiting_references():
    body = render_item(_SAMPLE_FULL)
    assert "**Limiting references" in body or "does not cover" in body
    assert "Anaesthetising" in body
    assert "A61D7/04" in body


def test_render_item_includes_glossary():
    body = render_item(_SAMPLE_FULL)
    assert "Stunning" in body
    assert "immobile or unconscious" in body


def test_render_item_strips_media_tags():
    raw = dedent("""\
    <definition-item>
    <classification-symbol scheme="cpc">A22B</classification-symbol>
    <definition-title>SLAUGHTERING</definition-title>
    <definition-statement>
      <section-body>
        <paragraph-text type="preamble">This place covers:</paragraph-text>
        <paragraph-text>Body content here.</paragraph-text>
        <paragraph-text type="body"><media id="m0" file-name="x.jpg" type="jpeg"/> US200516462</paragraph-text>
      </section-body>
    </definition-statement>
    </definition-item>
    """)
    body = render_item(raw)
    assert "Body content here." in body
    assert "<media" not in body
    assert "x.jpg" not in body


def test_render_item_strips_em_dashes_and_normalizes_whitespace():
    raw = dedent("""\
    <definition-item>
    <classification-symbol scheme="cpc">X</classification-symbol>
    <definition-title>TEST</definition-title>
    <definition-statement>
      <section-body>
        <paragraph-text>Foo \u2014 bar.</paragraph-text>
      </section-body>
    </definition-statement>
    </definition-item>
    """)
    body = render_item(raw)
    assert "\u2014" not in body
    assert "Foo - bar" in body


def test_render_item_returns_empty_on_no_content():
    raw = dedent("""\
    <definition-item>
    <classification-symbol scheme="cpc">X</classification-symbol>
    <definition-title>TEST</definition-title>
    </definition-item>
    """)
    body = render_item(raw)
    assert body == ""


def test_render_item_preserves_paragraph_breaks_in_definition():
    """Multiple <paragraph-text> blocks within a section must remain
    on separate lines so the rendered text is readable."""
    raw = dedent("""\
    <definition-item>
    <classification-symbol scheme="cpc">X</classification-symbol>
    <definition-title>TEST</definition-title>
    <definition-statement>
      <section-body>
        <paragraph-text type="preamble">This place covers:</paragraph-text>
        <paragraph-text>First paragraph.</paragraph-text>
        <paragraph-text>Second paragraph.</paragraph-text>
      </section-body>
    </definition-statement>
    </definition-item>
    """)
    body = render_item(raw)
    # Both paragraphs present and separated by a newline.
    assert "First paragraph." in body
    assert "Second paragraph." in body
    # Should NOT be a single run-on sentence.
    assert "First paragraph. Second paragraph." not in body


def test_render_item_decodes_html_entities():
    """The source XML contains &quot;, &amp;, &lt; as HTML entities;
    they must be decoded so the rendered description reads cleanly."""
    raw = dedent("""\
    <definition-item>
    <classification-symbol scheme="cpc">X</classification-symbol>
    <definition-title>TEST</definition-title>
    <definition-statement>
      <section-body>
        <paragraph-text>The term &quot;diesel&quot; refers to fuel &amp; oil.</paragraph-text>
      </section-body>
    </definition-statement>
    </definition-item>
    """)
    body = render_item(raw)
    assert '"diesel"' in body
    assert "&quot;" not in body
    assert "fuel & oil" in body
    assert "&amp;" not in body


def test_render_item_separates_sections_with_blank_line():
    """Definition + Limiting References + Glossary should each be on
    their own block, separated by a blank line for legibility."""
    raw = dedent("""\
    <definition-item>
    <classification-symbol scheme="cpc">X</classification-symbol>
    <definition-title>TEST</definition-title>
    <definition-statement>
      <section-body>
        <paragraph-text>Definition body.</paragraph-text>
      </section-body>
    </definition-statement>
    <glossary-of-terms>
      <section-body>
        <paragraph-text>Glossary body.</paragraph-text>
      </section-body>
    </glossary-of-terms>
    </definition-item>
    """)
    body = render_item(raw)
    assert "**Definition:**" in body
    assert "**Glossary:**" in body
    # The two section headers must be separated by a blank line.
    assert "**Definition:**\nDefinition body." in body
    assert "**Glossary:**\nGlossary body." in body
