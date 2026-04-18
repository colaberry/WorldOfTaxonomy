"""Tests for the failed-auth sliding-window tracker."""

import pytest

from world_of_taxonomy.api import failed_auth


@pytest.fixture(autouse=True)
def _reset():
    failed_auth.reset_for_tests()
    yield
    failed_auth.reset_for_tests()


def test_no_failures_is_not_blocked():
    blocked, reason = failed_auth.check_blocked("1.2.3.4", "a@b.co")
    assert blocked is False
    assert reason is None


def test_ip_lockout_after_threshold(monkeypatch):
    monkeypatch.setattr(failed_auth, "_MAX_PER_IP", 3, raising=False)
    monkeypatch.setattr(failed_auth, "_MAX_PER_EMAIL", 99, raising=False)
    for i in range(3):
        failed_auth.record_failure("9.9.9.9", f"u{i}@x.co")
    blocked, reason = failed_auth.check_blocked("9.9.9.9", "new@x.co")
    assert blocked is True
    assert reason == "ip"


def test_email_lockout_after_threshold(monkeypatch):
    monkeypatch.setattr(failed_auth, "_MAX_PER_IP", 99, raising=False)
    monkeypatch.setattr(failed_auth, "_MAX_PER_EMAIL", 2, raising=False)
    failed_auth.record_failure("1.1.1.1", "target@x.co")
    failed_auth.record_failure("2.2.2.2", "target@x.co")
    blocked, reason = failed_auth.check_blocked("3.3.3.3", "target@x.co")
    assert blocked is True
    assert reason == "email"


def test_success_clears_ip_and_email():
    for i in range(3):
        failed_auth.record_failure("5.5.5.5", "x@y.co")
    failed_auth.record_success("5.5.5.5", "x@y.co")
    blocked, _ = failed_auth.check_blocked("5.5.5.5", "x@y.co")
    assert blocked is False


def test_old_entries_fall_out_of_window(monkeypatch):
    monkeypatch.setattr(failed_auth, "_WINDOW_SECONDS", 1, raising=False)
    monkeypatch.setattr(failed_auth, "_MAX_PER_IP", 2, raising=False)
    failed_auth.record_failure("8.8.8.8", "old@x.co")
    failed_auth.record_failure("8.8.8.8", "old@x.co")
    import time
    time.sleep(1.1)
    blocked, _ = failed_auth.check_blocked("8.8.8.8", "old@x.co")
    assert blocked is False
