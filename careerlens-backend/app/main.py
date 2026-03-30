"""
CareerLens Backend — FastAPI Application  v2.0
================================================
Run with:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION
from app.core.database import engine, Base
from app.core.schema_migrations import run_schema_migrations
from app.services.email_provider import init_email_provider

# Import ALL models so Base.metadata registers every table
import app.models  # noqa: F401

# Import routers
from app.routers.auth import router as auth_router
from app.routers.analyze import router as analyze_router
from app.routers.occupation import router as occupation_router
from app.routers.user import router as user_router
from app.routers.resume import router as resume_router
from app.routers.roadmap import router as roadmap_router
from app.routers.bot import router as bot_router
from app.routers.contact import router as contact_router
from app.routers.newsletter import router as newsletter_router
from app.routers.recruiter_shortlist import router as recruiter_shortlist_router
from app.routers.dashboard_state import router as dashboard_state_router
from app.routers.ml_fit import router as ml_fit_router


# ── Lifespan (replaces deprecated @app.on_event) ───────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create DB tables on startup (safe – won't drop existing)."""
    Base.metadata.create_all(bind=engine)
    run_schema_migrations(engine)
    init_email_provider()

    yield


# ── Create the FastAPI app ──────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://careerlens.vercel.app",
        "https://*.vercel.app",  # Allow any Vercel preview
        "https://www.careerlens.in",
        "https://careerlens.in",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


# ── Register route modules ─────────────────────────────────────────
app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(occupation_router)
app.include_router(user_router)
app.include_router(resume_router)
app.include_router(roadmap_router)
app.include_router(bot_router)
app.include_router(contact_router)
app.include_router(newsletter_router)
app.include_router(recruiter_shortlist_router)
app.include_router(dashboard_state_router)
app.include_router(ml_fit_router)


# ── Health-check ────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "message": f"CareerLens API 🚀 v{APP_VERSION}",
        "endpoints": {
            "POST /analyze": "3-tier skill gap analysis",
            "POST /analyze/full": "Analysis + learning roadmap",
            "POST /analyze/basic": "Legacy simple scoring",
            "GET  /occupations/search": "Search ESCO occupations",
            "POST /users": "Create user",
            "POST /resumes": "Upload resume",
            "POST /roadmaps/generate": "Generate learning roadmap",
            "POST /bot/chat": "Hybrid assistant chat (coach + roadmap + recruiter)",
            "GET  /docs": "Swagger UI",
        },
    }
