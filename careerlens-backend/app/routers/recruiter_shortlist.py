"""
app/routers/recruiter_shortlist.py — Recruiter shortlist endpoints
"""

import ast
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy import String, cast, func, inspect, select
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


def _parse_json_list(value) -> list[str]:
    """Best-effort parser for list-like values persisted in legacy shortlist rows."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return _coerce_list(value)

    text = str(value).strip()
    if not text or text in {"None", "NULL", "null"}:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, (list, tuple)):
            return _coerce_list(parsed)
        if isinstance(parsed, str):
            return _coerce_list(parsed)
    except Exception:
        pass

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return _coerce_list(list(parsed))
        if isinstance(parsed, str):
            return _coerce_list(parsed)
    except Exception:
        pass

    return _coerce_list(text)


def _serialize_shortlist_row_mapping(row) -> dict:
    return {
        "id": row["id"],
        "recruiter_id": row["recruiter_id"],
        "role_title": (row["role_title"] or "").strip(),
        "candidate_name": (row["candidate_name"] or "").strip(),
        "rank": row["rank"],
        "overall_score": row["overall_score"],
        "core_match": row["core_match"],
        "secondary_match": row["secondary_match"],
        "bonus_match": row["bonus_match"],
        "match_label": row["match_label"],
        "analysis_mode": _normalize_analysis_mode(row["analysis_mode"]),
        "top_strengths": _parse_json_list(row.get("top_strengths_raw")),
        "top_gaps": _parse_json_list(row.get("top_gaps_raw")),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _find_existing_shortlist_id(
    db: Session,
    recruiter_id: int,
    role_title: str,
    candidate_name: str,
    analysis_mode: str,
) -> Optional[int]:
    table = RecruiterShortlist.__table__
    stmt = (
        select(table.c.id)
        .where(table.c.recruiter_id == recruiter_id)
        .where(func.lower(func.trim(table.c.role_title)) == role_title.lower())
        .where(func.lower(func.trim(table.c.candidate_name)) == candidate_name.lower())
        .where(func.lower(func.trim(func.coalesce(table.c.analysis_mode, "esco"))) == analysis_mode)
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def _fetch_shortlist_rows_safe(db: Session, recruiter_id: int, role: Optional[str] = None) -> list[dict]:
    table = RecruiterShortlist.__table__
    stmt = (
        select(
            table.c.id,
            table.c.recruiter_id,
            table.c.role_title,
            table.c.candidate_name,
            table.c.rank,
            table.c.overall_score,
            table.c.core_match,
            table.c.secondary_match,
            table.c.bonus_match,
            table.c.match_label,
            table.c.analysis_mode,
            cast(table.c.top_strengths, String).label("top_strengths_raw"),
            cast(table.c.top_gaps, String).label("top_gaps_raw"),
            table.c.created_at,
            table.c.updated_at,
        )
        .where(table.c.recruiter_id == recruiter_id)
        .order_by(table.c.created_at.desc())
    )
    if role:
        normalized_role = _normalize_key(role).lower()
        stmt = stmt.where(func.lower(func.trim(table.c.role_title)) == normalized_role)

    rows = db.execute(stmt).mappings().all()
    return [_serialize_shortlist_row_mapping(row) for row in rows]


def _fetch_shortlist_by_id_safe(db: Session, shortlist_id: int, include_skill_rows: bool = True) -> dict:
    try:
        query = db.query(RecruiterShortlist).filter(RecruiterShortlist.id == shortlist_id)
        if include_skill_rows:
            query = query.options(joinedload(RecruiterShortlist.shortlist_skills))
        entry = query.first()
        if entry:
            return _serialize_shortlist(entry, include_skill_rows=include_skill_rows)
    except Exception:
        pass

    table = RecruiterShortlist.__table__
    stmt = (
        select(
            table.c.id,
            table.c.recruiter_id,
            table.c.role_title,
            table.c.candidate_name,
            table.c.rank,
            table.c.overall_score,
            table.c.core_match,
            table.c.secondary_match,
            table.c.bonus_match,
            table.c.match_label,
            table.c.analysis_mode,
            cast(table.c.top_strengths, String).label("top_strengths_raw"),
            cast(table.c.top_gaps, String).label("top_gaps_raw"),
            table.c.created_at,
            table.c.updated_at,
        )
        .where(table.c.id == shortlist_id)
        .limit(1)
    )
    row = db.execute(stmt).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")
    return _serialize_shortlist_row_mapping(row)


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
    except Exception:
        return _fetch_shortlist_rows_safe(db, recruiter_id=current_user.id, role=role)


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

    existing_id = _find_existing_shortlist_id(
        db=db,
        recruiter_id=current_user.id,
        role_title=normalized_role_title,
        candidate_name=normalized_candidate_name,
        analysis_mode=normalized_mode,
    )

    if existing_id:
        db.query(RecruiterShortlist).filter(RecruiterShortlist.id == existing_id).update(
            {
                RecruiterShortlist.rank: request.rank,
                RecruiterShortlist.overall_score: request.overall_score,
                RecruiterShortlist.core_match: request.core_match,
                RecruiterShortlist.secondary_match: request.secondary_match,
                RecruiterShortlist.bonus_match: request.bonus_match,
                RecruiterShortlist.match_label: request.match_label,
                RecruiterShortlist.analysis_mode: normalized_mode,
                RecruiterShortlist.top_strengths: normalized_strengths,
                RecruiterShortlist.top_gaps: normalized_gaps,
            },
            synchronize_session=False,
        )
        db.flush()
        if include_skill_rows:
            _replace_shortlist_skills(db, existing_id, normalized_strengths, normalized_gaps)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save shortlist")
        return _fetch_shortlist_by_id_safe(db, existing_id, include_skill_rows=include_skill_rows)

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
        existing_id = _find_existing_shortlist_id(
            db=db,
            recruiter_id=current_user.id,
            role_title=normalized_role_title,
            candidate_name=normalized_candidate_name,
            analysis_mode=normalized_mode,
        )
        if not existing_id:
            raise HTTPException(status_code=409, detail="Shortlist entry already exists")

        db.query(RecruiterShortlist).filter(RecruiterShortlist.id == existing_id).update(
            {
                RecruiterShortlist.rank: request.rank,
                RecruiterShortlist.overall_score: request.overall_score,
                RecruiterShortlist.core_match: request.core_match,
                RecruiterShortlist.secondary_match: request.secondary_match,
                RecruiterShortlist.bonus_match: request.bonus_match,
                RecruiterShortlist.match_label: request.match_label,
                RecruiterShortlist.analysis_mode: normalized_mode,
                RecruiterShortlist.top_strengths: normalized_strengths,
                RecruiterShortlist.top_gaps: normalized_gaps,
            },
            synchronize_session=False,
        )
        db.flush()
        if include_skill_rows:
            _replace_shortlist_skills(db, existing_id, normalized_strengths, normalized_gaps)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save shortlist")
        return _fetch_shortlist_by_id_safe(db, existing_id, include_skill_rows=include_skill_rows)
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
