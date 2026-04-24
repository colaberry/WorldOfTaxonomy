"""Tests for the NACE Rev 2 group (XX.X) -> class (XX.XX) cascade.

Some NACE groups have no explanatory note in the EU Publications
Office RDF because they are defined entirely by their constituent
classes. When a group has exactly one class child with a populated
description, cascading the child's text up to the parent is safe.
"""
from world_of_taxonomy.ingest.nace_group_cascade import (
    build_group_mapping,
    is_class_child_of,
)


def test_is_class_child_of_recognizes_same_group():
    assert is_class_child_of(child="01.11", group="01.1")
    assert is_class_child_of(child="02.10", group="02.1")


def test_is_class_child_of_rejects_different_group():
    assert not is_class_child_of(child="01.11", group="02.1")
    assert not is_class_child_of(child="02.10", group="01.1")


def test_is_class_child_of_rejects_non_class_codes():
    # A 2-digit division is not a class child of a group
    assert not is_class_child_of(child="01", group="01.1")
    # A group cannot be its own child
    assert not is_class_child_of(child="01.1", group="01.1")


def test_build_group_mapping_single_child():
    classes = {
        "01.30": "Plant propagation description.",
        "01.50": "Mixed farming description.",
    }
    groups = ["01.3", "01.5"]
    out = build_group_mapping(groups, classes)
    assert out["01.3"] == "Plant propagation description."
    assert out["01.5"] == "Mixed farming description."


def test_build_group_mapping_skips_multi_child():
    classes = {
        "08.11": "Stone.",
        "08.12": "Sand.",
    }
    groups = ["08.1"]  # two children
    out = build_group_mapping(groups, classes)
    assert "08.1" not in out


def test_build_group_mapping_skips_group_without_classes():
    classes = {}
    groups = ["99.9"]
    out = build_group_mapping(groups, classes)
    assert out == {}
