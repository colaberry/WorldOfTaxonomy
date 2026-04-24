"""Tests for the MeSH descriptor XML parser.

NLM publishes MeSH as ``descYYYY.xml`` (also available gzipped).
Each ``<DescriptorRecord>`` carries a ``<DescriptorUI>`` (D-code),
a preferred concept with a ``<ScopeNote>`` (definition) and a
``<TermList>`` (entry terms / synonyms), plus a ``<TreeNumberList>``
pinning the descriptor to one or more places in the MeSH hierarchy.

Our DB stores descriptor codes verbatim (``D015704``). The structural
ingester persists only the name; this parser surfaces the definition,
tree numbers, and synonyms into ``classification_node.description``.
"""
from pathlib import Path

from world_of_taxonomy.ingest.mesh_descriptions import (
    parse_mesh_descriptor_xml,
)


_SAMPLE_XML = """<?xml version="1.0"?>
<DescriptorRecordSet LanguageCode="eng">
<DescriptorRecord DescriptorClass="1">
  <DescriptorUI>D000001</DescriptorUI>
  <DescriptorName><String>Calcimycin</String></DescriptorName>
  <TreeNumberList>
    <TreeNumber>D02.355.291.933.125</TreeNumber>
    <TreeNumber>D03.633.100.221.173</TreeNumber>
  </TreeNumberList>
  <ConceptList>
    <Concept PreferredConceptYN="Y">
      <ConceptUI>M0000001</ConceptUI>
      <ConceptName><String>Calcimycin</String></ConceptName>
      <ScopeNote>An ionophorous, polyether antibiotic from Streptomyces chartreusensis. It binds and transports CALCIUM across membranes.
      </ScopeNote>
      <TermList>
        <Term ConceptPreferredTermYN="Y" IsPermutedTermYN="N">
          <String>Calcimycin</String>
        </Term>
        <Term ConceptPreferredTermYN="N" IsPermutedTermYN="N">
          <String>A 23187</String>
        </Term>
        <Term ConceptPreferredTermYN="N" IsPermutedTermYN="Y">
          <String>Permuted, skip</String>
        </Term>
      </TermList>
    </Concept>
    <Concept PreferredConceptYN="N">
      <ConceptUI>M9999999</ConceptUI>
      <ConceptName><String>A-23187</String></ConceptName>
      <ScopeNote>This scope note is on a non-preferred concept and must be ignored.</ScopeNote>
      <TermList>
        <Term ConceptPreferredTermYN="Y" IsPermutedTermYN="N">
          <String>A-23187</String>
        </Term>
      </TermList>
    </Concept>
  </ConceptList>
</DescriptorRecord>
<DescriptorRecord DescriptorClass="1">
  <DescriptorUI>D000002</DescriptorUI>
  <DescriptorName><String>NoDefinition</String></DescriptorName>
  <TreeNumberList>
    <TreeNumber>A01.001</TreeNumber>
  </TreeNumberList>
  <ConceptList>
    <Concept PreferredConceptYN="Y">
      <ConceptUI>M0000002</ConceptUI>
      <ConceptName><String>NoDefinition</String></ConceptName>
      <TermList>
        <Term ConceptPreferredTermYN="Y" IsPermutedTermYN="N">
          <String>NoDefinition</String>
        </Term>
      </TermList>
    </Concept>
  </ConceptList>
</DescriptorRecord>
<DescriptorRecord DescriptorClass="1">
  <DescriptorUI>D000003</DescriptorUI>
  <DescriptorName><String>EmDash\u2014Term</String></DescriptorName>
  <ConceptList>
    <Concept PreferredConceptYN="Y">
      <ConceptUI>M0000003</ConceptUI>
      <ConceptName><String>EmDash\u2014Term</String></ConceptName>
      <ScopeNote>Contains an em\u2014dash here.</ScopeNote>
      <TermList>
        <Term ConceptPreferredTermYN="Y" IsPermutedTermYN="N">
          <String>EmDash\u2014Term</String>
        </Term>
      </TermList>
    </Concept>
  </ConceptList>
</DescriptorRecord>
</DescriptorRecordSet>
"""


