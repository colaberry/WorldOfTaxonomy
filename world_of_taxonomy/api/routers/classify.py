"""POST /api/v1/classify - Classify free-text against taxonomy systems."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from world_of_taxonomy.api.deps import get_conn, require_tier

_CLASSIFY_TIERS = frozenset({"pro", "enterprise"})
from world_of_taxonomy.api.text_guard import TextGuardError, guard
from world_of_taxonomy.category import get_category
from world_of_taxonomy.classify import DEFAULT_SYSTEMS, classify_text
from world_of_taxonomy.scope import resolve_country_scope
from world_of_taxonomy.system_kind import is_business_classification

router = APIRouter(prefix="/api/v1", tags=["classify"])


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=500, description="Free-text to classify")
    systems: Optional[list[str]] = Field(
        None,
        description="Optional list of system IDs to search. Default: major systems.",
    )
    countries: Optional[list[str]] = Field(
        None,
        description=(
            "Optional ISO 3166-1 alpha-2 country codes. Scopes candidates to "
            "systems applicable to these countries plus universal recommended "
            "standards (UN/WCO/WHO). Overrides `systems` when set."
        ),
    )
    limit: int = Field(5, ge=1, le=20, description="Max matches per system")


class ClassifyResult(BaseModel):
    code: str
    title: str
    score: float
    level: int
    crosswalk_count: int = Field(
        0,
        description=(
            "Number of equivalence edges originating from this code. The UI "
            "uses this to hide the 'Show crosswalks' affordance for codes "
            "with no outgoing edges."
        ),
    )


class ClassifySystemMatch(BaseModel):
    system_id: str
    system_name: str
    category: str = Field(
        ...,
        description="'domain' for curated WoT taxonomies (system_id starts 'domain_'), 'standard' otherwise.",
    )
    results: list[ClassifyResult]


class CrosswalkEdge(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    match_type: str
    edge_kind: str = Field(
        ...,
        description=(
            "Computed: '{source}_{target}' where each side is 'domain' "
            "if the system_id starts with 'domain_', else 'standard'."
        ),
    )

    model_config = {"populate_by_name": True}


class ScopeInfo(BaseModel):
    countries: list[str]
    country_specific_systems: list[str]
    global_standard_systems: list[str]
    candidate_systems: list[str]


class ClassifyResponse(BaseModel):
    query: str
    domain_matches: list[ClassifySystemMatch] = Field(
        default_factory=list,
        description="Matches from curated WoT Domain taxonomies (plain-language, concrete).",
    )
    standard_matches: list[ClassifySystemMatch] = Field(
        default_factory=list,
        description="Matches from official standard systems (NAICS, ISIC, NACE, SIC, SOC, ...).",
    )
    crosswalks: list[CrosswalkEdge]
    disclaimer: str
    report_issue_url: str
    scope: Optional[ScopeInfo] = Field(
        None,
        description=(
            "Present only when `countries` was supplied. Shows the resolved "
            "country-specific vs global candidate systems the classifier used."
        ),
    )


def partition_matches(matches: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split a flat matches list from classify_text into (domain, standard)."""
    domain, standard = [], []
    for m in matches:
        stamped = dict(m)
        stamped["category"] = get_category(m["system_id"])
        if stamped["category"] == "domain":
            domain.append(stamped)
        else:
            standard.append(stamped)
    return domain, standard


@router.post("/classify", response_model=ClassifyResponse)
async def classify_business(
    body: ClassifyRequest,
    auth: dict = Depends(require_tier("wot:classify", _CLASSIFY_TIERS)),
    conn=Depends(get_conn),
):
    """Classify a business/product/occupation description against taxonomy systems.

    Requires an API key with `wot:classify` scope and a Pro or
    Enterprise org plan. The web `/classify` UI uses a separate
    email-only gate (see project_classify_gate); this endpoint is the
    paid programmatic surface.
    """
    try:
        clean_text, _ = guard(body.text, max_length=500)
    except TextGuardError as exc:
        raise HTTPException(status_code=400, detail=exc.public_message) from exc

    scope = await resolve_country_scope(conn, body.countries)
    effective_systems = body.systems
    if scope is not None:
        # Truly invalid country codes yield no links in either bucket.
        if (
            not scope["country_specific_systems"]
            and not scope["global_standard_systems"]
        ):
            return {
                "query": clean_text,
                "domain_matches": [],
                "standard_matches": [],
                "crosswalks": [],
                "disclaimer": (
                    "No classification systems are linked to the requested countries."
                ),
                "report_issue_url": "https://github.com/colaberryinc/WorldOfTaxonomy/issues",
                "scope": scope,
            }
        # Narrow to the industrial/occupational default set plus the country's
        # own general-purpose business classifications only. Specialty
        # standards (medical, regulatory, trade-tariff, academic) tagged
        # 'official' for a country are NOT business classifications, so they
        # must not be added silently. Caller can still override with an
        # explicit `systems` list.
        base = body.systems if body.systems else list(DEFAULT_SYSTEMS)
        country_business = [
            s for s in scope["country_specific_systems"]
            if is_business_classification(s)
        ]
        effective_systems = sorted(set(base) | set(country_business))

    result = await classify_text(
        conn,
        text=clean_text,
        system_ids=effective_systems,
        limit=body.limit,
    )
    domain, standard = partition_matches(result.get("matches", []))
    return {
        "query": result["query"],
        "domain_matches": domain,
        "standard_matches": standard,
        "crosswalks": result.get("crosswalks", []),
        "disclaimer": result["disclaimer"],
        "report_issue_url": result["report_issue_url"],
        "scope": scope,
    }
