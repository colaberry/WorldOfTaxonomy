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
import os
import pytest

from world_of_taxanomy.ingest.patent_cpc import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    _normalize_cpc_code,
    _parse_cpc_xml_data,
    ingest_patent_cpc,
)

_COMBINED_ZIP = "data/CPCSchemeXML202601.zip"
_ZIP_AVAILABLE = os.path.exists(_COMBINED_ZIP)


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


class TestNormalizeCpcCode:
    def test_no_slash_unchanged(self):
        assert _normalize_cpc_code("A01B") == "A01B"

    def test_already_has_space_unchanged(self):
        assert _normalize_cpc_code("A01B 1/00") == "A01B 1/00"

    def test_adds_space_to_main_group(self):
        assert _normalize_cpc_code("A01B1/00") == "A01B 1/00"

    def test_adds_space_to_subgroup(self):
        assert _normalize_cpc_code("A01B1/02") == "A01B 1/02"

    def test_adds_space_multi_digit_group(self):
        assert _normalize_cpc_code("A01B10/00") == "A01B 10/00"

    def test_adds_space_deep_subgroup(self):
        assert _normalize_cpc_code("A01B1/022") == "A01B 1/022"

    def test_section_unchanged(self):
        assert _normalize_cpc_code("A") == "A"

    def test_class_unchanged(self):
        assert _normalize_cpc_code("A01") == "A01"


_MINIMAL_CPC_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<class-scheme>
  <classification-item level="5">
    <classification-symbol>A01B</classification-symbol>
    <class-title><title-part><text>SOIL WORKING</text></title-part></class-title>
    <classification-item level="6">
      <classification-symbol>A01B1/00</classification-symbol>
      <class-title><title-part><text>Hand tools</text></title-part></class-title>
    </classification-item>
    <classification-item level="8">
      <classification-symbol>A01B1/02</classification-symbol>
      <class-title><title-part><text>Spades</text></title-part></class-title>
    </classification-item>
  </classification-item>
</class-scheme>
"""


class TestParseCpcXmlData:
    def test_extracts_codes_from_child_element_symbol(self):
        nodes = _parse_cpc_xml_data(_MINIMAL_CPC_XML)
        codes = [code for code, _ in nodes]
        assert "A01B" in codes

    def test_normalizes_group_codes_to_space_format(self):
        nodes = _parse_cpc_xml_data(_MINIMAL_CPC_XML)
        codes = [code for code, _ in nodes]
        assert "A01B 1/00" in codes
        assert "A01B1/00" not in codes

    def test_normalizes_subgroup_codes_to_space_format(self):
        nodes = _parse_cpc_xml_data(_MINIMAL_CPC_XML)
        codes = [code for code, _ in nodes]
        assert "A01B 1/02" in codes

    def test_extracts_titles(self):
        nodes = _parse_cpc_xml_data(_MINIMAL_CPC_XML)
        code_to_title = dict(nodes)
        assert code_to_title.get("A01B") == "SOIL WORKING"
        assert code_to_title.get("A01B 1/00") == "Hand tools"

    def test_returns_list_of_tuples(self):
        nodes = _parse_cpc_xml_data(_MINIMAL_CPC_XML)
        assert isinstance(nodes, list)
        assert all(isinstance(n, tuple) and len(n) == 2 for n in nodes)

    def test_deduplicates_codes(self):
        # Duplicate code in XML should appear only once
        dup_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<class-scheme>
  <classification-item>
    <classification-symbol>A01B1/00</classification-symbol>
    <class-title><title-part><text>First</text></title-part></class-title>
  </classification-item>
  <classification-item>
    <classification-symbol>A01B1/00</classification-symbol>
    <class-title><title-part><text>Duplicate</text></title-part></class-title>
  </classification-item>
</class-scheme>"""
        nodes = _parse_cpc_xml_data(dup_xml)
        codes = [code for code, _ in nodes]
        assert codes.count("A01B 1/00") == 1


def test_patent_cpc_module_importable():
    assert callable(ingest_patent_cpc)
    assert callable(_determine_level)
    assert callable(_determine_parent)
    assert callable(_determine_sector)
    assert callable(_normalize_cpc_code)
    assert callable(_parse_cpc_xml_data)


@pytest.mark.skipif(
    not _ZIP_AVAILABLE,
    reason=f"Combined CPC ZIP not found at {_COMBINED_ZIP}.",
)
def test_ingest_patent_cpc_from_combined_zip(db_pool):
    """Integration test: ingest Patent CPC from CPCSchemeXML202601.zip."""
    import asyncio
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_patent_cpc(conn)
            assert count >= 200_000, f"Expected >= 200K CPC nodes, got {count}"
            assert count <= 350_000, f"Expected <= 350K CPC nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT node_count FROM classification_system WHERE id = 'patent_cpc'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Spot-check structure
            sample = await conn.fetchrow(
                "SELECT code, level, sector_code FROM classification_node "
                "WHERE system_id = 'patent_cpc' AND level = 1 LIMIT 1"
            )
            assert sample is not None
            assert len(sample["code"]) == 1  # section code
            assert sample["sector_code"] == sample["code"]

    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(
    not _ZIP_AVAILABLE,
    reason=f"Combined CPC ZIP not found at {_COMBINED_ZIP}.",
)
def test_ingest_patent_cpc_idempotent(db_pool):
    """Running ingest twice returns same count."""
    import asyncio
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_patent_cpc(conn)
            count2 = await ingest_patent_cpc(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())


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
