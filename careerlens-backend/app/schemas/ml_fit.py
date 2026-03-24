"""
app/schemas/ml_fit.py — ML Fit Model Schemas
=============================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MLFitScoreRequest(BaseModel):
    """Request to score a candidate's fit."""
    analysis_result: Dict[str, Any] = Field(..., description="Result from /analyze or /analyze/hybrid")
    candidate_id: Optional[str] = Field(None, description="Optional candidate identifier")


class MLFitScoreBatchRequest(BaseModel):
    """Batch request to score multiple candidates."""
    candidates: List[Dict[str, Any]] = Field(..., description="List of {candidate_id, analysis_result}")


class MLFitScoreResponse(BaseModel):
    """Fit score prediction result."""
    candidate_id: Optional[str] = None
    fit_class: int = Field(..., description="0=not fit, 1=fit")
    fit_probability: float = Field(..., description="Probability score 0-1")
    confidence: float = Field(..., description="Confidence 0-1")
    feature_values: Dict[str, float] = Field(..., description="Extracted features")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Feature importance scores")
    model_metadata: Dict[str, Any] = Field(..., description="Model info")


class MLFitBatchResponse(BaseModel):
    """Batch scoring response."""
    results: List[MLFitScoreResponse]
    ranked: List[MLFitScoreResponse] = Field(..., description="Ranked by fit_probability desc")


class MLFitModelMetadata(BaseModel):
    """ML model metadata and performance."""
    model_type: str
    trained: bool
    training_date: Optional[str]
    accuracy: Optional[float]
    auc_score: Optional[float]
    f1_score: Optional[float]
    samples_used: int
    feature_names: Optional[List[str]]
