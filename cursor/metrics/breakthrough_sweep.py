#!/usr/bin/env python3
"""Re-evaluate ALL discovered + novel metrics and test every pairwise combination."""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
METRICS = CURSOR / "metrics"
REGISTRY = METRICS / "discovery_registry.jsonl"
NOVEL_CSV = METRICS / "output" / "novel_metrics_scores.csv"
OUT_DIR = METRICS / "output"
REPORT = CURSOR / "findings" / "breakthrough-sweep.md"

# import shared frame builder
sys.path.insert(0, str(METRICS))
from discovery_engine import (  # noqa: E402
    REGISTRY as _,
    build_base_frame,
    eval_recipe,
    evaluate_metric,
    minmax_clipwise,
)

BLEND_MODES = ("mean_mm", "product", "max", "abs_diff", "harmonic")
TARGETS = [
    "ensemble_violation",
    "critical_miss",
    "judge_disagree",
    "gt_dispute",
    "low_margin",
]


def auc(y: pd.Series, score: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": score}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def clip_mm(s: pd.Series) -> pd.Series:
    s = pd.Series(s, index=s.index if hasattr(s, "index") else None, dtype=float)
    lo, hi = s.min(), s.max()
    if not np.isfinite(lo) or hi == lo:
        return pd.Series(0.5, index=s.index)
    return (s - lo) / (hi - lo)


def blend(a: pd.Series, b: pd.Series, mode: str) -> pd.Series:
    aa, bb = clip_mm(a), clip_mm(b)
    if mode == "mean_mm":
        return 0.5 * aa + 0.5 * bb
    if mode == "product":
        return aa * bb
    if mode == "max":
        return np.maximum(aa, bb)
    if mode == "abs_diff":
        return (aa - bb).abs()
    if mode == "harmonic":
        return 2 * aa * bb / (aa + bb + 1e-6)
    raise ValueError(mode)


def eval_on_t3(df: pd.DataFrame, col: str) -> dict:
    t3 = df[df["tier"] == "tier3_va11y"].dropna(subset=[col])
    out = {}
    if len(df.dropna(subset=[col, "gt"])) >= 8 and df[col].nunique() > 1:
        rho, _ = spearmanr(df["gt"], df[col], nan_policy="omit")
        out["tier_gt_rho"] = float(rho)
    for t in TARGETS:
        if t in t3.columns and t3[t].nunique() > 1:
            out[f"auc_{t}"] = auc(t3[t], t3[col])
    return out


def load_singles(df: pd.DataFrame) -> dict[str, pd.Series]:
    metrics: dict[str, pd.Series] = {}

    # baselines from frame
    df["ensemble_v4"] = 0.5 * minmax_clipwise(df, "adqa_v4_score") + 0.5 * minmax_clipwise(df, "clip_top3")
    metrics["ensemble_v4_minmax50"] = df["ensemble_v4"]
    metrics["adqa_v4_score"] = df["adqa_v4_score"]
    metrics["clip_top3"] = df["clip_top3"]
    metrics["tribe_pressure"] = df["tribe_pressure"]

    # discovery registry
    rows = [json.loads(l) for l in REGISTRY.read_text().splitlines() if l.strip()]
    for r in rows:
        name = r["name"]
        series = eval_recipe(df, name, r["recipe"])
        if series is not None:
            metrics[f"disc:{name}"] = series

    # novel metrics (tier-level columns on tier3 rows matter for clip targets)
    novel = pd.read_csv(NOVEL_CSV)
    novel_cols = [
        "comprehension_per_second", "false_grounding_gap", "temporal_misalign",
        "visual_lexicon_purity", "audio_leakage", "saturation_ratio", "rank_chaos",
        "head_agreement_index", "inversion_mass_adqa", "marginal_word_value_t3",
        "research_audit_index",
    ]
    for c in novel_cols:
        if c in novel.columns:
            m = novel.set_index(["clip_idx", "tier"])[c]
            mapped = df.set_index(["clip_idx", "tier"]).index.map(m)
            metrics[f"novel:{c}"] = pd.Series(mapped.values, index=df.index, dtype=float)

    return metrics


def score_row(name: str, series: pd.Series, df: pd.DataFrame) -> dict:
    tmp = df.copy()
    tmp["_m"] = series
    ev = eval_on_t3(tmp, "_m")
    best_auc = max((ev.get(f"auc_{t}", float("nan")) for t in TARGETS), default=float("nan"))
    best_target = max(TARGETS, key=lambda t: ev.get(f"auc_{t}", 0) or 0)
    return {
        "name": name,
        "kind": "single" if ":" in name or name.startswith("ensemble") else "single",
        "best_target": f"auc_{best_target}",
        "best_auc": best_auc,
        "tier_gt_rho": ev.get("tier_gt_rho", float("nan")),
        **{f"auc_{t}": ev.get(f"auc_{t}", float("nan")) for t in TARGETS},
    }


def main() -> None:
    df = build_base_frame()
    singles = load_singles(df)
    print(f"Loaded {len(singles)} single metrics")

    single_rows = [score_row(n, s, df) for n, s in singles.items()]
    singles_df = pd.DataFrame(single_rows).sort_values("best_auc", ascending=False)
    singles_df.to_csv(OUT_DIR / "breakthrough_singles.csv", index=False)

    # ALL pairwise combinations × blend modes
    names = list(singles.keys())
    pair_rows = []
    for i, (a, b) in enumerate(combinations(names, 2)):
        sa, sb = singles[a], singles[b]
        for mode in BLEND_MODES:
            combo_name = f"pair:{a}|{b}|{mode}"
            series = blend(sa, sb, mode)
            ev = score_row(combo_name, series, df)
            ev["kind"] = "pair"
            ev["metric_a"] = a
            ev["metric_b"] = b
            ev["blend"] = mode
            pair_rows.append(ev)
        if (i + 1) % 200 == 0:
            print(f"  pairs {i+1}/{len(list(combinations(names,2)))}")

    pairs_df = pd.DataFrame(pair_rows).sort_values("best_auc", ascending=False)
    pairs_df.to_csv(OUT_DIR / "breakthrough_pairs.csv", index=False)
    print(f"Tested {len(pair_rows)} pairwise combos ({len(names)} metrics × {len(BLEND_MODES)} blends)")

    # ALL triple mean blends among top-20 singles per best_auc
    top20 = singles_df.head(20)["name"].tolist()
    triple_rows = []
    for a, b, c in combinations(top20, 3):
        s = (clip_mm(singles[a]) + clip_mm(singles[b]) + clip_mm(singles[c])) / 3.0
        combo_name = f"triple:{a}|{b}|{c}|mean_mm"
        ev = score_row(combo_name, s, df)
        ev["kind"] = "triple"
        triple_rows.append(ev)
    triples_df = pd.DataFrame(triple_rows).sort_values("best_auc", ascending=False)
    triples_df.to_csv(OUT_DIR / "breakthrough_triples.csv", index=False)
    print(f"Tested {len(triple_rows)} triple combos (top-20 singles)")

    # QC gate: down-weight ensemble when risk composite is high
    risk_metrics = [
        "disc:lex_minus_clip",
        "disc:peak_over_words",
        "novel:inversion_mass_adqa",
        "novel:false_grounding_gap",
        "disc:diff(need_mean,speech_mean)",
    ]
    risk_parts = [clip_mm(singles[m]) for m in risk_metrics if m in singles]
    gate_row = {}
    if risk_parts:
        risk = sum(risk_parts) / len(risk_parts)
        tmp = df.copy()
        ens = 0.5 * minmax_clipwise(df, "adqa_v4_score") + 0.5 * minmax_clipwise(df, "clip_top3")
        tmp["gated_ensemble"] = ens * (1 - 0.5 * risk)
        gate_row = score_row("qc_gated_ensemble_v4", tmp["gated_ensemble"], df)
        risk_row = score_row("risk_composite_5", risk, df)

    # Report
    lines = [
        "# Breakthrough sweep — all singles, all pairs, top triples\n\n",
        f"**Singles:** {len(singles)} | **Pairs:** {len(pair_rows)} | **Triples:** {len(triple_rows)}\n\n",
        "## Top 15 singles (any research target)\n\n",
        "| metric | best target | AUC | tier ρ |\n|--------|-------------|----:|-------:|\n",
    ]
    for _, r in singles_df.head(15).iterrows():
        lines.append(
            f"| `{r['name'][:55]}` | {r['best_target']} | {r['best_auc']:.3f} | {r.get('tier_gt_rho', float('nan')):.3f} |\n"
        )

    lines.append("\n## Top 20 pairwise combos\n\n")
    lines.append("| combo | blend | best target | AUC | tier ρ |\n|-------|-------|-------------|----:|-------:|\n")
    for _, r in pairs_df.head(20).iterrows():
        lines.append(
            f"| `{r['metric_a'][:25]}` + `{r['metric_b'][:25]}` | {r['blend']} | {r['best_target']} | "
            f"{r['best_auc']:.3f} | {r.get('tier_gt_rho', float('nan')):.3f} |\n"
        )

    lines.append("\n## Top 15 triple blends (top-20 singles)\n\n")
    lines.append("| triple | best target | AUC | tier ρ |\n|--------|-------------|----:|-------:|\n")
    for _, r in triples_df.head(15).iterrows():
        lines.append(
            f"| `{r['name'][:70]}` | {r['best_target']} | {r['best_auc']:.3f} | {r.get('tier_gt_rho', float('nan')):.3f} |\n"
        )

    # Per-target best
    lines.append("\n## Best per target\n\n")
    all_df = pd.concat([singles_df, pairs_df, triples_df], ignore_index=True)
    for t in TARGETS:
        col = f"auc_{t}"
        if col in all_df.columns:
            best = all_df.sort_values(col, ascending=False).iloc[0]
            lines.append(
                f"- **{t}**: `{best['name'][:80]}` → **{best[col]:.3f}** (kind={best.get('kind','?')})\n"
            )

    if risk_parts:
        base_rho = singles_df.loc[singles_df["name"] == "ensemble_v4_minmax50", "tier_gt_rho"].iloc[0]
        lines.append(
            f"\n## QC gate\n\n"
            f"- Gated ensemble tier ρ: **{gate_row.get('tier_gt_rho', float('nan')):.3f}** "
            f"(baseline ensemble_v4: **{base_rho:.3f}**)\n"
            f"- Risk composite AUC violation: **{risk_row.get('auc_ensemble_violation', float('nan')):.3f}**\n"
        )

    # Breakthrough callouts
    lines.append("\n## Breakthrough callouts\n\n")
    perfect = all_df[all_df["best_auc"] >= 0.99]
    for _, r in perfect.drop_duplicates("name").head(10).iterrows():
        lines.append(f"- `{r['name'][:90]}` → {r['best_target']} **{r['best_auc']:.3f}**\n")

    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"\nWrote {REPORT}")
    print(f"  singles → {OUT_DIR / 'breakthrough_singles.csv'}")
    print(f"  pairs   → {OUT_DIR / 'breakthrough_pairs.csv'}")
    print(f"  triples → {OUT_DIR / 'breakthrough_triples.csv'}")


if __name__ == "__main__":
    main()
