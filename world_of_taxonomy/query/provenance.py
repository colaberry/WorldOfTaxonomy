"""Provenance enrichment and audit queries.

Provides helpers to attach system-level provenance metadata to node
responses, and aggregate audit queries for data trustworthiness review.
"""

from typing import Any, Dict, List, Optional


async def get_system_provenance_map(
    conn, system_ids: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Fetch provenance fields for a set of system IDs.

    Returns a dict mapping system_id -> {data_provenance, license,
    source_url, source_date, source_file_hash, node_url_template}.
    `node_url_template` contains a `{code}` placeholder to build a
    per-code authority deep link, or None when no such page exists.
    """
    if not system_ids:
        return {}
    rows = await conn.fetch(
        """SELECT id, data_provenance, license, source_url,
                  source_date, source_file_hash, node_url_template
           FROM classification_system
           WHERE id = ANY($1)""",
        system_ids,
    )
    result = {}
    for r in rows:
        source_date = r["source_date"]
        if source_date is not None:
            source_date = str(source_date)
        result[r["id"]] = {
            "data_provenance": r["data_provenance"],
            "license": r["license"],
            "source_url": r["source_url"],
            "source_date": source_date,
            "source_file_hash": r["source_file_hash"],
            "node_url_template": r["node_url_template"],
        }
    return result


def enrich_node_dict(node_dict: Dict[str, Any], prov: Dict[str, Any]) -> Dict[str, Any]:
    """Attach provenance fields from a system provenance entry to a node dict.

    Also computes `source_url_for_code` by interpolating the node's
    `code` into the system's `node_url_template`. Falls back to None
    when the system has no template configured.
    """
    node_dict["data_provenance"] = prov.get("data_provenance")
    node_dict["license"] = prov.get("license")
    node_dict["source_url"] = prov.get("source_url")
    node_dict["source_date"] = prov.get("source_date")
    node_dict["source_file_hash"] = prov.get("source_file_hash")
    template = prov.get("node_url_template")
    code = node_dict.get("code")
    node_dict["source_url_for_code"] = (
        template.replace("{code}", str(code))
        if template and code is not None
        else None
    )
    return node_dict


def node_response_kwargs(node_obj: Any, prov: Dict[str, Any]) -> Dict[str, Any]:
    """Build kwargs for `NodeResponse(**...)` from a node object + system provenance.

    Handles the `source_url_for_code` interpolation so every router
    that returns a `NodeResponse` gets the per-code authority link
    without repeating the template-replace logic.
    """
    template = prov.get("node_url_template")
    code = getattr(node_obj, "code", None)
    return {
        **node_obj.__dict__,
        **prov,
        "source_url_for_code": (
            template.replace("{code}", str(code))
            if template and code is not None
            else None
        ),
    }


async def get_audit_report(conn) -> Dict[str, Any]:
    """Generate an aggregate audit report for data trustworthiness review.

    Returns provenance tier breakdown, systems missing file hashes,
    structural derivation accounting, and skeleton system detection.
    """
    # Total systems and nodes
    totals = await conn.fetchrow(
        "SELECT count(*) AS systems, coalesce(sum(node_count), 0) AS nodes "
        "FROM classification_system"
    )

    # Provenance tier breakdown
    tier_rows = await conn.fetch(
        """SELECT data_provenance,
                  count(*) AS system_count,
                  coalesce(sum(node_count), 0) AS node_count
           FROM classification_system
           GROUP BY data_provenance
           ORDER BY node_count DESC"""
    )
    tiers = [
        {
            "data_provenance": r["data_provenance"],
            "system_count": r["system_count"],
            "node_count": r["node_count"],
        }
        for r in tier_rows
    ]

    # Official download systems missing file hash
    missing_hash_rows = await conn.fetch(
        """SELECT * FROM classification_system
           WHERE data_provenance = 'official_download'
             AND source_file_hash IS NULL
           ORDER BY name"""
    )

    # Structural derivation stats
    deriv = await conn.fetchrow(
        """SELECT count(*) AS system_count,
                  coalesce(sum(node_count), 0) AS node_count
           FROM classification_system
           WHERE data_provenance = 'structural_derivation'"""
    )

    # Skeleton systems (node_count < 30)
    skeleton_rows = await conn.fetch(
        """SELECT * FROM classification_system
           WHERE node_count < 30
           ORDER BY node_count, name"""
    )

    return {
        "total_systems": totals["systems"],
        "total_nodes": totals["nodes"],
        "provenance_tiers": tiers,
        "official_missing_hash": missing_hash_rows,
        "structural_derivation_count": deriv["system_count"],
        "structural_derivation_nodes": deriv["node_count"],
        "skeleton_systems": skeleton_rows,
    }
