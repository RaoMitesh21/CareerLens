"""
Build role-family scoring calibration from available datasets.

Usage:
  cd careerlens-backend
  PYTHONPATH=. python scripts/build_scoring_calibration.py
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Set

import pandas as pd

from app.services.scoring_calibration import DEFAULT_PROFILE, infer_role_family
from app.core.database import SessionLocal
from app.models.esco import Occupation, OccupationSkill

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "Datasets"
OUT_FILE = Path(__file__).resolve().parents[1] / "app" / "static" / "scoring_calibration.json"

DATA_CSV = DATASETS / "data.csv"
RESUME_CSV = DATASETS / "Resume.csv"
SO_PUBLIC = DATASETS / "stack-overflow-developer-survey-2025" / "survey_results_public.csv"
ESCO_SKILLS_CSV = DATASETS / "ESCO csv" / "skills.csv"

STOPWORDS = {
    "and", "the", "for", "with", "that", "this", "from", "into", "your", "have", "has", "will", "you",
    "are", "our", "their", "using", "use", "used", "job", "role", "required", "requirements", "experience",
    "years", "year", "work", "working", "skills", "skill", "ability", "strong", "plus", "preferred", "team",
    "data", "software", "system", "systems", "business", "technical", "including", "across", "within",
    "analysis", "manage", "management", "support", "development", "design", "build", "maintain", "improve",
    "project", "projects", "knowledge", "tools", "tool", "responsible", "responsibilities",
    "nan", "none", "null", "na", "n/a", "etc", "all", "other", "others", "professional",
    "senior", "junior", "executive", "suite", "models", "openai", "manager", "lead", "role",
    "c-suite", "city", "state",
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z+#.-]{2,}")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    raw = TOKEN_RE.findall(text.lower())
    cleaned = []
    for raw_token in raw:
        token = raw_token.strip(" .-#+")
        if token in STOPWORDS or token.isnumeric():
            continue
        if not any(c.isalpha() for c in token):
            continue
        cleaned.append(token)
    return cleaned


def as_text(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "n/a"}:
        return ""
    return text


def enrich_family_from_text(family_counters, global_counter, family_doc_counts, family: str, text: str):
    tokens = tokenize(text)
    if not tokens:
        return
    family_doc_counts[family] += 1
    family_counters[family].update(tokens)
    global_counter.update(tokens)


def load_data_csv(family_counters, global_counter, family_doc_counts):
    if not DATA_CSV.exists():
        return

    for chunk in pd.read_csv(DATA_CSV, chunksize=1000):
        for _, row in chunk.iterrows():
            title = as_text(row.get("Job Title", ""))
            desc = as_text(row.get("Description", ""))
            family = infer_role_family(title)
            enrich_family_from_text(family_counters, global_counter, family_doc_counts, family, f"{title} {desc}")


def load_resume_csv(family_counters, global_counter, family_doc_counts):
    if not RESUME_CSV.exists():
        return

    use_cols = ["Category", "Resume_str"]
    for chunk in pd.read_csv(RESUME_CSV, chunksize=1000, usecols=use_cols):
        for _, row in chunk.iterrows():
            category = as_text(row.get("Category", ""))
            resume_text = as_text(row.get("Resume_str", ""))
            family = infer_role_family(category)
            enrich_family_from_text(family_counters, global_counter, family_doc_counts, family, f"{category} {resume_text}")


def load_stack_overflow_csv(family_counters, global_counter, family_doc_counts):
    if not SO_PUBLIC.exists():
        return

    use_cols = [
        "DevType",
        "LanguageHaveWorkedWith",
        "DatabaseHaveWorkedWith",
        "PlatformHaveWorkedWith",
        "WebframeHaveWorkedWith",
        "AIModelsHaveWorkedWith",
        "Industry",
    ]
    for chunk in pd.read_csv(SO_PUBLIC, chunksize=3000, usecols=use_cols):
        for _, row in chunk.iterrows():
            dev_type = as_text(row.get("DevType", ""))
            family = infer_role_family(dev_type)
            fields = [as_text(row.get(col, "")) for col in use_cols]
            enrich_family_from_text(family_counters, global_counter, family_doc_counts, family, " ".join(fields))


def load_esco_vocab() -> Set[str]:
    if not ESCO_SKILLS_CSV.exists():
        return set()

    vocab: Set[str] = set()
    use_cols = ["PREFERREDLABEL", "ALTLABELS"]
    for chunk in pd.read_csv(ESCO_SKILLS_CSV, chunksize=20000, usecols=use_cols, dtype=str):
        for _, row in chunk.iterrows():
            pref = as_text(row.get("PREFERREDLABEL", ""))
            alts = as_text(row.get("ALTLABELS", ""))

            for token in tokenize(pref):
                vocab.add(token)

            if alts:
                for alt in re.split(r"[;|]", alts):
                    for token in tokenize(alt):
                        vocab.add(token)

    return vocab


def top_terms_for_family(
    family: str,
    family_counters,
    global_counter,
    family_doc_counts,
    esco_vocab: Set[str],
    top_n: int = 25,
) -> list[str]:
    counts = family_counters[family]
    doc_count = max(1, family_doc_counts[family])

    scored = []
    for token, freq in counts.items():
        if esco_vocab and token not in esco_vocab:
            continue
        if freq < 4:
            continue
        global_freq = global_counter[token]
        # Simple discriminative score: family density vs corpus prevalence.
        density = freq / doc_count
        specificity = math.log((global_counter.total() + 1) / (global_freq + 1))
        score = density * max(0.2, specificity)
        scored.append((score, token))

    scored.sort(reverse=True)
    return [token for _, token in scored[:top_n]]


def calibrate_family_weights_from_esco(profile: Dict) -> Dict:
    """Use ESCO essential/optional ratios to tune family weights."""
    db = SessionLocal()
    try:
        occ_rows = db.query(Occupation.id, Occupation.preferred_label).all()
        if not occ_rows:
            return profile

        rel_rows = db.query(OccupationSkill.occupation_id, OccupationSkill.relation_type).all()
        rel_map: Dict[int, Dict[str, int]] = defaultdict(lambda: {"essential": 0, "optional": 0})
        for occ_id, rel_type in rel_rows:
            if rel_type == "essential":
                rel_map[occ_id]["essential"] += 1
            elif rel_type == "optional":
                rel_map[occ_id]["optional"] += 1

        family_ratios: Dict[str, list[float]] = defaultdict(list)
        for occ_id, label in occ_rows:
            counts = rel_map.get(occ_id)
            if not counts:
                continue
            essential = counts["essential"]
            optional = counts["optional"]
            total = essential + optional
            if total == 0:
                continue

            family = infer_role_family(label or "")
            family_ratios[family].append(essential / total)

        for family, ratios in family_ratios.items():
            if family not in profile.get("families", {}):
                continue
            avg_ratio = sum(ratios) / max(1, len(ratios))

            # Map essential-ratio to a core-first but bounded weight profile.
            core = max(0.68, min(0.82, 0.62 + 0.28 * avg_ratio))
            remaining = 1.0 - core
            secondary = remaining * 0.72
            bonus = remaining * 0.28

            profile["families"][family]["weights"] = {
                "core": round(core, 4),
                "secondary": round(secondary, 4),
                "bonus": round(bonus, 4),
            }

        return profile
    finally:
        db.close()


def build_profile() -> dict:
    profile = json.loads(json.dumps(DEFAULT_PROFILE))

    family_counters = defaultdict(Counter)
    global_counter = Counter()
    family_doc_counts = defaultdict(int)
    esco_vocab = load_esco_vocab()

    load_data_csv(family_counters, global_counter, family_doc_counts)
    load_resume_csv(family_counters, global_counter, family_doc_counts)
    load_stack_overflow_csv(family_counters, global_counter, family_doc_counts)

    for family in profile.get("families", {}).keys():
        terms = top_terms_for_family(
            family,
            family_counters,
            global_counter,
            family_doc_counts,
            esco_vocab,
            top_n=25,
        )
        if terms:
            profile["families"][family]["core_terms"] = terms

    profile = calibrate_family_weights_from_esco(profile)

    profile["generated_from"] = {
        "data_csv": str(DATA_CSV),
        "resume_csv": str(RESUME_CSV),
        "stack_overflow_csv": str(SO_PUBLIC),
    }

    return profile


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    profile = build_profile()
    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print(f"Calibration profile written: {OUT_FILE}")
    for family, cfg in profile.get("families", {}).items():
        terms = cfg.get("core_terms", [])[:8]
        print(f"{family:10s} -> {', '.join(terms)}")


if __name__ == "__main__":
    main()
