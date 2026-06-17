#!/usr/bin/env python3
"""Turn the hallucination-sensitivity result into a calibrated GATE with an operating point.

Compares three gate designs on the same 60 clips (expert AD vs same-length hallucinated /
faithful-paraphrase twins) and reports ROC + an operating point at 10% false-positive:

  1. zero-reference  : decompose candidate AD into claims, flag by weakest CLIP claim
                       grounding (no reference). -> WEAK (absolute grounding too noisy).
  2. with-reference  : score the candidate's CLIP grounding DROP vs a trusted reference AD
                       (a prior approved AD or a 2nd generation). -> strong.
  3. with-reference  : fuse CLIP-drop + ADQA-drop. -> strongest (dual signal pays off).

Conclusion: SceneTwin is a deployable hallucination gate in the realistic QA setting where
a reference AD exists; it is NOT yet a turnkey zero-shot single-AD gate.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
HG = CURSOR / "output" / "halluc_gate" / "halluc_gate.csv"
CLAIMS = CURSOR / "output" / "claim_gate" / "claims.csv"
OUT_JSON = CURSOR / "output" / "gate_summary.json"
CHART = ROOT / "output" / "charts" / "scenetwin_gate_summary.png"


def op_point(y, s, fpr_target=0.10):
    """threshold so FPR on negatives == target; return recall + actual fpr."""
    neg = s[y == 0]; pos = s[y == 1]
    tau = np.quantile(neg, 1 - fpr_target)  # higher score => positive (lie)
    return float((pos > tau).mean()), float((neg > tau).mean()), float(tau)


def main() -> None:
    hg = pd.read_csv(HG).dropna(subset=["clip_para", "adqa_para"])
    cl = pd.read_csv(CLAIMS)

    # 1. zero-reference: AD-level weakest claim grounding (top1). lie=halluc, clean=expert+para
    admin = cl.groupby(["video_id", "kind"])["grounding_top1"].min().reset_index()
    lie0 = admin[admin.kind == "halluc"]["grounding_top1"].values
    clean0 = admin[admin.kind != "halluc"]["grounding_top1"].values
    y0 = np.r_[np.ones(len(lie0)), np.zeros(len(clean0))]
    s0 = -np.r_[lie0, clean0]  # lower grounding => more likely lie => higher score
    auc0 = roc_auc_score(y0, s0)

    # 2. with-reference: CLIP grounding drop vs reference (expert). lie=halluc, neg=paraphrase
    dh = (hg.clip_expert - hg.clip_halluc).values
    dp = (hg.clip_expert - hg.clip_para).values
    y1 = np.r_[np.ones(len(dh)), np.zeros(len(dp))]
    s1 = np.r_[dh, dp]
    auc1 = roc_auc_score(y1, s1)

    # 3. with-reference fused: CLIP-drop + ADQA-drop (each scaled by its own clip-level SD)
    ah = (hg.adqa_expert - hg.adqa_halluc).values
    ap = (hg.adqa_expert - hg.adqa_para).values
    cs, as_ = hg.clip_expert.std(), hg.adqa_expert.std()
    fh = dh / cs + ah / as_
    fp = dp / cs + ap / as_
    y2 = np.r_[np.ones(len(fh)), np.zeros(len(fp))]
    s2 = np.r_[fh, fp]
    auc2 = roc_auc_score(y2, s2)

    rep = {"n_clips": int(len(hg)),
           "zero_reference_claim_gate": {"auc": float(auc0)},
           "with_reference_clip_drop": {"auc": float(auc1)},
           "with_reference_clip_plus_adqa": {"auc": float(auc2)}}
    for key, (y, s) in {"zero_reference_claim_gate": (y0, s0),
                        "with_reference_clip_drop": (y1, s1),
                        "with_reference_clip_plus_adqa": (y2, s2)}.items():
        r, f, t = op_point(y, s)
        rep[key].update({"recall_at_10pct_fpr": r, "actual_fpr": f, "tau": t})
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.4, 6))
    curves = [
        ("zero-reference (claim grounding)", y0, s0, auc0, "#c62828", rep["zero_reference_claim_gate"]),
        ("with-reference: CLIP grounding-drop", y1, s1, auc1, "#ef6c00", rep["with_reference_clip_drop"]),
        ("with-reference: CLIP + ADQA fused", y2, s2, auc2, "#1b5e20", rep["with_reference_clip_plus_adqa"]),
    ]
    for label, y, s, auc, c, info in curves:
        fpr, tpr, _ = roc_curve(y, s)
        ax.plot(fpr, tpr, "-", color=c, lw=2.2, label=f"{label}  (AUC={auc:.2f})")
        ax.scatter([info["actual_fpr"]], [info["recall_at_10pct_fpr"]], color=c, s=45, zorder=5,
                   edgecolor="white", linewidth=0.8)
    ax.plot([0, 1], [0, 1], "--", color="gray", lw=1, label="chance")
    ax.axvline(0.10, color="gray", ls=":", lw=1)
    ax.set_xlabel("false-positive rate (flagging a truthful AD)")
    ax.set_ylabel("hallucination recall")
    ax.set_title("Reference-free vs reference-comparison hallucination gate\n"
                 f"(n={rep['n_clips']} clips; same-length lies vs faithful paraphrase)\n"
                 "dots = operating point at 10% FPR")
    ax.legend(loc="lower right", fontsize=8.5); ax.grid(alpha=0.25)
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    for k in ("zero_reference_claim_gate", "with_reference_clip_drop", "with_reference_clip_plus_adqa"):
        r = rep[k]
        print(f"{k:34s}: AUC={r['auc']:.3f}  recall={r['recall_at_10pct_fpr']:.0%} @ FPR={r['actual_fpr']:.0%}")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
