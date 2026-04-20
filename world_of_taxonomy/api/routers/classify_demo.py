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

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

# RFC 5322-lite: good enough for lead capture without the email-validator dep.
_EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

from world_of_taxonomy.api.deps import get_conn
from world_of_taxonomy.api.routers.classify import partition_matches
from world_of_taxonomy.api.text_guard import TextGuardError, guard
from world_of_taxonomy.classify import classify_text
from world_of_taxonomy.scope import resolve_country_scope
from world_of_taxonomy.system_kind import is_business_classification

router = APIRouter(prefix="/api/v1", tags=["classify"])

# Demo surface is intentionally narrower than the paid endpoint: five
# high-signal systems, three results each, no cross-system crosswalks.
# Pro/Enterprise users get the full surface via POST /api/v1/classify.
DEMO_SYSTEMS = [
    "naics_2022",
    "isic_rev4",
    "sic_1987",
    "nace_rev2",
    "soc_2018",
]
DEMO_RESULTS_PER_SYSTEM = 3


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


async def classify_demo_handler(
    body: ClassifyDemoRequest,
    *,
    conn,
    ip_address: Optional[str],
    user_agent: Optional[str],
    referrer: Optional[str],
) -> dict:
    """Insert a lead row, then run classify limited to the demo surface.

    Split from the route handler so tests can exercise the behaviour
    without spinning up a TestClient.
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

    scope = await resolve_country_scope(conn, body.countries)
    effective_systems = DEMO_SYSTEMS
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
                "upgrade_cta": (
                    "Want all 1000 systems, cross-system crosswalks, and "
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
        effective_systems = sorted(set(DEMO_SYSTEMS) | set(country_business))

    result = await classify_text(
        conn,
        text=clean_text,
        system_ids=effective_systems,
        limit=DEMO_RESULTS_PER_SYSTEM,
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
        "upgrade_cta": (
            "Want all 1000 systems, cross-system crosswalks, and "
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
):
    """Public classify endpoint gated by email only.

    Returns a limited result set (5 systems, 3 results each). Records
    the email as a lead.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    ref = request.headers.get("referer")

    return await classify_demo_handler(
        body,
        conn=conn,
        ip_address=ip,
        user_agent=ua,
        referrer=ref,
    )
