"""
app/core/schema_migrations.py — Lightweight schema migrations
=============================================================
Provides a minimal migration registry for additive schema updates
without requiring Alembic in this prototype stage.
"""

from __future__ import annotations

import json
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


def _normalize_string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text_value = value.strip()
        if not text_value or text_value in {"None", "NULL"}:
            return []
        try:
            parsed = json.loads(text_value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in text_value.split(";") if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _migration_20260406_009_backfill_recruiter_normalized_tables(conn: Connection) -> None:
    inspector = inspect(conn)
    if not inspector.has_table("recruiter_shortlists"):
        return

    # Backfill shortlist skill rows from legacy JSON arrays.
    if inspector.has_table("recruiter_shortlist_skills"):
        shortlist_rows = conn.execute(
            text("SELECT id, top_strengths, top_gaps FROM recruiter_shortlists")
        ).mappings().all()
        for row in shortlist_rows:
            shortlist_id = row["id"]
            existing_count = conn.execute(
                text("SELECT 1 FROM recruiter_shortlist_skills WHERE shortlist_id = :shortlist_id LIMIT 1"),
                {"shortlist_id": shortlist_id},
            ).first()
            if existing_count:
                continue

            for skill_type, values in (("strength", _normalize_string_list(row["top_strengths"])), ("gap", _normalize_string_list(row["top_gaps"]))):
                for index, skill_name in enumerate(values):
                    conn.execute(
                        text(
                            """
                            INSERT INTO recruiter_shortlist_skills (shortlist_id, skill_type, skill_order, skill_name)
                            VALUES (:shortlist_id, :skill_type, :skill_order, :skill_name)
                            """
                        ),
                        {
                            "shortlist_id": shortlist_id,
                            "skill_type": skill_type,
                            "skill_order": index,
                            "skill_name": skill_name,
                        },
                    )

    # Backfill recruiter analysis runs from dashboard state snapshots.
    if not inspector.has_table("dashboard_states") or not inspector.has_table("recruiter_analysis_runs"):
        return

    dashboard_rows = conn.execute(
        text("SELECT user_id, state, updated_at FROM dashboard_states WHERE scope = 'recruiter'")
    ).mappings().all()

    for row in dashboard_rows:
        state_value = row["state"]
        if isinstance(state_value, str):
            try:
                state = json.loads(state_value)
            except json.JSONDecodeError:
                state = {}
        else:
            state = state_value or {}

        if not isinstance(state, dict):
            continue

        history = state.get("analysisHistory") or []
        if not history and state.get("analysisResults"):
            history = [{
                "id": state.get("savedAt") or state.get("analysisKey") or f"legacy-{row['user_id']}",
                "jobTitle": state.get("jobTitle") or "Unspecified role",
                "analysisMode": state.get("analysisMode") or "esco",
                "analyzedAtIso": None,
                "analyzedAt": state.get("savedAt") or None,
                "totalCandidates": len(state.get("analysisResults") or []),
                "shortlistedCount": len(state.get("savedShortlists") or []),
                "averageScore": state.get("analysisResults") and round(sum(float(candidate.get("overall_score") or 0) for candidate in state.get("analysisResults") or []) / max(len(state.get("analysisResults") or []), 1), 1) or 0,
                "topCandidates": state.get("analysisResults") or [],
                "shortlistedCandidates": state.get("savedShortlists") or [],
            }]

        for report in history:
            if not isinstance(report, dict):
                continue

            analysis_key = str(report.get("id") or report.get("analysisKey") or report.get("savedAt") or report.get("analyzedAt") or f"legacy-{row['user_id']}-{report.get('jobTitle')}-{report.get('analysisMode')}").strip()
            if not analysis_key:
                continue

            exists = conn.execute(
                text(
                    "SELECT 1 FROM recruiter_analysis_runs WHERE recruiter_id = :recruiter_id AND analysis_key = :analysis_key LIMIT 1"
                ),
                {"recruiter_id": row["user_id"], "analysis_key": analysis_key},
            ).first()
            if exists:
                continue

            analyzed_at = report.get("analyzedAtIso") or report.get("analyzedAt") or row["updated_at"]
            if isinstance(analyzed_at, str) and analyzed_at.endswith("Z"):
                analyzed_at = analyzed_at.replace("Z", "+00:00")

            candidate_rows = report.get("topCandidates") or report.get("candidates") or []
            shortlisted_rows = report.get("shortlistedCandidates") or []
            shortlisted_count = report.get("shortlistedCount")
            if shortlisted_count is None:
                shortlisted_count = len(shortlisted_rows)

            total_candidates = report.get("totalCandidates")
            if total_candidates is None:
                total_candidates = len(candidate_rows)

            average_score = report.get("averageScore")
            if average_score is None and candidate_rows:
                average_score = round(
                    sum(float(candidate.get("overall_score") or candidate.get("decision_score") or 0) for candidate in candidate_rows)
                    / max(len(candidate_rows), 1),
                    1,
                )
            average_score = float(average_score or 0)

            conn.execute(
                text(
                    """
                    INSERT INTO recruiter_analysis_runs
                        (recruiter_id, analysis_key, role_title, analysis_mode, total_candidates, shortlisted_count, average_score, analyzed_at)
                    VALUES
                        (:recruiter_id, :analysis_key, :role_title, :analysis_mode, :total_candidates, :shortlisted_count, :average_score, :analyzed_at)
                    """
                ),
                {
                    "recruiter_id": row["user_id"],
                    "analysis_key": analysis_key,
                    "role_title": str(report.get("jobTitle") or "Unspecified role").strip(),
                    "analysis_mode": _normalize_string_list([report.get("analysisMode") or "esco"])[0] if report.get("analysisMode") else "esco",
                    "total_candidates": int(total_candidates or 0),
                    "shortlisted_count": int(shortlisted_count or 0),
                    "average_score": average_score,
                    "analyzed_at": analyzed_at,
                },
            )

            run_id_row = conn.execute(
                text(
                    "SELECT id FROM recruiter_analysis_runs WHERE recruiter_id = :recruiter_id AND analysis_key = :analysis_key LIMIT 1"
                ),
                {"recruiter_id": row["user_id"], "analysis_key": analysis_key},
            ).first()
            if not run_id_row:
                continue
            run_id = run_id_row[0]

            for candidate_index, candidate in enumerate(candidate_rows):
                if not isinstance(candidate, dict):
                    continue

                candidate_name = str(candidate.get("candidate_name") or candidate.get("name") or f"Candidate {candidate_index + 1}").strip()
                conn.execute(
                    text(
                        """
                        INSERT INTO recruiter_analysis_candidates
                            (run_id, rank, candidate_name, resume_filename, overall_score, decision_score, core_match, secondary_match, bonus_match, match_label, risk_level, matched_count, missing_count, skill_coverage_ratio, recommendation)
                        VALUES
                            (:run_id, :rank, :candidate_name, :resume_filename, :overall_score, :decision_score, :core_match, :secondary_match, :bonus_match, :match_label, :risk_level, :matched_count, :missing_count, :skill_coverage_ratio, :recommendation)
                        """
                    ),
                    {
                        "run_id": run_id,
                        "rank": candidate.get("rank"),
                        "candidate_name": candidate_name,
                        "resume_filename": candidate.get("resume_filename") or candidate.get("filename"),
                        "overall_score": float(candidate.get("overall_score") or 0),
                        "decision_score": candidate.get("decision_score"),
                        "core_match": candidate.get("core_match"),
                        "secondary_match": candidate.get("secondary_match"),
                        "bonus_match": candidate.get("bonus_match"),
                        "match_label": candidate.get("match_label"),
                        "risk_level": candidate.get("risk_level"),
                        "matched_count": candidate.get("matched_count"),
                        "missing_count": candidate.get("missing_count"),
                        "skill_coverage_ratio": candidate.get("skill_coverage_ratio"),
                        "recommendation": candidate.get("recommendation"),
                    },
                )

                candidate_id_row = conn.execute(
                    text(
                        "SELECT id FROM recruiter_analysis_candidates WHERE run_id = :run_id AND candidate_name = :candidate_name ORDER BY id DESC LIMIT 1"
                    ),
                    {"run_id": run_id, "candidate_name": candidate_name},
                ).first()
                if not candidate_id_row:
                    continue
                candidate_id = candidate_id_row[0]

                for skill_type, skill_values in (("strength", _normalize_string_list(candidate.get("top_strengths") or candidate.get("strengths"))), ("gap", _normalize_string_list(candidate.get("top_gaps") or candidate.get("gaps")))):
                    for skill_order, skill_name in enumerate(skill_values):
                        conn.execute(
                            text(
                                """
                                INSERT INTO recruiter_analysis_candidate_skills (candidate_id, skill_type, skill_order, skill_name)
                                VALUES (:candidate_id, :skill_type, :skill_order, :skill_name)
                                """
                            ),
                            {
                                "candidate_id": candidate_id,
                                "skill_type": skill_type,
                                "skill_order": skill_order,
                                "skill_name": skill_name,
                            },
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
    ("20260406_009_backfill_recruiter_normalized_tables", _migration_20260406_009_backfill_recruiter_normalized_tables),
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
