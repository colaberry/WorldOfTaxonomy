"""Tests for the ISIC Rev 4 description cascade from NACE Rev 2 notes.

NACE Rev 2 is an EU breakdown of ISIC Rev 4. At the 4-digit class level,
many NACE codes are identical to ISIC codes (e.g. NACE "01.11" and
ISIC "0111" both describe growing of cereals). Where the dots-stripped
NACE code matches an ISIC code, the NACE English note is a valid
description for the ISIC code. We build a cached map once and cascade
it to every ISIC-derived system in the DB.
"""
from pathlib import Path
from textwrap import dedent

from world_of_taxonomy.ingest.isic_cascade_from_nace import (
    build_isic_mapping,
    build_mapping_from_cache,
)


def _write_rdf(path: Path, uri: str, en_core: str, en_exclude: str = "") -> None:
    """Helper: build a minimal NACE-RDF payload on disk."""
    body = f"""<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:skos="http://www.w3.org/2004/02/skos/core#"
  xmlns:xkos="http://rdf-vocabulary.ddialliance.org/xkos#">
  <rdf:Description rdf:about="{uri}">
    <xkos:coreContentNote xml:lang="en">{en_core}</xkos:coreContentNote>"""
    if en_exclude:
        body += f'\n    <xkos:exclusionNote xml:lang="en">{en_exclude}</xkos:exclusionNote>'
    body += "\n  </rdf:Description>\n</rdf:RDF>\n"
    path.write_text(body, encoding="utf-8")


def test_build_mapping_reads_cache_by_uri_suffix(tmp_path: Path):
    _write_rdf(
        tmp_path / "0111.xml",
        "http://data.europa.eu/ux2/nace2/0111",
        "Growing of cereals.",
    )
    _write_rdf(
        tmp_path / "A.xml",
        "http://data.europa.eu/ux2/nace2/A",
        "Agriculture section.",
    )
    mapping = build_mapping_from_cache(tmp_path)
    assert mapping["0111"].startswith("Growing of cereals")
    assert mapping["A"].startswith("Agriculture section")


def test_build_mapping_skips_empty_english(tmp_path: Path):
    _write_rdf(
        tmp_path / "099.xml",
        "http://data.europa.eu/ux2/nace2/099",
        "",
    )
    mapping = build_mapping_from_cache(tmp_path)
    assert "099" not in mapping


def test_build_mapping_ignores_non_xml_files(tmp_path: Path):
    (tmp_path / "README.txt").write_text("not xml")
    _write_rdf(
        tmp_path / "01.xml",
        "http://data.europa.eu/ux2/nace2/01",
        "Division 01.",
    )
    mapping = build_mapping_from_cache(tmp_path)
    assert mapping == {"01": "Division 01."}


def test_build_mapping_handles_malformed_rdf_gracefully(tmp_path: Path):
    (tmp_path / "bad.xml").write_text("<not-closed")
    _write_rdf(
        tmp_path / "02.xml",
        "http://data.europa.eu/ux2/nace2/02",
        "Division 02.",
    )
    mapping = build_mapping_from_cache(tmp_path)
    assert "02" in mapping
    assert "bad" not in mapping


def _write_crosswalk(path: Path, rows: list[tuple[str, str, str, str]]) -> Path:
    """Write an ISIC4_to_NACE2-style CSV with 4 columns."""
    import csv
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ISIC4code", "ISIC4part", "NACE2code", "NACE2part"])
        for r in rows:
            w.writerow(r)
    return path


def test_build_isic_mapping_keeps_only_one_to_one_full_matches(tmp_path: Path):
    # NACE cache has notes for 01.11, 46.61 (suffix 0111 and 4661),
    # and 01.41 / 01.42 (suffix 0141 / 0142).
    cache = tmp_path / "cache"
    cache.mkdir()
    _write_rdf(cache / "0111.xml", "http://data.europa.eu/ux2/nace2/0111",
               "Growing of cereals.")
    _write_rdf(cache / "4661.xml", "http://data.europa.eu/ux2/nace2/4661",
               "Wholesale of agricultural machinery.")
    _write_rdf(cache / "4671.xml", "http://data.europa.eu/ux2/nace2/4671",
               "Wholesale of solid, liquid and gaseous fuels.")
    _write_rdf(cache / "0141.xml", "http://data.europa.eu/ux2/nace2/0141",
               "Raising of cattle and buffaloes.")
    _write_rdf(cache / "0142.xml", "http://data.europa.eu/ux2/nace2/0142",
               "Raising of horses and other equines.")

    xwalk = _write_crosswalk(tmp_path / "xwalk.csv", [
        # 1:1 exact -- keep
        ("0111", "0", "01.11", "0"),
        # ISIC 4661 maps 1:1 to NACE 46.71 (renumbered) -- we want
        # the NACE 46.71 note, NOT the suffix collision with NACE 46.61
        ("4661", "0", "46.71", "0"),
        # 1:N (split) -- skip
        ("0141", "1", "01.41", "1"),
        ("0141", "1", "01.42", "1"),
    ])

    mapping = build_isic_mapping(cache_dir=cache, crosswalk_path=xwalk)

    # ISIC 0111 picks up NACE 01.11's note
    assert mapping["0111"].startswith("Growing of cereals")
    # ISIC 4661 picks up NACE 46.71's note (fuels), NOT 46.61's (machinery)
    assert "fuels" in mapping["4661"]
    assert "agricultural machinery" not in mapping["4661"]
    # ISIC 0141 is split across NACE -- no safe single note, skip
    assert "0141" not in mapping


def test_build_isic_mapping_skips_isic_codes_with_partial_flag(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    _write_rdf(cache / "0111.xml", "http://data.europa.eu/ux2/nace2/0111",
               "Growing of cereals.")
    # Partial ISIC->NACE (part=1) -- skip even though 1:1
    xwalk = _write_crosswalk(tmp_path / "xwalk.csv", [
        ("9999", "1", "01.11", "0"),
    ])
    mapping = build_isic_mapping(cache_dir=cache, crosswalk_path=xwalk)
    assert mapping == {}


def test_build_isic_mapping_skips_codes_without_nace_note(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    # No cache file for NACE 99.99
    xwalk = _write_crosswalk(tmp_path / "xwalk.csv", [
        ("9999", "0", "99.99", "0"),
    ])
    mapping = build_isic_mapping(cache_dir=cache, crosswalk_path=xwalk)
    assert mapping == {}
