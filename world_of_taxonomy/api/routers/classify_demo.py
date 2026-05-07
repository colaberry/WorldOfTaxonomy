"""POST /api/v1/classify/demo - Public email-gated classify endpoint.

This is the web-facing classify surface. Anonymous users submit an
email plus a business description; we persist the email as a lead and
return a limited classify result set. The full /api/v1/classify
endpoint remains Pro-tier gated.

The gate will migrate to Zitadel hosted login once the central IdP is
provisioned; until then, an email-only gate is the stopgap.
"""

from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

# RFC 5322-lite: good enough for lead capture without the email-validator dep.
_EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

from world_of_taxonomy.api.deps import get_conn
from world_of_taxonomy.api.rate_guard import (
    check_classify_lead_budget,
    check_per_ip_rate,
)
from world_of_taxonomy.api.routers.classify import partition_matches
from world_of_taxonomy.api.text_guard import TextGuardError, guard
from world_of_taxonomy.classify import classify_text
from world_of_taxonomy.scope import resolve_country_scope
from world_of_taxonomy.system_kind import is_business_classification

router = APIRouter(prefix="/api/v1", tags=["classify"])

# Demo surface is tiered. Anonymous users get 5 high-signal industry
# / occupation systems, 3 results each. Logged-in users (those who
# completed the magic-link flow and hold a valid `dev_session` cookie)
# get a wider lens: 5 additional global systems covering trade,
# products, health, and international occupations, plus 5 results per
# system. Pro / Enterprise users get the full surface via the paid
# POST /api/v1/classify, which also returns curated Domain taxonomies.
DEMO_SYSTEMS = [
    "naics_2022",
    "isic_rev4",
    "sic_1987",
    "nace_rev2",
    "soc_2018",
]
DEMO_RESULTS_PER_SYSTEM = 3

# Logged-in tier: anon set + 5 globally authoritative cross-domain
# standards. One per major dimension to maximize breadth without
# overlapping the anon set:
#   hs_2022     - trade / customs (WCO global)
#   cpc_v21     - products / statistical (UN global)
#   unspsc_v24  - procurement (GS1 US global)
#   icd_11      - health (WHO global)
#   isco_08     - international occupations (ILO global)
LOGGED_IN_SYSTEMS = DEMO_SYSTEMS + [
    "hs_2022",
    "cpc_v21",
    "unspsc_v24",
    "icd_11",
    "isco_08",
]
LOGGED_IN_RESULTS_PER_SYSTEM = 5


class ClassifyDemoRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320, description="Lead email for follow-up")
    text: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Business/product/occupation description",
    )
    countries: Optional[list[str]] = Field(
        None,
        description=(
            "Optional ISO 3166-1 alpha-2 country codes. When supplied, classify "
            "against the systems applicable to those countries (plus globally "
            "recommended standards like ISIC Rev 4) instead of the default demo set."
        ),
    )

    @field_validator("email")
    @classmethod
    def _email_is_plausible(cls, v: str) -> str:
        if not _EMAIL_RX.match(v):
            raise ValueError("email must be a valid address")
        return v.strip().lower()


class ClassifyDemoResponse(BaseModel):
    query: str
    domain_matches: list = Field(
        default_factory=list,
        description="Matches from curated WoT Domain taxonomies (system_id starts 'domain_').",
    )
    standard_matches: list = Field(
        default_factory=list,
        description="Matches from official standard systems (NAICS, ISIC, NACE, SIC, SOC, ...).",
    )
    disclaimer: str
    report_issue_url: str
    demo: bool = True
    is_logged_in: bool = Field(
        False,
        description=(
            "True when the request carried a valid `dev_session` cookie. "
            "Logged-in callers get the broader 10-system / 5-result-per-system "
            "tier; anonymous callers get the 5-system / 3-result tier."
        ),
    )
    upgrade_cta: str
    compound: bool = False
    atoms: Optional[list] = None
    hero: Optional[dict] = None
    cta: Optional[dict] = None
    llm_used: bool = False
    llm_keywords: list = []
    scope: Optional[dict] = Field(
        None,
        description=(
            "Present only when `countries` was supplied. Mirrors the shape "
            "returned by the paid /classify endpoint."
        ),
    )


def _is_valid_dev_session(token: Optional[str]) -> bool:
    """Soft session check: True when the cookie decodes to a valid
    dev_session JWT. No DB lookup, no 401 raise. Used to choose the
    classify tier (anon vs logged-in) without changing the email-gate
    contract.
    """
    if not token:
        return False
    # Local import: keeps the developers router import graph contained
    # and avoids the circular-import risk from pulling
    # `_decode_dev_session` at module-load time.
    from world_of_taxonomy.api.routers.developers import _decode_dev_session

    try:
        _decode_dev_session(token)
    except HTTPException:
        return False
    return True


