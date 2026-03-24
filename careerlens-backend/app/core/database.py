"""
app/core/database.py — Database Engine & Session Factory
==========================================================
Provides:
  - SQLAlchemy engine (MySQL via PyMySQL)
  - Session factory
  - Declarative Base for ORM models
  - get_db() dependency for FastAPI route injection
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import DATABASE_URL

# ── Engine ──────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

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
