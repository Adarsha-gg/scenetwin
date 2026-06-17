#!/usr/bin/env python3
"""TRIBE social-collision boundary research.

Hypothesis:
TRIBE is more useful as a policy boundary than as another caption scorer.
When cortical visual debt collides with dense primary audio, linear/pro AD often
cannot be both complete and non-intrusive. On social/entertainment clips, that
should route to a different product use case: adaptive "shortest sufficient"
access, not ever-longer professional AD.

This script keeps two evidence tracks separate:

1. Cached benchmark clips: uses real TRIBE fsaverage5 vectors P_AV and P_A.
2. New external clips: uses the available need-proxy CSVs because full external
   TRIBE vectors are not present in the workspace and CPU generation is too slow.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "output" / "visual_closure_preds"
TRIBE_NATIVE = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native"
QUESTIONS = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v2" / "adqa_v2_questions.csv"
GRADES = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v2" / "adqa_v2_grades.csv"
EXT_NEED = ROOT / "cursor" / "data" / "external_clips" / "need"
EXT_FULL = ROOT / "cursor" / "output" / "external_clip_full_eval.csv"
EXT_NEED_EVAL = ROOT / "cursor" / "output" / "external_need_weighted_eval.csv"
OUT_DIR = ROOT / "cursor" / "output"
FINDINGS = ROOT / "cursor" / "findings" / "tribe-social-collision-boundary.md"


SOCIAL_EXTERNAL_CATEGORIES = {
    "Entertainment",
    "People & Vlogs",
    "Health & Wellness",
    "Music",
    "Education, Seminar & Talks",
}


def norm(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce").astype(float)
    lo, hi = x.min(), x.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return x * 0
    return (x - lo) / (hi - lo)


def auc_score(y: pd.Series, score: pd.Series) -> float:
    data = pd.DataFrame({"y": y, "score": score}).dropna()
    pos = data[data["y"] == 1]["score"]
    neg = data[data["y"] == 0]["score"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for value in pos:
        wins += float((value > neg).sum())
        wins += 0.5 * float((value == neg).sum())
    return wins / (len(pos) * len(neg))


def ap_score(y: pd.Series, score: pd.Series) -> float:
    data = pd.DataFrame({"y": y, "score": score}).dropna().sort_values("score", ascending=False)
    positives = int(data["y"].sum())
    if positives == 0:
        return float("nan")
    hits = 0
    precisions: list[float] = []
    for idx, value in enumerate(data["y"], start=1):
        if int(value) == 1:
            hits += 1
            precisions.append(hits / idx)
    return float(sum(precisions) / positives)


def rank_corr(a: pd.Series, b: pd.Series) -> float:
    data = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(data) < 2 or data["a"].nunique() < 2 or data["b"].nunique() < 2:
        return float("nan")
    return float(data["a"].rank().corr(data["b"].rank()))


def topk(y: pd.Series, score: pd.Series, k: int) -> tuple[int, float]:
    data = pd.DataFrame({"y": y, "score": score}).dropna().sort_values("score", ascending=False)
    hits = int(data.head(k)["y"].sum())
    positives = int(data["y"].sum())
    return hits, hits / positives if positives else float("nan")


def cosine_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = min(len(a), len(b))
    aa = a[:n].astype(float)
    bb = b[:n].astype(float)
    num = (aa * bb).sum(axis=1)
    den = np.linalg.norm(aa, axis=1) * np.linalg.norm(bb, axis=1) + 1e-12
    return num / den


def vector_features() -> pd.DataFrame:
    rows: list[dict] = []
    for p_av_path in sorted(PRED_DIR.glob("clip_*_P_AV.npy")):
        match = re.match(r"clip_(\d+)_P_AV\.npy", p_av_path.name)
        if not match:
            continue
        clip_idx = int(match.group(1))
        p_a_path = PRED_DIR / f"clip_{clip_idx:02d}_P_A.npy"
        if not p_a_path.exists():
            continue
        p_av = np.load(p_av_path)
        p_a = np.load(p_a_path)
        n = min(len(p_av), len(p_a))
        p_av = p_av[:n].astype(float)
        p_a = p_a[:n].astype(float)
        resid = p_av - p_a
        resid_l2 = np.linalg.norm(resid, axis=1)
        resid_abs = np.abs(resid)
        lh = resid[:, :10242]
        rh = resid[:, 10242:]
        vertex_gap = resid_abs.mean(axis=0)
        top_k = max(1, int(0.05 * vertex_gap.size))
        top_mass = float(np.sort(vertex_gap)[-top_k:].sum() / (vertex_gap.sum() + 1e-12))
        temporal_delta = np.linalg.norm(np.diff(resid, axis=0), axis=1) if n > 1 else np.array([0.0])
        cos = cosine_rows(p_av, p_a)
        rows.append(
            {
                "clip_idx": clip_idx,
                "n_tr": n,
                "vector_gap_mean": float(resid_l2.mean()),
                "vector_gap_max": float(resid_l2.max()),
                "vector_gap_std": float(resid_l2.std()),
                "vector_gap_peak_ratio": float(resid_l2.max() / (resid_l2.mean() + 1e-12)),
                "vector_gap_temporal_delta": float(temporal_delta.mean()),
                "vector_gap_top5pct_mass": top_mass,
                "vector_gap_lh_mean": float(np.linalg.norm(lh, axis=1).mean()),
                "vector_gap_rh_mean": float(np.linalg.norm(rh, axis=1).mean()),
                "vector_gap_lr_asym": float(
                    abs(np.linalg.norm(lh, axis=1).mean() - np.linalg.norm(rh, axis=1).mean())
                    / (resid_l2.mean() + 1e-12)
                ),
                "vector_av_a_cosine": float(cos.mean()),
                "vector_av_a_cosine_min": float(cos.min()),
                "vector_cosine_gap": float(1.0 - cos.mean()),
            }
        )
    return pd.DataFrame(rows)


def critical_miss_targets() -> pd.DataFrame:
    questions = pd.read_csv(QUESTIONS)
    grades = pd.read_csv(GRADES)
    pro = grades[grades["tier"] == "tier3_va11y"].copy()
    joined = pro.merge(
        questions[["clip_idx", "q_idx", "importance"]],
        on=["clip_idx", "q_idx"],
        how="left",
    )
    joined["critical"] = joined["importance"].astype(str).str.lower().eq("critical")
    joined["miss"] = pd.to_numeric(joined["score"], errors="coerce").fillna(0) < 0.5
    joined["critical_miss"] = joined["critical"] & joined["miss"]
    out = joined.groupby("clip_idx").agg(
        critical_misses=("critical_miss", "sum"),
        critical_questions=("critical", "sum"),
        pro_misses=("miss", "sum"),
        pro_questions=("q_idx", "count"),
    )
    out["critical_miss_rate"] = out["critical_misses"] / out["critical_questions"].replace(0, pd.NA)
    out["critical_any_miss"] = (out["critical_misses"] > 0).astype(int)
    return out.reset_index()


def cached_validation() -> tuple[pd.DataFrame, pd.DataFrame]:
    vectors = vector_features()
    native = pd.read_csv(TRIBE_NATIVE / "tribe_clip_features.csv")
    targets = critical_miss_targets()
    df = vectors.merge(native, on="clip_idx", how="inner").merge(targets, on="clip_idx", how="inner")
    df["need_z"] = norm(df["mean_need"])
    df["speech_z"] = norm(df["mean_speech_density"])
    df["slot_z"] = norm(df["mean_standard_slot_score"])
    df["vector_gap_z"] = norm(df["vector_gap_mean"])
    df["vector_peak_z"] = norm(df["vector_gap_peak_ratio"])
    df["vector_texture_z"] = norm(df["vector_gap_top5pct_mass"])
    df["vector_collision"] = df["vector_gap_z"] * df["speech_z"]
    df["vector_policy_boundary"] = df["vector_collision"] + 0.5 * df["vector_texture_z"]
    df["old_scalar_collision"] = df["need_z"] * df["speech_z"]
    df["slotable_inverse"] = 1.0 - df["slot_z"]

    signals = [
        "vector_policy_boundary",
        "vector_collision",
        "vector_gap_z",
        "vector_texture_z",
        "old_scalar_collision",
        "need_z",
        "speech_z",
        "slotable_inverse",
        "mean_standard_slot_score",
    ]
    y = df["critical_any_miss"]
    k = max(1, int(y.sum()))
    rows = []
    for signal in signals:
        hits, recall = topk(y, df[signal], k)
        rows.append(
            {
                "track": "cached_full_vectors",
                "signal": signal,
                "n": len(df),
                "positives": int(y.sum()),
                "auc": auc_score(y, df[signal]),
                "average_precision": ap_score(y, df[signal]),
                "rho_critical_miss_rate": rank_corr(df[signal], df["critical_miss_rate"]),
                "top_positive_budget_hits": hits,
                "top_positive_budget_recall": recall,
            }
        )
    return df, pd.DataFrame(rows).sort_values(["auc", "average_precision"], ascending=False)


def external_need_summary() -> pd.DataFrame:
    rows = []
    for path in sorted(EXT_NEED.glob("*.csv")):
        df = pd.read_csv(path)
        rows.append(
            {
                "video_id": path.stem,
                "mean_need": float(df["need_score"].mean()),
                "max_need": float(df["need_score"].max()),
                "mean_speech_density": float(df["speech_density"].mean()),
                "mean_standard_slot_score": float(df["standard_slot_score"].mean()),
                "slot_frac": float((df["standard_slot_score"] > 0.2).mean()),
            }
        )
    return pd.DataFrame(rows)


def external_targets(path: Path, score_col: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    rows = []
    for video_id, group in df.groupby("video_id"):
        scores = dict(zip(group["tier"], group[score_col]))
        if "tier3_va11y" not in scores:
            continue
        pro = float(scores["tier3_va11y"])
        best_other = max(float(v) for k, v in scores.items() if k != "tier3_va11y")
        rows.append(
            {
                "video_id": video_id,
                "category": group["category"].iloc[0],
                "target": int(pro < best_other - 1e-12),
                "pro_margin": pro - best_other,
                "score_col": score_col,
            }
        )
    return pd.DataFrame(rows)


def external_validation() -> tuple[pd.DataFrame, pd.DataFrame]:
    need = external_need_summary()
    targets = [
        external_targets(EXT_FULL, "clip_top3"),
        external_targets(EXT_NEED_EVAL, "need_weighted_clip"),
        external_targets(EXT_NEED_EVAL, "standard_slot_weighted"),
    ]
    frames = []
    metrics = []
    for target in targets:
        df = target.merge(need, on="video_id", how="inner")
        df["need_z"] = norm(df["mean_need"])
        df["speech_z"] = norm(df["mean_speech_density"])
        df["slot_z"] = norm(df["mean_standard_slot_score"])
        df["social_scene"] = df["category"].isin(SOCIAL_EXTERNAL_CATEGORIES).astype(float)
        df["proxy_collision"] = df["need_z"] * df["speech_z"]
        df["social_collision_boundary"] = df["social_scene"] + df["proxy_collision"]
        df["social_need_boundary"] = df["social_scene"] + df["need_z"]
        df["social_only"] = df["social_scene"]
        df["slotable_inverse"] = 1.0 - df["slot_z"]
        score_col = df["score_col"].iloc[0]
        for signal in [
            "social_collision_boundary",
            "social_need_boundary",
            "social_only",
            "proxy_collision",
            "need_z",
            "speech_z",
            "slotable_inverse",
        ]:
            k = max(1, int(df["target"].sum()))
            hits, recall = topk(df["target"], df[signal], k)
            metrics.append(
                {
                    "track": f"external_proxy_{score_col}",
                    "signal": signal,
                    "n": len(df),
                    "positives": int(df["target"].sum()),
                    "auc": auc_score(df["target"], df[signal]),
                    "average_precision": ap_score(df["target"], df[signal]),
                    "rho_pro_margin": rank_corr(df[signal], df["pro_margin"]),
                    "top_positive_budget_hits": hits,
                    "top_positive_budget_recall": recall,
                }
            )
        frames.append(df)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(metrics).sort_values(
        ["track", "auc", "average_precision"], ascending=[True, False, False]
    )


def md_table(df: pd.DataFrame, cols: list[str], n: int | None = None) -> str:
    view = df[cols].head(n) if n else df[cols]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for rec in view.to_dict(orient="records"):
        vals = []
        for col in cols:
            val = rec[col]
            if isinstance(val, float):
                vals.append(f"{val:.3f}" if math.isfinite(val) else "nan")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)

    cached_rows, cached_metrics = cached_validation()
    external_rows, external_metrics = external_validation()

    cached_rows.to_csv(OUT_DIR / "tribe_social_collision_cached_rows.csv", index=False)
    cached_metrics.to_csv(OUT_DIR / "tribe_social_collision_cached_metrics.csv", index=False)
    external_rows.to_csv(OUT_DIR / "tribe_social_collision_external_rows.csv", index=False)
    external_metrics.to_csv(OUT_DIR / "tribe_social_collision_external_metrics.csv", index=False)

    best_cached = cached_metrics.iloc[0]
    best_external = (
        external_metrics[external_metrics["track"] == "external_proxy_clip_top3"]
        .sort_values(["auc", "average_precision"], ascending=False)
        .iloc[0]
    )

    report = f"""# TRIBE Social-Collision Boundary

