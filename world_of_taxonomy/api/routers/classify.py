"""POST /api/v1/classify - Classify free-text against taxonomy systems."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from world_of_taxonomy.api.deps import get_conn, get_current_user
from world_of_taxonomy.api.text_guard import TextGuardError, guard
from world_of_taxonomy.category import get_category
from world_of_taxonomy.classify import classify_text

router = APIRouter(prefix="/api/v1", tags=["classify"])


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=500, description="Free-text to classify")
    systems: Optional[list[str]] = Field(
        None,
        description="Optional list of system IDs to search. Default: major systems.",
    )
    limit: int = Field(5, ge=1, le=20, description="Max matches per system")


class ClassifyResult(BaseModel):
    code: str
    title: str
    score: float
    level: int


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
    user: dict = Depends(get_current_user),
    conn=Depends(get_conn),
):
    """Classify a business/product/occupation description against taxonomy systems.

    Requires Pro or Enterprise tier.
    """
    if user.get("tier") not in ("pro", "enterprise"):
        raise HTTPException(
            status_code=403,
            detail=(
                "The classify endpoint requires a Pro or Enterprise tier account. "
                "See /developers for pricing information."
            ),
        )

    try:
        clean_text, _ = guard(body.text, max_length=500)
    except TextGuardError as exc:
        raise HTTPException(status_code=400, detail=exc.public_message) from exc

    result = await classify_text(
        conn,
        text=clean_text,
        system_ids=body.systems,
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
    }
