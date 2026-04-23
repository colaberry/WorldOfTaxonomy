"""Tests for the CPC Patent descriptions parser.

The EPO/USPTO publishes the Cooperative Patent Classification (CPC) as
two companion archives:

* ``CPCSchemeXML<version>.zip``        -- one XML file per subclass
  with the code hierarchy and titles. Consumed by the structural
  ingester.
* ``FullCPCDefinitionXML<version>.zip`` -- one XML file per subclass
  with the definition statements, limiting references, and glossary
  of terms that clinicians (examiners) actually read. Consumed here.

Codes in the definition XML appear as ``A22B3/00`` (no space). Our DB
stores them as ``A22B 3/00`` (space between the 4-character subclass
and the main group). The parser normalizes keys to the DB format.
"""

from pathlib import Path

from world_of_taxonomy.ingest.cpc_patent_descriptions import (
    parse_cpc_definition_xml,
)


_SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<definitions publication-date="2016-11-01" publication-type="official">
<definition-item>
  <classification-symbol scheme="cpc">A22B</classification-symbol>
  <definition-title>SLAUGHTERING</definition-title>
</definition-item>
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
          <table-row>
            <table-column><paragraph-text>Cutting in general</paragraph-text></table-column>
            <table-column><paragraph-text><class-ref scheme="cpc">B26</class-ref>, <class-ref scheme="cpc">B26B</class-ref></paragraph-text></table-column>
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
          <table-column><paragraph-text>Rendering animals immobile or unconscious, without killing the animal.</paragraph-text></table-column>
        </table-row>
      </table>
    </section-body>
  </glossary-of-terms>
</definition-item>
<definition-item>
  <classification-symbol scheme="cpc">A22B3/04</classification-symbol>
  <definition-title>Masks</definition-title>
  <definition-statement>
    <section-title>Definition statement</section-title>
    <section-body>
      <paragraph-text type="preamble">This place covers:</paragraph-text>
      <paragraph-text>Masks, combined or not with stunning arrangements.</paragraph-text>
      <paragraph-text type="body"><media id="media1.jpg" file-name="cpc-def-A22B-0001.jpg" type="jpeg"/> US1234567</paragraph-text>
    </section-body>
  </definition-statement>
</definition-item>
<definition-item>
  <classification-symbol scheme="cpc">A22B5/0005</classification-symbol>
  <definition-title>Very deep subgroup</definition-title>
</definition-item>
</definitions>
"""


def _write_sample(path: Path) -> Path:
    path.write_text(_SAMPLE_XML, encoding="utf-8")
    return path


def test_parse_normalizes_code_to_db_format(tmp_path: Path):
    """A22B3/00 in the XML -> A22B 3/00 in the DB."""
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    assert "A22B 3/00" in result
    assert "A22B3/00" not in result


def test_parse_normalizes_subclass_code(tmp_path: Path):
    """The 4-character subclass A22B has no group, stays as-is."""
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    # Subclass has only title, no definition-statement -> skipped
    assert "A22B" not in result


def test_parse_emits_definition_statement(tmp_path: Path):
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    desc = result["A22B 3/00"]
    assert "**Definition:**" in desc
    assert "Slaughtering or stunning of animals." in desc


def test_parse_emits_limiting_references(tmp_path: Path):
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    desc = result["A22B 3/00"]
    assert "**Limiting references" in desc
    assert "Anaesthetising of animals" in desc
    assert "A61D7/04" in desc or "A61D 7/04" in desc


def test_parse_emits_glossary(tmp_path: Path):
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    desc = result["A22B 3/00"]
    assert "**Glossary:**" in desc
    assert "Stunning" in desc
    assert "Rendering animals immobile" in desc


def test_parse_strips_media_noise(tmp_path: Path):
    """Illustrative example lines that embed <media> filenames should not leak."""
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    desc = result["A22B 3/04"]
    assert "cpc-def-A22B-0001.jpg" not in desc
    assert "media" not in desc.lower()


def test_parse_skips_definition_items_with_no_content(tmp_path: Path):
    f = _write_sample(tmp_path / "cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(f)
    assert "A22B 5/0005" not in result
    assert "A22B" not in result


def test_parse_accepts_zipped_archive(tmp_path: Path):
    """Parser should accept the CMS-style ZIP containing one XML per subclass."""
    import zipfile
    inner = _write_sample(tmp_path / "inner.xml")
    zip_path = tmp_path / "FullCPCDefinitionXML.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(inner, arcname="cpc-definition-A22B.xml")
    result = parse_cpc_definition_xml(zip_path)
    assert "A22B 3/00" in result