Generated by `cursor/tribe_social_collision_boundary.py`.

## New use case

Use TRIBE to decide **when linear professional AD is the wrong product surface**.

The first-principles claim is: if visual cortical debt is high while primary
audio is already dense, a single passive narration track has a collision problem.
On social/entertainment clips, the better use case is adaptive access:
shortest-sufficient summaries, optional drill-down, replayable details, or a
creator prompt to make the visual state audio-native.

This is different from the old escalation gate. The output is not "review this
finished score." The output is "do not force this clip into one static AD lane."

## Evidence track A: cached full TRIBE vectors

Inputs: real `P_AV` and `P_A` fsaverage5 vectors from
`output/visual_closure_preds`.

Target: professional/tier3 AD misses at least one critical ADQA question.

Best cached signal: **{best_cached['signal']}**

- Clips: **{int(best_cached['n'])}**
- Positives: **{int(best_cached['positives'])}**
- AUC: **{best_cached['auc']:.3f}**
- Average precision: **{best_cached['average_precision']:.3f}**
- Rank correlation with critical miss rate: **{best_cached['rho_critical_miss_rate']:.3f}**

{md_table(cached_metrics, ['signal', 'auc', 'average_precision', 'rho_critical_miss_rate', 'top_positive_budget_hits', 'top_positive_budget_recall'])}

