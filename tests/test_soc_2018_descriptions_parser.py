"""Tests for the SOC 2018 descriptions parser.

BLS publishes SOC 2018 titles, but its definitions file is not publicly
downloadable without browser-level access. O*NET (a BLS/DOL co-product)
publishes `onet_occupation_data.txt` with descriptions keyed by an
O*NET-SOC code of the form `11-1011.00` (base) or `11-1011.03`
(extension). The base rows (`.00`) map 1:1 to the SOC 6-digit code.

Only base (`.00`) rows contribute descriptions so that the 6-digit SOC
code's row is not overwritten by an extension-specific description.
"""

from pathlib import Path

from world_of_taxonomy.ingest.soc_2018_descriptions import (
    parse_soc_2018_descriptions_txt,
)


def _write_sample(path: Path) -> Path:
    """O*NET occupation_data.txt sample; tab-delimited, returns path."""
    path.write_text(
        "O*NET-SOC Code\tTitle\tDescription\n"
        "11-1011.00\tChief Executives\tDetermine and formulate policies.\n"
        "11-1011.03\tChief Sustainability Officers\tExtension-only description.\n"
        "11-1021.00\tGeneral and Operations Managers\tPlan, direct, or coordinate operations.\n"
        "11-1031.00\tLegislators\t\n",  # empty description row
        encoding="utf-8",
    )
    return path


def test_parse_returns_six_digit_soc_to_description(tmp_path: Path):
    txt = _write_sample(tmp_path / "onet.txt")
    result = parse_soc_2018_descriptions_txt(txt)
    assert result["11-1011"].startswith("Determine and formulate")
    assert result["11-1021"].startswith("Plan, direct")


def test_parse_ignores_extension_rows(tmp_path: Path):
    """11-1011.03 should not overwrite 11-1011's base description."""
    txt = _write_sample(tmp_path / "onet.txt")
    result = parse_soc_2018_descriptions_txt(txt)
    assert "Extension-only" not in result["11-1011"]


def test_parse_skips_empty_descriptions(tmp_path: Path):
    txt = _write_sample(tmp_path / "onet.txt")
    result = parse_soc_2018_descriptions_txt(txt)
    assert "11-1031" not in result
