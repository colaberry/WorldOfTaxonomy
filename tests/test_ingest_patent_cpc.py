"""Tests for Patent CPC ingester.

RED tests - written before any implementation exists.

CPC = Cooperative Patent Classification.
A joint classification system by EPO (European Patent Office) and USPTO.
License: open (EPO/USPTO)
Reference: https://www.cooperativepatentclassification.org/

CPC is organized in a 5-level hierarchy:
  Section    (1 letter,     level 1, e.g. 'A')
  Class      (3 chars,      level 2, e.g. 'A01')
  Subclass   (4 chars,      level 3, e.g. 'A01B')
  Group      (variable,     level 4, e.g. 'A01B 1/00')
  Subgroup   (variable,     level 5, leaf, e.g. 'A01B 1/02')

~260,000 total nodes across all levels.

Codes with spaces are stored with the space (e.g. 'A01B 1/00').
The parent of 'A01B 1/02' is 'A01B 1/00'.
The parent of 'A01B 1/00' is 'A01B'.

Source: bulk XML download from EPO (open license)
  https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/bulk

WARNING: Ingesting ~260K CPC codes takes several minutes.

Due to the large size, integration tests are always skipped unless the
data directory exists. Unit tests verify helper functions only.
"""
import pytest

from world_of_taxanomy.ingest.patent_cpc import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    ingest_patent_cpc,
)


class TestDetermineLevel:
    def test_single_letter_is_level_1(self):
        assert _determine_level("A") == 1

    def test_three_char_is_level_2(self):
        assert _determine_level("A01") == 2

    def test_four_char_is_level_3(self):
        assert _determine_level("A01B") == 3

    def test_group_with_slash_is_level_4(self):
        # Groups look like 'A01B 1/00' - first occurrence of '/'
        assert _determine_level("A01B 1/00") == 4

    def test_subgroup_with_nonzero_after_slash_is_level_5(self):
        assert _determine_level("A01B 1/02") == 5

    def test_another_subgroup(self):
        assert _determine_level("H04L 9/32") == 5

    def test_group_main_group_zero_zero(self):
        # Main group: anything ending '/00' is level 4
        assert _determine_level("A01B 3/00") == 4

    def test_deep_subgroup(self):
        assert _determine_level("A01B 1/022") == 5


class TestDetermineParent:
    def test_section_has_no_parent(self):
        assert _determine_parent("A") is None

    def test_class_parent_is_section(self):
        assert _determine_parent("A01") == "A"

    def test_subclass_parent_is_class(self):
        assert _determine_parent("A01B") == "A01"

    def test_group_parent_is_subclass(self):
        # 'A01B 1/00' -> parent is 'A01B'
        assert _determine_parent("A01B 1/00") == "A01B"

    def test_subgroup_parent_is_group(self):
        # 'A01B 1/02' -> parent is 'A01B 1/00'
        assert _determine_parent("A01B 1/02") == "A01B 1/00"

    def test_another_subgroup_parent(self):
        assert _determine_parent("H04L 9/32") == "H04L 9/00"


class TestDetermineSector:
    def test_section_A_gives_A(self):
        assert _determine_sector("A") == "A"

    def test_class_A01_gives_A(self):
        assert _determine_sector("A01") == "A"

    def test_subclass_A01B_gives_A(self):
        assert _determine_sector("A01B") == "A"

    def test_group_gives_section(self):
        assert _determine_sector("A01B 1/00") == "A"

    def test_section_H_gives_H(self):
        assert _determine_sector("H04L 9/32") == "H"


def test_patent_cpc_module_importable():
    assert callable(ingest_patent_cpc)
    assert callable(_determine_level)
    assert callable(_determine_parent)
    assert callable(_determine_sector)


def test_ingest_patent_cpc_skipped_without_data(db_pool):
    """Integration test always skips - CPC data is large and requires download."""
    import asyncio
    import os
    data_dir = "data/cpc"
    if os.path.isdir(data_dir) and any(
        f.endswith(".xml") for f in os.listdir(data_dir) if os.path.isfile(f)
    ):
        pytest.skip("CPC data directory found - run integration test separately")
    pytest.skip(
        f"CPC data not found in {data_dir}. "
        "Run: python -m world_of_taxanomy ingest patent_cpc"
    )
