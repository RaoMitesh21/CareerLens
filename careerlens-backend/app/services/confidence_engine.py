"""
confidence_engine.py — Skill Confidence Scoring  (v3 — word-boundary matching)
================================================================================

Measures HOW STRONGLY a skill appears in the resume.  Two signals:

  1. Frequency  — how many times the keyword appears (capped)
  2. Context    — did it appear in a project/experience section?

KEY DESIGN DECISIONS:
  • Scoped matching — only the occupation's required skills (~50-150) are
    checked, never all 13,896 ESCO skills.
  • Word-boundary matching — every keyword is wrapped in \\b…\\b regex so
    single-letter or short substrings can never match inside other words.
  • Minimum keyword length = 2 chars — rejects single-letter labels like
    "R", "C" that would match common text even with word boundaries.
  • Basic stemming — common suffixes (-ed, -ing, -tion, -ment, -s, -es,
    -ies, -ness) are stripped from both resume and keywords to allow
    "debugged" ↔ "debug", "provided" ↔ "provide", etc.
  • Stop-word filtering — common English words and generic domain terms
    are blocked as standalone keyword fragments.

Confidence formula:
  confidence = freq_score × 0.6 + context_score × 0.4
  freq_score = min(count / 5, 1.0)
  context_score = 1.0 if in project section, else 0.3
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session
from app.models import Skill

try:
    from rapidfuzz import fuzz as _fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False


# ── Config ──────────────────────────────────────────────────────────
FREQ_CAP = 5
FREQ_WEIGHT = 0.6
CONTEXT_WEIGHT = 0.4
CONTEXT_BONUS = 1.0
CONTEXT_BASE = 0.3
MIN_KEYWORD_LEN = 2          # reject single-char keywords like "r", "c"
MIN_SINGLE_WORD_LEN = 4      # individual words extracted from labels

# Process-level cache to avoid rebuilding keyword variants for the same skills
# on every candidate during recruiter batch analysis.
_SKILL_METADATA_CACHE: Dict[int, tuple[List[str], str]] = {}
_PATTERN_CACHE: Dict[str, re.Pattern] = {}

# Fuzzy fallback is useful for recall but can dominate latency for long resumes.
_FUZZY_MAX_RESUME_CHARS = 6000
_FUZZY_MAX_UNMATCHED_SKILLS = 80

# Section headers that indicate real project/experience usage
_PROJECT_HEADERS = re.compile(
    r"(?:^|\n)\s*(?:project|experience|work\s*history|employment|"
    r"professional\s*experience|responsibilities|achievements|"
    r"work\s*experience|key\s*project|internship)",
    re.IGNORECASE,
)

# Headers for bare skills lists (lower trust)
_LIST_HEADERS = re.compile(
    r"(?:^|\n)\s*(?:skills|technical\s*skills|tools|technologies|"
    r"certifications|education|summary|objective|profile)",
    re.IGNORECASE,
)

# Words that should NEVER be used as standalone keyword fragments.
# These are common English words AND generic domain terms that appear
# in thousands of ESCO labels and would cause false positives.
_STOP_WORDS: Set[str] = {
    # -- generic / structural --
    "use", "used", "uses", "using", "make", "made", "work", "tool",
    "tools", "system", "systems", "process", "method", "methods",
    "manage", "develop", "support", "service", "design", "ensure",
    "perform", "create", "provide", "maintain", "implement", "monitor",
    "analyse", "analyze", "operate", "prepare", "conduct", "assist",
    "apply", "report", "review", "identify", "control", "produce",
    "handle", "deliver", "execute", "measure", "follow", "select",
    "define", "assess", "evaluate", "determine", "establish", "adapt",
    "organise", "organize", "coordinate", "collaborate", "communicate",
    "present", "demonstrate", "document", "integrate", "transfer",
    "purpose", "resource", "resources", "approach", "standard",
    "standards", "procedure", "procedures", "practice", "practices",
    "technique", "techniques", "principle", "principles", "strategy",
    "programme", "program", "activity", "activities", "general",
    "specific", "relevant", "related", "appropriate", "effective",
    "necessary", "required", "various", "different", "particular",
    "individual", "professional", "technical", "quality", "information",
    "environment", "material", "equipment", "product", "products",
    "project", "customer", "client", "software", "hardware", "network",
    "database", "application", "development", "management", "research",
    "testing", "security", "performance", "business", "operations",
    "production", "company", "industry", "market", "financial",
    "health", "education", "training", "experience", "knowledge",
    "working", "results", "requirements", "objectives", "solutions",
    "issues", "problems", "changes", "conditions", "regulations",
    "policies", "technology", "communication", "relationship",
    "structure", "engineering", "analysis", "processing", "planning",
    "documentation", "compliance", "improvement", "assessment",
    "computer", "programming", "check", "checks", "complete",
    "language", "framework", "frameworks", "based", "oriented",
    "object", "data", "model", "level", "build", "learn", "skill",
    "skills", "input", "output", "basic", "class", "field", "write",
    "specification", "specifications", "migrate",
    "supervise", "supervisor",
}


# ── Data ────────────────────────────────────────────────────────────
@dataclass
class SkillConfidence:
    """Confidence details for one skill matched in the resume."""
    skill_id: int
    label: str
    raw_count: int
    in_project_section: bool
    freq_score: float
    context_score: float
    confidence: float


# ── Tokenizer ───────────────────────────────────────────────────────
def tokenize(text: str) -> str:
    """Lowercase, strip non-alphanum (keep +#), collapse whitespace."""
    return re.sub(r"[^a-z0-9+#]+", " ", (text or "").lower()).strip()


# ── Variant Generator ───────────────────────────────────────────────
def _word_variants(word: str) -> Set[str]:
    """
    Generate morphological variants of a SINGLE word so the matcher
    can find "debugged" when the skill says "debug", or "identified"
    when looking for "identify".

    Only generates plausible English inflections, not every possible
    suffix combination.
    """
    if len(word) < 3:
        return {word}

    forms: Set[str] = {word}

    # ── Forward: add common suffixes to the base ──
    # Strip trailing 'e' before adding vowel-starting suffixes
    base = word[:-1] if word.endswith("e") and len(word) > 4 else word
    forms.add(base + "ed")
    forms.add(base + "ing")
    forms.add(word + "s")
    forms.add(word + "es")
    if word.endswith("e"):
        forms.add(word + "d")   # provide → provided

    # Handle y→ied, y→ies: identify → identified, identifies
    if word.endswith("y") and len(word) > 3 and word[-2] not in "aeiouy":
        y_base = word[:-1]
        forms.add(y_base + "ied")    # identify → identified
        forms.add(y_base + "ies")    # identify → identifies
        forms.add(y_base + "ying")   # not standard but cover it

    # Double final consonant for short verbs: debug → debugged
    if (len(word) >= 4
            and word[-1] not in "aeiouy"
            and word[-2] in "aeiouy"
            and word[-3] not in "aeiouy"):
        forms.add(word + word[-1] + "ed")    # debug → debugged
        forms.add(word + word[-1] + "ing")   # debug → debugging
        forms.add(word + word[-1] + "er")    # debug → debugger

    # ── Backward: strip known suffixes to recover the root ──
    for suf in ("ation", "tion", "ment", "ness", "ence", "ance",
                "ised", "ized",
                "ings", "ling",
                "ing", "ied", "ies", "ive", "ity",
                "ise", "ize", "ful", "ous", "ist",
                "ers", "ess", "est", "ent", "ant",
                "ure", "age", "ual",
                "ed", "er", "ly", "al"):
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            root = word[: -len(suf)]
            forms.add(root)
            forms.add(root + "e")      # "provid" → "provide"
            forms.add(root + "y")      # "identif" → "identify"
            forms.add(root + "ed")
            forms.add(root + "ing")
            forms.add(root + "s")
            break  # Only strip the longest matching suffix

    return {f for f in forms if len(f) >= 2}


def _skill_keywords(
    preferred_label: str,
    alt_labels: str | None,
) -> Set[str]:
    """
    Build the complete set of keyword strings for one skill.

    Returns a set of tokenized keywords that should be matched via
    word-boundary regex against the resume text.

    Rules:
      - Full preferred_label + variants of each word
      - Full alt_labels (each entry) + variants of each word
      - Individual words from preferred_label (stop-word filtered,
        ≥ MIN_SINGLE_WORD_LEN) + their variants
    """
    keywords: Set[str] = set()

    pref = tokenize(preferred_label or "")

    # 1. Full phrase match (exact)
    if pref and len(pref) >= MIN_KEYWORD_LEN:
        keywords.add(pref)
        # Also add variant-inflected full phrases
        words = pref.split()
        for i, w in enumerate(words):
            if len(w) >= 4:
                for v in _word_variants(w):
                    inflected = words[:i] + [v] + words[i + 1:]
                    keywords.add(" ".join(inflected))

    # 2. Alt labels
    if alt_labels:
        for alt in re.split(r"[;\n]|\|", alt_labels):
            alt_tok = tokenize(alt.strip())
            if alt_tok and len(alt_tok) >= MIN_KEYWORD_LEN:
                keywords.add(alt_tok)
                awords = alt_tok.split()
                for i, w in enumerate(awords):
                    if len(w) >= 4:
                        for v in _word_variants(w):
                            inflected = awords[:i] + [v] + awords[i + 1:]
                            keywords.add(" ".join(inflected))

    # 3. Individual significant words (stop-word filtered)
    for word in pref.split():
        if len(word) >= MIN_SINGLE_WORD_LEN and word not in _STOP_WORDS:
            for v in _word_variants(word):
                if len(v) >= MIN_SINGLE_WORD_LEN and v not in _STOP_WORDS:
                    keywords.add(v)

    # Final filter: minimum length
    return {k for k in keywords if k and len(k) >= MIN_KEYWORD_LEN}


# ── Section Splitter ────────────────────────────────────────────────
def _split_resume_sections(text: str) -> Tuple[str, str]:
    """Split resume into (project_zone, other_zone) — both tokenized."""
    lines = text.split("\n")
    project_lines: List[str] = []
    other_lines: List[str] = []
    current_zone = "other"

    for line in lines:
        stripped = line.strip()
        if _PROJECT_HEADERS.search(stripped):
            current_zone = "project"
        elif _LIST_HEADERS.search(stripped):
            current_zone = "other"

        if current_zone == "project":
            project_lines.append(stripped)
        else:
            other_lines.append(stripped)

    return (
        tokenize("\n".join(project_lines)),
        tokenize("\n".join(other_lines)),
    )


# ── Word-Boundary Count ────────────────────────────────────────────
def _wb_count(pattern: re.Pattern, text: str) -> int:
    """Count regex pattern matches in text."""
    return len(pattern.findall(text))


def _make_wb_pattern(keyword: str) -> re.Pattern:
    """Compile a word-boundary regex for a keyword."""
    cached = _PATTERN_CACHE.get(keyword)
    if cached is not None:
        return cached

    escaped = re.escape(keyword)
    compiled = re.compile(r"\b" + escaped + r"\b")
    _PATTERN_CACHE[keyword] = compiled
    return compiled


# ── Keyword Map Builder (SCOPED) ───────────────────────────────────
def build_keyword_map_for_skills(
    skill_ids: Set[int],
    db: Session,
) -> Tuple[Dict[int, List[str]], Dict[int, str]]:
    """
    Build scoped skill metadata ONLY for the given skill IDs.

    Delegates to _skill_keywords() for each skill, which handles
    phrase variants, alt labels, and individual word extraction.
    """
    if not skill_ids:
        return {}, {}

    missing_ids = [sid for sid in skill_ids if sid not in _SKILL_METADATA_CACHE]
    if missing_ids:
        skills = db.query(Skill).filter(Skill.id.in_(missing_ids)).all()
        for s in skills:
            kws = list(_skill_keywords(s.preferred_label, s.alt_labels))
            label = s.preferred_label or ""
            _SKILL_METADATA_CACHE[s.id] = (kws, label)

        # Keep cache entries stable even if some ids are no longer present.
        for sid in missing_ids:
            _SKILL_METADATA_CACHE.setdefault(sid, ([], ""))

    keyword_map: Dict[int, List[str]] = {}
    label_map: Dict[int, str] = {}
    for sid in skill_ids:
        keywords, label = _SKILL_METADATA_CACHE.get(sid, ([], ""))
        keyword_map[sid] = keywords
        label_map[sid] = label

    return keyword_map, label_map


# ── Match Required Skills Against Resume ────────────────────────────
def match_skills_in_resume(
    resume_text: str,
    required_skill_ids: Set[int],
    db: Session,
) -> Tuple[Set[int], Dict[int, SkillConfidence], Dict[int, List[str]]]:
    """
    Match ONLY the occupation's required skills against the resume.

    Returns (matched_ids, confidences, keyword_map)

    Uses word-boundary regex matching and morphological variants so
    "debugged" matches "debug software" and "provided" matches
    "provide technical documentation".
    """
    keyword_map, label_map = build_keyword_map_for_skills(required_skill_ids, db)
    full_norm = tokenize(resume_text)
    project_zone, other_zone = _split_resume_sections(resume_text)

    matched: Set[int] = set()
    confidences: Dict[int, SkillConfidence] = {}

    for sid, keywords in keyword_map.items():
        best_count = 0
        found = False
        in_project = False

        for kw in keywords:
            if not kw:
                continue
            pat = _make_wb_pattern(kw)
            count = _wb_count(pat, full_norm)
            if count > 0:
                found = True
                best_count = max(best_count, count)
                if _wb_count(pat, project_zone) > 0:
                    in_project = True

        if found:
            matched.add(sid)
            freq_score = min(best_count / FREQ_CAP, 1.0)
            context_score = CONTEXT_BONUS if in_project else CONTEXT_BASE
            confidence = round(
                freq_score * FREQ_WEIGHT + context_score * CONTEXT_WEIGHT, 3
            )

            # Use pre-fetched label metadata to avoid per-skill DB queries.
            label = label_map.get(sid) or (keywords[0] if keywords else "")

            confidences[sid] = SkillConfidence(
                skill_id=sid,
                label=label,
                raw_count=best_count,
                in_project_section=in_project,
                freq_score=round(freq_score, 3),
                context_score=round(context_score, 3),
                confidence=confidence,
            )

    # ── Rapidfuzz fuzzy fallback for unmatched skills ──────────────
    # For skills not caught by exact/variant matching, try semantic
    # similarity using partial_ratio against the full resume text.
    # Only applied when rapidfuzz is installed and there are unmatched skills.
    if _RAPIDFUZZ_AVAILABLE:
        unmatched_ids = required_skill_ids - matched
        allow_fuzzy = (
            len(full_norm) <= _FUZZY_MAX_RESUME_CHARS
            and len(unmatched_ids) <= _FUZZY_MAX_UNMATCHED_SKILLS
        )
        if unmatched_ids and allow_fuzzy:
            # Fetch preferred_labels for all unmatched in one query
            unmatched_skills = (
                db.query(Skill)
                .filter(Skill.id.in_(unmatched_ids))
                .all()
            )
            for skill_obj in unmatched_skills:
                label_tok = tokenize(skill_obj.preferred_label or "")
                if len(label_tok) < 4:
                    continue  # skip trivially short labels
                # partial_ratio: finds best matching substring — ideal for
                # long resume text vs. short skill phrases
                score = _fuzz.partial_ratio(label_tok, full_norm)
                if score >= 88:  # high threshold to avoid false positives
                    matched.add(skill_obj.id)
                    # Fuzzy matches get a fixed moderate confidence
                    fuzzy_conf = round(0.28 + (score - 88) / 100 * 0.22, 3)
                    confidences[skill_obj.id] = SkillConfidence(
                        skill_id=skill_obj.id,
                        label=skill_obj.preferred_label,
                        raw_count=1,
                        in_project_section=False,
                        freq_score=0.2,
                        context_score=CONTEXT_BASE,
                        confidence=fuzzy_conf,
                    )

    return matched, confidences, keyword_map
