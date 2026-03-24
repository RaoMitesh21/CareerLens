"""
load_esco.py
------------
Bulk-import ESCO CSV files into the MySQL database.

Usage:
  cd careerlens-backend
  python3 -m scripts.load_esco

This script expects the ESCO CSV files at:
  ../Datasets/ESCO csv/occupations.csv
  ../Datasets/ESCO csv/skills.csv
  ../Datasets/ESCO csv/occupation_skill_relations.csv

The loader is conservative: it uses upsert semantics to avoid duplicates
and commits in batches to keep memory usage bounded.
"""

import os
import sys
import math
import pandas as pd
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal, Base
from app.models import Occupation, Skill, OccupationSkill

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'Datasets', 'ESCO csv')
OCC_FILE = os.path.join(DATA_DIR, 'occupations.csv')
SKILL_FILE = os.path.join(DATA_DIR, 'skills.csv')
REL_FILE = os.path.join(DATA_DIR, 'occupation_skill_relations.csv')

CHUNK = 5000


def _clean(val):
    """Convert pandas NaN / float-nan to None for MySQL."""
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, str) and val.strip() == '':
        return None
    return val


def create_tables():
    print('Creating tables if not exist...')
    Base.metadata.create_all(bind=engine)


def load_occupations():
    print('Loading occupations...')
    sess = SessionLocal()
    count = 0
    try:
        for chunk in pd.read_csv(OCC_FILE, chunksize=CHUNK, dtype=str, keep_default_na=False, na_values=['']):
            for _, r in chunk.iterrows():
                esco_id = _clean(r.get('ID'))
                if not esco_id:
                    continue
                exists = sess.execute(select(Occupation).where(Occupation.esco_id == esco_id)).scalar_one_or_none()
                if exists:
                    continue
                sess.add(Occupation(
                    esco_id=esco_id,
                    esco_uri=_clean(r.get('ORIGINURI')),
                    preferred_label=_clean(r.get('PREFERREDLABEL')) or _clean(r.get('PREFERRED_LABEL')) or _clean(r.get('PREFLABEL')),
                    alt_labels=_clean(r.get('ALTLABELS')),
                    description=_clean(r.get('DESCRIPTION')),
                ))
                count += 1
            sess.commit()
        print(f'  Inserted {count} occupations')
    finally:
        sess.close()


def load_skills():
    print('Loading skills...')
    sess = SessionLocal()
    count = 0
    try:
        for chunk in pd.read_csv(SKILL_FILE, chunksize=CHUNK, dtype=str, keep_default_na=False, na_values=['']):
            for _, r in chunk.iterrows():
                esco_id = _clean(r.get('ID'))
                if not esco_id:
                    continue
                exists = sess.execute(select(Skill).where(Skill.esco_id == esco_id)).scalar_one_or_none()
                if exists:
                    continue
                sess.add(Skill(
                    esco_id=esco_id,
                    esco_uri=_clean(r.get('ORIGINURI')),
                    preferred_label=_clean(r.get('PREFERREDLABEL')) or _clean(r.get('PREFERRED_LABEL')) or _clean(r.get('PREFLABEL')),
                    alt_labels=_clean(r.get('ALTLABELS')),
                    description=_clean(r.get('DESCRIPTION')),
                    skill_type=_clean(r.get('SKILLTYPE')),
                ))
                count += 1
            sess.commit()
        print(f'  Inserted {count} skills')
    finally:
        sess.close()


def load_relations():
    print('Loading occupation-skill relations...')
    sess = SessionLocal()
    try:
        # build lookup maps to avoid repeated DB queries
        skill_map = {s.esco_id: s.id for s in sess.query(Skill).all()}
        occ_map = {o.esco_id: o.id for o in sess.query(Occupation).all()}
        print(f'  Lookup maps: {len(occ_map)} occupations, {len(skill_map)} skills')

        count = 0
        skipped = 0
        for chunk in pd.read_csv(REL_FILE, chunksize=CHUNK, dtype=str, keep_default_na=False, na_values=['']):
            for _, r in chunk.iterrows():
                occ_id = _clean(r.get('OCCUPATIONID'))
                skl_id = _clean(r.get('SKILLID'))
                rel = (_clean(r.get('RELATIONTYPE')) or '').strip().lower()
                if not occ_id or not skl_id:
                    skipped += 1
                    continue
                occ_pk = occ_map.get(occ_id)
                skl_pk = skill_map.get(skl_id)
                if not occ_pk or not skl_pk:
                    skipped += 1
                    continue
                # skip if exists
                exists = sess.query(OccupationSkill).filter_by(occupation_id=occ_pk, skill_id=skl_pk).first()
                if exists:
                    skipped += 1
                    continue
                rel_type = 'essential' if 'essential' in rel else ('optional' if 'optional' in rel else 'other')
                sess.add(OccupationSkill(occupation_id=occ_pk, skill_id=skl_pk, relation_type=rel_type, source='esco-csv'))
                count += 1
                if count % 2000 == 0:
                    sess.commit()
                    print(f'    ... committed {count} relations so far')
            sess.commit()
        print(f'  Inserted {count} occupation_skill relations (skipped {skipped})')
    finally:
        sess.close()


def main():
    create_tables()
    load_occupations()
    load_skills()
    load_relations()
    print('Done! ESCO import complete.')


if __name__ == '__main__':
    main()
