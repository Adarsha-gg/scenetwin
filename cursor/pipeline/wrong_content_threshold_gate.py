#!/usr/bin/env python3
"""OUTCOME: deployment-honest wrong-content gate (single AD, no pool, no reference).

The existing gate_outcome.py is a MIN-OF-POOL gate: it ranks 4 candidates per clip and
rejects the lowest. Its "ensemble" column is per-clip min-max normalised, which forces the
wrong-content AD (tier0_cross) to exactly 0.0 -> 100% catch is partly tautological, and it
needs a clean candidate pool to compare against. That is not how deployment works.

Real product question: a blind viewer is about to hear ONE audio description for ONE clip.
There is no reference, no sibling candidates. Can a fixed score threshold catch a
wrong-content AD (catastrophic: describes a different video) without rejecting good ADs?

This script:
  - uses RAW signals only (clip_top3, adqa_score) — no per-clip normalisation leakage,
  - treats every (clip, tier) candidate INDEPENDENTLY (no pool),
  - calibrates the reject threshold by LEAVE-ONE-CLIP-OUT (LOCO): tau is set on 59 clips,
    applied to the held-out clip, so no clip sees its own threshold,
  - operating point = lowest tau on the train fold with false-reject (FPR on good ADs)
    <= 10%, maximising catch,
  - reports honest grader-free ROC AUC for each signal + raw ensemble.

Label: tier0_cross = should REJECT (positive). tier1/2/3 = should SHIP (about right clip).
Baseline: a gate that rejects at random with 10% reject budget catches 10% of cross ADs.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cursor" / "output" / "external_ensemble_eval.csv"
OUT_JSON = ROOT / "cursor" / "output" / "wrong_content_threshold_gate.json"
CHART = ROOT / "output" / "charts" / "scenetwin_wrong_content_threshold_gate.png"

CROSS = "tier0_cross"
FPR_BUDGET = 0.10  # max allowed false-reject of good ADs


def roc_auc(scores: np.ndarray, pos: np.ndarray) -> float:
    """AUC that a LOW score => positive (cross). Rank-based, ties handled."""
    # low score => positive (cross); rank "badness" = -score, average ranks for ties
    ranks = pd.Series(-scores).rank(method="average").to_numpy()
    n_pos = pos.sum(); n_neg = len(pos) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    return float((ranks[pos == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def loco_gate(df: pd.DataFrame, score_col: str) -> dict:
    """Reject if score < tau. tau calibrated leave-one-clip-out."""
    clips = df["video_id"].unique()
    rej_cross = tot_cross = rej_good = tot_good = 0
    for held in clips:
        train = df[df["video_id"] != held]
        test = df[df["video_id"] == held]
        good = train[train.tier != CROSS][score_col].to_numpy()
        cross = train[train.tier == CROSS][score_col].to_numpy()
        # candidate thresholds = sorted unique train scores; pick the one with
        # false-reject (good below tau) <= budget that maximises caught cross
        cands = np.unique(train[score_col].to_numpy())
        best_tau, best_catch = good.min() - 1e-6, -1.0
        for tau in cands:
            fr = (good < tau).mean()
            if fr <= FPR_BUDGET:
                catch = (cross < tau).mean()
                if catch > best_catch:
                    best_catch, best_tau = catch, tau
        for _, row in test.iterrows():
            reject = row[score_col] < best_tau
            if row.tier == CROSS:
                tot_cross += 1; rej_cross += int(reject)
            else:
                tot_good += 1; rej_good += int(reject)
    return {
        "catch_rate": rej_cross / tot_cross,
        "false_reject_rate": rej_good / tot_good,
        "n_cross": tot_cross, "n_good": tot_good,
        "auc": roc_auc(df[score_col].to_numpy(), (df.tier == CROSS).to_numpy().astype(int)),
    }


def build_signals(df: pd.DataFrame) -> dict:
    df = df.copy()
    # raw ensemble = mean of globally z-scored raw signals (no per-clip leakage)
    for c in ("clip_top3", "adqa_score"):
        z = (df[c] - df[c].mean()) / (df[c].std() + 1e-9)
        df[c + "_z"] = z
    df["raw_ensemble"] = (df["clip_top3_z"] + df["adqa_score_z"]) / 2
    return {
        "clip_only": "clip_top3",
        "adqa_only": "adqa_score",
        "raw_ensemble": "raw_ensemble",
    }, df


def main() -> None:
    df = pd.read_csv(SRC)
    cols, df = build_signals(df)
    rep = {
        "source": str(SRC),
        "design": "single-AD absolute threshold, leave-one-clip-out calibration, FPR budget 10%",
        "random_baseline_catch_at_10pct_budget": 0.10,
        "signals": {name: loco_gate(df, col) for name, col in cols.items()},
    }
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    names = list(cols)
    catch = [rep["signals"][n]["catch_rate"] for n in names]
    fr = [rep["signals"][n]["false_reject_rate"] for n in names]
    auc = [rep["signals"][n]["auc"] for n in names]
    x = np.arange(len(names)); w = 0.28
    ax.bar(x - w / 2, catch, w, label="catch wrong-content AD", color="#1b5e20")
    ax.bar(x + w / 2, fr, w, label="false-reject a good AD", color="#c62828")
    for i, a in enumerate(auc):
        ax.text(i, max(catch[i], fr[i]) + 0.03, f"AUC {a:.2f}", ha="center", fontsize=9)
    ax.axhline(0.10, ls="--", c="gray", lw=1, label="random gate @10% budget")
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("rate"); ax.set_ylim(0, 1.08)
    ax.set_title("Single-AD wrong-content gate (LOCO, no pool, no reference)")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    for n in names:
        r = rep["signals"][n]
        print(f"{n:13s}: catch={r['catch_rate']:.0%}  false-reject={r['false_reject_rate']:.0%}  "
              f"AUC={r['auc']:.3f}  (cross={r['n_cross']}, good={r['n_good']})")
    print("\nrandom gate @10% reject budget catches 10%")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
