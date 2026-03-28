"""
scoring.py — Weighted Scoring Engine
=======================================

Orchestrates skill_classifier + confidence_engine to produce a
professional, multi-dimensional resume analysis.

SCORING FORMULA (per tier):
  coverage     = n_matched / n_total
  avg_conf     = mean confidence of matched skills
  raw_score    = coverage × avg_conf × 100
  calibrated   = min(100, raw_score × calibration_factor)

  Calibration accounts for the fact that keyword matching inherently
  cannot detect all ESCO skills.  A typical well-qualified resume
  explicitly mentions ~25-35% of the ESCO skills for a role, so
  we scale so that 30% raw coverage ≈ 70% calibrated score.

  Overall = core × 0.50 + secondary × 0.30 + bonus × 0.20

KEY DESIGN: skill matching is SCOPED to only the occupation's
required skills (50-150), NOT all 13,896 ESCO skills.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models.esco import Occupation, OccupationSkill, Skill
from app.services.skill_classifier import (
    SkillTier,
    ClassifiedSkill,
    classify_occupation_skills,
)
from app.services.confidence_engine import (
    SkillConfidence,
    match_skills_in_resume,
)
from app.services.scoring_calibration import get_scoring_profile_for_role
from app.core.config import (
    CALIBRATION_K,
    DEFAULT_CONFIDENCE,
    TIER_CORE_WEIGHT,
    TIER_SECONDARY_WEIGHT,
    TIER_BONUS_WEIGHT,
)


_MIN_CONFIDENCE_BY_TIER: Dict[SkillTier, float] = {
    SkillTier.CORE: 0.24,
    SkillTier.SECONDARY: 0.22,
    SkillTier.BONUS: 0.20,
}

_GENERIC_RELAX_EXCLUSIONS = {
    "services", "engineer", "developer", "information", "microsoft", "company",
    "purpose", "physical", "reasoning", "mobile", "shell", "shells",
}


# Process-level cache: target role -> (resolved role label, classified skills, required skill ids).
_ROLE_PROFILE_CACHE: Dict[str, Tuple[str, List[ClassifiedSkill], Set[int]]] = {}


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _tokenize_text(value: str) -> set[str]:
    text = _normalize_text(value)
    if not text:
        return set()
    return set(t for t in text.split(" ") if len(t) > 1)


def _label_similarity_score(target_role: str, label: str) -> float:
    target_norm = _normalize_text(target_role)
    label_norm = _normalize_text(label)
    if not target_norm or not label_norm:
        return 0.0

    if label_norm == target_norm:
        return 1.0
    if label_norm.startswith(target_norm) or target_norm.startswith(label_norm):
        return 0.92
    if target_norm in label_norm or label_norm in target_norm:
        return 0.88

    target_tokens = _tokenize_text(target_norm)
    label_tokens = _tokenize_text(label_norm)
    if not target_tokens or not label_tokens:
        return 0.0

    overlap = len(target_tokens & label_tokens)
    if overlap == 0:
        return 0.0

    precision = overlap / len(label_tokens)
    recall = overlap / len(target_tokens)
    return (2 * precision * recall) / (precision + recall)


# ── Occupation Resolver ─────────────────────────────────────────────
def _resolve_occupation(target_role: str, db: Session) -> Optional[Occupation]:
    """Find best ESCO occupation using exact, alias, and token-overlap scoring."""
    target_norm = _normalize_text(target_role)
    if not target_norm:
        return None

    occ = db.query(Occupation).filter(
        Occupation.preferred_label.ilike(target_norm)
    ).first()
    if occ:
        return occ

    all_occupations = db.query(Occupation).all()
    if not all_occupations:
        return None

    best: Optional[Occupation] = None
    best_score = 0.0

    for occ in all_occupations:
        labels = [occ.preferred_label or ""]
        if occ.alt_labels:
            labels.extend([s.strip() for s in (occ.alt_labels or "").split("\n") if s.strip()])

        local_best = max((_label_similarity_score(target_norm, lbl) for lbl in labels), default=0.0)

        if local_best > best_score:
            best = occ
            best_score = local_best

    # Conservative threshold to avoid wrong-role mapping.
    if best_score < 0.45:
        return None
    return best


def _get_role_profile(
    target_role: str,
    db: Session,
) -> Tuple[Optional[Tuple[str, List[ClassifiedSkill], Set[int]]], Optional[str]]:
    """
    Resolve and cache role metadata needed for resume scoring.
    Returns (profile, error_message).
    """
    target_norm = _normalize_text(target_role)
    if not target_norm:
        return None, f"Role '{target_role}' not found in ESCO database"

    cached = _ROLE_PROFILE_CACHE.get(target_norm)
    if cached is not None:
        return cached, None

    occupation = _resolve_occupation(target_norm, db)
    if not occupation:
        return None, f"Role '{target_role}' not found in ESCO database"

    relations = (
        db.query(OccupationSkill, Skill)
        .join(Skill, OccupationSkill.skill_id == Skill.id)
        .filter(OccupationSkill.occupation_id == occupation.id)
        .all()
    )
    if not relations:
        return None, f"No skill data for '{occupation.preferred_label}'"

    classified = classify_occupation_skills(relations)
    required_ids = {c.skill_id for c in classified}

    profile = (occupation.preferred_label, classified, required_ids)
    _ROLE_PROFILE_CACHE[target_norm] = profile
    return profile, None


def _is_confident_match(
    classified_skill: ClassifiedSkill,
    confidences: Dict[int, SkillConfidence],
    min_confidence_by_tier: Dict[SkillTier, float],
    role_core_terms: set[str],
) -> bool:
    conf = confidences.get(classified_skill.skill_id)
    if not conf:
        return False

    threshold = min_confidence_by_tier[classified_skill.tier]
    label_norm = _normalize_text(classified_skill.label)
    if classified_skill.tier == SkillTier.CORE and role_core_terms:
        relax_terms = {
            t for t in role_core_terms
            if len(t) >= 4 and t not in _GENERIC_RELAX_EXCLUSIONS
        }
        if any(term in label_norm for term in relax_terms):
            threshold = max(0.18, threshold - 0.03)

    return conf.confidence >= threshold


def _infer_foundational_matches(
    classified: List[ClassifiedSkill],
    resume_text: str,
    matched_ids: set[int],
    confidences: Dict[int, SkillConfidence],
) -> None:
    """
    Infer a few foundational ESCO skills from strong concrete tech evidence.
    This reduces false negatives where resumes mention tools/languages but not
    umbrella labels like "computer programming".
    """
    text = _normalize_text(resume_text)
    if not text:
        return

    has_programming = any(token in text for token in [
        "javascript", "typescript", "python", "java", "c#", "c++", "php",
        "ruby", "go", "swift", "kotlin", "node", "react", "angular", "vue",
    ])
    has_markup = any(token in text for token in ["html", "css", "sass", "less", "tailwind"])
    has_web_stack = any(token in text for token in ["react", "angular", "vue", "next", "node", "express", "frontend", "backend"])
    has_debug = any(token in text for token in ["debug", "debugging", "bug", "testing", "test cases", "troubleshoot"])
    has_query = any(token in text for token in ["sql", "query", "mysql", "postgres", "mongodb", "database"])
    in_project_context = any(token in text for token in ["project", "experience", "internship", "work"])

    for skill in classified:
        if skill.skill_id in matched_ids:
            continue

        label_norm = _normalize_text(skill.label)
        inferred = False

        if "computer programming" in label_norm and has_programming:
            inferred = True
        elif "web programming" in label_norm and has_programming and (has_markup or has_web_stack):
            inferred = True
        elif "use markup languages" in label_norm and has_markup:
            inferred = True
        elif "implement front-end website design" in label_norm and (has_markup or has_web_stack):
            inferred = True
        elif ("debug software" in label_norm or "ict debugging tools" in label_norm) and has_debug:
            inferred = True
        elif "use query languages" in label_norm and has_query:
            inferred = True

        if not inferred:
            continue

        matched_ids.add(skill.skill_id)
        confidences[skill.skill_id] = SkillConfidence(
            skill_id=skill.skill_id,
            label=skill.label,
            raw_count=1,
            in_project_section=in_project_context,
            freq_score=0.35,
            context_score=1.0 if in_project_context else 0.3,
            confidence=0.56 if skill.tier == SkillTier.CORE else 0.5,
        )


# ── Per-Tier Sub-Score ──────────────────────────────────────────────
def _tier_score(
    classified: List[ClassifiedSkill],
    matched_ids: set,
    confidences: Dict[int, SkillConfidence],
    tier: SkillTier,
) -> float:
    """
    Compute a calibrated 0-100 sub-score for a single tier.

    1. Raw coverage: (n_matched / n_total) × avg_confidence
    2. Calibrated:   100 × (1 − e^(−k × raw_coverage))

    The exponential calibration accounts for the fact that keyword
    matching inherently captures only a fraction of ESCO skills.
    A 30% raw coverage for a qualified candidate scales to ~70%.
    """
    tier_skills = [c for c in classified if c.tier == tier]
    if not tier_skills:
        return 0.0

    n_total = len(tier_skills)
    matched_skills = [c for c in tier_skills if c.skill_id in matched_ids]
    n_matched = len(matched_skills)

    if n_matched == 0:
        return 0.0

    # Average confidence of matched skills
    total_conf = 0.0
    for c in matched_skills:
        conf = confidences.get(c.skill_id)
        total_conf += conf.confidence if conf else DEFAULT_CONFIDENCE
    avg_conf = total_conf / n_matched

    # Raw coverage weighted by confidence
    raw_coverage = (n_matched / n_total) * avg_conf

    # Exponential calibration (diminishing returns curve)
    calibrated = 100.0 * (1.0 - math.exp(-CALIBRATION_K * raw_coverage))
    return round(min(100.0, calibrated), 1)


# ── Priority Ranker ─────────────────────────────────────────────────
def _rank_improvement_priorities(
    missing: List[ClassifiedSkill],
) -> List[Dict[str, str]]:
    """Rank missing skills: Core→High, Secondary→Medium, Bonus→Low."""
    priority_map = {
        SkillTier.CORE: "High",
        SkillTier.SECONDARY: "Medium",
        SkillTier.BONUS: "Low",
    }
    order_map = {"High": 0, "Medium": 1, "Low": 2}

    items = [
        {"skill": c.label, "priority": priority_map[c.tier]}
        for c in missing
    ]
    items.sort(key=lambda x: (order_map[x["priority"]], x["skill"]))
    return items


# ── Summary Generator ───────────────────────────────────────────────
def _generate_summary(
    overall: float,
    core_pct: float,
    secondary_pct: float,
    n_strengths: int,
    n_missing_core: int,
    role: str,
) -> str:
    """Human-readable analysis paragraph."""
    if overall >= 75:
        opener = f"Excellent fit! Your profile is strongly aligned with \"{role}\"."
        advice = "Focus on showcasing depth of experience and consider advanced certifications."
    elif overall >= 55:
        opener = f"Good match. Your profile covers most requirements for \"{role}\"."
        advice = "Closing a few skill gaps — especially in core areas — would significantly strengthen your application."
    elif overall >= 35:
        opener = f"Moderate alignment with \"{role}\". You have a solid foundation but notable gaps remain."
        advice = "Prioritise the high-priority missing skills. Consider targeted courses or project work."
    elif overall >= 20:
        opener = f"Partial match with \"{role}\". You have some relevant skills but significant gaps exist."
        advice = "Start building core mandatory skills — these are non-negotiable for most employers."
    else:
        opener = f"Your profile currently has limited overlap with \"{role}\". Significant upskilling is needed."
        advice = "Focus on foundational core skills first. Consider introductory courses or entry-level project work."

    stats = (
        f"Core skill coverage: {core_pct}% | "
        f"Secondary knowledge: {secondary_pct}% | "
        f"Strengths identified: {n_strengths} | "
        f"Critical gaps: {n_missing_core}"
    )
    return f"{opener} {advice}\n\n{stats}"


# ═══════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════

def advanced_analyze(
    resume_text: str,
    target_role: str,
    db: Session,
) -> Dict:
    """
    Full Jobscan-level resume analysis.
    Returns the professional JSON structure or {"error": "..."}.
    """
    # 1. Resolve occupation and cached role profile for this target role.
    role_profile, role_error = _get_role_profile(target_role, db)
    if role_error or role_profile is None:
        return {"error": role_error or f"Role '{target_role}' not found in ESCO database"}

    resolved_role, classified, required_ids = role_profile

    calibration = get_scoring_profile_for_role(resolved_role)
    role_terms = set(calibration.get("core_terms", []))
    conf_cfg = calibration.get("confidence_thresholds", {})
    min_confidence_by_tier: Dict[SkillTier, float] = {
        SkillTier.CORE: float(conf_cfg.get("core", _MIN_CONFIDENCE_BY_TIER[SkillTier.CORE])),
        SkillTier.SECONDARY: float(conf_cfg.get("secondary", _MIN_CONFIDENCE_BY_TIER[SkillTier.SECONDARY])),
        SkillTier.BONUS: float(conf_cfg.get("bonus", _MIN_CONFIDENCE_BY_TIER[SkillTier.BONUS])),
    }

    # 2. Role-specific skills are preloaded/cached in role_profile.

    # 3. Match resume against ONLY the required skills (not all 13,896!)
    matched_ids, confidences, keyword_map = match_skills_in_resume(
        resume_text=resume_text,
        required_skill_ids=required_ids,
        db=db,
    )

    # Improve practical recall for role-foundation skills from concrete evidence.
    _infer_foundational_matches(
        classified=classified,
        resume_text=resume_text,
        matched_ids=matched_ids,
        confidences=confidences,
    )

    # 4. Separate matched vs missing with confidence threshold per tier.
    matched_classified = [
        c for c in classified
        if c.skill_id in matched_ids and _is_confident_match(c, confidences, min_confidence_by_tier, role_terms)
    ]
    matched_ids = {c.skill_id for c in matched_classified}
    missing_classified = [c for c in classified if c.skill_id not in matched_ids]

    # 5. Per-tier sub-scores
    core_match = _tier_score(classified, matched_ids, confidences, SkillTier.CORE)
    secondary_match = _tier_score(classified, matched_ids, confidences, SkillTier.SECONDARY)
    bonus_match = _tier_score(classified, matched_ids, confidences, SkillTier.BONUS)

    # 6. Overall score: weighted blend from calibrated role profile.
    weight_cfg = calibration.get("weights", {})
    core_weight = float(weight_cfg.get("core", TIER_CORE_WEIGHT))
    secondary_weight = float(weight_cfg.get("secondary", TIER_SECONDARY_WEIGHT))
    bonus_weight = float(weight_cfg.get("bonus", TIER_BONUS_WEIGHT))

    if core_match < 40:
        core_weight = min(0.82, core_weight + 0.06)
        secondary_weight = max(0.12, secondary_weight - 0.04)
        bonus_weight = max(0.04, bonus_weight - 0.02)

    total_weight = max(core_weight + secondary_weight + bonus_weight, 1e-6)
    core_weight, secondary_weight, bonus_weight = (
        core_weight / total_weight,
        secondary_weight / total_weight,
        bonus_weight / total_weight,
    )

    overall_raw = (
        core_match * core_weight
        + secondary_match * secondary_weight
        + bonus_match * bonus_weight
    )
    overall_score = round(max(0.0, min(100.0, overall_raw)), 1)

    # 7. Strengths = matched core skills + high-confidence matched skills
    strengths = []
    for c in matched_classified:
        conf = confidences.get(c.skill_id)
        if c.tier == SkillTier.CORE or (conf and conf.confidence >= 0.5):
            strengths.append(c.label)

    # 8. Structured matched / missing skill lists
    matched_skills = [c.label for c in matched_classified]
    missing_skills = [c.label for c in missing_classified]

    matched_core = [c.label for c in matched_classified if c.tier == SkillTier.CORE]
    matched_secondary = [c.label for c in matched_classified if c.tier == SkillTier.SECONDARY]
    matched_bonus = [c.label for c in matched_classified if c.tier == SkillTier.BONUS]

    # Missing by tier (used for roadmap generation)
    missing_core = [c.label for c in missing_classified if c.tier == SkillTier.CORE]
    missing_secondary = [c.label for c in missing_classified if c.tier == SkillTier.SECONDARY]
    missing_bonus = [c.label for c in missing_classified if c.tier == SkillTier.BONUS]

    # 9. Improvement priorities
    improvement_priority = _rank_improvement_priorities(missing_classified)

    # 10. Summary
    summary = _generate_summary(
        overall=overall_score,
        core_pct=core_match,
        secondary_pct=secondary_match,
        n_strengths=len(strengths),
        n_missing_core=len(missing_core),
        role=resolved_role,
    )

    # 13. Assemble response
    return {
        "role": resolved_role,
        "overall_score": overall_score,
        "core_match": core_match,
        "secondary_match": secondary_match,
        "bonus_match": bonus_match,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "improvement_priority": improvement_priority[:20],
        "skill_confidence": [
            {
                "skill": conf.label,
                "mentions": conf.raw_count,
                "in_project_context": conf.in_project_section,
                "confidence": conf.confidence,
            }
            for conf in sorted(
                confidences.values(),
                key=lambda x: x.confidence,
                reverse=True,
            )
        ][:30],
        "analysis_summary": summary,
        "meta": {
            "total_required_skills": len(classified),
            "core_skills_count": sum(1 for c in classified if c.tier == SkillTier.CORE),
            "secondary_skills_count": sum(1 for c in classified if c.tier == SkillTier.SECONDARY),
            "bonus_skills_count": sum(1 for c in classified if c.tier == SkillTier.BONUS),
            "total_matched": len(matched_classified),
            "total_missing": len(missing_classified),
            "weight_profile": {
                "core": core_weight,
                "secondary": secondary_weight,
                "bonus": bonus_weight,
            },
            "confidence_thresholds": {
                "core": min_confidence_by_tier[SkillTier.CORE],
                "secondary": min_confidence_by_tier[SkillTier.SECONDARY],
                "bonus": min_confidence_by_tier[SkillTier.BONUS],
            },
            "role_family": calibration.get("role_family", "general"),
        },
        # Internal: missing by tier for roadmap generator
        "_matched_core": matched_core,
        "_matched_secondary": matched_secondary,
        "_matched_bonus": matched_bonus,
        "_missing_core": missing_core,
        "_missing_secondary": missing_secondary,
        "_missing_bonus": missing_bonus,
    }
