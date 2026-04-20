"""Tests for the CIP 2020 descriptions CSV parser.

The NCES source CSV carries definitions in the `CIPDefinition` column
alongside titles. The structural ingester ignores that column, so a
separate parser surfaces it for the description backfill.

Source format:
    CIPFamily, CIPCode, Action, TextChange, CIPTitle, CIPDefinition, ...

CIP codes appear with an Excel-escape prefix (`="01.0101"`) that must
be stripped before use.
"""

from pathlib import Path

from world_of_taxonomy.ingest.cip_2020_descriptions import (
    parse_cip_2020_descriptions_csv,
)


def _write_sample(path: Path) -> Path:
    """NCES-formatted sample CSV; returns path."""
    path.write_text(
        '"CIPFamily","CIPCode","Action","TextChange","CIPTitle","CIPDefinition"\n'
        '="01",="01","No substantive changes",yes,"Agriculture.","Agriculture programs that focus on farming."\n'
        '="01",="01.0101","No substantive changes",no,"Agribusiness.","A general program in agribusiness."\n'
        '="01",="01.0199","No substantive changes",no,"Other.",""\n'
        '="01",="01.9999","Deleted",yes,"Removed program.","Should be ignored."\n',
        encoding="utf-8",
    )
    return path


def test_parse_returns_code_to_description(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "cip.csv")
    result = parse_cip_2020_descriptions_csv(csv_path)
    assert result["01"].startswith("Agriculture programs")
    assert result["01.0101"].startswith("A general program")


def test_parse_strips_excel_escape_prefix(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "cip.csv")
    result = parse_cip_2020_descriptions_csv(csv_path)
    assert '="01"' not in result
    assert "01" in result


def test_parse_skips_empty_definitions(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "cip.csv")
    result = parse_cip_2020_descriptions_csv(csv_path)
    assert "01.0199" not in result


def test_parse_skips_deleted_rows(tmp_path: Path):
    csv_path = _write_sample(tmp_path / "cip.csv")
    result = parse_cip_2020_descriptions_csv(csv_path)
    assert "01.9999" not in result
