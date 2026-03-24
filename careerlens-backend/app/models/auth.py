"""
Database Models for Authentication
User, OTPRecord, UserSession
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User role enumeration"""
    STUDENT = "student"
    RECRUITER = "recruiter"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    login_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Password & Security
    password_hash = Column(String(255), nullable=False)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Role
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    
    # Email Verification
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Account Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class OTPRecord(Base):
    """OTP Record for email verification and password reset"""
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)
    
    # OTP Details
    email = Column(String(255), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    
    # Purpose: 'registration', 'login_2fa', 'password_reset'
    purpose = Column(String(50), nullable=False)
    
    # Expiry
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    
    # Attempt tracking
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OTPRecord(id={self.id}, email={self.email}, purpose={self.purpose})>"


class UserSession(Base):
    """Track active user sessions for security"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, nullable=False, index=True)
    
    # Session token (can be used for logout/revocation)
    token = Column(String(500), unique=True, nullable=False, index=True)
    
    # User agent and IP for security tracking
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
