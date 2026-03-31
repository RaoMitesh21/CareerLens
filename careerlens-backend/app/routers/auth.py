"""
Authentication Routes
Register, Login, OTP Verification, Password Reset
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.models.user import User, OTPRecord, UserRole
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    VerifyOTPRequest, VerifyOTPResponse,
    LoginRequest, LoginResponse,
    VerifyLoginOTPRequest, VerifyLoginOTPResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    UserResponse
)
from app.services.auth_utils import (
    hash_password, verify_password,
    create_access_token,
    generate_otp, is_otp_valid,
    send_otp_email,
    log_auth_event
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _normalize_identifier(value: str) -> str:
    return (value or "").strip()


def _normalize_email(value: str) -> str:
    return _normalize_identifier(value).lower()


# ============================================
# 1. REGISTRATION
# ============================================

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user (Student or Recruiter)
    Sends OTP to email for verification
    """
    
    normalized_email = _normalize_email(request.email)
    normalized_login_id = _normalize_identifier(request.login_id)

    # Check if email already exists (case-insensitive)
    existing_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if login_id already exists (case-insensitive)
    existing_login = db.query(User).filter(func.lower(User.login_id) == normalized_login_id.lower()).first()
    if existing_login:
        raise HTTPException(
            status_code=400,
            detail="Login ID already taken"
        )
    
    try:
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create user
        user = User(
            name=request.name,
            email=normalized_email,
            login_id=normalized_login_id,
            password_hash=hashed_password,
            role=UserRole(request.role),
            created_at=datetime.utcnow()
        )
        
        # Generate OTP
        otp = generate_otp()
        otp_record = OTPRecord(
            email=normalized_email,
            otp=otp,
            purpose="registration",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        # Save staged records, but only commit after OTP delivery succeeds.
        db.add(user)
        db.add(otp_record)
        db.flush()

        email_sent = send_otp_email(normalized_email, otp, "registration")
        if not email_sent:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Email service is temporarily unavailable. Please try again."
            )

        db.commit()
        db.refresh(user)

        log_auth_event(user.id, "REGISTRATION_INITIATED", request.email)
        
        return RegisterResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            login_id=user.login_id,
            role=user.role.value,
            message="Registration successful. OTP sent to email.",
            otp_medium="email"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


# ============================================
# 2. OTP VERIFICATION (Registration)
# ============================================

@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify OTP during registration, login, or password reset
    """
    
    normalized_email = _normalize_email(request.email)

    # Find user
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Find OTP record - can be for registration, login_2fa, or password_reset
    otp_record = db.query(OTPRecord).filter(
        func.lower(OTPRecord.email) == normalized_email,
        OTPRecord.otp == request.otp
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    
    # Check if OTP expired
    if datetime.utcnow() > otp_record.expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )
    
    # Check attempt limit
    if otp_record.attempt_count >= otp_record.max_attempts:
        raise HTTPException(
            status_code=400,
            detail="Too many failed attempts"
        )
    
    try:
        # Handle different OTP purposes
        if otp_record.purpose == "registration":
            # Mark email as verified for registration
            user.email_verified = True
            user.email_verified_at = datetime.utcnow()
        elif otp_record.purpose == "login_2fa":
            # OTP verified for login - will generate JWT in separate endpoint
            pass
        elif otp_record.purpose == "password_reset":
            # OTP verified for password reset - will reset password in separate endpoint
            pass
        
        otp_record.is_used = True
        otp_record.used_at = datetime.utcnow()
        
        db.commit()
        
        if otp_record.purpose == "registration":
            log_auth_event(user.id, "EMAIL_VERIFIED", request.email)
        
        return VerifyOTPResponse(
            message="OTP verified successfully",
            user_id=user.id,
            verified_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )
    
    try:
        # Mark email as verified
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        otp_record.is_used = True
        otp_record.used_at = datetime.utcnow()
        
        db.commit()
        log_auth_event(user.id, "EMAIL_VERIFIED", request.email)
        
        return VerifyOTPResponse(
            message="Email verified successfully",
            user_id=user.id,
            verified_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


# ============================================
# 2B. RESEND OTP
# ============================================

@router.post("/resend-otp-registration")
async def resend_otp_registration(request: dict, db: Session = Depends(get_db)):
    """
    Resend OTP for registration
    """
    email = _normalize_email(request.get('email', ''))
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Find user
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new OTP
    otp = generate_otp()
    
    # Delete old OTP records and create new one
    db.query(OTPRecord).filter(
        OTPRecord.email == email,
        OTPRecord.purpose == "registration"
    ).delete()
    
    otp_record = OTPRecord(
        email=email,
        otp=otp,
        purpose="registration",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(otp_record)

    email_sent = send_otp_email(email, otp, "registration")
    if not email_sent:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Email service is temporarily unavailable. Please try again."
        )

    db.commit()
    
    return {
        "message": "OTP resent to email",
        "email": email
    }


@router.post("/resend-otp-reset")
async def resend_otp_reset(request: dict, db: Session = Depends(get_db)):
    """
    Resend OTP for password reset
    """
    email = _normalize_email(request.get('email', ''))
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Find user
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new OTP
    otp = generate_otp()
    
    # Delete old OTP records and create new one
    db.query(OTPRecord).filter(
        OTPRecord.email == email,
        OTPRecord.purpose == "password_reset"
    ).delete()
    
    otp_record = OTPRecord(
        email=email,
        otp=otp,
        purpose="password_reset",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(otp_record)

    email_sent = send_otp_email(email, otp, "password_reset")
    if not email_sent:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Email service is temporarily unavailable. Please try again."
        )

    db.commit()
    
    return {
        "message": "OTP resent to email",
        "email": email
    }


@router.post("/resend-otp-login")
async def resend_otp_login(request: dict, db: Session = Depends(get_db)):
    """
    Resend OTP for login 2FA
    """
    email = _normalize_email(request.get('email', ''))
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Find user
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new OTP
    otp = generate_otp()
    
    # Delete old OTP records and create new one
    db.query(OTPRecord).filter(
        OTPRecord.email == email,
        OTPRecord.purpose == "login_2fa"
    ).delete()
    
    otp_record = OTPRecord(
        email=email,
        otp=otp,
        purpose="login_2fa",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(otp_record)

    email_sent = send_otp_email(email, otp, "login_2fa")
    if not email_sent:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Email service is temporarily unavailable. Please try again."
        )

    db.commit()
    
    return {
        "message": "OTP resent to email",
        "email": email
    }


# ============================================
# 3. LOGIN (with 2FA OTP)
# ============================================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with credentials
    Initiates 2FA with OTP
    """
    
    identifier = _normalize_identifier(request.login_id)
    identifier_lower = identifier.lower()

    # Find user by login_id or email
    user = db.query(User).filter(
        or_(
            User.login_id == identifier,
            User.email == identifier,
            func.lower(func.trim(User.login_id)) == identifier_lower,
            func.lower(func.trim(User.email)) == identifier_lower,
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Check if email verified
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first"
        )
    
    # Check if account is active
    if not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )
    
    try:
        # Generate 2FA OTP
        otp = generate_otp()
        otp_record = OTPRecord(
            email=user.email,
            otp=otp,
            purpose="login_2fa",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        # Save OTP and commit only after confirmed email delivery.
        db.add(otp_record)

        email_sent = send_otp_email(user.email, otp, "login_2fa")
        if not email_sent:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Email service is temporarily unavailable. Please try again."
            )

        db.commit()
        
        log_auth_event(user.id, "LOGIN_INITIATED", user.email)
        
        return LoginResponse(
            message="Credentials verified. OTP sent to email.",
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            requires_2fa=True,
            otp_medium="email"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


# ============================================
# 4. VERIFY LOGIN OTP (Complete 2FA)
# ============================================

@router.post("/verify-login-otp", response_model=VerifyLoginOTPResponse)
async def verify_login_otp(request: VerifyLoginOTPRequest, db: Session = Depends(get_db)):
    """
    Verify 2FA OTP and issue JWT token
    """
    
    normalized_email = _normalize_email(request.email)

    # Find OTP record
    otp_record = db.query(OTPRecord).filter(
        func.lower(OTPRecord.email) == normalized_email,
        OTPRecord.otp == request.otp,
        OTPRecord.purpose == "login_2fa"
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    
    # Check if OTP expired
    if datetime.utcnow() > otp_record.expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )
    
    # Find user
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    try:
        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role.value,
                "email": user.email
            }
        )
        
        # Mark OTP as used
        otp_record.is_used = True
        otp_record.used_at = datetime.utcnow()
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        db.commit()
        log_auth_event(user.id, "LOGIN_SUCCESSFUL", user.email)
        
        return VerifyLoginOTPResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user),
            logged_in_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"2FA verification failed: {str(e)}"
        )


