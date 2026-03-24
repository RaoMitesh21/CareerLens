"""
app/services/roadmap_generator.py — Rule-Based Learning Roadmap
=================================================================

Generates a personalised, structured learning roadmap based on
the gap analysis results.

Logic:
  score < 40  → Beginner roadmap  (3 phases, foundational skills)
  40–70       → Intermediate      (3 phases, targeted gap-closing)
  70+         → Advanced          (2 phases, polish & specialise)

The roadmap is built from the actual missing skills detected in
the analysis, grouped into logical phases with concrete actions.

No ML required — pure rule-based skill grouping and prioritisation.
"""

from __future__ import annotations

from typing import Dict, List
import re

from app.core.config import ROADMAP_BEGINNER_CEILING, ROADMAP_INTERMEDIATE_CEILING


# ── Helpers ─────────────────────────────────────────────────────────

def _chunk_list(items: List[str], max_per_chunk: int = 5) -> List[List[str]]:
    """Split a list into sub-lists of at most max_per_chunk items."""
    return [items[i : i + max_per_chunk] for i in range(0, len(items), max_per_chunk)]


def _determine_level(overall_score: float) -> str:
    """Map an overall score (0-100) to a roadmap difficulty level."""
    if overall_score < ROADMAP_BEGINNER_CEILING:
        return "beginner"
    elif overall_score < ROADMAP_INTERMEDIATE_CEILING:
        return "intermediate"
    return "advanced"


