"""
app/routers/analyze.py — Analysis Endpoints
==============================================

POST /analyze         — Full gap analysis (3-tier scoring)
POST /analyze/full    — Gap analysis + roadmap in one call
POST /analyze/basic   — Legacy v0.2 simple scoring
POST /analyze/batch   — Rank multiple resumes vs one target role
POST /analyze/batch/hybrid — Hybrid ESCO+O*NET ranking
GET  /analyze         — Usage info
"""

import asyncio
import os
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analyze import (
    AnalyzeRequest,
    GapAnalysisResponse,
    AnalyzeWithRoadmapResponse,
    HybridAnalyzeResponse,
    BasicAnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    BatchCandidateResult,
)
from app.services.scoring import advanced_analyze
from app.services.analyzer import calculate_esco_score
from app.services.llm_analysis_enhancer import enhance_analysis_async
from app.services.llm_roadmap_enhancer import InferenceMode, enhance_roadmap_async
from app.services.roadmap_quality import enforce_roadmap_quality
from app.services.roadmap_generator import generate_roadmap
from app.services.hybrid_alignment import compute_onet_alignment, fuse_esco_onet_score

router = APIRouter(prefix="/analyze", tags=["Analysis"])


_LANGUAGE_PATTERNS = [
    (re.compile(r"\bjavascript\b", re.IGNORECASE), "JavaScript"),
    (re.compile(r"\btypescript\b", re.IGNORECASE), "TypeScript"),
    (re.compile(r"\bpython\b", re.IGNORECASE), "Python"),
    (re.compile(r"\bjava\b", re.IGNORECASE), "Java"),
    (re.compile(r"\bc\+\+\b", re.IGNORECASE), "C++"),
    (re.compile(r"\bc#\b", re.IGNORECASE), "C#"),
    (re.compile(r"\bgolang\b|\bgo\b", re.IGNORECASE), "Go"),
    (re.compile(r"\bruby\b", re.IGNORECASE), "Ruby"),
    (re.compile(r"\bphp\b", re.IGNORECASE), "PHP"),
    (re.compile(r"\bsql\b", re.IGNORECASE), "SQL"),
    (re.compile(r"\bhtml\b", re.IGNORECASE), "HTML"),
    (re.compile(r"\bcss\b", re.IGNORECASE), "CSS"),
    (re.compile(r"\brust\b", re.IGNORECASE), "Rust"),
    (re.compile(r"\bswift\b", re.IGNORECASE), "Swift"),
    (re.compile(r"\bkotlin\b", re.IGNORECASE), "Kotlin"),
]


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        item = (value or "").strip()
        if not item:
            continue
        key = _normalize_text(item)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _split_language_vs_other(skills: list[str]) -> tuple[list[str], list[str]]:
    language: list[str] = []
    other: list[str] = []
    for skill in skills:
        label = (skill or "").strip()
        if not label:
            continue
        if any(pattern.search(label) for pattern, _ in _LANGUAGE_PATTERNS):
            language.append(label)
        else:
            other.append(label)
    return _unique_keep_order(language), _unique_keep_order(other)


def _detect_languages_from_resume(resume_text: str) -> list[str]:
    found: list[str] = []
    text = resume_text or ""
    for pattern, label in _LANGUAGE_PATTERNS:
        if pattern.search(text):
            found.append(label)
    return _unique_keep_order(found)


def _comprehensive_classification(decision: float, core: float, overall: float, risk: str) -> dict[str, str]:
    risk_norm = (risk or "").strip().lower()
    if decision >= 80 and core >= 70 and risk_norm == "low":
        return {
            "label": "High Priority Shortlist",
            "summary": "Strong technical alignment with low delivery risk.",
        }
    if decision >= 65 and core >= 55:
        return {
            "label": "Interview Recommended",
            "summary": "Solid role fit with manageable skill gaps.",
        }
    if overall >= 45:
        return {
            "label": "Conditional Review",
            "summary": "Potential match if role priorities are flexible.",
        }
    return {
        "label": "Future Pipeline",
        "summary": "Not ideal for this opening, but may fit future roles.",
    }


def _resolve_inference_mode() -> InferenceMode:
    """Resolve inference mode from environment with safe default."""
    mode_raw = os.getenv("INFERENCE_MODE", "mock").strip().lower()
    mode_map = {
        "mock": InferenceMode.MOCK,
        "hf_api": InferenceMode.HF_API,
        "local": InferenceMode.LOCAL,
    }
    return mode_map.get(mode_raw, InferenceMode.MOCK)


