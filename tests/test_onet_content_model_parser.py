"""Tests for the ONET Content Model description enricher.

The O*NET database publishes ``Content Model Reference.txt`` inside its
bulk-download zip. Each row has ``Element ID``, ``Element Name``, and
``Description``. We index by the normalized ``Element Name`` so that
callers can look up descriptions by matching DB titles to ONET
Element Names.
"""
from pathlib import Path

from world_of_taxonomy.ingest.onet_content_model import (
    normalize_title,
    parse_content_model_reference,
)


def test_normalize_title_strips_and_lowers():
    assert normalize_title("  Cognitive Abilities  ") == "cognitive abilities"
    assert normalize_title("WORK Context") == "work context"


def test_parse_content_model_reference_keys_by_normalized_title(tmp_path: Path):
    f = tmp_path / "cm.txt"
    f.write_text(
        "Element ID\tElement Name\tDescription\n"
        "1.A.1\tCognitive Abilities\tAbilities that influence problem solving.\n"
        "1.A.2\tPsychomotor Abilities\tAbilities that influence motor skills.\n"
    )
    out = parse_content_model_reference(f)
    assert out["cognitive abilities"].startswith("Abilities that influence problem")
    assert out["psychomotor abilities"].startswith("Abilities that influence motor")


def test_parse_content_model_reference_skips_self_referential(tmp_path: Path):
    """Some rows have Description == Element Name -- those are
    placeholder top-level categories (Worker Characteristics, etc.).
    We skip them so the caller does not pollute real descriptions.
    """
    f = tmp_path / "cm.txt"
    f.write_text(
        "Element ID\tElement Name\tDescription\n"
        "1\tWorker Characteristics\tWorker Characteristics\n"
        "1.A.1\tCognitive Abilities\tAbilities that influence problem solving.\n"
    )
    out = parse_content_model_reference(f)
    assert "worker characteristics" not in out
    assert "cognitive abilities" in out


def test_parse_content_model_reference_strips_em_dashes(tmp_path: Path):
    f = tmp_path / "cm.txt"
    f.write_text(
        "Element ID\tElement Name\tDescription\n"
        "X\tTest Item\tA description \u2014 with em-dash.\n"
    )
    out = parse_content_model_reference(f)
    assert "\u2014" not in out["test item"]
