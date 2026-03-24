"""
app/schemas/occupation.py — Occupation Search Schemas
=======================================================
"""

from pydantic import BaseModel
from typing import Optional


class OccupationSearchResult(BaseModel):
    """One occupation in search results."""
    esco_id: Optional[str] = None
    preferred_label: str
    description: Optional[str] = None


class HybridOccupationSearchResult(BaseModel):
    """One occupation result from ESCO or O*NET source."""
    source: str
    preferred_label: str
    description: Optional[str] = None
    esco_id: Optional[str] = None
    onet_code: Optional[str] = None
