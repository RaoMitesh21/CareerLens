#!/usr/bin/env python3
"""
scripts/train_ml_fit_model.py — Train ML Fit Model
===================================================

Trains the ML model using historical resume analysis data.

Usage:
  cd careerlens-backend
  python3 -m scripts.train_ml_fit_model --input-csv ../Datasets/Resume.csv --target-role "software developer"
"""

from __future__ import annotations

import argparse
import os
import sys
import pandas as pd
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.analyzer import hybrid_analyze
from app.services.ml_fit_model import get_ml_fit_model
from app.core.database import SessionLocal


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def train_model_from_csv(
    csv_path: str,
    target_role: str,
    resume_col: str = "Resume_str",
    name_col: str = "ID",
    fit_threshold: float = 0.5,
    max_rows: Optional[int] = None,
) -> dict:
    """
    Train ML model from resume CSV file.
    
    Args:
        csv_path: Path to Resume CSV
        target_role: Target job role (e.g., "software developer")
        resume_col: Column name containing resume text
        name_col: Column name for candidate ID
        fit_threshold: Score threshold for binary fit classification
        max_rows: Max rows to process (None = all)
        
    Returns:
        Training results dict
    """
    print("=" * 70)
    print("  CareerLens - ML Fit Model Training Pipeline")
    print("=" * 70)
    
    # Load CSV
    print(f"\n[1] Loading resume data from {csv_path}...")
    if not os.path.exists(csv_path):
        print(f"  ✗ File not found: {csv_path}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"  ✗ Failed to read CSV: {e}")
        sys.exit(1)
    
    if len(df) == 0:
        print("  ✗ CSV is empty")
        sys.exit(1)
    
    # Apply row limit
    if max_rows:
        df = df.head(max_rows)
    
    print(f"  ✓ Loaded {len(df)} resumes")
    
    # Validate columns
    if resume_col not in df.columns:
        print(f"  ✗ Column '{resume_col}' not found. Available: {list(df.columns)}")
        sys.exit(1)
    
    if name_col not in df.columns:
        name_col = df.columns[0]
        print(f"  ! Column '{name_col}' not found, using first column: {name_col}")
    
    # Prepare training data
    print(f"\n[2] Running analysis on {len(df)} resumes...")
    db = SessionLocal()
    training_data = []
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            resume_text = str(row.get(resume_col, "")).strip()
            candidate_id = str(row.get(name_col, f"candidate_{idx}"))
            
            if not resume_text or len(resume_text) < 50:
                error_count += 1
                continue
            
            # Run analysis
            try:
                analysis = hybrid_analyze(resume_text, target_role, db)
            except Exception:
                # Fallback to basic analysis
                from app.services.analyzer import basic_analyze
                analysis = basic_analyze(resume_text, target_role, db)
            
            # Create training sample
            sample = {
                "candidate_id": candidate_id,
                "analysis_result": analysis,
                # Infer fit based on score threshold
                "fit": (analysis.get("overall_score", 0) / 100.0) >= fit_threshold,
            }
            training_data.append(sample)
            success_count += 1
            
            # Progress indicator
            if (success_count + error_count) % 50 == 0:
                print(f"  Progress: {success_count + error_count}/{len(df)} processed")
        
        except Exception as e:
            error_count += 1
            if error_count <= 3:
                print(f"  Warning: Failed to analyze row {idx}: {e}")
    
    db.close()
    print(f"  ✓ Analysis complete: {success_count} success, {error_count} errors")
    
    if len(training_data) < 10:
        print(f"  ✗ Not enough valid samples ({len(training_data)}). Need at least 10.")
        sys.exit(1)
    
    # Train model
    print(f"\n[3] Training ML model on {len(training_data)} samples...")
    try:
        model = get_ml_fit_model()
        result = model.train(training_data, fit_threshold=fit_threshold)
        print(f"  ✓ Model trained successfully")
        print(f"     Train accuracy: {result['train_accuracy']:.3f}")
        print(f"     Val accuracy: {result['val_accuracy']:.3f}")
        print(f"     AUC score: {result['auc_score']:.3f}")
        print(f"     F1 score: {result['f1_score']:.3f}")
    except Exception as e:
        print(f"  ✗ Training failed: {e}")
        sys.exit(1)
    
    # Save model
    print(f"\n[4] Saving model...")
    try:
        model_path = model.save()
        print(f"  ✓ Model saved to {model_path}")
    except Exception as e:
        print(f"  ✗ Failed to save model: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ ML Fit Model training complete!")
    print("=" * 70)
    print("\nNow you can use the model for predictions:")
    print("  curl -X POST http://localhost:8000/ml-fit/score \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"analysis_result\": {...}}'")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Train ML fit model on resume analysis data"
    )
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to Resume CSV file",
    )
    parser.add_argument(
        "--target-role",
        default="software developer",
        help="Target job role for analysis (default: 'software developer')",
    )
    parser.add_argument(
        "--resume-col",
        default="Resume_str",
        help="Column name containing resume text (default: 'Resume_str')",
    )
    parser.add_argument(
        "--name-col",
        default="ID",
        help="Column name for candidate ID (default: 'ID')",
    )
    parser.add_argument(
        "--fit-threshold",
        type=float,
        default=0.5,
        help="Score threshold for fit classification (0-1, default: 0.5)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Maximum rows to process (None = all)",
    )
    
    args = parser.parse_args()
    
    try:
        train_model_from_csv(
            csv_path=args.input_csv,
            target_role=args.target_role,
            resume_col=args.resume_col,
            name_col=args.name_col,
            fit_threshold=args.fit_threshold,
            max_rows=args.max_rows,
        )
    except KeyboardInterrupt:
        print("\n\n✗ Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
