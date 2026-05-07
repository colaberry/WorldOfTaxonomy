"""Alembic environment for WorldOfTaxonomy.

Reads DATABASE_URL from env (loaded via .env by python-dotenv) so we
never check a connection string into alembic.ini. We do not use an ORM
metadata object, so autogenerate is disabled; all migrations are
hand-written DDL.

pgbouncer note: pgbouncer in transaction pooling mode does not
support server-side prepared statements. psycopg2 does not use prepared
statements by default, so no extra flag is required here; asyncpg users
need ``statement_cache_size=0`` but alembic runs sync.
"""

from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_database_url() -> str:
    url = os.environ.get("ALEMBIC_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL (or ALEMBIC_DATABASE_URL) must be set in the "
            "environment for alembic to run."
        )
    # asyncpg URLs use postgresql+asyncpg://; alembic runs sync so we
    # normalise to the psycopg (v3) driver.
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql+psycopg://" + url[len("postgresql+asyncpg://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


config.set_main_option("sqlalchemy.url", _resolve_database_url())

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
