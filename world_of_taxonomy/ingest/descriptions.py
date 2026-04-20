"""Backfill classification_node.description without touching hierarchy.

Used by per-system scripts that re-parse an authoritative source file
(Census Bureau, Eurostat, WHO, ...) after the structural ingester has
already run. Only rows with NULL or empty descriptions are updated, so
re-running is safe and idempotent.
"""

from typing import Mapping, Optional


async def apply_descriptions(
    conn,
    system_id: str,
    code_to_description: Mapping[str, Optional[str]],
) -> int:
    """Fill description on existing nodes for a given system.

    Skips entries whose value is None, empty, or whitespace-only. Never
    overwrites an existing non-empty description.

    Returns the number of rows that were updated.
    """
    updated = 0
    for code, raw in code_to_description.items():
        if raw is None:
            continue
        desc = raw.strip()
        if not desc:
            continue
        result = await conn.execute(
            """
            UPDATE classification_node
               SET description = $3
             WHERE system_id = $1
               AND code = $2
               AND (description IS NULL OR description = '')
            """,
            system_id,
            code,
            desc,
        )
        updated += int(result.split()[-1])
    return updated
