"""Tests for the SOC 2018 broad->detailed description cascade.

SOC 2018 "broad occupation" codes (6 digits, ending in ``0``) aggregate
one or more "detailed occupation" codes (6 digits, ending in a non-zero
digit). For broads with exactly one detailed child, the semantic
content is identical: e.g. broad ``11-1010 Chief Executives`` has a
single detailed child ``11-1011 Chief Executives``. We can safely
cascade the child's description up to the parent. For broads with
multiple detailed children, we leave the description empty rather than
concatenate heterogeneous content.
"""
from world_of_taxonomy.ingest.soc2018_cascade import (
    build_broad_mapping,
    soc_broad_prefix,
)


def test_soc_broad_prefix_replaces_trailing_digit():
    assert soc_broad_prefix("11-1010") == "11-101"
    assert soc_broad_prefix("29-1140") == "29-114"


def test_build_broad_mapping_picks_singleton_children():
    detailed = {
        "11-1011": "Description of Chief Executives.",
        "11-2011": "Description of Advertising Managers.",
    }
    broads = ["11-1010", "11-2010"]  # both have a single child each
    out = build_broad_mapping(broads, detailed)
    assert out["11-1010"] == "Description of Chief Executives."
    assert out["11-2010"] == "Description of Advertising Managers."


def test_build_broad_mapping_skips_broads_with_multiple_children():
    detailed = {
        "11-2021": "Marketing.",
        "11-2022": "Sales.",
    }
    broads = ["11-2020"]  # has two children (21, 22)
    out = build_broad_mapping(broads, detailed)
    assert "11-2020" not in out


def test_build_broad_mapping_skips_broads_with_no_populated_children():
    detailed = {}
    broads = ["11-2020"]
    out = build_broad_mapping(broads, detailed)
    assert out == {}


def test_build_broad_mapping_ignores_unrelated_detailed_codes():
    detailed = {
        "29-1141": "Registered Nurses do X.",
        "11-1011": "Chief Executives do Y.",
    }
    broads = ["29-1140"]
    out = build_broad_mapping(broads, detailed)
    # Broad 29-1140 is matched only by child 29-1141, not 11-1011
    assert out == {"29-1140": "Registered Nurses do X."}
