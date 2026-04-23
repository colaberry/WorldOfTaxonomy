"""Tests for the ICD-10-CM Tabular XML descriptions parser.

The CMS order file provides the code + title only; the ICD-10-CM Tabular
XML file carries the inclusion terms, excludes1/excludes2, use-additional
and code-first instructional notes that clinicians actually read. This
parser surfaces those notes for the description backfill.

Codes in the Tabular XML use the dotted form (A00.1); codes in the DB
are stored without dots (A001). The parser emits dot-free keys so the
`apply_descriptions` helper can match rows directly.

Chapters in the Tabular XML are numbered 1-22; the ingester stores them
as CH01-CH22. The parser maps those.
"""

from pathlib import Path

from world_of_taxonomy.ingest.icd10cm_descriptions import (
    parse_icd10cm_tabular_xml,
)


_SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<ICD10CM.tabular>
  <version>2025</version>
  <chapter>
    <name>1</name>
    <desc>Certain infectious and parasitic diseases (A00-B99)</desc>
    <includes>
      <note>diseases generally recognized as communicable or transmissible</note>
    </includes>
    <useAdditionalCode>
      <note>code to identify resistance to antimicrobial drugs (Z16.-)</note>
    </useAdditionalCode>
    <excludes1>
      <note>certain localized infections - see body system-related chapters</note>
    </excludes1>
    <excludes2>
      <note>carrier or suspected carrier of infectious disease (Z22.-)</note>
      <note>infectious and parasitic diseases complicating pregnancy (O98.-)</note>
    </excludes2>
    <section id="A00-A09">
      <desc>Intestinal infectious diseases (A00-A09)</desc>
      <diag>
        <name>A00</name>
        <desc>Cholera</desc>
        <diag>
          <name>A00.0</name>
          <desc>Cholera due to Vibrio cholerae 01, biovar cholerae</desc>
          <inclusionTerm>
            <note>Classical cholera</note>
          </inclusionTerm>
        </diag>
        <diag>
          <name>A00.1</name>
          <desc>Cholera due to Vibrio cholerae 01, biovar eltor</desc>
          <inclusionTerm>
            <note>Cholera eltor</note>
          </inclusionTerm>
        </diag>
        <diag>
          <name>A00.9</name>
          <desc>Cholera, unspecified</desc>
        </diag>
      </diag>
      <diag>
        <name>A01</name>
        <desc>Typhoid and paratyphoid fevers</desc>
        <diag>
          <name>A01.0</name>
          <desc>Typhoid fever</desc>
          <inclusionTerm>
            <note>Infection due to Salmonella typhi</note>
          </inclusionTerm>
          <excludes1>
            <note>typhoid carrier (Z22.0)</note>
          </excludes1>
          <diag>
            <name>A01.02</name>
            <desc>Typhoid fever with heart involvement</desc>
            <inclusionTerm>
              <note>Typhoid endocarditis</note>
              <note>Typhoid myocarditis</note>
            </inclusionTerm>
          </diag>
        </diag>
      </diag>
    </section>
  </chapter>
  <chapter>
    <name>19</name>
    <desc>Injury, poisoning and certain other consequences of external causes (S00-T88)</desc>
    <notes>
      <note>Use secondary code(s) from Chapter 20 to indicate cause of injury.</note>
    </notes>
    <section id="S00-S09">
      <desc>Injuries to the head</desc>
      <diag>
        <name>S00</name>
        <desc>Superficial injury of head</desc>
        <sevenChrDef>
          <extension char="A">initial encounter</extension>
          <extension char="D">subsequent encounter</extension>
          <extension char="S">sequela</extension>
        </sevenChrDef>
        <sevenChrNote>
          <note>The appropriate 7th character is to be added to each code from category S00</note>
        </sevenChrNote>
      </diag>
    </section>
  </chapter>
</ICD10CM.tabular>
"""


def _write_sample(path: Path) -> Path:
    path.write_text(_SAMPLE_XML, encoding="utf-8")
    return path


def test_parse_returns_dot_free_code_keys(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    assert "A001" in result
    assert "A00.1" not in result
    assert "A0102" in result


def test_parse_emits_inclusion_terms_as_markdown(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    desc = result["A001"]
    assert "**Inclusion terms:**" in desc
    assert "- Cholera eltor" in desc


def test_parse_emits_multiple_inclusion_terms(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    desc = result["A0102"]
    assert "- Typhoid endocarditis" in desc
    assert "- Typhoid myocarditis" in desc


def test_parse_emits_excludes1_and_excludes2(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    desc = result["A010"]
    assert "**Excludes1:**" in desc
    assert "- typhoid carrier (Z22.0)" in desc


def test_parse_maps_chapter_number_to_CHxx(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    assert "CH01" in result
    assert "CH19" in result
    desc = result["CH01"]
    assert "**Includes:**" in desc
    assert "**Use additional code:**" in desc
    assert "**Excludes1:**" in desc
    assert "**Excludes2:**" in desc
    assert "- carrier or suspected carrier of infectious disease (Z22.-)" in desc


def test_parse_emits_seventh_character_definitions(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    desc = result["S00"]
    assert "**7th character:**" in desc
    assert "- A: initial encounter" in desc
    assert "- S: sequela" in desc


def test_parse_skips_nodes_without_any_notes(tmp_path: Path):
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    assert "A009" not in result
    assert "A00" not in result


def test_parse_ordering_is_stable(tmp_path: Path):
    """Sections appear in a consistent order in the rendered markdown."""
    xml_path = _write_sample(tmp_path / "icd.xml")
    result = parse_icd10cm_tabular_xml(xml_path)
    desc = result["CH01"]
    # Includes before Excludes before Use-additional
    assert desc.index("**Includes:**") < desc.index("**Excludes1:**")
    assert desc.index("**Excludes1:**") < desc.index("**Excludes2:**")
    assert desc.index("**Excludes2:**") < desc.index("**Use additional code:**")


def test_parse_accepts_zipped_input(tmp_path: Path):
    """The CMS release is a ZIP; parser should accept the zip path directly."""
    import zipfile
    xml_path = _write_sample(tmp_path / "inner.xml")
    zip_path = tmp_path / "icd10cm_tabular_2025.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(xml_path, arcname="icd10cm_tabular_2025.xml")
    result = parse_icd10cm_tabular_xml(zip_path)
    assert "A001" in result
