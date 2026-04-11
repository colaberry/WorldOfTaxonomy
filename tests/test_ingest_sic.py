"""Tests for SIC 1987 ingester.

Covers unit logic for level/parent/sector determination,
division structure validation, OSHA HTML parsing, BLS CSV parsing,
and integration tests for full ingestion.
"""

import asyncio
import io
import pytest
import tempfile
from pathlib import Path

from world_of_taxanomy.ingest.sic import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    _parse_osha_html,
    _parse_bls_csv,
    SIC_DIVISION_STRUCTURE,
    _MG_TO_DIVISION,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Unit tests: _determine_level ──────────────────────────────


class TestSicDetermineLevel:
    def test_letter_division_is_level_0(self):
        assert _determine_level("A") == 0
        assert _determine_level("D") == 0
        assert _determine_level("J") == 0

    def test_two_digit_major_group_is_level_1(self):
        assert _determine_level("01") == 1
        assert _determine_level("20") == 1
        assert _determine_level("99") == 1

    def test_three_digit_industry_group_is_level_2(self):
        assert _determine_level("011") == 2
        assert _determine_level("201") == 2

    def test_four_digit_industry_is_level_3(self):
        assert _determine_level("0111") == 3
        assert _determine_level("2011") == 3


# ── Unit tests: _determine_parent ─────────────────────────────


class TestSicDetermineParent:
    def test_division_has_no_parent(self):
        assert _determine_parent("A") is None
        assert _determine_parent("J") is None

    def test_major_group_parent_is_division(self):
        assert _determine_parent("01") == "A"
        assert _determine_parent("07") == "A"
        assert _determine_parent("10") == "B"
        assert _determine_parent("20") == "D"
        assert _determine_parent("50") == "F"
        assert _determine_parent("91") == "J"

    def test_industry_group_parent_is_major_group(self):
        assert _determine_parent("011") == "01"
        assert _determine_parent("201") == "20"

    def test_industry_parent_is_industry_group(self):
        assert _determine_parent("0111") == "011"
        assert _determine_parent("2011") == "201"


# ── Unit tests: _determine_sector ─────────────────────────────


class TestSicDetermineSector:
    def test_division_is_its_own_sector(self):
        assert _determine_sector("A") == "A"
        assert _determine_sector("J") == "J"

    def test_deep_code_resolves_to_division(self):
        assert _determine_sector("0111") == "A"
        assert _determine_sector("2011") == "D"
        assert _determine_sector("50") == "F"
        assert _determine_sector("9111") == "J"

    def test_all_divisions_covered(self):
        """Every major group in the mapping should resolve to a valid division."""
        for mg_num, division in _MG_TO_DIVISION.items():
            code = str(mg_num).zfill(2)
            assert _determine_sector(code) == division, (
                f"Major group {code} should map to division {division}"
            )


# ── Unit tests: division structure ────────────────────────────


class TestSicDivisionStructure:
    def test_all_10_divisions_present(self):
        """SIC has 10 divisions (A through J)."""
        expected = set("ABCDEFGHIJ")
        assert set(SIC_DIVISION_STRUCTURE.keys()) == expected

    def test_no_major_group_overlaps(self):
        """Major group ranges should not overlap between divisions."""
        all_mgs = []
        for _, (_, mg_range) in SIC_DIVISION_STRUCTURE.items():
            all_mgs.extend(mg_range)
        assert len(all_mgs) == len(set(all_mgs)), "Major group overlap detected"

    def test_division_a_covers_01_to_09(self):
        assert list(SIC_DIVISION_STRUCTURE["A"][1]) == list(range(1, 10))

    def test_division_d_covers_20_to_39(self):
        assert list(SIC_DIVISION_STRUCTURE["D"][1]) == list(range(20, 40))

    def test_division_j_covers_91_to_99(self):
        assert list(SIC_DIVISION_STRUCTURE["J"][1]) == list(range(91, 100))

    def test_reverse_lookup_complete(self):
        """Every major group should have a reverse lookup entry."""
        for division, (_, mg_range) in SIC_DIVISION_STRUCTURE.items():
            for mg in mg_range:
                assert _MG_TO_DIVISION[mg] == division


# ── Unit tests: OSHA HTML parsing ─────────────────────────────


