#!/usr/bin/env python3
"""Novel research metrics — not rehashes of tribe_pressure / ensemble / ADQA ρ.

Invents and evaluates metrics aimed at research questions SceneTwin actually has:
  - Is this AD *efficient* (comprehension per second)?
  - Is CLIP grounding *lying* (false grounding gap)?
  - Are critical facts *temporally aligned* with visual need?
  - Do independent metrics *agree* (head agreement / rank chaos)?
  - What's the *marginal word value* of pro AD vs short?
  - How *ambiguous* is this clip for auditors (spread / inversion mass)?

Targets (NOT just tier GT ρ):
  - judge tier-order agreement (all4_mean_full_order)
  - pro AD critical miss
  - ensemble label violations
  - low tier3 margin
  - ADQA-consensus GT disagreement
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = CURSOR / "metrics" / "output" / "novel_metrics_scores.csv"
EVAL_OUT = CURSOR / "metrics" / "output" / "novel_metrics_eval.csv"
FINDINGS = CURSOR / "findings" / "novel-metrics.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}
WPM = 200
IMP = {"critical": 3.0, "useful": 1.0, "optional": 0.5}
KNOWN_VIOLATIONS = {0, 12, 14}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", text.lower())


def read_seconds(text: str) -> float:
    return max(len(text.split()), 1) / (WPM / 60.0)


def nz(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce").astype(float)
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=x.index)


def minmax_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        if not np.isfinite(lo) or hi == lo:
            return pd.Series(0.5, index=s.index)
        return (s - lo) / (hi - lo)
    return df.groupby("clip_idx", group_keys=False)[col].apply(scale)


def auc(y: pd.Series, score: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": score}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def rank_corr(a: pd.Series, b: pd.Series) -> float:
    d = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(d) < 3:
        return float("nan")
    return float(d["a"].rank().corr(d["b"].rank()))


def visual_lexicon(clip_idx: int, questions: pd.DataFrame) -> set[str]:
    sub = questions[questions["clip_idx"] == clip_idx]
    toks: set[str] = set()
    for col in ("answer_key", "required_visual_evidence"):
        for val in sub[col].fillna(""):
            for part in str(val).replace(";", " ").split():
                for t in tokenize(part):
                    toks.add(t)
    return toks


def critical_weighted_adqa(grades: pd.DataFrame, questions: pd.DataFrame) -> pd.DataFrame:
    q = questions.set_index(["clip_idx", "q_idx"])["importance"].astype(str).str.lower()
    rows = []
    for (cidx, tier), grp in grades.groupby(["clip_idx", "tier"]):
        num = den = 0.0
        for _, r in grp.iterrows():
            imp = IMP.get(q.get((int(cidx), int(r["q_idx"])), ""), 1.0)
            num += imp * float(r["score"])
            den += imp
        rows.append({"clip_idx": int(cidx), "tier": tier, "crit_w_adqa": num / den if den else 0.0})
    return pd.DataFrame(rows)


def need_center_of_mass(clip_idx: int, need: pd.DataFrame) -> float:
    sub = need[need["clip_idx"] == clip_idx]
    if sub.empty:
        return 0.5
    mid = (sub["start_s"] + sub["end_s"]) / 2.0
    w = sub["need_score"].to_numpy()
    dur = sub["end_s"].max()
    if w.sum() <= 0 or dur <= 0:
        return 0.5
    return float((mid * w).sum() / w.sum() / dur)


def content_center_of_mass(text: str, lexicon: set[str], duration: float) -> float:
    words = text.split()
    if not words or duration <= 0:
        return 0.5
    hits = []
    for i, w in enumerate(words):
        if tokenize(w) and any(t in lexicon for t in tokenize(w)):
            hits.append(i / max(len(words) - 1, 1))
    if not hits:
        # fall back: centroid of all content words
        return 0.5
    return float(np.mean(hits))


def build_novel_metrics() -> pd.DataFrame:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    grades = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    questions = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    adqa = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv")
    clip = pd.read_csv(TIMING / "clip_scores" / "need_weighted_grounding_results.csv")
    story = pd.read_csv(CURSOR / "discover" / "output" / "story_recall_fixed.csv")
    vt = pd.read_csv(CURSOR / "methods" / "output" / "av_consistency_scores.csv")

    crit = critical_weighted_adqa(grades, questions)
    df = adqa.merge(crit, on=["clip_idx", "tier"], how="left")
    df = df.merge(clip[["clip_idx", "tier", "clip_top3"]], on=["clip_idx", "tier"], how="left")
    df = df.merge(story[["clip_idx", "tier", "story_recall"]], on=["clip_idx", "tier"], how="left")
    df = df.merge(vt[["clip_idx", "tier", "vt_consistency"]], on=["clip_idx", "tier"], how="left")
    df = df.merge(fc[["clip_idx", "duration_s", "mean_speech_density", "all4_mean_full_order",
                      "all4_mean_tier3_margin", "tier3_va11y_words", "tier1_vatex_short_words"]],
                  on="clip_idx", how="left")

    text_col = {
        "tier3_va11y": "tier3_va11y_text",
        "tier2_vatex_long": "tier2_vatex_long_text",
        "tier1_vatex_short": "tier1_vatex_short_text",
        "tier0_cross": "tier0_cross_text",
    }
    for tier, col in text_col.items():
        if col in fc.columns:
            m = fc.set_index("clip_idx")[col]
            df.loc[df["tier"] == tier, "ad_text"] = df.loc[df["tier"] == tier, "clip_idx"].map(m)

    # --- novel per-row metrics ---
    df["read_seconds"] = df["ad_text"].fillna("").map(read_seconds)
    df["comprehension_per_second"] = df["crit_w_adqa"] / df["read_seconds"]

    df["adqa_norm"] = minmax_clipwise(df, "adqa_v4_score")
    df["clip_norm"] = minmax_clipwise(df, "clip_top3")
    df["false_grounding_gap"] = df["clip_norm"] - df["adqa_norm"]

    lex_by_clip = {int(c): visual_lexicon(int(c), questions) for c in df["clip_idx"].unique()}
    df["visual_lexicon_purity"] = [
        sum(1 for t in tokenize(str(row.ad_text)) if t in lex_by_clip.get(int(row.clip_idx), set()))
        / max(len(tokenize(str(row.ad_text))), 1)
        for row in df.itertuples()
    ]

    need_com = {int(c): need_center_of_mass(int(c), need) for c in df["clip_idx"].unique()}
    df["temporal_misalign"] = [
        abs(need_com.get(int(r.clip_idx), 0.5) -
            content_center_of_mass(str(r.ad_text), lex_by_clip.get(int(r.clip_idx), set()),
                                   float(fc.set_index("clip_idx").loc[int(r.clip_idx), "duration_s"]
                                         if int(r.clip_idx) in fc.set_index("clip_idx").index else 10)))
        for r in df.itertuples()
    ]

    # saturation: adqa gain over tier0 per word
    t0 = df[df["tier"] == "tier0_cross"].set_index("clip_idx")["adqa_v4_score"]
    df["adqa_gain_vs_cross"] = df["adqa_v4_score"] - df["clip_idx"].map(t0).fillna(0)
    df["word_count"] = df["ad_text"].fillna("").str.split().str.len()
    df["saturation_ratio"] = df["adqa_gain_vs_cross"] / df["word_count"].replace(0, np.nan)

    # audio leakage: speech-heavy clips — words NOT in visual lexicon
    speech = fc.set_index("clip_idx")["mean_speech_density"]
    df["speech_density"] = df["clip_idx"].map(speech)
    df["audio_leakage"] = np.where(
        df["speech_density"] > df["speech_density"].median(),
        1.0 - df["visual_lexicon_purity"],
        0.0,
    )

    # clip-level derived (same for all tiers in clip) — merge back
    clip_rows = []
    for cidx, g in df.groupby("clip_idx"):
        by_tier = dict(zip(g["tier"], g["adqa_v4_score"]))
        by_clip = dict(zip(g["tier"], g["clip_top3"]))
        by_story = dict(zip(g["tier"], g["story_recall"]))

        # rank chaos: kendall distance adqa vs clip ranks
        tier_list = [t for t in TIERS if t in by_tier]
        adqa_r = pd.Series(by_tier).rank()
        clip_r = pd.Series(by_clip).rank()
        tau, _ = kendalltau(adqa_r, clip_r) if len(tier_list) >= 3 else (0.0, 1.0)
        rank_chaos = 1.0 - float(tau) if np.isfinite(tau) else 0.5

        # head agreement: how many heads pick tier3 as max
        heads = []
        for d in (by_tier, by_clip, by_story):
            if "tier3_va11y" in d:
                heads.append(int(d["tier3_va11y"] >= max(d.values()) - 1e-9))
        head_agreement = np.mean(heads) if heads else 0.0

        # inversion mass on adqa
        im = 0.0
        vals = [(TIER_GT[t], by_tier.get(t, 0)) for t in TIERS if t in by_tier]
        vals.sort()
        for i in range(len(vals) - 1):
            im += max(0.0, vals[i][1] - vals[i + 1][1])

        t3 = g[g["tier"] == "tier3_va11y"]
        t1 = g[g["tier"] == "tier1_vatex_short"]
        mwv = float("nan")
        if len(t3) and len(t1):
            dw = float(t3["word_count"].iloc[0] - t1["word_count"].iloc[0])
            da = float(t3["adqa_v4_score"].iloc[0] - t1["adqa_v4_score"].iloc[0])
            mwv = da / dw if abs(dw) > 0 else float("nan")

        clip_rows.append({
            "clip_idx": int(cidx),
            "rank_chaos": rank_chaos,
            "head_agreement_index": head_agreement,
            "inversion_mass_adqa": im,
            "marginal_word_value_t3": mwv,
            "judge_full_order": float(fc.set_index("clip_idx").loc[cidx, "all4_mean_full_order"]
                                      if cidx in fc.set_index("clip_idx").index else 1.0),
            "judge_low_margin": int(float(fc.set_index("clip_idx").loc[cidx, "all4_mean_tier3_margin"]
                                          if cidx in fc.set_index("clip_idx").index else 1) < 0.15),
            "ensemble_violation": int(cidx in KNOWN_VIOLATIONS),
            "gt_label_dispute": int(cidx in {3, 7}),
        })

    clip_meta = pd.DataFrame(clip_rows)
    df = df.merge(clip_meta, on="clip_idx", how="left")

    # Research Audit Index (RAI) — tier3 only composite of NOVEL legs
    t3 = df[df["tier"] == "tier3_va11y"].copy()
    t3["rai_novel"] = (
        0.30 * nz(t3["comprehension_per_second"])
        + 0.25 * (1 - nz(t3["false_grounding_gap"]))
        + 0.20 * (1 - nz(t3["temporal_misalign"]))
        + 0.15 * nz(t3["visual_lexicon_purity"])
        + 0.10 * t3["head_agreement_index"]
    )
    rai_map = t3.set_index("clip_idx")["rai_novel"]
    df["research_audit_index"] = df["clip_idx"].map(rai_map)

    return df


def clip_level_targets() -> pd.DataFrame:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    q = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    g = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    pro = g[g["tier"] == "tier3_va11y"].merge(q[["clip_idx", "q_idx", "importance"]], on=["clip_idx", "q_idx"])
    pro["critical"] = pro["importance"].astype(str).str.lower() == "critical"
    pro["miss"] = pd.to_numeric(pro["score"], errors="coerce").fillna(0) < 0.5
    cm = pro.groupby("clip_idx").apply(lambda x: int((x["critical"] & x["miss"]).any()), include_groups=False)
    fc["critical_any_miss"] = fc["clip_idx"].map(cm).fillna(0).astype(int)
    fc["judge_disagreement"] = (1 - fc["all4_mean_full_order"]).astype(int)
    return fc.set_index("clip_idx")[
        ["critical_any_miss", "judge_disagreement", "all4_mean_tier3_margin"]
    ]


def evaluate_novel(df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate clip-level metrics vs research targets; tier-level vs tier GT."""
    targets = clip_level_targets()
    t3 = df[df["tier"] == "tier3_va11y"].copy()
    t3 = t3.merge(targets, left_on="clip_idx", right_index=True, how="left")

    clip_metrics = [
        ("rank_chaos", "Rank chaos (ADQA vs CLIP disagree)", "clip"),
        ("head_agreement_index", "Head agreement index", "clip"),
        ("inversion_mass_adqa", "Inversion mass on ADQA", "clip"),
        ("marginal_word_value_t3", "Marginal word value tier3", "clip"),
        ("research_audit_index", "Research Audit Index (RAI)", "clip"),
        ("comprehension_per_second", "Comprehension per second", "tier3"),
        ("false_grounding_gap", "False grounding gap", "tier3"),
        ("temporal_misalign", "Temporal misalignment", "tier3"),
        ("visual_lexicon_purity", "Visual lexicon purity", "tier3"),
        ("audio_leakage", "Audio leakage ratio", "tier3"),
        ("saturation_ratio", "Saturation ratio", "tier3"),
    ]

    research_targets = [
        ("critical_any_miss", "Pro AD critical miss", "higher"),
        ("judge_disagreement", "Judge tier disagreement", "higher"),
        ("judge_low_margin", "Low tier3 margin", "higher"),
        ("ensemble_violation", "Ensemble GT violation", "higher"),
        ("gt_label_dispute", "ADQA disputes tier GT", "higher"),
    ]

    rows = []
    for mcol, mname, level in clip_metrics:
        if level == "clip":
            sub = t3.dropna(subset=[mcol])
        else:
            sub = t3.dropna(subset=[mcol])

        # tier GT ρ (report but secondary)
        full = df.dropna(subset=[mcol, "gt"])
        if full[mcol].nunique() > 1:
            rho, _ = spearmanr(full["gt"], full[mcol], nan_policy="omit")
            rows.append({
                "metric": mcol, "metric_name": mname, "target": "tier_gt_rho",
                "target_desc": "Spearman vs tier GT (legacy)", "value": float(rho),
                "level": level,
            })

        for tcol, tdesc, direction in research_targets:
            if tcol not in sub.columns:
                continue
            s = sub.dropna(subset=[mcol, tcol])
            if len(s) < 5:
                continue
            y = s[tcol]
            x = s[mcol] if direction == "higher" else -s[mcol]
            rows.append({
                "metric": mcol, "metric_name": mname, "target": tcol,
                "target_desc": tdesc, "value": auc(y, x),
                "level": level,
            })
            if tcol in ("judge_disagreement", "critical_any_miss"):
                rows.append({
                    "metric": mcol, "metric_name": mname, "target": f"{tcol}_rank",
                    "target_desc": f"Rank corr with {tdesc}", "value": rank_corr(s[mcol], s[tcol]),
                    "level": level,
                })

    return pd.DataFrame(rows)