def _write(path: Path, content: str = _SAMPLE_XML) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_returns_mapping_keyed_by_descriptor_ui(tmp_path: Path):
    f = _write(tmp_path / "desc.xml")
    result = parse_mesh_descriptor_xml(f)
    assert "D000001" in result
    assert "D000002" in result


def test_parse_emits_definition_from_preferred_concept(tmp_path: Path):
    f = _write(tmp_path / "desc.xml")
    desc = parse_mesh_descriptor_xml(f)["D000001"]
    assert "**Definition:**" in desc
    assert "ionophorous, polyether antibiotic" in desc
    # Non-preferred-concept scope note must not leak in
    assert "must be ignored" not in desc


def test_parse_emits_tree_numbers(tmp_path: Path):
    f = _write(tmp_path / "desc.xml")
    desc = parse_mesh_descriptor_xml(f)["D000001"]
    assert "**Tree numbers:**" in desc
    assert "D02.355.291.933.125" in desc
    assert "D03.633.100.221.173" in desc


def test_parse_emits_synonyms_skipping_preferred_and_permuted(tmp_path: Path):
    f = _write(tmp_path / "desc.xml")
    desc = parse_mesh_descriptor_xml(f)["D000001"]
    assert "**Synonyms:**" in desc
    assert "A 23187" in desc
    # The preferred term IS the name; exclude it from synonyms
    assert desc.count("Calcimycin") <= 1  # appears at most once (maybe not at all)
    # Permuted terms are noise, skip
    assert "Permuted, skip" not in desc


def test_parse_handles_records_without_scope_note(tmp_path: Path):
    """Descriptors without a ScopeNote get synonyms + tree numbers only."""
    f = _write(tmp_path / "desc.xml")
    desc = parse_mesh_descriptor_xml(f)["D000002"]
    assert "**Definition:**" not in desc
    assert "**Tree numbers:**" in desc
    assert "A01.001" in desc


def test_parse_replaces_em_dash(tmp_path: Path):
    f = _write(tmp_path / "desc.xml")
    desc = parse_mesh_descriptor_xml(f)["D000003"]
    assert "\u2014" not in desc
    assert "em-dash" in desc


def test_parse_accepts_gzipped_input(tmp_path: Path):
    """Parser should accept a .xml.gz file (NLM ships a .gz alongside the .xml)."""
    import gzip
    inner = tmp_path / "desc.xml.gz"
    with gzip.open(inner, "wt", encoding="utf-8") as gz:
        gz.write(_SAMPLE_XML)
    result = parse_mesh_descriptor_xml(inner)
    assert "D000001" in result
    assert "**Definition:**" in result["D000001"]


def test_parse_returns_empty_for_record_with_no_meaningful_fields(tmp_path: Path):
    """A descriptor with no ScopeNote, no synonyms, and no tree numbers is skipped."""
    content = """<?xml version="1.0"?>
<DescriptorRecordSet>
<DescriptorRecord>
  <DescriptorUI>D099999</DescriptorUI>
  <DescriptorName><String>Empty</String></DescriptorName>
  <ConceptList>
    <Concept PreferredConceptYN="Y">
      <ConceptUI>M0099999</ConceptUI>
      <ConceptName><String>Empty</String></ConceptName>
      <TermList>
        <Term ConceptPreferredTermYN="Y" IsPermutedTermYN="N">
          <String>Empty</String>
        </Term>
      </TermList>
    </Concept>
  </ConceptList>
</DescriptorRecord>
</DescriptorRecordSet>
"""
    f = _write(tmp_path / "desc.xml", content)
    result = parse_mesh_descriptor_xml(f)
    assert "D099999" not in result
