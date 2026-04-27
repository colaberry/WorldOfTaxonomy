"""Tests for the ESCO JSON-LD description parser.

The ESCO dataset is distributed as a ~650 MB JSON-LD file with a top
level ``@graph`` array. Every occupation and skill record carries a
``description`` field which is a list of ``NodeLiteral`` entries, one
per language. We pick the English one and write it to
``classification_node.description`` keyed by the UUID portion of the
ESCO URI (which is how our ESCO ingester stores codes).
"""
from world_of_taxonomy.ingest.esco_descriptions import (
    extract_english_description,
    extract_uuid,
)


def test_extract_uuid_from_occupation_uri():
    uri = "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34"
    assert extract_uuid(uri) == "00030d09-2b3a-4efd-87cc-c4ea39d27c34"


def test_extract_uuid_from_skill_uri():
    uri = "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab"
    assert extract_uuid(uri) == "0005c151-5b5a-4a66-8aac-60e734beb1ab"


def test_extract_uuid_returns_none_for_unrecognised_uri():
    assert extract_uuid("http://example.org/not-an-esco-uri") is None
    assert extract_uuid("") is None
    assert extract_uuid(None) is None


def test_extract_english_description_picks_en_literal():
    record = {
        "description": [
            {"language": "de", "nodeLiteral": "Deutsche Beschreibung."},
            {"language": "en", "nodeLiteral": "English description of the concept."},
            {"language": "fr", "nodeLiteral": "Description francaise."},
        ],
    }
    assert (
        extract_english_description(record)
        == "English description of the concept."
    )


def test_extract_english_description_returns_empty_when_no_en():
    """Some ESCO records only have non-English literals; we skip them."""
    record = {
        "description": [
            {"language": "fr", "nodeLiteral": "Description francaise."},
        ],
    }
    assert extract_english_description(record) == ""


def test_extract_english_description_returns_empty_when_no_description():
    assert extract_english_description({}) == ""
    assert extract_english_description({"description": []}) == ""


def test_extract_english_description_normalises_em_dash():
    record = {
        "description": [
            {"language": "en", "nodeLiteral": "A concept \u2014 with em dash."},
        ],
    }
    assert "\u2014" not in extract_english_description(record)


def test_extract_english_description_strips_whitespace():
    record = {
        "description": [
            {"language": "en", "nodeLiteral": "  padded description   \n"},
        ],
    }
    assert extract_english_description(record) == "padded description"


def test_extract_english_description_handles_missing_node_literal():
    """Some entries have an ``@value`` key instead, or no literal at all."""
    record = {
        "description": [
            {"language": "en"},
            {"language": "en", "nodeLiteral": ""},
            {"language": "en", "nodeLiteral": "Non empty."},
        ],
    }
    assert extract_english_description(record) == "Non empty."
