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

# Import email provider factory
# This will be initialized when app starts
from app.services.email_provider import get_current_provider


class EmailService:
    """Handle email sending via abstracted providers (SMTP/Resend)"""
    
    def __init__(self):
        # Delegate to the global email provider
        self.provider = get_current_provider()

    def is_configured(self) -> bool:
        return self.provider.is_configured()
    
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "registration") -> bool:
        """Send OTP via configured provider (SMTP or Resend)"""
        return self.provider.send_otp_email(recipient_email, otp, purpose)


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
