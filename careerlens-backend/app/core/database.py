"""
app/core/database.py — Database Engine & Session Factory
==========================================================
Provides:
  - SQLAlchemy engine (MySQL via PyMySQL or LibSQL for Turso)
  - Session factory
  - Declarative Base for ORM models
  - get_db() dependency for FastAPI route injection
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# IMPORTANT: Register libsql dialect for Turso support
try:
    import sqlalchemy_libsql  # noqa: F401
except ImportError:
    pass

from app.core.config import DATABASE_URL

# ── Engine ──────────────────────────────────────────────────────────
# For Turso/libsql, disable connection pooling and set connect_args
if DATABASE_URL.startswith("libsql://"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=NullPool  # Disable pooling for libsql
    )
else:
    # MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

# ── Session factory ─────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative base — all models inherit from this ─────────────────
Base = declarative_base()


# ── FastAPI dependency ──────────────────────────────────────────────
def get_db():
    """Yield a DB session per request, auto-close on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