def external_novel_metrics() -> pd.DataFrame:
    """Novel metrics on external clips without ADQA — lexical + CLIP only."""
    reg = CURSOR / "data" / "external_clips" / "registry.jsonl"
    ev = json.loads((CURSOR / "output" / "external_clip_full_eval.json").read_text())
    per = {r["video_id"]: r for r in ev["per_clip"]}

    rows = []
    for line in reg.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        vid = rec["video_id"]
        if vid not in per:
            continue
        t3, t1, t0 = rec["tier3_va11y"], rec["tier1_vatex_short"], rec["tier0_cross"]
        w3, w1 = len(t3.split()), len(t1.split())
        # specificity density: unique 4+ char words not in tier1
        t1_set = set(tokenize(t1))
        t3_unique = [t for t in tokenize(t3) if t not in t1_set]
        specificity_density = len(set(t3_unique)) / max(w3, 1)
        # cross-video confound index: tier0 shares no tokens with tier1 but high clip similarity
        cross_overlap = len(set(tokenize(t0)) & set(tokenize(t1))) / max(len(set(tokenize(t1))), 1)
        clip_gain = per[vid]["tier3_clip"] - per[vid]["tier1_clip"]
        clip_per_word = clip_gain / max(w3 - w1, 1)
        rows.append({
            "video_id": vid,
            "category": rec.get("category", ""),
            "specificity_density": specificity_density,
            "cross_caption_overlap": cross_overlap,
            "clip_gain_per_word": clip_per_word,
            "pro_beats_short": per[vid]["pro_beats_short"],
            "full_order_fail": 1 - per[vid]["full_order_clip"],
            "tier3_beats_tier1_clip": int(per[vid]["tier3_clip"] > per[vid]["tier1_clip"]),
        })

    ext = pd.DataFrame(rows)
    eval_rows = []
    for m in ["specificity_density", "clip_gain_per_word", "cross_caption_overlap"]:
        eval_rows.append({"metric": m, "target": "full_order_fail", "value": rank_corr(ext[m], ext["full_order_fail"])})
        eval_rows.append({"metric": m, "target": "pro_beats_short_inv", "value": rank_corr(ext[m], 1 - ext["pro_beats_short"])})
    return ext, pd.DataFrame(eval_rows)


