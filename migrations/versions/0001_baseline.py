"""Baseline: stamp of the schema.sql + schema_auth.sql state at 2026-04-17.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-17

This migration is intentionally a no-op. It exists only to be a target
for ``alembic stamp head`` against an existing deployment whose tables
were created by the legacy ``python -m world_of_taxonomy init`` flow
(which executes schema.sql + schema_auth.sql directly).

For fresh installs, the legacy init path still works; run
``alembic stamp head`` afterwards so alembic's version table reflects
the real state. All future DDL changes should be new alembic revisions,
not edits to schema.sql.

See docs/handover/runbooks/migrations.md for the full workflow.
"""
from __future__ import annotations

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
