"""Layer B: pure-logic tests for the developer-key system.

Covers free-email-domain detection, prefix derivation from scopes,
and scope-grant checking. These functions don't touch the database;
they're the building blocks the API router and middleware import.
"""

import pytest


# Free-email domain detection


class TestFreeEmailDomain:
    def test_gmail_is_free_email_domain(self):
        from world_of_taxonomy.auth.orgs import is_free_email_domain
        assert is_free_email_domain("alice@gmail.com") is True

    def test_yahoo_is_free_email_domain(self):
        from world_of_taxonomy.auth.orgs import is_free_email_domain
        assert is_free_email_domain("bob@yahoo.com") is True

    def test_acme_is_corporate(self):
        from world_of_taxonomy.auth.orgs import is_free_email_domain
        assert is_free_email_domain("alice@acme.com") is False

    def test_case_insensitive(self):
        from world_of_taxonomy.auth.orgs import is_free_email_domain
        assert is_free_email_domain("Alice@GMAIL.com") is True

    def test_domain_extraction_handles_subdomains(self):
        from world_of_taxonomy.auth.orgs import domain_for_email
        # acme.com signup with a sub-addressing should bucket by acme.com,
        # not by anything past the @. We don't strip subdomains.
        assert domain_for_email("alice@mail.acme.com") == "mail.acme.com"

    def test_domain_extraction_lowercases(self):
        from world_of_taxonomy.auth.orgs import domain_for_email
        assert domain_for_email("Alice@Acme.COM") == "acme.com"

    def test_invalid_email_raises(self):
        from world_of_taxonomy.auth.orgs import domain_for_email
        with pytest.raises(ValueError):
            domain_for_email("noatsign")


# Prefix derivation


class TestPrefixForScopes:
    def test_full_wot_scope_set_yields_wot_prefix(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        # All defined wot:* actions present -> full-product prefix.
        scopes = ["wot:read", "wot:list", "wot:export", "wot:classify", "wot:admin"]
        assert prefix_for_scopes(scopes) == "wot_"

    def test_wot_wildcard_is_full_product(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        assert prefix_for_scopes(["wot:*"]) == "wot_"

    def test_subset_of_wot_yields_restricted_prefix(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        assert prefix_for_scopes(["wot:read"]) == "rwot_"
        assert prefix_for_scopes(["wot:read", "wot:list"]) == "rwot_"

    def test_cross_product_yields_aix_prefix(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        assert prefix_for_scopes(["wot:read", "woo:read"]) == "aix_"

    def test_woo_only_yields_woo_prefix(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        assert prefix_for_scopes(["woo:*"]) == "woo_"

    def test_woo_subset_yields_rwoo_prefix(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        assert prefix_for_scopes(["woo:read"]) == "rwoo_"

    def test_empty_scopes_raises(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        with pytest.raises(ValueError):
            prefix_for_scopes([])

    def test_invalid_scope_format_raises(self):
        from world_of_taxonomy.auth.keys import prefix_for_scopes
        with pytest.raises(ValueError):
            prefix_for_scopes(["wot-read"])  # missing colon


# Scope-grant checking


class TestScopeGranted:
    def test_exact_scope_match_grants(self):
        from world_of_taxonomy.auth.keys import scope_granted
        assert scope_granted(["wot:read"], "wot:read") is True

    def test_exact_scope_mismatch_denies(self):
        from world_of_taxonomy.auth.keys import scope_granted
        assert scope_granted(["wot:read"], "wot:export") is False

    def test_wildcard_grants_any_action_in_product(self):
        from world_of_taxonomy.auth.keys import scope_granted
        assert scope_granted(["wot:*"], "wot:read") is True
        assert scope_granted(["wot:*"], "wot:export") is True
        assert scope_granted(["wot:*"], "wot:admin") is True

    def test_wildcard_does_not_cross_products(self):
        from world_of_taxonomy.auth.keys import scope_granted
        assert scope_granted(["wot:*"], "woo:read") is False

    def test_multiple_scopes_any_match_grants(self):
        from world_of_taxonomy.auth.keys import scope_granted
        granted = ["wot:read", "wot:list", "woo:read"]
        assert scope_granted(granted, "woo:read") is True
        assert scope_granted(granted, "wot:export") is False
