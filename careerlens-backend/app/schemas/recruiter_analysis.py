"""
app/schemas/recruiter_analysis.py — Recruiter analysis history schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RecruiterAnalysisSkillBase(BaseModel):
    skill_type: str = Field(..., pattern="^(strength|gap)$")
    skill_order: int = Field(..., ge=0)
    skill_name: str = Field(..., min_length=1, max_length=255)


class RecruiterAnalysisCandidateCreateRequest(BaseModel):
    rank: Optional[int] = None
    candidate_name: str = Field(..., min_length=1, max_length=255)
    resume_filename: Optional[str] = Field(default=None, max_length=255)
    overall_score: float = 0.0
    decision_score: Optional[float] = None
    core_match: Optional[float] = None
    secondary_match: Optional[float] = None
    bonus_match: Optional[float] = None
    match_label: Optional[str] = None
    risk_level: Optional[str] = None
    matched_count: Optional[int] = None
    missing_count: Optional[int] = None
    skill_coverage_ratio: Optional[float] = None
    recommendation: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


class RecruiterAnalysisRunCreateRequest(BaseModel):
    analysis_key: str = Field(..., min_length=3, max_length=255)
    role_title: str = Field(..., min_length=2, max_length=512)
    analysis_mode: str = Field(default="esco", min_length=3, max_length=16)
    analyzed_at: Optional[datetime] = None
    total_candidates: int = Field(default=0, ge=0)
    shortlisted_count: int = Field(default=0, ge=0)
    average_score: float = 0.0
    candidates: List[RecruiterAnalysisCandidateCreateRequest] = Field(default_factory=list)


class RecruiterAnalysisCandidateSkillResponse(RecruiterAnalysisSkillBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RecruiterAnalysisCandidateResponse(RecruiterAnalysisCandidateCreateRequest):
    id: int
    run_id: int
    created_at: datetime
    updated_at: datetime
    strengths: List[RecruiterAnalysisCandidateSkillResponse] = Field(default_factory=list)
    gaps: List[RecruiterAnalysisCandidateSkillResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RecruiterAnalysisRunResponse(BaseModel):
    id: int
    recruiter_id: int
    analysis_key: str
    role_title: str
    analysis_mode: str
    total_candidates: int
    shortlisted_count: int
    average_score: float
    analyzed_at: datetime
    created_at: datetime
    updated_at: datetime
    candidates: List[RecruiterAnalysisCandidateResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}