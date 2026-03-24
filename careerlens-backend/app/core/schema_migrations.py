"""
app/core/schema_migrations.py — Lightweight schema migrations
=============================================================
Provides a minimal migration registry for additive schema updates
without requiring Alembic in this prototype stage.
"""

from __future__ import annotations

from typing import Callable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine, Connection


MigrationFn = Callable[[Connection], None]


def _ensure_migration_table(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                migration_key VARCHAR(128) NOT NULL UNIQUE,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _is_applied(conn: Connection, migration_key: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM schema_migrations WHERE migration_key = :migration_key LIMIT 1"
        ),
        {"migration_key": migration_key},
    ).first()
    return row is not None


def _record_applied(conn: Connection, migration_key: str) -> None:
    conn.execute(
        text(
            "INSERT INTO schema_migrations (migration_key) VALUES (:migration_key)"
        ),
        {"migration_key": migration_key},
    )


def _migration_20260324_001_add_shortlist_analysis_mode(conn: Connection) -> None:
    inspector = inspect(conn)
    if not inspector.has_table("recruiter_shortlists"):
        return

    column_names = {col.get("name") for col in inspector.get_columns("recruiter_shortlists")}
    if "analysis_mode" not in column_names:
        conn.execute(
            text("ALTER TABLE recruiter_shortlists ADD COLUMN analysis_mode VARCHAR(16) NULL")
        )


MIGRATIONS: list[tuple[str, MigrationFn]] = [
    ("20260324_001_add_shortlist_analysis_mode", _migration_20260324_001_add_shortlist_analysis_mode),
]


def run_schema_migrations(engine: Engine) -> None:
    """Run pending schema migrations in a deterministic order."""
    with engine.begin() as conn:
        _ensure_migration_table(conn)
        for migration_key, migration_fn in MIGRATIONS:
            if _is_applied(conn, migration_key):
                continue
            migration_fn(conn)
            _record_applied(conn, migration_key)
