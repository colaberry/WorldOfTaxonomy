"""Tests for resolve_country_scope - country-aware candidate-system partitioning."""

from __future__ import annotations

import asyncio

import pytest

from world_of_taxonomy.scope import resolve_country_scope


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_empty_list_returns_none(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, [])
    assert _run(inner()) is None


def test_none_input_returns_none(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, None)
    assert _run(inner()) is None


def test_single_country_partitions_by_relevance(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, ["US"])
    scope = _run(inner())
    assert scope is not None
    assert "naics_2022" in scope["country_specific_systems"]
    assert "isic_rev4" in scope["global_standard_systems"]
    # Historical is excluded from both buckets
    assert "sic_1987" not in scope["country_specific_systems"]
    assert "sic_1987" not in scope["global_standard_systems"]
    assert scope["countries"] == ["US"]


def test_regional_relevance_treated_as_country_specific(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, ["CA"])
    scope = _run(inner())
    assert "naics_2022" in scope["country_specific_systems"]  # CA marked regional


def test_multiple_countries_union_deduplicated(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, ["US", "DE"])
    scope = _run(inner())
    assert "naics_2022" in scope["country_specific_systems"]
    # isic_rev4 recommended for both; should appear exactly once
    assert scope["global_standard_systems"].count("isic_rev4") == 1
    assert set(scope["countries"]) == {"US", "DE"}


def test_country_codes_normalized_to_upper(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, ["us"])
    scope = _run(inner())
    assert "naics_2022" in scope["country_specific_systems"]


def test_unknown_country_returns_empty_buckets(db_pool):
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, ["XX"])
    scope = _run(inner())
    assert scope is not None
    assert scope["country_specific_systems"] == []
    assert scope["global_standard_systems"] == []


def test_candidate_systems_union_of_both_buckets(db_pool):
    """candidate_systems is the convenience union callers use to scope search."""
    async def inner():
        async with db_pool.acquire() as conn:
            return await resolve_country_scope(conn, ["US"])
    scope = _run(inner())
    assert set(scope["candidate_systems"]) == {"naics_2022", "isic_rev4"}
