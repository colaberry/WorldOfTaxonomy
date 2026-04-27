"""Tests for NAICS 2022 4-digit industry group cascade.

Industry groups (4 digits) are parents of industries (5 digits) which
are parents of national industries (6 digits). For groups with exactly
one 5-digit child, we cascade the resolved description up. When a
5-digit child has only a "See industry description for X" pointer, we
follow the chain one more hop to the 6-digit to get the real text.
"""
from world_of_taxonomy.ingest.naics2022_cascade import (
    is_see_pointer,
    resolve_pointer_target,
    resolve_description,
)


def test_is_see_pointer_detects_redirect_form():
    assert is_see_pointer("See industry description for 112210.")
    assert is_see_pointer("See industry description for 113110.")
    assert is_see_pointer("  See industry description for 114210.  ")


def test_is_see_pointer_rejects_real_description():
    assert not is_see_pointer("This industry comprises establishments.")
    assert not is_see_pointer("")


def test_resolve_pointer_target_extracts_code():
    assert resolve_pointer_target("See industry description for 112210.") == "112210"
    assert resolve_pointer_target("See industry description for 114210.") == "114210"


def test_resolve_pointer_target_returns_none_when_not_pointer():
    assert resolve_pointer_target("This industry comprises.") is None
    assert resolve_pointer_target("See industry description") is None


def test_resolve_description_walks_pointer_chain():
    all_codes = {
        "11221": "See industry description for 112210.",
        "112210": "This industry comprises establishments raising hogs.",
    }
    assert resolve_description("11221", all_codes).startswith(
        "This industry comprises establishments raising hogs"
    )


def test_resolve_description_returns_real_text_directly():
    all_codes = {
        "11111": "This industry comprises soybean establishments.",
    }
    assert resolve_description("11111", all_codes).startswith(
        "This industry comprises soybean"
    )


def test_resolve_description_breaks_on_missing_target():
    all_codes = {
        "11221": "See industry description for 112210.",
        # 112210 missing
    }
    assert resolve_description("11221", all_codes) == ""


def test_resolve_description_breaks_on_loop():
    all_codes = {
        "A": "See industry description for B.",
        "B": "See industry description for A.",
    }
    assert resolve_description("A", all_codes) == ""
