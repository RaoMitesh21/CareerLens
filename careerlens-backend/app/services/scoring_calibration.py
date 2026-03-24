"""
scoring_calibration.py
----------------------
Role-family calibration profiles for scoring weights and confidence thresholds.

Profiles can be generated from datasets via scripts/build_scoring_calibration.py
and saved to app/static/scoring_calibration.json.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List


DEFAULT_PROFILE = {
    "version": 1,
    "global": {
        "weights": {"core": 0.72, "secondary": 0.2, "bonus": 0.08},
        "confidence_thresholds": {"core": 0.24, "secondary": 0.22, "bonus": 0.2},
        "core_terms": [],
    },
    "families": {
        "data": {
            "weights": {"core": 0.75, "secondary": 0.18, "bonus": 0.07},
            "confidence_thresholds": {"core": 0.23, "secondary": 0.21, "bonus": 0.2},
            "core_terms": ["analysis", "statistics", "sql", "dashboard", "etl", "data"],
        },
        "backend": {
            "weights": {"core": 0.74, "secondary": 0.19, "bonus": 0.07},
            "confidence_thresholds": {"core": 0.24, "secondary": 0.22, "bonus": 0.2},
            "core_terms": ["api", "database", "backend", "service", "microservice", "sql"],
        },
        "frontend": {
            "weights": {"core": 0.73, "secondary": 0.19, "bonus": 0.08},
            "confidence_thresholds": {"core": 0.24, "secondary": 0.22, "bonus": 0.2},
            "core_terms": ["ui", "react", "css", "frontend", "javascript", "component"],
        },
        "ai_ml": {
            "weights": {"core": 0.76, "secondary": 0.17, "bonus": 0.07},
            "confidence_thresholds": {"core": 0.23, "secondary": 0.21, "bonus": 0.2},
            "core_terms": ["machine", "learning", "model", "python", "training", "nlp"],
        },
        "devops": {
            "weights": {"core": 0.75, "secondary": 0.18, "bonus": 0.07},
            "confidence_thresholds": {"core": 0.24, "secondary": 0.22, "bonus": 0.2},
            "core_terms": ["cloud", "docker", "kubernetes", "ci", "cd", "monitoring"],
        },
        "security": {
            "weights": {"core": 0.77, "secondary": 0.16, "bonus": 0.07},
            "confidence_thresholds": {"core": 0.25, "secondary": 0.22, "bonus": 0.2},
            "core_terms": ["security", "risk", "threat", "incident", "compliance", "audit"],
        },
        "product": {
            "weights": {"core": 0.7, "secondary": 0.22, "bonus": 0.08},
            "confidence_thresholds": {"core": 0.23, "secondary": 0.21, "bonus": 0.2},
            "core_terms": ["stakeholder", "roadmap", "product", "requirements", "planning"],
        },
        "general": {
            "weights": {"core": 0.72, "secondary": 0.2, "bonus": 0.08},
            "confidence_thresholds": {"core": 0.24, "secondary": 0.22, "bonus": 0.2},
            "core_terms": [],
        },
    },
}


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = max(1e-9, float(weights.get("core", 0)) + float(weights.get("secondary", 0)) + float(weights.get("bonus", 0)))
    return {
        "core": round(float(weights.get("core", 0)) / total, 4),
        "secondary": round(float(weights.get("secondary", 0)) / total, 4),
        "bonus": round(float(weights.get("bonus", 0)) / total, 4),
    }


def _profile_path() -> Path:
    env_path = os.getenv("SCORING_CALIBRATION_PATH", "").strip()
    if env_path:
        return Path(env_path)

    return Path(__file__).resolve().parents[1] / "static" / "scoring_calibration.json"


def infer_role_family(role: str) -> str:
    text = (role or "").strip().lower()

    family_keywords = {
        "data": ["data", "analyst", "bi", "business intelligence", "etl", "analytics"],
        "backend": ["backend", "server", "api", "microservice", "java", "spring", "django", "fastapi"],
        "frontend": ["frontend", "front end", "ui", "ux", "react", "angular", "vue", "web"],
        "ai_ml": ["ml", "machine learning", "ai", "nlp", "data scientist", "llm"],
        "devops": ["devops", "sre", "cloud", "kubernetes", "docker", "infrastructure"],
        "security": ["security", "cyber", "soc", "threat", "iam", "pentest"],
        "product": ["product", "project manager", "business analyst", "owner", "scrum"],
    }

    for family, keywords in family_keywords.items():
        if any(k in text for k in keywords):
            return family
    return "general"


@lru_cache(maxsize=1)
def load_calibration_profile() -> Dict:
    base = json.loads(json.dumps(DEFAULT_PROFILE))
    path = _profile_path()

    if not path.exists():
        return base

    try:
        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
    except Exception:
        return base

    if not isinstance(loaded, dict):
        return base

    global_loaded = loaded.get("global", {}) if isinstance(loaded.get("global", {}), dict) else {}
    global_weights = global_loaded.get("weights", {}) if isinstance(global_loaded.get("weights", {}), dict) else {}
    global_conf = global_loaded.get("confidence_thresholds", {}) if isinstance(global_loaded.get("confidence_thresholds", {}), dict) else {}
    global_terms = global_loaded.get("core_terms", []) if isinstance(global_loaded.get("core_terms", []), list) else []

    base["global"]["weights"].update({k: float(v) for k, v in global_weights.items() if k in {"core", "secondary", "bonus"}})
    base["global"]["confidence_thresholds"].update({k: float(v) for k, v in global_conf.items() if k in {"core", "secondary", "bonus"}})
    base["global"]["core_terms"] = [str(x).lower() for x in global_terms if isinstance(x, str)]

    families = loaded.get("families", {}) if isinstance(loaded.get("families", {}), dict) else {}
    for family, cfg in families.items():
        if family not in base["families"] or not isinstance(cfg, dict):
            continue
        cfg_w = cfg.get("weights", {}) if isinstance(cfg.get("weights", {}), dict) else {}
        cfg_c = cfg.get("confidence_thresholds", {}) if isinstance(cfg.get("confidence_thresholds", {}), dict) else {}
        cfg_t = cfg.get("core_terms", []) if isinstance(cfg.get("core_terms", []), list) else []

        base["families"][family]["weights"].update({k: float(v) for k, v in cfg_w.items() if k in {"core", "secondary", "bonus"}})
        base["families"][family]["confidence_thresholds"].update({k: float(v) for k, v in cfg_c.items() if k in {"core", "secondary", "bonus"}})
        base["families"][family]["core_terms"] = [str(x).lower() for x in cfg_t if isinstance(x, str)]

    return base


def get_scoring_profile_for_role(role: str) -> Dict:
    all_profiles = load_calibration_profile()
    family = infer_role_family(role)

    global_cfg = all_profiles.get("global", {})
    family_cfg = all_profiles.get("families", {}).get(family, all_profiles.get("families", {}).get("general", {}))

    weights = dict(global_cfg.get("weights", {}))
    weights.update(family_cfg.get("weights", {}))
    weights = _normalize_weights(weights)

    conf = dict(global_cfg.get("confidence_thresholds", {}))
    conf.update(family_cfg.get("confidence_thresholds", {}))

    terms: List[str] = []
    terms.extend([str(x).lower() for x in global_cfg.get("core_terms", []) if isinstance(x, str)])
    terms.extend([str(x).lower() for x in family_cfg.get("core_terms", []) if isinstance(x, str)])
    terms = sorted(set(t for t in terms if t))

    return {
        "role_family": family,
        "weights": {
            "core": float(weights.get("core", 0.72)),
            "secondary": float(weights.get("secondary", 0.2)),
            "bonus": float(weights.get("bonus", 0.08)),
        },
        "confidence_thresholds": {
            "core": float(conf.get("core", 0.24)),
            "secondary": float(conf.get("secondary", 0.22)),
            "bonus": float(conf.get("bonus", 0.2)),
        },
        "core_terms": terms,
    }
