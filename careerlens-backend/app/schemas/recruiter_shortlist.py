"""
app/schemas/recruiter_shortlist.py — Recruiter shortlist schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RecruiterShortlistCreateRequest(BaseModel):
    """Create or update one shortlist entry for the current recruiter."""

    role_title: str = Field(..., min_length=2, max_length=512)
    candidate_name: str = Field(..., min_length=1, max_length=255)
    rank: Optional[int] = None
    overall_score: Optional[float] = None
    core_match: Optional[float] = None
    secondary_match: Optional[float] = None
    bonus_match: Optional[float] = None
    match_label: Optional[str] = None
    analysis_mode: Optional[str] = None
    top_strengths: List[str] = Field(default_factory=list)
    top_gaps: List[str] = Field(default_factory=list)


class RecruiterShortlistResponse(BaseModel):
    """Shortlist record response."""

    id: int
    recruiter_id: int
    role_title: str
    candidate_name: str
    rank: Optional[int] = None
    overall_score: Optional[float] = None
    core_match: Optional[float] = None
    secondary_match: Optional[float] = None
    bonus_match: Optional[float] = None
    match_label: Optional[str] = None
    analysis_mode: Optional[str] = None
    top_strengths: List[str] = Field(default_factory=list)
    top_gaps: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
