"""
app/schemas/resume.py — Resume Schemas
========================================
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResumeUploadRequest(BaseModel):
    """Upload a resume (text) linked to a user."""
    user_id: int
    resume_text: str = Field(..., min_length=20, description="Full resume text")
    filename: Optional[str] = Field(None, description="Original filename if available")


class ResumeResponse(BaseModel):
    """Stored resume record."""
    id: int
    user_id: int
    filename: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeDetailResponse(BaseModel):
    """Resume with full text."""
    id: int
    user_id: int
    raw_text: str
    filename: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
