"""
app/models/user.py — Application-Level ORM Models
====================================================
Tables that track users, resumes, analysis results, and roadmaps.

  users         – registered users with authentication
  resumes       – uploaded resume texts (linked to user)
  roles         – target roles a user has analysed against
  skill_scores  – per-analysis scoring snapshots
  roadmaps      – generated learning roadmaps
  otp_records   – OTP codes for email verification and 2FA
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Float,
    ForeignKey, DateTime, JSON, Boolean, Enum, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    STUDENT = "student"
    RECRUITER = "recruiter"


class User(Base):
    """A registered user of CareerLens with authentication."""

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    login_id = Column(String(50), unique=True, nullable=True, index=True)
    
    # Password & Security (nullable for backward compatibility)
    password_hash = Column(String(255), nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Role
    role = Column(Enum(UserRole), nullable=True, default=UserRole.STUDENT)
    
    # Email Verification
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Account Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    recruiter_shortlists = relationship("RecruiterShortlist", back_populates="recruiter", cascade="all, delete-orphan")
    recruiter_analysis_runs = relationship("RecruiterAnalysisRun", back_populates="recruiter", cascade="all, delete-orphan")
    dashboard_states = relationship("DashboardState", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"


class Resume(Base):
    """A stored resume linked to a user."""

    __tablename__ = "resumes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    filename = Column(String(255), nullable=True, comment="Original filename if uploaded")
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="resumes")
    skill_scores = relationship("SkillScore", back_populates="resume", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, user_id={self.user_id})>"


class Role(Base):
    """A target role that a user wants to be analysed against.

    Stores both the user-supplied label and the resolved ESCO occupation ID
    so we don't re-resolve on every request.
    """

    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False, comment="User-supplied role name")
    occupation_id = Column(
        BigInteger, ForeignKey("occupations.id"), nullable=True,
        comment="Resolved ESCO occupation FK",
    )
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    skill_scores = relationship("SkillScore", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, title='{self.title}')>"


class SkillScore(Base):
    """One analysis result — links a resume to a role with scores."""

    __tablename__ = "skill_scores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resume_id = Column(BigInteger, ForeignKey("resumes.id"), nullable=False)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False)
    overall_score = Column(Float, nullable=False, default=0.0)
    core_match = Column(Float, nullable=False, default=0.0)
    secondary_match = Column(Float, nullable=False, default=0.0)
    bonus_match = Column(Float, nullable=False, default=0.0)
    matched_skills = Column(JSON, nullable=True, comment="List of matched skill labels")
    missing_skills = Column(JSON, nullable=True, comment="List of missing skill labels")
    strengths = Column(JSON, nullable=True)
    improvement_priority = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    resume = relationship("Resume", back_populates="skill_scores")
    role = relationship("Role", back_populates="skill_scores")
    roadmap = relationship("Roadmap", back_populates="skill_score", uselist=False)

    def __repr__(self) -> str:
        return f"<SkillScore(id={self.id}, overall={self.overall_score})>"


class Roadmap(Base):
    """A generated learning roadmap for a specific analysis."""

    __tablename__ = "roadmaps"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    skill_score_id = Column(
        BigInteger, ForeignKey("skill_scores.id"), nullable=False, unique=True,
    )
    level = Column(String(32), nullable=False, comment="beginner / intermediate / advanced")
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    phases = Column(JSON, nullable=False, comment="Structured roadmap phases")
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    skill_score = relationship("SkillScore", back_populates="roadmap")

    def __repr__(self) -> str:
        return f"<Roadmap(id={self.id}, level='{self.level}')>"


class RecruiterShortlist(Base):
    """A recruiter-saved shortlist entry for one role and candidate."""

    __tablename__ = "recruiter_shortlists"
    __table_args__ = (
        UniqueConstraint(
            "recruiter_id",
            "role_title",
            "candidate_name",
            "analysis_mode",
            name="uq_shortlist_recruiter_role_candidate_mode",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recruiter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    role_title = Column(String(512), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=False, index=True)
    rank = Column(Integer, nullable=True)
    overall_score = Column(Float, nullable=True)
    core_match = Column(Float, nullable=True)
    secondary_match = Column(Float, nullable=True)
    bonus_match = Column(Float, nullable=True)
    match_label = Column(String(64), nullable=True)
    analysis_mode = Column(String(16), nullable=True)
    top_strengths = Column(JSON, nullable=True)
    top_gaps = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    recruiter = relationship("User", back_populates="recruiter_shortlists")
    shortlist_skills = relationship("RecruiterShortlistSkill", back_populates="shortlist", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<RecruiterShortlist(id={self.id}, recruiter_id={self.recruiter_id}, role='{self.role_title}')>"


class RecruiterShortlistSkill(Base):
    """Normalized shortlist skill rows for strengths/gaps."""

    __tablename__ = "recruiter_shortlist_skills"
    __table_args__ = (
        UniqueConstraint(
            "shortlist_id",
            "skill_type",
            "skill_order",
            name="uq_shortlist_skill_position",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shortlist_id = Column(BigInteger, ForeignKey("recruiter_shortlists.id"), nullable=False, index=True)
    skill_type = Column(String(16), nullable=False, comment="strength | gap")
    skill_order = Column(Integer, nullable=False, default=0)
    skill_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    shortlist = relationship("RecruiterShortlist", back_populates="shortlist_skills")

    def __repr__(self) -> str:
        return f"<RecruiterShortlistSkill(id={self.id}, shortlist_id={self.shortlist_id}, type='{self.skill_type}')>"


class RecruiterAnalysisRun(Base):
    """A persisted recruiter analysis session for one role and run key."""

    __tablename__ = "recruiter_analysis_runs"
    __table_args__ = (
        UniqueConstraint("recruiter_id", "analysis_key", name="uq_recruiter_analysis_key"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recruiter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    analysis_key = Column(String(255), nullable=False)
    role_title = Column(String(512), nullable=False, index=True)
    analysis_mode = Column(String(16), nullable=False, default="esco")
    total_candidates = Column(Integer, nullable=False, default=0)
    shortlisted_count = Column(Integer, nullable=False, default=0)
    average_score = Column(Float, nullable=False, default=0.0)
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    recruiter = relationship("User", back_populates="recruiter_analysis_runs")
    candidates = relationship("RecruiterAnalysisCandidate", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<RecruiterAnalysisRun(id={self.id}, recruiter_id={self.recruiter_id}, role='{self.role_title}')>"


class RecruiterAnalysisCandidate(Base):
    """A normalized candidate row for a recruiter analysis run."""

    __tablename__ = "recruiter_analysis_candidates"
    __table_args__ = (
        UniqueConstraint("run_id", "rank", "candidate_name", name="uq_analysis_candidate_position"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(BigInteger, ForeignKey("recruiter_analysis_runs.id"), nullable=False, index=True)
    rank = Column(Integer, nullable=True)
    candidate_name = Column(String(255), nullable=False, index=True)
    resume_filename = Column(String(255), nullable=True)
    overall_score = Column(Float, nullable=False, default=0.0)
    decision_score = Column(Float, nullable=True)
    core_match = Column(Float, nullable=True)
    secondary_match = Column(Float, nullable=True)
    bonus_match = Column(Float, nullable=True)
    match_label = Column(String(64), nullable=True)
    risk_level = Column(String(32), nullable=True)
    matched_count = Column(Integer, nullable=True)
    missing_count = Column(Integer, nullable=True)
    skill_coverage_ratio = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    run = relationship("RecruiterAnalysisRun", back_populates="candidates")
    skills = relationship("RecruiterAnalysisCandidateSkill", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<RecruiterAnalysisCandidate(id={self.id}, run_id={self.run_id}, candidate='{self.candidate_name}')>"


class RecruiterAnalysisCandidateSkill(Base):
    """Normalized skill rows for a recruiter analysis candidate."""

    __tablename__ = "recruiter_analysis_candidate_skills"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "skill_type",
            "skill_order",
            name="uq_analysis_candidate_skill_position",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("recruiter_analysis_candidates.id"), nullable=False, index=True)
    skill_type = Column(String(16), nullable=False, comment="strength | gap")
    skill_order = Column(Integer, nullable=False, default=0)
    skill_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    candidate = relationship("RecruiterAnalysisCandidate", back_populates="skills")

    def __repr__(self) -> str:
        return f"<RecruiterAnalysisCandidateSkill(id={self.id}, candidate_id={self.candidate_id}, type='{self.skill_type}')>"


class OTPRecord(Base):
    """OTP Record for email verification and password reset"""
    __tablename__ = "otp_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
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


class DashboardState(Base):
    """Persisted dashboard UI/application state per user and scope."""

    __tablename__ = "dashboard_states"
    __table_args__ = (
        UniqueConstraint("user_id", "scope", name="uq_dashboard_state_user_scope"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    scope = Column(String(64), nullable=False, index=True, comment="student | recruiter")
    state = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="dashboard_states")

    def __repr__(self) -> str:
        return f"<DashboardState(id={self.id}, user_id={self.user_id}, scope='{self.scope}')>"
