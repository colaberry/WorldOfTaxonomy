"""Tests for the Patent CPC scheme XML notes-and-warnings extractor.

The CPC Scheme XML zip ships one XML file per subclass with
``<classification-item>`` entries that may carry a
``<notes-and-warnings>`` block. The block contains one or more
``<note-paragraph>`` elements with inline ``<class-ref>`` references
that we strip to plain text. The DB stores subgroup codes with a
space after the 4-char subclass (``A01B 1/022``) while the XML uses
no space (``A01B1/022``); the parser normalizes to the DB form.
"""
from textwrap import dedent

from world_of_taxonomy.ingest.patent_cpc_scheme import (
    db_code_for_symbol,
    extract_notes_text,
)


def test_db_code_for_symbol_passes_short_codes_unchanged():
    assert db_code_for_symbol("A") == "A"
    assert db_code_for_symbol("A01") == "A01"
    assert db_code_for_symbol("A01B") == "A01B"


def test_db_code_for_symbol_inserts_space_for_groups():
    assert db_code_for_symbol("A01B1/00") == "A01B 1/00"
    assert db_code_for_symbol("A01B1/022") == "A01B 1/022"
    assert db_code_for_symbol("A61F2002/169052") == "A61F 2002/169052"


def test_extract_notes_text_strips_inline_xml():
    raw = (
        "<note type=\"note\">"
        "<note-paragraph>"
        "Auxiliary devices attached to machines, see "
        "<class-ref scheme=\"cpc\">A01B3/00</class-ref> for context."
        "</note-paragraph></note>"
    )
    out = extract_notes_text(raw)
    assert "<" not in out
    assert "Auxiliary devices" in out
    assert "A01B3/00" in out


def test_extract_notes_text_joins_multiple_paragraphs():
    raw = dedent("""\
    <note type="note">
      <note-paragraph>First paragraph here.</note-paragraph>
      <note-paragraph>Second paragraph follows.</note-paragraph>
    </note>
    """)
    out = extract_notes_text(raw)
    assert "First paragraph" in out
    assert "Second paragraph" in out


def test_extract_notes_text_handles_u_emphasis_tags():
    """Subclass notes commonly mark 'covers' / 'does not cover' with <u>."""
    raw = (
        "<note-paragraph>This subclass <u>covers</u> the topic. "
        "It <u>does not cover</u> X.</note-paragraph>"
    )
    out = extract_notes_text(raw)
    assert "covers" in out
    assert "does not cover" in out
    assert "<u>" not in out


def test_extract_notes_text_collapses_whitespace():
    raw = "<note-paragraph>A   B\n\n\n\nC</note-paragraph>"
    out = extract_notes_text(raw)
    assert "  " not in out
    assert "\n\n\n" not in out


def test_extract_notes_text_strips_em_dashes():
    raw = "<note-paragraph>Foo \u2014 bar.</note-paragraph>"
    assert "\u2014" not in extract_notes_text(raw)


def test_extract_notes_text_returns_empty_on_blank():
    assert extract_notes_text("") == ""
    assert extract_notes_text("   ") == ""
