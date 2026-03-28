"""
app/routers/dashboard_state.py — Persist dashboard UI state per authenticated user
"""

from datetime import datetime
import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import DashboardState, User
from app.services.auth_utils import verify_token

router = APIRouter(prefix="/dashboard-state", tags=["Dashboard State"])
security = HTTPBearer(auto_error=False)

ALLOWED_SCOPES = {"student", "recruiter"}
MAX_STATE_BYTES = 1024 * 1024  # 1MB safety guard


class DashboardStateUpsertRequest(BaseModel):
    state: Dict[str, Any] = Field(default_factory=dict)


class DashboardStateResponse(BaseModel):
    scope: str
    state: Dict[str, Any]
    updated_at: Optional[datetime] = None


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

    return user


def validate_scope(scope: str) -> str:
    normalized = (scope or "").strip().lower()
    if normalized not in ALLOWED_SCOPES:
        raise HTTPException(status_code=400, detail="Invalid dashboard scope")
    return normalized


@router.get("/{scope}", response_model=DashboardStateResponse)
def get_dashboard_state(
    scope: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_scope = validate_scope(scope)

    row = db.query(DashboardState).filter(
        DashboardState.user_id == current_user.id,
        DashboardState.scope == normalized_scope,
    ).first()

    if not row:
        return DashboardStateResponse(scope=normalized_scope, state={}, updated_at=None)

    return DashboardStateResponse(
        scope=normalized_scope,
        state=row.state or {},
        updated_at=row.updated_at,
    )


@router.put("/{scope}", response_model=DashboardStateResponse)
def upsert_dashboard_state(
    scope: str,
    request: DashboardStateUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_scope = validate_scope(scope)
    normalized_state = request.state or {}

    # Persist only JSON-serializable dictionaries to keep DB rows consistent.
    try:
        payload_bytes = len(json.dumps(normalized_state, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Dashboard state must be valid JSON object")

    # Guard oversized payloads.
    if payload_bytes > MAX_STATE_BYTES:
        raise HTTPException(status_code=413, detail="Dashboard state payload too large")

    row = db.query(DashboardState).filter(
        DashboardState.user_id == current_user.id,
        DashboardState.scope == normalized_scope,
    ).first()

    if row:
        row.state = normalized_state
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save dashboard state")
        db.refresh(row)
        return DashboardStateResponse(scope=normalized_scope, state=row.state or {}, updated_at=row.updated_at)

    row = DashboardState(
        user_id=current_user.id,
        scope=normalized_scope,
        state=normalized_state,
    )
    try:
        db.add(row)
        db.commit()
        db.refresh(row)
    except IntegrityError:
        # Concurrent insert race: fallback to update existing unique row.
        db.rollback()
        row = db.query(DashboardState).filter(
            DashboardState.user_id == current_user.id,
            DashboardState.scope == normalized_scope,
        ).first()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to save dashboard state")
        row.state = normalized_state
        try:
            db.commit()
            db.refresh(row)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save dashboard state")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save dashboard state")

    return DashboardStateResponse(scope=normalized_scope, state=row.state or {}, updated_at=row.updated_at)
