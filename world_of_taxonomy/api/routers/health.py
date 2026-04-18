"""Health check endpoint for uptime monitors and orchestrators."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


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
