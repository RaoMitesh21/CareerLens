"""
Contact Form Router
Handles contact form submissions and sends emails
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from app.services.email_provider import get_current_provider

router = APIRouter(prefix="/contact", tags=["contact"])


# ── Pydantic Models ──────────────────────────────────────────────────
class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1)
    message: str = Field(..., min_length=10, max_length=5000)

    class Config:
        example = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Demo Request",
            "role": "Student",
            "message": "I'm interested in learning more about CareerLens"
        }


class ContactFormResponse(BaseModel):
    success: bool
    message: str


def send_contact_email(contact_data: ContactFormRequest) -> bool:
    """
    Send contact form email using the configured provider (SMTP or Resend)
    Returns True if successful, False otherwise
    """
    try:
        provider = get_current_provider()
        # Convert to dict for provider
        contact_dict = {
            "name": contact_data.name,
            "email": contact_data.email,
            "subject": contact_data.subject,
            "role": contact_data.role,
            "message": contact_data.message
        }
        return provider.send_contact_email(contact_dict)
    except Exception as e:
        print(f"Error sending contact email: {str(e)}")
        return False



# ── Routes ──────────────────────────────────────────────────────────
@router.post("/submit", response_model=ContactFormResponse)
async def submit_contact_form(contact_data: ContactFormRequest):
    """
    Submit contact form and send email to admin
    
    **Parameters:**
    - name: Sender's full name
    - email: Sender's email address (for reply)
    - subject: Contact subject
    - role: Sender's role (Student/Recruiter/Other)
    - message: Contact message
    
    **Returns:**
    - success: Whether the submission was processed
    - message: Confirmation message
    """
    try:
        # Validate inputs
        if not contact_data.name or not contact_data.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name is required"
            )

        if not contact_data.email or not contact_data.email.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid email is required"
            )

        if not contact_data.subject or not contact_data.subject.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject is required"
            )

        if not contact_data.message or not contact_data.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required (minimum 10 characters)"
            )

        # Send contact email using configured provider
        email_sent = send_contact_email(contact_data)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send contact email right now. Please try again later."
            )

        return ContactFormResponse(
            success=True,
            message="Thank you for contacting us! We'll get back to you within 24 hours."
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in contact form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get("/health")
async def contact_health():
    """Health check for contact service"""
    provider = get_current_provider()
    return {
        "status": "ok",
        "service": "contact",
        "email_configured": provider.is_configured()
    }
