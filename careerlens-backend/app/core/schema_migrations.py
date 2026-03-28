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
    from app.core.config import DATABASE_URL
    if DATABASE_URL.startswith("libsql://"):
        # SQLite / Turso syntax
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_key TEXT NOT NULL UNIQUE,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    else:
        # MySQL syntax
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


def _needs_sqlite_pk_fix(conn: Connection, table_name: str) -> bool:
    row = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name},
    ).first()
    if not row or not row[0]:
        return False
    create_sql = row[0].upper()

    # Already fixed (or naturally valid rowid PK).
    if "ID INTEGER PRIMARY KEY AUTOINCREMENT" in create_sql:
        return False
    if "ID INTEGER PRIMARY KEY" in create_sql and "BIGINT" not in create_sql:
        return False

    # Legacy migrated tables still using BIGINT PK patterns.
    return "ID BIGINT" in create_sql and "PRIMARY KEY" in create_sql


def _rebuild_table_with_integer_pk(conn: Connection, table_name: str, create_sql: str, insert_cols: str) -> None:
    tmp_table = f"{table_name}__legacy"

    conn.execute(text(f"ALTER TABLE {table_name} RENAME TO {tmp_table}"))
    conn.execute(text(create_sql))
    conn.execute(text(f"INSERT INTO {table_name} ({insert_cols}) SELECT {insert_cols} FROM {tmp_table}"))
    conn.execute(text(f"DROP TABLE {tmp_table}"))

    # Keep AUTOINCREMENT sequence aligned with migrated data.
    # Turso may reject ON CONFLICT on sqlite_sequence in some modes.
    conn.execute(text("DELETE FROM sqlite_sequence WHERE name = :table_name"), {"table_name": table_name})
    conn.execute(
        text(
            """
            INSERT INTO sqlite_sequence(name, seq)
            VALUES (:table_name, COALESCE((SELECT MAX(id) FROM """ + table_name + """), 0))
            """
        ),
        {"table_name": table_name},
    )


def _table_sql(conn: Connection, table_name: str) -> str:
    row = conn.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name},
    ).first()
    return row[0] if row and row[0] else ""


