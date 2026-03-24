"""
app/routers/ml_fit.py — ML Fit Model API Endpoints
====================================================

POST /ml-fit/score           — Predict fit probability for a candidate
POST /ml-fit/score-batch     — Batch predict for multiple candidates
GET  /ml-fit/model/metadata  — Get model metadata and performance
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
import logging

from app.services.ml_fit_model import get_ml_fit_model
from app.schemas.ml_fit import (
    MLFitScoreRequest,
    MLFitScoreBatchRequest,
    MLFitScoreResponse,
    MLFitBatchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml-fit", tags=["ML Fit Model"])


@router.post("/score", response_model=MLFitScoreResponse, summary="Predict fit probability")
def score_fit(request: MLFitScoreRequest):
    """
    Predict job fit probability for a single candidate.
    
    Returns:
    - fit_class: 0 (not fit) or 1 (fit)
    - fit_probability: Continuous score 0-1
    - confidence: How confident the model is
    - feature_importance: Which features most influenced the prediction
    """
    try:
        model = get_ml_fit_model()
        
        # Check model is trained
        if not model.metadata.get("trained"):
            raise HTTPException(
                status_code=503,
                detail="ML model not trained yet. Run training script first: python3 -m scripts.train_ml_fit_model"
            )
        
        # Get prediction
        prediction = model.predict(request.analysis_result)
        
        return MLFitScoreResponse(
            candidate_id=request.candidate_id,
            fit_class=prediction["fit_class"],
            fit_probability=prediction["fit_probability"],
            confidence=prediction["confidence"],
            feature_values=prediction["feature_values"],
            feature_importance=prediction["feature_importance"],
            model_metadata={
                "model_type": model.model_type,
                "trained": model.metadata["trained"],
                "training_date": model.metadata["training_date"],
                "accuracy": model.metadata["accuracy"],
                "auc_score": model.metadata["auc_score"],
                "f1_score": model.metadata["f1_score"],
            },
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Score request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@router.post("/score-batch", response_model=MLFitBatchResponse, summary="Batch predict fit")
def score_fit_batch(request: MLFitScoreBatchRequest):
    """
    Predict fit probability for multiple candidates.
    
    Returns ranked results sorted by fit_probability (highest first).
    """
    try:
        model = get_ml_fit_model()
        
        if not model.metadata.get("trained"):
            raise HTTPException(
                status_code=503,
                detail="ML model not trained yet"
            )
        
        results = []
        for candidate_item in request.candidates:
            candidate_id = candidate_item.get("candidate_id", f"candidate_{len(results)}")
            analysis_result = candidate_item.get("analysis_result", {})
            
            try:
                prediction = model.predict(analysis_result)
                results.append(MLFitScoreResponse(
                    candidate_id=candidate_id,
                    fit_class=prediction["fit_class"],
                    fit_probability=prediction["fit_probability"],
                    confidence=prediction["confidence"],
                    feature_values=prediction["feature_values"],
                    feature_importance=prediction["feature_importance"],
                    model_metadata={
                        "model_type": model.model_type,
                        "trained": model.metadata["trained"],
                        "training_date": model.metadata["training_date"],
                        "accuracy": model.metadata["accuracy"],
                        "auc_score": model.metadata["auc_score"],
                    },
                ))
            except Exception as e:
                logger.warning(f"Failed to score {candidate_id}: {e}")
                continue
        
        # Rank by fit probability descending
        ranked = sorted(results, key=lambda x: x.fit_probability, reverse=True)
        
        return MLFitBatchResponse(results=results, ranked=ranked)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch scoring failed: {str(e)}")


@router.get("/model/metadata", summary="Get model info")
def get_model_metadata():
    """Get ML model metadata and performance metrics."""
    try:
        model = get_ml_fit_model()
        return {
            "model_type": model.model_type,
            "trained": model.metadata.get("trained", False),
            "training_date": model.metadata.get("training_date"),
            "accuracy": model.metadata.get("accuracy"),
            "auc_score": model.metadata.get("auc_score"),
            "f1_score": model.metadata.get("f1_score"),
            "samples_used": model.metadata.get("samples_count", 0),
            "feature_names": model.feature_names,
        }
    except Exception as e:
        logger.error(f"Metadata request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model metadata")