class TestParseOshaHtml:
    def test_parses_divisions_and_major_groups(self):
        """Parse a minimal OSHA-like HTML snippet."""
        html = """
        <p><a href="/data/sic-manual/division-a" title="Division A: Agriculture, Forestry, And Fishing">Division A: Agriculture, Forestry, And Fishing</a></p>
        <ul>
            <li><a href="/data/sic-manual/major-group-01" title="Major Group 01: Agricultural Production Crops">Major Group 01: Agricultural Production Crops</a></li>
            <li><a href="/data/sic-manual/major-group-02" title="Major Group 02: Agriculture Production Livestock">Major Group 02: Agriculture Production Livestock</a></li>
        </ul>
        <p><a href="/data/sic-manual/division-b" title="Division B: Mining">Division B: Mining</a></p>
        <ul>
            <li><a href="/data/sic-manual/major-group-10" title="Major Group 10: Metal Mining">Major Group 10: Metal Mining</a></li>
        </ul>
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html)
            f.flush()
            results = _parse_osha_html(Path(f.name))

        codes = {code: title for code, title in results}
        assert "A" in codes
        assert codes["A"] == "Agriculture, Forestry, And Fishing"
        assert "B" in codes
        assert codes["B"] == "Mining"
        assert "01" in codes
        assert "02" in codes
        assert "10" in codes

    def test_parses_real_osha_file(self):
        """Parse the actual downloaded OSHA HTML if available."""
        from world_of_taxanomy.ingest.sic import _get_project_root
        html_path = _get_project_root() / "data/sic/OSHA_SIC.html"
        if not html_path.exists():
            pytest.skip("OSHA HTML file not downloaded")

        results = _parse_osha_html(html_path)
        codes = {code for code, _ in results}

        # Should have all 10 divisions
        for letter in "ABCDEFGHIJ":
            assert letter in codes, f"Missing division {letter}"

        # Should have major groups (at least 70+)
        mg_codes = {c for c in codes if c.isdigit() and len(c) == 2}
        assert len(mg_codes) >= 70, f"Expected 70+ major groups, got {len(mg_codes)}"


# ── Unit tests: BLS CSV parsing ───────────────────────────────


class TestParseBLSCsv:
    def test_parses_standard_csv(self):
        """Parse a CSV with industry_code and industry_title columns."""
        csv_content = """industry_code,industry_title
01,"Agricultural Production Crops"
011,"Cash Grains"
0111,"Wheat"
0112,"Rice"
20,"Food And Kindred Products"
201,"Meat Products"
2011,"Meat Packing Plants"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            results = _parse_bls_csv(Path(f.name))

        codes = {code: title for code, title in results}
        assert "01" in codes
        assert "011" in codes
        assert "0111" in codes
        assert codes["0111"] == "Wheat"
        assert "2011" in codes
        assert codes["2011"] == "Meat Packing Plants"

    def test_skips_non_numeric_codes(self):
        """Non-numeric codes (headers, letters, etc.) should be skipped."""
        csv_content = """code,title
ABC,"Not a code"
01,"Valid"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            results = _parse_bls_csv(Path(f.name))

        codes = {code for code, _ in results}
        assert "01" in codes
        assert "ABC" not in codes

    def test_skips_codes_with_wrong_length(self):
        """Codes with 1 or 5+ digits should be skipped."""
        csv_content = """code,title
1,"Too short"
01,"Just right"
12345,"Too long"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            results = _parse_bls_csv(Path(f.name))

        codes = {code for code, _ in results}
        assert "01" in codes
        assert len(codes) == 1


# ── Integration test: full ingestion ──────────────────────────


