"""
Contact Form Router
Handles contact form submissions and sends emails
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
import os

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


# ── Email Configuration ──────────────────────────────────────────────
RECIPIENT_EMAIL = os.getenv("CONTACT_FORM_EMAIL", os.getenv("SMTP_USER", "raomitesh12@gmail.com"))
SMTP_SERVER = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_LOGIN_USER = os.getenv("SMTP_USER", "")
SENDER_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_LOGIN_USER or "raomitesh12@gmail.com")
SENDER_NAME = os.getenv("SMTP_FROM_NAME", "CareerLens")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def send_contact_email(contact_data: ContactFormRequest) -> bool:
    """
    Send contact form email via SMTP
    Returns True if successful, False otherwise
    """
    try:
        if not SMTP_LOGIN_USER or not SENDER_PASSWORD:
            print("Error: SMTP_USER/SMTP_PASSWORD not configured for contact emails")
            return False

        # Create message root as 'related' to hold inline images
        msg = MIMEMultipart("related")
        msg["Subject"] = f"CareerLens Contact: {contact_data.subject} - From {contact_data.name}"
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = RECIPIENT_EMAIL
        msg["Reply-To"] = contact_data.email

        # Create alternative container for text/html
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Create plain text and HTML versions
        text_body = f"""
Name: {contact_data.name}
Email: {contact_data.email}
Role: {contact_data.role}
Subject: {contact_data.subject}

Message:
{contact_data.message}
"""

        # We use CID (Content-ID) inline image embedding for the logo.
        # This bypassed Gmail's data URI blocking and external image proxies without showing as a standard attachment.

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>CareerLens Contact Form</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <!-- Top Accent -->
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <!-- Header -->
                  <tr>
                    <td align="center" style="padding: 40px 40px 10px 40px;">
                      <img src="cid:careerlens_logo" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none;" />
                    </td>
                  </tr>
                  
                  <!-- Title -->
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px;">
                        New Contact Submission
                      </h1>
                    </td>
                  </tr>

                  <!-- Details -->
                  <tr>
                    <td style="padding: 0 40px 30px 40px;">
                      <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                          <td style="padding-bottom: 15px;">
                            <strong style="color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Name</strong><br/>
                            <span style="color: #0f172a; font-size: 16px; font-weight: 500;">{contact_data.name}</span>
                          </td>
                        </tr>
                        <tr>
                          <td style="padding-bottom: 15px;">
                            <strong style="color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Email</strong><br/>
                            <a href="mailto:{contact_data.email}" style="color: #00C2CB; font-size: 16px; font-weight: 500; text-decoration: none;">{contact_data.email}</a>
                          </td>
                        </tr>
                        <tr>
                          <td style="padding-bottom: 15px;">
                            <strong style="color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Role</strong><br/>
                            <span style="color: #0f172a; font-size: 16px; font-weight: 500;">{contact_data.role}</span>
                          </td>
                        </tr>
                        <tr>
                          <td style="padding-bottom: 15px;">
                            <strong style="color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Subject</strong><br/>
                            <span style="color: #0f172a; font-size: 16px; font-weight: 500;">{contact_data.subject}</span>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>

                  <!-- Message Container -->
                  <tr>
                    <td style="padding: 0 40px 40px 40px;">
                      <div style="background-color: #f8fafc; border-left: 4px solid #00C2CB; border-radius: 4px; padding: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Message</h3>
                        <p style="margin: 0; color: #334155; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{contact_data.message}</p>
                      </div>
                    </td>
                  </tr>

                  <!-- Footer -->
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px; border-top: 1px solid #e2e8f0;">
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #94a3b8;">
                        This automated email was sent securely via CareerLens AI.
                      </p>
                    </td>
                  </tr>
                  
                </table>
              </td>
            </tr>
          </table>
          
        </body>
        </html>
        '''

        # Attach both plain text and HTML
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg_alternative.attach(part1)
        msg_alternative.attach(part2)

        # Attach CID Image (Logo)
        logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "careerlens-logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                img_data = f.read()
            image = MIMEImage(img_data, name="careerlens-logo.png")
            image.add_header("Content-ID", "<careerlens_logo>")
            image.add_header("Content-Disposition", "inline")
            msg.attach(image)
        else:
            print(f"Warning: Logo not found at {logo_path}")

        # Send email via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_LOGIN_USER, SENDER_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
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

        # Send email
        email_sent = send_contact_email(contact_data)

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please try again later."
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
    return {
        "status": "ok",
        "service": "contact",
        "email_configured": bool(SENDER_PASSWORD)
    }
