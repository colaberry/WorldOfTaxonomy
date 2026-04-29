"""Prometheus metrics for the FastAPI app.

Exposes a small, focused set of counters + histograms so operators can
track request volume, latency, and error rates per route. The exposition
endpoint is registered at /api/v1/metrics.

High-cardinality labels (user ids, full codes, request ids) are never
used; only route template, method, and status class, keeping the
metrics file tiny regardless of traffic shape.

Protected by a shared-secret header when METRICS_TOKEN is set. In
development (no token) the endpoint is open so `curl localhost:8000/api
/v1/metrics` works without ceremony.
"""

from __future__ import annotations

import hmac
import os
import time
from typing import Callable, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram
from prometheus_client import generate_latest

REQUEST_COUNT = Counter(
    "wot_http_requests_total",
    "Total HTTP requests by method, route, and status class.",
    ["method", "route", "status_class"],
)

REQUEST_LATENCY = Histogram(
    "wot_http_request_latency_seconds",
    "HTTP request latency in seconds.",
    ["method", "route"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUESTS_IN_FLIGHT = Gauge(
    "wot_http_requests_in_flight",
    "Number of HTTP requests currently being processed.",
)

ERROR_COUNT = Counter(
    "wot_http_errors_total",
    "Total HTTP 5xx responses by route.",
    ["route"],
)

# Bot/abuse signal: number of times the per-IP rate guard returned 429
# for a given endpoint. Spikes here mean either (a) abuse traffic
# arriving, or (b) a legitimate caller hitting the cap, both worth
# investigating. Cardinality is bounded by the small fixed set of
# endpoint_name values declared in rate_guard call sites.
RATE_GUARD_FIRED = Counter(
    "wot_rate_guard_fired_total",
    "Number of times the per-IP rate guard returned 429.",
    ["endpoint"],
)


def _route_template(request: Request) -> str:
    """Return the APIRoute path template (e.g. /api/v1/systems/{id})
    rather than the resolved URL, to keep cardinality bounded."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    # No matched route (404, 405) -> bucket under a sentinel label
    return "__unmatched__"


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Instrument every HTTP request with count + latency + in-flight."""
    # Never instrument the metrics endpoint itself: it would inflate
    # counters every time Prometheus scrapes.
    if request.url.path.endswith("/metrics"):
        return await call_next(request)

    REQUESTS_IN_FLIGHT.inc()
    start = time.perf_counter()
    method = request.method
    status_code = 500  # default if handler raises before returning
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        REQUESTS_IN_FLIGHT.dec()
        route = _route_template(request)
        REQUEST_COUNT.labels(
            method=method,
            route=route,
            status_class=f"{status_code // 100}xx",
        ).inc()
        REQUEST_LATENCY.labels(method=method, route=route).observe(elapsed)
        if status_code >= 500:
            ERROR_COUNT.labels(route=route).inc()


router = APIRouter(tags=["observability"])


@router.get("/api/v1/metrics", include_in_schema=False)
async def metrics_endpoint(
    x_metrics_token: Optional[str] = Header(default=None),
) -> Response:
    """Prometheus exposition endpoint.

    When METRICS_TOKEN is set in the environment, callers must send
    ``X-Metrics-Token: <token>``. Otherwise the endpoint is open so
    developers can curl it locally without setting up credentials.
    """
    expected = os.getenv("METRICS_TOKEN", "").strip()
    if expected:
        # Constant-time compare so a timing side channel can not leak
        # the secret one byte at a time.
        supplied = (x_metrics_token or "").encode("utf-8")
        if not hmac.compare_digest(supplied, expected.encode("utf-8")):
            raise HTTPException(status_code=401, detail="unauthorized")

    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