def _normalize_target_role(target_role: str) -> str:
    role = (target_role or "").strip()
    key = role.lower()

    alias_map = {
        "full stack developer": "web developer",
        "full-stack developer": "web developer",
        "fullstack developer": "web developer",
        "frontend developer": "web developer",
        "front-end developer": "web developer",
        "front end developer": "web developer",
        "backend developer": "software developer",
        "back-end developer": "software developer",
        "back end developer": "software developer",
        "sde": "software developer",
    }

    return alias_map.get(key, role)


def _run_async_with_timeout(coro, timeout_seconds: float = 8.0):
    """Run async enhancer work with an upper bound to avoid request hangs."""
    return asyncio.run(asyncio.wait_for(coro, timeout=timeout_seconds))


# ── Info ────────────────────────────────────────────────────────────
@router.get("")
def analyze_info():
    """Usage info for the analysis endpoints."""
    return {
        "message": "Use POST /analyze for gap analysis.",
        "endpoints": {
            "POST /analyze": "3-tier skill gap analysis",
            "POST /analyze/full": "Gap analysis + learning roadmap",
            "POST /analyze/basic": "Legacy simple weighted score",
        },
        "usage": {
            "method": "POST",
            "url": "/analyze",
            "body": {
                "resume_text": "Your full resume text…",
                "target_occupation": "software developer",
            },
        },
        "tip": "Open /docs for interactive Swagger UI.",
    }


