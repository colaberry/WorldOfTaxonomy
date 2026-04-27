"""Tests for the ANZSIC 2006 description enricher.

The ABS SDMX codelist CL_ANZSIC_2006 carries a per-code ``CONTEXT``
annotation whose body has two sections: ``Exclusions/References`` and
``Primary Activities``. The raw body is heavily tab-indented. This
parser collapses whitespace, preserves the two section headings as
bold markdown, and strips em-dashes.
"""
from textwrap import dedent

from world_of_taxonomy.ingest.anzsic2006_descriptions import render_context


_SAMPLE = dedent("""\
Exclusions/References
\t\t\t\t\t\t\t\tUnits mainly engaged in
\t\t\t\t\t\t\t\t(a) propagating plants outdoors are included in Class 0112.

\t\t\t\t\t\t\t\tPrimary Activities
\t\t\t\t\t\t\t\tBedding plant growing (under cover)
\t\t\t\t\t\t\t\tBulb propagating (under cover)
\t\t\t\t\t\t\tVine stock nursery operation (under cover)""")


def test_render_context_preserves_both_headings():
    out = render_context(_SAMPLE)
    assert "**Exclusions/References:**" in out
    assert "**Primary Activities:**" in out


def test_render_context_collapses_tab_runs():
    out = render_context(_SAMPLE)
    assert "\t" not in out
    # excessive whitespace runs eliminated
    assert "  " not in out


def test_render_context_keeps_activity_lines_as_bullets():
    out = render_context(_SAMPLE)
    assert "- Bedding plant growing (under cover)" in out
    assert "- Bulb propagating (under cover)" in out


def test_render_context_strips_em_dashes():
    body = "Exclusions/References\nItem \u2014 with em-dash"
    out = render_context(body)
    assert "\u2014" not in out


def test_render_context_handles_empty_input():
    assert render_context("") == ""
    assert render_context("   \t\t\t") == ""


def test_render_context_handles_only_primary_activities():
    body = "Primary Activities\n\t\t\tFoo\n\t\t\tBar"
    out = render_context(body)
    assert "**Primary Activities:**" in out
    assert "- Foo" in out
    assert "- Bar" in out
    assert "Exclusions" not in out
