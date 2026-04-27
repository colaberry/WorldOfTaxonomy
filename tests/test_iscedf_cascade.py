"""Tests for the ISCED-F 2013 single-child cascade.

ISCED-F has a 2/3/4-digit hierarchy. Some 2-digit broad fields
(``01 Education``) and 3-digit narrow fields (``001 Basic programmes``)
have no description in the ESCO export, but a single 4-digit child
that does. For parents with exactly one populated child, cascading
the child's description up is safe.
"""
from world_of_taxonomy.ingest.iscedf_cascade import (
    iscedf_child_prefix,
    build_parent_mapping,
)


def test_iscedf_child_prefix_returns_full_code():
    # A parent's children share its code as a prefix
    assert iscedf_child_prefix("001") == "001"
    assert iscedf_child_prefix("01") == "01"


def test_build_parent_mapping_picks_singleton_child():
    populated = {
        "0011": "Basic programmes content.",
        "0021": "Literacy and numeracy content.",
    }
    parents = ["001", "002"]
    out = build_parent_mapping(parents, populated)
    assert out["001"] == "Basic programmes content."
    assert out["002"] == "Literacy and numeracy content."


def test_build_parent_mapping_skips_multi_child():
    populated = {
        "0211": "Audio-visual.",
        "0212": "Fashion design.",
        "0213": "Fine arts.",
    }
    parents = ["021"]
    out = build_parent_mapping(parents, populated)
    assert "021" not in out


def test_build_parent_mapping_skips_parent_without_children():
    out = build_parent_mapping(["999"], {})
    assert out == {}


def test_build_parent_mapping_only_uses_direct_children():
    """Children must extend the parent code by exactly one digit."""
    populated = {
        # not a direct child of "01" - "0111" is a grandchild
        "0111": "grandchild content",
    }
    out = build_parent_mapping(["01"], populated)
    # "01" has no direct child (which would be "011" / "012" / "013"...)
    assert "01" not in out
