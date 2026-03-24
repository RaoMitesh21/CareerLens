"""
app/routers/user.py — User Endpoints
=======================================

POST /users        — Create a new user
GET  /users/{id}   — Get user detail with resume count
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, Resume
from app.schemas.user import UserCreateRequest, UserResponse, UserDetailResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=201, summary="Create user")
def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
):
    """Register a new user. Email must be unique."""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(name=request.name, email=request.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserDetailResponse, summary="Get user")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user profile with resume count."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resume_count = db.query(Resume).filter(Resume.user_id == user.id).count()
    return UserDetailResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        resume_count=resume_count,
        created_at=user.created_at,
    )
