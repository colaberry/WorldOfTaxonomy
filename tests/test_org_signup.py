"""Layer B (DB): signup_or_link bucketing into orgs.

Asserts the rules from project_org_throttling.md:
  - Free-email signup -> per-email personal org (kind='personal').
  - Corporate-domain signup -> shared org by domain (kind='corporate').
  - First user at a corporate domain becomes admin; subsequent users
    join as members.
"""

import asyncio


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSignupOrLink:
    def test_gmail_signup_creates_personal_org(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.orgs import signup_or_link
            async with db_pool.acquire() as conn:
                user = await signup_or_link(conn, "alice@gmail.com")
                assert user["email"] == "alice@gmail.com"
                org = await conn.fetchrow(
                    "SELECT kind, domain FROM org WHERE id = $1", user["org_id"]
                )
                assert org["kind"] == "personal"
                # personal orgs do not claim a domain.
                assert org["domain"] is None
                assert user["role"] == "admin"
        _run(_test())

    def test_two_gmail_signups_get_independent_personal_orgs(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.orgs import signup_or_link
            async with db_pool.acquire() as conn:
                u1 = await signup_or_link(conn, "alice@gmail.com")
                u2 = await signup_or_link(conn, "bob@gmail.com")
                assert u1["org_id"] != u2["org_id"]
        _run(_test())

    def test_first_acme_signup_creates_corp_org_as_admin(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.orgs import signup_or_link
            async with db_pool.acquire() as conn:
                user = await signup_or_link(conn, "alice@acme.com")
                org = await conn.fetchrow(
                    "SELECT kind, domain FROM org WHERE id = $1", user["org_id"]
                )
                assert org["kind"] == "corporate"
                assert org["domain"] == "acme.com"
                assert user["role"] == "admin"
        _run(_test())

    def test_second_acme_signup_joins_existing_org_as_member(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.orgs import signup_or_link
            async with db_pool.acquire() as conn:
                first = await signup_or_link(conn, "alice@acme.com")
                second = await signup_or_link(conn, "bob@acme.com")
                assert first["org_id"] == second["org_id"]
                assert second["role"] == "member"
        _run(_test())

    def test_signup_or_link_existing_email_is_idempotent(self, db_pool):
        async def _test():
            from world_of_taxonomy.auth.orgs import signup_or_link
            async with db_pool.acquire() as conn:
                first = await signup_or_link(conn, "alice@acme.com")
                again = await signup_or_link(conn, "alice@acme.com")
                assert first["id"] == again["id"]
                assert first["org_id"] == again["org_id"]
        _run(_test())
