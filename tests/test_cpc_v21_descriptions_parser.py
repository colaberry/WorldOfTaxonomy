"""Tests for the UN CPC v2.1 explanatory notes XLSX parser."""

from pathlib import Path

import openpyxl

from world_of_taxonomy.ingest.cpc_v21_descriptions import (
    parse_cpc_v21_exp_notes_xlsx,
)


def _build_workbook(path: Path) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CPC2.1"
    ws.append([
        "CPC Ver. 2.1 Code", "CPC Ver. 2.1 Title",
        "CPC Ver. 2.1 Explanatory Note - Inclusions",
        "CPC Ver. 2.1 Explanatory Note - Exclusions",
    ])
    # Section: no notes
    ws.append(["0", "Agriculture, forestry and fishery products", None, None])
    # Group: includes only
    ws.append([
        "011", "Cereals",
        "This group includes:\n- annual plants of the gramineous family\n- maize, wheat",
        None,
    ])
    # Subclass: both inclusions and exclusions
    ws.append([
        "01111", "Wheat, seed",
        "This subclass includes:\n- wheat species of Triticum\n- mainly aestivum and durum",
        "This subclass does not include:\n- wheat not grown specifically for seed",
    ])
    # Code with no notes: should be omitted
    ws.append(["0112", "Maize (corn)", None, None])

    # Wildcard sheet
    ws2 = wb.create_sheet("61_62")
    ws2.append(["Four-digit and five-digit codes in Divisions 61 and 62"])
    ws2.append(["Notes about the layout..."])
    ws2.append([
        "CPC Ver. 2.1 Code", "CPC Ver. 2.1 Title",
        "CPC Ver. 2.1 Explanatory Note - Inclusions",
    ])
    ws2.append([
        "***11", "Trade services, of grains and oilseeds",
        "This subclass includes:\n- trade services related to:\n- goods of group 011",
    ])
    wb.save(path)
    return path


def test_parses_inclusions_only(tmp_path: Path):
    xlsx = _build_workbook(tmp_path / "cpc.xlsx")
    result = parse_cpc_v21_exp_notes_xlsx(xlsx)
    assert "011" in result
    assert "**Includes:**" in result["011"]
    assert "annual plants of the gramineous family" in result["011"]
    assert "**Excludes:**" not in result["011"]


def test_parses_inclusions_and_exclusions(tmp_path: Path):
    xlsx = _build_workbook(tmp_path / "cpc.xlsx")
    result = parse_cpc_v21_exp_notes_xlsx(xlsx)
    desc = result["01111"]
    assert "**Includes:**" in desc
    assert "**Excludes:**" in desc
    assert desc.index("**Includes:**") < desc.index("**Excludes:**")
    assert "wheat species of Triticum" in desc
    assert "wheat not grown specifically for seed" in desc


def test_strips_verbose_leading_phrase(tmp_path: Path):
    xlsx = _build_workbook(tmp_path / "cpc.xlsx")
    result = parse_cpc_v21_exp_notes_xlsx(xlsx)
    assert "This subclass includes:" not in result["01111"]
    assert "This group includes:" not in result["011"]


def test_skips_codes_without_notes(tmp_path: Path):
    xlsx = _build_workbook(tmp_path / "cpc.xlsx")
    result = parse_cpc_v21_exp_notes_xlsx(xlsx)
    assert "0" not in result
    assert "0112" not in result


def test_expands_wildcard_codes_to_divisions_61_and_62(tmp_path: Path):
    xlsx = _build_workbook(tmp_path / "cpc.xlsx")
    result = parse_cpc_v21_exp_notes_xlsx(xlsx)
    assert "6111" in result
    assert "6211" in result
    assert "***11" not in result
    assert "trade services related to" in result["6111"]
    assert result["6111"] == result["6211"]
