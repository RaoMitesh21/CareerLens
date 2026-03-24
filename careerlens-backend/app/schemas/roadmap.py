"""
app/schemas/roadmap.py — Roadmap Schemas
==========================================
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RoadmapPhase(BaseModel):
    """One phase of a learning roadmap."""
    phase: int = Field(..., description="Phase number (1, 2, 3…)")
    title: str
    duration: str = Field(..., description="e.g. 'Weeks 1–4'")
    focus_area: str
    skills_to_learn: List[str]
    suggested_actions: List[str]
    enhanced_description: Optional[str] = None
    learning_objectives: List[str] = Field(default_factory=list)
    recommended_resources: List[str] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    """A structured learning roadmap."""
    level: str = Field(..., description="beginner / intermediate / advanced")
    title: str
    summary: str
    timeline_months: Optional[int] = None
    phases: List[RoadmapPhase]
    ai_enhanced: Optional[bool] = False
    inference_mode: Optional[str] = None


class RoadmapDetailResponse(BaseModel):
    """Roadmap stored in DB with timestamps."""
    id: int
    skill_score_id: int
    level: str
    title: str
    summary: Optional[str] = None
    phases: List[RoadmapPhase]
    created_at: datetime

    model_config = {"from_attributes": True}
