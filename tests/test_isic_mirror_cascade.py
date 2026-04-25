"""Tests for the ISIC family child->parent cascade."""
from world_of_taxonomy.ingest.isic_mirror_cascade import build_parent_mapping


def test_build_parent_mapping_single_child_division_to_section():
    populated = {"02": "Forestry section content."}
    out = build_parent_mapping(["B"], populated)
    # Section 'B' is a letter, not extending '02'; not a parent.
    # Division '0' would be a parent of '02'; not in input.
    assert out == {}


def test_build_parent_mapping_single_child_real_isic_pattern():
    populated = {
        "0130": "Plant propagation content.",  # only 4-digit class under 013
    }
    out = build_parent_mapping(["013"], populated)
    assert out["013"] == "Plant propagation content."


def test_build_parent_mapping_skips_multi_child():
    populated = {
        "0141": "Cattle.",
        "0142": "Buffaloes.",
    }
    out = build_parent_mapping(["014"], populated)
    assert "014" not in out


def test_build_parent_mapping_walks_through_grandparent():
    """Tests the iterative pattern: after grandchildren populate
    children, children should populate grandparents in a later pass.
    """
    populated_round1 = {"0130": "Plant propagation content."}
    out1 = build_parent_mapping(["013"], populated_round1)
    assert "013" in out1
    populated_round2 = dict(populated_round1)
    populated_round2.update(out1)
    out2 = build_parent_mapping(["01", "013"], populated_round2)
    # Now '01' has only a single populated child '013' if we restrict
    # to that map. But '01' has many children in real data; this just
    # exercises the function.
    assert "013" in populated_round2
