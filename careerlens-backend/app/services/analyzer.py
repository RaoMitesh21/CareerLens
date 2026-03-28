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
import time
from dataclasses import dataclass
from typing import List, Dict, Iterable, Tuple
from sqlalchemy.orm import Session
from app.models import Skill, Occupation, OccupationSkill


def _tokenize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower())


@dataclass
class _ResolvedOccupation:
    id: int
    preferred_label: str


@dataclass
class _CachedSkillRelation:
    skill_id: int
    relation_type: str
    preferred_label: str
    alt_labels: str


_CACHE_TTL_SECONDS = 900
_occupations_cache_expires_at = 0.0
_occupations_cache: List[Occupation] = []
_relations_cache: dict[int, tuple[float, List[_CachedSkillRelation]]] = {}


def _get_cached_occupations(db: Session) -> List[Occupation]:
    global _occupations_cache_expires_at, _occupations_cache
    now = time.time()
    if _occupations_cache and now < _occupations_cache_expires_at:
        return _occupations_cache

    _occupations_cache = db.query(Occupation).all()
    _occupations_cache_expires_at = now + _CACHE_TTL_SECONDS
    return _occupations_cache


def _get_cached_relations(db: Session, occupation_id: int) -> List[_CachedSkillRelation]:
    now = time.time()
    cached = _relations_cache.get(occupation_id)
    if cached and now < cached[0]:
        return cached[1]

    rows = (
        db.query(OccupationSkill, Skill)
        .join(Skill, OccupationSkill.skill_id == Skill.id)
        .filter(OccupationSkill.occupation_id == occupation_id)
        .all()
    )
    relations = [
        _CachedSkillRelation(
            skill_id=skill.id,
            relation_type=(rel.relation_type or "essential"),
            preferred_label=(skill.preferred_label or ""),
            alt_labels=(skill.alt_labels or ""),
        )
        for rel, skill in rows
    ]
    _relations_cache[occupation_id] = (now + _CACHE_TTL_SECONDS, relations)
    return relations


def _keywords_for_skill(skill: _CachedSkillRelation) -> List[str]:
    """Build normalized keyword list for one skill record."""
    raw_labels = [skill.preferred_label or ""]
    if skill.alt_labels:
        for alt in re.split(r"[;,]|\|", skill.alt_labels):
            alt = alt.strip()
            if alt:
                raw_labels.append(alt)

    full_keys = {_tokenize(k).strip() for k in raw_labels if k}
    pref_norm = _tokenize(skill.preferred_label or "")
    word_keys = {w for w in pref_norm.split() if len(w) >= 4}

    keys = [k for k in (full_keys | word_keys) if k]
    return keys


def build_skill_keyword_map_from_relations(relations: Iterable[_CachedSkillRelation]) -> Dict[int, List[str]]:
    """Return {skill_id: [keywords]} scoped only to one occupation's related skills."""
    out: Dict[int, List[str]] = {}
    for skill in relations:
        out[skill.skill_id] = _keywords_for_skill(skill)
    return out


def extract_skills_from_resume(resume_text: str, skill_map: Dict[int, List[str]]) -> List[int]:
    """Return list of skill IDs matched in the resume text using a provided scoped skill map."""
    resume_norm = _tokenize(resume_text)
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
    # 1) Find occupation from cached list — exact first, then shortest partial match
    target_norm = _tokenize(target_role).strip()
    occupations = _get_cached_occupations(db)
    occupation = None

    for occ in occupations:
        if _tokenize(occ.preferred_label or "").strip() == target_norm:
            occupation = _ResolvedOccupation(id=occ.id, preferred_label=occ.preferred_label)
            break

    if not occupation:
        candidates = [
            _ResolvedOccupation(id=occ.id, preferred_label=occ.preferred_label)
            for occ in occupations
            if target_norm and target_norm in _tokenize(occ.preferred_label or "")
        ]
        if not candidates:
            return {"error": f"Role '{target_role}' not found"}
        candidates.sort(key=lambda o: len(o.preferred_label or ""))
        occupation = candidates[0]

    # 2) Fetch all relations for occupation
    relations = _get_cached_relations(db, occupation.id)

    if not relations:
        return {"error": f"No skill relations found for '{occupation.preferred_label}'"}

    # 3) Extract skills from resume (scoped to this occupation's required skills only)
    skill_map = build_skill_keyword_map_from_relations(relations)
    matched_skill_ids = set(extract_skills_from_resume(resume_text, skill_map))

    # 4) Compute scoring using weights
    essential_total = 0
    optional_total = 0
    essential_matched = 0
    optional_matched = 0

    essential_list = []
    optional_list = []
    missing_essential = []
    missing_optional = []

    for rel in relations:
        sid = rel.skill_id
        rtype = rel.relation_type
        if rtype == 'essential':
            essential_total += 1
            if sid in matched_skill_ids:
                essential_matched += 1
                essential_list.append(rel.preferred_label)
            else:
                missing_essential.append(rel.preferred_label)
        else:
            optional_total += 1
            if sid in matched_skill_ids:
                optional_matched += 1
                optional_list.append(rel.preferred_label)
            else:
                missing_optional.append(rel.preferred_label)

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
