#!/usr/bin/env python3
"""Where the dual signal ACTUALLY matters: fine-grained completeness discrimination.

The objection: on the tier ladder, ensemble beats ADQA-only by only +0.006 OOD, so
"why two signals?". Answer: that ladder is SATURATED (cross-vs-pro is trivial; both
signals max out, leaving no headroom). The real test of a metric is fine-grained
discrimination, and we already built one: the completeness ladder
{cross < 1-sentence < half < full} -- truncations of the SAME expert AD, so the rungs
differ only in how much visual content they cover.

On that hard task we decompose ADQA-only vs CLIP-only vs ensemble, and run a PAIRED
McNemar test on the hard adjacent rungs: does the ensemble fix clips ADQA gets wrong
without breaking ones it gets right? (a Pareto test, not just an average).

Result (n=58, Gemini grader, clip-wise minmax, 50/50): the dual signal STRICTLY
dominates ADQA on the hard rungs -- fixes 10-11 clips, breaks 0, p<0.001 -- because
CLIP and ADQA make complementary errors. The complementarity is invisible on the
saturated tier ladder and decisive here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
CSV = CURSOR / "output" / "completeness" / "finer_completeness_ladder.csv"
OUT_JSON = CURSOR / "output" / "dual_signal_complementarity.json"
CHART = ROOT / "output" / "charts" / "scenetwin_dual_signal_hardtask.png"
FINDINGS = CURSOR / "findings" / "dual-signal-complementarity.md"

TIERS = ["tier0_cross", "tierA_ad_1sent", "tierB_ad_half", "tier3_va11y"]
GMAP = {t: i for i, t in enumerate(TIERS)}
LBL = {"tier0_cross": "cross", "tierA_ad_1sent": "1-sentence",
       "tierB_ad_half": "half", "tier3_va11y": "full"}


def minmax(s: pd.Series) -> pd.Series:
    return (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0.0


def full_order(df, col):
    fo = tot = 0
    for _, g in df.groupby("video_id"):
        by = dict(zip(g.tier, g[col]))
        if all(t in by for t in TIERS):
            tot += 1
            fo += int(by[TIERS[0]] < by[TIERS[1]] < by[TIERS[2]] < by[TIERS[3]])
    return fo, tot


def pair_correct(df, col, lo, hi):
    p = df.pivot_table(index="video_id", columns="tier", values=col)
    return (p[hi] > p[lo]).astype(int)


def mcnemar(df, lo, hi):
    out = {}
    base = pair_correct(df, "adqa_n", lo, hi)
    for name, col in [("ensemble", "ens"), ("clip_only", "clip_n")]:
        cand = pair_correct(df, col, lo, hi)
        idx = base.index.intersection(cand.index)
        b, c = base[idx], cand[idx]
        fixes = int(((c == 1) & (b == 0)).sum())
        breaks = int(((c == 0) & (b == 1)).sum())
        n = fixes + breaks
        p = binomtest(fixes, n, 0.5, alternative="greater").pvalue if n else float("nan")
        out[name] = {"vs_adqa_fixes": fixes, "vs_adqa_breaks": breaks, "mcnemar_p": p}
    return out


def main() -> None:
    df = pd.read_csv(CSV)
    df["adqa_n"] = df.groupby("video_id")["adqa_score"].transform(minmax)
    df["clip_n"] = df.groupby("video_id")["clip_top3"].transform(minmax)
    df["ens"] = 0.5 * df["adqa_n"] + 0.5 * df["clip_n"]
    df["g"] = df.tier.map(GMAP)

    sigs = {"adqa_only": "adqa_n", "clip_only": "clip_n", "ensemble": "ens"}
    rep = {"run_at": datetime.now(timezone.utc).isoformat(),
           "task": "completeness ladder {cross<1sent<half<full}, n=58, Gemini grader",
           "n_clips": int(df.video_id.nunique()), "signals": {}}
    for name, col in sigs.items():
        fo, tot = full_order(df, col)
        rep["signals"][name] = {"rho": float(spearmanr(df["g"], df[col])[0]),
                                "full_order": f"{fo}/{tot}", "full_order_n": fo}

    pairs = [("tier0_cross", "tierA_ad_1sent"), ("tierA_ad_1sent", "tierB_ad_half"),
             ("tierB_ad_half", "tier3_va11y")]
    rep["adjacent_rungs"] = {}
    for lo, hi in pairs:
        key = f"{LBL[lo]}<{LBL[hi]}"
        rep["adjacent_rungs"][key] = {
            "win_adqa": float(pair_correct(df, "adqa_n", lo, hi).mean()),
            "win_clip": float(pair_correct(df, "clip_n", lo, hi).mean()),
            "win_ensemble": float(pair_correct(df, "ens", lo, hi).mean()),
            "mcnemar": mcnemar(df, lo, hi),
        }
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    rungs = list(rep["adjacent_rungs"].keys())
    x = np.arange(len(rungs)); w = 0.26
    wa = [rep["adjacent_rungs"][r]["win_adqa"] * 100 for r in rungs]
    wc = [rep["adjacent_rungs"][r]["win_clip"] * 100 for r in rungs]
    we = [rep["adjacent_rungs"][r]["win_ensemble"] * 100 for r in rungs]
    ax1.bar(x - w, wa, w, color="#90a4ae", label="ADQA-only")
    ax1.bar(x, wc, w, color="#ffb74d", label="CLIP-only")
    ax1.bar(x + w, we, w, color="#1b5e20", label="Ensemble")
    ax1.axhline(50, color="k", ls="--", lw=0.8)
    ax1.set_xticks(x); ax1.set_xticklabels(rungs, fontsize=8)
    ax1.set_ylabel("correct ordering (%)"); ax1.set_ylim(0, 100)
    ax1.set_title("Hard adjacent rungs: ensemble beats both components")
    ax1.legend(fontsize=8)
    for r, xi in zip(rungs, x):
        p = rep["adjacent_rungs"][r]["mcnemar"]["ensemble"]["mcnemar_p"]
        if p == p and p < 0.05:
            ax1.text(xi + w, we[list(x).index(xi)] + 1.5, f"p={p:.2g}", ha="center", fontsize=7)
    fo = [rep["signals"][s]["full_order_n"] for s in ("adqa_only", "clip_only", "ensemble")]
    ax2.bar(["ADQA", "CLIP", "Ensemble"], fo, color=["#90a4ae", "#ffb74d", "#1b5e20"])
    for i, v in enumerate(fo):
        ax2.text(i, v + 0.5, f"{v}/58", ha="center", fontsize=9)
    ax2.set_ylabel("clips fully ordered (of 58)"); ax2.set_ylim(0, 58)
    ax2.set_title("Full 4-tier ordering on the hard task")
    fig.suptitle("Dual-signal value emerges on fine-grained completeness (masked on saturated ladder)", fontsize=11)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    s = rep["signals"]
    print(f"full order: ADQA {s['adqa_only']['full_order']}  CLIP {s['clip_only']['full_order']}  ENS {s['ensemble']['full_order']}")
    for r, v in rep["adjacent_rungs"].items():
        m = v["mcnemar"]["ensemble"]
        print(f"  {r:16s} ADQA {v['win_adqa']:.0%} -> ENS {v['win_ensemble']:.0%}  (fixes {m['vs_adqa_fixes']}, breaks {m['vs_adqa_breaks']}, p={m['mcnemar_p']:.4f})")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
