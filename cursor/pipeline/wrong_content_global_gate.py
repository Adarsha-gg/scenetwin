#!/usr/bin/env python3
"""OUTCOME: is the wrong-content catch a per-clip-normalization artifact, or a real
single-AD deployable gate?

`gate_outcome.py` reports 100% catch of the wrong-content AD (tier0_cross), but it does
so by ranking a 4-candidate pool and rejecting the *lowest* — a RELATIVE decision that
(a) needs a clean pool at inference and (b) is run on per-clip min-max-normalised columns
that force tier0_cross to 0.0 whenever it is the pool minimum. That makes "100% catch"
partly tautological and undeployable on a single AD.

This script tests the deployment-relevant claim: can a SINGLE GLOBAL absolute threshold on
the RAW (un-normalised) CLIP grounding score separate wrong-content ADs from legitimate
ADs across all clips, with no candidate pool? Honest validation via leave-one-clip-out so
the threshold is never fit on the clip it scores.

Positive (should-reject) = tier0_cross (a real AD describing the WRONG clip).
Negative (should-ship)    = tier1/tier2/tier3 legitimate ADs.
Baseline: gate_outcome random pool gate = 25% catch.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cursor" / "output" / "external_ensemble_eval.csv"
OUT_JSON = ROOT / "cursor" / "output" / "wrong_content_global_gate.json"
CHART = ROOT / "output" / "charts" / "scenetwin_wrong_content_global_gate.png"

RAW_COL = "clip_top3"          # raw CLIP grounding, NOT the per-clip-normalised column
CROSS = "tier0_cross"


def reject_auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """P(wrong-content score < legit score): a low-score-rejects detector."""
    wins = sum((pv < neg).sum() + 0.5 * (pv == neg).sum() for pv in pos)
    return float(wins / (len(pos) * len(neg)))


def youden_threshold(d: pd.DataFrame, col: str) -> float:
    p = d[d.tier == CROSS][col].values
    n = d[d.tier != CROSS][col].values
    best_T, best_j = 0.0, -1.0
    for T in np.unique(d[col].values):
        j = (p < T).mean() - (n < T).mean()
        if j > best_j:
            best_j, best_T = j, T
    return float(best_T)


def main() -> None:
    df = pd.read_csv(SRC)
    pos = df[df.tier == CROSS][RAW_COL].values
    neg = df[df.tier != CROSS][RAW_COL].values
    auc = reject_auc(pos, neg)

    # in-sample Youden operating point (optimistic upper bound)
    T_in = youden_threshold(df, RAW_COL)
    catch_in = float((pos < T_in).mean())
    fa_in = float((neg < T_in).mean())

    # honest leave-one-CLIP-out: threshold fit on the other clips, applied to held-out clip
    vids = sorted(df.video_id.unique())
    c = f = npos = nneg = 0
    folds = []
    for v in vids:
        T = youden_threshold(df[df.video_id != v], RAW_COL)
        te = df[df.video_id == v]
        p = te[te.tier == CROSS][RAW_COL].values
        n = te[te.tier != CROSS][RAW_COL].values
        c += int((p < T).sum()); npos += len(p)
        f += int((n < T).sum()); nneg += len(n)
        folds.append(T)
    loco = {
        "catch_rate": c / npos, "false_alarm_rate": f / nneg,
        "n_pos": npos, "n_neg": nneg,
        "T_median": float(np.median(folds)),
        "T_min": float(min(folds)), "T_max": float(max(folds)),
    }

    # fixed a-priori thresholds (no fitting at all) — robustness check
    fixed = {}
    for T in (0.12, 0.15, 0.18):
        fixed[f"{T:.2f}"] = {"catch_rate": float((pos < T).mean()),
                             "false_alarm_rate": float((neg < T).mean())}

    rep = {
        "source": str(SRC), "raw_col": RAW_COL,
        "random_pool_baseline_catch": 0.25,
        "reject_auc": auc,
        "in_sample_youden": {"T": T_in, "catch_rate": catch_in, "false_alarm_rate": fa_in},
        "leave_one_clip_out": loco,
        "fixed_threshold": fixed,
        "raw_separation": {
            "cross_mean": float(df[df.tier == CROSS][RAW_COL].mean()),
            "cross_max": float(df[df.tier == CROSS][RAW_COL].max()),
            "legit_mean": float(df[df.tier != CROSS][RAW_COL].mean()),
            "legit_min": float(df[df.tier != CROSS][RAW_COL].min()),
        },
    }
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
    # raw-score distributions by tier
    tiers = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
    colors = ["#c62828", "#ef9a9a", "#90caf9", "#1565c0"]
    for t, c_ in zip(tiers, colors):
        ax1.hist(df[df.tier == t][RAW_COL].values, bins=18, alpha=0.6, color=c_, label=t)
    ax1.axvline(loco["T_median"], ls="--", c="k", lw=1.2,
                label=f"LOCO T={loco['T_median']:.3f}")
    ax1.set_xlabel("raw CLIP grounding (clip_top3)"); ax1.set_ylabel("count")
    ax1.set_title("Wrong-content vs legit ADs separate on RAW CLIP")
    ax1.legend(fontsize=7)

    # operating points
    labels = ["LOCO\n(honest)", "in-sample\nYouden", "fixed\nT=0.15"]
    catches = [loco["catch_rate"], catch_in, fixed["0.15"]["catch_rate"]]
    fas = [loco["false_alarm_rate"], fa_in, fixed["0.15"]["false_alarm_rate"]]
    x = np.arange(len(labels)); w = 0.35
    ax2.bar(x - w / 2, catches, w, color="#1b5e20", label="catch wrong-content")
    ax2.bar(x + w / 2, fas, w, color="#c62828", label="false-alarm on legit")
    ax2.axhline(0.25, ls="--", c="gray", lw=1, label="random pool gate 25%")
    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=8)
    ax2.set_ylim(0, 1.05); ax2.set_ylabel("rate")
    ax2.set_title(f"Single-AD global gate (AUC={auc:.3f})")
    ax2.legend(fontsize=7.5)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    print(f"reject-AUC (wrong-content vs legit, raw CLIP): {auc:.3f}  n={len(pos)}+{len(neg)}")
    print(f"LOCO  : catch={loco['catch_rate']:.1%}  false-alarm={loco['false_alarm_rate']:.1%}"
          f"  (T median {loco['T_median']:.3f})")
    print(f"fixed T=0.15: catch={fixed['0.15']['catch_rate']:.0%}  "
          f"false-alarm={fixed['0.15']['false_alarm_rate']:.1%}")
    print(f"random pool baseline catch: 25%")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