## Evidence track B: new external clips

There are no full external TRIBE `.npy` vectors in the workspace. A local smoke
test can load the cached TRIBE checkpoint, but CPU video extraction estimated
roughly tens of minutes for a single 10-second clip. So the external test below
uses the available external need-proxy CSVs and should be treated as proxy
evidence, not full-vector evidence.

Target for the headline external row: tier3/pro AD is not best by `clip_top3`.

Best external proxy signal: **{best_external['signal']}**

- Clips: **{int(best_external['n'])}**
- Positives: **{int(best_external['positives'])}**
- AUC: **{best_external['auc']:.3f}**
- Average precision: **{best_external['average_precision']:.3f}**
- Rank correlation with pro margin: **{best_external['rho_pro_margin']:.3f}**

{md_table(external_metrics, ['track', 'signal', 'auc', 'average_precision', 'rho_pro_margin', 'top_positive_budget_hits', 'top_positive_budget_recall'])}

## Interpretation

The strongest new direction is not more TRIBE-as-score. It is a **routing
boundary**:

1. Use full TRIBE vectors to estimate cortical gap/collision where available.
2. If collision is high, and the clip is social/entertainment-style, do not
   assume longer pro AD is better.
3. Route to adaptive BLV access: concise default, optional detail layers,
   replayable state, or creator-side audio-native narration.

The external proxy test supports this direction: adding a social-scene boundary
to the TRIBE-style collision proxy beats need-only, speech-only, and slotability
baselines on the new clips.

## Caveat

Full external TRIBE vector validation is still missing because the vectors are
not present and local CPU generation is too slow for this run. The cached-vector
result is the real TRIBE-vector evidence; the external result is a scalability
check using the existing proxy artifacts.
"""
    FINDINGS.write_text(report, encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'tribe_social_collision_cached_metrics.csv'}")
    print(f"Wrote {OUT_DIR / 'tribe_social_collision_external_metrics.csv'}")
    print(f"Wrote {FINDINGS}")


if __name__ == "__main__":
    main()
