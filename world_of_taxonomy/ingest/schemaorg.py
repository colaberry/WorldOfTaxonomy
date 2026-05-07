"""schema.org type tree ingester.

Source: https://schema.org/version/latest/schemaorg-current-https.jsonld
Format: JSON-LD with @graph array; each entry has @id, @type, rdfs:label,
        rdfs:comment, and (optionally) rdfs:subClassOf.
License: CC BY-SA 3.0 (schema.org content license)
Verified count: 926 schema:* classes on 2026-05-07 (1003 total rdfs:Class
                in @graph, 77 are imports from external vocabularies and
                are skipped).

Hierarchy: rooted tree at schema:Thing. ~57 classes have multiple parents
via rdfs:subClassOf; we keep the first listed parent as the canonical
hierarchy edge and append the alternative parents to the description so
the relationship is preserved.

Properties (rdf:Property entries) are NOT ingested. Per the WoT inclusion
policy, pure property vocabularies are out of scope; only the type tree
qualifies.

Verdict against the WoT inclusion policy:
    1. Published and externally maintained: yes (schema.org consortium)
    2. Stable identifiers: yes (schema:<TypeName>)
    3. Enumerated/hierarchical: yes (rdfs:subClassOf tree)
    4. Practical size: yes (~926, well under 500K cap)
"""
from __future__ import annotations

import json
import os
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

from world_of_taxonomy.ingest.hash_util import sha256_of_file


# ── Provenance constants ─────────────────────────────────────────

_SYSTEM_ROW = (
    "schema_org",
    "schema.org",
    "schema.org Type Vocabulary",
    "latest",
    "Global",
    "schema.org consortium (Google, Microsoft, Yahoo, Yandex)",
)
_SOURCE_URL = "https://schema.org/version/latest/schemaorg-current-https.jsonld"
_DATA_PROVENANCE = "official_download"
_LICENSE = "CC BY-SA 3.0"
_EXPECTED_MIN = 700

CHUNK = 500
DEFAULT_DATA_FILE = "data/schemaorg-current-https.jsonld"

THING_ROOT = "Thing"
SCHEMA_PREFIX = "schema:"


# ── Parser ──────────────────────────────────────────────────────


def parse_schemaorg_jsonld(
    path: str = DEFAULT_DATA_FILE,
) -> List[Tuple[str, str, int, Optional[str], Optional[str]]]:
    """Parse the schema.org JSON-LD dump into WoT node tuples.

    Returns: list of (code, title, level, parent_code, description).

    Filtering: only schema:* rdfs:Class entries are kept. Non-schema
    imports (unece:, fibo:, snomed:, etc.) are skipped. rdf:Property
    entries are not ingested.

    Multi-parent classes use the first listed parent as the canonical
    hierarchy edge; alternative parents are appended to the description
    in a 'Also subclass of: A, B' suffix.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = data.get("@graph", [])
    classes = {}
    for entry in graph:
        et = entry.get("@type")
        if et != "rdfs:Class":
            continue
        eid = entry.get("@id", "")
        if not eid.startswith(SCHEMA_PREFIX):
            continue
        local_name = eid[len(SCHEMA_PREFIX):]
        classes[local_name] = entry

    # Build parent edges (first parent canonical, others tracked separately)
    primary_parent: Dict[str, Optional[str]] = {}
    extra_parents: Dict[str, List[str]] = defaultdict(list)
    for name, entry in classes.items():
        sub = entry.get("rdfs:subClassOf")
        if sub is None:
            primary_parent[name] = None
            continue
        if isinstance(sub, dict):
            parent_id = sub.get("@id", "")
            primary_parent[name] = (
                parent_id[len(SCHEMA_PREFIX):]
                if parent_id.startswith(SCHEMA_PREFIX)
                else None
            )
        elif isinstance(sub, list):
            primary_id = None
            extras: List[str] = []
            for item in sub:
                pid = item.get("@id", "") if isinstance(item, dict) else ""
                if not pid.startswith(SCHEMA_PREFIX):
                    continue
                short = pid[len(SCHEMA_PREFIX):]
                if primary_id is None:
                    primary_id = short
                else:
                    extras.append(short)
            primary_parent[name] = primary_id
            if extras:
                extra_parents[name] = extras
        else:
            primary_parent[name] = None

    # If a primary parent points outside the schema:* set (e.g., to an
    # imported class we filtered out), null it so the node still hangs
    # off Thing or sits as an alternate root.
    for name, parent in list(primary_parent.items()):
        if parent is not None and parent not in classes:
            primary_parent[name] = None

    # Compute level via BFS from Thing (level 1) and any other roots
    level: Dict[str, int] = {}
    children_of: Dict[str, List[str]] = defaultdict(list)
    for name, parent in primary_parent.items():
        if parent is not None:
            children_of[parent].append(name)
    roots = [n for n, p in primary_parent.items() if p is None]
    queue = deque(roots)
    for r in roots:
        level[r] = 1
    while queue:
        cur = queue.popleft()
        for child in children_of.get(cur, []):
            if child not in level:
                level[child] = level[cur] + 1
                queue.append(child)
    # Any class not reached (shouldn't happen with above null-fixup) gets level 1
    for name in classes:
        level.setdefault(name, 1)

    nodes: List[Tuple[str, str, int, Optional[str], Optional[str]]] = []
    for name, entry in classes.items():
        title = _label(entry.get("rdfs:label"))
        comment = _comment(entry.get("rdfs:comment"))
        if extras := extra_parents.get(name):
            extras_str = ", ".join(extras)
            comment = (
                f"{comment}\n\nAlso a subclass of: {extras_str}."
                if comment
                else f"Also a subclass of: {extras_str}."
            )
        nodes.append((
            name,
            _clean(title),
            level.get(name, 1),
            primary_parent.get(name),
            _clean(comment) if comment else None,
        ))

    nodes.sort(key=lambda r: (r[2], r[0]))
    return nodes


def _label(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("@value", "") or value.get("en", "")
    if isinstance(value, list):
        for item in value:
            txt = _label(item)
            if txt:
                return txt
    return ""


def _comment(value) -> str:
    return _label(value)


def _clean(s: str) -> str:
    if not s:
        return s
    return s.replace("\u2014", "-").strip()


# ── Ingestion ────────────────────────────────────────────────────


async def ingest_schemaorg(
    conn,
    data_file: str = DEFAULT_DATA_FILE,
) -> int:
    """Ingest schema.org type tree into the database.

    Args:
        conn: asyncpg connection.
        data_file: path to the schema.org JSON-LD file.

    Returns:
        Number of nodes ingested.
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(
            f"schema.org data file not found: {data_file}\n"
            f"Download with: curl -sSL {_SOURCE_URL} -o {data_file}"
        )

    nodes = parse_schemaorg_jsonld(data_file)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} schema.org nodes, expected >= "
            f"{_EXPECTED_MIN}. Source file may be corrupted."
        )

    file_hash = sha256_of_file(data_file)
    sid, short_name, full_name, ver, region, authority = _SYSTEM_ROW

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
        sid, short_name, full_name, ver, region, authority,
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
        batch = records[i : i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, description, level, parent_code)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            batch,
        )
        count += len(batch)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )

    print(f"  Ingested {count} schema.org type-tree nodes")
    return count
