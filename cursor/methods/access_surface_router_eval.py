#!/usr/bin/env python3
"""Compare access-surface routing policies on external clips.

Targets are used only for evaluation:
- target == 1 means the pro/tier3 AD was not best by the external CLIP proxy.

Policies are deliberately simple baselines plus the current surface router.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
IN_CSV = CURSOR / "methods" / "output" / "access_surface_router.csv"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "access_surface_router_eval.csv"
OUT_JSON = OUT_DIR / "access_surface_router_eval_summary.json"


def assign_policy(df: pd.DataFrame, policy: str) -> pd.Series:
    if policy == "all_static":
        return pd.Series(["static_ad"] * len(df), index=df.index)
    if policy == "need_only":
        return pd.Series(
            ["detail_chip" if need >= 0.60 else "static_ad" for need in df["need_z"]],
            index=df.index,
        )
    if policy == "speech_need":
        return pd.Series(
            [
                "defer_replay" if speech >= 0.75 and need >= 0.60 else "static_ad"
                for speech, need in zip(df["mean_speech_density"], df["need_z"])
            ],
            index=df.index,
        )
    if policy == "social_collision":
        return pd.Series(
            ["detail_chip" if collision >= 1.0 else "static_ad" for collision in df["social_collision_boundary"]],
            index=df.index,
        )
    if policy == "surface_router_v1":
        return df["surface"].copy()
    raise ValueError(f"unknown policy: {policy}")


def metrics_for(df: pd.DataFrame, policy: str) -> dict:
    surface = assign_policy(df, policy)
    non_static = surface.ne("static_ad")
    target = df["target"].astype(int).eq(1)
    high_collision = df["social_collision_boundary"].ge(1.0)
    weak_margin = df["pro_margin"].le(0.02)
    static = ~non_static

    def rate(mask: pd.Series) -> float:
        return float(mask.mean()) if len(mask) else 0.0

    def conditional_rate(condition: pd.Series, event: pd.Series) -> float:
        denom = int(condition.sum())
        if denom == 0:
            return 0.0
        return float((condition & event).sum() / denom)

    non_static_n = int(non_static.sum())
    static_n = int(static.sum())
    return {
        "policy": policy,
        "n_clips": int(len(df)),
        "non_static_n": non_static_n,
        "non_static_rate": rate(non_static),
        "surface_count": {str(k): int(v) for k, v in surface.value_counts().items()},
        "pro_not_best_recall": conditional_rate(target, non_static),
        "high_collision_recall": conditional_rate(high_collision, non_static),
        "weak_margin_recall": conditional_rate(weak_margin, non_static),
        "non_static_precision_pro_not_best": conditional_rate(non_static, target),
        "static_safety_target0_rate": conditional_rate(static, ~target) if static_n else 0.0,
        "avoidable_static_misses": int((static & target).sum()),
        "static_n": static_n,
    }


def main() -> None:
    df = pd.read_csv(IN_CSV)
    policies = ["all_static", "need_only", "speech_need", "social_collision", "surface_router_v1"]
    rows = [metrics_for(df, p) for p in policies]
    out = pd.DataFrame(rows)
    flat = out.drop(columns=["surface_count"]).copy()
    flat.to_csv(OUT_CSV, index=False)
    report = {
        "input": str(IN_CSV.relative_to(ROOT)),
        "policies": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print(flat.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
