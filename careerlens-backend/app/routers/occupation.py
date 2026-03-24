"""
app/routers/occupation.py — Occupation Search Endpoints
=========================================================

GET /occupations/search — Search ESCO occupations by keyword
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.models.esco import Occupation
from app.models.onet import OnetOccupation
from app.schemas.occupation import OccupationSearchResult, HybridOccupationSearchResult

router = APIRouter(prefix="/occupations", tags=["Occupations"])


@router.get(
    "/search",
    response_model=list[OccupationSearchResult],
    summary="Search ESCO occupations",
)
def search_occupations(
    q: str = Query(..., min_length=2, description="Search term (e.g. 'software', 'data')"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    db: Session = Depends(get_db),
):
    """
    Search for ESCO occupation titles.
    Use this to find the exact role name before calling /analyze.
    Returns up to `limit` matches sorted by preference.
    """
    try:
        # Safe case-insensitive search across occupation titles
        results = (
            db.query(Occupation)
            .filter(Occupation.preferred_label.ilike(f"%{q}%"))
            .order_by(Occupation.preferred_label)
            .limit(limit)
            .all()
        )
        
        # Convert results to response schema with safe defaults
        return [
            OccupationSearchResult(
                esco_id=r.esco_id or "",
                preferred_label=r.preferred_label or q,
                description=r.description or "",
            )
            for r in results
        ]
    except SQLAlchemyError as e:
        # Log DB error and return empty list (graceful fallback)
        print(f"Database error in occupation search: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database error during occupation search. Please try again."
        )
    except Exception as e:
        # Catch any other errors
        print(f"Unexpected error in occupation search: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching occupations."
        )


@router.get(
    "/search/hybrid",
    response_model=list[HybridOccupationSearchResult],
    summary="Search occupations across ESCO + O*NET",
)
def search_occupations_hybrid(
    q: str = Query(..., min_length=2, description="Search term (e.g. 'software', 'data')"),
    limit: int = Query(15, ge=1, le=100, description="Max merged results"),
    db: Session = Depends(get_db),
):
    """
    Additive hybrid search endpoint:
    - keeps existing /occupations/search untouched
    - merges ESCO and O*NET role candidates for better recall.
    """
    try:
        esco_rows = (
            db.query(Occupation)
            .filter(Occupation.preferred_label.ilike(f"%{q}%"))
            .order_by(Occupation.preferred_label)
            .limit(limit)
            .all()
        )

        onet_rows = (
            db.query(OnetOccupation)
            .filter(OnetOccupation.title.ilike(f"%{q}%"))
            .order_by(OnetOccupation.title)
            .limit(limit)
            .all()
        )

        merged: list[HybridOccupationSearchResult] = []
        seen_labels: set[str] = set()

        for row in esco_rows:
            label = (row.preferred_label or "").strip()
            if not label:
                continue
            key = label.lower()
            if key in seen_labels:
                continue
            seen_labels.add(key)
            merged.append(
                HybridOccupationSearchResult(
                    source="esco",
                    preferred_label=label,
                    description=row.description or "",
                    esco_id=row.esco_id,
                )
            )

        for row in onet_rows:
            label = (row.title or "").strip()
            if not label:
                continue
            key = label.lower()
            if key in seen_labels:
                continue
            seen_labels.add(key)
            merged.append(
                HybridOccupationSearchResult(
                    source="onet",
                    preferred_label=label,
                    description=row.description or "",
                    onet_code=row.onet_code,
                )
            )

        return merged[:limit]
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500, detail=f"Database error during hybrid search: {err}")
