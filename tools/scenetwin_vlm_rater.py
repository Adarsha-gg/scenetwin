#!/usr/bin/env python3
"""Direct VLM rater baseline for SceneTwin.

This is the obvious market-style baseline: give a multimodal model sampled
frames plus all candidate descriptions, then ask it to directly score each
candidate on AD quality. It is intentionally separate from ADQA so we can test
whether "just ask a VLM judge" is enough.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import kendalltau, spearmanr

from scenetwin_adqa import (
    SHARED_FRAMES_DIR,
    TIER_GT,
    TIERS,
    TIMING_DIR,
    cache_call,
    call_with_images,
    complete_clip_indices,
    load_clip_metadata,
    load_dotenv,
    parse_json_object,
    run_dir_name,
    sample_frames,
)


def rater_dir_name(model: str) -> str:
    return "vlm_rater_" + re.sub(r"[^a-zA-Z0-9_-]+", "-", model.replace(":", "-")).strip("-")


def rater_prompt(candidates: list[dict[str, str]]) -> str:
    return f"""You are evaluating audio descriptions for a blind/low-vision listener.

Look only at the attached sampled video frames and the candidate descriptions.
Do not use tier names, source assumptions, or outside knowledge.

Score each candidate from 0 to 100 on overall audio-description usefulness:
- visual_accuracy: describes what is actually visible; penalize hallucinations.
- completeness: covers main subjects, actions, setting, key objects, and visible text.
- specificity: more useful than a vague generic caption.
- concision: enough detail without irrelevant filler.
- listener_utility: would help a blind listener understand the visual scene.

Candidates are anonymized:
{json.dumps(candidates, indent=2)}

