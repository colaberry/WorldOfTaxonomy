"""Tests for the O*NET-SOC description enricher.

``data/onet_occupation_data.txt`` is the O*NET Occupation Data file
published by the U.S. Department of Labor. It is a tab-separated file
with three columns: ``O*NET-SOC Code``, ``Title``, ``Description``.
The DB stores the same dotted code (e.g. ``11-1011.00``) as title, so
this parser just surfaces the Description column verbatim.
"""
from pathlib import Path
from textwrap import dedent

from world_of_taxonomy.ingest.onet_descriptions import (
    parse_onet_descriptions,
)


def _write_tsv(path: Path, rows: list[tuple[str, str, str]]) -> Path:
    lines = ["O*NET-SOC Code\tTitle\tDescription"]
    for code, title, desc in rows:
        lines.append(f"{code}\t{title}\t{desc}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_parse_onet_descriptions_reads_tsv_by_code(tmp_path: Path):
    f = _write_tsv(
        tmp_path / "onet.txt",
        [
            ("11-1011.00", "Chief Executives",
             "Determine and formulate policies."),
            ("11-1021.00", "General Managers",
             "Plan, direct, or coordinate operations."),
        ],
    )
    out = parse_onet_descriptions(f)
    assert out["11-1011.00"].startswith("Determine and formulate")
    assert "Plan, direct" in out["11-1021.00"]


def test_parse_onet_descriptions_skips_empty_description(tmp_path: Path):
    f = _write_tsv(
        tmp_path / "onet.txt",
        [("11-9999.00", "Something", "")],
    )
    out = parse_onet_descriptions(f)
    assert "11-9999.00" not in out


def test_parse_onet_descriptions_strips_em_dashes(tmp_path: Path):
    f = _write_tsv(
        tmp_path / "onet.txt",
        [("11-1011.00", "CEO", "Does X \u2014 and Y.")],
    )
    out = parse_onet_descriptions(f)
    assert "\u2014" not in out["11-1011.00"]
    assert "-" in out["11-1011.00"]


def test_parse_onet_descriptions_handles_tabs_in_description(tmp_path: Path):
    """A description field must not itself contain tabs. If it does,
    csv.DictReader with tab delimiter still splits correctly when the
    field is the last column. Ensure we read the whole remainder.
    """
    # Simulate a line with trailing tab-separated fields; csv should
    # treat them as extra columns and we only take the third.
    f = tmp_path / "onet.txt"
    f.write_text(
        "O*NET-SOC Code\tTitle\tDescription\n"
        "11-1011.00\tCEO\tDetermines policy.\n",
        encoding="utf-8",
    )
    out = parse_onet_descriptions(f)
    assert out["11-1011.00"] == "Determines policy."


def test_parse_onet_descriptions_keys_by_exact_code(tmp_path: Path):
    f = _write_tsv(
        tmp_path / "onet.txt",
        [
            ("11-1011.00", "CEO", "Alpha"),
            ("11-1011.03", "CSO", "Beta"),
        ],
    )
    out = parse_onet_descriptions(f)
    assert out["11-1011.00"] == "Alpha"
    assert out["11-1011.03"] == "Beta"
