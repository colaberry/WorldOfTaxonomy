"""Tests for the WHO ICD-11 API entity -> description renderer.

The WHO ICD-11 API returns a JSON entity per code with fields like
``definition``, ``longDefinition``, ``inclusion[]``, ``exclusion[]``,
and ``codingNote``. The renderer turns that into a markdown block that
is stored in ``classification_node.description``.

These tests are pure -- no network. They pin the shape of the markdown
we write to the DB, which matters because the string is user-visible.
"""
from world_of_taxonomy.ingest.icd11_api import (
    render_entity,
    rewrite_release,
)


def test_rewrite_release_inserts_date_segment():
    """The Simple Tabulation URIs omit the release date; the API needs it."""
    raw = "http://id.who.int/icd/release/11/mms/257068234"
    assert (
        rewrite_release(raw, "2026-01")
        == "https://id.who.int/icd/release/11/2026-01/mms/257068234"
    )


def test_rewrite_release_is_idempotent_if_date_already_present():
    """If the URI already has a release date, rewriting to the same date is a no-op
    (modulo http -> https upgrade)."""
    dated = "https://id.who.int/icd/release/11/2026-01/mms/257068234"
    assert rewrite_release(dated, "2026-01") == dated


def test_rewrite_release_switches_existing_date():
    """Switching from one release to another should replace the date segment."""
    old = "https://id.who.int/icd/release/11/2024-01/mms/257068234"
    assert (
        rewrite_release(old, "2026-01")
        == "https://id.who.int/icd/release/11/2026-01/mms/257068234"
    )


def test_rewrite_release_upgrades_http_to_https():
    """WHO's CDN 301-redirects http -> https; upgrading at rewrite avoids a round trip."""
    raw = "http://id.who.int/icd/release/11/2026-01/mms/257068234"
    assert rewrite_release(raw, "2026-01").startswith("https://")


def _en(value: str) -> dict:
    return {"@language": "en", "@value": value}


def test_render_full_entity():
    entity = {
        "code": "BA00",
        "title": _en("Essential hypertension"),
        "definition": _en(
            "Essential (primary) hypertension, accounting for 95% of all cases."
        ),
        "longDefinition": _en(
            "Defined through the measurement of the blood pressure using cuff method."
        ),
        "inclusion": [{"label": _en("high blood pressure")}],
        "exclusion": [
            {"label": _en("Cerebrovascular diseases")},
            {"label": _en("Secondary hypertension")},
        ],
    }
    out = render_entity(entity)
    assert "**Definition:** Essential (primary) hypertension" in out
    assert "**Long definition:** Defined through the measurement" in out
    assert "**Inclusions:**" in out
    assert "- high blood pressure" in out
    assert "**Exclusions:**" in out
    assert "- Cerebrovascular diseases" in out
    assert "- Secondary hypertension" in out


def test_render_returns_empty_when_nothing_to_say():
    """If the entity has no definition/long/inclusion/exclusion/coding note,
    we return empty string so the caller can skip the row."""
    entity = {"code": "XYZ", "title": _en("Some code")}
    assert render_entity(entity) == ""


def test_render_handles_definition_only():
    entity = {"code": "X", "definition": _en("Just a short definition.")}
    out = render_entity(entity)
    assert out == "**Definition:** Just a short definition."


def test_render_handles_long_definition_only():
    entity = {"code": "X", "longDefinition": _en("Only long.")}
    assert render_entity(entity) == "**Long definition:** Only long."


def test_render_renders_coding_note_list():
    """codingNote.note is a list of language-tagged strings."""
    entity = {
        "code": "1C1G",
        "codingNote": {
            "@language": "en",
            "note": [
                _en("Use additional code if desired, to identify causative organism."),
                _en("Code first the underlying condition."),
            ],
        },
    }
    out = render_entity(entity)
    assert "**Coding note:**" in out
    assert "Use additional code if desired" in out
    assert "Code first the underlying" in out


def test_render_strips_em_dashes():
    entity = {"code": "X", "definition": _en("A \u2014 definition with em dash.")}
    out = render_entity(entity)
    assert "\u2014" not in out
    assert "A - definition" in out


def test_render_blocks_are_separated_by_blank_lines():
    """Markdown blocks render cleanly when separated by blank lines."""
    entity = {
        "code": "X",
        "definition": _en("Short."),
        "longDefinition": _en("Long."),
        "inclusion": [{"label": _en("inc1")}],
    }
    out = render_entity(entity)
    assert "\n\n" in out
    sections = out.split("\n\n")
    assert any(s.startswith("**Definition:**") for s in sections)
    assert any(s.startswith("**Long definition:**") for s in sections)
    assert any(s.startswith("**Inclusions:**") for s in sections)


def test_render_skips_empty_inclusion_labels():
    entity = {
        "code": "X",
        "inclusion": [
            {"label": _en("real item")},
            {"label": _en("")},
            {},
        ],
    }
    out = render_entity(entity)
    assert "- real item" in out
    assert "**Inclusions:**\n- real item" in out


def test_render_ignores_non_english_values_gracefully():
    """If a field comes back without @value (or empty), skip it cleanly."""
    entity = {
        "code": "X",
        "definition": {"@language": "en"},
        "longDefinition": _en("Only this one has content."),
    }
    out = render_entity(entity)
    assert "**Definition:**" not in out
    assert "**Long definition:** Only this one" in out
