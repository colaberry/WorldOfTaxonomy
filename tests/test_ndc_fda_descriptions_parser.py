"""Tests for the NDC (FDA) descriptions parser.

The FDA's National Drug Code Directory publishes a tab-delimited
product file (``product.txt``) alongside a package file. The structural
ingester at :mod:`world_of_taxonomy.ingest.ndc_fda` already consumes
this file for hierarchy and titles. This module surfaces the rich
drug metadata (active ingredient, strength, route, labeler,
pharmacologic class, DEA schedule) into ``classification_node.description``.

Codes in the product file use the labeler-product form (e.g. ``0002-0152``)
matching the ``PRODUCTNDC`` column and the DB layout.
"""
from pathlib import Path

from world_of_taxonomy.ingest.ndc_fda_descriptions import (
    parse_ndc_product_descriptions,
)


_HEADER = (
    "PRODUCTID\tPRODUCTNDC\tPRODUCTTYPENAME\tPROPRIETARYNAME\t"
    "PROPRIETARYNAMESUFFIX\tNONPROPRIETARYNAME\tDOSAGEFORMNAME\tROUTENAME\t"
    "STARTMARKETINGDATE\tENDMARKETINGDATE\tMARKETINGCATEGORYNAME\t"
    "APPLICATIONNUMBER\tLABELERNAME\tSUBSTANCENAME\tACTIVE_NUMERATOR_STRENGTH\t"
    "ACTIVE_INGRED_UNIT\tPHARM_CLASSES\tDEASCHEDULE\tNDC_EXCLUDE_FLAG\t"
    "LISTING_RECORD_CERTIFIED_THROUGH"
)

_ROW_ZEPBOUND = (
    "0002-0152_f4a0acea-cd2f-4e90-b495-bb07116e0509\t0002-0152\t"
    "HUMAN PRESCRIPTION DRUG\tZepbound\t\ttirzepatide\t"
    "INJECTION, SOLUTION\tSUBCUTANEOUS\t20240328\t\tNDA\tNDA217806\t"
    "Eli Lilly and Company\tTIRZEPATIDE\t2.5\tmg/.5mL\t"
    "G-Protein-linked Receptor Interactions [MoA], GLP-1 Receptor Agonist [EPC]\t"
    "\tN\t20271231"
)

_ROW_HUMULIN = (
    "0002-0213_42527ae4-c593-4e13-8b77-c0511198c708\t0002-0213\t"
    "HUMAN OTC DRUG\tHumulin\tR\tInsulin human\tINJECTION, SOLUTION\t"
    "PARENTERAL\t19830627\t20261215\tBLA\tBLA018780\t"
    "Eli Lilly and Company\tINSULIN HUMAN\t100\t[iU]/mL\t"
    "Insulin [CS], Insulin [EPC]\t\tN\t"
)

# An example with DEA schedule + minimal fields
_ROW_SCHEDULED = (
    "0409-1234_abc\t0409-1234\tHUMAN PRESCRIPTION DRUG\tOxyGeneric\t\t"
    "oxycodone\tTABLET\tORAL\t20100101\t\tANDA\tANDA090000\tHospira\t"
    "OXYCODONE HYDROCHLORIDE\t10\tmg/1\tOpioid Agonist [EPC]\tCII\tN\t"
)

# Excluded row - should be skipped entirely
_ROW_EXCLUDED = (
    "0000-0001_x\t0000-0001\tHUMAN PRESCRIPTION DRUG\tGhost\t\tghost\t"
    "TABLET\tORAL\t\t\tNDA\tNDA000001\tNobody\tGHOST\t1\tmg\t"
    "\t\tY\t"
)

# An em-dash inside a field -- must be stripped/replaced
_ROW_EMDASH = (
    "1234-5678_y\t1234-5678\tHUMAN PRESCRIPTION DRUG\tBrand\u2014X\t\t"
    "generic\u2014y\tCAPSULE\tORAL\t20200101\t\tNDA\tNDA999999\tMaker\u2014Co\t"
    "GENERIC\t20\tmg\tClass [EPC]\t\tN\t"
)