def _estimate_roadmap_months(level: str, role: str, total_missing: int) -> int:
    """
    Estimate total roadmap horizon in months.

    Rules:
    - Minimum 12 months for every role
    - Add months for occupation complexity
    - Add months for larger skill gaps
    - Cap at 24 months to keep plans practical
    """
    base_months = 12

    role_lc = (role or "").lower()
    complexity_bonus = 0

    # Occupation complexity boosters
    complexity_keywords = {
        "machine learning": 4,
        "ai": 4,
        "data scientist": 4,
        "cyber": 4,
        "security": 4,
        "architect": 3,
        "cloud": 3,
        "devops": 3,
        "full stack": 2,
        "software": 2,
    }

    for key, bonus in complexity_keywords.items():
        if key in role_lc:
            complexity_bonus = max(complexity_bonus, bonus)

    # Missing-skill pressure: roughly +1 month per 6 missing skills
    missing_bonus = min(8, max(0, total_missing // 6))

    # Small level adjustment keeps advanced tracks realistic but still >= 12
    level_adjust = {
        "beginner": 2,
        "intermediate": 1,
        "advanced": 0,
    }.get(level, 1)

    months = base_months + complexity_bonus + missing_bonus + level_adjust
    return max(12, min(24, months))


def _phase_spans(total_months: int, phase_count: int) -> List[str]:
    """Split total months into contiguous phase duration labels."""
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


def _skills_per_phase(level: str, total_missing: int, phase_count: int) -> int:
    """Decide a realistic number of skills per phase.

    Keep beginner plans digestible and avoid overwhelming users.
    """
    if phase_count <= 0:
        return 5

    target = (total_missing + phase_count - 1) // phase_count

    caps = {
        "beginner": 7,
        "intermediate": 8,
        "advanced": 10,
    }
    mins = {
        "beginner": 4,
        "intermediate": 5,
        "advanced": 6,
    }

    cap = caps.get(level, 16)
    min_v = mins.get(level, 5)
    return max(min_v, min(cap, target))


def _fill_skills(base: List[str], target: int, *pools: List[str]) -> List[str]:
    """Fill a phase skill list up to target using fallback pools without duplicates."""
    out: List[str] = []
    seen = set()

    def add_many(items: List[str]):
        for item in items:
            if item and item not in seen:
                seen.add(item)
                out.append(item)
            if len(out) >= target:
                break

    add_many(base)
    for pool in pools:
        if len(out) >= target:
            break
        add_many(pool)

    return out[:target]


def _role_track(role: str) -> str:
    """Map occupation name to a high-level track for dynamic roadmap writing."""
    r = (role or "").lower()
    if "data scientist" in r or "machine learning" in r or "ml" in r:
        return "data_science"
    if "data analyst" in r or "business analyst" in r or "analytics" in r:
        return "data_analyst"
    if "web" in r or "frontend" in r or "front-end" in r:
        return "web_dev"
    if "software" in r or "backend" in r or "back-end" in r or "developer" in r:
        return "software_dev"
    return "general"


def _infer_domain_tags(role: str, skills: List[str]) -> List[str]:
    """Infer broad occupation domains from role + missing skills."""
    role_text = (role or "").lower()
    skill_text = " ".join(skills or []).lower()

    def _keyword_present(text: str, keyword: str) -> bool:
        key = (keyword or "").strip().lower()
        if not key:
            return False
        # Prevent accidental substring hits (e.g., "bi" in "accessibility").
        if len(key) <= 3 or " " in key or "-" in key or "/" in key:
            return re.search(rf"\b{re.escape(key)}\b", text) is not None
        return key in text

    keyword_map = {
        "data": ["data", "analytics", "sql", "statistics", "business intelligence", "dashboard", "etl"],
        "ai_ml": ["machine learning", "ml", "ai", "model", "nlp", "computer vision"],
        "backend": ["backend", "api", "microservice", "database", "server", "spring", "django", "fastapi"],
        "frontend": ["frontend", "front-end", "ui", "ux", "react", "angular", "css", "javascript"],
        "devops": ["devops", "kubernetes", "docker", "ci", "cd", "terraform", "cloud"],
        "security": ["security", "cyber", "threat", "iam", "soc", "penetration", "incident"],
        "qa": ["qa", "quality assurance", "testing", "automation", "selenium", "cypress"],
        "mobile": ["android", "ios", "mobile", "swift", "kotlin", "flutter", "react native"],
        "product": ["product", "roadmap", "stakeholder", "requirements", "prioritization", "scrum"],
        "design": ["design", "figma", "prototype", "wireframe", "interaction", "visual"],
        "network": ["network", "routing", "switching", "tcp", "firewall"],
        "support": ["support", "service desk", "it support", "ticket", "incident management"],
        "finance": ["finance", "accounting", "audit", "tax", "compliance", "risk"],
        "healthcare": ["healthcare", "clinical", "patient", "medical", "hospital"],
    }

    tag_scores: Dict[str, int] = {}
    for tag, keys in keyword_map.items():
        score = 0
        for k in keys:
            if _keyword_present(role_text, k):
                score += 3
            if _keyword_present(skill_text, k):
                score += 1
        if score > 0:
            tag_scores[tag] = score

    if not tag_scores:
        return ["general"]

    ordered = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in ordered]


def _phase_title_focus_from_context(
    role: str,
    level: str,
    phase_num: int,
    phase_count: int,
    skills: List[str],
    domain_tags: List[str],
) -> tuple[str, str]:
    """Build phase title/focus dynamically from occupation context."""
    skill_hint = ", ".join(skills[:2]) if skills else role
    primary = domain_tags[0] if domain_tags else "general"

    starts = {
        "beginner": ["Foundation Sprint", "Applied Build Sprint", "Portfolio & Readiness Sprint"],
        "intermediate": ["Core Gap Closure Sprint", "Project Depth Sprint", "Specialization Sprint"],
        "advanced": ["Optimization Sprint", "Expert Delivery Sprint"],
    }
    focuses = {
        "data": "analytics workflow, decision metrics, and measurable insight delivery",
        "ai_ml": "model lifecycle, evaluation quality, and practical AI implementation",
        "backend": "service reliability, API quality, and scalable backend design",
        "frontend": "user experience quality, component architecture, and frontend performance",
        "devops": "delivery automation, cloud reliability, and operational excellence",
        "security": "risk reduction, secure engineering practices, and incident readiness",
        "qa": "test strategy, quality automation, and release confidence",
        "mobile": "mobile app quality, platform guidelines, and release stability",
        "product": "problem framing, prioritization quality, and delivery outcomes",
        "design": "user-centered design quality and practical product usability",
        "network": "network stability, performance diagnostics, and resilience",
        "support": "incident handling quality, troubleshooting speed, and service reliability",
        "finance": "accuracy, compliance, and decision-support reporting",
        "healthcare": "care workflow quality, compliance, and operational safety",
        "general": "core role capability and practical execution outcomes",
    }

    level_titles = starts.get(level, starts["intermediate"])
    idx = min(max(phase_num - 1, 0), len(level_titles) - 1)
    phase_label = level_titles[idx]

    if phase_count == 2 and phase_num == 2:
        title = f"Step {phase_num}: {role} Leadership and Differentiation"
    else:
        title = f"Step {phase_num}: {role} {phase_label}"

    focus = f"Strengthen {skill_hint} with focus on {focuses.get(primary, focuses['general'])}."
    return title, focus


def _domain_actions(domain_tags: List[str], role: str, skills: List[str], duration: str) -> List[str]:
    """Generate domain-aware action steps to avoid static roadmap text."""
    s1 = skills[0] if skills else "core skill"
    s2 = skills[1] if len(skills) > 1 else "secondary skill"
    tags = set(domain_tags)

    actions = [
        f"Step 1 ({duration}): Create a weekly plan focused on {s1} and {s2}, with clear output each week.",
        f"Step 2: Build one practical {role} deliverable that proves these skills in a real scenario.",
    ]

    if "data" in tags or "ai_ml" in tags:
        actions.append("Step 3: Use a real dataset, document assumptions, and present measurable insights or model outcomes.")
    elif "backend" in tags or "devops" in tags:
        actions.append("Step 3: Implement APIs/services, add tests and monitoring, and validate reliability under realistic load.")
    elif "frontend" in tags or "design" in tags:
        actions.append("Step 3: Build a user-facing flow, run usability checks, and improve accessibility/performance.")
    elif "security" in tags:
        actions.append("Step 3: Perform threat/risk checks on your solution and add security controls with evidence.")
    elif "product" in tags:
        actions.append("Step 3: Translate user/business needs into prioritized tasks and show impact metrics.")
    else:
        actions.append("Step 3: Run a project review, capture lessons learned, and refine quality based on feedback.")

    actions.append("Step 4: Publish artifacts (code/report/case study) and map remaining gaps to next-step learning goals.")
    return actions


def _parse_month_range(duration: str) -> tuple[int, int]:
    """Parse 'Months X-Y' into numeric boundaries."""
    match = re.search(r"(\d+)\s*-\s*(\d+)", duration or "")
    if not match:
        return 1, 1
    start = int(match.group(1))
    end = int(match.group(2))
    if end < start:
        end = start
    return start, end


def _track_default_skills(track: str, level: str) -> List[str]:
    """Provide role-specific fallback skills when missing lists are sparse."""
    if track == "data_science":
        if level == "beginner":
            return [
                "python fundamentals",
                "sql fundamentals",
                "statistics basics",
                "data cleaning",
                "data visualization",
                "exploratory data analysis",
            ]
        if level == "intermediate":
            return [
                "feature engineering",
                "model evaluation",
                "scikit-learn pipelines",
                "time series basics",
                "ml experimentation",
                "model interpretation",
            ]
        return [
            "model deployment",
            "mlops basics",
            "monitoring and drift",
            "cloud inference",
            "distributed training concepts",
            "advanced experimentation",
        ]

    if track == "data_analyst":
        if level == "beginner":
            return [
                "excel fundamentals",
                "sql fundamentals",
                "data cleaning",
                "dashboard basics",
                "business metrics",
                "data storytelling",
            ]
        if level == "intermediate":
            return [
                "advanced sql",
                "power bi or tableau",
                "cohort analysis",
                "funnel analysis",
                "a/b testing basics",
                "stakeholder communication",
            ]
        return [
            "forecasting",
            "causal analysis",
            "analytics engineering basics",
            "experiment design",
            "executive storytelling",
            "decision frameworks",
        ]

    if track == "web_dev":
        if level == "beginner":
            return [
                "html",
                "css",
                "javascript fundamentals",
                "responsive design",
                "git fundamentals",
                "browser debugging",
            ]
        if level == "intermediate":
            return [
                "react fundamentals",
                "state management",
                "api integration",
                "frontend testing",
                "accessibility",
                "performance optimization",
            ]
        return [
            "next.js or ssr",
            "frontend architecture",
            "design systems",
            "web security",
            "advanced performance",
            "frontend observability",
        ]

    if track == "software_dev":
        if level == "beginner":
            return [
                "programming fundamentals",
                "data structures",
                "algorithms basics",
                "git fundamentals",
                "debugging",
                "unit testing basics",
            ]
        if level == "intermediate":
            return [
                "api design",
                "database design",
                "authentication",
                "integration testing",
                "clean architecture",
                "performance tuning",
            ]
        return [
            "system design",
            "scalability patterns",
            "cloud deployment",
            "observability",
            "security hardening",
            "leadership and code review",
        ]

    return [
        "core domain fundamentals",
        "problem solving",
        "project execution",
        "tooling proficiency",
        "communication",
        "portfolio development",
    ]


def _phase_blueprint(level: str, track: str) -> List[tuple[str, str]]:
    """Return role-aware phase titles and focus areas."""
    if level == "beginner":
        if track == "data_science":
            return [
                ("Step 1: Basics and Data Foundations", "Basic programming, statistics, and data handling"),
                ("Step 2: Intermediate Modeling Skills", "Core machine learning workflow and feature work"),
                ("Step 3: Advanced Projects and Deployment", "Production-ready projects, deployment, and evaluation"),
            ]
        if track == "data_analyst":
            return [
                ("Step 1: Basics and Reporting Foundations", "Excel/SQL basics, clean datasets, and reporting"),
                ("Step 2: Intermediate Analytics", "BI tools, deeper SQL, and product analytics"),
                ("Step 3: Advanced Decision Analytics", "Forecasting, experimentation, and stakeholder impact"),
            ]
        if track == "web_dev":
            return [
                ("Step 1: Basics of Web Development", "HTML/CSS/JS and responsive UI fundamentals"),
                ("Step 2: Intermediate Frontend Engineering", "React, APIs, testing, and accessibility"),
                ("Step 3: Advanced Web Architecture", "Production architecture, performance, and security"),
            ]
        if track == "software_dev":
            return [
                ("Step 1: Basics of Software Engineering", "Programming fundamentals, debugging, and clean code"),
                ("Step 2: Intermediate Backend Engineering", "APIs, databases, and system reliability"),
                ("Step 3: Advanced System Design", "Scalability, cloud delivery, and engineering maturity"),
            ]
        return [
            ("Step 1: Basics", "Core foundations and tools"),
            ("Step 2: Intermediate Practice", "Applied project work and deeper techniques"),
            ("Step 3: Advanced Execution", "Complex projects and professional readiness"),
        ]

    if level == "intermediate":
        return [
            ("Step 1: Strengthen Core Gaps", "Close essential skill gaps with focused drills"),
            ("Step 2: Intermediate Project Depth", "Apply skills in realistic project scenarios"),
            ("Step 3: Advanced Specialization", "Differentiate with advanced projects and polish"),
        ]

    return [
        ("Step 1: Advanced Optimization", "Tune advanced capabilities and close remaining gaps"),
        ("Step 2: Expert-Level Specialization", "Lead with architecture, delivery quality, and domain depth"),
    ]


def _build_step_actions(
    role: str,
    level: str,
    phase_num: int,
    duration: str,
    skills: List[str],
    focus_area: str,
) -> List[str]:
    """Create clear, progressive, step-by-step actions for each phase."""
    start_m, end_m = _parse_month_range(duration)
    top_skills = skills[:3] if skills else ["core skills"]
    skills_text = ", ".join(top_skills)

    if level == "beginner":
        step1 = f"Step 1 (Months {start_m}-{min(end_m, start_m + 1)}): Learn the basics of {skills_text} using beginner tutorials."
        step2 = f"Step 2 (Months {start_m + 1}-{min(end_m, start_m + 2)}): Do guided practice tasks focused on {focus_area.lower()}."
        step3 = f"Step 3 (Months {start_m + 2}-{max(end_m, start_m + 2)}): Build one small {role} project using these skills."
        step4 = "Step 4: Review gaps, fix weak areas, and document what you learned in a portfolio note."
        return [step1, step2, step3, step4]

    step1 = f"Step 1: Prioritize highest-impact skills in this phase ({skills_text}) and set weekly targets."
    step2 = "Step 2: Implement two practical deliverables and validate quality with tests/reviews."
    step3 = f"Step 3: Build a portfolio-grade {role} artifact that demonstrates measurable outcomes."
    step4 = "Step 4: Run a retrospective, close remaining gaps, and prepare for the next phase depth." 
    return [step1, step2, step3, step4]


def _build_dynamic_phases(
    level: str,
    role: str,
    missing_core: List[str],
    missing_secondary: List[str],
    missing_bonus: List[str],
    total_months: int,
    max_skills_per_phase: int,
) -> List[Dict]:
    """Build role-aware, progressive, non-static roadmap phases."""
    phase_count = 2 if level == "advanced" else 3
    durations = _phase_spans(total_months, phase_count)
    track = _role_track(role)

    prioritized_skills = _clean_list(missing_core + missing_secondary + missing_bonus)
    if not prioritized_skills:
        prioritized_skills = _track_default_skills(track, level)

    domain_tags = _infer_domain_tags(role, prioritized_skills)

    phases: List[Dict] = []
    cursor = 0
    for i in range(phase_count):
        slice_skills = prioritized_skills[cursor:cursor + max_skills_per_phase]
        cursor += max_skills_per_phase

        # Top up from role defaults when gap list is short.
        if len(slice_skills) < max_skills_per_phase:
            fallback = _track_default_skills(track, level)
            for s in fallback:
                if s not in slice_skills:
                    slice_skills.append(s)
                if len(slice_skills) >= max_skills_per_phase:
                    break

        phase_skills = _clean_list(slice_skills)[:max_skills_per_phase]
        title, focus = _phase_title_focus_from_context(
            role=role,
            level=level,
            phase_num=i + 1,
            phase_count=phase_count,
            skills=phase_skills,
            domain_tags=domain_tags,
        )
        actions = _build_step_actions(
            role=role,
            level=level,
            phase_num=i + 1,
            duration=durations[i],
            skills=phase_skills,
            focus_area=focus,
        )
        actions = _clean_list(actions + _domain_actions(domain_tags, role, phase_skills, durations[i]))[:5]

        phases.append(
            {
                "phase": i + 1,
                "title": title,
                "duration": durations[i],
                "focus_area": focus,
                "skills_to_learn": phase_skills,
                "suggested_actions": actions,
            }
        )

    return phases


def _clean_list(items: List[str]) -> List[str]:
    """Normalize list while preserving order and removing duplicates."""
    out: List[str] = []
    seen = set()
    for item in items or []:
        value = str(item).strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


# ── Phase Builders ──────────────────────────────────────────────────

def _beginner_phases(
    missing_core: List[str],
    missing_secondary: List[str],
    missing_bonus: List[str],
    role: str,
    total_months: int,
    max_skills_per_phase: int,
) -> List[Dict]:
    """
    Beginner roadmap — 3 phases for someone starting from scratch.

    Phase 1: Foundations — learn the most critical core skills
    Phase 2: Build Up — remaining core + key secondary knowledge
    Phase 3: Practice — secondary + bonus, project work
    """
    core_chunks = _chunk_list(missing_core, max_skills_per_phase)
    sec_chunks = _chunk_list(missing_secondary, max_skills_per_phase)
    durations = _phase_spans(total_months, 3)

    phases = []

    # Phase 1: Foundations
    phase1_base = core_chunks[0] if core_chunks else missing_secondary[:3]
    phase1_skills = _fill_skills(
        phase1_base,
        max_skills_per_phase,
        missing_secondary,
        missing_bonus,
    )
    phases.append({
        "phase": 1,
        "title": "Build Your Foundation",
        "duration": durations[0],
        "focus_area": "Core mandatory skills",
        "skills_to_learn": phase1_skills,
        "suggested_actions": [
            f"Take an introductory online course covering {role} fundamentals",
            "Complete beginner tutorials for each listed skill",
            "Set up a development environment and practice daily",
            "Join online communities (forums, Discord) for peer support",
        ],
    })

    # Phase 2: Build Up
    phase2_base = core_chunks[1] if len(core_chunks) > 1 else sec_chunks[0] if sec_chunks else []
    phase2_skills = _fill_skills(
        phase2_base,
        max_skills_per_phase,
        missing_core,
        missing_secondary,
        missing_bonus,
    )
    phases.append({
        "phase": 2,
        "title": "Strengthen Core Competencies",
        "duration": durations[1],
        "focus_area": "Remaining core skills + key knowledge areas",
        "skills_to_learn": phase2_skills,
        "suggested_actions": [
            "Build a small portfolio project using the skills from Phase 1",
            "Study domain knowledge areas relevant to the role",
            "Read official documentation and best-practice guides",
            "Start contributing to open-source or personal projects",
        ],
    })

    # Phase 3: Practice & Expand
    phase3_base = (
        (sec_chunks[0] if sec_chunks and len(core_chunks) > 1 else
         sec_chunks[1] if len(sec_chunks) > 1 else
         missing_bonus[:max_skills_per_phase])
    )
    phase3_skills = _fill_skills(
        phase3_base,
        max_skills_per_phase,
        missing_secondary,
        missing_bonus,
        missing_core,
    )
    phases.append({
        "phase": 3,
        "title": "Apply & Expand",
        "duration": durations[2],
        "focus_area": "Secondary knowledge + hands-on projects",
        "skills_to_learn": phase3_skills,
        "suggested_actions": [
            "Complete a capstone project demonstrating all learned skills",
            "Practice mock interviews and technical assessments",
            "Write blog posts or documentation about what you've learned",
            "Update your resume with newly acquired skills and projects",
        ],
    })

    return phases


def _intermediate_phases(
    missing_core: List[str],
    missing_secondary: List[str],
    missing_bonus: List[str],
    role: str,
    total_months: int,
    max_skills_per_phase: int,
) -> List[Dict]:
    """
    Intermediate roadmap — 3 phases for targeted gap-closing.

    Phase 1: Close Critical Gaps — remaining core skills
    Phase 2: Deepen Knowledge — secondary domain knowledge
    Phase 3: Polish & Differentiate — bonus skills, portfolio
    """
    phases = []
    durations = _phase_spans(total_months, 3)

    # Phase 1: Close Critical Gaps
    phases.append({
        "phase": 1,
        "title": "Close Critical Skill Gaps",
        "duration": durations[0],
        "focus_area": "Missing core/mandatory skills",
        "skills_to_learn": _fill_skills(
            missing_core[:max_skills_per_phase],
            max_skills_per_phase,
            missing_secondary,
            missing_bonus,
        ),
        "suggested_actions": [
            "Focus intensive study on each missing core skill",
            "Take intermediate-level courses or workshops",
            "Build mini-projects that specifically exercise these skills",
            "Seek mentorship or code reviews from experienced professionals",
        ],
    })

    # Phase 2: Deepen Knowledge
    phases.append({
        "phase": 2,
        "title": "Deepen Domain Knowledge",
        "duration": durations[1],
        "focus_area": "Secondary knowledge areas",
        "skills_to_learn": _fill_skills(
            missing_secondary[:max_skills_per_phase],
            max_skills_per_phase,
            missing_core,
            missing_bonus,
        ),
        "suggested_actions": [
            "Study industry standards and best practices in depth",
            "Read technical books and research papers",
            "Attend webinars, meetups, or conferences",
            "Practice applying knowledge in real-world scenarios",
        ],
    })

    # Phase 3: Polish & Differentiate
    bonus_take = max(3, max_skills_per_phase // 2)
    core_take = max(3, max_skills_per_phase // 2)
    phase3_skills = missing_bonus[:bonus_take] + missing_core[max_skills_per_phase:max_skills_per_phase + core_take]
    phases.append({
        "phase": 3,
        "title": "Polish & Differentiate",
        "duration": durations[2],
        "focus_area": "Bonus skills + portfolio",
        "skills_to_learn": (
            _fill_skills(
                phase3_skills[:max_skills_per_phase],
                max_skills_per_phase,
                missing_bonus,
                missing_core,
                missing_secondary,
            )
            if phase3_skills
            else ["Portfolio refinement"]
        ),
        "suggested_actions": [
            "Add bonus tools and frameworks to your toolkit",
            "Refine your portfolio with polished, documented projects",
            "Prepare for technical interviews with mock sessions",
            "Tailor your resume to highlight strengths for this role",
        ],
    })

    return phases


def _advanced_phases(
    missing_core: List[str],
    missing_secondary: List[str],
    missing_bonus: List[str],
    role: str,
    total_months: int,
    max_skills_per_phase: int,
) -> List[Dict]:
    """
    Advanced roadmap — 2 phases for someone who's already strong.

    Phase 1: Fine-Tune — any remaining gaps
    Phase 2: Specialise — depth, leadership, differentiation
    """
    all_remaining = missing_core + missing_secondary[:3]
    phases = []
    durations = _phase_spans(total_months, 2)

    # Phase 1: Fine-Tune
    phases.append({
        "phase": 1,
        "title": "Fine-Tune Remaining Gaps",
        "duration": durations[0],
        "focus_area": "Minor skill gaps",
        "skills_to_learn": (
            _fill_skills(
                all_remaining[:max_skills_per_phase],
                max_skills_per_phase,
                missing_bonus,
            )
            if all_remaining
            else ["No critical gaps"]
        ),
        "suggested_actions": [
            "Address any remaining core or secondary skill gaps",
            "Deepen expertise in areas where confidence is moderate",
            "Get certifications for key technologies",
            "Contribute to high-impact open-source projects",
        ],
    })

    # Phase 2: Specialise
    phases.append({
        "phase": 2,
        "title": "Specialise & Lead",
        "duration": durations[1],
        "focus_area": "Advanced specialisation",
        "skills_to_learn": (
            _fill_skills(
                missing_bonus[:max_skills_per_phase],
                max_skills_per_phase,
                missing_secondary,
                missing_core,
            )
            if missing_bonus
            else ["Leadership", "Architecture"]
        ),
        "suggested_actions": [
            "Pursue advanced certifications or specialisations",
            "Mentor others and demonstrate leadership capability",
            "Build a standout portfolio piece or case study",
            f"Position yourself as a specialist within {role}",
        ],
    })

    return phases


# ═══════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════

def generate_roadmap(
    overall_score: float,
    role: str,
    missing_core: List[str],
    missing_secondary: List[str],
    missing_bonus: List[str],
) -> Dict:
    """
    Generate a structured, rule-based learning roadmap.

    Args:
        overall_score:     0-100 overall match score
        role:              target occupation label
        missing_core:      list of missing core skill labels
        missing_secondary: list of missing secondary skill labels
        missing_bonus:     list of missing bonus skill labels

    Returns:
        dict with keys: level, title, summary, phases
    """
    level = _determine_level(overall_score)
    total_missing = len(missing_core) + len(missing_secondary) + len(missing_bonus)
    total_months = _estimate_roadmap_months(level, role, total_missing)
    phase_count = 2 if level == "advanced" else 3
    max_skills_per_phase = _skills_per_phase(level, total_missing, phase_count)

    # Build title and summary based on level
    if level == "beginner":
        title = f"Beginner Roadmap — Getting Started as {role}"
        summary = (
            f"Your current score is {overall_score}%. This roadmap covers "
            f"{total_months} months with a step-by-step path from basics to advanced capability in {role}. "
            "Each phase keeps skill load realistic and adds practical projects so progress is clear and measurable."
        )
        phases = _build_dynamic_phases(
            level,
            role,
            missing_core,
            missing_secondary,
            missing_bonus,
            total_months,
            max_skills_per_phase,
        )

    elif level == "intermediate":
        title = f"Intermediate Roadmap — Levelling Up for {role}"
        summary = (
            f"Your current score is {overall_score}%. You have a solid base "
            f"but specific gaps remain. This {total_months}-month roadmap progresses from "
            "targeted gap-closing to deeper project execution and advanced specialization."
        )
        phases = _build_dynamic_phases(
            level,
            role,
            missing_core,
            missing_secondary,
            missing_bonus,
            total_months,
            max_skills_per_phase,
        )

    else:
        title = f"Advanced Roadmap — Mastering {role}"
        summary = (
            f"Your current score is {overall_score}%. You're well-aligned "
            f"with this role. This {total_months}-month plan focuses on advanced optimization, "
            "specialization, and high-impact delivery outcomes."
        )
        phases = _build_dynamic_phases(
            level,
            role,
            missing_core,
            missing_secondary,
            missing_bonus,
            total_months,
            max_skills_per_phase,
        )

    return {
        "level": level,
        "title": title,
        "summary": summary,
        "timeline_months": total_months,
        "phases": phases,
    }
