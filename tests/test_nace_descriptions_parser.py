"""Tests for the NACE Rev 2 description enricher.

The EU Publications Office serves per-concept SKOS/XKOS RDF for every
NACE Rev 2 code at ``http://data.europa.eu/ux2/nace2/<path>``. The DB
stores codes in dotted form (``01.11``) while the RDF URI uses the
dots-stripped form (``0111``). This parser extracts the English
``xkos:coreContentNote`` and ``xkos:exclusionNote`` from each RDF
payload and combines them into a single markdown body.
"""
from textwrap import dedent

from world_of_taxonomy.ingest.nace_descriptions import (
    code_to_uri_path,
    parse_concept_rdf,
    render_description,
)


def test_code_to_uri_path_drops_dots_for_group_and_class():
    assert code_to_uri_path("01.11") == "0111"
    assert code_to_uri_path("01.1") == "011"
    assert code_to_uri_path("01") == "01"
    assert code_to_uri_path("A") == "A"


def test_parse_concept_rdf_extracts_english_notes():
    xml = dedent("""\
    <?xml version="1.0" encoding="utf-8" ?>
    <rdf:RDF
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:skos="http://www.w3.org/2004/02/skos/core#"
      xmlns:xkos="http://rdf-vocabulary.ddialliance.org/xkos#">
      <rdf:Description rdf:about="http://data.europa.eu/ux2/nace2/0111">
        <skos:prefLabel xml:lang="en">01.11 Growing of cereals</skos:prefLabel>
        <skos:prefLabel xml:lang="fr">01.11 Culture de cereales</skos:prefLabel>
        <xkos:coreContentNote xml:lang="en">This class includes growing of cereals.</xkos:coreContentNote>
        <xkos:coreContentNote xml:lang="fr">French text not chosen.</xkos:coreContentNote>
        <xkos:exclusionNote xml:lang="en">This class excludes growing of rice, see 01.12.</xkos:exclusionNote>
      </rdf:Description>
    </rdf:RDF>
    """).encode()
    out = parse_concept_rdf(xml, uri_suffix="0111")
    assert out["core_content"] == "This class includes growing of cereals."
    assert "rice" in out["exclusion"]


def test_parse_concept_rdf_returns_empty_when_no_english():
    xml = dedent("""\
    <?xml version="1.0" encoding="utf-8" ?>
    <rdf:RDF
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:xkos="http://rdf-vocabulary.ddialliance.org/xkos#">
      <rdf:Description rdf:about="http://data.europa.eu/ux2/nace2/99">
        <xkos:coreContentNote xml:lang="fr">French only.</xkos:coreContentNote>
      </rdf:Description>
    </rdf:RDF>
    """).encode()
    out = parse_concept_rdf(xml, uri_suffix="99")
    assert out == {"core_content": "", "exclusion": ""}


def test_render_description_combines_both_blocks():
    out = render_description({
        "core_content": "This class includes growing of cereals.",
        "exclusion": "This class excludes growing of rice, see 01.12.",
    })
    assert "This class includes" in out
    assert "This class excludes" in out
    assert "\n\n" in out


def test_render_description_handles_exclusion_only():
    out = render_description({
        "core_content": "",
        "exclusion": "This class excludes growing of rice.",
    })
    assert out == "This class excludes growing of rice."


def test_render_description_returns_empty_when_both_missing():
    out = render_description({"core_content": "", "exclusion": ""})
    assert out == ""


def test_render_description_strips_em_dashes():
    out = render_description({
        "core_content": "Includes \u2014 primarily cereals.",
        "exclusion": "",
    })
    assert "\u2014" not in out
    assert "-" in out


def test_render_description_collapses_bullet_characters():
    # NACE uses "•" for nested bullets. Leave them intact
    # (they are valid UTF-8 bullet glyphs, not em-dashes).
    raw = "This class includes:\n- growing of cereals such as:\n  • wheat\n  • barley"
    out = render_description({"core_content": raw, "exclusion": ""})
    assert "\u2022" in out
    assert out.startswith("This class includes:")
