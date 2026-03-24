"""
scripts/evaluate_hybrid.py — ESCO vs Hybrid evaluation helper
===============================================================

Usage:
  python3 -m scripts.evaluate_hybrid \
    --input-csv ../Datasets/Resume.csv \
    --target-role "software developer" \
    --resume-col "Resume_str" \
    --name-col "Name" \
    --output-csv ./hybrid_eval_output.csv
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from app.core.database import SessionLocal
from app.services.scoring import advanced_analyze
from app.services.hybrid_alignment import compute_onet_alignment, fuse_esco_onet_score


@dataclass
class EvalRow:
    name: str
    esco_score: float
    fused_score: float
    onet_score: float
    delta: float
    onet_available: bool
    onet_role: str


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _resolve_column(row: dict[str, str], preferred: str, fallbacks: list[str]) -> str:
    keys = list(row.keys())
    lookup = {_normalize(k): k for k in keys}

    if preferred and _normalize(preferred) in lookup:
        return lookup[_normalize(preferred)]

    for candidate in fallbacks:
        key = lookup.get(_normalize(candidate))
        if key:
            return key

    raise ValueError(f"Missing expected column. Available columns: {keys}")


def _rank_map(rows: list[EvalRow], score_attr: str) -> dict[str, int]:
    ordered = sorted(rows, key=lambda item: getattr(item, score_attr), reverse=True)
    return {row.name: idx + 1 for idx, row in enumerate(ordered)}


def _rank_shift_rows(rows: list[EvalRow]) -> list[dict[str, float | int | str]]:
    esco_rank = _rank_map(rows, "esco_score")
    fused_rank = _rank_map(rows, "fused_score")

    shifts: list[dict[str, float | int | str]] = []
    for row in rows:
        prev_rank = esco_rank[row.name]
        new_rank = fused_rank[row.name]
        shifts.append(
            {
                "name": row.name,
                "esco_rank": prev_rank,
                "hybrid_rank": new_rank,
                "rank_delta": prev_rank - new_rank,
                "esco_score": row.esco_score,
                "hybrid_score": row.fused_score,
                "score_delta": row.delta,
                "onet_available": row.onet_available,
            }
        )

    return shifts


def evaluate(
    input_csv: Path,
    target_role: str,
    resume_col: str,
    name_col: str,
    max_rows: int = 0,
) -> list[EvalRow]:
    with input_csv.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV has no rows")

    resume_key = _resolve_column(
        rows[0],
        preferred=resume_col,
        fallbacks=["resume_text", "resume", "cv", "text", "Resume", "Resume_str"],
    )
    name_key = _resolve_column(
        rows[0],
        preferred=name_col,
        fallbacks=["name", "candidate_name", "candidate", "Name"],
    )

    db = SessionLocal()
    out: list[EvalRow] = []

    try:
        for idx, row in enumerate(rows, start=1):
            if max_rows > 0 and len(out) >= max_rows:
                break

            resume_text = (row.get(resume_key) or "").strip()
            candidate_name = (row.get(name_key) or "").strip() or f"Candidate {idx}"

            if len(resume_text) < 20:
                continue

            esco = advanced_analyze(resume_text=resume_text, target_role=target_role, db=db)
            if "error" in esco:
                continue

            onet = compute_onet_alignment(resume_text=resume_text, target_role=target_role, db=db)
            esco_score = float(esco.get("overall_score", 0.0))
            onet_score = float(onet.get("skill_match_score", 0.0))
            fused = fuse_esco_onet_score(
                esco_score=esco_score,
                onet_score=onet_score,
                onet_available=bool(onet.get("available")),
            )

            out.append(
                EvalRow(
                    name=candidate_name,
                    esco_score=round(esco_score, 3),
                    fused_score=round(float(fused), 3),
                    onet_score=round(onet_score, 3),
                    delta=round(float(fused) - esco_score, 3),
                    onet_available=bool(onet.get("available", False)),
                    onet_role=str(onet.get("matched_role") or ""),
                )
            )
    finally:
        db.close()

    return out


def print_summary(rows: list[EvalRow], top_k: int = 3) -> None:
    if not rows:
        print("No valid rows evaluated.")
        return

    avg_esco = mean([row.esco_score for row in rows])
    avg_fused = mean([row.fused_score for row in rows])
    avg_delta = mean([row.delta for row in rows])
    onet_available_count = sum(1 for row in rows if row.onet_available)

    esco_rank = _rank_map(rows, "esco_score")
    fused_rank = _rank_map(rows, "fused_score")
    top_esco = {name for name, rank in esco_rank.items() if rank <= top_k}
    top_fused = {name for name, rank in fused_rank.items() if rank <= top_k}
    overlap = len(top_esco.intersection(top_fused))

    print("=" * 62)
    print("Hybrid Evaluation Summary")
    print("=" * 62)
    print(f"Rows evaluated           : {len(rows)}")
    print(f"Avg ESCO score           : {avg_esco:.2f}")
    print(f"Avg Hybrid fused score   : {avg_fused:.2f}")
    print(f"Avg delta (hybrid-esco)  : {avg_delta:.2f}")
    print(f"O*NET available          : {onet_available_count}/{len(rows)}")
    print(f"Top-{top_k} overlap         : {overlap}/{top_k}")
    print("=" * 62)


def build_summary_report(rows: list[EvalRow], top_k: int = 3, top_movers: int = 10) -> str:
    if not rows:
        return "No valid rows evaluated."

    avg_esco = mean([row.esco_score for row in rows])
    avg_fused = mean([row.fused_score for row in rows])
    avg_delta = mean([row.delta for row in rows])
    onet_available_count = sum(1 for row in rows if row.onet_available)

    esco_rank = _rank_map(rows, "esco_score")
    fused_rank = _rank_map(rows, "fused_score")
    top_esco = sorted(esco_rank.items(), key=lambda item: item[1])[:top_k]
    top_fused = sorted(fused_rank.items(), key=lambda item: item[1])[:top_k]
    overlap = len({name for name, _ in top_esco}.intersection({name for name, _ in top_fused}))

    shifts = _rank_shift_rows(rows)
    biggest_up = sorted(shifts, key=lambda item: int(item["rank_delta"]), reverse=True)[:top_movers]
    biggest_down = sorted(shifts, key=lambda item: int(item["rank_delta"]))[:top_movers]

    lines: list[str] = []
    lines.append("Hybrid Evaluation Report")
    lines.append("=" * 80)
    lines.append(f"Rows evaluated             : {len(rows)}")
    lines.append(f"Avg ESCO score             : {avg_esco:.2f}")
    lines.append(f"Avg Hybrid fused score     : {avg_fused:.2f}")
    lines.append(f"Avg score delta            : {avg_delta:.2f}")
    lines.append(f"O*NET available            : {onet_available_count}/{len(rows)}")
    lines.append(f"Top-{top_k} overlap            : {overlap}/{top_k}")
    lines.append("-")
    lines.append(f"Top {top_k} by ESCO:")
    for name, rank in top_esco:
        lines.append(f"  #{rank} {name}")
    lines.append(f"Top {top_k} by Hybrid:")
    for name, rank in top_fused:
        lines.append(f"  #{rank} {name}")
    lines.append("-")
    lines.append(f"Biggest rank gains (top {top_movers}):")
    for item in biggest_up:
        lines.append(
            "  {name}: {esco_rank} -> {hybrid_rank} (delta {rank_delta:+d}) | "
            "score {esco_score:.2f} -> {hybrid_score:.2f}".format(
                name=item["name"],
                esco_rank=int(item["esco_rank"]),
                hybrid_rank=int(item["hybrid_rank"]),
                rank_delta=int(item["rank_delta"]),
                esco_score=float(item["esco_score"]),
                hybrid_score=float(item["hybrid_score"]),
            )
        )
    lines.append(f"Biggest rank drops (top {top_movers}):")
    for item in biggest_down:
        lines.append(
            "  {name}: {esco_rank} -> {hybrid_rank} (delta {rank_delta:+d}) | "
            "score {esco_score:.2f} -> {hybrid_score:.2f}".format(
                name=item["name"],
                esco_rank=int(item["esco_rank"]),
                hybrid_rank=int(item["hybrid_rank"]),
                rank_delta=int(item["rank_delta"]),
                esco_score=float(item["esco_score"]),
                hybrid_score=float(item["hybrid_score"]),
            )
        )

    return "\n".join(lines)


def write_output(rows: list[EvalRow], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "candidate_name",
                "esco_score",
                "fused_score",
                "onet_score",
                "delta",
                "onet_available",
                "onet_matched_role",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.name,
                    row.esco_score,
                    row.fused_score,
                    row.onet_score,
                    row.delta,
                    row.onet_available,
                    row.onet_role,
                ]
            )


def write_summary_report(rows: list[EvalRow], output_path: Path, top_k: int, top_movers: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_summary_report(rows, top_k=top_k, top_movers=top_movers)
    output_path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ESCO vs Hybrid scoring from CSV resumes")
    parser.add_argument("--input-csv", required=True, help="Path to input CSV containing resume text")
    parser.add_argument("--target-role", required=True, help="Target occupation/role")
    parser.add_argument("--resume-col", default="resume_text", help="Resume text column name")
    parser.add_argument("--name-col", default="candidate_name", help="Candidate name column name")
    parser.add_argument("--output-csv", default="", help="Optional output CSV path")
    parser.add_argument("--output-report", default="", help="Optional text summary report path")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k overlap size")
    parser.add_argument("--top-movers", type=int, default=10, help="How many rank movers to show")
    parser.add_argument("--max-rows", type=int, default=0, help="Optional cap on evaluated valid rows (0 = no cap)")
    args = parser.parse_args()

    rows = evaluate(
        input_csv=Path(args.input_csv),
        target_role=args.target_role,
        resume_col=args.resume_col,
        name_col=args.name_col,
        max_rows=max(0, args.max_rows),
    )
    print_summary(rows, top_k=max(1, args.top_k))

    if args.output_csv:
        output_path = Path(args.output_csv)
        write_output(rows, output_path)
        print(f"Detailed output written to: {output_path}")

    if args.output_report:
        report_path = Path(args.output_report)
        write_summary_report(
            rows,
            report_path,
            top_k=max(1, args.top_k),
            top_movers=max(1, args.top_movers),
        )
        print(f"Summary report written to: {report_path}")


if __name__ == "__main__":
    main()
