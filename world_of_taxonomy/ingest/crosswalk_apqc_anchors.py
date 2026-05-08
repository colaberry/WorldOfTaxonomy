"""APQC PCF Level-1 conceptual crosswalks to adjacent process frameworks.

These edges anchor APQC PCF to SCOR, ITIL 4, COBIT, and PMBOK at the
conceptual-overlap level (match_type='partial'). They are NOT strict
equivalences: PCF 8.0 ("Manage IT") and ITIL 4 cover overlapping
ground but neither is a substitute for the other. Use these edges as
discovery hints, not as substitution rules.

The schema's match_type CHECK constraint allows
{exact, partial, broad, narrow}. We use 'partial' here because PCF
top-level categories and the target frameworks have meaningful
overlap without one strictly containing the other - PCF 8.0 covers
IT management as a business function while ITIL 4 covers IT service
management as a discipline; neither is a subset of the other.

NAICS sector ranges are intentionally NOT crosswalked to APQC PCF.
PCF describes internal business processes that every NAICS sector
performs (every Construction firm runs HR; every Healthcare provider
runs IT); the cross-product would be 12 PCF categories x 99 NAICS
sectors = ~1,200 noisy edges. The semantic value is zero. Industry-
to-process anchoring is better expressed as "see also" rather than
as classification edges.

ISO 15926 is also out of scope (license posture: ISO paywall) per
the inclusion-policy assessment.
"""
from __future__ import annotations

from typing import List, Tuple

# Each tuple: (pcf_code, target_system, target_code, notes)
# All edges use match_type='partial'.
APQC_CROSSWALKS: List[Tuple[str, str, str, str]] = [
    # ── PCF -> SCOR (Supply Chain Operations Reference) ─────────────
    # PCF 4.0 Deliver Physical Products fans out across the SCOR
    # supply chain: Plan -> Source -> Make -> Deliver.
    ("4.0", "scor_model", "SC.01", "PCF Deliver Physical Products plans the supply chain (SCOR Plan)"),
    ("4.0", "scor_model", "SC.02", "PCF Deliver Physical Products sources materials (SCOR Source)"),
    ("4.0", "scor_model", "SC.03", "PCF Deliver Physical Products produces goods (SCOR Make)"),
    ("4.0", "scor_model", "SC.04", "PCF Deliver Physical Products fulfills orders (SCOR Deliver)"),
    # PCF 5.0 Deliver Services overlaps SCOR Deliver and Orchestrate
    # but is service-shaped rather than physical-goods-shaped.
    ("5.0", "scor_model", "SC.04", "PCF Deliver Services delivers via service execution (SCOR Deliver, service-shaped)"),
    ("5.0", "scor_model", "SC.07", "PCF Deliver Services orchestrates multi-party service workflows (SCOR Orchestrate)"),
    # PCF 11.0 Manage Risk and 13.0 Develop Capabilities both overlap
    # the SCOR Enable category which covers cross-cutting governance.
    ("11.0", "scor_model", "SC.06", "PCF Manage Enterprise Risk overlaps SCOR Enable (governance and controls)"),
    ("13.0", "scor_model", "SC.06", "PCF Develop and Manage Business Capabilities overlaps SCOR Enable (capability foundations)"),

    # ── PCF -> ITIL 4 (IT service management) ──────────────────────
    # PCF 8.0 Manage IT is the umbrella; ITIL 4 elaborates it into
    # 25 practices. Wire the most direct overlaps; consumers can
    # browse from there.
    ("8.0", "itil4", "IL.16", "PCF Manage IT includes business analysis (ITIL Service Mgmt: Business Analysis)"),
    ("8.0", "itil4", "IL.18", "PCF Manage IT includes change enablement (ITIL Service Mgmt: Change Enablement)"),
    ("8.0", "itil4", "IL.19", "PCF Manage IT includes incident management (ITIL Service Mgmt: Incident Management)"),
    ("8.0", "itil4", "IL.20", "PCF Manage IT includes problem management (ITIL Service Mgmt: Problem Management)"),
    ("8.0", "itil4", "IL.21", "PCF Manage IT includes service desk operations (ITIL Service Mgmt: Service Desk)"),
    ("8.0", "itil4", "IL.22", "PCF Manage IT includes service level management (ITIL Service Mgmt: Service Level Mgmt)"),
    ("8.0", "itil4", "IL.23", "PCF Manage IT includes deployment (ITIL Technical: Deployment Management)"),
    ("8.0", "itil4", "IL.24", "PCF Manage IT includes infrastructure ops (ITIL Technical: Infrastructure / Platform Mgmt)"),
    ("8.0", "itil4", "IL.25", "PCF Manage IT includes software development and management (ITIL Technical: Software Dev and Mgmt)"),
    # Cross-cutting practices that overlap multiple PCF categories.
    ("7.0", "itil4", "IL.14", "PCF Develop and Manage Human Capital overlaps ITIL General: Workforce and Talent Mgmt"),
    ("11.0", "itil4", "IL.10", "PCF Manage Enterprise Risk overlaps ITIL General: Risk Management"),
    ("11.0", "itil4", "IL.03", "PCF Manage Enterprise Risk overlaps ITIL General: Information Security Management"),
    ("13.0", "itil4", "IL.07", "PCF Develop and Manage Business Capabilities overlaps ITIL General: Portfolio Mgmt"),
    ("13.0", "itil4", "IL.12", "PCF Develop and Manage Business Capabilities overlaps ITIL General: Strategy Management"),
    ("13.0", "itil4", "IL.08", "PCF Develop and Manage Business Capabilities overlaps ITIL General: Project Management"),

    # ── PCF -> COBIT 2019 (IT governance) ──────────────────────────
    # COBIT 2019 has 5 governance domains; PCF 8.0 (Manage IT) and
    # 11.0 (Manage Risk) both overlap multiple domains.
    ("8.0", "reg_cobit", "apo", "PCF Manage IT covers COBIT APO (Align, Plan and Organize)"),
    ("8.0", "reg_cobit", "bai", "PCF Manage IT covers COBIT BAI (Build, Acquire and Implement)"),
    ("8.0", "reg_cobit", "dss", "PCF Manage IT covers COBIT DSS (Deliver, Service and Support)"),
    ("11.0", "reg_cobit", "edm", "PCF Manage Enterprise Risk overlaps COBIT EDM (Evaluate, Direct and Monitor)"),
    ("11.0", "reg_cobit", "mea", "PCF Manage Enterprise Risk overlaps COBIT MEA (Monitor, Evaluate and Assess)"),
    ("13.0", "reg_cobit", "bai", "PCF Develop and Manage Business Capabilities overlaps COBIT BAI"),

    # ── PCF -> PMBOK 7 (project management) ────────────────────────
    # PCF 13.0 (Develop and Manage Business Capabilities) is the
    # umbrella for project portfolio work; PMBOK 7's performance
    # domains specialize this for project execution.
    ("13.0", "pmbok7", "PM.01", "PCF Develop and Manage Business Capabilities engages stakeholders (PMBOK Stakeholders)"),
    ("13.0", "pmbok7", "PM.04", "PCF Develop and Manage Business Capabilities plans work (PMBOK Planning)"),
    ("13.0", "pmbok7", "PM.06", "PCF Develop and Manage Business Capabilities delivers project outcomes (PMBOK Delivery)"),
    ("13.0", "pmbok7", "PM.07", "PCF Develop and Manage Business Capabilities measures progress (PMBOK Measurement)"),
    ("13.0", "pmbok7", "PM.08", "PCF Develop and Manage Business Capabilities manages uncertainty (PMBOK Uncertainty)"),
]


