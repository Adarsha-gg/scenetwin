#!/usr/bin/env python3
"""OUTCOME: the wrong-content AD's "structural zero" is real but UNDEPLOYABLE as a
binary rule — the catch is a CONTINUOUS-resolution property of the evidence.

Round 73 angle: information-content / quantization of the RAW ADQA evidence.

A wrong-content AD describes the WRONG clip, so intuitively it should answer NONE of
the frame-grounded questions. The data confirms it: tier0_cross scores EXACTLY 0 on
`adqa_yes_rate` for all 60 clips. The tempting deployment rule is therefore pool-free
and parameter-free: "reject any AD that grounds zero questions."

That rule is a trap. `adqa_yes_rate = yes_count / n_questions` and n_questions is fixed
at 5, so the yes-rate is quantized into 6 bins {0, .2, .4, .6, .8, 1}. Thin-but-correct
genuine ADs pile up in the bottom bin alongside the wrong-content ADs. The "reject
yes_rate==0" rule catches 100% of wrong-content but also flags ~46% of GENUINE ADs.

The discriminative signal survives only BELOW the bin floor: the continuous `adqa_score`
keeps sub-bin resolution (and raw CLIP keeps it best). This script quantifies the
information thrown away by binarization as a drop in standalone (pool-free) wrong-content
AUC, and shows the separation that lives inside the saturated yes_rate==0 floor.

This is NOT the r68 raw-CLIP global threshold, the r69 base-rate precision, the r70 noise
margin, the r71 normalized 2-class confounder, or the r72 ship-best selective prediction.
It is the first round to read the unused `adqa_yes_rate` / `n_questions` columns and to
diagnose WHY a perfect structural zero is a useless gate. Free, no LLM.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cursor" / "output" / "external_ensemble_eval.csv"
OUT_JSON = ROOT / "cursor" / "output" / "wrong_content_evidence_resolution.json"
CHART = ROOT / "output" / "charts" / "scenetwin_wrong_content_evidence_resolution.png"

CROSS = "tier0_cross"
RAW_SIGNALS = ["adqa_yes_rate", "adqa_score", "clip_top3"]


def auc_genuine_over_cross(score: np.ndarray, is_cross: np.ndarray) -> float:
    """AUC for detecting wrong-content as the LOW-scoring class (Mann-Whitney, tie=0.5)."""
    pos = score[is_cross == 1]  # wrong-content (want low)
    neg = score[is_cross == 0]  # genuine
    wins = ties = 0.0
    for p in pos:
        wins += float((neg > p).sum())
        ties += float((neg == p).sum())
    return (wins + 0.5 * ties) / (len(pos) * len(neg))


def main() -> None:
    df = pd.read_csv(SRC)
    is_cross = (df.tier == CROSS).astype(int).values
    genuine = df[df.tier != CROSS]
    cross = df[df.tier == CROSS]

    # 1) standalone (pool-free) wrong-content AUC per RAW signal
    aucs = {c: auc_genuine_over_cross(df[c].values, is_cross) for c in RAW_SIGNALS}

    # 2) the "structural zero" trap on the binarized yes-rate
    n_q = sorted(df.n_questions.unique().tolist())
    yr_levels = sorted(df.adqa_yes_rate.unique().tolist())
    zero_rule = {
        "catch": float((cross.adqa_yes_rate == 0).mean()),
        "false_flag_genuine": float((genuine.adqa_yes_rate == 0).mean()),
        "genuine_at_zero": int((genuine.adqa_yes_rate == 0).sum()),
        "genuine_total": int(len(genuine)),
    }

    # 3) sub-floor resolution: inside yes_rate==0, do the continuous signals still split?
    floor = df[df.adqa_yes_rate == 0]
    fc = floor[floor.tier == CROSS]
    fg = floor[floor.tier != CROSS]
    subfloor = {
        "n_floor_rows": int(len(floor)),
        "n_cross_in_floor": int(len(fc)),
        "n_genuine_in_floor": int(len(fg)),
        "genuine_with_nonzero_adqa_score": int((fg.adqa_score > 0).sum()),
        "clip_top3": {"cross_mean": float(fc.clip_top3.mean()), "genuine_mean": float(fg.clip_top3.mean()),
                      "auc": float(auc_genuine_over_cross(floor.clip_top3.values, (floor.tier == CROSS).astype(int).values))},
        "adqa_score": {"cross_mean": float(fc.adqa_score.mean()), "genuine_mean": float(fg.adqa_score.mean()),
                       "auc": float(auc_genuine_over_cross(floor.adqa_score.values, (floor.tier == CROSS).astype(int).values))},
    }

    rep = {
        "source": str(SRC),
        "n_questions_levels": n_q,
        "yes_rate_levels": yr_levels,
        "standalone_auc_genuine_over_cross": aucs,
        "binarization_auc_loss": {
            "yes_rate": aucs["adqa_yes_rate"],
            "continuous_adqa_score": aucs["adqa_score"],
            "delta": aucs["adqa_score"] - aucs["adqa_yes_rate"],
        },
        "structural_zero_rule": zero_rule,
        "subfloor_resolution": subfloor,
        "random_baseline_catch": 0.25,
    }
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    # chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

    labels = ["adqa_yes_rate\n(binarized, 6 bins)", "adqa_score\n(continuous)", "clip_top3\n(raw CLIP)"]
    vals = [aucs["adqa_yes_rate"], aucs["adqa_score"], aucs["clip_top3"]]
    colors = ["#c62828", "#ef6c00", "#1b5e20"]
    ax1.bar(range(3), vals, color=colors)
    for i, v in enumerate(vals):
        ax1.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=9)
    ax1.axhline(0.5, ls="--", c="gray", lw=1, label="random (0.5)")
    ax1.set_xticks(range(3)); ax1.set_xticklabels(labels, fontsize=8)
    ax1.set_ylabel("pool-free wrong-content AUC"); ax1.set_ylim(0, 1.08)
    ax1.set_title("Binarizing the ADQA evidence costs ~0.19 AUC")
    ax1.legend(fontsize=8); ax1.grid(axis="y", alpha=0.25)

    # panel 2: the saturated yes_rate==0 floor, resolved by clip_top3
    ax2.scatter(fg.clip_top3, np.random.RandomState(0).normal(1, 0.04, len(fg)),
                s=18, c="#1565c0", alpha=0.6, label=f"genuine in yes_rate==0 floor (n={len(fg)})")
    ax2.scatter(fc.clip_top3, np.random.RandomState(1).normal(0, 0.04, len(fc)),
                s=18, c="#c62828", alpha=0.6, label=f"wrong-content (n={len(fc)})")
    ax2.set_yticks([0, 1]); ax2.set_yticklabels(["cross", "genuine"], fontsize=9)
    ax2.set_xlabel("raw clip_top3"); ax2.set_ylim(-0.4, 1.4)
    ax2.set_title("Inside the saturated yes_rate==0 bin,\nraw CLIP still splits the two classes")
    ax2.legend(fontsize=7.5, loc="upper center"); ax2.grid(axis="x", alpha=0.25)

    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    print(f"n_questions levels: {n_q}  ->  yes_rate bins: {yr_levels}")
    print("standalone pool-free wrong-content AUC (genuine > cross):")
    for c in RAW_SIGNALS:
        print(f"  {c:14s} {aucs[c]:.4f}")
    print(f"binarization AUC loss (adqa_score - yes_rate): {rep['binarization_auc_loss']['delta']:+.4f}")
    print(f"\n'reject yes_rate==0' rule: catch={zero_rule['catch']:.0%}  "
          f"false-flag genuine={zero_rule['false_flag_genuine']:.0%} "
          f"({zero_rule['genuine_at_zero']}/{zero_rule['genuine_total']})  -> perfect recall, useless precision")
    print(f"inside floor: clip_top3 cross={subfloor['clip_top3']['cross_mean']:.3f} "
          f"genuine={subfloor['clip_top3']['genuine_mean']:.3f}  AUC={subfloor['clip_top3']['auc']:.3f}")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
