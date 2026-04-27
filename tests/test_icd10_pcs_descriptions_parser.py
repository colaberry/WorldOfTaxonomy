"""Tests for the ICD-10-PCS Tables XML descriptions parser.

The CMS Tables XML embeds an operation ``<definition>`` for each
3-char root operation table. The parser surfaces those definitions
keyed by the 3-char code, optionally cascading to 7-char leaves.
"""

from pathlib import Path

from world_of_taxonomy.ingest.icd10_pcs_descriptions import (
    parse_icd10pcs_tables_xml,
)


_SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<ICD10PCS.tabular>
  <version>2025</version>
  <pcsTable>
    <axis pos="1" values="1">
      <title>Section</title>
      <label code="0">Medical and Surgical</label>
    </axis>
    <axis pos="2" values="1">
      <title>Body System</title>
      <label code="0">Central Nervous System and Cranial Nerves</label>
    </axis>
    <axis pos="3" values="1">
      <title>Operation</title>
      <label code="1">Bypass</label>
      <definition>Altering the route of passage of the contents of a tubular body part</definition>
    </axis>
    <pcsRow codes="99">
      <axis pos="4" values="1"><label code="6">Cerebral Ventricle</label></axis>
      <axis pos="5" values="1"><label code="0">Open</label></axis>
      <axis pos="6" values="1"><label code="7">Autologous Tissue Substitute</label></axis>
      <axis pos="7" values="1"><label code="0">Nasopharynx</label></axis>
    </pcsRow>
  </pcsTable>
  <pcsTable>
    <axis pos="1" values="1">
      <title>Section</title>
      <label code="0">Medical and Surgical</label>
    </axis>
    <axis pos="2" values="1">
      <title>Body System</title>
      <label code="F">Hepatobiliary System and Pancreas</label>
    </axis>
    <axis pos="3" values="1">
      <title>Operation</title>
      <label code="B">Excision</label>
      <definition>Cutting out or off, without replacement, a portion of a body part</definition>
    </axis>
  </pcsTable>
  <pcsTable>
    <axis pos="1" values="1">
      <title>Section</title>
      <label code="X">New Technology</label>
    </axis>
    <axis pos="2" values="1">
      <title>Body System</title>
      <label code="W">Anatomical Regions</label>
    </axis>
    <axis pos="3" values="1">
      <title>Operation</title>
      <label code="0">Introduction</label>
      <!-- no definition: should be skipped -->
    </axis>
  </pcsTable>
</ICD10PCS.tabular>
"""


def _write_sample(path: Path) -> Path:
    path.write_text(_SAMPLE_XML, encoding="utf-8")
    return path


def test_parse_returns_three_char_prefix_keys(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "tables.xml")
    result = parse_icd10pcs_tables_xml(xml_path)
    assert "001" in result
    assert "0FB" in result
    assert "Bypass" not in result["001"]
    assert "Altering the route" in result["001"]


def test_parse_skips_table_without_definition(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "tables.xml")
    result = parse_icd10pcs_tables_xml(xml_path)
    assert "XW0" not in result


def test_parse_cascades_definition_to_leaves(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "tables.xml")
    leaves = ["0010X07", "001607J", "0FB00ZZ"]
    result = parse_icd10pcs_tables_xml(xml_path, leaf_codes=leaves)
    assert result["0010X07"] == result["001"]
    assert result["0FB00ZZ"] == result["0FB"]
    # Untouched 3-char descriptions still present
    assert "001" in result
    assert "0FB" in result


def test_parse_omits_leaves_under_unknown_prefix(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "tables.xml")
    result = parse_icd10pcs_tables_xml(xml_path, leaf_codes=["XW0XX5Z"])
    # XW0 was skipped (no definition), so XW0XX5Z must not be filled
    assert "XW0XX5Z" not in result


def test_parse_omits_non_seven_char_leaves(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "tables.xml")
    result = parse_icd10pcs_tables_xml(xml_path, leaf_codes=["0010X"])
    assert "0010X" not in result


def test_parse_accepts_zipped_input(tmp_path: Path):
    import zipfile
    xml_path = _write_sample(tmp_path / "inner.xml")
    zip_path = tmp_path / "icd10pcs_tables_2025.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(xml_path, arcname="icd10pcs_tables_2025.xml")
    result = parse_icd10pcs_tables_xml(zip_path)
    assert "001" in result
