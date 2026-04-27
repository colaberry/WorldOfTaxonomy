"""Tests for the LLM description generator for skeleton taxonomies.

The structural ingester for many small reference systems (OWASP Top 10,
APGAR Score, Bristol Stool, BMI Categories, Pain Scale, MITRE ATT&CK,
etc.) creates 11-30 rows with titles only. This module wraps
``world_of_taxonomy.llm_client.chat_json`` to produce one-sentence
factual descriptions for each leaf row, with strict response
sanitization.
"""
from world_of_taxonomy.ingest.llm_descriptions import (
    build_messages,
    sanitize_response,
)


def test_build_messages_includes_system_code_and_title():
    messages = build_messages(
        system_name="OWASP Top 10 Web Application Security Risks",
        code="OW.01",
        title="A01: Broken Access Control",
    )
    assert isinstance(messages, list)
    assert any("OWASP Top 10" in (m.get("content") or "") for m in messages)
    assert any("Broken Access Control" in (m.get("content") or "") for m in messages)


def test_build_messages_has_system_and_user_roles():
    messages = build_messages(
        system_name="X", code="Y", title="Z",
    )
    roles = [m.get("role") for m in messages]
    assert "system" in roles
    assert "user" in roles


def test_build_messages_includes_parent_context_when_given():
    """For codes with terse titles like 'Magnesium Mg', the parent path
    helps the model disambiguate. The optional parent_context goes into
    the user message verbatim."""
    messages = build_messages(
        system_name="UNSPSC",
        code="12141502",
        title="Magnesium Mg",
        parent_context="Chemicals\nElements and gases\nEarth metals",
    )
    user = next(m["content"] for m in messages if m["role"] == "user")
    assert "Chemicals" in user
    assert "Earth metals" in user
    assert "Hierarchy" in user or "context" in user.lower()


def test_build_messages_omits_context_section_when_empty():
    """No parent_context -> the original short user template is used."""
    messages = build_messages(
        system_name="X", code="Y", title="Z", parent_context="",
    )
    user = next(m["content"] for m in messages if m["role"] == "user")
    assert "Hierarchy" not in user


def test_sanitize_response_strips_em_dash():
    out = sanitize_response("Foo \u2014 bar.")
    assert "\u2014" not in out


def test_sanitize_response_collapses_runs_of_whitespace():
    out = sanitize_response("Foo    bar\n\n\n\nbaz.")
    assert "  " not in out
    assert "\n\n\n" not in out


def test_sanitize_response_strips_leading_quotes_and_trailing_quotes():
    """Models sometimes quote their answer. Strip surrounding quotes."""
    out = sanitize_response('"This is the description."')
    assert not out.startswith('"')
    assert not out.endswith('"')
    assert "description" in out


def test_sanitize_response_returns_empty_for_too_short():
    """Reject obvious LLM refusals or null answers."""
    assert sanitize_response("") == ""
    assert sanitize_response("N/A") == ""
    assert sanitize_response("...") == ""


def test_sanitize_response_returns_empty_for_too_long():
    """Reject blob outputs (probably the model leaked the prompt or rambled)."""
    long = "x" * 5000
    assert sanitize_response(long) == ""


def test_sanitize_response_strips_assistant_role_prefix():
    """Some models prepend the role label."""
    out = sanitize_response("Description: This is the answer.")
    assert "Description:" not in out
    assert "This is the answer." in out


def test_sanitize_response_normalizes_unicode_dashes():
    """Models often emit non-breaking hyphens / en-dashes / figure
    dashes inside numeric ranges. Convert them all to ASCII '-'."""
    out = sanitize_response("Range 18.5\u201124.9 covers normal weight.")
    assert "\u2011" not in out
    assert "18.5-24.9" in out


def test_sanitize_response_normalizes_narrow_nbsp():
    out = sanitize_response("OWASP\u202fA01 is the top risk.")
    assert "\u202f" not in out
    assert "OWASP A01" in out


def test_sanitize_response_rejects_refusal_phrases():
    out = sanitize_response("BS.04 is not a recognized entry in the OWASP framework, but...")
    assert out == ""


def test_sanitize_response_rejects_ai_disclaimer():
    out = sanitize_response("As an AI language model, I cannot provide that information.")
    assert out == ""


def test_sanitize_response_normalizes_curly_quotes():
    out = sanitize_response("Score \u201cnormal\u201d range \u2018ideal\u2019.")
    assert "\u201c" not in out
    assert "\u2019" not in out
    assert '"normal"' in out


def test_sanitize_response_strips_nul_bytes():
    """LLMs sometimes emit a stray U+0000 inside text; Postgres rejects
    that as 'invalid byte sequence for encoding UTF8: 0x00'."""
    out = sanitize_response("Foo\x00bar is fine description text here.")
    assert "\x00" not in out
    assert "Foobar" in out


def test_sanitize_response_strips_other_c0_controls():
    """Backspace, vertical tab, etc. are also stripped; tab/newline kept."""
    out = sanitize_response("Foo\x08\x07bar baz spam description text here.")
    assert "\x08" not in out
    assert "\x07" not in out
    assert "Foobar" in out