# ── Gap Analysis ────────────────────────────────────────────────────
@router.post(
    "",
    response_model=GapAnalysisResponse,
    summary="Skill-gap analysis",
)
def analyze_resume(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    **3-tier resume analysis** against an ESCO occupation.

    Returns overall score (0-100), per-tier breakdowns, matched/missing
    skills, confidence details, and a human-readable summary.
    """
    normalized_target = _normalize_target_role(request.target_occupation)
    result = advanced_analyze(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    mode = _resolve_inference_mode()
    try:
        result = _run_async_with_timeout(
            enhance_analysis_async(
                base_analysis=result,
                mode=mode,
            ),
            timeout_seconds=8.0,
        )
    except Exception:
        pass

    # Strip internal keys before returning
    clean = {k: v for k, v in result.items() if not k.startswith("_")}
    return clean


@router.post(
    "/hybrid",
    response_model=HybridAnalyzeResponse,
    summary="Hybrid ESCO + O*NET analysis",
)
def analyze_resume_hybrid(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Additive hybrid endpoint that preserves ESCO as primary scoring while
    blending in O*NET alignment as a secondary signal.
    """
    normalized_target = _normalize_target_role(request.target_occupation)
    base = advanced_analyze(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    if "error" in base:
        raise HTTPException(status_code=404, detail=base["error"])

    onet = compute_onet_alignment(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    fused = fuse_esco_onet_score(
        esco_score=float(base.get("overall_score", 0.0)),
        onet_score=float(onet.get("skill_match_score", 0.0)),
        onet_available=bool(onet.get("available")),
    )

    analysis_clean = {k: v for k, v in base.items() if not k.startswith("_")}
    return {
        "analysis": analysis_clean,
        "fused_score": fused,
        "fusion_strategy": "weighted_esco_primary_82_18_onet",
        "onet": onet,
    }


@router.post(
    "/hybrid/diagnostics",
    summary="Hybrid diagnostics (ESCO vs O*NET)",
)
def analyze_resume_hybrid_diagnostics(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Debug-oriented hybrid endpoint for tuning and validation.
    Additive only: does not alter any existing endpoint behavior.
    """
    normalized_target = _normalize_target_role(request.target_occupation)
    base = advanced_analyze(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    if "error" in base:
        raise HTTPException(status_code=404, detail=base["error"])

    onet = compute_onet_alignment(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    fused = fuse_esco_onet_score(
        esco_score=float(base.get("overall_score", 0.0)),
        onet_score=float(onet.get("skill_match_score", 0.0)),
        onet_available=bool(onet.get("available")),
    )

    return {
        "target_role": request.target_occupation,
        "esco_overall_score": base.get("overall_score", 0.0),
        "onet_skill_match_score": onet.get("skill_match_score", 0.0),
        "fused_score": fused,
        "fusion_strategy": "weighted_esco_primary_82_18_onet",
        "onet_matched_role": onet.get("matched_role"),
        "onet_available": onet.get("available", False),
        "onet_match_breakdown": onet.get("match_breakdown", {}),
        "onet_matched_via_alias": onet.get("matched_via_alias", []),
        "top_missing_esco": (base.get("missing_skills") or [])[:10],
        "top_missing_onet": (onet.get("missing_skills") or [])[:10],
    }


# ── Gap Analysis + Roadmap ──────────────────────────────────────────
@router.post(
    "/full",
    response_model=AnalyzeWithRoadmapResponse,
    summary="Analysis + learning roadmap",
)
def analyze_with_roadmap(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Full analysis **plus** a personalised learning roadmap in one call.
    """
    normalized_target = _normalize_target_role(request.target_occupation)
    result = advanced_analyze(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    mode = _resolve_inference_mode()

    try:
        result = _run_async_with_timeout(
            enhance_analysis_async(
                base_analysis=result,
                mode=mode,
            ),
            timeout_seconds=8.0,
        )
    except Exception:
        pass

    roadmap = generate_roadmap(
        overall_score=result["overall_score"],
        role=result["role"],
        missing_core=result.get("_missing_core", []),
        missing_secondary=result.get("_missing_secondary", []),
        missing_bonus=result.get("_missing_bonus", []),
    )

    try:
        roadmap = _run_async_with_timeout(
            enhance_roadmap_async(
                base_roadmap=roadmap,
                role=result["role"],
                mode=mode,
            ),
            timeout_seconds=8.0,
        )
    except Exception:
        # Fall back to deterministic roadmap if enhancement fails.
        pass

    # Strict quality gate: repair incomplete/static fields and enforce relevance.
    roadmap, _quality = enforce_roadmap_quality(
        roadmap=roadmap,
        role=result["role"],
        missing_skills=result.get("missing_skills", []),
    )

    # Strip internal keys
    analysis = {k: v for k, v in result.items() if not k.startswith("_")}
    return {"analysis": analysis, "roadmap": roadmap}


# ── Legacy Basic Analysis ──────────────────────────────────────────
@router.post(
    "/basic",
    response_model=BasicAnalyzeResponse,
    summary="Basic weighted score (legacy)",
)
def analyze_resume_basic(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """Legacy v0.2 essential/optional weighted score."""
    normalized_target = _normalize_target_role(request.target_occupation)
    result = calculate_esco_score(
        resume_text=request.resume_text,
        target_role=normalized_target,
        db=db,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Batch Ranking ───────────────────────────────────────────────────
@router.post(
    "/batch",
    response_model=BatchAnalyzeResponse,
    summary="Rank multiple candidates vs one role",
)
def analyze_batch(
    request: BatchAnalyzeRequest,
    db: Session = Depends(get_db),
):
    return _analyze_batch_impl(request=request, db=db, use_hybrid=False)


@router.post(
    "/batch/hybrid",
    response_model=BatchAnalyzeResponse,
    summary="Rank multiple candidates with hybrid ESCO + O*NET scoring",
)
def analyze_batch_hybrid(
    request: BatchAnalyzeRequest,
    db: Session = Depends(get_db),
):
    return _analyze_batch_impl(request=request, db=db, use_hybrid=True)


def _analyze_batch_impl(
    request: BatchAnalyzeRequest,
    db: Session,
    use_hybrid: bool,
):
    """
    Analyze up to 10 resumes against one target role and return a
    ranked leaderboard sorted by overall score (highest first).

    Used by the Recruiter Dashboard to compare candidates automatically.
    """
    ranked: list[BatchCandidateResult] = []
    normalized_target = _normalize_target_role(request.target_occupation)

    def _match_label(score: float) -> str:
        if score >= 75:
            return "Excellent"
        if score >= 55:
            return "Good"
        if score >= 35:
            return "Fair"
        return "Weak"

    def _decision_score(
        overall: float,
        core: float,
        secondary: float,
        bonus: float,
        missing_count: int,
        total_required: int,
        core_missing_count: int,
        core_total_count: int,
    ) -> float:
        # Recruiter-first ranking: prioritize core fit, then overall role alignment.
        weighted = (0.62 * core) + (0.23 * overall) + (0.10 * secondary) + (0.05 * bonus)

        missing_ratio = (missing_count / total_required) if total_required > 0 else 0.0
        core_missing_ratio = (core_missing_count / core_total_count) if core_total_count > 0 else 0.0

        # Penalize broad gaps and missing core requirements without collapsing
        # mid-quality candidates to zero too aggressively.
        breadth_penalty = min(8.0, missing_ratio * 8.0)
        core_penalty = min(10.0, core_missing_ratio * 10.0)

        # Boost when core coverage is meaningfully strong to stabilize top ordering.
        core_coverage = 1.0 - core_missing_ratio if core_total_count > 0 else 0.0
        core_boost = 8.0 * max(0.0, core_coverage - 0.35)

        return max(0.0, min(100.0, weighted - breadth_penalty - core_penalty + core_boost))

    def _risk_level(core: float, missing_count: int, total_required: int) -> str:
        missing_ratio = (missing_count / total_required) if total_required > 0 else 0.0
        if core >= 72 and missing_ratio <= 0.30:
            return "Low"
        if core >= 52 and missing_ratio <= 0.50:
            return "Medium"
        return "High"

    def _recommendation(decision: float, risk: str) -> str:
        if decision >= 80 and risk == "Low":
            return "Strong Shortlist"
        if decision >= 65:
            return "Shortlist"
        if decision >= 45:
            return "Review"
        return "Hold"

    for item in request.resumes:
        resume_text = re.sub(r"\s+", " ", str(item.resume_text or "")).strip()[:12000]

        result = advanced_analyze(
            resume_text=resume_text,
            target_role=normalized_target,
            db=db,
        )
        if "error" in result:
            # Hybrid mode fallback: keep candidate evaluable via O*NET when ESCO role mapping is weak.
            if not use_hybrid:
                continue

            onet = compute_onet_alignment(
                resume_text=resume_text,
                target_role=normalized_target,
                db=db,
            )
            if not bool(onet.get("available")):
                continue

            onet_score = float(onet.get("skill_match_score", 0.0))
            onet_matched = _unique_keep_order(list(onet.get("matched_skills", [])))
            onet_missing = _unique_keep_order(list(onet.get("missing_skills", [])))
            onet_total = max(int(onet.get("total_skills", 0)), len(onet_matched) + len(onet_missing), 1)
            onet_missing_ratio = len(onet_missing) / onet_total

            fallback_core = round(onet_score, 1)
            fallback_secondary = round(max(0.0, onet_score * 0.85), 1)
            fallback_bonus = round(max(0.0, onet_score * 0.70), 1)
            fallback_decision = max(
                0.0,
                min(
                    100.0,
                    (0.78 * onet_score) + (0.22 * fallback_core) - min(10.0, onet_missing_ratio * 12.0),
                ),
            )
            fallback_risk = _risk_level(
                core=fallback_core,
                missing_count=len(onet_missing),
                total_required=onet_total,
            )
            fallback_reco = _recommendation(fallback_decision, fallback_risk)
            fallback_languages = _detect_languages_from_resume(resume_text)
            fallback_language_matched = _unique_keep_order([s for s in onet_matched if s in fallback_languages])
            fallback_language_missing = _unique_keep_order([s for s in onet_missing if s in fallback_languages])

            ranked.append(
                BatchCandidateResult(
                    candidate_name=item.candidate_name or f"Candidate {len(ranked) + 1}",
                    rank=0,
                    overall_score=round(onet_score, 1),
                    decision_score=round(fallback_decision, 1),
                    core_match=fallback_core,
                    secondary_match=fallback_secondary,
                    bonus_match=fallback_bonus,
                    matched_count=len(onet_matched),
                    missing_count=len(onet_missing),
                    skill_coverage_ratio=round((len(onet_matched) / onet_total) * 100, 1),
                    match_label=_match_label(fallback_decision),
                    risk_level=fallback_risk,
                    recommendation=fallback_reco,
                    comprehensive_classification=_comprehensive_classification(
                        decision=fallback_decision,
                        core=fallback_core,
                        overall=onet_score,
                        risk=fallback_risk,
                    ),
                    skill_classification={
                        "core": {
                            "matched": onet_matched[:25],
                            "missing": onet_missing[:25],
                        },
                        "language": {
                            "matched": fallback_language_matched,
                            "missing": fallback_language_missing,
                        },
                        "other": {
                            "matched": onet_matched[:25],
                            "missing": onet_missing[:25],
                        },
                    },
                    top_strengths=onet_matched[:4],
                    top_gaps=onet_missing[:4],
                )
            )
            continue

        meta = result.get("meta", {})
        hybrid_overall_score = float(result["overall_score"])
        onet_score = 0.0
        onet_available = False
        if use_hybrid:
            onet = compute_onet_alignment(
                resume_text=resume_text,
                target_role=normalized_target,
                db=db,
            )
            onet_score = float(onet.get("skill_match_score", 0.0))
            onet_available = bool(onet.get("available"))
            hybrid_overall_score = fuse_esco_onet_score(
                esco_score=float(result.get("overall_score", 0.0)),
                onet_score=onet_score,
                onet_available=onet_available,
            )

        matched_count = int(meta.get("total_matched", 0))
        missing_count = int(meta.get("total_missing", 0))
        total_required = max(int(meta.get("total_required_skills", 0)), matched_count + missing_count)
        coverage_ratio = round((matched_count / total_required) * 100, 1) if total_required > 0 else 0.0
        matched_core = _unique_keep_order(list(result.get("_matched_core", [])))
        matched_secondary = _unique_keep_order(list(result.get("_matched_secondary", [])))
        matched_bonus = _unique_keep_order(list(result.get("_matched_bonus", [])))

        missing_core = _unique_keep_order(list(result.get("_missing_core", [])))
        missing_secondary = _unique_keep_order(list(result.get("_missing_secondary", [])))
        missing_bonus = _unique_keep_order(list(result.get("_missing_bonus", [])))

        core_total_count = len(matched_core) + len(missing_core)
        decision_core_score = float(result["core_match"])
        if use_hybrid and onet_available:
            # Stabilize hybrid ranking when ESCO core signal is sparse/noisy.
            decision_core_score = (0.85 * float(result["core_match"])) + (0.15 * onet_score)

        decision_score = _decision_score(
            overall=hybrid_overall_score,
            core=decision_core_score,
            secondary=float(result["secondary_match"]),
            bonus=float(result["bonus_match"]),
            missing_count=missing_count,
            total_required=total_required,
            core_missing_count=len(missing_core),
            core_total_count=core_total_count,
        )
        risk_level = _risk_level(
            core=float(result["core_match"]),
            missing_count=missing_count,
            total_required=total_required,
        )
        recommendation = _recommendation(decision_score, risk_level)

        all_matched = _unique_keep_order(matched_core + matched_secondary + matched_bonus)

        language_matched_a, core_matched_other = _split_language_vs_other(matched_core)
        language_missing_b, core_missing_other_a = _split_language_vs_other(missing_core)
        language_missing_c, other_missing_secondary = _split_language_vs_other(missing_secondary)
        language_missing_d, other_missing_bonus = _split_language_vs_other(missing_bonus)

        language_detected_resume = _detect_languages_from_resume(item.resume_text)
        language_matched = _unique_keep_order(language_matched_a + language_detected_resume)
        language_missing = _unique_keep_order(language_missing_b + language_missing_c + language_missing_d)

        other_matched = _unique_keep_order(
            core_matched_other + all_matched
        )
        other_missing = _unique_keep_order(
            core_missing_other_a + other_missing_secondary + other_missing_bonus
        )
        core_matched = _unique_keep_order([s for s in matched_core if s not in language_matched])
        core_missing = _unique_keep_order([s for s in missing_core if s not in language_missing])

        comprehensive = _comprehensive_classification(
            decision=decision_score,
            core=float(result["core_match"]),
            overall=hybrid_overall_score,
            risk=risk_level,
        )

        ranked.append(
            BatchCandidateResult(
                candidate_name=item.candidate_name or f"Candidate {len(ranked) + 1}",
                rank=0,  # filled after sort
                overall_score=round(hybrid_overall_score, 1),
                decision_score=round(decision_score, 1),
                core_match=result["core_match"],
                secondary_match=result["secondary_match"],
                bonus_match=result["bonus_match"],
                matched_count=matched_count,
                missing_count=missing_count,
                skill_coverage_ratio=coverage_ratio,
                match_label=_match_label(decision_score),
                risk_level=risk_level,
                recommendation=recommendation,
                comprehensive_classification=comprehensive,
                skill_classification={
                    "core": {
                        "matched": core_matched,
                        "missing": core_missing,
                    },
                    "language": {
                        "matched": language_matched,
                        "missing": language_missing,
                    },
                    "other": {
                        "matched": other_matched,
                        "missing": other_missing,
                    },
                },
                top_strengths=result.get("strengths", [])[:4],
                top_gaps=[p["skill"] for p in result.get("improvement_priority", [])
                          if p["priority"] == "High"][:4],
            )
        )

    # Sort descending by decision score and then by core alignment.
    ranked.sort(
        key=lambda c: (
            c.decision_score,
            c.core_match,
            c.overall_score,
            -c.missing_count,
        ),
        reverse=True,
    )
    for i, c in enumerate(ranked):
        c.rank = i + 1

    return BatchAnalyzeResponse(
        target_role=request.target_occupation,
        total_candidates=len(ranked),
        candidates=ranked,
    )