async def classify_demo_handler(
    body: ClassifyDemoRequest,
    *,
    conn,
    ip_address: Optional[str],
    user_agent: Optional[str],
    referrer: Optional[str],
    is_logged_in: bool = False,
) -> dict:
    """Insert a lead row, then run classify limited to the demo surface.

    Split from the route handler so tests can exercise the behaviour
    without spinning up a TestClient.

    `is_logged_in` selects the result tier: when True (caller had a
    valid `dev_session` cookie), the broader 10-system / 5-result tier
    is used; otherwise the 5-system / 3-result anonymous tier.
    """
    try:
        clean_text, _ = guard(body.text, max_length=500)
    except TextGuardError as exc:
        raise HTTPException(status_code=400, detail=exc.public_message) from exc

    await conn.execute(
        """
        INSERT INTO classify_lead (email, query_text, ip_address, user_agent, referrer)
        VALUES ($1, $2, $3, $4, $5)
        """,
        body.email,
        clean_text,
        ip_address,
        user_agent,
        referrer,
    )

    # Pick tier based on auth state. Logged-in callers get the broader
    # 10-system surface; anonymous callers get the 5-system anon surface.
    base_systems = LOGGED_IN_SYSTEMS if is_logged_in else DEMO_SYSTEMS
    results_per_system = (
        LOGGED_IN_RESULTS_PER_SYSTEM if is_logged_in else DEMO_RESULTS_PER_SYSTEM
    )

    scope = await resolve_country_scope(conn, body.countries)
    effective_systems = base_systems
    if scope is not None:
        # Truly invalid country codes: no country-specific systems AND no
        # globally-recommended standards link to them. Return empty.
        if (
            not scope["country_specific_systems"]
            and not scope["global_standard_systems"]
        ):
            return {
                "query": clean_text,
                "domain_matches": [],
                "standard_matches": [],
                "disclaimer": (
                    "No classification systems are linked to the requested countries."
                ),
                "report_issue_url": "https://github.com/colaberryinc/WorldOfTaxonomy/issues",
                "demo": True,
                "is_logged_in": is_logged_in,
                "upgrade_cta": (
                    "Want all 1000+ systems, cross-system crosswalks, and "
                    "programmatic API access? Upgrade to Pro at /pricing."
                ),
                "compound": False,
                "atoms": None,
                "hero": None,
                "cta": None,
                "llm_used": False,
                "llm_keywords": [],
                "scope": scope,
            }
        # Narrow the scope: demo default set (industrial/occupational standards)
        # PLUS the country's own general-purpose business classifications
        # (NAICS/ISIC/NACE/SIC family + SOC/ISCO family). Country-specific
        # medical, regulatory, trade-tariff, and academic systems are tagged
        # 'official' in country_system_link but are NOT business
        # classifications, so they must not expand an industry query's scope.
        country_business = [
            s for s in scope["country_specific_systems"]
            if is_business_classification(s)
        ]
        effective_systems = sorted(set(base_systems) | set(country_business))

    result = await classify_text(
        conn,
        text=clean_text,
        system_ids=effective_systems,
        limit=results_per_system,
        # Domain taxonomies (`domain_*`) are a paid-tier differentiator.
        # The /classify page promises "5 major systems ... full result set
        # on the paid API"; keeping domains out of the demo enforces that
        # contract and saves a per-call DB round-trip.
        include_domains=False,
    )

    domain, standard = partition_matches(result.get("matches", []))

    # Hero atom (compound path) is pre-split so the client renders two
    # sections directly, no re-partitioning needed.
    hero = result.get("hero")
    hero_payload = None
    if hero is not None:
        h_domain, h_standard = partition_matches(hero.get("matches", []))
        hero_payload = {
            "phrase": hero["phrase"],
            "domain_matches": h_domain,
            "standard_matches": h_standard,
        }

    # Each atom gets the same split.
    atoms_payload = None
    if result.get("atoms"):
        atoms_payload = []
        for atom in result["atoms"]:
            a_domain, a_standard = partition_matches(atom.get("matches", []))
            atoms_payload.append({
                "phrase": atom["phrase"],
                "domain_matches": a_domain,
                "standard_matches": a_standard,
            })

    return {
        "query": result["query"],
        "domain_matches": domain,
        "standard_matches": standard,
        "disclaimer": result["disclaimer"],
        "report_issue_url": result["report_issue_url"],
        "demo": True,
        "is_logged_in": is_logged_in,
        "upgrade_cta": (
            "Want all 1000+ systems, cross-system crosswalks, and "
            "programmatic API access? Upgrade to Pro at /pricing."
        ),
        "compound": result.get("compound", False),
        "atoms": atoms_payload,
        "hero": hero_payload,
        "cta": result.get("cta"),
        "llm_used": result.get("llm_used", False),
        "llm_keywords": result.get("llm_keywords", []),
        "scope": scope,
    }


@router.post("/classify/demo", response_model=ClassifyDemoResponse)
async def classify_demo(
    body: ClassifyDemoRequest,
    request: Request,
    conn=Depends(get_conn),
    dev_session: Optional[str] = Cookie(default=None),
):
    """Public classify endpoint gated by email only.

    Anonymous callers get the 5-system / 3-result anon tier. Callers
    with a valid `dev_session` cookie (i.e., they completed the
    magic-link sign-in) get the broader 10-system / 5-result tier.
    Records the email as a lead either way.

    Per-IP rate guard: 20/hour. The cap is well above any legitimate
    interactive use (a user trying ~5 prompts in a session) but tight
    enough to deter farming, since each call is LLM-backed and each
    INSERT into classify_lead is downstream lead-pipeline noise.

    Global classify-lead budget: 500/hour, env-tunable via
    CLASSIFY_LEAD_BUDGET_PER_HOUR. The per-IP cap above bounds a
    single source; this DB-backed counter catches distributed botnets
    rotating IPs (each making 1-2 calls, slipping under the per-IP
    cap) and acts as a hard ceiling on LLM cost.
    """
    check_per_ip_rate("classify_demo", request, max_per_window=20)
    await check_classify_lead_budget(conn)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    ref = request.headers.get("referer")

    return await classify_demo_handler(
        body,
        conn=conn,
        ip_address=ip,
        user_agent=ua,
        referrer=ref,
        is_logged_in=_is_valid_dev_session(dev_session),
    )
