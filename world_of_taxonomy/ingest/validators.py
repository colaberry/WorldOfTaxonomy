"""Post-ingest validators.

Reusable sanity checks an ingester (or an audit job) can run once rows
are loaded. Kept deliberately small and stateless so ingesters can opt
in without inheriting a base class.

Typical usage at the end of an ingester:

    from world_of_taxonomy.ingest.validators import validate_system

    await validate_system(
        conn,
        system_id="naics_2022",
        expected_min=2000,
        expected_max=2500,
    )

Each validator raises ValidationError on failure so the caller can abort
the transaction. Aggregated checks via ``validate_system`` return a
``ValidationReport`` and raise only if ``raise_on_error=True``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class ValidationError(Exception):
    """Raised when a post-ingest check fails."""


@dataclass
class ValidationReport:
    system_id: str
    node_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


async def count_nodes(conn, system_id: str) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM classification_node WHERE system_id = $1",
        system_id,
    )


async def check_row_count(
    conn,
    system_id: str,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    """Assert the row count for a system is within expected bounds."""
    count = await count_nodes(conn, system_id)
    if minimum is not None and count < minimum:
        raise ValidationError(
            f"{system_id}: only {count} nodes loaded, expected at least {minimum}"
        )
    if maximum is not None and count > maximum:
        raise ValidationError(
            f"{system_id}: {count} nodes loaded, expected at most {maximum}"
        )
    return count


async def check_no_duplicate_codes(conn, system_id: str) -> None:
    """Assert (system_id, code) is unique. The schema enforces this, but
    pre-insert duplicates in source data can crash batched loads in
    surprising ways; this check surfaces the offender."""
    row = await conn.fetchrow(
        """
        SELECT code, COUNT(*) AS n
          FROM classification_node
         WHERE system_id = $1
         GROUP BY code
        HAVING COUNT(*) > 1
         LIMIT 1
        """,
        system_id,
    )
    if row:
        raise ValidationError(
            f"{system_id}: duplicate code {row['code']!r} appears {row['n']} times"
        )


async def check_no_orphaned_parents(conn, system_id: str) -> None:
    """Assert every non-null parent_code resolves to a real node in the
    same system."""
    row = await conn.fetchrow(
        """
        SELECT c.code, c.parent_code
          FROM classification_node c
     LEFT JOIN classification_node p
            ON p.system_id = c.system_id AND p.code = c.parent_code
         WHERE c.system_id = $1
           AND c.parent_code IS NOT NULL
           AND p.code IS NULL
         LIMIT 1
        """,
        system_id,
    )
    if row:
        raise ValidationError(
            f"{system_id}: node {row['code']!r} references missing parent "
            f"{row['parent_code']!r}"
        )


async def check_titles_present(conn, system_id: str) -> int:
    """Warn (not fail) if more than 1% of rows have empty titles."""
    total = await count_nodes(conn, system_id)
    if total == 0:
        return 0
    empty = await conn.fetchval(
        """
        SELECT COUNT(*)
          FROM classification_node
         WHERE system_id = $1
           AND (title IS NULL OR btrim(title) = '')
        """,
        system_id,
    )
    return empty


async def validate_system(
    conn,
    system_id: str,
    expected_min: Optional[int] = None,
    expected_max: Optional[int] = None,
    raise_on_error: bool = True,
) -> ValidationReport:
    """Run the full suite of post-ingest checks for one system.

    Returns a report even on success. Raises ValidationError on first
    failure when raise_on_error is True (the default), so ingesters can
    abort cleanly without writing partial state to the DB.
    """
    report = ValidationReport(system_id=system_id)

    try:
        report.node_count = await check_row_count(
            conn, system_id, minimum=expected_min, maximum=expected_max
        )
        await check_no_duplicate_codes(conn, system_id)
        await check_no_orphaned_parents(conn, system_id)

        empty_titles = await check_titles_present(conn, system_id)
        if empty_titles and report.node_count:
            ratio = empty_titles / report.node_count
            if ratio > 0.01:
                report.warnings.append(
                    f"{empty_titles}/{report.node_count} rows have empty titles "
                    f"({ratio:.1%})"
                )
    except ValidationError as exc:
        report.errors.append(str(exc))
        if raise_on_error:
            raise

    return report
