#!/usr/bin/env python3
"""TRIBE use-case lab — novel applications beyond failure forecast.

Experiments:
  UC1  Need routing accuracy — extended windows where ADQA critical is low
  UC2  Category gap profiles — which genres have highest accessibility pressure
  UC3  Risk score vs label violations (2 known GT failures)
  UC4  Speech-heavy clips — TRIBE extended frac vs ADQA on tier3
  UC5  Need peak timing vs AD slot generator alignment
  UC6  Counterfactual gap proxy — tribe_pressure predicts when cross-tier0 wins
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = Path(__file__).resolve().parent / "output" / "tribe_usecase_lab.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "fundamentals-tribe-usecases.md"

ENSEMBLE_COL = "ensemble_w50_adqa_need_weighted_clip"


def _tier_vals(g: pd.DataFrame, col: str) -> dict[str, float]:
    return dict(zip(g["tier"], g[col]))


def main() -> None:
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    forecast = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    adqa = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv")
    ens = pd.read_csv(TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv")

    rows = []

    # UC1: extended windows — do they correlate with low tier3 ADQA?
    ext_frac = forecast.set_index("clip_idx")["extended_seconds_frac"]
    t3_adqa = adqa[adqa["tier"] == "tier3_va11y"].set_index("clip_idx")["adqa_v4_score"]
    common = ext_frac.index.intersection(t3_adqa.index)
    if len(common) >= 5:
        r, p = spearmanr(ext_frac[common], t3_adqa[common])
        rows.append({
            "usecase": "UC1_extended_vs_tier3_adqa",
            "stat": f"rho={r:.3f}",
            "p_value": p,
            "n": len(common),
            "finding": "negative rho → extended need clips are harder for pro AD (expected)",
        })

    # UC2: category gap profiles
    cat_gap = forecast.groupby("category").agg(
        mean_pressure=("tribe_pressure", "mean"),
        mean_extended=("extended_seconds_frac", "mean"),
        n_clips=("clip_idx", "count"),
    ).reset_index()
    top = cat_gap.sort_values("mean_pressure", ascending=False).head(3)
    rows.append({
        "usecase": "UC2_category_gap_profile",
        "stat": top["category"].tolist().__str__(),
        "p_value": float("nan"),
        "n": len(cat_gap),
        "finding": f"highest pressure categories: {list(top['category'])}",
    })

    # UC3: risk vs known failures (clip 0 cross-video, clip 12 tier2>tier1)
    known_fail = {0, 12}
    forecast["known_fail"] = forecast["clip_idx"].isin(known_fail)
    fail_risk = forecast[forecast["known_fail"]]["risk_score"]
    ok_risk = forecast[~forecast["known_fail"]]["risk_score"]
    if len(fail_risk) >= 1 and len(ok_risk) >= 3:
        _, p = mannwhitneyu(fail_risk, ok_risk, alternative="greater")
        rows.append({
            "usecase": "UC3_risk_separates_known_failures",
            "stat": f"fail_mean={fail_risk.mean():.3f}, ok_mean={ok_risk.mean():.3f}",
            "p_value": p,
            "n": len(forecast),
            "finding": "risk score should rank clip_00/12 above median",
        })

    # UC4: speech-heavy — high mean_speech_density clips
    speech = forecast.set_index("clip_idx")["mean_speech_density"]
    ens_t3 = ens[ens["tier"] == "tier3_va11y"].set_index("clip_idx")[ENSEMBLE_COL]
    common = speech.index.intersection(ens_t3.index)
    heavy = speech[common] >= speech[common].median()
    r_heavy, _ = spearmanr(speech[common], ens_t3[common])
    margin_heavy = ens_t3[heavy].mean() - ens_t3[~heavy].mean()
    rows.append({
        "usecase": "UC4_speech_density_vs_tier3_ensemble",
        "stat": f"rho={r_heavy:.3f}, margin_heavy-lean={margin_heavy:.3f}",
        "p_value": float("nan"),
        "n": len(common),
        "finding": "speech-heavy clips may need integrated AD not standard slots",
    })

    # UC5: need peak count vs extended slot count from generator output
    gen_dir = Path(__file__).resolve().parents[1] / "methods" / "output" / "generated_ad"
    if gen_dir.exists():
        slot_counts = []
        for p in gen_dir.glob("clip_*_slots.jsonl"):
            cidx = int(p.stem.split("_")[1])
            n_ext = sum(1 for line in p.read_text().splitlines()
                        if line and "extended" in line)
            n_need_ext = (need[(need["clip_idx"] == cidx) &
                               (need["recommendation"].str.contains("extended", na=False))]).shape[0]
            slot_counts.append((n_need_ext, n_ext))
        if slot_counts:
            need_ext, gen_ext = zip(*slot_counts)
            r, p = spearmanr(need_ext, gen_ext)
            rows.append({
                "usecase": "UC5_need_windows_vs_generated_slots",
                "stat": f"rho={r:.3f}",
                "p_value": p,
                "n": len(slot_counts),
                "finding": "ADX3 slot generator should track TRIBE extended windows",
            })

    # UC6: tribe_pressure when tier0 beats tier1 (cross-video confound clips)
    confound_clips = []
    for cidx, g in ens.groupby("clip_idx"):
        v = _tier_vals(g, ENSEMBLE_COL)
        if v.get("tier0_cross", 0) > v.get("tier1_vatex_short", 0):
            confound_clips.append(cidx)
    if confound_clips:
        press_conf = forecast[forecast["clip_idx"].isin(confound_clips)]["tribe_pressure"].mean()
        press_other = forecast[~forecast["clip_idx"].isin(confound_clips)]["tribe_pressure"].mean()
        rows.append({
            "usecase": "UC6_pressure_on_cross_video_confound_clips",
            "stat": f"confound={press_conf:.3f}, other={press_other:.3f}",
            "p_value": float("nan"),
            "n": len(confound_clips),
            "finding": f"clips where tier0>tier1: {confound_clips} — check if low-pressure Food clips",
        })

    # UC7: NEW — TRIBE as AD length recommender
    t3_words = forecast.set_index("clip_idx")["tier3_va11y_words"]
    r_len, p_len = spearmanr(forecast["tribe_pressure"], t3_words)
    rows.append({
        "usecase": "UC7_pressure_vs_pro_ad_length",
        "stat": f"rho={r_len:.3f}",
        "p_value": p_len,
        "n": len(forecast),
        "finding": "if positive: high-need clips already have longer pro AD (human alignment)",
    })

    rep = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rep.to_csv(OUT, index=False)

    lines = ["# TRIBE use-case lab\n\n", "Novel applications beyond ρ=0.929 ensemble headline.\n\n"]
    for _, r in rep.iterrows():
        pstr = f"p={r['p_value']:.4f}" if np.isfinite(r["p_value"]) else ""
        lines.append(f"### {r['usecase']}\n\n")
        lines.append(f"- {r['stat']} {pstr} (n={int(r['n'])})\n")
        lines.append(f"- {r['finding']}\n\n")

    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(rep.to_string(index=False))
    print(f"\nWrote {OUT} and {FINDINGS}")


if __name__ == "__main__":
    main()
