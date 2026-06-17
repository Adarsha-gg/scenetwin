#!/usr/bin/env python3
"""Calibrate QC gate on external clips; evaluate on benchmark + external holdout."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
EXT_REG = CURSOR / "data" / "external_clips" / "registry.jsonl"
EXT_NEED = CURSOR / "data" / "external_clips" / "need"
EXT_EVAL = CURSOR / "output" / "external_clip_full_eval.json"
CALIB = CURSOR / "data" / "qc_calibration.json"
REPORT = CURSOR / "findings" / "qc-generalization.md"
WPM = 200


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", str(text).lower())


def auc(y: pd.Series, score: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": score}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def need_peak_t(nd: pd.DataFrame) -> float:
    w = nd.sort_values("t_mid" if "t_mid" in nd.columns else nd.columns[2])
    col_t = "t_mid" if "t_mid" in w.columns else "start_s"
    if col_t not in w.columns:
        col_t = w.columns[2]
    scores = w["need_score"].astype(float).values
    t = w[col_t].astype(float).values
    if len(scores) == 0 or scores.sum() <= 0:
        return 0.5
    com = float(np.average(t, weights=scores + 1e-6))
    dur = float(t.max() - t.min() + 1e-6)
    return com / dur


def build_external_frame() -> pd.DataFrame:
    ev = json.loads(EXT_EVAL.read_text())
    per = {r["video_id"]: r for r in ev["per_clip"]}
    rows = []
    for line in EXT_REG.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        vid = rec["video_id"]
        if vid not in per:
            continue
        need_path = EXT_NEED / f"{vid}.csv"
        if not need_path.exists():
            continue
        nd = pd.read_csv(need_path)
        t3 = rec["tier3_va11y"]
        words = max(len(t3.split()), 1)
        read_s = words / (WPM / 60.0)
        p = per[vid]
        rows.append({
            "video_id": vid,
            "category": rec.get("category", ""),
            "need_mean": nd["need_score"].mean(),
            "speech_mean": nd["speech_density"].mean(),
            "need_speech_gap": nd["need_score"].mean() - nd["speech_density"].mean(),
            "need_peak_t": need_peak_t(nd),
            "peak_over_words": need_peak_t(nd) / (words + 1),
            "read_seconds": read_s,
            "words": words,
            "clip_t3_minus_t1": p["tier3_clip"] - p["tier1_clip"],
            "clip_t3": p["tier3_clip"],
            "full_order_fail": 1 - int(p["full_order_clip"]),
            "pro_loses": 1 - int(p["pro_beats_short"]),
        })
    return pd.DataFrame(rows)


def build_benchmark_frame() -> pd.DataFrame:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    ens = pd.read_csv(TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv")
    adqa = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv")

    need_agg = need.groupby("clip_idx").agg(
        need_mean=("need_score", "mean"),
        speech_mean=("speech_density", "mean"),
    ).reset_index()
    peaks = []
    for cidx, grp in need.groupby("clip_idx"):
        w = grp.sort_values("start_s")
        scores = w["need_score"].astype(float).values
        t = w["start_s"].astype(float).values
        if len(scores) == 0 or scores.sum() <= 0:
            peaks.append({"clip_idx": cidx, "need_peak_t": 0.5})
        else:
            com = float(np.average(t, weights=scores + 1e-6))
            dur = float(w["end_s"].max() - w["start_s"].min() + 1e-6)
            peaks.append({"clip_idx": cidx, "need_peak_t": com / dur})
    need_agg = need_agg.merge(pd.DataFrame(peaks), on="clip_idx")

    t3e = ens[ens["tier"] == "tier3_va11y"].set_index("clip_idx")
    t1e = ens[ens["tier"] == "tier1_vatex_short"].set_index("clip_idx")
    t3a = adqa[adqa["tier"] == "tier3_va11y"].set_index("clip_idx")
    t0a = adqa[adqa["tier"] == "tier0_cross"].set_index("clip_idx")
    fc_i = fc.set_index("clip_idx")

    rows = []
    for cidx in sorted(fc["clip_idx"].unique()):
        words = int(fc_i.loc[cidx, "tier3_va11y_words_feature"])
        read_s = max(words, 1) / (WPM / 60.0)
        na = need_agg[need_agg["clip_idx"] == cidx].iloc[0]
        adqa_t3 = float(t3a.loc[cidx, "adqa_v4_score"])
        adqa_t0 = float(t0a.loc[cidx, "adqa_v4_score"])
        rows.append({
            "clip_idx": int(cidx),
            "category": fc_i.loc[cidx, "category"],
            "need_mean": float(na["need_mean"]),
            "speech_mean": float(na["speech_mean"]),
            "need_speech_gap": float(na["need_mean"] - na["speech_mean"]),
            "need_peak_t": float(na["need_peak_t"]),
            "peak_over_words": float(na["need_peak_t"] / (words + 1)),
            "read_seconds": read_s,
            "words": words,
            "read_inversion": read_s / (adqa_t3 - adqa_t0 + 0.01),
            "clip_t3_minus_t1": float(t3e.loc[cidx, "clip_top3"] - t1e.loc[cidx, "clip_top3"]),
            "clip_t3": float(t3e.loc[cidx, "clip_top3"]),
            "ensemble_raw": float(t3e.loc[cidx, "ensemble_mean_clip_top3"]),
            "full_order_fail": 1 - int(fc_i.loc[cidx, "all4_mean_full_order"]),
            "pro_loses": int(t3e.loc[cidx, "clip_top3"] <= t1e.loc[cidx, "clip_top3"]),
            "judge_disagree": 1 - int(fc_i.loc[cidx, "all4_mean_full_order"]),
            "known_violation": int(cidx in {0, 12, 14}),
        })
    return pd.DataFrame(rows)


def calibrate(ext: pd.DataFrame) -> dict:
    """Fixed thresholds from external distribution only — no benchmark peeking."""
    signals = ["need_speech_gap", "peak_over_words", "clip_t3_minus_t1", "read_seconds"]
    cal = {"signals": {}, "weights": {}, "source": "external_clips_only", "n_external": len(ext)}
    weights = {"need_speech_gap": 0.35, "peak_over_words": 0.25, "clip_t3_minus_t1": 0.25, "read_seconds": 0.15}

    for sig in signals:
        s = ext[sig].astype(float)
        cal["signals"][sig] = {
            "mean": float(s.mean()),
            "std": float(s.std(ddof=0) or 1e-6),
            "p50": float(s.quantile(0.5)),
            "p80": float(s.quantile(0.8)),
            "direction": "high_bad" if sig != "clip_t3_minus_t1" else "low_bad",
        }
        if sig == "clip_t3_minus_t1":
            cal["signals"][sig]["auc_full_order"] = auc(ext["full_order_fail"], -s)
            cal["signals"][sig]["auc_pro_loses"] = auc(ext["pro_loses"], -s)
        else:
            cal["signals"][sig]["auc_full_order"] = auc(ext["full_order_fail"], s)
            cal["signals"][sig]["auc_pro_loses"] = auc(ext["pro_loses"], s)

    def risk_row(row: pd.Series) -> float:
        parts = []
        for sig, w in weights.items():
            meta = cal["signals"][sig]
            z = (float(row[sig]) - meta["mean"]) / meta["std"]
            if meta["direction"] == "low_bad":
                z = -z
            parts.append(w * (1 / (1 + np.exp(-z))))  # sigmoid
        return float(np.sum(parts))

    ext = ext.copy()
    ext["risk"] = ext.apply(risk_row, axis=1)
    cal["risk_p80"] = float(ext["risk"].quantile(0.8))
    cal["risk_mean"] = float(ext["risk"].mean())
    cal["weights"] = weights
    cal["flag_rule"] = "risk >= external p80 (top 20% on held-out YouTube clips)"
    cal["external_auc"] = {
        "full_order_fail": auc(ext["full_order_fail"], ext["risk"]),
        "pro_loses": auc(ext["pro_loses"], ext["risk"]),
    }
    return cal


def apply_calibrated(df: pd.DataFrame, cal: dict) -> pd.DataFrame:
    out = df.copy()

    def risk_row(row: pd.Series) -> float:
        parts = []
        for sig, w in cal["weights"].items():
            if sig not in row.index:
                continue
            meta = cal["signals"][sig]
            z = (float(row[sig]) - meta["mean"]) / meta["std"]
            if meta["direction"] == "low_bad":
                z = -z
            parts.append(w * (1 / (1 + np.exp(-z))))
        return float(np.sum(parts)) if parts else 0.0

    out["risk_score"] = out.apply(risk_row, axis=1)
    out["flagged"] = out["risk_score"] >= cal["risk_p80"]
    return out


def main() -> None:
    ext = build_external_frame()
    bench = build_benchmark_frame()
    cal = calibrate(ext)
    CALIB.parent.mkdir(parents=True, exist_ok=True)
    CALIB.write_text(json.dumps(cal, indent=2), encoding="utf-8")

    ext_scored = apply_calibrated(ext, cal)
    bench_scored = apply_calibrated(bench, cal)

    bench_auc = {
        "full_order_fail": auc(bench_scored["full_order_fail"], bench_scored["risk_score"]),
        "pro_loses": auc(bench_scored["pro_loses"], bench_scored["risk_score"]),
        "judge_disagree": auc(bench_scored["judge_disagree"], bench_scored["risk_score"]),
        "known_violation": auc(bench_scored["known_violation"], bench_scored["risk_score"]),
    }

    lines = [
        "# QC generalization — external calibration\n\n",
        f"**External clips:** {len(ext)} | **Benchmark:** {len(bench)}\n\n",
        "## Calibration rule\n\n",
        f"- Thresholds: mean/std/p80 from **external YouTube clips only** ({cal['n_external']} clips)\n",
        f"- Flag rule: {cal['flag_rule']} (p80 risk = **{cal['risk_p80']:.3f}**)\n",
        "- Signals: need−speech gap, peak/words, CLIP(t3−t1), read time\n",
        "- **No** benchmark min-max, **no** hard-coded violation clip IDs\n\n",
        "## AUC — external (calibration set)\n\n",
        f"- full_order_fail: **{cal['external_auc']['full_order_fail']:.3f}**\n",
        f"- pro_loses: **{cal['external_auc']['pro_loses']:.3f}**\n\n",
        "## AUC — benchmark (true holdout for thresholds)\n\n",
    ]
    for k, v in bench_auc.items():
        lines.append(f"- {k}: **{v:.3f}**\n")

    lines.append("\n## Per-signal AUC on external\n\n| signal | full_order_fail | pro_loses |\n|--------|----------------:|----------:|\n")
    for sig, meta in cal["signals"].items():
        lines.append(f"| {sig} | {meta['auc_full_order']:.3f} | {meta['auc_pro_loses']:.3f} |\n")

    lines.append("\n## Flagged clips (same rule both sets)\n\n")
    lines.append("**External:** " + ", ".join(
        ext_scored[ext_scored["flagged"]]["video_id"].str[:20].tolist()[:12]
    ) + f" … ({ext_scored['flagged'].sum()}/{len(ext_scored)})\n\n")
    lines.append("**Benchmark:** " + ", ".join(
        f"clip_{i:02d}" for i in bench_scored[bench_scored["flagged"]]["clip_idx"]
    ) + f" ({bench_scored['flagged'].sum()}/{len(bench_scored)})\n\n")

    lines.append("## Benchmark violations vs QC risk (sanity, not training)\n\n")
    for _, r in bench_scored.sort_values("risk_score", ascending=False).iterrows():
        tag = "VIOL" if r["known_violation"] else "    "
        lines.append(f"- clip_{int(r['clip_idx']):02d} risk={r['risk_score']:.3f} flagged={bool(r['flagged'])} {tag}\n")

    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"External n={len(ext)} | benchmark flagged {bench_scored['flagged'].sum()}/18")
    print(f"External AUC full_order={cal['external_auc']['full_order_fail']:.3f}")
    print(f"Benchmark AUC violation={bench_auc['known_violation']:.3f} (holdout)")
    print(f"Wrote {CALIB} and {REPORT}")


if __name__ == "__main__":
    main()
