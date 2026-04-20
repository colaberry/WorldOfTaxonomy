"""Full-text search queries using PostgreSQL tsvector + GIN index."""

from typing import List, Optional

from world_of_taxonomy.models import ClassificationNode


def _row_to_node(row) -> ClassificationNode:
    """Convert a database row to a ClassificationNode."""
    return ClassificationNode(
        id=row["id"],
        system_id=row["system_id"],
        code=row["code"],
        title=row["title"],
        description=row.get("description"),
        level=row["level"],
        parent_code=row.get("parent_code"),
        sector_code=row.get("sector_code"),
        is_leaf=row["is_leaf"],
        seq_order=row.get("seq_order", 0),
    )


async def search_nodes(
    conn,
    query: str,
    system_id: Optional[str] = None,
    limit: int = 50,
    system_ids: Optional[List[str]] = None,
) -> List[ClassificationNode]:
    """Search classification nodes using full-text search.

    Uses PostgreSQL's websearch_to_tsquery for natural language queries,
    falling back to prefix matching for short terms.

    `system_id` (singular) is a hard filter to a single system.
    `system_ids` (plural) is an allowlist used by country scoping. If both are
    supplied, `system_id` wins.
    """
    if not query or not query.strip():
        return []

    if system_id:
        rows = await conn.fetch(
            """SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
               FROM classification_node
               WHERE system_id = $3
                 AND (search_vector @@ plainto_tsquery('english', $1)
                      OR code ILIKE $2
                      OR title ILIKE $2)
               ORDER BY rank DESC, seq_order
               LIMIT $4""",
            query,
            f"%{query}%",
            system_id,
            limit,
        )
    elif system_ids:
        rows = await conn.fetch(
            """SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
               FROM classification_node
               WHERE system_id = ANY($3::text[])
                 AND (search_vector @@ plainto_tsquery('english', $1)
                      OR code ILIKE $2
                      OR title ILIKE $2)
               ORDER BY rank DESC, seq_order
               LIMIT $4""",
            query,
            f"%{query}%",
            system_ids,
            limit,
        )
    else:
        rows = await conn.fetch(
            """SELECT *, ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
               FROM classification_node
               WHERE search_vector @@ plainto_tsquery('english', $1)
                  OR code ILIKE $2
                  OR title ILIKE $2
               ORDER BY rank DESC, seq_order
               LIMIT $3""",
            query,
            f"%{query}%",
            limit,
        )

    return [_row_to_node(r) for r in rows]
