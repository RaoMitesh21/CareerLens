"""
app/routers/recruiter_shortlist.py — Recruiter shortlist endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import RecruiterShortlist, RecruiterShortlistSkill, User, UserRole
from app.schemas.recruiter_shortlist import (
    RecruiterShortlistCreateRequest,
    RecruiterShortlistResponse,
)
from app.services.auth_utils import verify_token

router = APIRouter(prefix="/recruiter/shortlists", tags=["Recruiter Shortlists"])
security = HTTPBearer(auto_error=False)


def _normalize_analysis_mode(mode: Optional[str]) -> str:
    return "hybrid" if str(mode or "").strip().lower() == "hybrid" else "esco"


def _normalize_key(value: str) -> str:
    # Keep persisted display text readable while normalizing matching behavior.
    return " ".join((value or "").strip().split())


def _coerce_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text or text in {"None", "NULL"}:
            return []
        return [item.strip() for item in text.split(";") if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _shortlist_skills_table_available(db: Session) -> bool:
    try:
        bind = db.get_bind()
        if bind is None:
            return False
        return inspect(bind).has_table("recruiter_shortlist_skills")
    except Exception:
        return False


def _serialize_shortlist(entry: RecruiterShortlist, include_skill_rows: bool = True) -> dict:
    skill_rows = list(getattr(entry, "shortlist_skills", []) or []) if include_skill_rows else []
    return {
        "id": entry.id,
        "recruiter_id": entry.recruiter_id,
        "role_title": (entry.role_title or "").strip(),
        "candidate_name": (entry.candidate_name or "").strip(),
        "rank": entry.rank,
        "overall_score": entry.overall_score,
        "core_match": entry.core_match,
        "secondary_match": entry.secondary_match,
        "bonus_match": entry.bonus_match,
        "match_label": entry.match_label,
        "analysis_mode": _normalize_analysis_mode(entry.analysis_mode),
        "top_strengths": [
            skill.skill_name
            for skill in sorted(
                [row for row in skill_rows if row.skill_type == "strength"],
                key=lambda item: item.skill_order,
            )
        ] or _coerce_list(entry.top_strengths),
        "top_gaps": [
            skill.skill_name
            for skill in sorted(
                [row for row in skill_rows if row.skill_type == "gap"],
                key=lambda item: item.skill_order,
            )
        ] or _coerce_list(entry.top_gaps),
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


def _replace_shortlist_skills(db: Session, shortlist_id: int, strengths: list[str], gaps: list[str]) -> None:
    db.query(RecruiterShortlistSkill).filter(RecruiterShortlistSkill.shortlist_id == shortlist_id).delete(synchronize_session=False)

    for index, skill_name in enumerate(strengths):
        db.add(RecruiterShortlistSkill(shortlist_id=shortlist_id, skill_type="strength", skill_order=index, skill_name=skill_name))

    for index, skill_name in enumerate(gaps):
        db.add(RecruiterShortlistSkill(shortlist_id=shortlist_id, skill_type="gap", skill_order=index, skill_name=skill_name))


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
    include_skill_rows = _shortlist_skills_table_available(db)
    query = db.query(RecruiterShortlist).filter(
        RecruiterShortlist.recruiter_id == current_user.id,
    )
    if include_skill_rows:
        query = query.options(joinedload(RecruiterShortlist.shortlist_skills))

    if role:
        normalized_role = _normalize_key(role).lower()
        query = query.filter(func.lower(func.trim(RecruiterShortlist.role_title)) == normalized_role)

    try:
        entries = query.order_by(RecruiterShortlist.created_at.desc()).all()
        return [_serialize_shortlist(entry, include_skill_rows=include_skill_rows) for entry in entries]
    except SQLAlchemyError:
        fallback_query = db.query(RecruiterShortlist).filter(
            RecruiterShortlist.recruiter_id == current_user.id,
        )
        if role:
            normalized_role = _normalize_key(role).lower()
            fallback_query = fallback_query.filter(func.lower(func.trim(RecruiterShortlist.role_title)) == normalized_role)
        entries = fallback_query.order_by(RecruiterShortlist.created_at.desc()).all()
        return [_serialize_shortlist(entry, include_skill_rows=False) for entry in entries]


@router.post("", response_model=RecruiterShortlistResponse)
def upsert_shortlist(
    request: RecruiterShortlistCreateRequest,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db),
):
    """Save one shortlisted candidate for the authenticated recruiter."""
    normalized_role_title = _normalize_key(request.role_title)
    normalized_candidate_name = _normalize_key(request.candidate_name)
    normalized_mode = _normalize_analysis_mode(request.analysis_mode)
    normalized_strengths = _coerce_list(request.top_strengths)
    normalized_gaps = _coerce_list(request.top_gaps)
    include_skill_rows = _shortlist_skills_table_available(db)

    existing = db.query(RecruiterShortlist).filter(
        RecruiterShortlist.recruiter_id == current_user.id,
        func.lower(func.trim(RecruiterShortlist.role_title)) == normalized_role_title.lower(),
        func.lower(func.trim(RecruiterShortlist.candidate_name)) == normalized_candidate_name.lower(),
        func.lower(func.trim(func.coalesce(RecruiterShortlist.analysis_mode, "esco"))) == normalized_mode,
    ).first()

    if existing:
        existing.rank = request.rank
        existing.overall_score = request.overall_score
        existing.core_match = request.core_match
        existing.secondary_match = request.secondary_match
        existing.bonus_match = request.bonus_match
        existing.match_label = request.match_label
        existing.analysis_mode = normalized_mode
        existing.top_strengths = normalized_strengths
        existing.top_gaps = normalized_gaps
        db.flush()
        if include_skill_rows:
            _replace_shortlist_skills(db, existing.id, normalized_strengths, normalized_gaps)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save shortlist")
        db.refresh(existing)
        return _serialize_shortlist(existing, include_skill_rows=include_skill_rows)

    entry = RecruiterShortlist(
        recruiter_id=current_user.id,
        role_title=normalized_role_title,
        candidate_name=normalized_candidate_name,
        rank=request.rank,
        overall_score=request.overall_score,
        core_match=request.core_match,
        secondary_match=request.secondary_match,
        bonus_match=request.bonus_match,
        match_label=request.match_label,
        analysis_mode=normalized_mode,
        top_strengths=normalized_strengths,
        top_gaps=normalized_gaps,
    )

    try:
        db.add(entry)
        db.flush()
        if include_skill_rows:
            _replace_shortlist_skills(db, entry.id, normalized_strengths, normalized_gaps)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(RecruiterShortlist).filter(
            RecruiterShortlist.recruiter_id == current_user.id,
            func.lower(func.trim(RecruiterShortlist.role_title)) == normalized_role_title.lower(),
            func.lower(func.trim(RecruiterShortlist.candidate_name)) == normalized_candidate_name.lower(),
            func.lower(func.trim(func.coalesce(RecruiterShortlist.analysis_mode, "esco"))) == normalized_mode,
        ).first()
        if not existing:
            raise HTTPException(status_code=409, detail="Shortlist entry already exists")
        existing.rank = request.rank
        existing.overall_score = request.overall_score
        existing.core_match = request.core_match
        existing.secondary_match = request.secondary_match
        existing.bonus_match = request.bonus_match
        existing.match_label = request.match_label
        existing.analysis_mode = normalized_mode
        existing.top_strengths = normalized_strengths
        existing.top_gaps = normalized_gaps
        db.flush()
        if include_skill_rows:
            _replace_shortlist_skills(db, existing.id, normalized_strengths, normalized_gaps)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save shortlist")
        db.refresh(existing)
        return _serialize_shortlist(existing, include_skill_rows=include_skill_rows)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save shortlist")
    db.refresh(entry)
    return _serialize_shortlist(entry, include_skill_rows=include_skill_rows)


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
        return Response(status_code=204)

    db.delete(entry)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete shortlist")
    return Response(status_code=204)