_SAMPLE = "\n".join([
    _HEADER, _ROW_ZEPBOUND, _ROW_HUMULIN, _ROW_SCHEDULED,
    _ROW_EXCLUDED, _ROW_EMDASH,
])


def _write(path: Path, content: str = _SAMPLE) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_returns_mapping_keyed_by_ndc(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    result = parse_ndc_product_descriptions(f)
    assert "0002-0152" in result
    assert "0002-0213" in result
    assert "0409-1234" in result


def test_parse_skips_excluded_products(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    result = parse_ndc_product_descriptions(f)
    assert "0000-0001" not in result


def test_parse_emits_active_ingredient_and_strength(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0002-0152"]
    assert "**Active ingredient:**" in desc
    assert "TIRZEPATIDE" in desc
    assert "**Strength:**" in desc
    assert "2.5" in desc
    assert "mg/.5mL" in desc


def test_parse_emits_dosage_form_and_route(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0002-0152"]
    assert "**Dosage form:**" in desc
    assert "Injection, Solution" in desc or "INJECTION, SOLUTION" in desc
    assert "**Route:**" in desc
    assert "Subcutaneous" in desc or "SUBCUTANEOUS" in desc


def test_parse_emits_labeler_and_marketing_category(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0002-0152"]
    assert "**Labeler:**" in desc
    assert "Eli Lilly and Company" in desc
    assert "**Marketing category:**" in desc
    assert "NDA" in desc
    assert "NDA217806" in desc


def test_parse_emits_pharm_classes_when_present(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0002-0152"]
    assert "**Pharmacologic class:**" in desc
    assert "GLP-1 Receptor Agonist" in desc


def test_parse_emits_dea_schedule_when_present(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0409-1234"]
    assert "**DEA schedule:**" in desc
    assert "CII" in desc


def test_parse_omits_dea_schedule_when_absent(tmp_path: Path):
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0002-0152"]
    assert "**DEA schedule:**" not in desc


def test_parse_omits_pharm_classes_when_absent(tmp_path: Path):
    row = (
        "9999-0001_z\t9999-0001\tHUMAN OTC DRUG\tSimple\t\tsimple\t"
        "TABLET\tORAL\t\t\tOTC monograph final\tpart341\tACME\t"
        "SIMPLE\t1\tmg\t\t\tN\t"
    )
    f = _write(tmp_path / "product.txt", "\n".join([_HEADER, row]))
    desc = parse_ndc_product_descriptions(f)["9999-0001"]
    assert "**Pharmacologic class:**" not in desc


def test_parse_replaces_em_dash(tmp_path: Path):
    """Em-dashes in any rendered field must be normalized to hyphen.

    Brand/generic names live in the node title (not in description), so
    we only assert on fields that the description actually surfaces --
    here, LABELERNAME.
    """
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["1234-5678"]
    assert "\u2014" not in desc
    assert "Maker-Co" in desc


def test_parse_accepts_zipped_archive(tmp_path: Path):
    """Parser should accept the CMS-style ZIP containing product.txt."""
    import zipfile
    inner = _write(tmp_path / "product.txt")
    zip_path = tmp_path / "ndc_product.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(inner, arcname="product.txt")
    result = parse_ndc_product_descriptions(zip_path)
    assert "0002-0152" in result
    assert "**Active ingredient:**" in result["0002-0152"]


def test_parse_titlecases_dosage_form_and_route(tmp_path: Path):
    """Upper-case source values should be Title Cased in the rendered prose."""
    f = _write(tmp_path / "product.txt")
    desc = parse_ndc_product_descriptions(f)["0002-0152"]
    # Not asserting exact casing strategy beyond 'not shouting in caps'
    assert "INJECTION, SOLUTION" not in desc or "Injection, Solution" in desc
