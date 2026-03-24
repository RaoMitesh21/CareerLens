"""
app/routers/roadmap.py — Roadmap Endpoints
=============================================

POST /roadmaps/generate  — Generate a roadmap from a skill_score record
GET  /roadmaps/{id}      — Retrieve a stored roadmap
"""

import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import SkillScore, Roadmap as RoadmapModel
from app.schemas.roadmap import RoadmapResponse, RoadmapDetailResponse
from app.services.llm_roadmap_enhancer import InferenceMode, enhance_roadmap_async
from app.services.roadmap_generator import generate_roadmap
from app.services.roadmap_quality import enforce_roadmap_quality

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


class GenerateRoadmapRequest(BaseModel):
    """Generate a roadmap from a stored skill_score record."""
    skill_score_id: int = Field(..., description="ID of an existing SkillScore")


@router.post(
    "/generate",
    response_model=RoadmapDetailResponse,
    status_code=201,
    summary="Generate roadmap",
)
def create_roadmap(
    request: GenerateRoadmapRequest,
    db: Session = Depends(get_db),
):
    """
    Generate and persist a learning roadmap based on a stored analysis.

    If a roadmap already exists for this skill_score, it is returned instead.
    """
    score = db.query(SkillScore).filter(SkillScore.id == request.skill_score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="SkillScore not found")

    # Return existing roadmap if already generated
    if score.roadmap:
        return score.roadmap

    # Build missing skill lists from stored JSON
    missing = score.missing_skills or []
    # Approximate tier split: first 40% core, next 35% secondary, rest bonus
    n = len(missing)
    core_cut = int(n * 0.40)
    sec_cut = int(n * 0.75)
    missing_core = missing[:core_cut]
    missing_secondary = missing[core_cut:sec_cut]
    missing_bonus = missing[sec_cut:]

    roadmap_data = generate_roadmap(
        overall_score=score.overall_score,
        role=score.role.title if score.role else "Unknown Role",
        missing_core=missing_core,
        missing_secondary=missing_secondary,
        missing_bonus=missing_bonus,
    )

    # Optional LLM enhancement controlled by environment variable.
    # Supported values: mock, hf_api, local
    mode_raw = os.getenv("INFERENCE_MODE", "mock").strip().lower()
    mode_map = {
        "mock": InferenceMode.MOCK,
        "hf_api": InferenceMode.HF_API,
        "local": InferenceMode.LOCAL,
    }
    mode = mode_map.get(mode_raw, InferenceMode.MOCK)

    try:
        roadmap_data = asyncio.run(
            enhance_roadmap_async(
                base_roadmap=roadmap_data,
                role=score.role.title if score.role else "Unknown Role",
                mode=mode,
            )
        )
    except Exception:
        # Fall back to deterministic roadmap if enhancement fails.
        pass

    roadmap_data, _quality = enforce_roadmap_quality(
        roadmap=roadmap_data,
        role=score.role.title if score.role else "Unknown Role",
        missing_skills=missing,
    )

    roadmap = RoadmapModel(
        skill_score_id=score.id,
        level=roadmap_data["level"],
        title=roadmap_data["title"],
        summary=roadmap_data["summary"],
        phases=roadmap_data["phases"],
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap


@router.get("/{roadmap_id}", response_model=RoadmapDetailResponse, summary="Get roadmap")
def get_roadmap(roadmap_id: int, db: Session = Depends(get_db)):
    """Retrieve a stored roadmap by ID."""
    roadmap = db.query(RoadmapModel).filter(RoadmapModel.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap
