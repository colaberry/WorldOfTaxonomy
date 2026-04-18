"""In-memory failed-authentication tracker.

Brute-force and credential-stuffing defense. We keep a sliding window
of failed login + failed-API-key attempts keyed by IP and by target
email, and reject with HTTP 429 once either bucket exceeds a threshold.

Deliberately in-process and un-persisted: the window is short (default
15 minutes) and a restart clearing the counters is an acceptable
fail-open. For multi-worker deployments, run Redis later; this is a
safe first defense without taking on that dep.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Deque, Dict, Tuple

from prometheus_client import Counter

FAILED_AUTH_COUNT = Counter(
    "wot_failed_auth_total",
    "Failed authentication attempts by surface.",
    ["surface"],  # login_password | api_key | oauth
)

FAILED_AUTH_LOCKOUT = Counter(
    "wot_failed_auth_lockouts_total",
    "Lockout events (429) triggered by too many failed auth attempts.",
    ["bucket"],  # ip | email
)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


_WINDOW_SECONDS = _env_int("AUTH_FAILURE_WINDOW_SECONDS", 900)  # 15 min
_MAX_PER_IP = _env_int("AUTH_FAILURES_PER_IP", 10)
_MAX_PER_EMAIL = _env_int("AUTH_FAILURES_PER_EMAIL", 5)

_lock = threading.Lock()
_ip_history: Dict[str, Deque[float]] = {}
_email_history: Dict[str, Deque[float]] = {}


def _prune(history: Deque[float], now: float) -> None:
    while history and now - history[0] > _WINDOW_SECONDS:
        history.popleft()


def _count_within_window(bucket: Dict[str, Deque[float]], key: str, now: float) -> int:
    history = bucket.get(key)
    if history is None:
        return 0
    _prune(history, now)
    if not history:
        bucket.pop(key, None)
        return 0
    return len(history)


def _get_or_make(bucket: Dict[str, Deque[float]], key: str) -> Deque[float]:
    history = bucket.get(key)
    if history is None:
        history = deque()
        bucket[key] = history
    return history


def check_blocked(ip: str, email: str | None = None) -> Tuple[bool, str | None]:
    """Return (blocked, reason). reason is one of: None, 'ip', 'email'."""
    now = time.time()
    with _lock:
        if _count_within_window(_ip_history, ip, now) >= _MAX_PER_IP:
            return True, "ip"
        if email and _count_within_window(_email_history, email.lower(), now) >= _MAX_PER_EMAIL:
            return True, "email"
    return False, None


def record_failure(ip: str, email: str | None = None, surface: str = "login_password") -> None:
    """Record a single failed auth attempt."""
    now = time.time()
    FAILED_AUTH_COUNT.labels(surface=surface).inc()
    with _lock:
        history = _get_or_make(_ip_history, ip)
        history.append(now)
        _prune(history, now)
        if email:
            email_history = _get_or_make(_email_history, email.lower())
            email_history.append(now)
            _prune(email_history, now)


def record_success(ip: str, email: str | None = None) -> None:
    """Clear counters on a verified successful login so retries after a
    fumbled password do not snowball into a lockout."""
    with _lock:
        _ip_history.pop(ip, None)
        if email:
            _email_history.pop(email.lower(), None)


def mark_lockout(bucket: str) -> None:
    FAILED_AUTH_LOCKOUT.labels(bucket=bucket).inc()


def reset_for_tests() -> None:
    """Test helper: wipe in-memory state."""
    with _lock:
        _ip_history.clear()
        _email_history.clear()
