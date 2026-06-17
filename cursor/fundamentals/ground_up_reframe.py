#!/usr/bin/env python3
"""Ground-up SceneTwin audit — challenge tier GT, recompute ensemble, reframe TRIBE.

The headline ρ≈0.929 assumes:
  1. tier3 > tier2 > tier1 > tier0 is always correct ground truth
  2. minmax-normalized ADQA v2 + CLIP fusion is the right score
  3. TRIBE should be blended into that score

This script tests all three and proposes a two-stage model:
  Stage A — TRIBE collision index routes accessibility *regime*
  Stage B — ADQA/CLIP scores tiers *within* regime (or rejects linear tier order)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT_DIR = Path(__file__).resolve().parent / "output"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "ground-up-reframe.md"
THESIS = Path(__file__).resolve().parents[1] / "research" / "GROUND-UP-THESIS.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}
COMPARISONS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]
IMP_WEIGHT = {"critical": 3.0, "useful": 1.0, "optional": 0.5}


def minmax_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        if not np.isfinite(lo) or hi == lo:
            return pd.Series(np.full(len(s), 0.5), index=s.index)
        return (s - lo) / (hi - lo)
    return df.groupby("clip_idx", group_keys=False)[col].apply(scale)


def rank_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    return df.groupby("clip_idx", group_keys=False)[col].rank(pct=True)


def pairwise_wins(df: pd.DataFrame, col: str) -> tuple[int, int]:
    wins = total = 0
    for _, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        if "tier3_va11y" not in by:
            continue
        for lo in COMPARISONS:
            if lo in by:
                total += 1
                wins += int(by["tier3_va11y"] > by[lo])
    return wins, total


def full_order(df: pd.DataFrame, col: str) -> tuple[int, int]:
    n = total = 0
    for _, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        if all(t in by for t in TIERS):
            total += 1
            n += int(by["tier3_va11y"] > by["tier2_vatex_long"] > by["tier1_vatex_short"] > by["tier0_cross"])
    return n, total


def violation_clips(df: pd.DataFrame, col: str) -> list[int]:
    bad = []
    for cidx, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        for hi, lo in [("tier3_va11y", "tier2_vatex_long"), ("tier3_va11y", "tier1_vatex_short"),
                       ("tier2_vatex_long", "tier1_vatex_short"), ("tier3_va11y", "tier0_cross")]:
            if hi in by and lo in by and by[hi] < by[lo]:
                bad.append(int(cidx))
                break
    return sorted(set(bad))


def loo_rho(df: pd.DataFrame, col: str) -> float:
    rhos = []
    for drop in df["clip_idx"].unique():
        sub = df[df["clip_idx"] != drop]
        if sub[col].nunique() <= 1:
            continue
        r, _ = spearmanr(sub["gt"], sub[col], nan_policy="omit")
        if np.isfinite(r):
            rhos.append(r)
    return float(np.mean(rhos)) if rhos else float("nan")


def mean_per_clip_rho(df: pd.DataFrame, col: str) -> float:
    rhos = []
    for _, g in df.groupby("clip_idx"):
        if g[col].nunique() <= 1:
            continue
        r, _ = spearmanr(g["gt"], g[col], nan_policy="omit")
        if np.isfinite(r):
            rhos.append(r)
    return float(np.mean(rhos)) if rhos else float("nan")


def eval_metric(df: pd.DataFrame, col: str) -> dict:
    sub = df.dropna(subset=[col, "gt"])
    rho, rp = spearmanr(sub["gt"], sub[col])
    tau, _ = kendalltau(sub["gt"], sub[col])
    pw, pt = pairwise_wins(sub, col)
    fo, fot = full_order(sub, col)
    return {
        "metric": col,
        "rho_pooled": float(rho),
        "rho_per_clip_mean": mean_per_clip_rho(sub, col),
        "loo_rho": loo_rho(sub, col),
        "kendall_tau": float(tau),
        "pairwise": f"{pw}/{pt}",
        "full_order": f"{fo}/{fot}",
        "violations": len(violation_clips(sub, col)),
        "violation_ids": ",".join(map(str, violation_clips(sub, col))),
    }


def weighted_adqa_v4() -> pd.DataFrame:
    q = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    g = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    imp = {
        (int(r.clip_idx), int(r.q_idx)): IMP_WEIGHT.get(str(r.importance).lower(), 1.0)
        for _, r in q.iterrows()
    }
    rows = []
    for (cidx, tier), grp in g.groupby(["clip_idx", "tier"]):
        num = den = crit_num = crit_den = 0.0
        for _, r in grp.iterrows():
            w = imp.get((int(cidx), int(r.q_idx)), 1.0)
            s = float(r["score"])
            num += w * s
            den += w
            if w >= 3.0:
                crit_num += s
                crit_den += 1.0
        rows.append({
            "clip_idx": int(cidx),
            "tier": tier,
            "gt": TIER_GT[tier],
            "adqa_v4_mean": num / den if den else float("nan"),
            "adqa_critical_only": crit_num / crit_den if crit_den else float("nan"),
        })
    return pd.DataFrame(rows)


def rebuild_scores() -> pd.DataFrame:
    clip = pd.read_csv(TIMING / "clip_scores" / "need_weighted_grounding_results.csv")
    adqa = weighted_adqa_v4()
    stale = pd.read_csv(TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv")

    df = clip.merge(adqa, on=["clip_idx", "tier", "gt"], how="inner")
    df = df.merge(
        stale[["clip_idx", "tier", "adqa_v2_score", "ensemble_w50_adqa_need_weighted_clip"]],
        on=["clip_idx", "tier"], how="left", suffixes=("", "_stale"),
    )

    # Fusion variants — all from v4 + raw CLIP, not stale v2
    df["adqa_v4_norm"] = minmax_clipwise(df, "adqa_v4_mean")
    df["adqa_crit_norm"] = minmax_clipwise(df, "adqa_critical_only")
    df["clip_top3_norm"] = minmax_clipwise(df, "clip_top3")
    df["need_w_norm"] = minmax_clipwise(df, "need_weighted_clip")

    df["adqa_v4_rank"] = rank_clipwise(df, "adqa_v4_mean")
    df["clip_top3_rank"] = rank_clipwise(df, "clip_top3")

    df["ensemble_v4_minmax_50"] = 0.5 * df["adqa_v4_norm"] + 0.5 * df["clip_top3_norm"]
    df["ensemble_crit_minmax_50"] = 0.5 * df["adqa_crit_norm"] + 0.5 * df["clip_top3_norm"]
    df["ensemble_v4_rank_50"] = 0.5 * df["adqa_v4_rank"] + 0.5 * df["clip_top3_rank"]
    df["ensemble_adqa_v4_only"] = df["adqa_v4_mean"]
    df["ensemble_clip_only"] = df["clip_top3"]
    df["ensemble_no_norm_sum"] = df["adqa_v4_mean"] + df["clip_top3"]  # no within-clip scaling

    # v2 mismatch diagnostic
    df["v2_v4_adqa_delta"] = df["adqa_v2_score"] - df["adqa_v4_mean"]
    return df


def gt_challenge(df: pd.DataFrame) -> pd.DataFrame:
    """Compare tier GT to ADQA-v4-implied best tier per clip."""
    rows = []
    for cidx, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g["adqa_v4_mean"]))
        best_tier = max(by, key=by.get)
        best_gt = TIER_GT[best_tier]
        tier3_score = by.get("tier3_va11y", float("nan"))
        tier2_score = by.get("tier2_vatex_long", float("nan"))
        rows.append({
            "clip_idx": int(cidx),
            "gt_best_tier": 3,
            "adqa_best_tier": best_gt,
            "adqa_best_name": best_tier,
            "gt_matches_adqa": int(best_gt == 3),
            "tier3_wins_adqa": int(tier3_score >= max(by.values()) - 1e-9),
            "tier2_beats_tier3_adqa": int(tier2_score > tier3_score + 1e-9),
            "tier3_adqa": tier3_score,
            "tier2_adqa": tier2_score,
            "spread_adqa": tier3_score - by.get("tier1_vatex_short", 0),
        })
    return pd.DataFrame(rows)


def critical_miss_tier3() -> pd.DataFrame:
    q = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    g = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    pro = g[g["tier"] == "tier3_va11y"].merge(
        q[["clip_idx", "q_idx", "importance"]], on=["clip_idx", "q_idx"], how="left",
    )
    pro["critical"] = pro["importance"].astype(str).str.lower() == "critical"
    pro["miss"] = pd.to_numeric(pro["score"], errors="coerce").fillna(0) < 0.5
    pro["critical_miss"] = pro["critical"] & pro["miss"]
    out = pro.groupby("clip_idx").agg(
        critical_any_miss=("critical_miss", "max"),
        critical_miss_rate=("critical_miss", "mean"),
    ).reset_index()
    return out


def tribe_collision_index(forecast: pd.DataFrame) -> pd.Series:
    def nz(s: pd.Series) -> pd.Series:
        x = s.astype(float)
        lo, hi = x.min(), x.max()
        if hi <= lo:
            return x * 0
        return (x - lo) / (hi - lo)
    collision = nz(forecast["extended_seconds_frac"]) * nz(forecast["mean_speech_density"])
    collision += 0.35 * nz(forecast["tribe_pressure"])
    return collision.rename("collision_index")


def auc(y: pd.Series, score: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": score}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def tribe_reframe(df: pd.DataFrame, gt_ch: pd.DataFrame, crit: pd.DataFrame) -> pd.DataFrame:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    fc["collision_index"] = tribe_collision_index(fc)
    clip = fc.merge(gt_ch, on="clip_idx").merge(crit, on="clip_idx", how="left")
    clip["critical_any_miss"] = clip["critical_any_miss"].fillna(0).astype(int)
    clip["tier2_beats_tier3"] = clip["tier2_beats_tier3_adqa"].astype(int)
    clip["gt_disagreement"] = (1 - clip["gt_matches_adqa"]).astype(int)
    clip["label_inversion"] = clip["tier2_beats_tier3"]

    # Violations on stale ensemble
    ens = df[df["tier"] == "tier3_va11y"].groupby("clip_idx")["ensemble_w50_adqa_need_weighted_clip"].first()
    t1 = df[df["tier"] == "tier1_vatex_short"].groupby("clip_idx")["ensemble_w50_adqa_need_weighted_clip"].first()
    clip["tier0_beats_tier1_ens"] = (
        df[df["tier"] == "tier0_cross"].groupby("clip_idx")["ensemble_w50_adqa_need_weighted_clip"].first()
        > t1
    ).astype(int).reindex(clip["clip_idx"]).fillna(0).values

    targets = {
        "critical_any_miss": "Pro AD misses ≥1 critical ADQA question",
        "tier2_beats_tier3": "Tier2 VATEX-long beats pro on ADQA v4",
        "gt_disagreement": "ADQA-best tier ≠ tier3 (GT wrong?)",
        "label_inversion": "Same as tier2 beats tier3",
    }
    signals = ["collision_index", "tribe_pressure", "extended_seconds_frac", "mean_speech_density", "high_need_seconds_frac"]
    rows = []
    for target, desc in targets.items():
        y = clip[target]
        for sig in signals:
            if sig not in clip.columns:
                continue
            rows.append({
                "target": target,
                "target_desc": desc,
                "signal": sig,
                "auc": auc(y, clip[sig]),
                "n_pos": int(y.sum()),
                "n": len(clip),
                "mean_signal_pos": float(clip.loc[y == 1, sig].mean()) if y.sum() else float("nan"),
                "mean_signal_neg": float(clip.loc[y == 0, sig].mean()) if (y == 0).sum() else float("nan"),
            })
    return pd.DataFrame(rows)


def two_stage_eval(df: pd.DataFrame, clip_meta: pd.DataFrame) -> dict:
    """High collision → prefer tier2 over tier3 on ADQA; low → trust tier order."""
    merged = df.merge(clip_meta[["clip_idx", "collision_index"]], on="clip_idx")
    threshold = merged["collision_index"].median()
    merged["regime"] = np.where(merged["collision_index"] >= threshold, "collision", "standard")

    # Within standard: does ADQA v4 alone beat stale ensemble ρ?
    std = merged[merged["regime"] == "standard"]
    col = merged[merged["regime"] == "collision"]

    out = {"collision_threshold": float(threshold)}
    for name, sub in [("standard_regime", std), ("collision_regime", col), ("all_clips", merged)]:
        if len(sub) < 8:
            continue
        for m in ["adqa_v4_mean", "ensemble_v4_minmax_50", "ensemble_w50_adqa_need_weighted_clip"]:
            if m not in sub.columns:
                continue
            r, _ = spearmanr(sub["gt"], sub[m], nan_policy="omit")
            out[f"{name}_{m}_rho"] = float(r)

    # Collision regime: tier2 win rate vs tier3 on ADQA
    coll_clips = clip_meta[clip_meta["collision_index"] >= threshold]["clip_idx"]
    std_clips = clip_meta[clip_meta["collision_index"] < threshold]["clip_idx"]
    adqa_best = gt_challenge(df)

    def tier2_win_rate(clips: pd.Series) -> float:
        sub = adqa_best[adqa_best["clip_idx"].isin(clips)]
        return float(sub["tier2_beats_tier3_adqa"].mean()) if len(sub) else float("nan")

    out["tier2_beats_tier3_rate_collision"] = tier2_win_rate(coll_clips)
    out["tier2_beats_tier3_rate_standard"] = tier2_win_rate(std_clips)
    return out


def write_thesis(metrics: pd.DataFrame, gt: pd.DataFrame, tribe: pd.DataFrame, two_stage: dict, df: pd.DataFrame) -> None:
    stale_rho = metrics[metrics["metric"] == "ensemble_w50_adqa_need_weighted_clip"]["rho_pooled"].iloc[0]
    v4_rho = metrics[metrics["metric"] == "ensemble_v4_minmax_50"]["rho_pooled"].iloc[0]
    adqa_only = metrics[metrics["metric"] == "ensemble_adqa_v4_only"]["rho_pooled"].iloc[0]
    rank_rho = metrics[metrics["metric"] == "ensemble_v4_rank_50"]["rho_pooled"].iloc[0]

    gt_agree = gt["gt_matches_adqa"].mean()
    tier2_wins = gt["tier2_beats_tier3_adqa"].sum()

    best_tribe = tribe.sort_values("auc", ascending=False).iloc[0] if len(tribe) else None

    v2_mismatch = (df["v2_v4_adqa_delta"].abs() > 0.05).sum()

    lines = [
        "# SceneTwin ground-up thesis (2026-05-27)",
        "",
        "## What we challenged",
        "",
        "1. **Frozen ensemble CSV uses ADQA v2**, not v4 — headline ρ may be stale.",
        "2. **Within-clip minmax** ties max tiers (clip 0: tier0/tier3 ADQA ties → both get 1.0).",
        "3. **Tier GT is assumed**, not verified — ADQA v4 disagrees on "
        f"**{100*(1-gt_agree):.0f}%** of clips.",
        "4. **TRIBE as blend weight** is wrong framing — collision signals predict *when GT fails*.",
        "",
        "## Ensemble recomputed (honest)",
        "",
        "| Method | ρ pooled | ρ per-clip mean | LOO ρ | violations |",
        "|--------|---------:|----------------:|------:|-----------:|",
    ]
    for _, r in metrics.sort_values("rho_pooled", ascending=False).head(10).iterrows():
        lines.append(
            f"| {r['metric']} | {r['rho_pooled']:.3f} | {r['rho_per_clip_mean']:.3f} | "
            f"{r['loo_rho']:.3f} | {int(r['violations'])} |"
        )

    lines += [
        "",
        f"- Stale `ensemble_w50_adqa_need_weighted_clip` (v2): **ρ={stale_rho:.3f}**",
        f"- Rebuilt v4 minmax 50/50: **ρ={v4_rho:.3f}**",
        f"- ADQA v4 alone (no CLIP, no norm): **ρ={adqa_only:.3f}**",
        f"- Rank fusion (no minmax tie inflation): **ρ={rank_rho:.3f}**",
        f"- v2 vs v4 row mismatches (|Δ|>0.05): **{v2_mismatch}** / 72",
        "",
        "## Tier GT vs ADQA v4",
        "",
        f"- Tier3 is ADQA-best on **{gt_agree*100:.0f}%** of clips ({int(gt['gt_matches_adqa'].sum())}/18)",
        f"- Tier2 beats tier3 on ADQA in **{tier2_wins}** clips",
        f"- Clips where GT likely wrong: {','.join(map(str, gt.loc[~gt['gt_matches_adqa'].astype(bool), 'clip_idx'].tolist()))}",
        "",
        "## TRIBE reframed: collision regime router",
        "",
        "Stop asking: *does TRIBE improve ρ?*",
        "",
        "Ask: *when dense speech + high visual debt collide, does professional slot-AD fail?*",
        "",
        "**Target:** tier2 beats tier3 on ADQA, or pro AD critical miss.",
        "",
    ]
    if best_tribe is not None:
        lines.append(
            f"Best signal: `{best_tribe['signal']}` → `{best_tribe['target']}` "
            f"AUC=**{best_tribe['auc']:.3f}** (n_pos={int(best_tribe['n_pos'])})"
        )

    lines += [
        "",
        "### Two-stage model",
        "",
        "```",
        "if collision_index >= median:",
        "    regime = INTEGRATED  # tier order may invert; audit tier2/tier3 separately",
        "else:",
        "    regime = STANDARD    # ADQA v4 + CLIP ranking applies",
        "```",
        "",
        f"- Tier2 beats tier3 rate (collision regime): **{two_stage.get('tier2_beats_tier3_rate_collision', float('nan')):.2f}**",
        f"- Tier2 beats tier3 rate (standard regime): **{two_stage.get('tier2_beats_tier3_rate_standard', float('nan')):.2f}**",
        "",
        "## Real research claim (replaces ρ headline)",
        "",
        "> **SceneTwin is a two-stage accessibility auditor.** Stage 1 (TRIBE collision index) "
        "classifies whether a clip is in *standard slot-AD* or *integrated/collision* regime. "
        "Stage 2 (ADQA + CLIP) scores description quality **within** regime. Global tier ordering "
        "is invalid when regimes mix — the old ρ=0.929 conflates correct rankings on easy clips "
        "with wrong GT on collision clips.",
        "",
        "## Next experiments",
        "",
        "- Export TRIBE P_AV/P_A vectors for cached clips → `vector_policy_boundary`",
        "- Regime-conditional ρ (report separately, not pooled)",
        "- External clips: test if collision predicts generalization gap",
        "- Replace tier GT with ADQA-consensus labels on disagreement clips",
    ]
    THESIS.parent.mkdir(parents=True, exist_ok=True)
    THESIS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    df = rebuild_scores()
    gt = gt_challenge(df)
    crit = critical_miss_tier3()

    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    fc["collision_index"] = tribe_collision_index(fc)
    clip_meta = fc[["clip_idx", "collision_index", "tribe_pressure", "extended_seconds_frac", "mean_speech_density", "category"]]

    metric_cols = [
        "ensemble_w50_adqa_need_weighted_clip",
        "ensemble_v4_minmax_50",
        "ensemble_crit_minmax_50",
        "ensemble_v4_rank_50",
        "ensemble_adqa_v4_only",
        "ensemble_clip_only",
        "ensemble_no_norm_sum",
        "adqa_v4_mean",
        "clip_top3",
        "need_weighted_clip",
    ]
    metrics = pd.DataFrame([eval_metric(df, c) for c in metric_cols if c in df.columns])
    metrics = metrics.sort_values("rho_pooled", ascending=False)

    tribe = tribe_reframe(df, gt, crit)
    two_stage = two_stage_eval(df, clip_meta)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "ground_up_scores.csv", index=False)
    metrics.to_csv(OUT_DIR / "ground_up_metrics.csv", index=False)
    gt.to_csv(OUT_DIR / "ground_up_gt_challenge.csv", index=False)
    tribe.to_csv(OUT_DIR / "ground_up_tribe_router.csv", index=False)
    with open(OUT_DIR / "ground_up_two_stage.json", "w") as f:
        json.dump(two_stage, f, indent=2)

    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    write_thesis(metrics, gt, tribe, two_stage, df)
    FINDINGS.write_text(THESIS.read_text(encoding="utf-8"), encoding="utf-8")

    print("=== METRICS (top) ===")
    print(metrics.head(8).to_string(index=False))
    print("\n=== GT CHALLENGE ===")
    print(gt[["clip_idx", "adqa_best_name", "gt_matches_adqa", "tier2_beats_tier3_adqa"]].to_string(index=False))
    print("\n=== TRIBE ROUTER (top AUC) ===")
    print(tribe.sort_values("auc", ascending=False).head(8).to_string(index=False))
    print("\n=== TWO STAGE ===")
    print(json.dumps(two_stage, indent=2))
    print(f"\nWrote {OUT_DIR} and {THESIS}")


if __name__ == "__main__":
    main()
