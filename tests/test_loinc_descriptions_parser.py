"""Tests for the LOINC descriptions parser.

The structural ingester at :mod:`world_of_taxonomy.ingest.loinc` only
pulls the code + LONG_COMMON_NAME. LOINC codes are defined by their
six-axis structure (Component, Property, Time aspect, System, Scale,
Method) plus an optional DefinitionDescription prose. This parser
surfaces the axes + prose as a markdown narrative for the description
backfill.
"""

from pathlib import Path

from world_of_taxonomy.ingest.loinc_descriptions import (
    parse_loinc_descriptions_csv,
)


_HEADER = (
    '"LOINC_NUM","COMPONENT","PROPERTY","TIME_ASPCT","SYSTEM","SCALE_TYP",'
    '"METHOD_TYP","CLASS","VersionLastChanged","CHNG_TYPE",'
    '"DefinitionDescription","STATUS","CONSUMER_NAME","CLASSTYPE","FORMULA",'
    '"EXMPL_ANSWERS","SURVEY_QUEST_TEXT","SURVEY_QUEST_SRC","UNITSREQUIRED",'
    '"RELATEDNAMES2","SHORTNAME","ORDER_OBS","HL7_FIELD_SUBFIELD_ID",'
    '"EXTERNAL_COPYRIGHT_NOTICE","EXAMPLE_UNITS","LONG_COMMON_NAME",'
    '"EXAMPLE_UCUM_UNITS","STATUS_REASON","STATUS_TEXT",'
    '"CHANGE_REASON_PUBLIC","COMMON_TEST_RANK","COMMON_ORDER_RANK",'
    '"HL7_ATTACHMENT_STRUCTURE","EXTERNAL_COPYRIGHT_LINK","PanelType",'
    '"AskAtOrderEntry","AssociatedObservations","VersionFirstReleased",'
    '"ValidHL7AttachmentRequest","DisplayName"\n'
)


def _row(
    loinc: str,
    component: str = "",
    prop: str = "",
    time: str = "",
    system: str = "",
    scale: str = "",
    method: str = "",
    defn: str = "",
    status: str = "ACTIVE",
    shortname: str = "",
) -> str:
    """Compose a single CSV row in the LOINC schema (all remaining cols blank)."""
    cols = [loinc, component, prop, time, system, scale, method, "", "", ""]
    cols += [defn, status, "", "", "", "", "", "", ""]
    cols += ["", shortname, "", "", "", "", "", ""]
    cols += ["", "", "", "", "", "", "", "", "", "", "", ""]
    return ",".join(f'"{c}"' for c in cols) + "\n"


def _write_sample(path: Path) -> Path:
    body = _HEADER
    body += _row(
        "2345-7",
        component="Glucose",
        prop="MCnc",
        time="Pt",
        system="Ser/Plas",
        scale="Qn",
        method="",
        defn="Glucose measurement in serum or plasma by routine methods.",
        shortname="Gluc SerPl-mCnc",
    )
    body += _row(
        "9999-9",
        component="Sodium",
        prop="SCnc",
        time="Pt",
        system="Ser/Plas",
        scale="Qn",
        method="ISE",
        defn="",
        shortname="Na SerPl-sCnc",
    )
    body += _row(
        "1111-1",
        component="Test",
        prop="Nar",
        time="Pt",
        system="^Patient",
        scale="Nar",
        method="",
        defn="",
        status="DEPRECATED",
    )
    body += _row(
        "2222-2",
        component="",
        prop="",
        time="",
        system="",
        scale="",
        method="",
        defn="",
        status="ACTIVE",
    )
    path.write_text(body, encoding="utf-8")
    return path


def test_parse_emits_six_axis_structure(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    desc = result["2345-7"]
    assert "**Component:** Glucose" in desc
    assert "**Property:** MCnc" in desc
    assert "**Time aspect:** Pt" in desc
    assert "**System:** Ser/Plas" in desc
    assert "**Scale:** Qn" in desc


def test_parse_omits_method_when_blank(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    desc = result["2345-7"]
    assert "**Method:**" not in desc


def test_parse_includes_method_when_present(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    desc = result["9999-9"]
    assert "**Method:** ISE" in desc


def test_parse_includes_definition_prose(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    desc = result["2345-7"]
    assert "**Definition:**" in desc
    assert "serum or plasma" in desc


def test_parse_includes_shortname(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    assert "**Short name:** Gluc SerPl-mCnc" in result["2345-7"]


def test_parse_skips_deprecated_and_discouraged(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    assert "1111-1" not in result


def test_parse_skips_rows_with_no_axes_or_prose(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "loinc.csv")
    result = parse_loinc_descriptions_csv(csv_path)
    assert "2222-2" not in result


def test_parse_accepts_zipped_input(tmp_path: Path):
    """The Regenstrief release is a nested ZIP with LoincTable/Loinc.csv."""
    import zipfile

    csv_path = _write_sample(tmp_path / "inner.csv")
    zip_path = tmp_path / "Loinc_2.82.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(csv_path, arcname="Loinc_2.82/LoincTable/Loinc.csv")
    result = parse_loinc_descriptions_csv(zip_path)
    assert "2345-7" in result
