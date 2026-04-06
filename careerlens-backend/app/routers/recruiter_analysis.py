"""
app/routers/recruiter_analysis.py — Normalized recruiter analysis history endpoints
"""

from datetime import datetime
from typing import Iterable, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import (
    RecruiterAnalysisCandidate,
    RecruiterAnalysisCandidateSkill,
    RecruiterAnalysisRun,
    User,
    UserRole,
)
from app.schemas.recruiter_analysis import (
    RecruiterAnalysisCandidateCreateRequest,
    RecruiterAnalysisRunCreateRequest,
    RecruiterAnalysisRunResponse,
)
from app.services.auth_utils import verify_token


router = APIRouter(prefix="/recruiter/analysis-history", tags=["Recruiter Analysis History"])
security = HTTPBearer(auto_error=False)


def _normalize_mode(mode: Optional[str]) -> str:
    return "hybrid" if str(mode or "").strip().lower() == "hybrid" else "esco"


def _normalize_text(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().split())


def _to_skill_rows(values: Iterable[str], skill_type: str) -> list[dict]:
    rows: list[dict] = []
    for index, item in enumerate(values):
        label = _normalize_text(item)
        if not label:
            continue
        rows.append({"skill_type": skill_type, "skill_order": index, "skill_name": label})
    return rows


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = verify_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(
        User.id == int(payload["sub"]),
        User.is_active == True,
        User.is_deleted == False,
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter access required")

    return user


def _serialize_run(run: RecruiterAnalysisRun) -> dict:
    return {
        "id": run.id,
        "recruiter_id": run.recruiter_id,
        "analysis_key": run.analysis_key,
        "role_title": run.role_title,
        "analysis_mode": run.analysis_mode,
        "total_candidates": run.total_candidates,
        "shortlisted_count": run.shortlisted_count,
        "average_score": run.average_score,
        "analyzed_at": run.analyzed_at,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "candidates": [
            {
                "id": candidate.id,
                "run_id": candidate.run_id,
                "rank": candidate.rank,
                "candidate_name": candidate.candidate_name,
                "resume_filename": candidate.resume_filename,
                "overall_score": candidate.overall_score,
                "decision_score": candidate.decision_score,
                "core_match": candidate.core_match,
                "secondary_match": candidate.secondary_match,
                "bonus_match": candidate.bonus_match,
                "match_label": candidate.match_label,
                "risk_level": candidate.risk_level,
                "matched_count": candidate.matched_count,
                "missing_count": candidate.missing_count,
                "skill_coverage_ratio": candidate.skill_coverage_ratio,
                "recommendation": candidate.recommendation,
                "created_at": candidate.created_at,
                "updated_at": candidate.updated_at,
                "strengths": [
                    {
                        "id": skill.id,
                        "skill_type": skill.skill_type,
                        "skill_order": skill.skill_order,
                        "skill_name": skill.skill_name,
                        "created_at": skill.created_at,
                    }
                    for skill in candidate.skills
                    if skill.skill_type == "strength"
                ],
                "gaps": [
                    {
                        "id": skill.id,
                        "skill_type": skill.skill_type,
                        "skill_order": skill.skill_order,
                        "skill_name": skill.skill_name,
                        "created_at": skill.created_at,
                    }
                    for skill in candidate.skills
                    if skill.skill_type == "gap"
                ],
            }
            for candidate in sorted(
                run.candidates,
                key=lambda item: (
                    item.rank if item.rank is not None else 10**9,
                    item.id,
                ),
            )
        ],
    }


@router.get("", response_model=list[RecruiterAnalysisRunResponse])
def list_analysis_runs(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(RecruiterAnalysisRun)
        .options(joinedload(RecruiterAnalysisRun.candidates).joinedload(RecruiterAnalysisCandidate.skills))
        .filter(RecruiterAnalysisRun.recruiter_id == current_user.id)
        .order_by(RecruiterAnalysisRun.analyzed_at.desc(), RecruiterAnalysisRun.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_run(run) for run in runs]


@router.get("/{analysis_key}", response_model=RecruiterAnalysisRunResponse)
def get_analysis_run(
    analysis_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = (
        db.query(RecruiterAnalysisRun)
        .options(joinedload(RecruiterAnalysisRun.candidates).joinedload(RecruiterAnalysisCandidate.skills))
        .filter(
            RecruiterAnalysisRun.recruiter_id == current_user.id,
            RecruiterAnalysisRun.analysis_key == analysis_key,
        )
        .first()
    )

    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    return _serialize_run(run)


@router.post("", response_model=RecruiterAnalysisRunResponse)
def upsert_analysis_run(
    request: RecruiterAnalysisRunCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_mode = _normalize_mode(request.analysis_mode)
    analyzed_at = request.analyzed_at or datetime.utcnow()
    role_title = _normalize_text(request.role_title)
    analysis_key = _normalize_text(request.analysis_key)

    if not analysis_key:
        raise HTTPException(status_code=400, detail="analysis_key is required")

    run = (
        db.query(RecruiterAnalysisRun)
        .filter(
            RecruiterAnalysisRun.recruiter_id == current_user.id,
            RecruiterAnalysisRun.analysis_key == analysis_key,
        )
        .first()
    )

    if not run:
        run = RecruiterAnalysisRun(
            recruiter_id=current_user.id,
            analysis_key=analysis_key,
            role_title=role_title,
            analysis_mode=normalized_mode,
            analyzed_at=analyzed_at,
            total_candidates=request.total_candidates,
            shortlisted_count=request.shortlisted_count,
            average_score=request.average_score,
        )
        db.add(run)
        db.flush()
    else:
        run.role_title = role_title
        run.analysis_mode = normalized_mode
        run.analyzed_at = analyzed_at
        run.total_candidates = request.total_candidates
        run.shortlisted_count = request.shortlisted_count
        run.average_score = request.average_score
        db.flush()
        candidate_ids = [row[0] for row in db.query(RecruiterAnalysisCandidate.id).filter(RecruiterAnalysisCandidate.run_id == run.id).all()]
        if candidate_ids:
            db.query(RecruiterAnalysisCandidateSkill).filter(
                RecruiterAnalysisCandidateSkill.candidate_id.in_(candidate_ids)
            ).delete(synchronize_session=False)
        db.query(RecruiterAnalysisCandidate).filter(RecruiterAnalysisCandidate.run_id == run.id).delete(synchronize_session=False)
        db.flush()

    for candidate_request in request.candidates:
        candidate = RecruiterAnalysisCandidate(
            run_id=run.id,
            rank=candidate_request.rank,
            candidate_name=_normalize_text(candidate_request.candidate_name),
            resume_filename=_normalize_text(candidate_request.resume_filename) or None,
            overall_score=candidate_request.overall_score,
            decision_score=candidate_request.decision_score,
            core_match=candidate_request.core_match,
            secondary_match=candidate_request.secondary_match,
            bonus_match=candidate_request.bonus_match,
            match_label=_normalize_text(candidate_request.match_label) or None,
            risk_level=_normalize_text(candidate_request.risk_level) or None,
            matched_count=candidate_request.matched_count,
            missing_count=candidate_request.missing_count,
            skill_coverage_ratio=candidate_request.skill_coverage_ratio,
            recommendation=candidate_request.recommendation,
        )
        db.add(candidate)
        db.flush()

        for skill_row in _to_skill_rows(candidate_request.strengths, "strength"):
            db.add(RecruiterAnalysisCandidateSkill(candidate_id=candidate.id, **skill_row))
        for skill_row in _to_skill_rows(candidate_request.gaps, "gap"):
            db.add(RecruiterAnalysisCandidateSkill(candidate_id=candidate.id, **skill_row))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save recruiter analysis run")

    run = (
        db.query(RecruiterAnalysisRun)
        .options(joinedload(RecruiterAnalysisRun.candidates).joinedload(RecruiterAnalysisCandidate.skills))
        .filter(
            RecruiterAnalysisRun.recruiter_id == current_user.id,
            RecruiterAnalysisRun.analysis_key == analysis_key,
        )
        .first()
    )
    return _serialize_run(run)


@router.delete("/{analysis_key}", status_code=204)
def delete_analysis_run(
    analysis_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = (
        db.query(RecruiterAnalysisRun)
        .filter(
            RecruiterAnalysisRun.recruiter_id == current_user.id,
            RecruiterAnalysisRun.analysis_key == analysis_key,
        )
        .first()
    )

    if not run:
        return Response(status_code=204)

    candidate_ids = [row[0] for row in db.query(RecruiterAnalysisCandidate.id).filter(RecruiterAnalysisCandidate.run_id == run.id).all()]
    if candidate_ids:
        db.query(RecruiterAnalysisCandidateSkill).filter(
            RecruiterAnalysisCandidateSkill.candidate_id.in_(candidate_ids)
        ).delete(synchronize_session=False)
    db.query(RecruiterAnalysisCandidate).filter(RecruiterAnalysisCandidate.run_id == run.id).delete(synchronize_session=False)
    db.delete(run)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete recruiter analysis run")

    return Response(status_code=204)