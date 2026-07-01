#!/usr/bin/env python3
"""OUTCOME: SceneTwin as a reference-free AD SAFETY GATE.

The real product question is not "what's the correlation" — it's "does it stop a bad
audio description from reaching a blind viewer, with no ground-truth reference?"

Each clip has a candidate pool of mixed quality:
  tier0_cross        = a real, normal-length AD describing the WRONG clip  (catastrophic:
                       actively misleads the viewer — the failure that matters most)
  tier1_vatex_short  = sparse crowd caption
  tier2_vatex_long   = fuller crowd caption
  tier3_va11y        = professional expert AD  (the one we'd want to ship)

Gate = reject the lowest-scoring candidate. Outcomes reported (not a p-value):
  - CATCH rate: how often the gate flags the wrong-content AD as worst        (want high)
  - FALSE-REJECT rate: how often it flags a GOOD AD (long/pro) as worst        (want ~0)
  - SHIP-BEST rate: how often the top-ranked candidate is the expert AD
  - ABSTENTION: coverage-reliability — on the confident fraction of clips, does
                catch rate reach 100%? (confidence = score margin, reference-free)
Baselines: random gate catches 1/4 = 25%.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cursor" / "output" / "external_ensemble_eval.csv"
OUT_JSON = ROOT / "cursor" / "output" / "gate_outcome.json"
CHART = ROOT / "output" / "charts" / "scenetwin_gate_outcome.png"
FINDINGS = ROOT / "cursor" / "findings" / "ad-safety-gate.md"

CROSS = "tier0_cross"
GOOD = {"tier2_vatex_long", "tier3_va11y"}
PRO = "tier3_va11y"
SCORES = {"ensemble": "ensemble_mean_clip_top3", "adqa_only": "adqa_norm", "clip_only": "clip_top3_norm"}


def gate_metrics(df: pd.DataFrame, col: str) -> dict:
    catch = falsereject = shipbest = total = 0
    margins, caught_flags = [], []
    for vid, g in df.groupby("video_id"):
        by = dict(zip(g["tier"], g[col]))
        if CROSS not in by or len(by) < 3:
            continue
        total += 1
        worst_tier = min(by, key=by.get)
        best_tier = max(by, key=by.get)
        is_catch = int(worst_tier == CROSS)
        catch += is_catch
        falsereject += int(worst_tier in GOOD)
        shipbest += int(best_tier == PRO)
        # reference-free confidence: gap between the worst and the 2nd-worst (how clearly
        # the rejected AD stands out as worst), normalized by the pool's score range
        vals = sorted(by.values())
        rng = (vals[-1] - vals[0]) or 1e-9
        margins.append((vals[1] - vals[0]) / rng)
        caught_flags.append(is_catch)
    margins = np.array(margins); caught = np.array(caught_flags)
    # coverage-reliability: keep most-confident k%, report catch rate on them
    order = np.argsort(-margins)
    cov_curve = []
    for frac in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        k = max(1, int(round(frac * len(order))))
        sel = order[:k]
        cov_curve.append({"coverage": frac, "catch_rate": float(caught[sel].mean())})
    return {
        "n_clips": total,
        "catch_rate": catch / total,
        "false_reject_rate": falsereject / total,
        "ship_best_rate": shipbest / total,
        "coverage_reliability": cov_curve,
    }


def main() -> None:
    df = pd.read_csv(SRC)
    rep = {"source": str(SRC), "random_baseline_catch": 0.25,
           **{name: gate_metrics(df, col) for name, col in SCORES.items()}}
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

    names = list(SCORES)
    catch = [rep[n]["catch_rate"] for n in names]
    fr = [rep[n]["false_reject_rate"] for n in names]
    ship = [rep[n]["ship_best_rate"] for n in names]
    x = np.arange(len(names)); w = 0.26
    ax1.bar(x - w, catch, w, label="catch wrong-content AD", color="#1b5e20")
    ax1.bar(x, ship, w, label="ship expert AD", color="#1565c0")
    ax1.bar(x + w, fr, w, label="false-reject a good AD", color="#c62828")
    ax1.axhline(0.25, ls="--", c="gray", lw=1, label="random gate (25%)")
    ax1.set_xticks(x); ax1.set_xticklabels(names, fontsize=9)
    ax1.set_ylabel("rate"); ax1.set_ylim(0, 1.05)
    ax1.set_title(f"Reference-free AD safety gate (n={rep['ensemble']['n_clips']} clips)")
    ax1.legend(fontsize=7.5, loc="center right"); ax1.grid(axis="y", alpha=0.25)

    for n, c in zip(names, ["#1b5e20", "#1565c0", "#ef6c00"]):
        cc = rep[n]["coverage_reliability"]
        ax2.plot([p["coverage"] for p in cc], [p["catch_rate"] for p in cc],
                 "-o", color=c, label=n, ms=4)
    ax2.set_xlabel("coverage (most-confident clips kept)")
    ax2.set_ylabel("catch rate on kept clips")
    ax2.set_title("Abstention: confident clips -> near-perfect catch")
    ax2.set_ylim(0.4, 1.02); ax2.invert_xaxis()
    ax2.legend(fontsize=8); ax2.grid(alpha=0.25)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    for n in names:
        r = rep[n]
        print(f"{n:10s}: catch={r['catch_rate']:.0%}  ship-best={r['ship_best_rate']:.0%}  "
              f"false-reject={r['false_reject_rate']:.0%}  (n={r['n_clips']})")
    print(f"\nrandom gate catch baseline: 25%")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
