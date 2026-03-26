"""
app/core/config.py — Centralised Application Configuration
=============================================================
Single source of truth for all settings.
Reads from environment variables (.env) with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── Database ────────────────────────────────────────────────────────
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "3306")
DB_NAME: str = os.getenv("DB_NAME", "careerlens")

DEFAULT_DATABASE_URL: str = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Debug: Log which URL is being used
import sys
db_source = "environment variable (TURSO)" if os.getenv("DATABASE_URL") else "default (MySQL)"
print(f"\n📌 DATABASE_URL loaded from {db_source}", file=sys.stderr)
if DATABASE_URL.startswith("libsql://"):
    print(f"✅ Using Turso (libsql) database", file=sys.stderr)
else:
    print(f"⚠️  Using MySQL fallback (localhost)", file=sys.stderr)


# ── Application ─────────────────────────────────────────────────────
APP_TITLE: str = "CareerLens — ESCO Skill-Gap Analyzer"
APP_VERSION: str = "2.0.0"
APP_DESCRIPTION: str = (
    "Professional resume analysis powered by the ESCO taxonomy.\n\n"
    "**Capabilities:**\n"
    "- 3-tier skill classification (Core / Secondary / Bonus)\n"
    "- Confidence engine (frequency × project-context weighting)\n"
    "- Weighted scoring normalised 0–100\n"
    "- Rule-based personalised learning roadmap\n"
    "- Resume storage & history tracking\n"
)


# ── Scoring Engine ──────────────────────────────────────────────────
CALIBRATION_K: float = 4.0          # Exponential calibration factor
DEFAULT_CONFIDENCE: float = 0.5     # Fallback confidence
TIER_CORE_WEIGHT: float = 0.50      # Overall blend weights
TIER_SECONDARY_WEIGHT: float = 0.30
TIER_BONUS_WEIGHT: float = 0.20


# ── Confidence Engine ───────────────────────────────────────────────
FREQ_CAP: int = 5
FREQ_WEIGHT: float = 0.6
CONTEXT_WEIGHT: float = 0.4
CONTEXT_BONUS: float = 1.0
CONTEXT_BASE: float = 0.3
MIN_KEYWORD_LEN: int = 2
MIN_SINGLE_WORD_LEN: int = 4


# ── Roadmap Thresholds ──────────────────────────────────────────────
ROADMAP_BEGINNER_CEILING: float = 40.0
ROADMAP_INTERMEDIATE_CEILING: float = 70.0
# Anything above is advanced