def test_ingest_sic_from_synthetic_data(db_pool):
    """Integration test: ingest from synthetic CSV + HTML data."""

    html_content = """
    <p><a title="Division A: Agriculture, Forestry, And Fishing">Division A: Agriculture, Forestry, And Fishing</a></p>
    <li><a title="Major Group 01: Agricultural Production Crops">Major Group 01: Agricultural Production Crops</a></li>
    <li><a title="Major Group 02: Agriculture Production Livestock">Major Group 02: Agriculture Production Livestock</a></li>
    <p><a title="Division D: Manufacturing">Division D: Manufacturing</a></p>
    <li><a title="Major Group 20: Food And Kindred Products">Major Group 20: Food And Kindred Products</a></li>
    """

    csv_content = """industry_code,industry_title
01,"Agricultural Production Crops"
011,"Cash Grains"
0111,"Wheat"
0112,"Rice"
02,"Agriculture Production Livestock"
20,"Food And Kindred Products"
201,"Meat Products"
2011,"Meat Packing Plants"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as hf, \
         tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as cf:
        hf.write(html_content)
        hf.flush()
        cf.write(csv_content)
        cf.flush()

        html_path = Path(hf.name)
        csv_path = Path(cf.name)

    async def _test():
        from world_of_taxanomy.ingest.sic import ingest_sic_1987

        async with db_pool.acquire() as conn:
            # Clear any existing SIC data
            await conn.execute("DELETE FROM classification_node WHERE system_id = 'sic_1987'")
            await conn.execute("DELETE FROM classification_system WHERE id = 'sic_1987'")

            count = await ingest_sic_1987(conn, csv_path=csv_path, html_path=html_path)

            # Should have: 10 divisions (hardcoded) + 3 major groups from HTML
            # + 3-digit and 4-digit from CSV = more nodes
            assert count > 10, f"Expected 10+ SIC codes, got {count}"

            # Verify system was registered
            row = await conn.fetchrow(
                "SELECT * FROM classification_system WHERE id = 'sic_1987'"
            )
            assert row is not None
            assert row["node_count"] == count
            assert row["tint_color"] == "#78716C"

            # Verify division A exists
            div_a = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'sic_1987' AND code = 'A'"
            )
            assert div_a is not None
            assert div_a["level"] == 0
            assert div_a["parent_code"] is None

            # Verify major group 01 has parent A
            mg_01 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'sic_1987' AND code = '01'"
            )
            assert mg_01 is not None
            assert mg_01["level"] == 1
            assert mg_01["parent_code"] == "A"

            # Verify industry group 011 has parent 01
            ig_011 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'sic_1987' AND code = '011'"
            )
            assert ig_011 is not None
            assert ig_011["level"] == 2
            assert ig_011["parent_code"] == "01"

            # Verify industry 0111 has parent 011
            ind_0111 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'sic_1987' AND code = '0111'"
            )
            assert ind_0111 is not None
            assert ind_0111["level"] == 3
            assert ind_0111["parent_code"] == "011"
            assert ind_0111["sector_code"] == "A"

            # Verify leaf status: 0111 should be a leaf (no children)
            assert ind_0111["is_leaf"] is True

            # Verify non-leaf status: 01 should NOT be a leaf
            assert mg_01["is_leaf"] is False

    _run(_test())


def test_ingest_sic_from_real_files(db_pool):
    """Integration test: ingest from the real OSHA HTML + BLS CSV.

    Skips if the data files haven't been downloaded yet.
    """
    from world_of_taxanomy.ingest.sic import ingest_sic_1987, _get_project_root

    root = _get_project_root()
    html_path = root / "data/sic/OSHA_SIC.html"
    csv_path = root / "data/sic/sic-titles.csv"

    if not html_path.exists():
        pytest.skip("OSHA HTML not downloaded")
    if not csv_path.exists():
        pytest.skip("BLS CSV not downloaded - run ingestion first")

    async def _test():
        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM classification_node WHERE system_id = 'sic_1987'")
            await conn.execute("DELETE FROM classification_system WHERE id = 'sic_1987'")

            count = await ingest_sic_1987(conn, csv_path=csv_path, html_path=html_path)

            # SIC has ~1000+ codes total (10 divisions + ~84 major groups + groups + industries)
            assert count > 400, f"Expected 400+ SIC codes, got {count}"

            # Verify all 10 divisions exist
            divisions = await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id = 'sic_1987' AND level = 0"
            )
            div_codes = {r["code"] for r in divisions}
            expected_divs = set("ABCDEFGHIJ")
            assert div_codes == expected_divs, f"Missing divisions: {expected_divs - div_codes}"

            # Verify hierarchy: major group 20 should have parent D (Manufacturing)
            node_20 = await conn.fetchrow(
                "SELECT * FROM classification_node WHERE system_id = 'sic_1987' AND code = '20'"
            )
            assert node_20 is not None
            assert node_20["parent_code"] == "D"

            # Verify leaf nodes exist
            leaf_count = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node WHERE system_id = 'sic_1987' AND is_leaf = TRUE"
            )
            assert leaf_count > 0, "Should have leaf nodes"

    _run(_test())
