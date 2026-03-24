"""
skill_classifier.py — 3-Tier Skill Classification Engine
==========================================================

Classifies every occupation→skill relation into one of three tiers
using ESCO's own metadata (relation_type × skill_type).

  CORE (Mandatory)      = essential relation_type
  SECONDARY (Important) = optional  + knowledge skill_type
  BONUS (Nice-to-have)  = optional  + skill/competence

Scoring weights & penalties tuned for realistic Jobscan-style output:
  - Matching a core skill earns 3 points
  - Missing a core skill is penalised at 50% of its weight
  - Missing a bonus skill costs nothing
"""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


# ── Tier Enum ───────────────────────────────────────────────────────
class SkillTier(str, Enum):
    CORE = "core"
    SECONDARY = "secondary"
    BONUS = "bonus"


# Weight each tier earns when MATCHED
TIER_WEIGHTS: Dict[SkillTier, float] = {
    SkillTier.CORE: 3.0,
    SkillTier.SECONDARY: 1.5,
    SkillTier.BONUS: 0.5,
}

# Fraction of weight applied as penalty when MISSING
# (multiplied by the tier weight to get actual penalty points)
TIER_MISS_PENALTY: Dict[SkillTier, float] = {
    SkillTier.CORE: 0.5,       # miss core → lose half its weight
    SkillTier.SECONDARY: 0.2,  # miss secondary → small penalty
    SkillTier.BONUS: 0.0,      # miss bonus → no penalty
}


# ── Classified Skill ────────────────────────────────────────────────
@dataclass
class ClassifiedSkill:
    """A single skill with its tier, weight, and ESCO metadata."""
    skill_id: int
    label: str
    tier: SkillTier
    relation_type: str
    skill_type: Optional[str]
    weight: float = 0.0
    miss_penalty: float = 0.0

    def __post_init__(self):
        self.weight = TIER_WEIGHTS[self.tier]
        self.miss_penalty = TIER_MISS_PENALTY[self.tier]


# ── Classification ──────────────────────────────────────────────────
def classify_skill(relation_type: str, skill_type: Optional[str]) -> SkillTier:
    """
    Pure function: (relation_type, skill_type) → tier.

    essential (any)                → CORE
    optional  + knowledge          → SECONDARY
    optional  + skill/competence   → BONUS
    """
    rt = (relation_type or "").strip().lower()
    st = (skill_type or "").strip().lower()

    if rt == "essential":
        return SkillTier.CORE
    if "knowledge" in st:
        return SkillTier.SECONDARY
    return SkillTier.BONUS


def classify_occupation_skills(
    relations: list,  # [(OccupationSkill, Skill)]
) -> List[ClassifiedSkill]:
    """Classify a list of DB join tuples into sorted ClassifiedSkills."""
    tier_order = {SkillTier.CORE: 0, SkillTier.SECONDARY: 1, SkillTier.BONUS: 2}
    classified: List[ClassifiedSkill] = []

    for rel, skill in relations:
        tier = classify_skill(rel.relation_type, skill.skill_type)
        classified.append(ClassifiedSkill(
            skill_id=skill.id,
            label=skill.preferred_label,
            tier=tier,
            relation_type=rel.relation_type or "essential",
            skill_type=skill.skill_type,
        ))

    classified.sort(key=lambda c: tier_order[c.tier])
    return classified
