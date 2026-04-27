"""Tests for the verifier prompts + verdict parsing.

Track 2 introduces a generator + verifier pipeline. The generator
(reused from PR #67) produces a candidate description; the verifier
prompt asks gpt-oss:120b to judge whether the description is an
accurate factual match for the (system, code, title) and returns
``yes`` / ``no`` / ``uncertain``.

Tests here cover prompt construction and verdict parsing only -
the LLM call itself is exercised end-to-end via the orchestration
script.
"""
from world_of_taxonomy.ingest.llm_verifier import (
    build_verifier_messages,
    parse_verdict,
)


def test_build_verifier_messages_includes_all_inputs():
    messages = build_verifier_messages(
        system_name="OWASP Top 10 Web Application Security Risks",
        code="OW.01",
        title="A01: Broken Access Control",
        candidate="Broken access control occurs when an application fails to enforce policies...",
    )
    blob = " ".join(m["content"] for m in messages)
    assert "OWASP Top 10" in blob
    assert "Broken Access Control" in blob
    assert "Broken access control occurs when" in blob


def test_parse_verdict_recognizes_yes():
    assert parse_verdict("YES") == "yes"
    assert parse_verdict("yes") == "yes"
    assert parse_verdict("Yes, this is accurate.") == "yes"
    assert parse_verdict("Verdict: yes") == "yes"


def test_parse_verdict_recognizes_no():
    assert parse_verdict("NO") == "no"
    assert parse_verdict("no") == "no"
    assert parse_verdict("No, the description is inaccurate.") == "no"
    assert parse_verdict("Verdict: no") == "no"


def test_parse_verdict_recognizes_uncertain():
    assert parse_verdict("UNCERTAIN") == "uncertain"
    assert parse_verdict("uncertain") == "uncertain"
    assert parse_verdict("I am uncertain.") == "uncertain"


def test_parse_verdict_defaults_to_uncertain_on_garbage():
    """When the model produces something we cannot parse, treat it
    as uncertain (not as a pass)."""
    assert parse_verdict("") == "uncertain"
    assert parse_verdict("Hmm, well, you see...") == "uncertain"
    assert parse_verdict("123") == "uncertain"


def test_parse_verdict_strips_quotes_and_case():
    assert parse_verdict("'yes'") == "yes"
    assert parse_verdict('"NO"') == "no"


def test_build_verifier_messages_emits_strict_format_request():
    """Verifier prompt must instruct the model to answer with one of
    yes / no / uncertain so parse_verdict can recognise it."""
    messages = build_verifier_messages(
        system_name="X", code="Y", title="Z", candidate="W",
    )
    sys_content = next(
        (m["content"] for m in messages if m["role"] == "system"),
        "",
    )
    low = sys_content.lower()
    assert "yes" in low
    assert "no" in low
    assert "uncertain" in low
