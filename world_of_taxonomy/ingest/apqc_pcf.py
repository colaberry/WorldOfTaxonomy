"""APQC PCF Cross-Industry Process Classification Framework (Skeleton).

Source: APQC, https://www.apqc.org/process-frameworks
The cross-industry PCF is the canonical pan-industry process taxonomy.
Originally introduced in 1992; current public release is the v7.x line.

This is a Level-1 skeleton: 13 top-level categories of the Cross-Industry
PCF. Levels 2-5 (~1,500 detailed process elements: process groups,
processes, activities, tasks) require the official APQC spreadsheet,
which is gated behind APQC's free registration. When that file is
available, this ingester can be extended in place; the system_id stays
the same, so existing crosswalks to apqc_pcf level-1 codes survive.

The 13 codes (1.0 through 13.0) are APQC's own identifiers, not
WoT-minted. Top-level wording follows the APQC v7.4 Cross-Industry
release; descriptions are paraphrases of APQC's published category
abstracts encoded from canonical-knowledge for the skeleton.

Provenance: manual_transcription (Tier 3) - the structure is encoded
from publicly documented APQC materials; consumers should treat this
as a stable starting point and re-anchor against the official
spreadsheet when they need the full ~1,500-element tree.

Hierarchy:
  Level 1: 13 top-level categories. Codes 1.0 - 6.0 are operating
           processes; 7.0 - 13.0 are management and support services.
"""
from __future__ import annotations

import hashlib
from typing import List, Optional, Tuple


_SYSTEM_ROW = (
    "apqc_pcf",
    "APQC PCF (Skeleton)",
    "APQC Cross-Industry Process Classification Framework (Level 1)",
    "v7.4 (skeleton)",
    "Global",
    "APQC",
)
_SOURCE_URL = "https://www.apqc.org/process-frameworks"
_DATA_PROVENANCE = "manual_transcription"
_LICENSE = "APQC PCF (free use with attribution)"

CHUNK = 500


# Authoritative source-of-truth for the skeleton. Future contributors
# extending this ingester to Levels 2-5 should keep this dict and add
# parallel structures for the deeper levels rather than rewriting this
# table.
APQC_PCF_LEVEL_1: dict[str, tuple[str, str]] = {
    "1.0": (
        "Develop Vision and Strategy",
        "Define the business concept and long-term vision, develop business "
        "strategy, manage strategic initiatives, and align organizational "
        "objectives. The category covers strategic planning, corporate "
        "development, and the cross-functional governance that sets direction.",
    ),
    "2.0": (
        "Develop and Manage Products and Services",
        "Govern, plan, design, develop, and manage the lifecycle of products "
        "and services. Spans portfolio management, product/service ideation, "
        "design and engineering, prototyping, and product retirement.",
    ),
    "3.0": (
        "Market and Sell Products and Services",
        "Understand markets and customers, develop marketing strategy, "
        "develop sales strategy, manage sales channels, and execute marketing "
        "and sales operations including pricing, promotion, and lead-to-order.",
    ),
    "4.0": (
        "Deliver Physical Products",
        "Plan for and align supply chain resources, procure materials and "
        "services, produce/manufacture and deliver physical products, "
        "manage logistics and warehousing. The category formalizes the "
        "physical-goods delivery path that PCF v7.4 separated from services.",
    ),
    "5.0": (
        "Deliver Services",
        "Plan for and acquire necessary service-delivery resources, define "
        "service-delivery requirements, deliver services to customer, "
        "and manage service-delivery resources. Mirrors category 4.0 for "
        "the service-economy path.",
    ),
    "6.0": (
        "Manage Customer Service",
        "Develop customer-service strategy, plan and manage customer-service "
        "operations, measure and evaluate customer-service operations. "
        "Covers contact-center, field-service, and post-sale support.",
    ),
    "7.0": (
        "Develop and Manage Human Capital",
        "Develop and manage human-resources strategy and planning; recruit, "
        "source, and select; develop and counsel employees; manage employee "
        "performance, rewards, and engagement; redeploy and retire workforce. "
        "Spans the full employee lifecycle.",
    ),
    "8.0": (
        "Manage Information Technology (IT)",
        "Develop IT strategy and govern IT, develop and manage IT customer "
        "relationships, manage business resiliency and risk, manage enterprise "
        "information and data, develop and maintain IT solutions, deploy IT "
        "solutions, deliver IT services, manage IT knowledge.",
    ),
    "9.0": (
        "Manage Financial Resources",
        "Perform planning and management accounting, perform revenue "
        "accounting, perform general accounting and reporting, manage fixed-"
        "asset accounting, process payroll, manage treasury and risk, "
        "manage internal controls, manage taxes, manage international funds "
        "and consolidation.",
    ),
    "10.0": (
        "Acquire, Construct, and Manage Assets",
        "Plan and acquire assets, design and construct productive assets, "
        "maintain productive assets, dispose of assets. Covers facilities, "
        "machinery, vehicles, and other productive long-lived assets.",
    ),
    "11.0": (
        "Manage Enterprise Risk, Compliance, Remediation, and Resiliency",
        "Manage enterprise risk; manage regulatory and ethics compliance; "
        "manage remediation efforts; manage business resiliency. Includes "
        "policy, audit, internal controls beyond finance, and crisis response.",
    ),
    "12.0": (
        "Manage External Relationships",
        "Build investor relationships; manage government and industry "
        "relationships; manage relationships with the board of directors; "
        "manage legal and ethical issues; manage public relations; manage "
        "ESG/sustainability relationships.",
    ),
    "13.0": (
        "Develop and Manage Business Capabilities",
        "Manage business processes, manage portfolio of programs and "
        "projects, manage enterprise quality, manage knowledge, manage "
        "change, develop and manage organization architecture, manage "
        "enterprise organizational capabilities. The PCF's self-referential "
        "category for managing process and capability work itself.",
    ),
}


