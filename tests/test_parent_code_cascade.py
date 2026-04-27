"""Tests for the parent_code-based cascade."""
from world_of_taxonomy.ingest.parent_code_cascade import build_parent_mapping


def test_single_populated_child_cascades_up():
    out = build_parent_mapping(
        parent_codes=["P1", "P2"],
        populated_children=[
            ("C11", "P1", "P1's only child description."),
            ("C21", "P2", "P2's only child description."),
        ],
    )
    assert out["P1"] == "P1's only child description."
    assert out["P2"] == "P2's only child description."


def test_multi_populated_children_skip_parent():
    out = build_parent_mapping(
        parent_codes=["P1"],
        populated_children=[
            ("C11", "P1", "First child."),
            ("C12", "P1", "Second child."),
        ],
    )
    assert "P1" not in out


def test_empty_descriptions_do_not_count():
    out = build_parent_mapping(
        parent_codes=["P1"],
        populated_children=[
            ("C11", "P1", ""),
            ("C12", "P1", "Real content."),
        ],
    )
    assert out["P1"] == "Real content."


def test_missing_parent_code_in_child_record():
    out = build_parent_mapping(
        parent_codes=["P1"],
        populated_children=[
            ("C11", None, "Orphan child."),
        ],
    )
    assert out == {}


def test_unrelated_children_dont_pollute_parent():
    out = build_parent_mapping(
        parent_codes=["P1"],
        populated_children=[
            ("C11", "P1", "Right child."),
            ("C99", "PX", "Unrelated."),
        ],
    )
    assert out["P1"] == "Right child."
