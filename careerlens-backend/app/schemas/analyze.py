"""
app/schemas/analyze.py — Analysis Request & Response Schemas
==============================================================
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ── Request ─────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    """Input for resume analysis."""

    resume_text: str = Field(..., min_length=20, description="Full resume text")
    target_occupation: str = Field(..., min_length=2, description="Target role title")
    user_id: Optional[int] = Field(None, description="Optional user ID to persist results")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "resume_text": (
                        "EXPERIENCE\n"
                        "Software Engineer at Acme Corp (2020-2024)\n"
                        "- Built REST APIs using Python and FastAPI\n"
                        "- Managed CI/CD pipelines with Jenkins and Docker\n\n"
                        "SKILLS\n"
                        "Python, JavaScript, SQL, Docker, Git"
                    ),
                    "target_occupation": "software developer",
                }
            ]
        }
    }


# ── Sub-models ──────────────────────────────────────────────────────
class ImprovementItem(BaseModel):
    """One missing skill with its priority level."""
    skill: str
    priority: str = Field(..., description="High / Medium / Low")


class SkillConfidenceItem(BaseModel):
    """Confidence detail for one matched skill."""
    skill: str
    mentions: int = Field(..., description="Keyword frequency in resume")
    in_project_context: bool = Field(..., description="Found in project/experience section")
    confidence: float = Field(..., ge=0, le=1, description="Blended score 0→1")


class AnalysisMeta(BaseModel):
    """Metadata about the analysis run."""
    total_required_skills: int
    core_skills_count: int
    secondary_skills_count: int
    bonus_skills_count: int
    total_matched: int
    total_missing: int


class LLMInsights(BaseModel):
    """Optional AI-generated insights for analytics and tips sections."""
    analytics_summary: str
    tips: List[str] = []
    priority_actions: List[str] = []


# ── Responses ───────────────────────────────────────────────────────
class GapAnalysisResponse(BaseModel):
    """
    Full skill-gap analysis result — the primary response shape.

    Includes 3-tier scoring, strengths, gaps, confidence details,
    improvement priorities, and a human-readable summary.
    """

    role: str
    overall_score: float = Field(..., ge=0, le=100)
    core_match: float = Field(..., ge=0, le=100, description="Core/mandatory skill coverage %")
    secondary_match: float = Field(..., ge=0, le=100, description="Secondary knowledge coverage %")
    bonus_match: float = Field(..., ge=0, le=100, description="Bonus/tool coverage %")
    matched_skills: List[str]
    missing_skills: List[str]
    strengths: List[str]
    improvement_priority: List[ImprovementItem]
    skill_confidence: List[SkillConfidenceItem]
    analysis_summary: str
    llm_insights: Optional[LLMInsights] = None
    meta: AnalysisMeta


class AnalyzeWithRoadmapResponse(BaseModel):
    """Combined analysis + roadmap in a single response."""

    analysis: GapAnalysisResponse
    roadmap: "RoadmapResponse"   # forward ref resolved at runtime


class HybridOnetMeta(BaseModel):
    """O*NET alignment details used in hybrid scoring."""
    available: bool
    reason: Optional[str] = None
    matched_role: Optional[str] = None
    role_match_score: float = 0.0
    skill_match_score: float = 0.0
    total_skills: int = 0
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    match_breakdown: dict = {}
    matched_via_alias: List[str] = []


class HybridAnalyzeResponse(BaseModel):
    """ESCO primary analysis enriched with O*NET auxiliary alignment."""
    analysis: GapAnalysisResponse
    fused_score: float = Field(..., ge=0, le=100)
    fusion_strategy: str
    onet: HybridOnetMeta


# ── Legacy ──────────────────────────────────────────────────────────
class SkillCoverage(BaseModel):
    essential_percent: float = 0.0
    optional_percent: float = 0.0


class MatchedSkillsBasic(BaseModel):
    essential: List[str] = []
    optional: List[str] = []


class MissingSkillsBasic(BaseModel):
    essential: List[str] = []
    optional: List[str] = []


class BasicAnalyzeResponse(BaseModel):
    """Legacy v0.2 response shape (kept for backward compatibility)."""
    role: str
    match_score: float = Field(..., ge=0, le=100)
    readiness_level: str
    coverage: SkillCoverage
    matched_skills: MatchedSkillsBasic
    missing_skills: MissingSkillsBasic
    critical_gaps: List[str] = []


# ── Forward-ref import (must be at bottom) ──────────────────────────
from app.schemas.roadmap import RoadmapResponse  # noqa: E402


# ── Batch Analysis Schemas ───────────────────────────────────────────
class BatchResumeItem(BaseModel):
    """One candidate's resume in a batch request."""
    resume_text: str = Field(..., min_length=10, description="Full resume text")
    candidate_name: str = Field("", description="Candidate display name")


class BatchAnalyzeRequest(BaseModel):
    """Batch analysis request — up to 10 resumes vs one target role."""
    resumes: List[BatchResumeItem] = Field(..., min_length=1, max_length=10)
    target_occupation: str = Field(..., min_length=2)


class CandidateSkillBucket(BaseModel):
    """Matched and missing skills for one bucket."""
    matched: List[str] = []
    missing: List[str] = []


class CandidateSkillClassification(BaseModel):
    """Detailed candidate skill grouping used by recruiter dashboard."""
    core: CandidateSkillBucket
    language: CandidateSkillBucket
    other: CandidateSkillBucket


class ComprehensiveClassification(BaseModel):
    """High-level candidate disposition for hiring prioritization."""
    label: str
    summary: str


class BatchCandidateResult(BaseModel):
    """Analysis summary of one candidate in a batch result."""
    candidate_name: str
    rank: int
    overall_score: float
    decision_score: float
    core_match: float
    secondary_match: float
    bonus_match: float
    matched_count: int
    missing_count: int
    skill_coverage_ratio: float
    match_label: str = Field(..., description="Excellent / Good / Fair / Weak")
    risk_level: str = Field(..., description="Low / Medium / High")
    recommendation: str = Field(..., description="Strong Shortlist / Shortlist / Review / Hold")
    comprehensive_classification: ComprehensiveClassification
    skill_classification: CandidateSkillClassification
    top_strengths: List[str]
    top_gaps: List[str]


class BatchAnalyzeResponse(BaseModel):
    """Ranked list of candidates for a target role."""
    target_role: str
    total_candidates: int
    candidates: List[BatchCandidateResult]

AnalyzeWithRoadmapResponse.model_rebuild()
