"""
app/services/roadmap_quality.py
================================

Final quality gate for roadmap responses.

This module ensures every roadmap field is complete, role-relevant,
and not empty/generic before data is returned to clients.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Tuple


def _clean_list(items) -> List[str]:
    """Normalize to a de-duplicated non-empty list of strings."""
    if items is None:
        return []

    if isinstance(items, str):
        items = [items]

    out: List[str] = []
    seen = set()
    for item in items if isinstance(items, list) else [items]:
        value = str(item).strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _phase_spans(total_months: int, phase_count: int) -> List[str]:
    """Create contiguous month ranges per phase."""
    if phase_count <= 0:
        return []

    each = total_months // phase_count
    remainder = total_months % phase_count

    spans: List[str] = []
    start = 1
    for i in range(phase_count):
        extra = 1 if i < remainder else 0
        length = each + extra
        end = start + length - 1
        spans.append(f"Months {start}-{end}")
        start = end + 1
    return spans


def _expected_phase_count(level: str) -> int:
    return 2 if (level or "").lower() == "advanced" else 3


def _skills_target_per_phase(level: str, total_missing: int, phase_count: int) -> int:
    """Compute realistic per-phase skill target to avoid cognitive overload."""
    if phase_count <= 0:
        return 5
    raw = (total_missing + phase_count - 1) // phase_count
    caps = {"beginner": 7, "intermediate": 8, "advanced": 10}
    mins = {"beginner": 4, "intermediate": 5, "advanced": 6}
    level_lc = (level or "intermediate").lower()
    min_v = mins.get(level_lc, 5)
    cap_v = caps.get(level_lc, 8)
    return max(min_v, min(cap_v, raw if raw > 0 else min_v))


def _resource_templates_for_skill(skill: str) -> List[str]:
    """Return skill-aware resource suggestions."""
    s = skill.lower()

    if "data mining" in s:
        return [
            "Kaggle micro-course: Intro to Machine Learning and feature engineering",
            "Hands-On Machine Learning chapters on data preparation",
        ]
    if "information extraction" in s:
        return [
            "Natural Language Processing Specialization (Coursera)",
            "spaCy practical tutorials for entity extraction",
        ]
    if "business intelligence" in s:
        return [
            "Microsoft Power BI learning path",
            "Tableau guided dashboard case studies",
        ]
    if "web programming" in s:
        return [
            "The Odin Project full stack path",
            "MDN web development learning path",
        ]
    if "computer programming" in s:
        return [
            "CS50x introduction to computer science",
            "Exercism language practice track",
        ]
    if "software design patterns" in s:
        return [
            "Head First Design Patterns",
            "Refactoring Guru design patterns catalog",
        ]
    if "python" in s:
        return [
            "Python official tutorial and docs",
            "Hands-on Python exercises on Kaggle/LeetCode",
        ]
    if "sql" in s:
        return [
            "SQLBolt or Mode SQL tutorial",
            "Practice queries on real datasets",
        ]
    if "machine learning" in s or "ml" == s:
        return [
            "Intro to Machine Learning course (Andrew Ng or equivalent)",
            "Scikit-learn documentation with example notebooks",
        ]
    if "statistics" in s or "probability" in s:
        return [
            "Applied statistics course with worked examples",
            "Statistics cheat sheets and formula practice",
        ]
    if "data" in s and "visual" in s:
        return [
            "Tableau/Power BI guided project tutorials",
            "Data storytelling case studies",
        ]
    if "excel" in s:
        return [
            "Advanced Excel practice workbook",
            "Dashboard-building walkthrough videos",
        ]
    if "git" in s or "github" in s:
        return [
            "Git official book (free online)",
            "GitHub workflow tutorial with pull requests",
        ]
    if "docker" in s:
        return [
            "Docker getting-started guide",
            "Containerizing a sample app end-to-end",
        ]

    return [
        f"Official documentation and beginner guide for {skill}",
        f"Project-based tutorial focused on {skill}",
    ]


def _role_default_resources(role: str) -> List[str]:
    """Return occupation-wise default resources."""
    role_lc = (role or "").lower()

    if "data scientist" in role_lc or "machine learning" in role_lc:
        return [
            "Machine Learning Specialization by Andrew Ng (Coursera)",
            "Kaggle Learn tracks for Python, Pandas, and ML",
            "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow",
        ]
    if "data analyst" in role_lc or "analytics" in role_lc:
        return [
            "Google Data Analytics Professional Certificate",
            "SQL practice on StrataScratch or LeetCode SQL",
            "Power BI or Tableau portfolio dashboard project course",
        ]
    if "web" in role_lc or "frontend" in role_lc:
        return [
            "The Odin Project curriculum",
            "Full Stack Open web development modules",
            "Frontend Mentor real UI project challenges",
        ]
    if "software" in role_lc or "developer" in role_lc or "backend" in role_lc:
        return [
            "CS50x for core programming foundations",
            "System Design Primer (GitHub)",
            "NeetCode roadmap for coding interview-level practice",
        ]

    return [
        "Role-specific Coursera/edX specialization with projects",
        "Official documentation and implementation guides",
        "Portfolio-focused project tutorial series",
    ]


def _looks_generic_resources(resources: List[str]) -> bool:
    """Detect low-quality generic resource lists."""
    if not resources:
        return True

    generic_markers = [
        "official documentation and beginner guide",
        "project-based tutorial focused on",
        "beginner-friendly online course",
        "guided tutorials",
    ]

    generic_hits = 0
    for item in resources:
        text = str(item).lower()
        if any(marker in text for marker in generic_markers):
            generic_hits += 1

    return generic_hits >= max(2, len(resources) - 1)


def _build_description(role: str, phase_title: str, skills: List[str], duration: str) -> str:
    """Create a concise, role-specific phase description."""
    if skills:
        top = ", ".join(skills[:3])
        return (
            f"During {duration}, this phase builds practical {role} capability through {top}. "
            f"By the end of {phase_title.lower()}, you should be able to apply these skills in a small real-world project."
        )
    return (
        f"During {duration}, this phase strengthens your readiness for {role} through guided practice, "
        "project work, and measurable weekly milestones."
    )


def _build_objectives(role: str, phase_title: str, skills: List[str]) -> List[str]:
    """Create actionable, non-generic learning objectives."""
    objectives: List[str] = []

    for skill in skills[:3]:
        objectives.append(f"Reach working proficiency in {skill} through exercises and mini tasks.")

    objectives.append(
        f"Complete one portfolio-ready project for {role} aligned with {phase_title.lower()}."
    )
    objectives.append("Track weekly progress with checkpoints and close weak areas before moving forward.")

    return _clean_list(objectives)[:5]


def _build_actions(role: str, skills: List[str]) -> List[str]:
    """Create concrete suggested actions when actions are missing."""
    skill_text = ", ".join(skills[:3]) if skills else "core role skills"
    return [
        f"Follow a guided learning plan for {skill_text} with 5-7 focused hours per week.",
        f"Build one small project applying {skill_text} to {role} tasks.",
        "Review mistakes weekly and rewrite notes into a personal playbook.",
        "Publish your progress on GitHub or a portfolio page.",
    ]


def _build_resources(skills: List[str], role: str) -> List[str]:
    """Create resource recommendations matched to phase skills."""
    resources: List[str] = []
    for skill in skills[:4]:
        resources.extend(_resource_templates_for_skill(skill)[:1])

    resources.extend(_role_default_resources(role)[:2])

    resources.extend(
        [
            f"One guided portfolio project for {role}",
            "Interview question bank focused on phase skills",
        ]
    )
    return _clean_list(resources)[:5]


def _ensure_phase_shape(phase: Dict, role: str, phase_num: int, duration: str) -> Dict:
    """Ensure one phase has all required roadmap fields."""
    fixed = deepcopy(phase) if isinstance(phase, dict) else {}

    title = str(fixed.get("title") or f"Phase {phase_num} Learning Sprint").strip()
    focus_area = str(fixed.get("focus_area") or "Core skill development").strip()
    skills = _clean_list(fixed.get("skills_to_learn"))
    actions = _clean_list(fixed.get("suggested_actions"))
    objectives = _clean_list(fixed.get("learning_objectives"))
    resources = _clean_list(fixed.get("recommended_resources"))

    if not actions:
        actions = _build_actions(role, skills)

    if len(objectives) < 3:
        objectives = _clean_list(objectives + _build_objectives(role, title, skills))

    if len(resources) < 3 or _looks_generic_resources(resources):
        resources = _clean_list(_build_resources(skills, role))

    enhanced_description = str(fixed.get("enhanced_description") or "").strip()
    if not enhanced_description:
        enhanced_description = _build_description(role, title, skills, duration)

    fixed.update(
        {
            "phase": phase_num,
            "title": title,
            "duration": duration,
            "focus_area": focus_area,
            "skills_to_learn": skills,
            "suggested_actions": actions[:5],
            "enhanced_description": enhanced_description,
            "learning_objectives": objectives[:5],
            "recommended_resources": resources[:5],
        }
    )
    return fixed


def _distribute_uncovered_skills(
    phases: List[Dict],
    missing_skills: List[str],
    level: str,
) -> List[Dict]:
    """Distribute missing skills without overloading phases."""
    if not phases:
        return phases

    phase_count = len(phases)
    target_per_phase = _skills_target_per_phase(level, len(missing_skills), phase_count)

    missing_clean = _clean_list(missing_skills)

    # Normalize and trim existing skills first.
    for phase in phases:
        phase["skills_to_learn"] = _clean_list(phase.get("skills_to_learn"))[:target_per_phase]

    covered = set()
    for p in phases:
        for s in p.get("skills_to_learn", []):
            covered.add(str(s).strip().lower())

    uncovered = [s for s in missing_clean if s.lower() not in covered]

    # Round-robin uncovered skills only while capacity exists.
    idx = 0
    for skill in uncovered:
        attempts = 0
        placed = False
        while attempts < phase_count and not placed:
            phase = phases[(idx + attempts) % phase_count]
            skills = _clean_list(phase.get("skills_to_learn"))
            skill_keys = {x.lower() for x in skills}
            if len(skills) < target_per_phase and skill.lower() not in skill_keys:
                skills.append(skill)
                phase["skills_to_learn"] = skills
                placed = True
                idx += 1
            attempts += 1

    # Top up each phase to target using missing skill pool.
    for phase in phases:
        skills = _clean_list(phase.get("skills_to_learn"))
        skill_keys = {s.lower() for s in skills}
        for skill in missing_clean:
            if len(skills) >= target_per_phase:
                break
            if skill.lower() not in skill_keys:
                skills.append(skill)
                skill_keys.add(skill.lower())
        phase["skills_to_learn"] = skills[:target_per_phase]

    return phases


def enforce_roadmap_quality(
    roadmap: Dict,
    role: str,
    missing_skills: List[str],
) -> Tuple[Dict, Dict]:
    """
    Validate and repair roadmap so all response fields are complete and useful.

    Returns:
        (fixed_roadmap, quality_report)
    """
    fixed = deepcopy(roadmap) if isinstance(roadmap, dict) else {}

    level = str(fixed.get("level") or "intermediate").strip().lower()
    fixed["level"] = level

    phases = fixed.get("phases") if isinstance(fixed.get("phases"), list) else []
    expected_count = _expected_phase_count(level)

    if not phases:
        phases = [{} for _ in range(expected_count)]

    timeline = fixed.get("timeline_months")
    try:
        timeline_months = int(timeline)
    except (TypeError, ValueError):
        timeline_months = 12
    timeline_months = max(12, min(24, timeline_months))
    fixed["timeline_months"] = timeline_months

    durations = _phase_spans(timeline_months, len(phases))

    repaired: List[Dict] = []
    for i, phase in enumerate(phases, start=1):
        repaired.append(_ensure_phase_shape(phase, role, i, durations[i - 1]))

    repaired = _distribute_uncovered_skills(repaired, missing_skills, level)

    # Rebuild dependent fields after skills changed.
    final_phases: List[Dict] = []
    for i, phase in enumerate(repaired, start=1):
        duration = durations[i - 1]
        phase = _ensure_phase_shape(phase, role, i, duration)
        final_phases.append(phase)

    fixed["phases"] = final_phases

    if not str(fixed.get("title") or "").strip():
        fixed["title"] = f"{level.title()} Roadmap for {role}"

    if not str(fixed.get("summary") or "").strip():
        fixed["summary"] = (
            f"This {timeline_months}-month roadmap is tailored for {role} and prioritizes "
            "missing skills in a phase-by-phase sequence with practical project milestones."
        )

    # Keep ai_enhanced truthful: true only if enriched fields are populated.
    fixed["ai_enhanced"] = any(
        bool(p.get("enhanced_description"))
        or bool(p.get("learning_objectives"))
        or bool(p.get("recommended_resources"))
        for p in final_phases
    )

    missing_clean = _clean_list(missing_skills)
    covered = {
        s.strip().lower()
        for p in final_phases
        for s in p.get("skills_to_learn", [])
        if str(s).strip()
    }
    coverage_pct = 100.0
    if missing_clean:
        matched = sum(1 for s in missing_clean if s.lower() in covered)
        coverage_pct = round((matched / len(missing_clean)) * 100, 2)

    quality_report = {
        "phase_count": len(final_phases),
        "timeline_months": timeline_months,
        "coverage_pct": coverage_pct,
        "all_phases_have_objectives": all(bool(p.get("learning_objectives")) for p in final_phases),
        "all_phases_have_resources": all(bool(p.get("recommended_resources")) for p in final_phases),
        "resources_all_strings": all(
            isinstance(item, str)
            for p in final_phases
            for item in (p.get("recommended_resources") or [])
        ),
    }

    return fixed, quality_report
