"""
app/core/database.py — Database Engine & Session Factory
==========================================================
Provides:
  - SQLAlchemy engine (MySQL via PyMySQL or LibSQL for Turso)
  - Session factory
  - Declarative Base for ORM models
  - get_db() dependency for FastAPI route injection
"""

# CRITICAL: Import custom Turso dialect FIRST to register dialect before SQLAlchemy uses it
try:
    from app.core.turso_dialect import SQLiteDialect_Turso
    from sqlalchemy.dialects import registry
    registry.register("libsql", "app.core.turso_dialect", "SQLiteDialect_Turso")
except ImportError:
    print("Warning: Custom Turso dialect not available, falling back to standard libsql")
    try:
        import sqlalchemy_libsql
        from sqlalchemy.dialects import registry
        registry.register("libsql", "sqlalchemy_libsql", "SQLiteDialect_libsql")
    except ImportError:
        pass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import DATABASE_URL

# ── Engine Configuration ────────────────────────────────────────────
if DATABASE_URL.startswith("libsql://"):
    # Turso/Hrana configuration with custom dialect
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        pool_pre_ping=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

# ── Session factory ─────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative base ────────────────────────────────────────────────
Base = declarative_base()


# ── FastAPI dependency ──────────────────────────────────────────────
def get_db():
    """Yield a DB session per request, auto-close on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
