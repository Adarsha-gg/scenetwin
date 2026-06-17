#!/usr/bin/env python3
"""Can TRIBE close the OOD gap CLIP can't?  Honest test on the corrected 3-tier ladder.

Finding from robustness: on OOD, ADQA-only already gets rho=0.946; the ensemble's
0.952 is barely a lift, and CLIP's only OOD job is fixing strict per-clip ordering
(50/60 -> 58/60). The user wants TRIBE to add the missing signal.

KEY STRUCTURAL FACT: TRIBE's accessibility_gap is ONE value PER CLIP (a property of
the video's AV-vs-A neural response), not per candidate AD. So it CANNOT reorder
tier0<tier1<tier3 within a clip -> it cannot lift within-clip rho by construction.
That is why every TRIBE-as-calibration test returned null (p>0.16). It is the wrong
tool for rho.

What it CAN do is flag which whole clips are hard. We test exactly that: does the
TRIBE gap separate the clips the metric MISORDERS (3-tier) from the ones it nails?
If yes, TRIBE is an orthogonal clip-level review-triage layer (not a rho booster).
Reported honestly either way; N of failures is small so we state power limits.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
EXT = CURSOR / "output" / "external_ensemble_eval.csv"
TRIBE = CURSOR / "research" / "output" / "tribe_counterfactual_external_per_clip.csv"
OUT_JSON = CURSOR / "output" / "tribe_triage_corrected_ladder.json"
CHART = ROOT / "output" / "charts" / "scenetwin_tribe_triage.png"
FINDINGS = CURSOR / "findings" / "tribe-clip-level-triage.md"

THREE = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]
GMAP = {t: i for i, t in enumerate(THREE)}


def minmax(s: pd.Series) -> pd.Series:
    r = s.max() - s.min()
    return (s - s.min()) / r if r else s * 0.0


def per_clip_order(df: pd.DataFrame, score_col: str) -> pd.DataFrame:
    rows = []
    for vid, gg in df.groupby("video_id"):
        by = dict(zip(gg["tier"], gg[score_col]))
        if all(t in by for t in THREE):
            ok = int(by[THREE[0]] < by[THREE[1]] < by[THREE[2]])
            rows.append({"video_id": vid, "ordered": ok})
    return pd.DataFrame(rows)


def auc_mwu(pos: np.ndarray, neg: np.ndarray) -> tuple[float, float]:
    """AUC that gap is HIGHER on failures, + Mann-Whitney p (one-sided)."""
    if len(pos) == 0 or len(neg) == 0:
        return float("nan"), float("nan")
    u, p = mannwhitneyu(pos, neg, alternative="greater")
    return float(u / (len(pos) * len(neg))), float(p)


def main() -> None:
    e = pd.read_csv(EXT)
    e = e[e.tier.isin(THREE)].copy()
    e["adqa_n"] = e.groupby("video_id")["adqa_score"].transform(minmax)
    e["clip_n"] = e.groupby("video_id")["clip_top3"].transform(minmax)
    e["ens"] = 0.5 * e["adqa_n"] + 0.5 * e["clip_n"]

    ens_ord = per_clip_order(e, "ens").rename(columns={"ordered": "ens_ordered"})
    adqa_ord = per_clip_order(e.assign(a=e["adqa_n"]), "a").rename(columns={"ordered": "adqa_ordered"})

    tribe = pd.read_csv(TRIBE)[["video_id", "accessibility_gap"]]
    m = ens_ord.merge(adqa_ord, on="video_id").merge(tribe, on="video_id", how="inner")

    report = {"run_at": datetime.now(timezone.utc).isoformat(), "n_clips": int(len(m))}
    for who, col in [("ensemble", "ens_ordered"), ("adqa_only", "adqa_ordered")]:
        fail = m.loc[m[col] == 0, "accessibility_gap"].values
        ok = m.loc[m[col] == 1, "accessibility_gap"].values
        auc, p = auc_mwu(fail, ok)
        report[who] = {
            "n_fail": int(len(fail)), "n_ok": int(len(ok)),
            "gap_fail_mean": float(np.mean(fail)) if len(fail) else None,
            "gap_ok_mean": float(np.mean(ok)) if len(ok) else None,
            "auc_gap_predicts_failure": auc, "mwu_p_one_sided": p,
        }
        # recall@budget: if we flag the top-k highest-gap clips for human review,
        # what fraction of the metric's failures do we catch?
        order = m.sort_values("accessibility_gap", ascending=False)["video_id"].tolist()
        fails = set(m.loc[m[col] == 0, "video_id"])
        for budget in (0.1, 0.2, 0.3):
            k = max(1, int(round(budget * len(m))))
            caught = len(fails & set(order[:k]))
            report[who][f"recall_at_{int(budget*100)}pct"] = caught / len(fails) if fails else None

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for ax, (who, col, ttl) in zip(axes, [("ensemble", "ens_ordered", "Ensemble (3-tier)"),
                                           ("adqa_only", "adqa_ordered", "ADQA-only (3-tier)")]):
        fail = m.loc[m[col] == 0, "accessibility_gap"].values
        ok = m.loc[m[col] == 1, "accessibility_gap"].values
        ax.boxplot([ok, fail], tick_labels=[f"ordered\nn={len(ok)}", f"misordered\nn={len(fail)}"], widths=0.5)
        ax.scatter(np.random.normal(1, 0.04, len(ok)), ok, s=14, alpha=0.5, color="#1b5e20")
        ax.scatter(np.random.normal(2, 0.04, len(fail)), fail, s=22, alpha=0.7, color="#c62828")
        ax.set_title(f"{ttl}\nAUC={report[who]['auc_gap_predicts_failure']:.2f}, p={report[who]['mwu_p_one_sided']:.2g}")
        ax.set_ylabel("TRIBE accessibility gap (clip-level)")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("TRIBE flags hard CLIPS, not bad ADs: gap vs metric misordering (OOD)", fontsize=12)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    en, aq = report["ensemble"], report["adqa_only"]
    print(f"n={report['n_clips']}")
    print(f"ENSEMBLE  fails={en['n_fail']}  gap fail/ok={en['gap_fail_mean']}/{en['gap_ok_mean']}  AUC={en['auc_gap_predicts_failure']:.3f} p={en['mwu_p_one_sided']:.3g}")
    print(f"ADQA-ONLY fails={aq['n_fail']}  gap fail/ok={aq['gap_fail_mean']:.3f}/{aq['gap_ok_mean']:.3f}  AUC={aq['auc_gap_predicts_failure']:.3f} p={aq['mwu_p_one_sided']:.3g}")
    print(f"ADQA recall@10/20/30%: {aq['recall_at_10pct']:.2f}/{aq['recall_at_20pct']:.2f}/{aq['recall_at_30pct']:.2f}")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
