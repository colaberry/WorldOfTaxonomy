"""Layer E: org-level rate limiting.

The pricing-model loophole this closes: if rate limits keyed on
user_id, a company could spin up N personal accounts to multiply the
free-tier ceiling. With org-level keying, every employee at the same
corporate domain shares one pool.

These tests assert the keying behavior of the in-process token
bucket; the middleware integration is asserted in
test_api_developers.py via the 429 contract.
"""


class TestRateLimitBucketKey:
    def test_bucket_key_uses_org_id_for_authenticated_users(self):
        from world_of_taxonomy.api.middleware import bucket_key_for
        # Two users at acme.com share the same org_id -> same bucket.
        u1 = {"id": "u-1", "org_id": "org-acme", "tier": "free"}
        u2 = {"id": "u-2", "org_id": "org-acme", "tier": "free"}
        assert bucket_key_for(u1) == bucket_key_for(u2)
        assert "org-acme" in bucket_key_for(u1)

    def test_bucket_key_differs_across_orgs(self):
        from world_of_taxonomy.api.middleware import bucket_key_for
        u1 = {"id": "u-1", "org_id": "org-acme", "tier": "free"}
        u2 = {"id": "u-2", "org_id": "org-other", "tier": "free"}
        assert bucket_key_for(u1) != bucket_key_for(u2)

    def test_bucket_key_for_anonymous_uses_ip(self):
        from world_of_taxonomy.api.middleware import bucket_key_for
        key = bucket_key_for(None, ip="203.0.113.5")
        assert key == "ip:203.0.113.5"


class TestPoolSizing:
    def test_org_pool_for_free_tier_is_1000_per_minute(self):
        from world_of_taxonomy.api.middleware import org_pool_per_minute
        assert org_pool_per_minute({"tier": "free", "rate_limit_pool_per_minute": 1000}) == 1000

    def test_org_pool_for_pro_tier_is_10000_per_minute(self):
        from world_of_taxonomy.api.middleware import org_pool_per_minute
        assert org_pool_per_minute(
            {"tier": "pro", "rate_limit_pool_per_minute": 10000}
        ) == 10000

    def test_anon_pool_is_30_per_minute(self):
        from world_of_taxonomy.api.middleware import org_pool_per_minute
        assert org_pool_per_minute(None) == 30
