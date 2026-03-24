"""
load_onet_data.py
-----------------
Bulk-load O*NET reference data into additive O*NET tables.

Safe-by-design: this script does NOT modify ESCO production tables,
so existing skill-gap APIs and current prototype behavior are preserved.

Usage:
  cd careerlens-backend
  python3 -m scripts.load_onet_data
"""

from __future__ import annotations

import os
import sys
from typing import Any

import pandas as pd
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine
from app.models import OnetOccupation, OnetSkill, OnetOccupationSkill


DATASET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "Datasets",
    "db_30_1_excel",
)
SKILLS_FILE = os.path.join(DATASET_DIR, "Skills.xlsx")
OCCUPATION_FILE = os.path.join(DATASET_DIR, "Occupation Data.xlsx")

CHUNK_SIZE = 2000


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _safe_str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    if not text or text.lower() == "nan":
        return None
    return text


def create_tables() -> None:
    print("Creating tables (including O*NET additive tables)...")
    Base.metadata.create_all(bind=engine)
    print("  Ready: onet_occupations, onet_skills, onet_occupation_skills")


def _read_required_file(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_excel(path)


def load_occupations(session) -> tuple[int, int]:
    print("\nLoading O*NET occupations...")
    df = _read_required_file(OCCUPATION_FILE)

    inserted = 0
    updated = 0
    for _, row in df.iterrows():
        onet_code = _safe_str(row.get("O*NET-SOC Code"))
        title = _safe_str(row.get("Title"))
        description = _safe_str(row.get("Description"))

        if not onet_code or not title:
            continue

        existing = session.execute(
            select(OnetOccupation).where(OnetOccupation.onet_code == onet_code)
        ).scalar_one_or_none()

        if existing:
            changed = False
            if existing.title != title:
                existing.title = title
                changed = True
            if (existing.description or None) != description:
                existing.description = description
                changed = True
            if changed:
                updated += 1
            continue

        session.add(
            OnetOccupation(
                onet_code=onet_code,
                title=title,
                description=description,
                source_file=os.path.basename(OCCUPATION_FILE),
            )
        )
        inserted += 1

    session.commit()
    print(f"  Occupations inserted={inserted}, updated={updated}")
    return inserted, updated


def load_skills(session) -> tuple[int, int]:
    print("\nLoading O*NET skills...")
    df = _read_required_file(SKILLS_FILE)
    unique_skills = df[["Element ID", "Element Name"]].drop_duplicates()

    inserted = 0
    updated = 0
    for _, row in unique_skills.iterrows():
        element_id = _safe_str(row.get("Element ID"))
        name = _safe_str(row.get("Element Name"))
        if not element_id or not name:
            continue

        normalized_name = _normalize_text(name)
        existing = session.execute(
            select(OnetSkill).where(OnetSkill.element_id == element_id)
        ).scalar_one_or_none()

        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.normalized_name != normalized_name:
                existing.normalized_name = normalized_name
                changed = True
            if changed:
                updated += 1
            continue

        session.add(
            OnetSkill(
                element_id=element_id,
                name=name,
                normalized_name=normalized_name,
                source_file=os.path.basename(SKILLS_FILE),
            )
        )
        inserted += 1

    session.commit()
    print(f"  Skills inserted={inserted}, updated={updated}")
    return inserted, updated


def load_occupation_skills(session) -> tuple[int, int, int]:
    print("\nLoading O*NET occupation-skill relations...")
    df = _read_required_file(SKILLS_FILE)

    importance_df = df[df["Scale ID"] == "IM"][["O*NET-SOC Code", "Element ID", "Data Value"]].copy()
    level_df = df[df["Scale ID"] == "LV"][["O*NET-SOC Code", "Element ID", "Data Value"]].copy()
    level_df = level_df.rename(columns={"Data Value": "Level Value"})
    merged = importance_df.merge(level_df, on=["O*NET-SOC Code", "Element ID"], how="left")

    occ_lookup = {o.onet_code: o.id for o in session.query(OnetOccupation).all()}
    skill_lookup = {s.element_id: s.id for s in session.query(OnetSkill).all()}
    existing_lookup = {
        (rel.occupation_id, rel.skill_id): rel
        for rel in session.query(OnetOccupationSkill).all()
    }

    inserted = 0
    updated = 0
    skipped = 0
    batch_count = 0

    for _, row in merged.iterrows():
        occ_code = _safe_str(row.get("O*NET-SOC Code"))
        element_id = _safe_str(row.get("Element ID"))

        occ_id = occ_lookup.get(occ_code)
        skill_id = skill_lookup.get(element_id)
        if not occ_id or not skill_id:
            skipped += 1
            continue

        importance = float(row["Data Value"]) if pd.notna(row.get("Data Value")) else None
        level = float(row["Level Value"]) if pd.notna(row.get("Level Value")) else None

        key = (occ_id, skill_id)
        existing = existing_lookup.get(key)
        if existing:
            changed = False
            if (existing.importance or None) != importance:
                existing.importance = importance
                changed = True
            if (existing.level or None) != level:
                existing.level = level
                changed = True
            if changed:
                updated += 1
            continue

        rel = OnetOccupationSkill(
            occupation_id=occ_id,
            skill_id=skill_id,
            importance=importance,
            level=level,
            source_file=os.path.basename(SKILLS_FILE),
        )
        session.add(rel)
        existing_lookup[key] = rel
        inserted += 1
        batch_count += 1

        if batch_count >= CHUNK_SIZE:
            session.commit()
            batch_count = 0

    session.commit()
    print(f"  Relations inserted={inserted}, updated={updated}, skipped={skipped}")
    return inserted, updated, skipped


def main() -> None:
    print("=" * 68)
    print("  CareerLens - O*NET Safe Loader (Additive Tables)")
    print("=" * 68)

    create_tables()

    session = SessionLocal()
    try:
        load_occupations(session)
        load_skills(session)
        load_occupation_skills(session)
    except Exception as err:
        session.rollback()
        print(f"\nERROR: {err}")
        raise
    finally:
        session.close()

    print("\n" + "=" * 68)
    print("  O*NET load complete (prototype-safe).")
    print("=" * 68)


if __name__ == "__main__":
    main()
