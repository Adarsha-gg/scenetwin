#!/usr/bin/env python3
"""Neural Contrastive Retrieval (NCR) — local analyzer.

Consumes the retrieval cosines produced in Colab by
`cursor/research/tribe_ncr_dump_cell.py` and answers:

  Q1 (quality ordering): does an AD's neural retrievability rise tier0<tier1<tier3?
      -> per-tier mean rank-percentile / margin / R@1, and Spearman rho vs tier.
  Q2 (wrong-content control — the test neural closure FAILED): does tier0_cross
      (an AD copied from a DIFFERENT clip) sit near CHANCE while tier3 sits high?
  Q3: does per-clip tier3 retrieval margin track the ensemble's per-clip quality?

NCR is verbosity-robust (cosine + rank) and AD-dependent, unlike accessibility_gap.
If retrieval is at chance for all tiers, NCR is an honest negative (report it).

Usage:
  # after downloading ncr_similarity.csv into cursor/research/output/
  python neural_contrastive_retrieval.py
  # verify the pipeline + see expected output shape without Colab data:
  python neural_contrastive_retrieval.py --selftest
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
SIM_CSV = CURSOR / "research" / "output" / "ncr_similarity.csv"
ENS_CSV = CURSOR / "output" / "external_ensemble_eval.csv"
OUT_JSON = CURSOR / "output" / "neural_contrastive_retrieval.json"
CHART = ROOT / "output" / "charts" / "scenetwin_ncr.png"
FINDINGS = CURSOR / "findings" / "neural-contrastive-retrieval.md"

THREE = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]
GMAP = {t: i for i, t in enumerate(THREE)}


def per_query_retrieval(sim: pd.DataFrame) -> pd.DataFrame:
    """For each (query_vid, tier): rank of the correct ref, margin, percentile, R@k."""
    rows = []
    for (qv, tier), g in sim.groupby(["query_vid", "tier"]):
        g = g.sort_values("cos", ascending=False).reset_index(drop=True)
        n = len(g)
        if qv not in set(g["ref_vid"]) or n < 3:
            continue
        rank = int(g.index[g["ref_vid"] == qv][0]) + 1  # 1 = best
        self_cos = float(g.loc[g["ref_vid"] == qv, "cos"].iloc[0])
        distr = g.loc[g["ref_vid"] != qv, "cos"]
        rows.append({
            "query_vid": qv, "tier": tier, "n_ref": n, "rank": rank,
            "rank_pct": (n - rank) / (n - 1),          # 1=top, 0=bottom, .5=chance
            "recip_rank": 1.0 / rank,
            "margin": self_cos - float(distr.mean()),  # +ve = correct beats avg distractor
            "r_at_1": int(rank == 1), "r_at_5": int(rank <= 5),
        })
    return pd.DataFrame(rows)


def make_selftest_sim(n=60, seed=0) -> pd.DataFrame:
    """Synthesize a plausible similarity table where better tiers retrieve better.
    PURELY to validate the analysis code path — NOT a result."""
    rng = np.random.default_rng(seed)
    vids = [f"clip{i:02d}" for i in range(n)]
    signal = {"tier0_cross": 0.0, "tier1_vatex_short": 0.18,
              "tier2_vatex_long": 0.20, "tier3_va11y": 0.30}
    rows = []
    for qi, qv in enumerate(vids):
        for tier, s in signal.items():
            base = rng.normal(0, 0.1, n)
            base[qi] += s + rng.normal(0, 0.05)  # correct clip gets a tier-scaled bump
            for rv, c in zip(vids, base):
                rows.append({"query_vid": qv, "tier": tier, "ref_vid": rv, "cos": float(c)})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    synthetic = False
    if args.selftest:
        sim = make_selftest_sim(); synthetic = True
        print("[SELFTEST] synthetic similarity table — output is NOT a real result")
    elif SIM_CSV.exists():
        sim = pd.read_csv(SIM_CSV)
    else:
        print(f"No retrieval data at {SIM_CSV}.")
        print("Run cursor/research/tribe_ncr_dump_cell.py in Colab, download")
        print("ncr_similarity.csv into cursor/research/output/, then rerun.")
        print("To validate the analysis pipeline now: --selftest")
        return

    pq = per_query_retrieval(sim)
    chance = 0.5

    def tier_block(name, tiers):
        d = pq[pq.tier.isin(tiers)].copy()
        d["g"] = d.tier.map({t: i for i, t in enumerate(tiers)})
        rho = float(spearmanr(d["g"], d["rank_pct"])[0]) if d["g"].nunique() > 1 else float("nan")
        rho_m = float(spearmanr(d["g"], d["margin"])[0]) if d["g"].nunique() > 1 else float("nan")
        return {"rho_tier_vs_rankpct": rho, "rho_tier_vs_margin": rho_m, "n_rows": int(len(d))}

    rep = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_selftest": synthetic,
        "n_queries": int(pq.query_vid.nunique()),
        "n_ref": int(pq["n_ref"].max()) if len(pq) else 0,
        "per_tier": {}, "ordering": {}, "wrong_content_control": {},
    }
    for t in sorted(pq.tier.unique()):
        s = pq[pq.tier == t]
        rep["per_tier"][t] = {
            "rank_pct_mean": float(s.rank_pct.mean()), "margin_mean": float(s.margin.mean()),
            "r_at_1": float(s.r_at_1.mean()), "r_at_5": float(s.r_at_5.mean()),
            "median_rank": float(s["rank"].median()), "n": int(len(s)),
        }
    rep["ordering"]["three_tier"] = tier_block("3tier", THREE)
    rep["ordering"]["all_tiers"] = tier_block("all", sorted(pq.tier.unique()))

    # Q2 wrong-content control: tier0 vs chance, tier3 vs chance (one-sample via wilcoxon on rank_pct-0.5)
    for t in ("tier0_cross", "tier3_va11y"):
        s = pq[pq.tier == t]["rank_pct"]
        if len(s) >= 6 and s.nunique() > 1:
            try:
                w_p = float(wilcoxon(s - chance, alternative="greater").pvalue)
            except ValueError:
                w_p = float("nan")
        else:
            w_p = float("nan")
        rep["wrong_content_control"][t] = {
            "rank_pct_mean": float(s.mean()) if len(s) else None,
            "above_chance_frac": float((s > chance).mean()) if len(s) else None,
            "p_above_chance": w_p,
        }

    # Q3: tier3 retrieval margin vs ensemble per-clip quality (if ensemble data present)
    if not synthetic and ENS_CSV.exists():
        ens = pd.read_csv(ENS_CSV)
        t3q = (ens[ens.tier == "tier3_va11y"][["video_id", "ensemble_mean_clip_top3"]]
               .rename(columns={"video_id": "query_vid"}))
        j = pq[pq.tier == "tier3_va11y"].merge(t3q, on="query_vid", how="inner")
        if len(j) > 5:
            rep["q3_tier3_margin_vs_ensemble_rho"] = float(spearmanr(j["margin"], j["ensemble_mean_clip_top3"])[0])

    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    # chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tiers = [t for t in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
             if t in rep["per_tier"]]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
    rp = [rep["per_tier"][t]["rank_pct_mean"] for t in tiers]
    r1 = [rep["per_tier"][t]["r_at_1"] for t in tiers]
    x = np.arange(len(tiers)); w = 0.36
    ax1.bar(x - w / 2, rp, w, color="#00695c", label="mean rank-percentile")
    ax1.bar(x + w / 2, r1, w, color="#26a69a", label="R@1")
    ax1.axhline(chance, color="k", ls="--", lw=0.8, label="chance (rank-pct)")
    ax1.set_xticks(x); ax1.set_xticklabels([t.split("_")[0] for t in tiers], fontsize=8)
    ax1.set_ylim(0, 1); ax1.legend(fontsize=7); ax1.set_title("Neural retrievability by tier")
    for t, g in pq.groupby("tier"):
        if t in tiers:
            ax2.scatter(np.full(len(g), tiers.index(t)) + np.random.normal(0, 0.05, len(g)),
                        g["rank_pct"], s=10, alpha=0.4)
    ax2.axhline(chance, color="k", ls="--", lw=0.8)
    ax2.set_xticks(x); ax2.set_xticklabels([t.split("_")[0] for t in tiers], fontsize=8)
    ax2.set_ylabel("rank-percentile (1=retrieves right clip)"); ax2.set_title("Per-clip retrieval spread")
    title = "Neural Contrastive Retrieval" + (" [SELFTEST — synthetic]" if synthetic else "")
    fig.suptitle(title, fontsize=12); fig.tight_layout()
    CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    print(f"queries={rep['n_queries']} refs={rep['n_ref']}")
    for t in tiers:
        b = rep["per_tier"][t]
        print(f"  {t:20s} rank_pct={b['rank_pct_mean']:.3f}  R@1={b['r_at_1']:.2f}  median_rank={b['median_rank']:.0f}")
    print(f"  rho(tier, rank_pct) 3-tier = {rep['ordering']['three_tier']['rho_tier_vs_rankpct']:.3f}")
    wc = rep["wrong_content_control"]
    print(f"  control: tier0 rank_pct={wc['tier0_cross']['rank_pct_mean']}, "
          f"tier3 rank_pct={wc['tier3_va11y']['rank_pct_mean']} (p_above_chance={wc['tier3_va11y']['p_above_chance']})")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
