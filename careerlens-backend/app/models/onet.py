"""
app/models/onet.py — O*NET Raw Dataset ORM Models
===================================================
Additive tables for O*NET ingestion. These models are intentionally
separate from ESCO-powered production tables to avoid breaking the
current prototype behavior.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OnetOccupation(Base):
    """Raw O*NET occupation row (SOC code + title)."""

    __tablename__ = "onet_occupations"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    onet_code = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    description = Column(Text, nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    occupation_skills = relationship("OnetOccupationSkill", back_populates="occupation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OnetOccupation(id={self.id}, code='{self.onet_code}', title='{self.title}')>"


class OnetSkill(Base):
    """Raw O*NET skill element row."""

    __tablename__ = "onet_skills"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    element_id = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(512), nullable=False)
    normalized_name = Column(String(512), nullable=False, index=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    occupation_skills = relationship("OnetOccupationSkill", back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OnetSkill(id={self.id}, element_id='{self.element_id}', name='{self.name}')>"


class OnetOccupationSkill(Base):
    """O*NET occupation-skill linkage with importance/level signals."""

    __tablename__ = "onet_occupation_skills"
    __table_args__ = (
        UniqueConstraint("occupation_id", "skill_id", name="uq_onet_occ_skill"),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    occupation_id = Column(BigInteger(), ForeignKey("onet_occupations.id"), nullable=False, index=True)
    skill_id = Column(BigInteger(), ForeignKey("onet_skills.id"), nullable=False, index=True)
    importance = Column(Float, nullable=True)
    level = Column(Float, nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    occupation = relationship("OnetOccupation", back_populates="occupation_skills")
    skill = relationship("OnetSkill", back_populates="occupation_skills")

    def __repr__(self) -> str:
        return (
            f"<OnetOccupationSkill(id={self.id}, occupation_id={self.occupation_id}, "
            f"skill_id={self.skill_id}, importance={self.importance}, level={self.level})>"
        )
