"""
app/schemas/user.py — User Schemas
=====================================
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreateRequest(BaseModel):
    """Create a new user."""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)


class UserResponse(BaseModel):
    """User record response."""
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserDetailResponse(BaseModel):
    """User with resume count."""
    id: int
    name: str
    email: str
    resume_count: int = 0
    created_at: datetime