async def ingest_crosswalk_apqc_anchors(conn) -> int:
    """Insert the APQC PCF Level-1 anchor crosswalks. Idempotent via
    ON CONFLICT DO NOTHING on the natural key."""
    # Pre-flight: confirm apqc_pcf and target systems exist. Skip
    # specific edges silently if the target system isn't ingested
    # (e.g., some skeletons may not be deployed in a given DB).
    sys_rows = await conn.fetch(
        "SELECT id FROM classification_system WHERE id = ANY($1::text[])",
        ["apqc_pcf", "scor_model", "itil4", "reg_cobit", "pmbok7"],
    )
    available = {r["id"] for r in sys_rows}
    if "apqc_pcf" not in available:
        raise RuntimeError(
            "ingest_crosswalk_apqc_anchors: apqc_pcf system not present in DB; "
            "ingest the apqc_pcf system first."
        )

    inserted = 0
    skipped = 0
    for src_code, tgt_sys, tgt_code, notes in APQC_CROSSWALKS:
        if tgt_sys not in available:
            skipped += 1
            continue
        # Verify the target node actually exists; we don't want to
        # insert an edge to a non-existent code.
        row = await conn.fetchrow(
            "SELECT 1 FROM classification_node WHERE system_id=$1 AND code=$2",
            tgt_sys, tgt_code,
        )
        if row is None:
            skipped += 1
            continue
        result = await conn.execute(
            """INSERT INTO equivalence
                   (source_system, source_code, target_system, target_code,
                    match_type, notes)
               VALUES ($1, $2, $3, $4, 'partial', $5)
               ON CONFLICT (source_system, source_code, target_system, target_code)
               DO NOTHING""",
            "apqc_pcf", src_code, tgt_sys, tgt_code, notes,
        )
        # asyncpg returns 'INSERT 0 1' on success, 'INSERT 0 0' on conflict.
        if result.endswith(" 1"):
            inserted += 1

    print(
        f"  APQC anchor crosswalks: inserted {inserted}, "
        f"skipped {skipped} (target system or node not present)"
    )
    return inserted
