"""Honeypot routes + /.well-known/security.txt.

Attacker scanners aggressively probe for leaked WordPress/phpMyAdmin
admin paths, dotfiles, and exposed .git directories. Serving a deliberate
404 for those paths is both safer and more informative than the default
FastAPI 404 (which is indistinguishable from a typo). Each honeypot hit
is counted so operators can spot scanning spikes in Prometheus.

We also publish a /.well-known/security.txt per RFC 9116 so researchers
know where to report vulnerabilities.
"""

from __future__ import annotations

import logging
import os
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import Counter

_logger = logging.getLogger(__name__)

HONEYPOT_HITS = Counter(
    "wot_honeypot_hits_total",
    "Requests to honeypot paths commonly probed by attacker scanners.",
    ["path"],
)

# Minimal set of the most-probed attacker-recon paths. Kept small so a
# real user who mistypes a URL does not accidentally trigger a honeypot;
# everything else still returns the normal 404.
HONEYPOT_PATHS: List[str] = [
    "/wp-admin",
    "/wp-admin/",
    "/wp-admin/setup-config.php",
    "/wp-login.php",
    "/wordpress",
    "/wordpress/wp-login.php",
    "/xmlrpc.php",
    "/.env",
    "/.env.local",
    "/.env.production",
    "/.git/config",
    "/.git/HEAD",
    "/.DS_Store",
    "/phpmyadmin",
    "/phpmyadmin/",
    "/pma",
    "/admin",
    "/admin.php",
    "/administrator",
    "/config.php",
    "/database.yml",
    "/server-status",
    "/.aws/credentials",
    "/.ssh/id_rsa",
    "/api/.env",
    "/api/v1/.env",
]


def _build_security_txt() -> str:
    """Build RFC 9116 /.well-known/security.txt body from env.

    Falls back to generic placeholders so the route still works before
    operators set SECURITY_CONTACT and SECURITY_ACK_POLICY.
    """
    contact = os.getenv("SECURITY_CONTACT", "https://worldoftaxonomy.com/contact")
    policy = os.getenv(
        "SECURITY_POLICY_URL", "https://worldoftaxonomy.com/security"
    )
    ack = os.getenv("SECURITY_ACK_POLICY", "").strip()
    expires = os.getenv("SECURITY_EXPIRES", "2027-01-01T00:00:00Z")
    preferred = os.getenv("SECURITY_PREFERRED_LANGS", "en")

    lines = [
        f"Contact: {contact}",
        f"Expires: {expires}",
        f"Policy: {policy}",
        f"Preferred-Languages: {preferred}",
    ]
    if ack:
        lines.append(f"Acknowledgments: {ack}")
    return "\n".join(lines) + "\n"


router = APIRouter(tags=["honeypot"])


@router.get("/.well-known/security.txt", include_in_schema=False)
async def security_txt() -> PlainTextResponse:
    return PlainTextResponse(_build_security_txt())


def _honeypot_handler_factory(path: str):
    async def _handler(request: Request) -> Response:
        client = request.client.host if request.client else "?"
        ua = request.headers.get("user-agent", "?")
        HONEYPOT_HITS.labels(path=path).inc()
        _logger.info(
            "honeypot hit path=%s ip=%s ua=%s",
            path,
            client,
            ua,
        )
        # Return a plain 404 so the scanner can not easily distinguish
        # a honeypot from a real dead path. Do not leak server info.
        return Response(status_code=404, content="Not Found")

    return _handler


for _p in HONEYPOT_PATHS:
    router.add_api_route(
        _p,
        _honeypot_handler_factory(_p),
        methods=["GET", "POST", "HEAD"],
        include_in_schema=False,
    )
