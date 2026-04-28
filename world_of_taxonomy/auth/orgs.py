"""Org bucketing for new signups.

Every app_user belongs to exactly one org. The bucketing rule keeps
rate-limit accounting tight: corporate-domain employees share a pool,
free-email signups behave like individual accounts. See
project_org_throttling.md for why per-user limits would be a pricing
loophole.
"""

from __future__ import annotations

from typing import Mapping

from world_of_taxonomy.auth.free_email_domains import FREE_EMAIL_DOMAINS


def domain_for_email(email: str) -> str:
    """Return the lowercase domain after the @, or raise on malformed input."""
    if "@" not in email:
        raise ValueError(f"not an email: {email!r}")
    _, _, domain = email.partition("@")
    if not domain:
        raise ValueError(f"empty domain in email: {email!r}")
    return domain.lower()


def is_free_email_domain(email: str) -> bool:
    """True when the email's domain is in the curated free-provider set."""
    return domain_for_email(email) in FREE_EMAIL_DOMAINS


async def signup_or_link(conn, email: str) -> Mapping:
    """Idempotent signup. Returns the app_user record (id, email, org_id, role).

    If the email already exists, returns it unchanged. Otherwise:
      - free-email domain -> brand-new personal org, user is admin.
      - corporate domain  -> first user creates the org and is admin;
                             subsequent users join as members.
    """
    existing = await conn.fetchrow(
        "SELECT id, email, org_id, role FROM app_user WHERE email = $1", email
    )
    if existing:
        return dict(existing)

    domain = domain_for_email(email)

    if domain in FREE_EMAIL_DOMAINS:
        org_id = await conn.fetchval(
            """INSERT INTO org (name, domain, kind)
               VALUES ($1, NULL, 'personal') RETURNING id""",
            f"personal:{email}",
        )
        role = "admin"
    else:
        org_id = await conn.fetchval(
            "SELECT id FROM org WHERE domain = $1 AND kind = 'corporate'",
            domain,
        )
        if org_id is None:
            org_id = await conn.fetchval(
                """INSERT INTO org (name, domain, kind)
                   VALUES ($1, $1, 'corporate') RETURNING id""",
                domain,
            )
            role = "admin"
        else:
            role = "member"

    row = await conn.fetchrow(
        """INSERT INTO app_user (email, org_id, role)
           VALUES ($1, $2, $3)
           RETURNING id, email, org_id, role""",
        email,
        org_id,
        role,
    )
    return dict(row)
