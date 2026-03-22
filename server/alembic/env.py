# -*- coding: utf-8 -*-
"""
Alembic migration environment.

Database URL is read from server/.env (DATABASE_URL),
falling back to the engine already configured in server.core.database.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy import engine_from_config

# ---------------------------------------------------------------------------
# Make sure the repo root is on sys.path so that "server.*" imports work
# whether alembic is run from server/ or from the repo root.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import project engine + Base (triggers model registration)
from server.core.database import DATABASE_URL, Base  # noqa: E402
import server.db.models  # noqa: E402, F401  -- registers all ORM classes

# ---------------------------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------------------------
config = context.config

# Override the ini sqlalchemy.url with the value from .env
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set up Python logging from the ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point autogenerate at our ORM metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without an active DB connection (SQL script output)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
