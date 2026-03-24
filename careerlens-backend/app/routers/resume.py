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

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, Resume
from app.schemas.resume import (
    ResumeUploadRequest,
    ResumeResponse,
    ResumeDetailResponse,
)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("", response_model=ResumeResponse, status_code=201, summary="Upload resume")
def upload_resume(
    request: ResumeUploadRequest,
    db: Session = Depends(get_db),
):
    """Upload a resume text linked to an existing user."""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resume = Resume(
        user_id=request.user_id,
        raw_text=request.resume_text,
        filename=request.filename,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/upload-pdf", response_model=ResumeResponse, status_code=201, summary="Upload PDF resume")
async def upload_pdf_resume(
    user_id: int = Form(..., description="User ID"),
    file: UploadFile = None,
    db: Session = Depends(get_db),
):
    """
    Upload a resume PDF file. Extracts text server-side using pdfplumber.
    
    - **user_id**: ID of the user uploading the resume
    - **file**: PDF file (multipart/form-data)
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
            user_id=user_id,
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
    user_id: int = Query(..., description="User ID to filter by"),
    db: Session = Depends(get_db),
):
    """List all resumes for a given user."""
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return resumes


@router.get("/{resume_id}", response_model=ResumeDetailResponse, summary="Get resume")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get a single resume with full text."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