# ============================================
# 5. FORGOT PASSWORD
# ============================================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset
    Sends OTP to registered email
    """
    
    identifier = _normalize_identifier(request.email_or_username)
    identifier_lower = identifier.lower()

    # Find user by email or login_id
    user = db.query(User).filter(
        or_(
            User.email == identifier,
            User.login_id == identifier,
            func.lower(func.trim(User.email)) == identifier_lower,
            func.lower(func.trim(User.login_id)) == identifier_lower,
        )
    ).first()
    
    if not user:
        # Don't reveal user existence
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    try:
        # Generate reset OTP
        otp = generate_otp()
        otp_record = OTPRecord(
            email=user.email,
            otp=otp,
            purpose="password_reset",
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        
        # Save OTP and commit only after confirmed email delivery.
        db.add(otp_record)

        email_sent = send_otp_email(user.email, otp, "password_reset")
        if not email_sent:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Email service is temporarily unavailable. Please try again."
            )

        db.commit()
        
        log_auth_event(user.id, "PASSWORD_RESET_REQUESTED", user.email)
        
        return ForgotPasswordResponse(
            message="Password reset OTP sent to your email",
            email=user.email
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Password reset request failed: {str(e)}"
        )


# ============================================
# 6. RESET PASSWORD
# ============================================

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password with OTP verification
    """
    
    normalized_email = _normalize_email(request.email)

    # Find OTP record
    otp_record = db.query(OTPRecord).filter(
        func.lower(OTPRecord.email) == normalized_email,
        OTPRecord.otp == request.otp,
        OTPRecord.purpose == "password_reset"
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    
    # Check if OTP expired
    if datetime.utcnow() > otp_record.expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )
    
    # Find user
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    try:
        # Hash and update password
        user.password_hash = hash_password(request.new_password)
        user.password_changed_at = datetime.utcnow()
        otp_record.is_used = True
        otp_record.used_at = datetime.utcnow()
        
        db.commit()
        log_auth_event(user.id, "PASSWORD_RESET_SUCCESSFUL", user.email)
        
        return ResetPasswordResponse(
            message="Password reset successfully",
            user_id=user.id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Password reset failed: {str(e)}"
        )


# ============================================
# 7. LOGOUT (Optional - for session tracking)
# ============================================

@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    """
    Logout endpoint (tokens are stateless, but can be blacklisted if needed)
    """
    return {"message": "Logged out successfully"}
