"""Tests for the ANZSIC 2006 single-child cascade."""
from world_of_taxonomy.ingest.anzsic_cascade import (
    build_parent_mapping,
    is_direct_child,
)


def test_is_direct_child_recognizes_one_char_extension():
    assert is_direct_child(child="0111", parent="011")
    assert is_direct_child(child="012", parent="01")


def test_is_direct_child_rejects_grandchild():
    assert not is_direct_child(child="0111", parent="01")


def test_is_direct_child_rejects_unrelated():
    assert not is_direct_child(child="0211", parent="01")


def test_build_parent_mapping_picks_singleton_child():
    populated = {
        "0160": "Dairy cattle farming description.",
        "0180": "Deer farming description.",
    }
    parents = ["016", "018"]
    out = build_parent_mapping(parents, populated)
    assert out["016"] == "Dairy cattle farming description."
    assert out["018"] == "Deer farming description."


def test_build_parent_mapping_skips_multi_child():
    populated = {
        "0171": "Egg production.",
        "0172": "Meat poultry.",
    }
    parents = ["017"]
    out = build_parent_mapping(parents, populated)
    assert "017" not in out


def test_build_parent_mapping_skips_parent_without_children():
    out = build_parent_mapping(["999"], {})
    assert out == {}


def test_build_parent_mapping_only_uses_direct_children():
    populated = {
        "0111": "grandchild content",
    }
    out = build_parent_mapping(["01"], populated)
    assert "01" not in out
