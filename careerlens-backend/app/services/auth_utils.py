"""
Authentication Utilities
Password hashing, JWT token generation, OTP handling, Email sending
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets
import string
from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# PASSWORD HASHING
# ============================================

import warnings

# Use pbkdf2_sha256 for new passwords; keep bcrypt for legacy verification.
pwd_context = CryptContext(
  schemes=["pbkdf2_sha256", "bcrypt"],
  deprecated="auto"
)


def hash_password(password: str) -> str:
    """Hash a password using the configured primary scheme."""

    try:
        # Suppress passlib backend warnings; functional errors still raise.
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            warnings.filterwarnings('ignore', category=UserWarning)
            return pwd_context.hash(password)
    except Exception as e:
      raise e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            warnings.filterwarnings('ignore', category=UserWarning)
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise e


# ============================================
# JWT TOKEN HANDLING
# ============================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from token"""
    payload = verify_token(token)
    if payload:
        return int(payload.get("sub"))
    return None


# ============================================
# OTP GENERATION & VALIDATION
# ============================================

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(secrets.randbelow(1000000)).zfill(6)


def is_otp_valid(otp_created_at: datetime, expiry_minutes: int = 10) -> bool:
    """Check if OTP is still valid (not expired)"""
    expiry_time = otp_created_at + timedelta(minutes=expiry_minutes)
    return datetime.utcnow() <= expiry_time


# ============================================
# EMAIL SENDING
# ============================================

class EmailService:
    """Handle email sending via SMTP"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER") or os.getenv("SENDER_EMAIL")
        configured_sender = os.getenv("SMTP_FROM_EMAIL") or self.smtp_user
        # Gmail commonly rejects arbitrary From addresses; default to authenticated account.
        if self.smtp_user and "gmail" in self.smtp_server.lower():
            self.sender_email = self.smtp_user
        else:
            self.sender_email = configured_sender
        self.sender_name = os.getenv("SMTP_FROM_NAME", "CareerLens")
        self.sender_password = os.getenv("SMTP_PASSWORD") or os.getenv("SENDER_PASSWORD")

    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.sender_password)
    
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "registration") -> bool:
        """Send OTP via email"""
        if not self.is_configured():
            print("OTP email failed: SMTP_USER/SMTP_PASSWORD not configured")
            return False
        
        try:
            subject = {
                "registration": "Verify Your Email - CareerLens",
                "login_2fa": "Login Verification Code - CareerLens",
                "password_reset": "Password Reset Code - CareerLens"
            }.get(purpose, "Verification Code - CareerLens")
            
            body = self._get_email_body(otp, purpose)
            
            # Use 'related' to hold inline images
            message = MIMEMultipart("related")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            
            # Alternative container holds the html
            msg_alternative = MIMEMultipart("alternative")
            message.attach(msg_alternative)
            msg_alternative.attach(MIMEText(body, "html"))
            
            # Attach CID Image (Logo)
            logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "careerlens-logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    img_data = f.read()
                image = MIMEImage(img_data, name="careerlens-logo.png")
                image.add_header("Content-ID", "<careerlens_logo>")
                image.add_header("Content-Disposition", "inline")
                message.attach(image)
            else:
                print(f"Warning: Logo not found at {logo_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            print(f"Email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def _get_email_body(self, otp: str, purpose: str) -> str:
        """Generate HTML email body with premium web-based theme"""
        title = {
            "registration": "Email Verification",
            "login_2fa": "Two-Step Authentication",
            "password_reset": "Password Reset Request"
        }.get(purpose, "Verification Code")
        
        message = {
            "registration": "Welcome to CareerLens! Please verify your email address to complete your registration and start exploring career opportunities.",
            "login_2fa": "A sign-in attempt requires further verification. Enter the code below to securely access your account.",
            "password_reset": "We received a request to reset your CareerLens password. Use the verification code below to securely create a new password."
        }.get(purpose, "Use this code to verify your request.")
        
        # We use CID (Content-ID) inline image embedding for the logo.
        # This bypassed Gmail's data URI blocking and external image proxies.

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
          
          <!-- Background Wrapper -->
          <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 40px 20px;">
            <tr>
              <td align="center">
                
                <!-- Main Email Card -->
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);">
                  
                  <!-- Top Gradient Accent Bar -->
                  <tr>
                    <td style="height: 6px; background: linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%); border-radius: 16px 16px 0 0;"></td>
                  </tr>

                  <!-- Header / Logo -->
                  <tr>
                    <td align="center" style="padding: 40px 40px 20px 40px;">
                      <img src="cid:careerlens_logo" alt="CareerLens Logo" width="180" style="display: block; outline: none; border: none; text-decoration: none;" />
                    </td>
                  </tr>
                  
                  <!-- Content Body -->
                  <tr>
                    <td align="center" style="padding: 10px 40px 30px 40px;">
                      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; text-align: center;">
                        {title}
                      </h1>
                      
                      <p style="margin: 20px 0 30px 0; font-size: 15px; line-height: 1.6; color: #475569; text-align: center;">
                        {message}
                      </p>
                      
                      <!-- OTP Box -->
                      <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0f9ff; border: 1px solid rgba(0, 194, 203, 0.3); border-radius: 12px; margin-bottom: 30px;">
                        <tr>
                          <td align="center" style="padding: 24px;">
                            <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #00C2CB; display: block;">
                              {otp}
                            </span>
                          </td>
                        </tr>
                      </table>
                      
                      <!-- Security Tips -->
                      <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; text-align: center;">
                        This code will securely expire in <strong style="color: #475569;">10 minutes</strong>.
                      </p>
                      
                      <p style="margin: 0; font-size: 14px; color: #ef4444; font-weight: 500; text-align: center;">
                        Please do not share this code with anyone.
                      </p>
                    </td>
                  </tr>
                  
                  <!-- Divider -->
                  <tr>
                    <td style="padding: 0 40px;">
                      <div style="height: 1px; background-color: #e2e8f0; width: 100%;"></div>
                    </td>
                  </tr>
                  
                  <!-- Footer -->
                  <tr>
                    <td align="center" style="padding: 25px 40px 30px 40px;">
                      <p style="margin: 0 0 10px 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        If you did not request this email, there is nothing you need to do. Because this is a security, notification, you may still receive it even if you have opted out of marketing emails.
                      </p>
                      <p style="margin: 0; font-size: 12px; font-weight: 600; color: #64748b;">
                        © {datetime.utcnow().year} CareerLens AI. All rights reserved.
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


# Initialize email service
email_service = EmailService()


def send_otp_email(email: str, otp: str, purpose: str = "registration") -> bool:
    """Wrapper function to send OTP email"""
    return email_service.send_otp_email(email, otp, purpose)


# ============================================
# HELPER FUNCTIONS
# ============================================

def log_auth_event(user_id: int, event_type: str, details: str = "") -> None:
    """Log authentication events for security"""
    timestamp = datetime.utcnow().isoformat()
    print(f"[AUTH] {timestamp} | User {user_id} | {event_type} | {details}")