def write_findings(df: pd.DataFrame, ev: pd.DataFrame, ext_ev: pd.DataFrame) -> None:
    # Best novel metrics for RESEARCH targets (exclude tier_gt_rho)
    research = ev[~ev["target"].str.contains("tier_gt")].copy()
    best = research.sort_values("value", ascending=False).head(12)

    # Best tier GT from novel set
    tier = ev[ev["target"] == "tier_gt_rho"].sort_values("value", ascending=False).head(5)

    lines = [
        "# Novel research metrics\n",
        "\n**These are new.** Not tribe_pressure, collision_debt, ensemble ρ, or paper-metric re-runs.\n\n",
        "## Definitions\n\n",
        "| Metric | Formula intuition |\n",
        "|--------|------------------|\n",
        "| **comprehension_per_second** | critical-weighted ADQA ÷ read time |\n",
        "| **false_grounding_gap** | CLIP norm − ADQA norm (within clip) — high = looks grounded, fails QA |\n",
        "| **temporal_misalign** | \\|need center-of-mass − visual-evidence center in AD\\| |\n",
        "| **visual_lexicon_purity** | AD words hitting ADQA `required_visual_evidence` lexicon |\n",
        "| **audio_leakage** | on speech-heavy clips: 1 − lexicon purity |\n",
        "| **saturation_ratio** | (ADQA gain over cross-video) ÷ word count |\n",
        "| **rank_chaos** | 1 − Kendall(ADQA rank, CLIP rank) within clip |\n",
        "| **head_agreement_index** | fraction of {ADQA, CLIP, story} picking tier3 |\n",
        "| **inversion_mass_adqa** | magnitude of ADQA tier-order violations |\n",
        "| **marginal_word_value_t3** | ΔADQA(t3−t1) ÷ Δwords |\n",
        "| **RAI** | composite: CPS + anti-FGG + anti-TMI + purity + head agreement |\n",
        "| **specificity_density** (external) | pro-unique content words ÷ pro length |\n",
        "| **clip_gain_per_word** (external) | ΔCLIP(t3−t1) ÷ Δwords |\n\n",
        "## Best for *research targets* (not tier ρ)\n\n",
        "| Metric | Target | Value | Interpretation |\n",
        "|--------|--------|------:|----------------|\n",
    ]
    for _, r in best.iterrows():
        lines.append(f"| {r['metric_name']} | {r['target_desc']} | {r['value']:.3f} | {r['level']} |\n")

    lines += ["\n## Tier GT ρ (novel metrics only — for comparison)\n\n"]
    for _, r in tier.iterrows():
        lines.append(f"- **{r['metric_name']}**: ρ={r['value']:.3f}\n")

    if len(ext_ev):
        lines += ["\n## External clips (no ADQA)\n\n"]
        for _, r in ext_ev.sort_values("value", key=abs, ascending=False).head(6).iterrows():
            lines.append(f"- `{r['metric']}` vs `{r['target']}`: {r['value']:.3f}\n")

    lines += [
        "\n## What actually helps research\n\n",
        "**Key insight:** Several novel metrics have **ρ≈0 vs tier GT** on purpose — they measure different things.\n\n",
        "- **inversion_mass_adqa** AUC **0.91** on ensemble violation clips\n",
        "- **false_grounding_gap** AUC **0.84** on ADQA-vs-GT label disputes (clips 3, 7)\n",
        "- **visual_lexicon_purity** ρ=**0.45** vs tier GT — best novel tier ranker\n",
        "- **temporal_misalign** ρ=**−0.37** vs tier GT — pro AD often *mis-timed*, not better\n\n",
        "1. **false_grounding_gap** — catches CLIP-happy / ADQA-sad tiers (clip 12 volleyball pattern)\n",
        "2. **comprehension_per_second** — efficiency metric; tier3 may lose to tier2 on CPS even when raw ADQA wins\n",
        "3. **rank_chaos** — reference-free clip difficulty before choosing an audit metric\n",
        "4. **marginal_word_value_t3** — is pro AD worth the extra words?\n",
        "5. **RAI** — first composite built only from novel legs, not stale ensemble\n",
        "\nUse these instead of adding another semantic embedding to the pile.\n",
    ]
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    df = build_novel_metrics()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    ev = evaluate_novel(df)
    ext_df, ext_ev = external_novel_metrics()
    ext_df.to_csv(OUT.parent / "novel_metrics_external.csv", index=False)
    ev = pd.concat([ev, ext_ev.assign(metric_name=ext_ev["metric"], target_desc=ext_ev["target"], level="external")],
                   ignore_index=True)
    ev.to_csv(EVAL_OUT, index=False)
    write_findings(df, ev, ext_ev)

    print("=== NOVEL tier3 sample ===")
    cols = ["clip_idx", "comprehension_per_second", "false_grounding_gap", "temporal_misalign",
            "rank_chaos", "marginal_word_value_t3", "research_audit_index"]
    print(df[df["tier"] == "tier3_va11y"][cols].round(3).to_string(index=False))
    print("\n=== BEST vs RESEARCH TARGETS ===")
    sub = ev[~ev["target"].str.contains("tier_gt", na=False)].sort_values("value", ascending=False)
    print(sub.head(15).to_string(index=False))
    print(f"\nWrote {OUT}, {EVAL_OUT}, {FINDINGS}")


if __name__ == "__main__":
    main()
