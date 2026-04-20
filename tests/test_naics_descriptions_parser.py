"""Tests for the NAICS 2022 descriptions XLSX parser.

The Census Bureau publishes a separate descriptions file alongside the
structure file. Source URL:
https://www.census.gov/naics/2022NAICS/2022_NAICS_Descriptions.xlsx

Columns: Code | Title | Description (long prose, occasionally with
cross-reference notes at the end).
"""

from pathlib import Path

import openpyxl
import pytest

from world_of_taxonomy.ingest.naics_descriptions import (
    parse_naics_descriptions_xlsx,
)


@pytest.fixture
def sample_xlsx(tmp_path: Path) -> Path:
    """A tiny NAICS descriptions file mirroring the Census format."""
    path = tmp_path / "naics_desc.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Code", "Title", "Description"])
    ws.append([
        "11",
        "Agriculture, Forestry, Fishing and Hunting",
        "The Agriculture sector comprises establishments primarily engaged in growing crops, raising animals, and harvesting fish and other animals.",
    ])
    ws.append([
        "6211",
        "Offices of Physicians",
        "This industry comprises establishments of health practitioners having the degree of M.D. or D.O. primarily engaged in the independent practice of general or specialized medicine.",
    ])
    # A row whose description is blank should still be tolerated.
    ws.append(["9999", "Placeholder", None])
    # Census source uses the literal string "NULL" for codes that inherit
    # description from their parent - these must be treated as missing.
    ws.append(["1112", "Vegetable and Melon Farming", "NULL"])
    ws.append(["1113", "Fruit and Tree Nut Farming", "null"])
    # A row whose code is a float (Excel quirk) should be stringified.
    ws.append([111110.0, "Soybean Farming", "Soybean farming description."])
    wb.save(path)
    wb.close()
    return path


def test_parse_returns_code_to_description_map(sample_xlsx: Path):
    result = parse_naics_descriptions_xlsx(sample_xlsx)
    assert isinstance(result, dict)
    assert result["11"].startswith("The Agriculture sector")
    assert result["6211"].startswith("This industry comprises")


def test_parse_skips_blank_descriptions(sample_xlsx: Path):
    result = parse_naics_descriptions_xlsx(sample_xlsx)
    assert "9999" not in result


def test_parse_skips_literal_null_sentinel(sample_xlsx: Path):
    """Census source uses 'NULL' as a sentinel; must not be persisted."""
    result = parse_naics_descriptions_xlsx(sample_xlsx)
    assert "1112" not in result
    assert "1113" not in result


def test_parse_coerces_numeric_codes_to_strings(sample_xlsx: Path):
    result = parse_naics_descriptions_xlsx(sample_xlsx)
    assert "111110" in result
    assert result["111110"] == "Soybean farming description."


def test_parse_skips_header_row(sample_xlsx: Path):
    result = parse_naics_descriptions_xlsx(sample_xlsx)
    assert "Code" not in result