def parse_apqc_pcf() -> List[Tuple[str, str, int, Optional[str], Optional[str]]]:
    """Return the Level-1 APQC PCF skeleton as (code, title, level,
    parent_code, description) tuples. Pure function, no I/O.
    """
    nodes: List[Tuple[str, str, int, Optional[str], Optional[str]]] = []
    # Sort by numeric prefix so output is stable and intuitive.
    for code in sorted(
        APQC_PCF_LEVEL_1.keys(),
        key=lambda c: int(c.split(".")[0]),
    ):
        title, desc = APQC_PCF_LEVEL_1[code]
        nodes.append((code, _clean(title), 1, None, _clean(desc)))
    return nodes


def _clean(s: str) -> str:
    """Replace em-dashes (U+2014) with hyphens and trim. Uses the
    unicode escape to keep this file clean of literal em-dashes per
    the repo's CI guard.
    """
    if s is None:
        return ""
    return s.replace("\u2014", "-").strip()


def _synthetic_file_hash(nodes) -> str:
    """No source file to hash; emit a deterministic hash of the
    encoded skeleton so source_file_hash is non-null and changes
    only when the skeleton itself changes."""
    h = hashlib.sha256()
    for code, title, _l, _p, desc in nodes:
        h.update(code.encode("utf-8"))
        h.update(b"|")
        h.update(title.encode("utf-8"))
        h.update(b"|")
        h.update((desc or "").encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


async def ingest_apqc_pcf(conn) -> int:
    nodes = parse_apqc_pcf()
    file_hash = _synthetic_file_hash(nodes)
    sid, short, full, ver, region, authority = _SYSTEM_ROW

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority,
                source_url, source_date, data_provenance, license,
                source_file_hash, node_count)
           VALUES ($1,$2,$3,$4,$5,$6,$7,CURRENT_DATE,$8,$9,$10,0)
           ON CONFLICT (id) DO UPDATE SET
                name=$2, full_name=$3, version=$4, region=$5, authority=$6,
                source_url=$7, source_date=CURRENT_DATE, data_provenance=$8,
                license=$9, source_file_hash=$10, node_count=0""",
        sid, short, full, ver, region, authority,
        _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, file_hash,
    )

    await conn.execute(
        "DELETE FROM classification_node WHERE system_id = $1", sid
    )

    records = [
        (sid, code, title, description, level, parent)
        for code, title, level, parent, description in nodes
    ]

    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i : i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, description, level, parent_code)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            chunk,
        )
        count += len(chunk)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )

    print(f"  Ingested {count} APQC PCF Level-1 categories (skeleton)")
    return count
