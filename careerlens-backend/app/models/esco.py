"""
app/models/esco.py — ESCO Taxonomy ORM Models
================================================
Tables that store the imported ESCO dataset:

  occupations        – 3,007 ESCO occupation definitions
  skills             – 13,896 ESCO skills (knowledge + competence)
  occupation_skills  – 123,788 occupation↔skill relations
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text,
    Enum, ForeignKey, DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Occupation(Base):
    """An ESCO occupation (e.g. 'software developer')."""

    __tablename__ = "occupations"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True, autoincrement=True,
    )
    esco_id = Column(String(128), nullable=True, unique=True, comment="ESCO ID")
    esco_uri = Column(String(512), nullable=True, unique=True, comment="ESCO URI")
    preferred_label = Column(String(512), nullable=False)
    alt_labels = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    occupation_skills = relationship("OccupationSkill", back_populates="occupation")

    def __repr__(self) -> str:
        return f"<Occupation(id={self.id}, label='{self.preferred_label}')>"


class Skill(Base):
    """An ESCO skill — either 'knowledge' or 'skill/competence'."""

    __tablename__ = "skills"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True, autoincrement=True,
    )
    esco_id = Column(String(128), nullable=True, unique=True)
    esco_uri = Column(String(512), nullable=True, unique=True)
    preferred_label = Column(String(512), nullable=False)
    alt_labels = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    skill_type = Column(String(64), nullable=True)
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    occupation_skills = relationship("OccupationSkill", back_populates="skill")

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, label='{self.preferred_label}')>"


class OccupationSkill(Base):
    """Join table: which skills are required for which occupation."""

    __tablename__ = "occupation_skills"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True, autoincrement=True,
    )
    occupation_id = Column(BigInteger(), ForeignKey("occupations.id"), nullable=False)
    skill_id = Column(BigInteger(), ForeignKey("skills.id"), nullable=False)
    relation_type = Column(
        Enum("essential", "optional", "other", name="relation_type_enum"),
        nullable=False, default="essential",
    )
    source = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    occupation = relationship("Occupation", back_populates="occupation_skills")
    skill = relationship("Skill", back_populates="occupation_skills")

    def __repr__(self) -> str:
        return (
            f"<OccupationSkill(occ={self.occupation_id}, "
            f"skill={self.skill_id}, rel={self.relation_type})>"
        )
