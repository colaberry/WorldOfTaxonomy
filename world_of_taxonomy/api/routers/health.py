"""Health + version endpoints for uptime monitors and deploy verification."""

from __future__ import annotations

import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# Read once at import time so the endpoint is cheap. Values are
# injected at container build time (GIT_SHA, BUILD_TIME) or fall back
# to "dev" locally.
_APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
_GIT_SHA = os.getenv("GIT_SHA", "dev")
_BUILD_TIME = os.getenv("BUILD_TIME", "dev")


@router.get("/api/v1/healthz", tags=["health"])
async def healthz(request: Request) -> JSONResponse:
    """Return liveness + database reachability in a single round trip.

    Response shape:
      { "status": "ok" | "degraded", "db": "ok" | "fail", "latency_ms": 0 }

    Returns 200 when the pool is reachable and can run SELECT 1,
    503 when the database probe fails.
    """
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        return JSONResponse(
            {"status": "degraded", "db": "fail", "latency_ms": 0},
            status_code=503,
        )

    started = time.perf_counter()
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        return JSONResponse(
            {"status": "degraded", "db": "fail", "latency_ms": 0},
            status_code=503,
        )

    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return JSONResponse({"status": "ok", "db": "ok", "latency_ms": latency_ms})


@router.get("/api/v1/version", tags=["health"])
async def version() -> JSONResponse:
    """Return the app version, git SHA, and build time.

    Lets operators verify which image is actually running behind a
    load balancer. Values are read from env (APP_VERSION, GIT_SHA,
    BUILD_TIME) injected at container build time.
    """
    return JSONResponse(
        {
            "version": _APP_VERSION,
            "git_sha": _GIT_SHA,
            "build_time": _BUILD_TIME,
        }
    )
