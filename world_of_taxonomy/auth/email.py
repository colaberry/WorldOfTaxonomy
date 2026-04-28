"""Email delivery for magic-link sign-in and key-issuance receipts.

Uses Resend by default. The `EmailClient` protocol is the only thing
the rest of the codebase imports, so swapping to Postmark / SES later
is a one-file change.

When `RESEND_API_KEY` is not set, `default_client()` returns a
`NoopEmailClient` that logs a warning and silently drops the message.
This keeps signup endpoints from 500ing on infrastructure problems
the user cannot fix; the magic link is also returned in the API
response so local development works without an email account.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol

logger = logging.getLogger("wot.auth.email")


class EmailClient(Protocol):
    def send(self, *, to: str, subject: str, html: str, text: str) -> None: ...


class NoopEmailClient:
    """Drops messages with a warning. Used when RESEND_API_KEY is missing."""

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        logger.warning(
            "email_dropped: RESEND_API_KEY not set; would have sent %r to %s",
            subject, to,
        )


class ResendClient:
    """Thin wrapper around the Resend HTTP API.

    No SDK dependency: a single POST keeps the import surface tiny
    and the test mock obvious.
    """

    def __init__(self, api_key: str, sender: str = "noreply@aixcelerator.ai"):
        self._api_key = api_key
        self._sender = sender

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        import urllib.request
        import json

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps({
                "from": self._sender,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status >= 400:
                    logger.error(
                        "resend_send_failed: status=%s body=%s",
                        response.status, response.read()[:500],
                    )
        except Exception as exc:
            logger.exception("resend_send_exception: %s", exc)


def default_client() -> EmailClient:
    """Return the production client when configured, otherwise a no-op."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        return NoopEmailClient()
    sender = os.environ.get("RESEND_SENDER", "noreply@aixcelerator.ai")
    return ResendClient(api_key=api_key, sender=sender)


# Templates


def _login_email_text(magic_link_url: str) -> str:
    return (
        "Sign in to WorldOfTaxonomy\n\n"
        f"Click here to sign in: {magic_link_url}\n\n"
        "This link expires in 15 minutes and works once. If you did not\n"
        "request it, ignore this email.\n"
    )


def _login_email_html(magic_link_url: str) -> str:
    return (
        '<div style="font-family:system-ui,sans-serif;font-size:15px">'
        "<h2>Sign in to WorldOfTaxonomy</h2>"
        f'<p><a href="{magic_link_url}">Click here to sign in</a></p>'
        f'<p style="color:#666;font-size:13px">Or copy this link:<br>{magic_link_url}</p>'
        '<p style="color:#999;font-size:13px">'
        "This link expires in 15 minutes and works once. If you did not "
        "request it, ignore this email."
        "</p>"
        "</div>"
    )


def send_login_email(*, client: EmailClient, to: str, magic_link_url: str) -> None:
    """Send the magic-link sign-in email."""
    client.send(
        to=to,
        subject="Sign in to WorldOfTaxonomy",
        text=_login_email_text(magic_link_url),
        html=_login_email_html(magic_link_url),
    )


def send_key_issued_email(
    *, client: EmailClient, to: str, key_prefix: str, dashboard_url: str,
) -> None:
    """Tell the user a new API key was created. The key itself is NOT
    in the email - it was shown once in the UI; this is a receipt."""
    body = (
        f"A new API key (prefix {key_prefix}...) was created on your "
        f"WorldOfTaxonomy account.\n\n"
        f"Manage keys: {dashboard_url}\n\n"
        "If you did not create this key, revoke it immediately and "
        "contact support."
    )
    client.send(
        to=to,
        subject="New WorldOfTaxonomy API key created",
        text=body,
        html=f"<pre>{body}</pre>",
    )


def send_key_revoked_email(
    *, client: EmailClient, to: str, key_prefix: str, dashboard_url: str,
) -> None:
    """Receipt for a revoked key."""
    body = (
        f"API key with prefix {key_prefix}... was revoked.\n\n"
        f"Manage keys: {dashboard_url}\n"
    )
    client.send(
        to=to,
        subject="WorldOfTaxonomy API key revoked",
        text=body,
        html=f"<pre>{body}</pre>",
    )
