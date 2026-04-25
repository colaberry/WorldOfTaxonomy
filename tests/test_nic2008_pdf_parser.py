"""Tests for the MOSPI NIC 2008 PDF description extractor.

The MOSPI NIC 2008 publication (193 pages) carries 4-digit class
explanatory notes in a "Detailed Structure" section starting around
page 35. This parser extracts ``{4-digit-code: notes}`` from the
already-extracted plain text of that section.
"""
from textwrap import dedent

from world_of_taxonomy.ingest.nic2008_pdf import (
    extract_class_notes,
    render_notes,
)


_SAMPLE = dedent("""\
DiviSion 01 : Crop anD animal proDuCtion
011 Growing of non-perennial crops
0111 Growing of cereals (except rice), leguminous crops and oil seeds
This class includes all forms of growing of cereals, leguminous crops
and oil seeds in open fields.
This class excludes:
- growing of maize for fodder, see 0119
01111 Growing of wheat
01112 Growing of jowar
0112 Growing of rice
This class includes the growing of rice, including organic farming.
01121 Organic farming of basmati rice
0113 Growing of vegetables and melons, roots and tubers
This class excludes:
- growing of mushroom spawn, see 0130
01131 Growing of asparagus
""")


def test_extract_class_notes_picks_4_digit_codes():
    out = extract_class_notes(_SAMPLE)
    assert "0111" in out
    assert "0112" in out
    assert "0113" in out


def test_extract_class_notes_skips_5_digit_subclasses():
    out = extract_class_notes(_SAMPLE)
    assert "01111" not in out
    assert "01121" not in out


def test_extract_class_notes_skips_3_digit_groups():
    out = extract_class_notes(_SAMPLE)
    assert "011" not in out


def test_extract_class_notes_drops_title_keeps_notes():
    out = extract_class_notes(_SAMPLE)
    body = out["0111"]
    # Title text "Growing of cereals" should NOT appear at the start
    assert not body.startswith("Growing of cereals")
    assert body.startswith("This class includes")


def test_extract_class_notes_handles_excludes_only():
    out = extract_class_notes(_SAMPLE)
    body = out["0113"]
    assert body.startswith("This class excludes")


def test_render_notes_strips_em_dashes():
    raw = "This class includes \u2014 some content."
    assert "\u2014" not in render_notes(raw)


def test_render_notes_collapses_excessive_whitespace():
    raw = "Line 1.\n\n\n\nLine 2."
    out = render_notes(raw)
    assert "\n\n\n" not in out
