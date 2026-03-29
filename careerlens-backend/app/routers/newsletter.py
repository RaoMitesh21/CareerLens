"""
Newsletter Subscription Router
Handles newsletter signups and sends confirmation emails via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import os

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


# ── Pydantic Models ──────────────────────────────────────────────────
class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr


class NewsletterSubscribeResponse(BaseModel):
    success: bool
    message: str


# ── Email Configuration ──────────────────────────────────────────────
SMTP_SERVER = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SMTP_USER", "raomitesh12@gmail.com")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def send_newsletter_confirmation(subscriber_email: str) -> bool:
    """
    Send a beautifully designed newsletter confirmation email to the subscriber.
    Uses the same CID-embedded logo pattern as the contact form emails.
    """
    # Validate SMTP config before attempting
    if not SENDER_PASSWORD or not SENDER_PASSWORD.strip():
        print("Error: SMTP_PASSWORD not configured. Newsletter emails cannot be sent.")
        return False
    
    if not SENDER_EMAIL or not SENDER_EMAIL.strip():
        print("Error: SMTP_USER not configured. Newsletter emails cannot be sent.")
        return False
    
    try:
        # Create message root as 'related' to hold inline images
        msg = MIMEMultipart("related")
        msg["Subject"] = "Welcome to the CareerLens Newsletter! 🎉"
        msg["From"] = SENDER_EMAIL
        msg["To"] = subscriber_email

        # Create alternative container for text/html
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Plain text version
        text_body = """
Welcome to CareerLens Newsletter!

Thank you for subscribing to the CareerLens newsletter.

You will now receive the latest updates on:
- AI-powered career insights and industry trends
- New platform features and improvements
- Tips for students and recruiters to leverage data-driven career analysis

Stay ahead in your career journey with CareerLens.

Best regards,
The CareerLens Team

---
Career insights are generated using a combination of publicly available datasets and proprietary processing models.
If you wish to unsubscribe, please contact us at support@careerlens.in.
"""

        # HTML version — matching the contact form design
        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Welcome to CareerLens Newsletter</title>
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
                  
                  <!-- Welcome Badge -->
                  <tr>
                    <td align="center" style="padding: 15px 40px 5px 40px;">
                      <div style="display: inline-block; background: linear-gradient(135deg, rgba(0, 194, 203, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); border-radius: 50px; padding: 8px 20px;">
                        <span style="font-size: 13px; font-weight: 600; color: #00C2CB; letter-spacing: 1px; text-transform: uppercase;">🎉 You're In!</span>
                      </div>
                    </td>
                  </tr>
                  
                  <!-- Title -->
                  <tr>
                    <td align="center" style="padding: 15px 40px 10px 40px;">
                      <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #0f172a;">
                        Welcome to the CareerLens Newsletter
                      </h1>
                    </td>
                  </tr>

                  <!-- Subtitle -->
                  <tr>
                    <td align="center" style="padding: 0 40px 30px 40px;">
                      <p style="margin: 0; font-size: 15px; color: #64748b; line-height: 1.6;">
                        Thank you for subscribing, <strong style="color: #0f172a;">{subscriber_email}</strong>! You'll now receive the latest career insights directly in your inbox.
                      </p>
                    </td>
                  </tr>

                  <!-- What You'll Get Section -->
                  <tr>
                    <td style="padding: 0 40px 30px 40px;">
                      <div style="background-color: #f8fafc; border-left: 4px solid #00C2CB; border-radius: 4px; padding: 20px;">
                        <h3 style="margin: 0 0 12px 0; color: #0f172a; font-size: 15px; font-weight: 700;">What you'll receive:</h3>
                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                          <tr>
                            <td style="padding: 6px 0; font-size: 14px; color: #334155; line-height: 1.5;">
                              ✦ &nbsp; AI-powered career insights and industry trends
                            </td>
                          </tr>
                          <tr>
                            <td style="padding: 6px 0; font-size: 14px; color: #334155; line-height: 1.5;">
                              ✦ &nbsp; New platform features and improvements
                            </td>
                          </tr>
                          <tr>
                            <td style="padding: 6px 0; font-size: 14px; color: #334155; line-height: 1.5;">
                              ✦ &nbsp; Tips for students and recruiters
                            </td>
                          </tr>
                          <tr>
                            <td style="padding: 6px 0; font-size: 14px; color: #334155; line-height: 1.5;">
                              ✦ &nbsp; Data-driven career analysis updates
                            </td>
                          </tr>
                        </table>
                      </div>
                    </td>
                  </tr>

                  <!-- CTA Button -->
                  <tr>
                    <td align="center" style="padding: 0 40px 35px 40px;">
                      <a href="https://careerlens.in" style="display: inline-block; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); color: #ffffff; font-size: 15px; font-weight: 600; text-decoration: none; padding: 14px 32px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0, 194, 203, 0.25);">
                        Explore CareerLens →
                      </a>
                    </td>
                  </tr>

                  <!-- Footer -->
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px; border-top: 1px solid #e2e8f0;">
                      <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; color: #94a3b8;">
                        Career insights are generated using a combination of publicly available datasets and proprietary processing models.
                      </p>
                      <p style="margin: 0; font-size: 11px; color: #cbd5e1;">
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

        # Attach CID Image (Logo) — same path as contact.py
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
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Error sending newsletter email: {str(e)}")
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

        # Check if SMTP is configured
        if not SENDER_PASSWORD or not SENDER_PASSWORD.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is temporarily unavailable. Please try again later."
            )

        # Send confirmation email
        email_sent = send_newsletter_confirmation(data.email)

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send confirmation email. Please try again later."
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