def _migration_20260328_002_fix_turso_autoincrement_ids(conn: Connection) -> None:
    from app.core.config import DATABASE_URL

    if not DATABASE_URL.startswith("libsql://"):
        return

    # SQLite/LibSQL: autoincrement works only for INTEGER PRIMARY KEY.
    # Older migrated tables used BIGINT PK, which causes NULL-id insert failures.
    tables_to_fix = [
        (
            "users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                login_id VARCHAR(50),
                password_hash VARCHAR(255),
                password_changed_at DATETIME,
                role VARCHAR(9),
                email_verified BOOLEAN,
                email_verified_at DATETIME,
                is_active BOOLEAN,
                is_deleted BOOLEAN,
                created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                last_login_at DATETIME
            )
            """,
            "id, name, email, login_id, password_hash, password_changed_at, role, email_verified, email_verified_at, is_active, is_deleted, created_at, updated_at, last_login_at",
        ),
        (
            "resumes",
            """
            CREATE TABLE resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                raw_text TEXT NOT NULL,
                filename VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """,
            "id, user_id, raw_text, filename, created_at",
        ),
        (
            "roles",
            """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(512) NOT NULL,
                occupation_id BIGINT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(occupation_id) REFERENCES occupations (id)
            )
            """,
            "id, title, occupation_id, created_at",
        ),
        (
            "skill_scores",
            """
            CREATE TABLE skill_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                overall_score FLOAT NOT NULL,
                core_match FLOAT NOT NULL,
                secondary_match FLOAT NOT NULL,
                bonus_match FLOAT NOT NULL,
                matched_skills JSON,
                missing_skills JSON,
                strengths JSON,
                improvement_priority JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(resume_id) REFERENCES resumes (id),
                FOREIGN KEY(role_id) REFERENCES roles (id)
            )
            """,
            "id, resume_id, role_id, overall_score, core_match, secondary_match, bonus_match, matched_skills, missing_skills, strengths, improvement_priority, created_at",
        ),
        (
            "roadmaps",
            """
            CREATE TABLE roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_score_id INTEGER NOT NULL UNIQUE,
                level VARCHAR(32) NOT NULL,
                title VARCHAR(512) NOT NULL,
                summary TEXT,
                phases JSON NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(skill_score_id) REFERENCES skill_scores (id)
            )
            """,
            "id, skill_score_id, level, title, summary, phases, created_at",
        ),
        (
            "recruiter_shortlists",
            """
            CREATE TABLE recruiter_shortlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recruiter_id INTEGER NOT NULL,
                role_title VARCHAR(512) NOT NULL,
                candidate_name VARCHAR(255) NOT NULL,
                rank INTEGER,
                overall_score FLOAT,
                core_match FLOAT,
                secondary_match FLOAT,
                bonus_match FLOAT,
                match_label VARCHAR(64),
                analysis_mode VARCHAR(16),
                top_strengths JSON,
                top_gaps JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(recruiter_id) REFERENCES users (id)
            )
            """,
            "id, recruiter_id, role_title, candidate_name, rank, overall_score, core_match, secondary_match, bonus_match, match_label, analysis_mode, top_strengths, top_gaps, created_at, updated_at",
        ),
        (
            "dashboard_states",
            """
            CREATE TABLE dashboard_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scope VARCHAR(64) NOT NULL,
                state JSON NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_dashboard_state_user_scope UNIQUE (user_id, scope),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """,
            "id, user_id, scope, state, created_at, updated_at",
        ),
    ]

    conn.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        for table_name, create_sql, insert_cols in tables_to_fix:
            if _needs_sqlite_pk_fix(conn, table_name):
                _rebuild_table_with_integer_pk(conn, table_name, create_sql, insert_cols)
    finally:
        conn.execute(text("PRAGMA foreign_keys=ON"))


def _migration_20260328_004_repair_partial_pk_fix_state(conn: Connection) -> None:
    from app.core.config import DATABASE_URL

    if not DATABASE_URL.startswith("libsql://"):
        return

    # Force-repair tables that can be left in an inconsistent state after
    # interrupted BIGINT->INTEGER PK conversions.
    repairs = [
        (
            "roles",
            """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(512) NOT NULL,
                occupation_id BIGINT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(occupation_id) REFERENCES occupations (id)
            )
            """,
            "id, title, occupation_id, created_at",
        ),
        (
            "resumes",
            """
            CREATE TABLE resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                raw_text TEXT NOT NULL,
                filename VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """,
            "id, user_id, raw_text, filename, created_at",
        ),
        (
            "skill_scores",
            """
            CREATE TABLE skill_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                overall_score FLOAT NOT NULL,
                core_match FLOAT NOT NULL,
                secondary_match FLOAT NOT NULL,
                bonus_match FLOAT NOT NULL,
                matched_skills JSON,
                missing_skills JSON,
                strengths JSON,
                improvement_priority JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(resume_id) REFERENCES resumes (id),
                FOREIGN KEY(role_id) REFERENCES roles (id)
            )
            """,
            "id, resume_id, role_id, overall_score, core_match, secondary_match, bonus_match, matched_skills, missing_skills, strengths, improvement_priority, created_at",
        ),
        (
            "roadmaps",
            """
            CREATE TABLE roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_score_id INTEGER NOT NULL UNIQUE,
                level VARCHAR(32) NOT NULL,
                title VARCHAR(512) NOT NULL,
                summary TEXT,
                phases JSON NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(skill_score_id) REFERENCES skill_scores (id)
            )
            """,
            "id, skill_score_id, level, title, summary, phases, created_at",
        ),
        (
            "dashboard_states",
            """
            CREATE TABLE dashboard_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scope VARCHAR(64) NOT NULL,
                state JSON NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_dashboard_state_user_scope UNIQUE (user_id, scope),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """,
            "id, user_id, scope, state, created_at, updated_at",
        ),
        (
            "recruiter_shortlists",
            """
            CREATE TABLE recruiter_shortlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recruiter_id INTEGER NOT NULL,
                role_title VARCHAR(512) NOT NULL,
                candidate_name VARCHAR(255) NOT NULL,
                rank INTEGER,
                overall_score FLOAT,
                core_match FLOAT,
                secondary_match FLOAT,
                bonus_match FLOAT,
                match_label VARCHAR(64),
                analysis_mode VARCHAR(16),
                top_strengths JSON,
                top_gaps JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(recruiter_id) REFERENCES users (id)
            )
            """,
            "id, recruiter_id, role_title, candidate_name, rank, overall_score, core_match, secondary_match, bonus_match, match_label, analysis_mode, top_strengths, top_gaps, created_at, updated_at",
        ),
    ]

    conn.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        for table_name, create_sql, insert_cols in repairs:
            current_sql = _table_sql(conn, table_name).upper()
            if not current_sql:
                continue

            needs_repair = (
                "ID BIGINT" in current_sql
                or "RESUMES__LEGACY" in current_sql
                or "ID INTEGER PRIMARY KEY AUTOINCREMENT" not in current_sql
            )

            if needs_repair:
                _rebuild_table_with_integer_pk(conn, table_name, create_sql, insert_cols)
    finally:
        conn.execute(text("PRAGMA foreign_keys=ON"))


def _migration_20260328_005_fix_legacy_fk_references(conn: Connection) -> None:
    from app.core.config import DATABASE_URL

    if not DATABASE_URL.startswith("libsql://"):
        return

    # If a table was renamed to *_legacy during rebuild, SQLite can rewrite
    # foreign-key targets in dependent tables. Rebuild those dependents again
    # with canonical FK targets.
    repairs = [
        (
            "skill_scores",
            """
            CREATE TABLE skill_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                overall_score FLOAT NOT NULL,
                core_match FLOAT NOT NULL,
                secondary_match FLOAT NOT NULL,
                bonus_match FLOAT NOT NULL,
                matched_skills JSON,
                missing_skills JSON,
                strengths JSON,
                improvement_priority JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(resume_id) REFERENCES resumes (id),
                FOREIGN KEY(role_id) REFERENCES roles (id)
            )
            """,
            "id, resume_id, role_id, overall_score, core_match, secondary_match, bonus_match, matched_skills, missing_skills, strengths, improvement_priority, created_at",
        ),
        (
            "roadmaps",
            """
            CREATE TABLE roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_score_id INTEGER NOT NULL UNIQUE,
                level VARCHAR(32) NOT NULL,
                title VARCHAR(512) NOT NULL,
                summary TEXT,
                phases JSON NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(skill_score_id) REFERENCES skill_scores (id)
            )
            """,
            "id, skill_score_id, level, title, summary, phases, created_at",
        ),
    ]

    conn.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        for table_name, create_sql, insert_cols in repairs:
            current_sql = _table_sql(conn, table_name).upper()
            if "__LEGACY" in current_sql:
                _rebuild_table_with_integer_pk(conn, table_name, create_sql, insert_cols)
    finally:
        conn.execute(text("PRAGMA foreign_keys=ON"))


def _migration_20260328_006_normalize_shortlist_json_fields(conn: Connection) -> None:
    from app.core.config import DATABASE_URL

    if not DATABASE_URL.startswith("libsql://"):
        return

    inspector = inspect(conn)
    if not inspector.has_table("recruiter_shortlists"):
        return

    # Some legacy imports stored Python-list-like strings (or null-ish values)
    # in JSON columns, which can crash ORM deserialization with JSONDecodeError.
    conn.execute(
        text(
            """
            UPDATE recruiter_shortlists
            SET top_strengths = '[]'
            WHERE top_strengths IS NULL
               OR trim(CAST(top_strengths AS TEXT)) = ''
               OR trim(CAST(top_strengths AS TEXT)) = 'None'
               OR trim(CAST(top_strengths AS TEXT)) = 'NULL'
               OR json_valid(CAST(top_strengths AS TEXT)) = 0
            """
        )
    )


def _migration_20260328_007_normalize_dashboard_state_json(conn: Connection) -> None:
    from app.core.config import DATABASE_URL

    if not DATABASE_URL.startswith("libsql://"):
        return

    inspector = inspect(conn)
    if not inspector.has_table("dashboard_states"):
        return

    # Guard against legacy/imported invalid JSON blobs that break ORM decode.
    conn.execute(
        text(
            """
            UPDATE dashboard_states
            SET state = '{}'
            WHERE state IS NULL
               OR trim(CAST(state AS TEXT)) = ''
               OR trim(CAST(state AS TEXT)) = 'None'
               OR trim(CAST(state AS TEXT)) = 'NULL'
               OR json_valid(CAST(state AS TEXT)) = 0
               OR json_type(CAST(state AS TEXT)) != 'object'
            """
        )
    )

    conn.execute(
        text(
            """
            UPDATE recruiter_shortlists
            SET top_gaps = '[]'
            WHERE top_gaps IS NULL
               OR trim(CAST(top_gaps AS TEXT)) = ''
               OR trim(CAST(top_gaps AS TEXT)) = 'None'
               OR trim(CAST(top_gaps AS TEXT)) = 'NULL'
               OR json_valid(CAST(top_gaps AS TEXT)) = 0
            """
        )
    )


def _migration_20260328_008_enforce_shortlist_consistency(conn: Connection) -> None:
    inspector = inspect(conn)
    if not inspector.has_table("recruiter_shortlists"):
        return

    from app.core.config import DATABASE_URL

    # Normalize mode values and trim display keys before dedupe.
    if DATABASE_URL.startswith("libsql://"):
        conn.execute(
            text(
                """
                UPDATE recruiter_shortlists
                SET analysis_mode = CASE
                    WHEN lower(trim(COALESCE(analysis_mode, ''))) = 'hybrid' THEN 'hybrid'
                    ELSE 'esco'
                END,
                role_title = trim(role_title),
                candidate_name = trim(candidate_name)
                """
            )
        )

        # Keep most recently updated row per normalized recruiter-role-candidate-mode key.
        conn.execute(
            text(
                """
                DELETE FROM recruiter_shortlists
                WHERE id IN (
                    SELECT id FROM (
                        SELECT
                            id,
                            row_number() OVER (
                                PARTITION BY
                                    recruiter_id,
                                    lower(trim(role_title)),
                                    lower(trim(candidate_name)),
                                    lower(trim(COALESCE(analysis_mode, 'esco')))
                                ORDER BY updated_at DESC, created_at DESC, id DESC
                            ) AS rn
                        FROM recruiter_shortlists
                    ) ranked
                    WHERE rn > 1
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_shortlist_recruiter_role_candidate_mode
                ON recruiter_shortlists (recruiter_id, role_title, candidate_name, analysis_mode)
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_shortlist_recruiter_role_mode
                ON recruiter_shortlists (recruiter_id, role_title, analysis_mode)
                """
            )
        )
        return

    # MySQL-compatible cleanup and constraint creation.
    conn.execute(
        text(
            """
            UPDATE recruiter_shortlists
            SET analysis_mode = CASE
                WHEN LOWER(TRIM(COALESCE(analysis_mode, ''))) = 'hybrid' THEN 'hybrid'
                ELSE 'esco'
            END,
            role_title = TRIM(role_title),
            candidate_name = TRIM(candidate_name)
            """
        )
    )

    conn.execute(
        text(
            """
            DELETE s1 FROM recruiter_shortlists s1
            JOIN recruiter_shortlists s2
              ON s1.recruiter_id = s2.recruiter_id
             AND LOWER(TRIM(s1.role_title)) = LOWER(TRIM(s2.role_title))
             AND LOWER(TRIM(s1.candidate_name)) = LOWER(TRIM(s2.candidate_name))
             AND LOWER(TRIM(COALESCE(s1.analysis_mode, 'esco'))) = LOWER(TRIM(COALESCE(s2.analysis_mode, 'esco')))
             AND (
                    COALESCE(s1.updated_at, s1.created_at) < COALESCE(s2.updated_at, s2.created_at)
                 OR (COALESCE(s1.updated_at, s1.created_at) = COALESCE(s2.updated_at, s2.created_at) AND s1.id < s2.id)
             )
            """
        )
    )

    conn.execute(
        text(
            """
            ALTER TABLE recruiter_shortlists
            ADD CONSTRAINT uq_shortlist_recruiter_role_candidate_mode
            UNIQUE (recruiter_id, role_title, candidate_name, analysis_mode)
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE INDEX ix_shortlist_recruiter_role_mode
            ON recruiter_shortlists (recruiter_id, role_title, analysis_mode)
            """
        )
    )


MIGRATIONS: list[tuple[str, MigrationFn]] = [
    ("20260324_001_add_shortlist_analysis_mode", _migration_20260324_001_add_shortlist_analysis_mode),
    ("20260328_002_fix_turso_autoincrement_ids", _migration_20260328_002_fix_turso_autoincrement_ids),
    ("20260328_003_fix_remaining_bigint_primary_keys", _migration_20260328_002_fix_turso_autoincrement_ids),
    ("20260328_004_repair_partial_pk_fix_state", _migration_20260328_004_repair_partial_pk_fix_state),
    ("20260328_005_fix_legacy_fk_references", _migration_20260328_005_fix_legacy_fk_references),
    ("20260328_006_normalize_shortlist_json_fields", _migration_20260328_006_normalize_shortlist_json_fields),
    ("20260328_007_normalize_dashboard_state_json", _migration_20260328_007_normalize_dashboard_state_json),
    ("20260328_008_enforce_shortlist_consistency", _migration_20260328_008_enforce_shortlist_consistency),
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
