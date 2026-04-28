"""Bulk JSONL export endpoints - Pro+ tier only.

GET /api/v1/export/systems.jsonl - all systems, one JSON object per line
GET /api/v1/export/systems/{id}/nodes.jsonl - all nodes for a system as JSONL
GET /api/v1/export/crosswalks.jsonl - all equivalence edges as JSONL (Enterprise)
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from world_of_taxonomy.api.deps import get_conn, require_tier

router = APIRouter(prefix="/api/v1/export", tags=["bulk-export"])

_PRO_OR_ENTERPRISE = frozenset({"pro", "enterprise"})
_ENTERPRISE_ONLY = frozenset({"enterprise"})


async def _jsonl_stream(rows, transform) -> AsyncGenerator[str, None]:
    """Stream rows as newline-delimited JSON."""
    for row in rows:
        yield json.dumps(transform(row), ensure_ascii=False) + "\n"


@router.get("/systems.jsonl")
async def export_systems_jsonl(
    auth: dict = Depends(require_tier("wot:export", _PRO_OR_ENTERPRISE)),
    conn=Depends(get_conn),
):
    """Export all classification systems as JSONL. Requires Pro+ tier."""
    rows = await conn.fetch(
        """SELECT id, name, full_name, authority, region, version,
                  node_count, source_url, source_date, data_provenance, license
           FROM classification_system
           ORDER BY id"""
    )

    def transform(r):
        return {
            "id": r["id"],
            "name": r["name"],
            "full_name": r["full_name"],
            "authority": r["authority"],
            "region": r["region"],
            "version": r["version"],
            "node_count": r["node_count"],
            "source_url": r["source_url"],
            "source_date": r["source_date"],
            "data_provenance": r["data_provenance"],
            "license": r["license"],
        }

    return StreamingResponse(
        _jsonl_stream(rows, transform),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="systems.jsonl"'},
    )


@router.get("/systems/{system_id}/nodes.jsonl")
async def export_nodes_jsonl(
    system_id: str,
    auth: dict = Depends(require_tier("wot:export", _PRO_OR_ENTERPRISE)),
    conn=Depends(get_conn),
):
    """Export all nodes in a system as JSONL. Requires Pro+ tier."""
    # Verify system exists
    exists = await conn.fetchval(
        "SELECT 1 FROM classification_system WHERE id = $1", system_id
    )
    if not exists:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found")

    rows = await conn.fetch(
        """SELECT code, title, description, level, parent_code, is_leaf
           FROM classification_node
           WHERE system_id = $1
           ORDER BY seq_order, code""",
        system_id,
    )

    def transform(r):
        return {
            "code": r["code"],
            "title": r["title"],
            "description": r["description"],
            "level": r["level"],
            "parent_code": r["parent_code"],
            "is_leaf": r["is_leaf"],
        }

    safe_name = system_id.replace("/", "_")
    return StreamingResponse(
        _jsonl_stream(rows, transform),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_nodes.jsonl"'},
    )


@router.get("/crosswalks.jsonl")
async def export_crosswalks_jsonl(
    auth: dict = Depends(require_tier("wot:export", _ENTERPRISE_ONLY)),
    conn=Depends(get_conn),
):
    """Export all crosswalk edges as JSONL. Requires Enterprise tier."""
    rows = await conn.fetch(
        """SELECT source_system, source_code, target_system, target_code, match_type
           FROM equivalence
           ORDER BY source_system, source_code"""
    )

    def transform(r):
        return {
            "source_system": r["source_system"],
            "source_code": r["source_code"],
            "target_system": r["target_system"],
            "target_code": r["target_code"],
            "match_type": r["match_type"],
        }

    return StreamingResponse(
        _jsonl_stream(rows, transform),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="crosswalks.jsonl"'},
    )
