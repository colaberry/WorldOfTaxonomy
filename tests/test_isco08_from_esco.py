"""Tests for the ISCO-08 description enricher that reuses the ESCO cache.

ESCO v1.2.1 publishes ISCO groups as ``skos:Concept`` entries with
``uri`` of the form ``http://data.europa.eu/esco/isco/C<notation>``
and an English ``description.nodeLiteral`` field. This parser streams
the ESCO JSON-LD, filters to ISCO entries, and emits
``{notation: english_description}``.
"""
from pathlib import Path

from world_of_taxonomy.ingest.isco08_from_esco import (
    extract_english_description,
    is_isco_entry,
)


def test_is_isco_entry_detects_isco_uri():
    assert is_isco_entry({"uri": "http://data.europa.eu/esco/isco/C1111"})
    assert is_isco_entry({"uri": "http://data.europa.eu/esco/isco/C0"})


def test_is_isco_entry_rejects_occupation_uri():
    assert not is_isco_entry({
        "uri": "http://data.europa.eu/esco/occupation/abc-123"
    })


def test_is_isco_entry_rejects_skill_uri():
    assert not is_isco_entry({
        "uri": "http://data.europa.eu/esco/skill/xyz-789"
    })


def test_extract_english_description_from_single_object():
    item = {
        "description": {
            "language": "en",
            "nodeLiteral": "Legislators determine and direct policies.",
        },
    }
    assert extract_english_description(item).startswith("Legislators determine")


def test_extract_english_description_from_list_picks_english():
    item = {
        "description": [
            {"language": "de", "nodeLiteral": "German text."},
            {"language": "en", "nodeLiteral": "English text."},
            {"language": "fr", "nodeLiteral": "French text."},
        ],
    }
    assert extract_english_description(item) == "English text."


def test_extract_english_description_returns_empty_when_missing():
    assert extract_english_description({}) == ""
    assert extract_english_description({"description": {}}) == ""
    assert extract_english_description({"description": [
        {"language": "de", "nodeLiteral": "Only German."}
    ]}) == ""


def test_extract_english_description_strips_em_dashes():
    item = {
        "description": {
            "language": "en",
            "nodeLiteral": "Some text \u2014 continues.",
        },
    }
    assert "\u2014" not in extract_english_description(item)
    assert "-" in extract_english_description(item)
