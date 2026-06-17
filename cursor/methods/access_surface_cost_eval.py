#!/usr/bin/env python3
"""Cost-aware evaluation for the Access Surface OS router.

The policy comparison counts every non-static surface equally. That is too crude:
an identity chip, a queued replay, and a spoken interruption have different user
costs. This script adds a small auditable cost model over the same 58 external
clips.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
IN_CSV = CURSOR / "methods" / "output" / "access_surface_router.csv"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "access_surface_cost_eval.csv"
OUT_JSON = OUT_DIR / "access_surface_cost_eval_summary.json"

POLICIES = ["all_static", "need_only", "speech_need", "social_collision", "surface_router_v1"]

PASSIVE_SURFACES = {"identity_chip", "detail_chip", "object_explorer", "creator_qc"}
QUEUED_SURFACES = {"defer_replay"}
SPOKEN_NOW_SURFACES = {"static_ad", "concise_cue", "emotive_style", "soundscape"}


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


def surface_cost(surface: str, speech: float, slot: float, need: float) -> float:
    """Approximate user cost on a 0..1 scale.

    The key distinction is presentation mode, not whether a route is "static."
    Dense speech and low slot availability make spoken-now surfaces more costly.
    """
    no_slot_pressure = max(0.0, min(1.0, speech - slot))
    need_pressure = max(0.0, min(1.0, need))

    if surface == "static_ad":
        return 0.28 + 0.42 * no_slot_pressure
    if surface == "concise_cue":
        return 0.16 + 0.20 * no_slot_pressure
    if surface == "emotive_style":
        return 0.24 + 0.24 * no_slot_pressure
    if surface == "soundscape":
        return 0.18 + 0.12 * need_pressure
    if surface == "defer_replay":
        return 0.10 + 0.08 * need_pressure
    if surface == "identity_chip":
        return 0.08 + 0.08 * need_pressure
    if surface == "detail_chip":
        return 0.10 + 0.06 * need_pressure
    if surface == "object_explorer":
        return 0.12 + 0.08 * need_pressure
    if surface == "creator_qc":
        return 0.04
    return 0.20


def metrics_for(df: pd.DataFrame, policy: str) -> dict:
    surface = assign_policy(df, policy)
    target = df["target"].astype(int).eq(1)
    high_collision = df["social_collision_boundary"].ge(1.0)
    non_static = surface.ne("static_ad")

    costs = pd.Series(
        [
            surface_cost(str(s), float(speech), float(slot), float(need))
            for s, speech, slot, need in zip(
                surface,
                df["mean_speech_density"],
                df["mean_standard_slot_score"],
                df["need_z"],
            )
        ],
        index=df.index,
    )
    passive = surface.isin(PASSIVE_SURFACES)
    queued = surface.isin(QUEUED_SURFACES)
    spoken_now = surface.isin(SPOKEN_NOW_SURFACES)
    caught_target = target & non_static
    static_miss = target & ~non_static

    target_n = int(target.sum())
    high_collision_n = int(high_collision.sum())
    recall = float(caught_target.sum() / target_n) if target_n else 0.0
    high_collision_recall = float((high_collision & non_static).sum() / high_collision_n) if high_collision_n else 0.0
    mean_cost = float(costs.mean()) if len(costs) else 0.0
    return {
        "policy": policy,
        "n_clips": int(len(df)),
        "mean_cost": mean_cost,
        "total_cost": float(costs.sum()),
        "spoken_now_rate": float(spoken_now.mean()),
        "passive_rate": float(passive.mean()),
        "queued_rate": float(queued.mean()),
        "pro_not_best_recall": recall,
        "high_collision_recall": high_collision_recall,
        "avoidable_static_misses": int(static_miss.sum()),
        "caught_targets": int(caught_target.sum()),
        "caught_targets_per_cost": float(caught_target.sum() / costs.sum()) if costs.sum() else 0.0,
        "surface_count": {str(k): int(v) for k, v in surface.value_counts().items()},
    }


def main() -> None:
    df = pd.read_csv(IN_CSV)
    rows = [metrics_for(df, policy) for policy in POLICIES]
    out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.drop(columns=["surface_count"]).to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(
        json.dumps({"input": str(IN_CSV.relative_to(ROOT)), "policies": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print(out.drop(columns=["surface_count"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
