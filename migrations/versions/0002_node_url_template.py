"""Add node_url_template to classification_system; backfill NAICS 2022.

Revision ID: 0002_node_url_template
Revises: 0001_baseline
Create Date: 2026-04-23

Adds a nullable per-code URL template so the API can expose
`NodeResponse.source_url_for_code` by substituting each node's code into
the template. NULL means the system has no per-code authority page.

Also backfills NAICS 2022 to the Census Bureau per-code search page so
existing deployments get working per-code links without having to
re-ingest.
"""
from __future__ import annotations

from alembic import op


revision = "0002_node_url_template"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE classification_system "
        "ADD COLUMN IF NOT EXISTS node_url_template TEXT"
    )
    op.execute(
        "UPDATE classification_system "
        "   SET node_url_template = "
        "       'https://www.census.gov/naics/?input={code}&year=2022' "
        " WHERE id = 'naics_2022' "
        "   AND node_url_template IS NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE classification_system DROP COLUMN IF EXISTS node_url_template")
