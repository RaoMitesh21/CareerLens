"""
app/services/hybrid_alignment.py — ESCO + O*NET Fusion Helpers
================================================================
Additive helpers for hybrid scoring. ESCO remains the primary model,
while O*NET provides an auxiliary alignment signal.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.onet import OnetOccupation, OnetOccupationSkill, OnetSkill


# Controlled alias bridge from resume vocabulary to O*NET broad skill labels.
# This improves recall for technical resumes without changing ESCO scoring.
_ONET_ALIAS_HINTS: dict[str, tuple[str, ...]] = {
    "programming": (
        "python", "java", "javascript", "typescript", "sql", "c++", "c#",
        "go", "golang", "ruby", "php", "kotlin", "swift",
    ),
    "technology design": (
        "system design", "architecture", "api design", "microservices", "design pattern",
    ),
    "systems analysis": (
        "requirements", "business analysis", "system analysis", "root cause",
    ),
    "critical thinking": (
        "problem solving", "debugging", "troubleshooting", "analysis",
    ),
    "active learning": (
        "upskilling", "self learning", "continuous learning", "course",
    ),
    "mathematics": (
        "statistics", "probability", "linear algebra", "quantitative",
    ),
    "science": (
        "machine learning", "deep learning", "ai", "research",
    ),
    "operations analysis": (
        "performance optimization", "capacity planning", "monitoring",
    ),
    "time management": (
        "prioritization", "deadline", "time management",
    ),
    "coordination": (
        "collaboration", "cross functional", "teamwork", "stakeholder",
    ),
}


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _tokenize(value: str) -> set[str]:
    text = _normalize_text(value)
    if not text:
        return set()
    return {t for t in text.split(" ") if len(t) > 1}


def _label_similarity(target: str, label: str) -> float:
    t = _normalize_text(target)
    l = _normalize_text(label)
    if not t or not l:
        return 0.0

    if t == l:
        return 1.0
    if l.startswith(t) or t.startswith(l):
        return 0.92
    if t in l or l in t:
        return 0.86

    t_tokens = _tokenize(t)
    l_tokens = _tokenize(l)
    if not t_tokens or not l_tokens:
        return 0.0

    overlap = len(t_tokens & l_tokens)
    if overlap == 0:
        return 0.0

    precision = overlap / len(l_tokens)
    recall = overlap / len(t_tokens)
    return (2 * precision * recall) / (precision + recall)


def resolve_onet_occupation(target_role: str, db: Session) -> tuple[Optional[OnetOccupation], float]:
    target = _normalize_text(target_role)
    if not target:
        return None, 0.0

    exact = (
        db.query(OnetOccupation)
        .filter(OnetOccupation.title.ilike(target))
        .first()
    )
    if exact:
        return exact, 1.0

    all_roles = db.query(OnetOccupation).all()
    if not all_roles:
        return None, 0.0

    best = None
    best_score = 0.0
    for role in all_roles:
        score = _label_similarity(target, role.title or "")
        if score > best_score:
            best = role
            best_score = score

    if best_score < 0.40:
        return None, best_score
    return best, best_score


def _resume_matches_skill(resume_text_norm: str, skill_name: str) -> tuple[bool, str]:
    name = _normalize_text(skill_name)
    if not name:
        return False, "none"

    if name in resume_text_norm:
        return True, "phrase"

    resume_tokens = _tokenize(resume_text_norm)
    name_tokens = _tokenize(name)
    if not name_tokens:
        return False, "none"

    # Single-token skills (e.g., python, sql)
    if len(name_tokens) == 1:
        token = next(iter(name_tokens))
        if len(token) >= 3 and token in resume_tokens:
            return True, "token"

    # Alias hints (e.g. python/java -> programming)
    aliases = _ONET_ALIAS_HINTS.get(name, ())
    for alias in aliases:
        alias_norm = _normalize_text(alias)
        if not alias_norm:
            continue
        if alias_norm in resume_text_norm:
            return True, "alias"
        alias_tokens = _tokenize(alias_norm)
        if alias_tokens and alias_tokens.issubset(resume_tokens):
            return True, "alias"

    # Multi-token skills: require strong overlap to avoid noisy matches.
    overlap = len(name_tokens & resume_tokens)
    overlap_ratio = overlap / len(name_tokens)
    if overlap >= 2 and overlap_ratio >= 0.66:
        return True, "overlap"

    return False, "none"


def compute_onet_alignment(resume_text: str, target_role: str, db: Session) -> dict:
    role, role_score = resolve_onet_occupation(target_role, db)
    if not role:
        return {
            "available": False,
            "reason": "No O*NET role match",
            "target_role": target_role,
            "matched_role": None,
            "role_match_score": round(role_score * 100, 1),
            "skill_match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "total_skills": 0,
        }

    relations = (
        db.query(OnetOccupationSkill, OnetSkill)
        .join(OnetSkill, OnetOccupationSkill.skill_id == OnetSkill.id)
        .filter(OnetOccupationSkill.occupation_id == role.id)
        .order_by(OnetOccupationSkill.importance.desc())
        .limit(120)
        .all()
    )

    if not relations:
        return {
            "available": False,
            "reason": "No O*NET skills for matched role",
            "target_role": target_role,
            "matched_role": role.title,
            "role_match_score": round(role_score * 100, 1),
            "skill_match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "total_skills": 0,
        }

    resume_norm = _normalize_text(resume_text)
    match_breakdown = {
        "phrase": 0,
        "token": 0,
        "alias": 0,
        "overlap": 0,
    }
    matched: list[str] = []
    missing: list[str] = []
    matched_via_alias: list[str] = []

    for rel, skill in relations:
        name = (skill.name or "").strip()
        if not name:
            continue
        is_match, match_mode = _resume_matches_skill(resume_norm, name)
        if is_match:
            matched.append(name)
            if match_mode in match_breakdown:
                match_breakdown[match_mode] += 1
            if match_mode == "alias":
                matched_via_alias.append(name)
        else:
            missing.append(name)

    total = len(matched) + len(missing)
    match_score = round((len(matched) / total) * 100, 1) if total > 0 else 0.0

    return {
        "available": True,
        "reason": None,
        "target_role": target_role,
        "matched_role": role.title,
        "role_match_score": round(role_score * 100, 1),
        "skill_match_score": match_score,
        "matched_skills": matched[:30],
        "missing_skills": missing[:30],
        "match_breakdown": match_breakdown,
        "matched_via_alias": matched_via_alias[:20],
        "total_skills": total,
    }


def fuse_esco_onet_score(esco_score: float, onet_score: float, onet_available: bool) -> float:
    esco = float(esco_score)
    onet = float(onet_score)
    if not onet_available:
        return round(esco, 1)

    # ESCO-first blend preserves current model behavior while adding O*NET signal.
    fused = (esco * 0.82) + (onet * 0.18)
    return round(max(0.0, min(100.0, fused)), 1)
