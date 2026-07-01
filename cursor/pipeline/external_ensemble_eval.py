#!/usr/bin/env python3
"""Full CLIP+ADQA ensemble on external clips — answers "does 0.93 generalize?"

Pipeline per external clip (same recipe as benchmark headline):
  1. Frame-grounded ADQA: 5 questions from frames, blind grade all 4 tiers
  2. Merge CLIP top3 from external_clip_full_eval.csv
  3. Min-max normalize ADQA + CLIP within clip
  4. ensemble_mean_clip_top3 = 0.5 * adqa_norm + 0.5 * clip_top3_norm
  5. Pooled Spearman ρ vs tier ground truth

Caches LLM calls under cursor/output/external_adqa/cache/.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import scenetwin_stage4_frame_grounded_adqa as s4  # noqa: E402

CURSOR = ROOT / "cursor"
EXT_DIR = CURSOR / "data" / "external_clips"
REGISTRY = EXT_DIR / "registry.jsonl"
FRAMES_ROOT = EXT_DIR / "frames"
CLIP_CSV = CURSOR / "output" / "external_clip_full_eval.csv"
OUT_DIR = CURSOR / "output" / "external_adqa"
CACHE_DIR = OUT_DIR / "cache"
OUT_TIER = OUT_DIR / "external_adqa_tier_scores.csv"
OUT_GRADES = OUT_DIR / "external_adqa_grades.csv"
OUT_QUESTIONS = OUT_DIR / "external_adqa_questions.csv"
OUT_ENSEMBLE_CSV = CURSOR / "output" / "external_ensemble_eval.csv"
OUT_JSON = CURSOR / "output" / "external_ensemble_eval.json"
FINDINGS = CURSOR / "findings" / "external-ensemble-generalization.md"

TIMING = ROOT / "output" / "scenetwin_timing_20clip"
BENCH_ENSEMBLE = TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv"

TIERS = s4.TIERS
TIER_GT = s4.TIER_GT
N_FRAMES = 8


def load_registry() -> list[dict]:
    rows = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return [r for r in rows if r.get("download_ok", True)]


def frame_paths(video_id: str) -> list[Path]:
    paths = sorted((FRAMES_ROOT / video_id).glob("frame_*.jpg"))
    if len(paths) >= N_FRAMES:
        return paths[:N_FRAMES]
    raise FileNotFoundError(f"{video_id}: need {N_FRAMES} frames in {FRAMES_ROOT / video_id}")


def cache_json(name: str, payload: Any, fn, refresh: bool) -> dict[str, Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / f"{name}_{s4.stable_hash(payload)}.json"
    if p.exists() and not refresh:
        return json.loads(p.read_text(encoding="utf-8"))
    result = fn()
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def run_adqa_clip(meta: dict, model: str, n_questions: int, seed: int, refresh: bool) -> tuple[list[dict], list[dict]]:
    vid = meta["video_id"]
    paths = frame_paths(vid)
    frame_keys = [f.name for f in paths]

    q_payload = {
        "kind": "external_frame_questions_v1",
        "model": model,
        "video_id": vid,
        "frame_files": frame_keys,
        "n_questions": n_questions,
    }

    def make_questions() -> dict[str, Any]:
        return s4.call_anthropic_with_images(
            s4.question_text_prompt(meta, n_questions),
            paths,
            model,
        )

    parsed_q = cache_json("questions", q_payload, make_questions, refresh)
    questions = s4.sanitize_questions(parsed_q, n_questions)
    if not questions:
        raise RuntimeError(f"{vid}: no questions parsed")

    q_rows = []
    for q in questions:
        q_rows.append({
            "video_id": vid,
            "category": meta["category"],
            "model": model,
            "n_frames": len(paths),
            **q,
        })

    questions_for_prompt = [
        {
            "q_idx": q["q_idx"],
            "question": q["question"],
            "answer_key": q["answer_key"],
            "required_visual_evidence": q["required_visual_evidence"].split("; ") if q["required_visual_evidence"] else [],
            "importance": q["importance"],
        }
        for q in questions
    ]

    rng = random.Random(seed + hash(vid) % 10000)
    ordered = list(TIERS)
    rng.shuffle(ordered)
    candidate_ids = ["A", "B", "C", "D"]
    id_to_tier = dict(zip(candidate_ids, ordered))
    anonymized = [{"candidate_id": cid, "description": meta[id_to_tier[cid]]} for cid in candidate_ids]

    g_payload = {
        "kind": "external_grades_v1_blind",
        "model": model,
        "video_id": vid,
        "questions": questions_for_prompt,
        "anonymized_candidates": anonymized,
        "id_to_tier": id_to_tier,
    }

    def make_grades() -> dict[str, Any]:
        return s4.call_anthropic_text(
            s4.grade_prompt(questions_for_prompt, anonymized),
            model,
            max_tokens=5000,
        )

    parsed_g = cache_json("grades", g_payload, make_grades, refresh)
    grades = s4.sanitize_grades(parsed_g, id_to_tier)

    g_rows = []
    for g in grades:
        tier = g["tier"]
        g_rows.append({
            "video_id": vid,
            "category": meta["category"],
            "tier": tier,
            "gt": TIER_GT[tier],
            "description": meta[tier],
            "model": model,
            **g,
        })
    return q_rows, g_rows


def aggregate_tier(grades_df: pd.DataFrame) -> pd.DataFrame:
    return (
        grades_df.groupby(["video_id", "category", "tier", "gt"], as_index=False)
        .agg(
            adqa_score=("score", "mean"),
            adqa_yes_rate=("label", lambda s: sum(str(x).lower() == "yes" for x in s) / len(s)),
            n_questions=("q_idx", "count"),
        )
    )


def minmax_clipwise(df: pd.DataFrame, col: str, group: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        if not np.isfinite(lo) or hi == lo:
            return pd.Series(np.full(len(s), 0.5), index=s.index)
        return (s - lo) / (hi - lo)

    return df.groupby(group, group_keys=False)[col].apply(scale)


def full_order_rate(df: pd.DataFrame, col: str, group: str) -> tuple[int, int]:
    n = total = 0
    for _, g in df.groupby(group):
        by = dict(zip(g["tier"], g[col]))
        if all(t in by for t in TIERS):
            total += 1
            n += int(by["tier3_va11y"] > by["tier2_vatex_long"] > by["tier1_vatex_short"] > by["tier0_cross"])
    return n, total


def pairwise_wins(df: pd.DataFrame, col: str, group: str) -> tuple[int, int]:
    wins = total = 0
    comparisons = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]
    for _, g in df.groupby(group):
        by = dict(zip(g["tier"], g[col]))
        if "tier3_va11y" not in by:
            continue
        for lo in comparisons:
            if lo in by:
                total += 1
                wins += int(by["tier3_va11y"] > by[lo])
    return wins, total


def build_ensemble(df: pd.DataFrame, group: str) -> pd.DataFrame:
    out = df.copy()
    out["adqa_norm"] = minmax_clipwise(out, "adqa_score", group)
    out["clip_top3_norm"] = minmax_clipwise(out, "clip_top3", group)
    out["ensemble_mean_clip_top3"] = 0.5 * out["adqa_norm"] + 0.5 * out["clip_top3_norm"]
    return out


def metric_block(df: pd.DataFrame, col: str, group: str) -> dict[str, Any]:
    rho, p = spearmanr(df["gt"], df[col], nan_policy="omit")
    fo, fo_t = full_order_rate(df, col, group)
    pw, pw_t = pairwise_wins(df, col, group)
    return {
        "spearman_rho": float(rho),
        "spearman_p": float(p),
        "full_order": fo,
        "full_order_total": fo_t,
        "full_order_rate": float(fo / fo_t) if fo_t else float("nan"),
        "pairwise_wins": pw,
        "pairwise_total": pw_t,
        "n_rows": len(df),
        "n_clips": df[group].nunique(),
    }


def benchmark_recompute() -> dict[str, Any]:
    """Same ensemble recipe on benchmark rows for apples-to-apples."""
    if not BENCH_ENSEMBLE.exists():
        return {}
    b = pd.read_csv(BENCH_ENSEMBLE)
    b = b.rename(columns={"adqa_v2_score": "adqa_score"})
    b = build_ensemble(b, "clip_idx")
    return {
        "adqa_only": metric_block(b, "adqa_score", "clip_idx"),
        "clip_top3_only": metric_block(b, "clip_top3", "clip_idx"),
        "ensemble_mean_clip_top3": metric_block(b, "ensemble_mean_clip_top3", "clip_idx"),
        "stored_ensemble_rho": float(
            spearmanr(b["gt"], b["ensemble_mean_clip_top3"], nan_policy="omit")[0]
        ),
    }


def write_findings(report: dict[str, Any]) -> None:
    ext = report["external"]
    bench = report.get("benchmark_recomputed", {})
    clip_only = report.get("clip_only_external", {})
    lines = [
        "---",
        "title: External Ensemble Generalization",
        "category: research",
        "tags: [SceneTwin, ensemble, generalization, ADQA, CLIP]",
        f"created: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "---",
        "",
        "# External Ensemble Generalization",
        "",
        "Does headline **ensemble_mean_clip_top3 ρ≈0.93** hold on 58 held-out YouTube clips?",
        "",
        "## Method",
        "",
        "- Frame-grounded ADQA (5Q, blind A/B/C/D grading) — same protocol as benchmark adqa_v2",
        "- CLIP ViT-L-14 top3 from `external_clip_full_eval.csv`",
        "- Min-max normalize ADQA + CLIP within clip; ensemble = 50/50",
        "",
        "## Results",
        "",
        "| Split | Metric | ρ | full order | pairwise |",
        "|-------|--------|---|------------|----------|",
    ]
    for label, block in [
        ("External", ext.get("ensemble_mean_clip_top3", {})),
        ("External CLIP-only", clip_only),
        ("External ADQA-only", ext.get("adqa_only", {})),
        ("Benchmark (recomputed)", bench.get("ensemble_mean_clip_top3", {})),
    ]:
        if block:
            lines.append(
                f"| {label} | {block.get('spearman_rho', float('nan')):.3f} | "
                f"{block.get('full_order', '?')}/{block.get('full_order_total', '?')} | "
                f"{block.get('pairwise_wins', '?')}/{block.get('pairwise_total', '?')} |"
            )
    lines += [
        "",
        "## Verdict",
        "",
        report.get("verdict", "See JSON for details."),
        "",
        "## See Also",
        "",
        "- [[research/GROUND-UP-THESIS]]",
        "- [[findings/ground-up-reframe]]",
        "",
    ]
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    s4.load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--questions-per-clip", type=int, default=5)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--clip-limit", type=int, default=0)
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    if not CLIP_CSV.exists():
        raise SystemExit(f"Run external_clip_pipeline.py first — missing {CLIP_CSV}")

    registry = load_registry()
    if args.clip_limit > 0:
        registry = registry[: args.clip_limit]

    clip_df = pd.read_csv(CLIP_CSV)
    clip_lookup = clip_df.set_index(["video_id", "tier"])["clip_top3"].to_dict()

    question_rows: list[dict] = []
    grade_rows: list[dict] = []
    failed: list[str] = []

    for i, meta in enumerate(registry):
        vid = meta["video_id"]
        print(f"[{i+1}/{len(registry)}] ADQA {vid} ({meta['category']})")
        try:
            q_rows, g_rows = run_adqa_clip(
                meta, args.model, args.questions_per_clip, args.seed, args.refresh_cache
            )
            question_rows.extend(q_rows)
            grade_rows.extend(g_rows)
            print(f"  {len(q_rows)} qs, {len(g_rows)} grades")
        except Exception as exc:
            print(f"  FAIL: {exc}", file=sys.stderr)
            failed.append(vid)

    if not grade_rows:
        raise SystemExit("No ADQA grades produced.")

    questions_df = pd.DataFrame(question_rows)
    grades_df = pd.DataFrame(grade_rows)
    tier_df = aggregate_tier(grades_df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    questions_df.to_csv(OUT_QUESTIONS, index=False)
    grades_df.to_csv(OUT_GRADES, index=False)
    tier_df.to_csv(OUT_TIER, index=False)

    merged = tier_df.copy()
    merged["clip_top3"] = merged.apply(
        lambda r: clip_lookup.get((r["video_id"], r["tier"]), float("nan")), axis=1
    )
    merged = merged.dropna(subset=["clip_top3"])
    ens = build_ensemble(merged, "video_id")
    ens.to_csv(OUT_ENSEMBLE_CSV, index=False)

    ext_metrics = {
        "adqa_only": metric_block(ens, "adqa_score", "video_id"),
        "clip_top3_only": metric_block(ens, "clip_top3", "video_id"),
        "ensemble_mean_clip_top3": metric_block(ens, "ensemble_mean_clip_top3", "video_id"),
    }
    clip_only = metric_block(clip_df, "clip_top3", "video_id")
    bench = benchmark_recompute()

    ext_rho = ext_metrics["ensemble_mean_clip_top3"]["spearman_rho"]
    bench_rho = bench.get("ensemble_mean_clip_top3", {}).get("spearman_rho", float("nan"))
    clip_rho = clip_only["spearman_rho"]

    if np.isfinite(bench_rho):
        verdict = (
            f"External ensemble ρ={ext_rho:.3f} vs benchmark ρ={bench_rho:.3f} "
            f"(Δρ={bench_rho - ext_rho:.3f}). CLIP-only external ρ={clip_rho:.3f}. "
            f"{'0.93 does NOT generalize' if ext_rho < 0.80 else 'Partial generalization'} — "
            f"ensemble {'lifts' if ext_rho > clip_rho else 'does not lift'} over CLIP-only on external."
        )
    else:
        verdict = f"External ensemble ρ={ext_rho:.3f}; CLIP-only ρ={clip_rho:.3f}."

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "n_questions_per_clip": args.questions_per_clip,
        "n_clips_attempted": len(registry),
        "n_clips_scored": ens["video_id"].nunique(),
        "n_tier_rows": len(ens),
        "failed_clips": failed,
        "external": ext_metrics,
        "clip_only_external": clip_only,
        "benchmark_recomputed": bench,
        "generalization_gap_ensemble": float(bench_rho - ext_rho) if np.isfinite(bench_rho) else None,
        "verdict": verdict,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_findings(report)

    print("\n=== EXTERNAL ENSEMBLE ===")
    for name, block in ext_metrics.items():
        print(f"{name}: ρ={block['spearman_rho']:.3f} | full {block['full_order']}/{block['full_order_total']}")
    if bench:
        b = bench["ensemble_mean_clip_top3"]
        print(f"\nBenchmark recomputed ensemble: ρ={b['spearman_rho']:.3f}")
    print(f"\n{verdict}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
