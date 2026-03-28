"""
app/routers/resume.py — Resume Endpoints
===========================================

POST /resumes            — Upload a resume (text)
POST /resumes/upload-pdf — Upload a resume (PDF file)
GET  /resumes?user_id=   — List resumes for a user
GET  /resumes/{id}       — Get resume detail
"""

import pdfplumber
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, Form, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, Resume
from app.services.auth_utils import verify_token
from app.schemas.resume import (
    ResumeUploadRequest,
    ResumeResponse,
    ResumeDetailResponse,
)

router = APIRouter(prefix="/resumes", tags=["Resumes"])
security = HTTPBearer(auto_error=False)


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


@router.post("", response_model=ResumeResponse, status_code=201, summary="Upload resume")
def upload_resume(
    request: ResumeUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a resume text linked to the authenticated user."""
    if request.user_id and request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot upload resume for another user")

    resume = Resume(
        user_id=current_user.id,
        raw_text=request.resume_text,
        filename=request.filename,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/upload-pdf", response_model=ResumeResponse, status_code=201, summary="Upload PDF resume")
async def upload_pdf_resume(
    user_id: int | None = Form(None, description="Optional user ID; must match authenticated user"),
    file: UploadFile = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a resume PDF file. Extracts text server-side using pdfplumber.
    
    - **user_id**: Optional ID; if provided must match authenticated user
    - **file**: PDF file (multipart/form-data)
    """
    if user_id and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot upload resume for another user")
    
    # Validate file
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if file.content_type not in ["application/pdf", "application/x-pdf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Expected PDF.",
        )
    
    # Read file content
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Extract text from PDF
    try:
        extracted_text = _extract_pdf_text(file_content)
        if not extracted_text or len(extracted_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="PDF contains insufficient text. Extracted text must be at least 20 characters.",
            )
    except pdfplumber.PDFPlumberError as e:
        raise HTTPException(status_code=400, detail=f"PDF parsing error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")
    
    # Save resume
    try:
        resume = Resume(
            user_id=current_user.id,
            raw_text=extracted_text,
            filename=file.filename or "uploaded_resume.pdf",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using pdfplumber.
    
    Args:
        pdf_bytes: Raw PDF file content
        
    Returns:
        Extracted text from all pages
        
    Raises:
        pdfplumber.PDFPlumberError: If PDF parsing fails
    """
    text_parts = []
    pdf_file = BytesIO(pdf_bytes)
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF has no pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    # Log but continue if single page fails
                    print(f"Warning: Failed to extract page {page_num}: {e}")
        
        if not text_parts:
            raise ValueError("No text could be extracted from any page")
        
        return "\n".join(text_parts)
    finally:
        pdf_file.close()


@router.get("", response_model=list[ResumeResponse], summary="List resumes")
def list_resumes(
    user_id: int | None = Query(None, description="Optional user ID filter; must match authenticated user"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List resumes for the authenticated user."""
    if user_id and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot list resumes for another user")

    target_user_id = current_user.id
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == target_user_id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return resumes


@router.get("/{resume_id}", response_model=ResumeDetailResponse, summary="Get resume")
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single resume owned by the authenticated user."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access another user's resume")
    return resume
