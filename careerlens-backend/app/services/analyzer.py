"""
ESCO-aware Skill-Gap Analyzer
-----------------------------
Uses ESCO relations (occupation_skills.relation_type)
to compute a weighted match score where:
  essential = weight 2
  optional  = weight 1

Simple keyword matching against `preferred_label` and `alt_labels`.
"""

import re
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Skill, Occupation, OccupationSkill


def _tokenize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower())


def build_skill_keyword_map(db: Session) -> Dict[int, List[str]]:
    """Return {skill_id: [keywords]} for all skills in DB.

    For each skill we store:
      1. The full preferred_label (tokenized)
      2. Each alt_label (tokenized)
      3. Individual words from preferred_label that are >= 4 chars
         (so "Python (computer programming)" also matches plain "python")
    """
    skills = db.query(Skill).all()
    out = {}
    for s in skills:
        raw_labels = [s.preferred_label or '']
        if s.alt_labels:
            for alt in re.split(r"[;,]|\|", s.alt_labels):
                alt = alt.strip()
                if alt:
                    raw_labels.append(alt)
        # normalize full labels
        full_keys = {_tokenize(k).strip() for k in raw_labels if k}
        # also add individual words >= 4 chars from preferred_label only
        pref_norm = _tokenize(s.preferred_label or '')
        word_keys = {w for w in pref_norm.split() if len(w) >= 4}
        keys = list(full_keys | word_keys)
        keys = [k for k in keys if k]  # drop empties
        out[s.id] = keys
    return out


def extract_skills_from_resume(resume_text: str, db: Session) -> List[int]:
    """Return list of skill IDs matched in the resume text."""
    resume_norm = _tokenize(resume_text)
    skill_map = build_skill_keyword_map(db)
    matched = []
    for skill_id, keywords in skill_map.items():
        for kw in keywords:
            if not kw:
                continue
            if kw in resume_norm:
                matched.append(skill_id)
                break
    return matched


def calculate_esco_score(resume_text: str, target_role: str, db: Session) -> Dict:
    # 1) Find occupation — prefer exact match, then shortest ILIKE match
    occupation = db.query(Occupation).filter(
        Occupation.preferred_label.ilike(target_role)
    ).first()

    if not occupation:
        # fallback: partial match, pick the one whose label is shortest (closest)
        candidates = (
            db.query(Occupation)
            .filter(Occupation.preferred_label.ilike(f"%{target_role}%"))
            .all()
        )
        if not candidates:
            return {"error": f"Role '{target_role}' not found"}
        # sort by label length so "software developer" beats "embedded systems software developer"
        candidates.sort(key=lambda o: len(o.preferred_label or ''))
        occupation = candidates[0]

    # 2) Fetch all relations for occupation
    relations = (
        db.query(OccupationSkill, Skill)
        .join(Skill, OccupationSkill.skill_id == Skill.id)
        .filter(OccupationSkill.occupation_id == occupation.id)
        .all()
    )

    if not relations:
        return {"error": f"No skill relations found for '{occupation.preferred_label}'"}

    # 3) Extract skills from resume (by skill id)
    matched_skill_ids = set(extract_skills_from_resume(resume_text, db))

    # 4) Compute scoring using weights
    essential_total = 0
    optional_total = 0
    essential_matched = 0
    optional_matched = 0

    essential_list = []
    optional_list = []
    missing_essential = []
    missing_optional = []

    for rel, skill in relations:
        sid = skill.id
        rtype = (rel.relation_type or 'essential')
        if rtype == 'essential':
            essential_total += 1
            if sid in matched_skill_ids:
                essential_matched += 1
                essential_list.append(skill.preferred_label)
            else:
                missing_essential.append(skill.preferred_label)
        else:
            optional_total += 1
            if sid in matched_skill_ids:
                optional_matched += 1
                optional_list.append(skill.preferred_label)
            else:
                missing_optional.append(skill.preferred_label)

    total_points = essential_total * 2 + optional_total * 1
    user_points = essential_matched * 2 + optional_matched * 1
    score = (user_points / total_points * 100) if total_points > 0 else 0.0

    # readiness level simple heuristic
    readiness = 'Low'
    if score >= 80:
        readiness = 'High'
    elif score >= 50:
        readiness = 'Moderate'

    result = {
        'role': occupation.preferred_label,
        'match_score': round(score, 1),
        'readiness_level': readiness,
        'coverage': {
            'essential_percent': round((essential_matched / essential_total * 100) if essential_total else 0, 1),
            'optional_percent': round((optional_matched / optional_total * 100) if optional_total else 0, 1),
        },
        'matched_skills': {
            'essential': essential_list,
            'optional': optional_list,
        },
        'missing_skills': {
            'essential': missing_essential,
            'optional': missing_optional,
        },
        'critical_gaps': missing_essential[:5],
    }

    return result


# Backwards-compatible alias used by older routes
def calculate_match_score(resume_text: str, occupation_title: str, db: Session) -> Dict:
    return calculate_esco_score(resume_text, occupation_title, db)
