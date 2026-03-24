"""
app/routers/recruiter_shortlist.py — Recruiter shortlist endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import RecruiterShortlist, User, UserRole
from app.schemas.recruiter_shortlist import (
    RecruiterShortlistCreateRequest,
    RecruiterShortlistResponse,
)
from app.services.auth_utils import verify_token

router = APIRouter(prefix="/recruiter/shortlists", tags=["Recruiter Shortlists"])
security = HTTPBearer(auto_error=False)


def _normalize_analysis_mode(mode: Optional[str]) -> str:
    return "hybrid" if str(mode or "").strip().lower() == "hybrid" else "esco"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Resolve authenticated user from Bearer JWT."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(
        User.id == int(sub),
        User.is_active == True,
        User.is_deleted == False,
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_recruiter(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the caller has recruiter role."""
    if current_user.role != UserRole.RECRUITER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required",
        )
    return current_user


@router.get("", response_model=list[RecruiterShortlistResponse])
def list_shortlists(
    role: Optional[str] = Query(None, description="Optional role title filter"),
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """Get saved shortlist entries for the authenticated recruiter."""
    query = db.query(RecruiterShortlist).filter(
        RecruiterShortlist.recruiter_id == current_user.id,
    )

    if role:
        query = query.filter(RecruiterShortlist.role_title == role)

    return query.order_by(RecruiterShortlist.created_at.desc()).all()


@router.post("", response_model=RecruiterShortlistResponse)
def upsert_shortlist(
    request: RecruiterShortlistCreateRequest,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """Save one shortlisted candidate for the authenticated recruiter."""
    existing = db.query(RecruiterShortlist).filter(
        RecruiterShortlist.recruiter_id == current_user.id,
        RecruiterShortlist.role_title == request.role_title.strip(),
        RecruiterShortlist.candidate_name == request.candidate_name.strip(),
    ).first()

    if existing:
        existing.rank = request.rank
        existing.overall_score = request.overall_score
        existing.core_match = request.core_match
        existing.secondary_match = request.secondary_match
        existing.bonus_match = request.bonus_match
        existing.match_label = request.match_label
        existing.analysis_mode = _normalize_analysis_mode(request.analysis_mode)
        existing.top_strengths = request.top_strengths
        existing.top_gaps = request.top_gaps
        db.commit()
        db.refresh(existing)
        return existing

    entry = RecruiterShortlist(
        recruiter_id=current_user.id,
        role_title=request.role_title.strip(),
        candidate_name=request.candidate_name.strip(),
        rank=request.rank,
        overall_score=request.overall_score,
        core_match=request.core_match,
        secondary_match=request.secondary_match,
        bonus_match=request.bonus_match,
        match_label=request.match_label,
        analysis_mode=_normalize_analysis_mode(request.analysis_mode),
        top_strengths=request.top_strengths,
        top_gaps=request.top_gaps,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{shortlist_id}", status_code=204)
def delete_shortlist(
    shortlist_id: int,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """Delete one shortlist entry owned by the authenticated recruiter."""
    entry = db.query(RecruiterShortlist).filter(
        RecruiterShortlist.id == shortlist_id,
        RecruiterShortlist.recruiter_id == current_user.id,
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")

    db.delete(entry)
    db.commit()
    return Response(status_code=204)
