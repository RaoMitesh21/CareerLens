"""
app/services/ml_fit_model.py — ML-Based Job Fit Scoring Service
==================================================================

Trains a machine learning model to predict recruiter fit (success probability)
based on resume analysis scores. Uses scikit-learn for model training and inference.

Training data: Historical resume analysis results + recruiter outcomes
Features: ESCO match score, O*NET match score, skill gap metrics, etc.
Target: Binary (fit/no-fit) or continuous (fit probability 0-1)

Models supported:
  - Logistic Regression (default, fast, interpretable)
  - Random Forest (more complex, better non-linearity)
"""

from __future__ import annotations

import os
import pickle
import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_curve, f1_score
import numpy as np

logger = logging.getLogger(__name__)

# Model persistence directories
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "..", "ml_models"
)
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "fit_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "fit_scaler.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "fit_metadata.json")


class MLFitModel:
    """Machine learning model for predicting job fit probability."""
    
    def __init__(self, model_type: str = "logistic_regression"):
        """
        Initialize ML fit model.
        
        Args:
            model_type: "logistic_regression" or "random_forest"
        """
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.metadata = {
            "model_type": model_type,
            "trained": False,
            "training_date": None,
            "accuracy": None,
            "auc_score": None,
            "f1_score": None,
            "samples_count": 0,
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Create model instance based on type."""
        if self.model_type == "logistic_regression":
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight="balanced",  # Handle class imbalance
            )
        elif self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight="balanced",
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        self.scaler = StandardScaler()
    
    def extract_features(self, analysis_result: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features from an analysis result.
        
        Args:
            analysis_result: Result dict from /analyze or /analyze/hybrid
            
        Returns:
            Feature dict with normalized values
        """
        features = {
            "overall_score": analysis_result.get("overall_score", 0.0) / 100.0,
            "core_match": analysis_result.get("core_match", 0.0) / 100.0,
            "secondary_match": analysis_result.get("secondary_match", 0.0) / 100.0,
            "bonus_match": analysis_result.get("bonus_match", 0.0) / 100.0,
            "strengths_count": len(analysis_result.get("strengths", [])),
            "matched_skills_count": len(analysis_result.get("matched_skills", [])),
            "missing_skills_count": len(analysis_result.get("missing_skills", [])),
            "confidence_score": analysis_result.get("confidence", 0.5),
        }
        
        # Add hybrid-specific features if available
        if "onet_score" in analysis_result:
            features["onet_score"] = analysis_result["onet_score"] / 100.0
            features["fused_score"] = analysis_result.get("fused_score", 0.0) / 100.0
        
        return features
    
    def prepare_training_data(
        self,
        data: list[dict],
        fit_threshold: float = 0.5
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from analysis results.
        
        Args:
            data: List of {"analysis_result": {...}, "fit": bool} dicts
            fit_threshold: ESCO score threshold to consider as fit
            
        Returns:
            (X, y) numpy arrays
        """
        if not data:
            raise ValueError("No training data provided")
        
        X_list = []
        y_list = []
        
        for sample in data:
            try:
                features = self.extract_features(sample.get("analysis_result", {}))
                
                # If explicit fit label provided, use it; otherwise infer from score
                if "fit" in sample:
                    fit_label = 1 if sample["fit"] else 0
                else:
                    overall_score = sample.get("analysis_result", {}).get("overall_score", 0)
                    fit_label = 1 if (overall_score / 100.0) >= fit_threshold else 0
                
                X_list.append(list(features.values()))
                y_list.append(fit_label)
                
            except Exception as e:
                logger.warning(f"Failed to process training sample: {e}")
                continue
        
        if not X_list:
            raise ValueError("No valid training samples extracted")
        
        self.feature_names = list(self.extract_features({}).keys())
        X = np.array(X_list)
        y = np.array(y_list)
        
        return X, y
    
    def train(
        self,
        data: list[dict],
        fit_threshold: float = 0.5,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Train the ML model on historical data.
        
        Args:
            data: Training data
            fit_threshold: Score threshold for binary classification
            test_size: Validation set size
            
        Returns:
            Training metrics dict
        """
        try:
            # Prepare data
            X, y = self.prepare_training_data(data, fit_threshold)
            
            # Split train/val
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            val_score = self.model.score(X_val_scaled, y_val)
            
            # Get predictions and probabilities
            y_pred = self.model.predict(X_val_scaled)
            y_proba = self.model.predict_proba(X_val_scaled)[:, 1]
            
            # Compute metrics
            auc = roc_auc_score(y_val, y_proba)
            f1 = f1_score(y_val, y_pred)
            
            # Update metadata
            self.metadata["trained"] = True
            self.metadata["training_date"] = datetime.now().isoformat()
            self.metadata["accuracy"] = float(val_score)
            self.metadata["auc_score"] = float(auc)
            self.metadata["f1_score"] = float(f1)
            self.metadata["samples_count"] = len(X)
            
            logger.info(f"Model trained: accuracy={val_score:.3f}, AUC={auc:.3f}, F1={f1:.3f}")
            
            return {
                "status": "success",
                "train_accuracy": float(train_score),
                "val_accuracy": float(val_score),
                "auc_score": float(auc),
                "f1_score": float(f1),
                "samples_used": len(X),
            }
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def predict(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict fit probability for a candidate.
        
        Args:
            analysis_result: Result dict from analysis endpoint
            
        Returns:
            Prediction dict with fit_probability, fit_class, and confidence
        """
        if not self.metadata.get("trained"):
            raise RuntimeError("Model not trained. Call train() first.")
        
        try:
            # Extract and scale features
            features = self.extract_features(analysis_result)
            X = np.array([list(features.values())])
            X_scaled = self.scaler.transform(X)
            
            # Get prediction
            fit_class = self.model.predict(X_scaled)[0]
            fit_probability = self.model.predict_proba(X_scaled)[0][1]
            
            # Get feature importance if available
            feature_importance = None
            if hasattr(self.model, "coef_"):
                # Logistic regression coefficients
                feature_importance = {}
                for i, name in enumerate(self.feature_names):
                    feature_importance[name] = float(self.model.coef_[0][i])
            elif hasattr(self.model, "feature_importances_"):
                # Random forest importances
                feature_importance = {}
                for i, name in enumerate(self.feature_names):
                    feature_importance[name] = float(self.model.feature_importances_[i])
            
            return {
                "fit_class": int(fit_class),  # 0 = not fit, 1 = fit
                "fit_probability": float(fit_probability),
                "confidence": float(abs(fit_probability - 0.5) * 2),  # Higher near 0 or 1
                "feature_values": {name: float(val) for name, val in features.items()},
                "feature_importance": feature_importance,
            }
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
    
    def save(self) -> str:
        """Save model to disk."""
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            
            with open(SCALER_PATH, "wb") as f:
                pickle.dump(self.scaler, f)
            
            with open(METADATA_PATH, "w") as f:
                json.dump(self.metadata, f, indent=2)
            
            logger.info(f"Model saved to {MODEL_PATH}")
            return MODEL_PATH
        except Exception as e:
            logger.error(f"Save failed: {e}")
            raise
    
    def load(self) -> bool:
        """Load model from disk."""
        try:
            if not all(os.path.exists(p) for p in [MODEL_PATH, SCALER_PATH, METADATA_PATH]):
                logger.warning("Model files not found on disk")
                return False
            
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            
            with open(METADATA_PATH, "r") as f:
                self.metadata = json.load(f)
            
            logger.info(f"Model loaded from {MODEL_PATH}")
            return True
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False


# Singleton instance
_model_instance: Optional[MLFitModel] = None


def get_ml_fit_model() -> MLFitModel:
    """Get or create the ML fit model singleton."""
    global _model_instance
    if _model_instance is None:
        _model_instance = MLFitModel(model_type="logistic_regression")
        # Try to load pre-trained model
        _model_instance.load()
    return _model_instance
