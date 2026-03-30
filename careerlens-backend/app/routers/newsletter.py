"""
Newsletter Subscription Router
Handles newsletter signups and sends confirmation emails
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.services.email_provider import get_current_provider

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


# ── Pydantic Models ──────────────────────────────────────────────────
class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr


class NewsletterSubscribeResponse(BaseModel):
    success: bool
    message: str


def send_newsletter_confirmation(subscriber_email: str) -> bool:
    """
    Send a newsletter confirmation email using the configured provider (SMTP or Resend)
    """
    try:
        provider = get_current_provider()
        return provider.send_newsletter_confirmation(subscriber_email)
    except Exception as e:
        print(f"Error sending newsletter confirmation: {str(e)}")
        return False



# ── Routes ──────────────────────────────────────────────────────────
@router.post("/subscribe", response_model=NewsletterSubscribeResponse)
async def subscribe_newsletter(data: NewsletterSubscribeRequest):
    """
    Subscribe to the CareerLens newsletter.
    Sends a confirmation email to the subscriber.
    """
    try:
        if not data.email or not data.email.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid email address is required."
            )

        # Send confirmation email using configured provider
        email_sent = send_newsletter_confirmation(data.email)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send confirmation email right now. Please try again later."
            )

        return NewsletterSubscribeResponse(
            success=True,
            message="You've successfully subscribed to the CareerLens newsletter! Check your inbox for a confirmation."
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in newsletter subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
