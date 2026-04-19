"""Tests for the domain vs standard category helper."""

import pytest

from world_of_taxonomy.category import (
    CATEGORY_DOMAIN,
    CATEGORY_STANDARD,
    DOMAIN_PREFIX,
    EDGE_DOMAIN_DOMAIN,
    EDGE_DOMAIN_STANDARD,
    EDGE_STANDARD_DOMAIN,
    EDGE_STANDARD_STANDARD,
    compute_edge_kind,
    get_category,
    is_domain,
)


@pytest.mark.parametrize(
    "system_id,expected",
    [
        ("domain_truck_freight", CATEGORY_DOMAIN),
        ("domain_medical_device", CATEGORY_DOMAIN),
        ("naics_2022", CATEGORY_STANDARD),
        ("isic_rev4", CATEGORY_STANDARD),
        ("nace_rev2", CATEGORY_STANDARD),
        ("soc_2018", CATEGORY_STANDARD),
        ("", CATEGORY_STANDARD),
    ],
)
def test_get_category(system_id, expected):
    assert get_category(system_id) == expected


def test_is_domain():
    assert is_domain("domain_truck_freight") is True
    assert is_domain("naics_2022") is False


def test_domain_prefix_constant():
    assert DOMAIN_PREFIX == "domain_"


@pytest.mark.parametrize(
    "source,target,expected",
    [
        ("naics_2022", "isic_rev4", EDGE_STANDARD_STANDARD),
        ("isic_rev4", "naics_2022", EDGE_STANDARD_STANDARD),
        ("naics_2022", "domain_truck_freight", EDGE_STANDARD_DOMAIN),
        ("domain_truck_freight", "naics_2022", EDGE_DOMAIN_STANDARD),
        ("domain_truck_freight", "domain_ag_crop", EDGE_DOMAIN_DOMAIN),
    ],
)
def test_compute_edge_kind(source, target, expected):
    assert compute_edge_kind(source, target) == expected


def test_edge_kind_constants():
    assert EDGE_STANDARD_STANDARD == "standard_standard"
    assert EDGE_STANDARD_DOMAIN == "standard_domain"
    assert EDGE_DOMAIN_STANDARD == "domain_standard"
    assert EDGE_DOMAIN_DOMAIN == "domain_domain"


def test_get_systems_populates_category(db_pool):
    """Every system returned by the query layer has a populated category."""
    import asyncio
    from world_of_taxonomy.query.browse import get_systems

    async def go():
        async with db_pool.acquire() as conn:
            return await get_systems(conn)

    systems = asyncio.get_event_loop().run_until_complete(go())

    assert len(systems) > 0
    for sys in systems:
        assert sys.category in (CATEGORY_DOMAIN, CATEGORY_STANDARD)
        if sys.id.startswith(DOMAIN_PREFIX):
            assert sys.category == CATEGORY_DOMAIN
        else:
            assert sys.category == CATEGORY_STANDARD
