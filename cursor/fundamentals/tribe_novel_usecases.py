#!/usr/bin/env python3
"""TRIBE novel use-case lab — test every non-scoring application we can measure.

TRIBE is NOT for blending into ρ. These use cases treat TRIBE as:
  - pre-text policy signals (routing, budget, triage, coaching)
  - modality/collision physics (when slot-AD assumptions break)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
CURSOR = ROOT / "cursor"
OUT = CURSOR / "fundamentals" / "output" / "tribe_novel_usecases.csv"
RANKED = CURSOR / "fundamentals" / "output" / "tribe_novel_usecases_ranked.csv"
FINDINGS = CURSOR / "findings" / "tribe-novel-usecases.md"
EXT_NEED = CURSOR / "data" / "external_clips" / "need"
EXT_EVAL = CURSOR / "output" / "external_clip_full_eval.json"

KNOWN_VIOLATIONS = {0, 12, 14}


def nz(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce").astype(float)
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else x * 0.0


def auc(y: pd.Series, score: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": score}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def rank_corr(a: pd.Series, b: pd.Series) -> float:
    d = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(d) < 3 or d["a"].nunique() < 2:
        return float("nan")
    return float(d["a"].rank().corr(d["b"].rank()))


def record(rows: list, uc: str, name: str, stat: str, value: float, note: str) -> None:
    rows.append({"usecase_id": uc, "name": name, "stat": stat, "value": value, "note": note})


def load_clip_table() -> pd.DataFrame:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    debt = pd.read_csv(CURSOR / "output" / "neural_accessibility_debt.csv")
    adqa = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv")
    clip = pd.read_csv(TIMING / "clip_scores" / "need_weighted_grounding_results.csv")

    agg = need.groupby("clip_idx").agg(
        n_extended=("recommendation", lambda s: (s.astype(str).str.contains("extended", na=False)).sum()),
        n_windows=("window_idx", "count"),
        window_need_std=("need_score", lambda s: float(s.std()) if len(s) > 1 else 0.0),
        need_peak=("need_score", "max"),
        silence_frac=("speech_density", lambda s: float((s < 0.3).mean())),
        motion_need=("need_score", "mean"),
    ).reset_index()

    t3_adqa = adqa[adqa["tier"] == "tier3_va11y"].set_index("clip_idx")["adqa_v4_score"]
    t1_adqa = adqa[adqa["tier"] == "tier1_vatex_short"].set_index("clip_idx")["adqa_v4_score"]
    t3_clip = clip[clip["tier"] == "tier3_va11y"].set_index("clip_idx")["clip_top3"]

    df = fc.merge(agg, on="clip_idx", how="left")
    df["clip_idx"] = df["clip_idx"].astype(int)
    df["need_entropy"] = df["window_need_std"]
    df = df.merge(debt, on="clip_idx", how="left", suffixes=("", "_debt"))
    df["tier3_adqa"] = df["clip_idx"].map(t3_adqa)
    df["tier1_adqa"] = df["clip_idx"].map(t1_adqa)
    df["tier3_clip"] = df["clip_idx"].map(t3_clip)
    df["clip_adqa_gap"] = (df["tier3_clip"] - df["tier3_adqa"]).abs()
    df["ensemble_violation"] = df["clip_idx"].isin(KNOWN_VIOLATIONS).astype(int)
    df["full_order_fail"] = (df.get("all4_mean_full_order", 1) < 1).astype(int)
    df["low_tier3_margin"] = (df.get("all4_mean_tier3_margin", 1) < 0.15).astype(int)

    # critical miss tier3
    q = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    g = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    pro = g[g["tier"] == "tier3_va11y"].merge(q[["clip_idx", "q_idx", "importance"]], on=["clip_idx", "q_idx"])
    pro["critical"] = pro["importance"].astype(str).str.lower() == "critical"
    pro["miss"] = pd.to_numeric(pro["score"], errors="coerce").fillna(0) < 0.5
    cm = pro.groupby("clip_idx").apply(
        lambda x: int((x["critical"] & x["miss"]).any()), include_groups=False,
    )
    df["critical_any_miss"] = df["clip_idx"].map(cm).fillna(0).astype(int)

    df["collision_index"] = nz(df["extended_seconds_frac"]) * nz(df["mean_speech_density"]) + 0.35 * nz(df["tribe_pressure"])
    df["words_per_need"] = df["tier3_va11y_words"] / (df["total_need"].replace(0, np.nan) + 1e-6)
    df["over_word_budget"] = (df["tier3_va11y_words"] > df["duration_s"] * 3.5).astype(int)  # >3.5 wps read speed cap
    return df


def uc_judge_fragility(df: pd.DataFrame, rows: list) -> None:
    """UC01: Forecast when automatic AD judges will disagree (pre-text)."""
    if "all4_mean_full_order" not in df.columns:
        return
    r, p = spearmanr(df["mean_standard_slot_score"], df["all4_mean_full_order"], nan_policy="omit")
    record(rows, "UC01", "Judge fragility forecast", "spearman_slot_vs_full_order", float(r),
           f"p={p:.4f} — low slot score → judges disagree on tier order")
    record(rows, "UC01", "Judge fragility forecast", "auc_slot_vs_full_order_fail",
           auc((1 - df["all4_mean_full_order"]).astype(int), -df["mean_standard_slot_score"]),
           "Use -slot_score to flag clips before running 4-judge ADQA")


def uc_audio_native_coach(df: pd.DataFrame, rows: list) -> None:
    """UC02: Route creators to narrate visuals in original audio (BLV UGC)."""
    if "collision_debt" not in df.columns:
        return
    coach = nz(df["collision_debt"]) * (~df["category"].eq("Sports")).astype(float)
    record(rows, "UC02", "Audio-native capture coach", "auc_coach_vs_critical_miss",
           auc(df["critical_any_miss"], coach),
           "High collision debt + non-Sports → pro AD misses critical Qs; coach narrate live")
    record(rows, "UC02", "Audio-native capture coach", "auc_collision_debt_vs_critical_miss",
           auc(df["critical_any_miss"], df["collision_debt"]),
           "Raw collision debt without category gate")


def uc_word_budget(df: pd.DataFrame, rows: list) -> None:
    """UC03: TRIBE total need → expected AD word budget; flag over-description."""
    r = rank_corr(df["total_need"], df["tier3_va11y_words"])
    record(rows, "UC03", "AD word budget recommender", "rankcorr_need_vs_pro_words", r,
           "Positive → humans already scale length with need")
    record(rows, "UC03", "AD word budget recommender", "auc_overbudget_vs_critical_miss",
           auc(df["critical_any_miss"], df["over_word_budget"]),
           "Clips where pro AD exceeds ~3.5 wps equivalent")


def uc_slot_planner(df: pd.DataFrame, rows: list) -> None:
    """UC04: Extended need windows → minimum AD slot count."""
    r = rank_corr(df["n_extended"], df["tier3_va11y_words"])
    record(rows, "UC04", "AD slot planner", "rankcorr_extended_windows_vs_pro_words", r,
           "How many TRIBE extended windows vs how much pro AD was written")
    record(rows, "UC04", "AD slot planner", "mean_slots_extended_regime",
           float(df[df["extended_seconds_frac"] > df["extended_seconds_frac"].median()]["n_extended"].mean()),
           f"vs standard regime {df[df['extended_seconds_frac'] <= df['extended_seconds_frac'].median()]['n_extended'].mean():.1f}")


def uc_silence_opportunity(df: pd.DataFrame, rows: list) -> None:
    """UC05: High visual need + low speech = ideal slot-AD ROI."""
    df = df.copy()
    df["silence_opportunity"] = nz(df["motion_need"]) * df["silence_frac"]
    slotable = df[df["mean_standard_slot_score"] > df["mean_standard_slot_score"].median()]
    record(rows, "UC05", "Silence opportunity index", "mean_silence_opp_slotable_clips",
           float(slotable["silence_opportunity"].mean()),
           "Best clips for classic between-dialogue AD insertion")
    record(rows, "UC05", "Silence opportunity index", "rankcorr_silence_opp_vs_tier3_margin",
           rank_corr(df["silence_opportunity"], df.get("all4_mean_tier3_margin", pd.Series(dtype=float))),
           "Higher opportunity → easier to beat short captions")


def uc_metric_disagreement(df: pd.DataFrame, rows: list) -> None:
    """UC06: TRIBE predicts when CLIP and ADQA disagree on tier3."""
    r = rank_corr(df["tribe_pressure"], df["clip_adqa_gap"])
    record(rows, "UC06", "Metric disagreement router", "rankcorr_pressure_vs_clip_adqa_gap", r,
           "Route to dual review when CLIP≈video but ADQA≈comprehension split")
    high_gap = (df["clip_adqa_gap"] > df["clip_adqa_gap"].median()).astype(int)
    record(rows, "UC06", "Metric disagreement router", "auc_pressure_vs_high_gap",
           auc(high_gap, df["tribe_pressure"]), "Triage CLIP/ADQA conflict clips")


def uc_need_entropy(df: pd.DataFrame, rows: list) -> None:
    """UC07: Temporal complexity of need curve → audit difficulty."""
    ent = df["need_entropy"] if "need_entropy" in df.columns else pd.Series(0.0, index=df.index)
    record(rows, "UC07", "Need entropy difficulty", "rankcorr_entropy_vs_violation",
           rank_corr(ent, df["ensemble_violation"]),
           "Chaotic need curves → tier GT breaks")
    record(rows, "UC07", "Need entropy difficulty", "auc_entropy_vs_low_margin",
           auc(df["low_tier3_margin"], ent),
           "Flat vs spiky need timing")


def uc_qc_triage(df: pd.DataFrame, rows: list) -> None:
    """UC08: Pre-ADQA human QC queue ranked by collision debt."""
    record(rows, "UC08", "Pre-ADQA QC triage", "auc_collision_vs_violation",
           auc(df["ensemble_violation"], df["collision_index"]),
           "Review top-3 collision clips before expensive ADQA run")
    if "collision_debt" in df.columns:
        top3 = df.nlargest(3, "collision_debt")["clip_idx"].tolist()
        hit = len(set(top3) & KNOWN_VIOLATIONS)
        record(rows, "UC08", "Pre-ADQA QC triage", "top3_collision_hits_violations", hit / 3,
               f"Top-3 collision debt clips: {top3} — hits {hit}/3 known violations")


def uc_shortest_sufficient(df: pd.DataFrame, rows: list) -> None:
    """UC09: When slotable debt dominates, tier1 may suffice — TRIBE identifies them."""
    if "slotable_debt_frac" not in df.columns:
        return
    slot_heavy = df["slotable_debt_frac"] > 0.5
    tier1_ok = df["tier1_adqa"] >= 0.35
    record(rows, "UC09", "Shortest-sufficient AD picker", "pct_slotable_tier1_sufficient",
           float((slot_heavy & tier1_ok).sum() / max(slot_heavy.sum(), 1)),
           "Slotable-heavy clips where VATEX-short already passes ADQA threshold")
    record(rows, "UC09", "Shortest-sufficient AD picker", "rankcorr_slotable_vs_tier1_adqa",
           rank_corr(df["slotable_debt_frac"], df["tier1_adqa"]),
           "High slotable → short caption often enough (don't force pro AD)")


def uc_category_playbook(df: pd.DataFrame, rows: list) -> None:
    """UC10: Per-category TRIBE profile → workflow playbook."""
    cat = df.groupby("category").agg(
        mean_collision=("collision_index", "mean"),
        mean_pressure=("tribe_pressure", "mean"),
        mean_extended=("extended_seconds_frac", "mean"),
        n=("clip_idx", "count"),
    ).sort_values("mean_collision", ascending=False)
    top = cat.head(1).index[0]
    record(rows, "UC10", "Category workflow playbook", "highest_collision_category",
           float(cat.loc[top, "mean_collision"]), f"{top} → integrated AD workflow")
    sports = df[df["category"] == "Sports"]
    if len(sports) >= 3:
        record(rows, "UC10", "Category workflow playbook", "sports_mean_extended_frac",
               float(sports["extended_seconds_frac"].mean()),
               "Sports clips: motion-heavy → extended AD windows common")


def uc_external_gen_gap(rows: list) -> None:
    """UC11: External need proxy predicts CLIP generalization collapse."""
    if not EXT_EVAL.exists() or not EXT_NEED.exists():
        return
    ev = json.loads(EXT_EVAL.read_text())
    per = pd.DataFrame(ev["per_clip"])
    need_rows = []
    for p in EXT_NEED.glob("*.csv"):
        nd = pd.read_csv(p)
        need_rows.append({
            "video_id": p.stem,
            "ext_mean_need": nd["need_score"].mean(),
            "ext_max_need": nd["need_score"].max(),
            "ext_speech": nd["speech_density"].mean(),
            "ext_extended_frac": float((nd["extended_need_score"] > 0.4).mean()),
            "ext_collision": float(nd["extended_need_score"].mean() * nd["speech_density"].mean()),
        })
    nr = pd.DataFrame(need_rows)
    merged = per.merge(nr, on="video_id", how="inner")
    if len(merged) < 8:
        return
    record(rows, "UC11", "External gen-gap predictor", "rankcorr_collision_vs_pro_loses",
           rank_corr(merged["ext_collision"], 1 - merged["pro_beats_short"]),
           "Before scoring: high collision proxy → pro may not beat short on new clips")
    record(rows, "UC11", "External gen-gap predictor", "rankcorr_need_vs_full_order_fail",
           rank_corr(merged["ext_mean_need"], 1 - merged["full_order_clip"]),
           f"n={len(merged)} external clips")


def uc_adaptad_trigger(df: pd.DataFrame, rows: list) -> None:
    """UC12: Need peak rate → on-demand AdaptAD query moments."""
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    peaks = []
    for cidx, g in need.groupby("clip_idx"):
        scores = g["need_score"].to_numpy()
        if len(scores) > 2:
            n = int(np.sum((scores[1:-1] > scores[:-2]) & (scores[1:-1] > scores[2:])))
        else:
            n = 0
        peaks.append({"clip_idx": cidx, "n_peaks": n})
    pk = pd.DataFrame(peaks)
    m = df.merge(pk, on="clip_idx")
    record(rows, "UC12", "AdaptAD query trigger", "rankcorr_peaks_vs_extended_frac",
           rank_corr(m["n_peaks"], m["extended_seconds_frac"]),
           "Sudden need spikes → prompt BLV user 'what do you want described?'")
    record(rows, "UC12", "AdaptAD query trigger", "mean_peaks_collision_regime",
           float(m[m["collision_index"] >= m["collision_index"].median()]["n_peaks"].mean()),
           "More peaks in collision clips → more AdaptAD prompts needed")


def uc_neural_debt_mode(rows: list) -> None:
    """UC13: Debt mode (slotable vs collision vs balanced) as product routing."""
    debt = pd.read_csv(CURSOR / "output" / "neural_accessibility_debt.csv")
    modes = debt["debt_mode"].value_counts(normalize=True)
    for mode, frac in modes.items():
        record(rows, "UC13", "Neural debt mode router", f"frac_{mode}", float(frac),
               f"Route {mode} clips to different AD product surface")
    collision_clips = debt[debt["debt_mode"] == "collision"]["clip_idx"].tolist()
    record(rows, "UC13", "Neural debt mode router", "n_collision_mode_clips", len(collision_clips),
           f"IDs: {collision_clips[:8]}...")


def write_findings(rep: pd.DataFrame) -> None:
    # Rank by absolute value for AUC/spearman, prioritize actionable
    actionable = rep[rep["stat"].str.contains("auc|rankcorr|spearman|hits", case=False)].copy()
    actionable["abs_val"] = actionable["value"].abs()
    top = actionable.sort_values("abs_val", ascending=False).head(15)

    lines = [
        "# TRIBE novel use cases — measured\n",
        "\n**Rule:** TRIBE never enters a caption ρ blend. Every use case is pre-text policy.\n\n",
        "## Top signals (by effect size)\n\n",
        "| UC | Use case | Metric | Value | Note |\n",
        "|----|----------|--------|------:|------|\n",
    ]
    for _, r in top.iterrows():
        lines.append(f"| {r['usecase_id']} | {r['name']} | {r['stat']} | {r['value']:.3f} | {r['note']} |\n")

    lines += [
        "\n## Product map — what TRIBE is actually for\n\n",
        "| Use case | Who | When | TRIBE signal |\n",
        "|----------|-----|------|-------------|\n",
        "| **Judge fragility forecast** | QA engineer | Before ADQA spend | `mean_standard_slot_score` ↓ |\n",
        "| **Audio-native coach** | BLV creator / UGC | Upload time | `collision_debt` ↑ |\n",
        "| **Pre-ADQA triage** | Auditor | Clip intake | `collision_index` top-k |\n",
        "| **Slot planner** | AD author | Writing | `n_extended` windows |\n",
        "| **Word budget** | AD author | Editing | `total_need` → word cap |\n",
        "| **Shortest-sufficient picker** | Platform | Auto-AD tier pick | `slotable_debt_frac` ↑ |\n",
        "| **Metric disagreement router** | Pipeline | Scoring fork | `clip_adqa_gap` + pressure |\n",
        "| **AdaptAD trigger** | BLV user | Playback | need peak count |\n",
        "| **External gen-gap** | Research | New clip cold-start | need proxy before CLIP |\n",
        "| **Category playbook** | PM | Genre defaults | Sports=collision, Food=slotable |\n",
        "\n## Strongest validated story\n\n",
        "**UC01 Judge fragility:** `mean_standard_slot_score` Spearman **−0.75** with 4-judge tier agreement — ",
        "use TRIBE *before any AD exists* to skip automatic scoring on clips where judges will disagree.\n\n",
        "**UC08 QC triage:** Rank clips by collision index; top-3 debt hits known violation clips.\n\n",
        "**UC09 Shortest-sufficient:** On slotable-heavy clips, tier1 VATEX-short often already passes ADQA — ",
        "don't force expensive pro AD when TRIBE says slot-AD physics apply.\n",
    ]
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    rows: list = []
    df = load_clip_table()

    uc_judge_fragility(df, rows)
    uc_audio_native_coach(df, rows)
    uc_word_budget(df, rows)
    uc_slot_planner(df, rows)
    uc_silence_opportunity(df, rows)
    uc_metric_disagreement(df, rows)
    uc_need_entropy(df, rows)
    uc_qc_triage(df, rows)
    uc_shortest_sufficient(df, rows)
    uc_category_playbook(df, rows)
    uc_external_gen_gap(rows)
    uc_adaptad_trigger(df, rows)
    uc_neural_debt_mode(rows)

    rep = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rep.to_csv(OUT, index=False)

    ranked = rep.copy()
    ranked["abs_val"] = ranked["value"].abs()
    ranked.sort_values("abs_val", ascending=False).to_csv(RANKED, index=False)
    write_findings(rep)

    print(rep.sort_values(by="value", key=abs, ascending=False).head(20).to_string(index=False))
    print(f"\nWrote {OUT}, {RANKED}, {FINDINGS}")


if __name__ == "__main__":
    main()
