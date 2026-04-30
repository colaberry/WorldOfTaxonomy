"""Adversarial tests for the per-IP rate guard.

These were written AFTER the original implementation as a partial
substitute for the missed TDD red phase on PRs #140 / #144 / #145 /
#147. They try to break the guard in ways the original tests do not
cover:

  - IPv6 with brackets and ports (does the bucket key vary on port?)
  - X-Forwarded-For with empty first hop (where do "unknown" callers
    bucket together?)
  - X-Forwarded-For with whitespace-only entry (same)
  - Header value with trailing/leading whitespace around IPs
  - window_seconds == 0 and < 0 edge cases
  - max_per_window negative
  - Distinct deque buckets do not bleed between endpoints
  - The CSRF double-submit check accepts an empty header equal to an
    empty cookie (it must not - the not-empty guard runs FIRST)

Each test is named after the attack scenario it tries to exploit so a
future reader sees what's being defended against.

A test that passes here documents that the guard already handles the
case. A test that fails reveals a real bug that needs a fix.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from world_of_taxonomy.api.rate_guard import (
    _client_ip,
    _reset_for_tests,
    check_per_ip_rate,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _Stub:
    """Minimal stand-in for fastapi.Request that lets us inject the
    socket peer + headers verbatim, including malformed values."""

    def __init__(self, *, ip=None, xff=None, extra_headers=None):
        self.client = type("C", (), {"host": ip})() if ip is not None else None
        self.headers = {}
        if xff is not None:
            self.headers["x-forwarded-for"] = xff
        if extra_headers:
            self.headers.update(extra_headers)
        self.cookies = {}


# ----- _client_ip robustness ----------------------------------------------


class TestClientIPEdgeCases:
    def test_xff_with_empty_first_hop_falls_back_to_unknown(self):
        # `, 10.0.0.1` -> first entry is empty after split+strip.
        assert _client_ip(_Stub(xff=", 10.0.0.1")) == "unknown"

    def test_xff_with_whitespace_only_first_hop_falls_back_to_unknown(self):
        assert _client_ip(_Stub(xff="   , 10.0.0.1")) == "unknown"

    def test_xff_with_only_whitespace_falls_back_to_unknown(self):
        assert _client_ip(_Stub(xff="   ")) == "unknown"

    def test_xff_strips_whitespace_around_first_entry(self):
        # The CDN may leave a space after the IP, leading or trailing.
        assert _client_ip(_Stub(xff="  1.2.3.4  , 10.0.0.1")) == "1.2.3.4"

    def test_xff_takes_priority_over_socket_peer(self):
        # Both set: the LB-rewritten XFF should win, not the socket.
        assert _client_ip(_Stub(ip="10.0.0.1", xff="203.0.113.5")) == "203.0.113.5"

    def test_no_xff_no_socket_returns_unknown(self):
        assert _client_ip(_Stub()) == "unknown"

    def test_ipv6_with_port_keeps_port_in_bucket_key(self):
        """IPv6 addresses in X-Forwarded-For sometimes arrive with a
        port (e.g. `[::1]:1234`). The current implementation uses the
        whole string as the bucket key, so an attacker rotating ports
        gets distinct buckets. This test documents the behaviour - if
        we ever strip the port, this assertion is the canary."""
        a = _client_ip(_Stub(xff="[::1]:1234"))
        b = _client_ip(_Stub(xff="[::1]:5678"))
        # Today: distinct keys (port-aware). If we ever normalize, both
        # should equal "[::1]" and this test will need flipping.
        assert a == "[::1]:1234"
        assert b == "[::1]:5678"
        assert a != b

    def test_socket_with_ipv6_brackets(self):
        # Sockets normally don't include brackets; whatever the client
        # claims is what we get. Not a bug, just a test of fidelity.
        assert _client_ip(_Stub(ip="::1")) == "::1"


# ----- check_per_ip_rate window/cap edge cases ----------------------------


class TestRateGuardEdgeCases:
    def setup_method(self):
        _reset_for_tests()

    def test_zero_window_seconds_does_not_throw_but_disables_cap(self):
        """window_seconds=0 means cutoff == now, so EVERY past entry
        evicts immediately. The bucket is always empty, so no 429 is
        ever raised. This is silent behaviour - we want to know if it
        ever changes."""
        req = _Stub(ip="1.2.3.4")
        for _ in range(50):
            check_per_ip_rate("z", req, max_per_window=3, window_seconds=0)

    def test_negative_window_seconds_silently_disables(self):
        """window_seconds<0 means cutoff > now, so all entries are
        always 'older than the window' and evict. Bucket stays empty.
        Footgun if a caller passes window_seconds=-1 by accident."""
        req = _Stub(ip="1.2.3.4")
        for _ in range(50):
            check_per_ip_rate("n", req, max_per_window=3, window_seconds=-5)

    def test_negative_max_per_window_disables(self):
        req = _Stub(ip="1.2.3.4")
        for _ in range(50):
            check_per_ip_rate("neg", req, max_per_window=-1)

    def test_unknown_bucket_can_be_DoSd_by_one_attacker(self):
        """All callers without a usable IP land in bucket 'unknown'.
        One attacker can fill that bucket and a legitimate caller
        whose IP could not be determined is then locked out. Documents
        the current behaviour - we'd need IP enrichment (e.g. from
        Cloudflare's CF-Connecting-IP header) to fix it."""
        attacker = _Stub(xff="")  # falls back to 'unknown'
        for _ in range(5):
            check_per_ip_rate("dos", attacker, max_per_window=5)
        # A second 'unknown' caller is now blocked from this endpoint.
        with pytest.raises(HTTPException) as exc:
            check_per_ip_rate("dos", _Stub(xff=""), max_per_window=5)
        assert exc.value.status_code == 429

    def test_distinct_endpoints_with_same_ip_are_independent(self):
        """A flood on /signup must not lock the same IP out of /search."""
        req = _Stub(ip="1.2.3.4")
        for _ in range(5):
            check_per_ip_rate("signup", req, max_per_window=5)
        # Same IP, fresh endpoint - should pass.
        check_per_ip_rate("search", req, max_per_window=5)

    def test_exactly_at_cap_passes_then_next_raises(self):
        """Verify the boundary: with cap=N, the Nth call passes and
        the (N+1)th raises. The original tests cover this; included
        here so the adversarial file is self-contained."""
        req = _Stub(ip="1.2.3.4")
        for _ in range(5):
            check_per_ip_rate("e", req, max_per_window=5)
        with pytest.raises(HTTPException):
            check_per_ip_rate("e", req, max_per_window=5)


