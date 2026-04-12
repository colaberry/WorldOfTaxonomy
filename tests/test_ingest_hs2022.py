"""Tests for HS 2022 Harmonized System ingester.

RED tests - written before any implementation exists.

Hierarchy:
  L1 - Section (Roman numerals I-XXI, e.g. "I" = Live animals)
  L2 - Chapter (2-digit, e.g. "01" = Live animals)
  L3 - Heading (4-digit, e.g. "0101" = Live horses, asses, mules, hinnies)
  L4 - Subheading (6-digit, leaf, e.g. "010121" = Pure-bred breeding horses)

Source: github.com/datasets/harmonized-system (CC0)
        https://raw.githubusercontent.com/datasets/harmonized-system/main/data/harmonized-system.csv
"""
import pytest
from world_of_taxanomy.ingest.hs2022 import (
    _SECTION_NAMES,
    _determine_level,
    _determine_parent,
    _determine_sector,
    ingest_hs2022,
)


class TestHs2022DetermineLevel:
    def test_section_roman_numeral_is_level_1(self):
        assert _determine_level("I") == 1

    def test_section_xxi_is_level_1(self):
        assert _determine_level("XXI") == 1

    def test_chapter_2digit_is_level_2(self):
        assert _determine_level("01") == 2

    def test_chapter_97_is_level_2(self):
        assert _determine_level("97") == 2

    def test_heading_4digit_is_level_3(self):
        assert _determine_level("0101") == 3

    def test_subheading_6digit_is_level_4(self):
        assert _determine_level("010121") == 4


class TestHs2022DetermineParent:
    def test_section_has_no_parent(self):
        assert _determine_parent("I", csv_parent="TOTAL", section="I") is None

    def test_chapter_parent_is_section(self):
        # Chapter 01 belongs to Section I
        assert _determine_parent("01", csv_parent="TOTAL", section="I") == "I"

    def test_heading_parent_is_chapter(self):
        # Heading 0101 parent is chapter 01
        assert _determine_parent("0101", csv_parent="01", section="I") == "01"

    def test_subheading_parent_is_heading(self):
        # Subheading 010121 parent is heading 0101
        assert _determine_parent("010121", csv_parent="0101", section="I") == "0101"


class TestHs2022DetermineSector:
    def test_section_sector_is_itself(self):
        assert _determine_sector("I", section="I") == "I"

    def test_chapter_sector_is_its_section(self):
        assert _determine_sector("01", section="I") == "I"

    def test_heading_sector_is_section(self):
        assert _determine_sector("0101", section="I") == "I"

    def test_subheading_sector_is_section(self):
        assert _determine_sector("010121", section="I") == "I"


class TestHs2022SectionNames:
    def test_has_21_sections(self):
        assert len(_SECTION_NAMES) == 21

    def test_section_i_is_live_animals(self):
        assert "I" in _SECTION_NAMES
        assert "animal" in _SECTION_NAMES["I"].lower()

    def test_section_xxi_exists(self):
        assert "XXI" in _SECTION_NAMES


def test_ingest_hs2022_from_csv(db_pool):
    """Integration test - ingest from downloaded CSV."""
    import asyncio
    from pathlib import Path

    data_path = Path("data/hs2022.csv")
    if not data_path.exists():
        pytest.skip(f"Download {data_path} first: see world_of_taxanomy/ingest/hs2022.py for URL")

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_hs2022(conn, path=str(data_path))
            assert count >= 6000, f"Expected >= 6000 nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'hs_2022'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Section I must exist at level 1 with no parent
            sec = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'hs_2022' AND code = 'I'"
            )
            assert sec is not None
            assert sec["level"] == 1
            assert sec["parent_code"] is None

            # Chapter 01 at level 2, parent Section I
            ch = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'hs_2022' AND code = '01'"
            )
            assert ch is not None
            assert ch["level"] == 2
            assert ch["parent_code"] == "I"

            # Heading 0101 at level 3, parent 01
            hd = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'hs_2022' AND code = '0101'"
            )
            assert hd is not None
            assert hd["level"] == 3
            assert hd["parent_code"] == "01"

            # Subheading 010121 at level 4, is_leaf=True
            sub = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'hs_2022' AND code = '010121'"
            )
            assert sub is not None
            assert sub["level"] == 4
            assert sub["parent_code"] == "0101"
            assert sub["is_leaf"] is True

    asyncio.get_event_loop().run_until_complete(_run())
