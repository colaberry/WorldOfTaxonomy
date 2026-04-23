"""Tests for the NCI Thesaurus descriptions parser.

The structural ingester at :mod:`world_of_taxonomy.ingest.nci_thesaurus`
only pulls the code + first synonym (display name) and the parent code.
Columns 3, 4, and 7 of the flat file carry the rest of the synonyms,
the free-text definition, and the semantic type -- all omitted today.

This parser composes a markdown narrative with those three pieces so
the description backfill can surface them into
``classification_node.description``.
"""

from pathlib import Path

from world_of_taxonomy.ingest.nci_thesaurus_descriptions import (
    parse_nci_thesaurus_descriptions,
)


def _line(
    code: str,
    synonyms: str = "",
    definition: str = "",
    semantic_type: str = "",
) -> str:
    """Compose a tab-delimited NCI flat-file row with the relevant columns."""
    url = f"<http://example/{code}>"
    return "\t".join([code, url, "", synonyms, definition, "", "", semantic_type, ""]) + "\n"


def _write_sample(path: Path) -> Path:
    body = ""
    body += _line(
        "C100000",
        synonyms="Percutaneous Coronary Intervention for STEMI|PCI STEMI",
        definition="A percutaneous coronary intervention for ST elevation MI. (ACC)",
        semantic_type="Therapeutic or Preventive Procedure",
    )
    body += _line(
        "C200001",
        synonyms="Sodium",
        definition="",
        semantic_type="Chemical",
    )
    body += _line(
        "C300002",
        synonyms="Solo",
        definition="Single synonym test.",
        semantic_type="Test",
    )
    body += _line(
        "C400003",
        synonyms="Has em\u2014dash",
        definition="Definition with em\u2014dash character.",
        semantic_type="Test",
    )
    body += _line(
        "C500004",
        synonyms="Nothing",
        definition="",
        semantic_type="",
    )
    path.write_text(body, encoding="utf-8")
    return path


def test_parse_emits_semantic_type(tmp_path: Path):
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    assert "**Semantic type:** Therapeutic or Preventive Procedure" in result["C100000"]


def test_parse_emits_definition(tmp_path: Path):
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    desc = result["C100000"]
    assert "**Definition:**" in desc
    assert "A percutaneous coronary intervention" in desc


def test_parse_emits_synonyms_excluding_display_name(tmp_path: Path):
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    desc = result["C100000"]
    assert "**Synonyms:**" in desc
    assert "- PCI STEMI" in desc
    assert "Percutaneous Coronary Intervention for STEMI" not in desc


def test_parse_omits_synonyms_when_only_display_name(tmp_path: Path):
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    desc = result["C300002"]
    assert "**Synonyms:**" not in desc


def test_parse_skips_row_with_no_content(tmp_path: Path):
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    assert "C500004" not in result


def test_parse_includes_row_with_only_semantic_type(tmp_path: Path):
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    desc = result["C200001"]
    assert "**Semantic type:** Chemical" in desc
    assert "**Definition:**" not in desc


def test_parse_replaces_em_dash_with_hyphen(tmp_path: Path):
    """Project convention forbids em-dashes anywhere in the codebase or data."""
    f = _write_sample(tmp_path / "thes.txt")
    result = parse_nci_thesaurus_descriptions(f)
    desc = result["C400003"]
    assert "\u2014" not in desc
    assert "em-dash" in desc


def test_parse_accepts_zipped_input(tmp_path: Path):
    import zipfile
    f = _write_sample(tmp_path / "inner.txt")
    zip_path = tmp_path / "nci_thesaurus.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(f, arcname="Thesaurus.txt")
    result = parse_nci_thesaurus_descriptions(zip_path)
    assert "C100000" in result