Return JSON only:
{{
  "scores": [
    {{
      "candidate_id": "A",
      "visual_accuracy": 0,
      "completeness": 0,
      "specificity": 0,
      "concision": 0,
      "listener_utility": 0,
      "overall": 0,
      "rationale": "under 16 words"
    }}
  ]
}}
"""


def sanitize_scores(parsed: dict[str, Any], id_to_tier: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for raw in parsed.get("scores", []):
        cid = str(raw.get("candidate_id", "")).strip()
        tier = id_to_tier.get(cid)
        if tier not in TIERS:
            continue
        row: dict[str, Any] = {"candidate_id": cid, "tier": tier}
        for field in ["visual_accuracy", "completeness", "specificity", "concision", "listener_utility", "overall"]:
            try:
                val = float(raw.get(field, 0.0))
            except (TypeError, ValueError):
                val = 0.0
            row[field] = max(0.0, min(100.0, val))
        row["rationale"] = str(raw.get("rationale", "")).strip()[:180]
        rows.append(row)
    return rows


def compute_metrics(df: pd.DataFrame, score_col: str) -> dict[str, object]:
    scored = df.dropna(subset=[score_col, "gt"])
    rho, rho_p = spearmanr(scored["gt"], scored[score_col])
    tau, tau_p = kendalltau(scored["gt"], scored[score_col])
    wins = total = full = full_total = 0
    for _, group in scored.groupby("clip_idx"):
        by_tier = {row.tier: float(getattr(row, score_col)) for row in group.itertuples()}
        if "tier3_va11y" in by_tier:
            for tier in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
                total += 1
                wins += int(by_tier["tier3_va11y"] > by_tier[tier])
        if set(TIERS).issubset(by_tier):
            full_total += 1
            full += int(
                by_tier["tier3_va11y"]
                > by_tier["tier2_vatex_long"]
                > by_tier["tier1_vatex_short"]
                > by_tier["tier0_cross"]
            )
    return {
        "metric": score_col,
        "spearman_rho": float(rho) if not math.isnan(rho) else float("nan"),
        "spearman_p": float(rho_p) if not math.isnan(rho_p) else float("nan"),
        "kendall_tau": float(tau) if not math.isnan(tau) else float("nan"),
        "kendall_p": float(tau_p) if not math.isnan(tau_p) else float("nan"),
        "pairwise_wins": wins,
        "pairwise_total": total,
        "full_order_clips": full,
        "full_order_total": full_total,
    }


def permutation_null(df: pd.DataFrame, score_col: str, n: int, seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    observed = compute_metrics(df, score_col)["spearman_rho"]
    nulls = []
    for _ in range(n):
        work = df.copy()
        for clip_idx in work["clip_idx"].unique():
            mask = work["clip_idx"] == clip_idx
            vals = list(work.loc[mask, "gt"])
            rng.shuffle(vals)
            work.loc[mask, "gt"] = vals
        rho = compute_metrics(work, score_col)["spearman_rho"]
        if not math.isnan(rho):
            nulls.append(rho)
    return {
        "metric": score_col,
        "observed_rho": observed,
        "null_mean_rho": sum(nulls) / len(nulls) if nulls else float("nan"),
        "null_p_ge_observed": sum(x >= observed for x in nulls) / len(nulls) if nulls else float("nan"),
        "n_permutations": len(nulls),
    }


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="openai:gpt-4o", help="provider:model with vision support")
    parser.add_argument("--n-permutations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--clip-limit", type=int, default=0)
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    out_dir = TIMING_DIR / rater_dir_name(args.model)
    cache_dir = out_dir / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_df = load_clip_metadata()
    clip_indices = complete_clip_indices()
    if args.clip_limit:
        clip_indices = clip_indices[:args.clip_limit]
    meta_df = meta_df[meta_df["clip_idx"].isin(clip_indices)]

    rows = []
    print(f"Model  : {args.model}")
    print(f"Clips  : {len(meta_df)}")
    print(f"Output : {out_dir}")
    print(f"Frames : {SHARED_FRAMES_DIR}\n")

    for meta in meta_df.to_dict(orient="records"):
        clip_idx = int(meta["clip_idx"])
        print(f"=== clip_{clip_idx:02d} ===", flush=True)
        frame_paths = sample_frames(clip_idx)
        rng = random.Random(args.seed * 1009 + clip_idx)
        shuffled_tiers = list(TIERS)
        rng.shuffle(shuffled_tiers)
        ids = ["A", "B", "C", "D"]
        id_to_tier = dict(zip(ids, shuffled_tiers))
        candidates = [{"candidate_id": cid, "description": meta.get(id_to_tier[cid], "")} for cid in ids]
        key = {
            "model": args.model,
            "clip_idx": clip_idx,
            "frames": [p.name for p in frame_paths],
            "candidates": candidates,
            "prompt_version": "direct_vlm_rater_v1",
        }
        try:
            parsed = cache_call(
                cache_dir,
                key,
                "vlm_scores",
                lambda fp=frame_paths, cs=candidates: call_with_images(args.model, rater_prompt(cs), fp),
                args.refresh_cache,
            )
        except Exception as exc:
            print(f"  failed: {exc}", flush=True)
            continue
        scored = sanitize_scores(parsed, id_to_tier)
        for score in scored:
            tier = score["tier"]
            rows.append({
                "clip_idx": clip_idx,
                "video_id": meta["video_id"],
                "category": meta["category"],
                "tier": tier,
                "gt": TIER_GT[tier],
                "model": args.model,
                **score,
            })
        print(f"  {len(scored)} scores", flush=True)

    if not rows:
        raise RuntimeError("No VLM scores produced.")

    scores = pd.DataFrame(rows)
    scores.to_csv(out_dir / "scores.csv", index=False)

    metrics = pd.DataFrame([compute_metrics(scores, col) for col in [
        "overall",
        "visual_accuracy",
        "completeness",
        "specificity",
        "concision",
        "listener_utility",
    ]])
    metrics["model"] = args.model
    metrics.to_csv(out_dir / "aggregate_results.csv", index=False)

    nulls = pd.DataFrame([permutation_null(scores, "overall", args.n_permutations, args.seed)])
    nulls["model"] = args.model
    nulls.to_csv(out_dir / "nulls.csv", index=False)

    print("\n=== Results ===")
    print(metrics.to_string(index=False))
    print("\n=== Null ===")
    print(nulls.to_string(index=False))


if __name__ == "__main__":
    main()