# ----- CSRF double-submit edge cases --------------------------------------


try:
    from world_of_taxonomy.api.routers.developers import _check_csrf
    _CSRF_AVAILABLE = True
except ImportError:
    _CSRF_AVAILABLE = False


@pytest.mark.skipif(
    not _CSRF_AVAILABLE,
    reason="_check_csrf lands on PR #148 (phase6/ops-hardening); these tests activate after merge",
)
class TestCsrfEdgeCases:
    """The _check_csrf helper in developers.py uses the pattern:

        if not cookie or not header or not hmac.compare_digest(cookie, header):
            raise 403

    Empty-string cookie + empty-string header would be equal under
    compare_digest, but the not-empty short-circuit MUST run first so
    a missing cookie cannot bypass the check by also being missing in
    the header.
    """

    def _stub(self, *, csrf_cookie=None, csrf_header=None):
        class _Client:
            host = "1.2.3.4"

        class _Req:
            client = _Client()
            cookies = {}
            headers = {}

        req = _Req()
        if csrf_cookie is not None:
            req.cookies["wot_csrf"] = csrf_cookie
        if csrf_header is not None:
            req.headers["x-csrf-token"] = csrf_header
        return req

    def test_empty_cookie_and_empty_header_must_be_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _check_csrf(self._stub(csrf_cookie="", csrf_header=""))
        assert exc.value.status_code == 403
        assert exc.value.detail["error"] == "csrf_token_mismatch"

    def test_present_cookie_missing_header_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _check_csrf(self._stub(csrf_cookie="abc"))
        assert exc.value.status_code == 403

    def test_missing_cookie_present_header_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _check_csrf(self._stub(csrf_header="abc"))
        assert exc.value.status_code == 403

    def test_different_lengths_rejected_without_crash(self):
        """compare_digest can still operate on different lengths - it
        returns False but is not constant-time across lengths. That's
        OK for a 32-hex token; verify it does not crash."""
        with pytest.raises(HTTPException) as exc:
            _check_csrf(self._stub(csrf_cookie="aaaa", csrf_header="aaaab"))
        assert exc.value.status_code == 403

    def test_matching_tokens_pass(self):
        # Should NOT raise.
        _check_csrf(self._stub(csrf_cookie="deadbeef", csrf_header="deadbeef"))
