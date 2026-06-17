#!/usr/bin/env python3
"""Metric discovery engine — every run invents NEW formulas, never repeats.

Reads base signals once, combinatorially generates fresh metrics per iteration,
evaluates vs research targets (not just tier ρ), logs to discovery_registry.jsonl.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
METRICS = Path(__file__).resolve().parent
REGISTRY = METRICS / "discovery_registry.jsonl"
LEADERBOARD = METRICS / "output" / "discovery_leaderboard.csv"
FINDINGS = CURSOR / "findings" / "metric-discovery-log.md"
DISCOVERIES = CURSOR / "findings" / "auto-discoveries.md"
STATE = METRICS / ".discovery.state.json"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}
KNOWN_VIOLATIONS = {0, 12, 14}
WPM = 200
IMP = {"critical": 3.0, "useful": 1.0, "optional": 0.5}

# Already measured — never rediscover these exact recipes
BANNED_SIGNATURES = {
    "ensemble_w50", "tribe_pressure", "collision_debt", "collision_index",
    "llm_ad_eval", "metric_leaderboard", "bootstrap", "weight_sweep",
    "comprehension_per_second", "false_grounding_gap", "inversion_mass_adqa",
    "rank_chaos", "research_audit_index", "mean_standard_slot_score",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sig(recipe: str) -> str:
    return hashlib.sha256(recipe.encode()).hexdigest()[:16]


def load_registry() -> set[str]:
    seen = set(BANNED_SIGNATURES)
    if REGISTRY.exists():
        for line in REGISTRY.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                seen.add(row.get("signature", row.get("recipe", "")))
                seen.add(row.get("recipe", ""))
    return seen


def append_registry(row: dict) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def append_discovery(msg: str) -> None:
    DISCOVERIES.parent.mkdir(parents=True, exist_ok=True)
    with DISCOVERIES.open("a", encoding="utf-8") as f:
        f.write(f"- [{utc_now()}] {msg}\n")


def auc(y: pd.Series, score: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": score}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def minmax_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        if not np.isfinite(lo) or hi == lo:
            return pd.Series(0.5, index=s.index)
        return (s - lo) / (hi - lo)
    return df.groupby("clip_idx", group_keys=False)[col].apply(scale)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", str(text).lower())


def build_base_frame() -> pd.DataFrame:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    adqa = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv")
    clip = pd.read_csv(TIMING / "clip_scores" / "need_weighted_grounding_results.csv")
    grades = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    questions = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    story_p = CURSOR / "discover" / "output" / "story_recall_fixed.csv"
    vt_p = CURSOR / "methods" / "output" / "av_consistency_scores.csv"
    story = pd.read_csv(story_p) if story_p.exists() else pd.DataFrame()
    vt = pd.read_csv(vt_p) if vt_p.exists() else pd.DataFrame()

    imp = { (int(r.clip_idx), int(r.q_idx)): IMP.get(str(r.importance).lower(), 1.0)
            for _, r in questions.iterrows() }
    crit_rows = []
    for (cidx, tier), grp in grades.groupby(["clip_idx", "tier"]):
        num = den = 0.0
        for _, r in grp.iterrows():
            w = imp.get((int(cidx), int(r.q_idx)), 1.0)
            num += w * float(r["score"])
            den += w
        crit_rows.append({"clip_idx": int(cidx), "tier": tier, "crit_w": num / den if den else 0.0})
    crit = pd.DataFrame(crit_rows)

    df = adqa.merge(clip, on=["clip_idx", "tier", "gt"], how="inner", suffixes=("", "_clip"))
    df = df.merge(crit, on=["clip_idx", "tier"], how="left")
    if not story.empty:
        df = df.merge(story[["clip_idx", "tier", "story_recall"]], on=["clip_idx", "tier"], how="left")
    if not vt.empty:
        df = df.merge(vt[["clip_idx", "tier", "vt_consistency"]], on=["clip_idx", "tier"], how="left")

    text_cols = {"tier3_va11y": "tier3_va11y_text", "tier1_vatex_short": "tier1_vatex_short_text",
                 "tier2_vatex_long": "tier2_vatex_long_text", "tier0_cross": "tier0_cross_text"}
    for tier, col in text_cols.items():
        if col in fc.columns:
            m = fc.set_index("clip_idx")[col]
            df.loc[df["tier"] == tier, "ad_text"] = df.loc[df["tier"] == tier, "clip_idx"].map(m)

    df["words"] = df["ad_text"].fillna("").str.split().str.len()
    df["read_s"] = df["words"].clip(lower=1) / (WPM / 60.0)

    need_agg = need.groupby("clip_idx").agg(
        need_std=("need_score", "std"),
        need_max=("need_score", "max"),
        need_mean=("need_score", "mean"),
        n_ext=("recommendation", lambda s: int(s.astype(str).str.contains("extended", na=False).sum())),
        speech_mean=("speech_density", "mean"),
    ).reset_index()

    fc_slim = fc[["clip_idx", "duration_s", "tribe_pressure", "extended_seconds_frac",
                  "mean_speech_density", "all4_mean_full_order", "all4_mean_tier3_margin"]].copy()
    df = df.merge(need_agg, on="clip_idx", how="left").merge(fc_slim, on="clip_idx", how="left")

    t0 = df[df["tier"] == "tier0_cross"].set_index("clip_idx")["adqa_v4_score"]
    df["gain_vs_cross"] = df["adqa_v4_score"] - df["clip_idx"].map(t0).fillna(0)
    df["clip_norm"] = minmax_clipwise(df, "clip_top3")
    df["adqa_norm"] = minmax_clipwise(df, "adqa_v4_score")

    for col in ("adqa_v4_score", "clip_top3", "crit_w", "gain_vs_cross"):
        g = df.groupby("clip_idx")[col]
        df[f"{col}_spread"] = df["clip_idx"].map(g.max() - g.min())
        df[f"{col}_std"] = df["clip_idx"].map(g.std()).fillna(0)

    # need timing: peak position vs clip midpoint
    need_peaks = []
    for cidx, grp in need.groupby("clip_idx"):
        w = grp.sort_values("start_s")
        if w.empty:
            need_peaks.append({"clip_idx": cidx, "need_peak_t": 0.5, "need_skew": 0.0})
            continue
        scores = w["need_score"].astype(float).values
        t = w["start_s"].astype(float).values
        if scores.sum() <= 0:
            need_peaks.append({"clip_idx": cidx, "need_peak_t": 0.5, "need_skew": 0.0})
            continue
        com = float(np.average(t, weights=scores + 1e-6))
        dur = float(w["end_s"].max() - w["start_s"].min() + 1e-6)
        skew = float(np.mean((scores - scores.mean()) ** 3) / (scores.std() + 1e-6))
        need_peaks.append({"clip_idx": cidx, "need_peak_t": com / dur, "need_skew": skew})
    df = df.merge(pd.DataFrame(need_peaks), on="clip_idx", how="left")

    # lexical: fraction of AD tokens that appear in clip QA lexicon
    lex_by_clip = {}
    for cidx, qg in questions.groupby("clip_idx"):
        lex = set()
        for t in qg["question"].fillna("").astype(str):
            lex.update(tokenize(t))
        for t in qg.get("answer_key", pd.Series(dtype=str)).fillna("").astype(str):
            lex.update(tokenize(t))
        lex_by_clip[int(cidx)] = lex

    def lex_purity(row) -> float:
        toks = tokenize(str(row.get("ad_text", "")))
        if not toks:
            return 0.0
        lex = lex_by_clip.get(int(row["clip_idx"]), set())
        if not lex:
            return 0.0
        return sum(1 for t in toks if t in lex) / len(toks)

    df["lex_purity"] = df.apply(lex_purity, axis=1)
    df["tier_idx"] = df["tier"].map(TIER_GT).astype(float)

    t3_adqa = df[df["tier"] == "tier3_va11y"].set_index("clip_idx")["adqa_v4_score"]
    t0_adqa = df[df["tier"] == "tier0_cross"].set_index("clip_idx")["adqa_v4_score"]
    df["adqa_t3_minus_t0"] = df["clip_idx"].map(t3_adqa) - df["clip_idx"].map(t0_adqa)
    df["adqa_inversion"] = (df["adqa_t3_minus_t0"] < 0).astype(float)

    # clip-level targets (tier3 row carries them)
    q = questions
    pro = grades[grades["tier"] == "tier3_va11y"].merge(q[["clip_idx", "q_idx", "importance"]], on=["clip_idx", "q_idx"])
    pro["critical"] = pro["importance"].astype(str).str.lower() == "critical"
    pro["miss"] = pd.to_numeric(pro["score"], errors="coerce").fillna(0) < 0.5
    cm = pro.groupby("clip_idx").apply(lambda x: int((x["critical"] & x["miss"]).any()), include_groups=False)
    targets = fc_slim.set_index("clip_idx").copy()
    targets["critical_miss"] = targets.index.map(cm).fillna(0).astype(int)
    targets["ensemble_violation"] = targets.index.isin(KNOWN_VIOLATIONS).astype(int)
    targets["judge_disagree"] = (1 - fc.set_index("clip_idx")["all4_mean_full_order"]).astype(int)
    targets["gt_dispute"] = targets.index.isin({3, 7}).astype(int)
    targets["low_margin"] = (fc.set_index("clip_idx")["all4_mean_tier3_margin"] < 0.15).astype(int)

    df = df.merge(targets, left_on="clip_idx", right_index=True, how="left", suffixes=("", "_tgt"))
    return df


def _shuffle_batch(ops: list[tuple[str, str]], iteration: int, batch_size: int) -> list[tuple[str, str]]:
    rng = np.random.default_rng(10000 + iteration)
    if not ops:
        return []
    idx = rng.permutation(len(ops))
    start = (iteration * batch_size) % len(ops)
    chosen = []
    for i in range(len(ops)):
        j = idx[(start + i) % len(idx)]
        chosen.append(ops[j])
        if len(chosen) >= batch_size * 3:
            break
    return chosen


def _tier_spread_family(cols: list[str]) -> list[tuple[str, str]]:
    ops = []
    for c in cols:
        ops.append((f"spread_x_need({c})", f"{c}_spread * need_mean"))
        ops.append((f"spread_over_read({c})", f"{c}_spread / (read_s + 0.01)"))
    for a, b in combinations(cols, 2):
        ops.append((f"spread_diff({a},{b})", f"({a}_spread) - ({b}_spread)"))
        ops.append((f"std_ratio({a},{b})", f"({a}_std) / ({b}_std + 1e-6)"))
    return ops


def _temporal_family() -> list[tuple[str, str]]:
    return [
        ("need_peak_x_adqa", "need_peak_t * adqa_v4_score"),
        ("need_skew_x_clip", "need_skew * clip_norm"),
        ("peak_minus_lex", "need_peak_t - lex_purity"),
        ("skew_per_ext", "need_skew / (n_ext + 1)"),
        ("peak_x_inversion", "need_peak_t * adqa_inversion"),
        ("com_x_tribe", "need_peak_t * tribe_pressure"),
        ("skew_x_crit_spread", "need_skew * crit_w_spread"),
        ("peak_over_words", "need_peak_t / (words + 1)"),
    ]


def _lexical_family() -> list[tuple[str, str]]:
    return [
        ("lex_x_adqa", "lex_purity * adqa_v4_score"),
        ("lex_minus_clip", "lex_purity - clip_norm"),
        ("lex_per_need", "lex_purity / (need_mean + 0.01)"),
        ("words_x_lex", "words * lex_purity"),
        ("lex_x_gain", "lex_purity * gain_vs_cross"),
        ("lex_spread_proxy", "lex_purity * adqa_v4_score_spread"),
        ("read_minus_lex", "read_s - lex_purity"),
        ("lex_x_vt", "lex_purity * vt_consistency"),
    ]


def _rank_instability_family() -> list[tuple[str, str]]:
    return [
        ("t3_adqa_minus_clip", "adqa_t3_minus_t0 - (clip_norm - adqa_norm)"),
        ("tier3_clip_diverge", "tier_idx * (clip_norm - adqa_norm)"),
        ("inversion_x_spread", "adqa_inversion * adqa_v4_score_spread"),
        ("gain_x_tier", "gain_vs_cross * tier_idx"),
        ("crit_slope", "crit_w * tier_idx"),
        ("story_tier_gap", "(story_recall - adqa_norm) * tier_idx"),
        ("adqa_slope", "adqa_v4_score * tier_idx"),
        ("clip_spread_x_tier", "clip_top3_spread * tier_idx"),
    ]


def _mutate_registry(iteration: int) -> list[tuple[str, str]]:
    if not REGISTRY.exists():
        return []
    rows = [json.loads(l) for l in REGISTRY.read_text().splitlines() if l.strip()]
    if not rows:
        return []
    rep = pd.DataFrame(rows).sort_values("best_value", ascending=False)
    muts = []
    transforms = [
        ("inv", "1.0 / (abs({}) + 0.01)"),
        ("log", "log1p(abs({}))"),
        ("need_scale", "({}) * need_mean"),
        ("ext_scale", "({}) * extended_seconds_frac"),
        ("tier_scale", "({}) * tier_idx"),
    ]
    for _, r in rep.head(5).iterrows():
        base_expr = str(r["recipe"])
        base_name = str(r["name"])[:30]
        for tag, tpl in transforms:
            muts.append((f"mut_{tag}_{base_name}", tpl.format(base_expr)))
    rng = np.random.default_rng(20000 + iteration)
    idx = rng.permutation(len(muts))
    return [muts[i] for i in idx[:12]]


def _combinatorial_family() -> list[tuple[str, str]]:
    cols = [
        "adqa_v4_score", "crit_w", "clip_top3", "clip_mean", "need_weighted_clip",
        "story_recall", "vt_consistency", "words", "read_s", "gain_vs_cross",
        "clip_norm", "adqa_norm", "need_std", "need_max", "need_mean", "n_ext",
        "speech_mean", "tribe_pressure", "extended_seconds_frac",
        "need_peak_t", "need_skew", "lex_purity", "adqa_t3_minus_t0",
    ]
    ops = []
    for a, b in combinations(cols, 2):
        ops.append((f"ratio({a},{b})", f"({a}) / ({b} + 1e-6)"))
        ops.append((f"product({a},{b})", f"({a}) * ({b})"))
        ops.append((f"diff({a},{b})", f"({a}) - ({b})"))
    for c in cols:
        ops.append((f"log1p({c})", f"log1p(abs({c}))"))
        ops.append((f"sqrt({c})", f"sqrt(abs({c}))"))
        ops.append((f"sq({c})", f"({c}) ** 2"))
    ops.extend([
        ("blend_adqa_clip_need", "0.4*adqa_norm + 0.35*clip_norm + 0.25*need_weighted_clip"),
        ("efficiency_crit", "crit_w / read_s"),
        ("grounding_minus_qa", "clip_norm - adqa_norm"),
        ("qa_per_need", "adqa_v4_score / (need_mean + 0.01)"),
        ("crit_per_ext", "crit_w / (n_ext + 1)"),
        ("story_clip_gap", "story_recall - clip_norm"),
        ("vt_adqa_harmonic", "2*vt_consistency*adqa_v4_score / (vt_consistency + adqa_v4_score + 1e-6)"),
        ("words_per_gain", "words / (gain_vs_cross + 0.01)"),
        ("pressure_x_speech", "tribe_pressure * speech_mean"),
        ("ext_frac_x_crit", "extended_seconds_frac * crit_w"),
        ("need_std_x_adqa", "need_std * adqa_v4_score"),
        ("clip_per_word", "clip_top3 / (words + 1)"),
        ("tier_spread_proxy", "adqa_v4_score - clip_top3"),
    ])
    return ops


def recipe_candidates(iteration: int) -> list[tuple[str, str]]:
    """Rotate recipe family each iteration so we never exhaust the same search space."""
    batch_size = 8
    spread_cols = ["adqa_v4_score", "clip_top3", "crit_w", "gain_vs_cross"]
    phase = iteration % 7
    if phase == 0:
        return _shuffle_batch(_tier_spread_family(spread_cols), iteration, batch_size)
    if phase == 1:
        return _shuffle_batch(_temporal_family(), iteration, batch_size)
    if phase == 2:
        return _shuffle_batch(_lexical_family(), iteration, batch_size)
    if phase == 3:
        muts = _mutate_registry(iteration)
        if muts:
            return _shuffle_batch(muts, iteration, batch_size)
    if phase == 4:
        return _shuffle_batch(_rank_instability_family(), iteration, batch_size)
    if phase == 5:
        cond = [
            ("cond_clip_adqa", "clip_norm - adqa_norm + 0.1 * adqa_inversion"),
            ("cond_need_pressure", "need_mean * tribe_pressure / (speech_mean + 0.01)"),
            ("cond_ext_crit", "extended_seconds_frac - crit_w / (need_max + 0.01)"),
            ("cond_story_need", "story_recall / (need_peak_t + 0.01)"),
            ("cond_vt_spread", "vt_consistency * adqa_v4_score_spread"),
            ("cond_lex_inversion", "lex_purity * (1 - adqa_inversion)"),
        ]
        return _shuffle_batch(cond, iteration, batch_size)
    return _shuffle_batch(_combinatorial_family(), iteration, batch_size)


def eval_recipe(df: pd.DataFrame, name: str, expr: str) -> pd.Series | None:
    local = {c: df[c].astype(float) for c in df.columns if pd.api.types.is_numeric_dtype(df[c])}
    try:
        val = eval(expr, {"__builtins__": {}, "log1p": np.log1p, "sqrt": np.sqrt, "abs": np.abs}, local)
        s = pd.Series(val, index=df.index, dtype=float)
        if not np.isfinite(s).any() or s.nunique() <= 1:
            return None
        return s
    except Exception:
        return None


def evaluate_metric(df: pd.DataFrame, col: str) -> dict:
    t3 = df[df["tier"] == "tier3_va11y"].dropna(subset=[col])
    out = {"metric_col": col}
    if len(df.dropna(subset=[col, "gt"])) >= 8 and df[col].nunique() > 1:
        rho, _ = spearmanr(df["gt"], df[col], nan_policy="omit")
        out["tier_gt_rho"] = float(rho)
    for target, tcol in [
        ("ensemble_violation", "ensemble_violation"),
        ("critical_miss", "critical_miss"),
        ("judge_disagree", "judge_disagree"),
        ("gt_dispute", "gt_dispute"),
        ("low_margin", "low_margin"),
    ]:
        if tcol in t3.columns and t3[tcol].nunique() > 1:
            out[f"auc_{target}"] = auc(t3[tcol], t3[col])
    return out


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"iteration": 0, "total_discovered": 0}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def refresh_leaderboard() -> None:
    if not REGISTRY.exists():
        return
    rows = [json.loads(l) for l in REGISTRY.read_text().splitlines() if l.strip()]
    if not rows:
        return
    rep = pd.DataFrame(rows)
    score_col = "best_value"
    if score_col in rep.columns:
        rep = rep.sort_values(score_col, ascending=False)
    rep.to_csv(LEADERBOARD, index=False)

    top = rep.head(15)
    lines = ["# Metric discovery leaderboard\n", f"Updated {utc_now()}. Total recipes tried: **{len(rows)}**\n\n",
             "| iteration | recipe | best target | value | tier ρ |\n",
             "|-----------|--------|-------------|------:|-------:|\n"]
    for _, r in top.iterrows():
        lines.append(
            f"| {r.get('iteration','')} | `{r.get('recipe','')[:50]}` | {r.get('best_target','')} | "
            f"{r.get('best_value', float('nan')):.3f} | {r.get('tier_gt_rho', float('nan')):.3f} |\n"
        )
    FINDINGS.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    state = load_state()
    state["iteration"] = int(state.get("iteration", 0)) + 1
    iteration = state["iteration"]
    seen = load_registry()

    df = build_base_frame()
    phase = iteration % 7
    phase_names = ["tier_spread", "temporal", "lexical", "mutations", "rank_instability", "conditional", "combinatorial"]
    print(f"Phase: {phase_names[phase]}")
    candidates = recipe_candidates(iteration)
    if not candidates:
        candidates = _combinatorial_family()
    discovered = 0
    results_this_run = []
    scanned = 0
    max_scan = 80

    for name, expr in candidates:
        if scanned >= max_scan and discovered >= 1:
            break
        scanned += 1
        recipe_key = f"{name}|{expr}"
        signature = sig(recipe_key)
        if signature in seen or name in seen or any(b in recipe_key for b in BANNED_SIGNATURES):
            continue

        col = f"auto_{signature}"
        series = eval_recipe(df, name, expr)
        if series is None:
            continue
        df[col] = series
        ev = evaluate_metric(df, col)

        # pick best research target (prefer non-tier targets)
        aucs = {k: v for k, v in ev.items() if k.startswith("auc_") and np.isfinite(v)}
        if not aucs and "tier_gt_rho" not in ev:
            continue

        best_target = max(aucs, key=aucs.get) if aucs else "tier_gt_rho"
        best_value = aucs.get(best_target, abs(ev.get("tier_gt_rho", 0)))

        # only keep if interesting: AUC > 0.55 or |rho| > 0.45 or novel high AUC on violations
        interesting = (
            (aucs.get("auc_ensemble_violation", 0) or 0) >= 0.55
            or (aucs.get("auc_critical_miss", 0) or 0) >= 0.55
            or (aucs.get("auc_judge_disagree", 0) or 0) >= 0.55
            or (aucs.get("auc_gt_dispute", 0) or 0) >= 0.55
            or (aucs.get("auc_low_margin", 0) or 0) >= 0.55
            or abs(ev.get("tier_gt_rho", 0)) >= 0.45
        )
        if not interesting:
            seen.add(signature)
            continue

        row = {
            "iteration": iteration,
            "timestamp": utc_now(),
            "name": name,
            "recipe": expr,
            "signature": signature,
            "best_target": best_target,
            "best_value": float(best_value),
            **ev,
        }
        append_registry(row)
        seen.add(signature)
        discovered += 1
        results_this_run.append(row)

        msg = f"DISCOVER iter {iteration}: `{name}` → {best_target}={best_value:.3f} (ρ={ev.get('tier_gt_rho', float('nan')):.3f})"
        append_discovery(msg)
        print(msg)

        if discovered >= 3:
            break

    # exhausted primary phase — pull fallback recipes from another phase
    if discovered == 0:
        fallback = _combinatorial_family() + _temporal_family() + _rank_instability_family()
        fb = _shuffle_batch(fallback, iteration + 999, 12)
        for name, expr in fb:
            if scanned >= max_scan:
                break
            scanned += 1
            recipe_key = f"{name}|{expr}"
            signature = sig(recipe_key)
            if signature in seen or name in seen:
                continue
            col = f"auto_{signature}"
            series = eval_recipe(df, name, expr)
            if series is None:
                continue
            df[col] = series
            ev = evaluate_metric(df, col)
            aucs = {k: v for k, v in ev.items() if k.startswith("auc_") and np.isfinite(v)}
            if not aucs and "tier_gt_rho" not in ev:
                continue
            best_target = max(aucs, key=aucs.get) if aucs else "tier_gt_rho"
            best_value = aucs.get(best_target, abs(ev.get("tier_gt_rho", 0)))
            interesting = (
                (aucs.get("auc_ensemble_violation", 0) or 0) >= 0.55
                or (aucs.get("auc_critical_miss", 0) or 0) >= 0.55
                or (aucs.get("auc_judge_disagree", 0) or 0) >= 0.55
                or (aucs.get("auc_gt_dispute", 0) or 0) >= 0.55
                or (aucs.get("auc_low_margin", 0) or 0) >= 0.55
                or abs(ev.get("tier_gt_rho", 0)) >= 0.45
            )
            if not interesting:
                seen.add(signature)
                continue
            row = {
                "iteration": iteration,
                "timestamp": utc_now(),
                "name": name,
                "recipe": expr,
                "signature": signature,
                "best_target": best_target,
                "best_value": float(best_value),
                **ev,
            }
            append_registry(row)
            seen.add(signature)
            discovered += 1
            msg = f"DISCOVER iter {iteration} [fallback]: `{name}` → {best_target}={best_value:.3f} (ρ={ev.get('tier_gt_rho', float('nan')):.3f})"
            append_discovery(msg)
            print(msg)
            if discovered >= 3:
                break

    state["total_discovered"] = int(state.get("total_discovered", 0)) + discovered
    state["last_run"] = utc_now()
    save_state(state)
    refresh_leaderboard()

    print(f"\nIter {iteration}: {discovered} new metrics (total registry ~{len(seen)})")
    if not discovered:
        print("No new interesting metrics this batch — expanded search next iteration")
    return discovered


if __name__ == "__main__":
    n = main()
    raise SystemExit(0 if n >= 0 else 1)
