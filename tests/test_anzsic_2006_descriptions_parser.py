"""Tests for the ANZSIC 2006 SDMX XML descriptions parser."""

from pathlib import Path

from world_of_taxonomy.ingest.anzsic_2006_descriptions import (
    parse_anzsic_2006_descriptions,
)


_SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<message:Structure
    xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
    xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
    xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <message:Structures>
    <structure:Codelists>
      <structure:Codelist id="CL_ANZSIC_2006">
        <structure:Code id="TOT">
          <common:Name>All Industries</common:Name>
          <common:Description>Should be ignored.</common:Description>
        </structure:Code>
        <structure:Code id="A">
          <common:Name>Agriculture, Forestry and Fishing</common:Name>
          <common:Description>The Agriculture, Forestry and Fishing Division includes units mainly engaged in growing crops, raising animals, growing and harvesting timber, and harvesting fish and other animals from farms.

          A second paragraph of details.</common:Description>
        </structure:Code>
        <structure:Code id="B">
          <common:Name>Mining</common:Name>
          <common:Description></common:Description>
        </structure:Code>
        <structure:Code id="01">
          <common:Name>Agriculture</common:Name>
        </structure:Code>
      </structure:Codelist>
    </structure:Codelists>
  </message:Structures>
</message:Structure>
"""


def _write(path: Path) -> Path:
    path.write_text(_SAMPLE_XML, encoding="utf-8")
    return path


def test_extracts_description_for_division(tmp_path: Path):
    f = _write(tmp_path / "anzsic.xml")
    result = parse_anzsic_2006_descriptions(f)
    assert "A" in result
    assert "Agriculture, Forestry and Fishing Division" in result["A"]


def test_drops_total_aggregator(tmp_path: Path):
    f = _write(tmp_path / "anzsic.xml")
    result = parse_anzsic_2006_descriptions(f)
    assert "TOT" not in result


def test_skips_codes_with_empty_description(tmp_path: Path):
    f = _write(tmp_path / "anzsic.xml")
    result = parse_anzsic_2006_descriptions(f)
    assert "B" not in result


def test_skips_codes_without_description_element(tmp_path: Path):
    f = _write(tmp_path / "anzsic.xml")
    result = parse_anzsic_2006_descriptions(f)
    assert "01" not in result


def test_normalizes_whitespace_keeping_paragraph_breaks(tmp_path: Path):
    f = _write(tmp_path / "anzsic.xml")
    result = parse_anzsic_2006_descriptions(f)
    text = result["A"]
    assert "\n\n" in text
    # Inline whitespace collapsed
    assert "  " not in text
