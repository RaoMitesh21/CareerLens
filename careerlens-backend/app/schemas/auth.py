"""
Pydantic Schemas for Authentication Endpoints
Request and Response models with validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class RegisterRequest(BaseModel):
    """User registration request"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    login_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(student|recruiter)$")

    @validator('login_id')
    def validate_login_id(cls, v):
        """Only alphanumeric, underscore, hyphen allowed"""
        if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', v):
            raise ValueError('Login ID: 3-50 chars, alphanumeric, underscore, hyphen only')
        return v

    @validator('password')
    def validate_password(cls, v):
        """Password must contain uppercase, lowercase, number, special char"""
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or fewer')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letters')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letters')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain numbers')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError('Password must contain special characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "login_id": "john_doe",
                "password": "SecurePass123!",
                "role": "student"
            }
        }


class RegisterResponse(BaseModel):
    """User registration response"""
    user_id: int
    name: str
    email: str
    login_id: str
    role: str
    message: str
    otp_medium: str = "email"

    class Config:
        from_attributes = True


class VerifyOTPRequest(BaseModel):
    """OTP verification request"""
    email: EmailStr
    otp: str = Field(..., pattern="^[0-9]{6}$")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "otp": "123456"
            }
        }


class VerifyOTPResponse(BaseModel):
    """OTP verification response"""
    message: str
    user_id: Optional[int] = None
    verified_at: datetime


class LoginRequest(BaseModel):
    """User login request"""
    login_id: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "login_id": "john_doe",
                "password": "SecurePass123!"
            }
        }


class LoginResponse(BaseModel):
    """Login response (after credential verification, before 2FA)"""
    message: str
    user_id: int
    email: str
    name: str
    role: str
    requires_2fa: bool = True
    otp_medium: str = "email"


class VerifyLoginOTPRequest(BaseModel):
    """Complete login with 2FA OTP"""
    email: EmailStr
    otp: str = Field(..., pattern="^[0-9]{6}$")


class VerifyLoginOTPResponse(BaseModel):
    """Successful login response with JWT token"""
    access_token: str
    token_type: str = "bearer"
    user: 'UserResponse'
    logged_in_at: datetime


class UserResponse(BaseModel):
    """User data response"""
    id: int
    name: str
    email: str
    login_id: str
    role: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    """Request password reset"""
    email_or_username: str = Field(..., min_length=3)

    class Config:
        json_schema_extra = {
            "example": {
                "email_or_username": "john@example.com"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """Password reset requested response"""
    message: str
    email: str


class ResetPasswordRequest(BaseModel):
    """Reset password with OTP"""
    email: EmailStr
    otp: str = Field(..., pattern="^[0-9]{6}$")
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        """Password must contain uppercase, lowercase, number, special char"""
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or fewer')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letters')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letters')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain numbers')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError('Password must contain special characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "otp": "123456",
                "new_password": "NewSecurePass123!"
            }
        }


class ResetPasswordResponse(BaseModel):
    """Password reset response"""
    message: str
    user_id: int


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None


# Update forward reference
VerifyLoginOTPResponse.update_forward_refs()
