"""Tests for the ISCED-F 2013 description enricher using ESCO JSON-LD.

ESCO v1.2.1 publishes ISCED-F 2013 fields of education as SKOS concepts
at ``http://data.europa.eu/esco/isced-f/<notation>`` with English
``description.nodeLiteral`` bodies. This parser streams the ESCO
graph, filters by URI prefix, and emits ``{notation: description}``.
"""
from world_of_taxonomy.ingest.iscedf2013_from_esco import (
    extract_english_description,
    is_iscedf_entry,
)


def test_is_iscedf_entry_detects_iscedf_uri():
    assert is_iscedf_entry({"uri": "http://data.europa.eu/esco/isced-f/0011"})
    assert is_iscedf_entry({"uri": "http://data.europa.eu/esco/isced-f/00"})


def test_is_iscedf_entry_rejects_other_uri():
    assert not is_iscedf_entry({"uri": "http://data.europa.eu/esco/isco/C1"})
    assert not is_iscedf_entry({"uri": "http://data.europa.eu/esco/occupation/x"})


def test_extract_english_description_from_single_object():
    item = {
        "description": {
            "language": "en",
            "nodeLiteral": "Basic programmes and qualifications description.",
        }
    }
    assert extract_english_description(item).startswith("Basic programmes")


def test_extract_english_description_from_list_picks_english():
    item = {
        "description": [
            {"language": "de", "nodeLiteral": "German."},
            {"language": "en", "nodeLiteral": "English."},
        ]
    }
    assert extract_english_description(item) == "English."


def test_extract_english_description_returns_empty_without_english():
    assert extract_english_description({}) == ""
    assert extract_english_description({"description": {}}) == ""


def test_extract_english_description_strips_em_dashes():
    item = {
        "description": {
            "language": "en",
            "nodeLiteral": "Field X \u2014 description.",
        }
    }
    assert "\u2014" not in extract_english_description(item)
