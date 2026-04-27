"""Tests for the ANZSCO 2022 description enricher.

The SDMX XML at data/anzsco_2022.xml carries per-code annotations that
the structural ingester throws away. For every ``structure:Code`` we
surface the short ``common:Description`` plus the ``INDICATIVE_SKILL_LEVEL``
and ``TASKS_INCLUDE`` annotation blocks into a single markdown body and
write it into ``classification_node.description``. Codes where none of
these fields carry content are skipped so we do not overwrite NULL with
an empty string.
"""
from pathlib import Path
from textwrap import dedent

from world_of_taxonomy.ingest.anzsco_descriptions import (
    parse_anzsco_descriptions,
    render_code_xml,
)


_MINIMAL_XML = dedent("""\
<?xml version="1.0" encoding="utf-8"?>
<message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure" xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <message:Structures>
    <structure:Codelists>
      <structure:Codelist id="CL_ANZSCO_2022">
        <structure:Code id="TOT">
          <common:Name xml:lang="en">All occupations</common:Name>
        </structure:Code>
        <structure:Code id="1">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>INDICATIVE_SKILL_LEVEL</common:AnnotationType>
              <common:AnnotationText xml:lang="en">Bachelor degree or higher.</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>TASKS_INCLUDE</common:AnnotationType>
              <common:AnnotationText xml:lang="en">-   setting direction
-   formulating policy</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">10</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Managers</common:Name>
          <common:Description xml:lang="en">Managers plan, organise, direct, control and coordinate operations.</common:Description>
        </structure:Code>
        <structure:Code id="11">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">15</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Chief Executives</common:Name>
        </structure:Code>
      </structure:Codelist>
    </structure:Codelists>
  </message:Structures>
</message:Structure>
""")


def test_render_code_xml_combines_description_skill_level_and_tasks():
    import xml.etree.ElementTree as ET
    ns = {
        "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
        "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
    }
    root = ET.fromstring(_MINIMAL_XML)
    code_el = root.find(".//structure:Code[@id='1']", ns)
    out = render_code_xml(code_el, ns)
    assert "Managers plan, organise, direct" in out
    assert "**Indicative skill level:**" in out
    assert "Bachelor degree or higher." in out
    assert "**Tasks include:**" in out
    assert "- setting direction" in out
    assert "- formulating policy" in out


def test_render_code_xml_returns_empty_when_no_content():
    import xml.etree.ElementTree as ET
    ns = {
        "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
        "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
    }
    root = ET.fromstring(_MINIMAL_XML)
    code_el = root.find(".//structure:Code[@id='11']", ns)
    out = render_code_xml(code_el, ns)
    assert out == ""


def test_render_code_xml_omits_missing_sections():
    import xml.etree.ElementTree as ET
    ns = {
        "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
        "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
    }
    xml = dedent("""\
    <?xml version="1.0"?>
    <structure:Code xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure" xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common" id="2">
      <common:Name xml:lang="en">Professionals</common:Name>
      <common:Description xml:lang="en">Professionals perform specialised tasks.</common:Description>
    </structure:Code>
    """)
    code_el = ET.fromstring(xml)
    out = render_code_xml(code_el, ns)
    assert out == "Professionals perform specialised tasks."
    assert "Indicative skill level" not in out
    assert "Tasks include" not in out


def test_render_code_xml_replaces_em_dash():
    import xml.etree.ElementTree as ET
    ns = {
        "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
        "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
    }
    xml = (
        '<?xml version="1.0"?>'
        '<structure:Code xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure" '
        'xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common" id="9">'
        '<common:Name xml:lang="en">X</common:Name>'
        '<common:Description xml:lang="en">plain \u2014 dash</common:Description>'
        '</structure:Code>'
    )
    code_el = ET.fromstring(xml)
    out = render_code_xml(code_el, ns)
    assert "\u2014" not in out
    assert "-" in out


def test_parse_anzsco_descriptions_keys_by_code_skips_tot_and_empty(tmp_path: Path):
    f = tmp_path / "anzsco.xml"
    f.write_text(_MINIMAL_XML)
    out = parse_anzsco_descriptions(f)
    assert "1" in out
    assert "TOT" not in out
    assert "11" not in out
    assert "Managers plan, organise" in out["1"]
    assert "Bachelor degree" in out["1"]


def test_tasks_bullets_normalize_hyphen_spacing():
    # SDMX source uses "-   setting direction" (hyphen, 3 spaces);
    # rendered output should collapse to "- setting direction".
    import xml.etree.ElementTree as ET
    ns = {
        "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
        "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
    }
    root = ET.fromstring(_MINIMAL_XML)
    code_el = root.find(".//structure:Code[@id='1']", ns)
    out = render_code_xml(code_el, ns)
    assert "-   setting" not in out
    assert "- setting" in out
