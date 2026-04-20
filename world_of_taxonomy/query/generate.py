"""AI-powered taxonomy generation.

Calls the shared LLM client (Ollama Cloud by default) to suggest
sub-classifications for any node on demand. Nothing is persisted until the
user explicitly accepts the suggestions.
"""
from __future__ import annotations

import json
from typing import List

from world_of_taxonomy import llm_client
from world_of_taxonomy.api.schemas import GeneratedNode


async def _fetch_context(conn, system_id: str, parent_code: str) -> dict:
    """Fetch system metadata, node details, ancestors, and existing children."""
    system = await conn.fetchrow(
        "SELECT id, name, full_name, region, authority FROM classification_system WHERE id = $1",
        system_id,
    )
    if system is None:
        raise ValueError(f"System {system_id!r} not found")

    node = await conn.fetchrow(
        "SELECT code, title, description, level, parent_code, sector_code "
        "FROM classification_node WHERE system_id = $1 AND code = $2",
        system_id,
        parent_code,
    )
    if node is None:
        raise ValueError(f"Node {parent_code!r} not found in system {system_id!r}")

    # Ancestors (walk up the tree)
    ancestors = []
    cursor_code = node["parent_code"]
    while cursor_code is not None:
        row = await conn.fetchrow(
            "SELECT code, title, level, parent_code "
            "FROM classification_node WHERE system_id = $1 AND code = $2",
            system_id,
            cursor_code,
        )
        if row is None:
            break
        ancestors.insert(0, dict(row))
        cursor_code = row["parent_code"]

    # Existing children (so we don't suggest duplicates)
    children = await conn.fetch(
        "SELECT code, title FROM classification_node "
        "WHERE system_id = $1 AND parent_code = $2 ORDER BY seq_order",
        system_id,
        parent_code,
    )

    # Sibling examples for code format inference
    siblings = await conn.fetch(
        "SELECT code FROM classification_node "
        "WHERE system_id = $1 AND parent_code = $2 ORDER BY seq_order LIMIT 5",
        system_id,
        node["parent_code"] or parent_code,
    )

    return {
        "system": dict(system),
        "node": dict(node),
        "ancestors": ancestors,
        "children": [dict(r) for r in children],
        "sibling_codes": [r["code"] for r in siblings],
    }


def _build_prompt(ctx: dict, count: int) -> str:
    system = ctx["system"]
    node = ctx["node"]
    ancestors = ctx["ancestors"]
    children = ctx["children"]
    sibling_codes = ctx["sibling_codes"]

    ancestor_path = " > ".join(a["title"] for a in ancestors) if ancestors else "(root level)"

    existing_block = ""
    if children:
        existing_block = "Existing children (do NOT duplicate these):\n" + "\n".join(
            f"  - {c['code']}: {c['title']}" for c in children
        )
    else:
        existing_block = "This node has no existing children yet."

    code_hint = ""
    if sibling_codes:
        code_hint = (
            f"Code format hint - sibling codes at this level look like: "
            + ", ".join(sibling_codes)
        )
    else:
        code_hint = (
            f"Code format hint - parent code is {node['code']!r}. "
            "Generate child codes that follow the natural extension pattern of this system."
        )

    return f"""You are a taxonomy expert. Generate exactly {count} sub-classification nodes
for the following parent node in the {system['name']} classification system.

System: {system['name']} ({system.get('full_name') or system['name']})
Authority: {system.get('authority') or 'N/A'}
Region: {system.get('region') or 'Global'}

Parent node:
  Code: {node['code']}
  Title: {node['title']}
  Description: {node.get('description') or 'N/A'}
  Level: {node['level']}
  Ancestor path: {ancestor_path}

{existing_block}

{code_hint}

Rules:
1. Generate exactly {count} sub-classifications.
2. Each must be a genuine, meaningful sub-category of "{node['title']}" -
   a true subtype, not a topic about the parent (e.g. for "Alkali Metals",
   "Lithium Group" is a subtype; "Physical Properties of Alkali Metals" is NOT).
3. Codes must be unique and follow the code format of this system.
4. Titles should be concise (3-8 words), consistent with how this taxonomy names things.
5. Descriptions are optional - only include if it genuinely adds clarity.
6. Reason is REQUIRED for every item: one short sentence (<=20 words) explaining
   why this is a legitimate subtype of the parent. Humans use this to accept or
   reject the suggestion.
7. Do NOT duplicate any existing children listed above.
8. Output ONLY valid JSON, no markdown, no explanation.

Output format (JSON array):
[
  {{"code": "...", "title": "...", "description": "...", "reason": "..."}},
  ...
]"""


async def generate_children(
    conn,
    system_id: str,
    parent_code: str,
    count: int = 5,
) -> List[GeneratedNode]:
    """Call the configured LLM to suggest sub-classifications for a node.

    Does NOT write to the database. Returns suggestions for the user to review.
    Raises llm_client.LLMNotConfiguredError if OLLAMA_API_KEY is not set.
    """
    ctx = await _fetch_context(conn, system_id, parent_code)
    prompt = _build_prompt(ctx, count)

    raw = await llm_client.chat_json(
        [{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.0,
    )
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0].strip()

    data = json.loads(raw)
    return [
        GeneratedNode(
            code=item["code"],
            title=item["title"],
            description=item.get("description") or None,
            reason=item.get("reason") or None,
        )
        for item in data
    ]


async def persist_generated_children(
    conn,
    system_id: str,
    parent_code: str,
    nodes: List[GeneratedNode],
) -> List[dict]:
    """Insert accepted generated nodes into the database.

    Sets is_leaf=True for each new node and is_leaf=False for the parent.
    Updates the system node_count.
    Returns the inserted rows.
    """
    parent = await conn.fetchrow(
        "SELECT level, sector_code FROM classification_node "
        "WHERE system_id = $1 AND code = $2",
        system_id,
        parent_code,
    )
    if parent is None:
        raise ValueError(f"Parent node {parent_code!r} not found in {system_id!r}")

    child_level = parent["level"] + 1
    sector_code = parent["sector_code"]

    # Get current max seq_order for children of this parent
    max_seq = await conn.fetchval(
        "SELECT COALESCE(MAX(seq_order), 0) FROM classification_node "
        "WHERE system_id = $1 AND parent_code = $2",
        system_id,
        parent_code,
    )

    inserted = []
    for i, node in enumerate(nodes, 1):
        row = await conn.fetchrow(
            """
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code,
                 sector_code, is_leaf, seq_order)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (system_id, code) DO NOTHING
            RETURNING id, system_id, code, title, description, level,
                      parent_code, sector_code, is_leaf, seq_order
            """,
            system_id,
            node.code,
            node.title,
            child_level,
            parent_code,
            sector_code,
            True,  # is_leaf
            max_seq + i,
        )
        if row is not None:
            r = dict(row)
            if node.description:
                await conn.execute(
                    "UPDATE classification_node SET description = $1 "
                    "WHERE system_id = $2 AND code = $3",
                    node.description,
                    system_id,
                    node.code,
                )
                r["description"] = node.description
            inserted.append(r)

    if inserted:
        # Parent is no longer a leaf
        await conn.execute(
            "UPDATE classification_node SET is_leaf = FALSE "
            "WHERE system_id = $1 AND code = $2",
            system_id,
            parent_code,
        )
        # Update system node count
        await conn.execute(
            "UPDATE classification_system SET node_count = node_count + $1 WHERE id = $2",
            len(inserted),
            system_id,
        )

    return inserted
