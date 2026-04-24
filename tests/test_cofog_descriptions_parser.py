"""Tests for the COFOG description enricher.

``data/cofog.csv`` is the UN Classification of the Functions of
Government file. Every row has ``Code``, ``Description_EN``, optional
``Description_FR`` / ``Description_ES`` and ``ExplanatoryNote``. The
ExplanatoryNote column carries bulleted content that we surface into
``classification_node.description``. 131 of 188 rows have a non-empty
note; rows without a note are skipped.
"""
from pathlib import Path
from textwrap import dedent

from world_of_taxonomy.ingest.cofog_descriptions import (
    parse_cofog_descriptions,
    render_note,
)


_HEADER = "Code,Description_EN,Description_FR,Description_ES,ExplanatoryNote\n"


def test_render_note_strips_em_dashes():
    out = render_note("Item \u2014 second part.", title="T")
    assert "\u2014" not in out


def test_render_note_converts_u2212_minus_to_hyphen():
    out = render_note("Economic aid \u2212 foo \u2212 bar", title="T")
    assert "\u2212" not in out
    # two hyphens for the two minus signs
    assert out.count("-") >= 2


def test_render_note_strips_leading_title_prefix():
    title = "Economic aid routed through international organizations  (CS)"
    note = title + " \u2212 Administration of economic aid routed through..."
    out = render_note(note, title=title)
    assert not out.startswith(title)
    assert "Administration" in out


def test_render_note_keeps_note_when_title_not_prefix():
    out = render_note("Some standalone explanation", title="Completely Different Title")
    assert out.startswith("Some")


def test_render_note_collapses_whitespace():
    out = render_note("A  B\t\tC\n\n\nD", title="T")
    assert "  " not in out
    assert "\n\n\n" not in out


def test_render_note_returns_empty_on_blank():
    assert render_note("", title="T") == ""
    assert render_note("   ", title="T") == ""


def test_parse_cofog_descriptions_keys_by_code_and_skips_empty(tmp_path: Path):
    f = tmp_path / "cofog.csv"
    f.write_text(_HEADER +
        '01,General,General_FR,General_ES,\n'
        '01.1,Executive,FR,ES,Executive Administration of foo\n'
        '01.2,Economic,FR,ES,\n'
    )
    out = parse_cofog_descriptions(f)
    assert "01" not in out
    assert "01.2" not in out
    assert "01.1" in out
    assert "Administration" in out["01.1"]
