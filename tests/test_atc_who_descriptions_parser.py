"""Tests for the WHO ATC description enricher.

The CSV at data/atc_who.csv has six columns:
``atc_code, atc_name, ddd, uom, adm_r, note``. For every row where any
of DDD / unit of measure / route / note carries non-NA content, we
render a small markdown block and write it into
``classification_node.description``. Rows where everything is NA are
skipped so we do not overwrite NULL with an empty string.
"""
from pathlib import Path

from world_of_taxonomy.ingest.atc_who_descriptions import (
    parse_atc_who_descriptions,
    render_row,
    route_label,
)


def test_route_label_expands_single_letter_codes():
    assert route_label("O") == "oral"
    assert route_label("P") == "parenteral"
    assert route_label("R") == "rectal"
    assert route_label("N") == "nasal"
    assert route_label("V") == "vaginal"
    assert route_label("SL") == "sublingual"
    assert route_label("TD") == "transdermal"


def test_route_label_returns_verbose_form_unchanged():
    assert route_label("Inhal.powder") == "Inhal.powder"
    assert route_label("oral aerosol") == "oral aerosol"


def test_route_label_returns_empty_on_na():
    assert route_label("NA") == ""
    assert route_label("") == ""


def test_render_row_with_full_data():
    row = {"ddd": "1.1", "uom": "mg", "adm_r": "O", "note": "0.5 mg fluoride"}
    out = render_row(row)
    assert "**Defined daily dose:** 1.1 mg (oral)" in out
    assert "**Note:** 0.5 mg fluoride" in out


def test_render_row_ddd_only():
    row = {"ddd": "500", "uom": "mg", "adm_r": "P", "note": "NA"}
    out = render_row(row)
    assert out == "**Defined daily dose:** 500 mg (parenteral)"


def test_render_row_note_only():
    row = {"ddd": "NA", "uom": "NA", "adm_r": "NA", "note": "refer to monograph"}
    out = render_row(row)
    assert out == "**Note:** refer to monograph"


def test_render_row_skips_when_everything_is_na():
    row = {"ddd": "NA", "uom": "NA", "adm_r": "NA", "note": "NA"}
    assert render_row(row) == ""


def test_render_row_ddd_without_route_still_renders():
    row = {"ddd": "1.5", "uom": "g", "adm_r": "NA", "note": "NA"}
    out = render_row(row)
    assert out == "**Defined daily dose:** 1.5 g"


def test_render_row_replaces_em_dash():
    row = {"ddd": "NA", "uom": "NA", "adm_r": "NA", "note": "note \u2014 with dash"}
    assert "\u2014" not in render_row(row)


def _write_csv(path: Path, rows: list[dict]) -> Path:
    import csv
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["atc_code", "atc_name", "ddd", "uom", "adm_r", "note"]
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path


def test_parse_atc_who_descriptions_keys_by_code_and_skips_empty(tmp_path: Path):
    f = _write_csv(
        tmp_path / "atc.csv",
        [
            {"atc_code": "A01AA01", "atc_name": "sodium fluoride",
             "ddd": "1.1", "uom": "mg", "adm_r": "O", "note": "NA"},
            {"atc_code": "A",        "atc_name": "Alimentary tract",
             "ddd": "NA", "uom": "NA", "adm_r": "NA", "note": "NA"},
            {"atc_code": "A01AA04",  "atc_name": "stannous fluoride",
             "ddd": "NA", "uom": "NA", "adm_r": "NA", "note": "special handling"},
        ],
    )
    out = parse_atc_who_descriptions(f)
    assert "A01AA01" in out
    assert "A01AA04" in out
    assert "A" not in out
    assert "1.1 mg (oral)" in out["A01AA01"]
    assert "special handling" in out["A01AA04"]
