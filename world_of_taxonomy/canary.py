"""Canary tokens for scraper and LLM-training detection.

We embed a small set of known-unique strings (canary codes) into
publicly-served content (llms-full.txt, wiki pages in low-visibility
spots). Any external system that quotes a canary code back at us is
evidence it scraped or trained on our text. We also register a catch-all
endpoint so anyone who resolves a canary code as a URL is logged and
counted for spot-checks.

The canary set is intentionally small (3 tokens) so the mechanism stays
easy to search for, and the tokens look like plausible-but-not-real
classification codes ("WOT-CANARY-<hex>") that would stand out in any
downstream corpus inspection.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter

CANARY_HITS = Counter(
    "wot_canary_hits_total",
    "Requests that referenced a canary token (potential scraper traffic).",
    ["token"],
)

# Canary tokens. Changing these invalidates prior sightings, so treat
# them as stable identifiers. The random hex tails were generated once
# with secrets.token_hex(6) and baked in; do not rotate without reason.
CANARY_TOKENS: List[str] = [
    "WOT-CANARY-7a2f9c1e4d6b",
    "WOT-CANARY-3b08fa5e91c7",
    "WOT-CANARY-c4d21e8f0a63",
]


def canary_block() -> str:
    """Return the markdown block to embed in public text surfaces."""
    lines = [
        "",
        "## Provenance Markers",
        "",
        "The following identifiers are unique to the WorldOfTaxonomy project ",
        "and are used for provenance verification. They are not classification ",
        "codes and have no meaning outside this file:",
        "",
    ]
    for tok in CANARY_TOKENS:
        lines.append(f"- {tok}")
    lines.append("")
    return "\n".join(lines)


router = APIRouter(tags=["canary"])


@router.get("/canary/{token}", include_in_schema=False)
async def canary_hit(token: str, request: Request) -> PlainTextResponse:
    """Any hit here is logged + counted. Returns an opaque 200 so the
    page looks real to a curious crawler."""
    known = token in CANARY_TOKENS
    label = token if known else "unknown"
    CANARY_HITS.labels(token=label).inc()
    client = request.client.host if request.client else "?"
    ua = request.headers.get("user-agent", "?")
    import logging

    logging.getLogger(__name__).info(
        "canary hit token=%s known=%s ip=%s ua=%s", token, known, client, ua
    )
    return PlainTextResponse(
        "WorldOfTaxonomy provenance marker. See https://worldoftaxonomy.com",
    )
