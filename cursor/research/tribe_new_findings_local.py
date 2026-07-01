#!/usr/bin/env python3
"""Local cached-data experiments for new SceneTwin/TRIBE findings.

This script intentionally avoids API calls and heavy TRIBE inference. It mines the
existing CSV/JSON artifacts for new validation signals and guardrails.
"""
from __future__ import annotations

import ast
import csv
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "research" / "output" / "new_findings_local"
REPORT = ROOT / "output" / "reports" / "tribe-new-findings-local-run.md"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with open(ROOT / path if isinstance(path, str) else path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for k in row:
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def fnum(v, default=math.nan) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def finite(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def avg(xs: list[float]) -> float:
    xs = [x for x in xs if finite(x)]
    return mean(xs) if xs else math.nan


def auc_score(values: list[float], labels: list[int]) -> float:
    """AUC for higher values indicating positive labels; tie = 0.5."""
    pairs = [(v, y) for v, y in zip(values, labels) if finite(v) and y in (0, 1)]
    pos = [v for v, y in pairs if y == 1]
    neg = [v for v, y in pairs if y == 0]
    if not pos or not neg:
        return math.nan
    wins = ties = total = 0
    for p in pos:
        for n in neg:
            total += 1
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
    return (wins + 0.5 * ties) / total if total else math.nan


def spearman(xs: list[float], ys: list[float]) -> float:
    pairs = [(x, y) for x, y in zip(xs, ys) if finite(x) and finite(y)]
    if len(pairs) < 3:
        return math.nan
    xs2, ys2 = zip(*pairs)

    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            r = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                out[order[k]] = r
            i = j + 1
        return out

    rx, ry = ranks(xs2), ranks(ys2)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    deny = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (denx * deny) if denx and deny else math.nan


def sign_p_one_sided(wins: int, losses: int) -> float:
    """Exact one-sided binomial P(X>=wins), ignoring ties, p=0.5."""
    n = wins + losses
    if n == 0:
        return math.nan
    return sum(math.comb(n, k) for k in range(wins, n + 1)) / (2**n)


def paired_deltas(path: str | Path, positive_condition: str = "gap_targeted") -> tuple[list[dict], dict[str, dict]]:
    rows = read_csv(path)
    by_key: dict[tuple[str, str], dict] = defaultdict(dict)
    meta: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["video_id"], str(r["q_idx"]))
        by_key[key][r["condition"]] = fnum(r["score"])
        meta[key] = {k: r.get(k, "") for k in r.keys() if k not in {"condition", "score"}}
    out = []
    by_video: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for key, scores in by_key.items():
        if "baseline" not in scores:
            continue
        cond = positive_condition if positive_condition in scores else None
        if cond is None:
            candidates = [c for c in scores if c != "baseline"]
            if not candidates:
                continue
            cond = candidates[0]
        delta = scores[cond] - scores["baseline"]
        row = {"video_id": key[0], "q_idx": key[1], "condition": cond, "delta": delta, **meta[key]}
        out.append(row)
        matched = str(meta[key].get("matched", "0")) == "1"
        by_video[key[0]]["all"].append(delta)
        by_video[key[0]]["matched" if matched else "unmatched"].append(delta)
    video_summary = {}
    for vid, d in by_video.items():
        md = d.get("matched", [])
        ud = d.get("unmatched", [])
        all_d = d.get("all", [])
        video_summary[vid] = {
            "all_n": len(all_d),
            "all_mean_delta": avg(all_d),
            "matched_n": len(md),
            "matched_mean_delta": avg(md),
            "matched_wins": sum(1 for x in md if x > 0),
            "matched_losses": sum(1 for x in md if x < 0),
            "matched_ties": sum(1 for x in md if x == 0),
            "unmatched_n": len(ud),
            "unmatched_mean_delta": avg(ud),
        }
    return out, video_summary


def tensor_health_audit() -> dict:
    manifest_path = ROOT / "cursor" / "research" / "output" / "tribe_tensors" / "manifest.csv"
    manifest = read_csv(manifest_path)
    rows = []
    missing_files = []
    bad_shapes = []
    audio_bad = []
    align_zero_or_low = []
    temporal_mismatch = []
    json_manifest_mismatch = []
    files_by_key = {}
    for p in (ROOT / "cursor" / "research" / "output" / "tribe_tensors").glob("*/*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            files_by_key[obj.get("clip_key", p.stem)] = p
        except Exception:
            files_by_key[p.stem] = p
    for r in manifest:
        key = r["clip_key"]
        p = files_by_key.get(key)
        if not p:
            missing_files.append(key)
            continue
        obj = json.loads(p.read_text(encoding="utf-8"))
        try:
            pav = ast.literal_eval(str(r.get("P_AV_shape", "[]")))
            pa = ast.literal_eval(str(r.get("P_A_shape", "[]")))
            pad = ast.literal_eval(str(r.get("P_AD_shape", "[]")))
        except Exception:
            pav = pa = pad = []
        vertices_ok = all(len(s) == 2 and int(s[1]) == 20484 for s in [pav, pa, pad])
        if not vertices_ok:
            bad_shapes.append(key)
        if str(r.get("audio_only_ok", "")).lower() != "true":
            audio_bad.append(key)
        align = fnum(r.get("alignment_cosine"))
        if finite(align) and align <= 0.5:
            align_zero_or_low.append(key)
        av_t = int(pav[0]) if len(pav) == 2 else -1
        a_t = int(pa[0]) if len(pa) == 2 else -1
        ad_t = int(pad[0]) if len(pad) == 2 else -1
        if av_t != a_t:
            temporal_mismatch.append(key)
        for col in ["accessibility_gap", "description_gain", "alignment_cosine", "video_id", "corpus", "category"]:
            if str(obj.get(col, "")) != str(r.get(col, "")):
                # Float formatting can differ; only record large numeric mismatches.
                if col in {"accessibility_gap", "description_gain", "alignment_cosine"}:
                    if abs(fnum(obj.get(col)) - fnum(r.get(col))) > 1e-9:
                        json_manifest_mismatch.append(f"{key}:{col}")
                else:
                    json_manifest_mismatch.append(f"{key}:{col}")
        rows.append({
            "clip_key": key,
            "corpus": r.get("corpus", ""),
            "video_id": r.get("video_id", ""),
            "category": r.get("category", ""),
            "audio_only_ok": r.get("audio_only_ok", ""),
            "alignment_cosine": align,
            "accessibility_gap": fnum(r.get("accessibility_gap")),
            "description_gain": fnum(r.get("description_gain")),
            "P_AV_T": av_t,
            "P_A_T": a_t,
            "P_AD_T": ad_t,
            "vertices_ok": vertices_ok,
            "av_a_temporal_mismatch": av_t != a_t,
        })
    write_csv(OUT_DIR / "tensor_health_rows.csv", rows)
    summary = {
        "manifest_rows": len(manifest),
        "json_files": len(files_by_key),
        "missing_json_files": missing_files,
        "extra_json_files": sorted(set(files_by_key) - {r["clip_key"] for r in manifest}),
        "bad_shape_count": len(bad_shapes),
        "audio_only_bad_count": len(audio_bad),
        "alignment_le_0_5_count": len(align_zero_or_low),
        "alignment_le_0_5_keys": align_zero_or_low,
        "av_a_temporal_mismatch_count": len(temporal_mismatch),
        "json_manifest_mismatch_count": len(json_manifest_mismatch),
        "json_manifest_mismatch_examples": json_manifest_mismatch[:20],
        "accessibility_gap_mean": avg([r["accessibility_gap"] for r in rows]),
        "description_gain_mean": avg([r["description_gain"] for r in rows]),
    }
    return summary


def feature_selection_null() -> dict:
    rows = read_csv("output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv")
    features = [
        "duration_s", "mean_need", "max_need", "need_entropy", "high_need_frac",
        "high_need_seconds_frac", "extended_seconds_frac", "mean_speech_density",
        "mean_standard_slot_score", "mean_extended_need_score", "tribe_pressure",
        "tier3_va11y_words", "pro_minus_short_words", "pro_minus_long_words",
    ]
    labels = [1 if fnum(r.get("all4_fail")) > 0 else 0 for r in rows]
    values_by_feature = {f: [fnum(r.get(f)) for r in rows] for f in features}
    feature_rows = []
    observed_best = -1.0
    observed_best_feature = None
    observed_best_direction = None
    for f, vals in values_by_feature.items():
        high = auc_score(vals, labels)
        low = auc_score([-v if finite(v) else math.nan for v in vals], labels)
        best = max(high, low)
        direction = "high_bad" if high >= low else "low_bad"
        feature_rows.append({"feature": f, "auc_high_bad": high, "auc_low_bad": low, "best_auc": best, "best_direction": direction})
        if best > observed_best:
            observed_best = best
            observed_best_feature = f
            observed_best_direction = direction
    write_csv(OUT_DIR / "feature_selection_null_features.csv", feature_rows)
    n = len(labels)
    positives = sum(labels)
    max_stats = []
    obs_pos = tuple(i for i, y in enumerate(labels) if y)
    for pos_idx in itertools.combinations(range(n), positives):
        perm = [1 if i in pos_idx else 0 for i in range(n)]
        mx = -1.0
        for vals in values_by_feature.values():
            high = auc_score(vals, perm)
            low = auc_score([-v if finite(v) else math.nan for v in vals], perm)
            mx = max(mx, high, low)
        max_stats.append(mx)
    p_familywise = sum(1 for x in max_stats if x >= observed_best - 1e-12) / len(max_stats)
    # Hypergeometric p for the selected feature's top-k in selected direction.
    selected_vals = values_by_feature[observed_best_feature]
    if observed_best_direction == "low_bad":
        selected_vals = [-v if finite(v) else math.nan for v in selected_vals]
    top = sorted(range(n), key=lambda i: selected_vals[i], reverse=True)[:positives]
    hits = sum(labels[i] for i in top)
    # P(at least hits positives in top positives positions) under random ranking.
    hyper = 0.0
    N = n; K = positives; draws = positives
    for h in range(hits, min(K, draws) + 1):
        hyper += math.comb(K, h) * math.comb(N - K, draws - h) / math.comb(N, draws)
    return {
        "n": n,
        "positives": positives,
        "candidate_feature_count": len(features),
        "observed_best_feature": observed_best_feature,
        "observed_best_direction": observed_best_direction,
        "observed_best_auc": observed_best,
        "exact_familywise_maxstat_p": p_familywise,
        "selected_top_k_hits": hits,
        "selected_top_k_hypergeom_p": hyper,
        "all_possible_positive_sets": len(max_stats),
        "observed_positive_indices": obs_pos,
    }


def external_low_gap_and_failure() -> dict:
    score_rows = read_csv("cursor/output/external_ensemble_eval.csv")
    by_vid: dict[str, dict[str, dict]] = defaultdict(dict)
    cat_by_vid = {}
    for r in score_rows:
        by_vid[r["video_id"]][r["tier"]] = r
        cat_by_vid[r["video_id"]] = r.get("category", "")
    clip_summary = {r["video_id"]: r for r in read_csv("cursor/research/output/tribe_blind_spot_clip_summary.csv") if r.get("corpus") == "external"}
    out = []
    for vid, tiers in by_vid.items():
        # Corrected ladder excludes tier2_vatex_long.
        need = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]
        if not all(t in tiers for t in need) or vid not in clip_summary:
            continue
        vals_adqa = [fnum(tiers[t]["adqa_score"]) for t in need]
        vals_ens = [fnum(tiers[t]["ensemble_mean_clip_top3"]) for t in need]
        vals_clip = [fnum(tiers[t]["clip_top3"]) for t in need]
        def full_order(vals):
            return int(vals[0] < vals[1] < vals[2])
        cs = clip_summary[vid]
        out.append({
            "video_id": vid,
            "category": cat_by_vid.get(vid, ""),
            "adqa_full_order": full_order(vals_adqa),
            "ensemble_full_order": full_order(vals_ens),
            "clip_full_order": full_order(vals_clip),
            "adqa_fail": 1 - full_order(vals_adqa),
            "ensemble_fail": 1 - full_order(vals_ens),
            "clip_fail": 1 - full_order(vals_clip),
            "mean_visual_gap": fnum(cs.get("mean_visual_gap")),
            "max_visual_gap": fnum(cs.get("max_visual_gap")),
            "top1_vs_uniform": fnum(cs.get("top1_vs_uniform")),
            "top1_share": fnum(cs.get("top1_share")),
            "scene_agent_time_rho": fnum(cs.get("scene_agent_time_rho")),
            "scene_agent_peak_apart": fnum(cs.get("scene_agent_peak_apart")),
        })
    write_csv(OUT_DIR / "external_low_gap_failure_rows.csv", out)
    labels_adqa = [r["adqa_fail"] for r in out]
    labels_ens = [r["ensemble_fail"] for r in out]
    metric_rows = []
    for feat in ["mean_visual_gap", "max_visual_gap", "top1_vs_uniform", "top1_share", "scene_agent_peak_apart"]:
        vals = [r[feat] for r in out]
        metric_rows.append({
            "feature": feat,
            "adqa_fail_auc_high_bad": auc_score(vals, labels_adqa),
            "ensemble_fail_auc_high_bad": auc_score(vals, labels_ens),
            "spearman_vs_adqa_fail": spearman(vals, labels_adqa),
        })
    write_csv(OUT_DIR / "external_low_gap_failure_metrics.csv", metric_rows)
    # Bottom quartile/third failure rates by max_visual_gap.
    sorted_rows = sorted(out, key=lambda r: r["max_visual_gap"])
    def subset_stats(frac: float):
        k = max(1, int(round(len(sorted_rows) * frac)))
        low = sorted_rows[:k]
        high = sorted_rows[-k:]
        return {
            f"bottom_{int(frac*100)}_n": k,
            f"bottom_{int(frac*100)}_adqa_fail_rate": avg([r["adqa_fail"] for r in low]),
            f"bottom_{int(frac*100)}_ensemble_fail_rate": avg([r["ensemble_fail"] for r in low]),
            f"top_{int(frac*100)}_adqa_fail_rate": avg([r["adqa_fail"] for r in high]),
            f"top_{int(frac*100)}_ensemble_fail_rate": avg([r["ensemble_fail"] for r in high]),
        }
    summary = {"n": len(out), "adqa_fail_count": sum(labels_adqa), "ensemble_fail_count": sum(labels_ens)}
    summary.update(subset_stats(0.25))
    summary.update(subset_stats(1/3))
    summary["feature_metrics"] = metric_rows
    return summary


def route_confidence_and_controls() -> dict:
    # Build per-video route/window feature summary.
    windows = read_csv("cursor/research/output/tribe_blind_spot_windows.csv")
    feat_by_vid = {}
    for vid, group in defaultdict(list, { }).items():
        pass
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in windows:
        if r.get("corpus") == "external":
            grouped[r["video_id"]].append(r)
    for vid, g in grouped.items():
        high_windows = [r for r in g if r.get("route") != "static_ad_ok_low_gap"]
        peak = max(fnum(r.get("peak_visual_gap")) for r in g)
        top = max(g, key=lambda r: fnum(r.get("peak_visual_gap")))
        vis_minus = max(fnum(r.get("visual_minus_control")) for r in g)
        control_ratio_vals = []
        for r in g:
            pv = fnum(r.get("peak_visual_gap"))
            cg = fnum(r.get("control_gap"))
            if finite(pv) and pv > 0:
                control_ratio_vals.append(cg / pv)
        routes = Counter(r.get("route") for r in g)
        feat_by_vid[vid] = {
            "video_id": vid,
            "window_n": len(g),
            "active_window_frac": len(high_windows) / len(g) if g else math.nan,
            "max_peak_visual_gap": peak,
            "max_visual_minus_control": vis_minus,
            "top_control_ratio": fnum(top.get("control_gap")) / peak if peak else math.nan,
            "mean_control_ratio": avg(control_ratio_vals),
            "top_dominance_margin": fnum(top.get("dominance_margin")),
            "top_route": top.get("route"),
            "top_dominant_type": top.get("dominant_type"),
            "layout_window_count": routes.get("layout_replay_or_scene_cue", 0),
            "action_window_count": routes.get("action_state_or_agent_cue", 0),
            "low_window_count": routes.get("static_ad_ok_low_gap", 0),
        }
    # Clip summary features.
    for r in read_csv("cursor/research/output/tribe_blind_spot_clip_summary.csv"):
        vid = r.get("video_id")
        if r.get("corpus") == "external" and vid in feat_by_vid:
            feat_by_vid[vid].update({
                "category": r.get("category", ""),
                "top1_vs_uniform": fnum(r.get("top1_vs_uniform")),
                "scene_agent_time_rho": fnum(r.get("scene_agent_time_rho")),
                "scene_agent_peak_apart": fnum(r.get("scene_agent_peak_apart")),
                "mean_visual_gap": fnum(r.get("mean_visual_gap")),
                "max_visual_gap": fnum(r.get("max_visual_gap")),
            })
    summaries = {}
    for name, path in {
        "surgical_haiku": "cursor/research/output/tribe_surgical_adqa_perq.csv",
        "crossjudge_gpt5": "cursor/research/output/tribe_crossjudge_gpt5_perq.csv",
        "crossjudge_opus17": "cursor/research/output/tribe_crossjudge_opus_17_perq.csv",
    }.items():
        _, vsummary = paired_deltas(path)
        rows = []
        for vid, vs in vsummary.items():
            if vid not in feat_by_vid:
                continue
            row = {**feat_by_vid[vid], **vs, "run": name}
            rows.append(row)
        write_csv(OUT_DIR / f"route_confidence_{name}.csv", rows)
        metric_rows = []
        for feat in [
            "max_peak_visual_gap", "max_visual_minus_control", "top_control_ratio",
            "mean_control_ratio", "top_dominance_margin", "active_window_frac",
            "top1_vs_uniform", "scene_agent_peak_apart", "mean_visual_gap", "max_visual_gap",
        ]:
            vals = [r.get(feat, math.nan) for r in rows]
            target = [r.get("matched_mean_delta", math.nan) for r in rows]
            metric_rows.append({"run": name, "feature": feat, "spearman_vs_matched_delta": spearman(vals, target)})
        write_csv(OUT_DIR / f"route_confidence_metrics_{name}.csv", metric_rows)
        # Top/bottom third by strongest predictor candidates.
        def split(feat: str):
            avail = [r for r in rows if finite(r.get(feat, math.nan)) and finite(r.get("matched_mean_delta", math.nan))]
            avail = sorted(avail, key=lambda r: r[feat])
            k = max(1, len(avail) // 3)
            low = avail[:k]; high = avail[-k:]
            return {
                f"{feat}_low_third_delta": avg([r["matched_mean_delta"] for r in low]),
                f"{feat}_high_third_delta": avg([r["matched_mean_delta"] for r in high]),
                f"{feat}_n_per_third": k,
            }
        s = {"n_videos": len(rows), "matched_mean_delta": avg([r["matched_mean_delta"] for r in rows])}
        for feat in ["max_visual_minus_control", "top_control_ratio", "top_dominance_margin", "top1_vs_uniform"]:
            s.update(split(feat))
        s["metrics"] = metric_rows
        summaries[name] = s
    # Type-specific deltas from surgical run (has q_type/tribe_type).
    deltas, _ = paired_deltas("cursor/research/output/tribe_surgical_adqa_perq.csv")
    by_type = defaultdict(list)
    for r in deltas:
        if str(r.get("matched", "0")) == "1":
            by_type[r.get("tribe_type") or "unknown"].append(r["delta"])
    type_rows = []
    for t, ds in sorted(by_type.items()):
        type_rows.append({
            "tribe_type": t,
            "n": len(ds),
            "mean_delta": avg(ds),
            "wins": sum(1 for x in ds if x > 0),
            "losses": sum(1 for x in ds if x < 0),
            "ties": sum(1 for x in ds if x == 0),
            "sign_p_one_sided": sign_p_one_sided(sum(1 for x in ds if x > 0), sum(1 for x in ds if x < 0)),
        })
    write_csv(OUT_DIR / "surgical_matched_delta_by_tribe_type.csv", type_rows)
    summaries["surgical_type_specific"] = type_rows
    return summaries


def write_report(results: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    fs = results["feature_selection_null"]
    tensor = results["tensor_health"]
    ext = results["external_low_gap"]
    route = results["route_confidence"]

    # Helper for compact metric rendering.
    def fmt(x, digits=3):
        return "n/a" if not finite(x) else f"{x:.{digits}f}"

    feature_lines = []
    for m in ext["feature_metrics"]:
        feature_lines.append(
            f"| {m['feature']} | {fmt(m['adqa_fail_auc_high_bad'])} | {fmt(m['ensemble_fail_auc_high_bad'])} | {fmt(m['spearman_vs_adqa_fail'])} |"
        )
    type_lines = []
    for r in route["surgical_type_specific"]:
        type_lines.append(
            f"| {r['tribe_type']} | {r['n']} | {fmt(r['mean_delta'])} | {r['wins']}/{r['losses']}/{r['ties']} | {fmt(r['sign_p_one_sided'], 4)} |"
        )
    conf_lines = []
    for run_name in ["surgical_haiku", "crossjudge_gpt5", "crossjudge_opus17"]:
        s = route[run_name]
        metrics = {m["feature"]: m["spearman_vs_matched_delta"] for m in s["metrics"]}
        conf_lines.append(
            f"| {run_name} | {s['n_videos']} | {fmt(s['matched_mean_delta'])} | {fmt(metrics.get('top_dominance_margin'))} | {fmt(metrics.get('max_visual_minus_control'))} | {fmt(metrics.get('top_control_ratio'))} | {fmt(metrics.get('top1_vs_uniform'))} |"
        )

    text = f"""---
title: TRIBE New Findings — Local Cached-Data Run
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_new_findings_local.py
  - cursor/research/output/new_findings_local/
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_surgical_adqa_perq.csv
  - cursor/research/output/tribe_crossjudge_gpt5_perq.csv
  - cursor/research/output/tribe_crossjudge_opus_17_perq.csv
  - cursor/output/external_ensemble_eval.csv
---

# TRIBE New Findings — Local Cached-Data Run

This is the first actual cached-data pass after the 100-item backlog. It uses no new API calls and no GPU/TRIBE inference.

## Finding 1 — the in-benchmark AUC=1.00 survives feature-selection correction only as pilot evidence

The old in-benchmark result had 2 positives out of 18 clips. I re-tested it as a **family-wise max-statistic null** over {fs['candidate_feature_count']} plausible TRIBE/simple features, enumerating all {fs['all_possible_positive_sets']} possible 2-positive label assignments.

- Best observed feature: `{fs['observed_best_feature']}` ({fs['observed_best_direction']})
- Best observed AUC: **{fmt(fs['observed_best_auc'])}**
- Selected feature top-2 hypergeometric p: **{fmt(fs['selected_top_k_hypergeom_p'], 4)}**
- Family-wise max-stat p across candidate features: **{fmt(fs['exact_familywise_maxstat_p'], 4)}**

Interpretation: the recall@2/AUC=1.00 story remains real as a pilot, but the corrected p is weaker than the single-feature hypergeometric number. Use it as supporting evidence, not as a standalone headline.

Artifact: `cursor/research/output/new_findings_local/feature_selection_null_features.csv`.

## Finding 2 — external low-gap clips look safer, but max visual gap is only a modest failure predictor

On the corrected external ladder, joined `external_ensemble_eval.csv` to the 60 external TRIBE blind-spot summaries.

- n clips: {ext['n']}
- ADQA full-order failures: {ext['adqa_fail_count']}/{ext['n']}
- Ensemble full-order failures: {ext['ensemble_fail_count']}/{ext['n']}
- Bottom 25% by `max_visual_gap`: ADQA fail rate **{fmt(ext['bottom_25_adqa_fail_rate'])}**, ensemble fail rate **{fmt(ext['bottom_25_ensemble_fail_rate'])}**
- Top 25% by `max_visual_gap`: ADQA fail rate **{fmt(ext['top_25_adqa_fail_rate'])}**, ensemble fail rate **{fmt(ext['top_25_ensemble_fail_rate'])}**

| Feature | AUC vs ADQA fail | AUC vs ensemble fail | Spearman vs ADQA fail |
|---|---:|---:|---:|
{chr(10).join(feature_lines)}

Interpretation: this supports **low-gap early-exit / lower-review priority** as a hypothesis, but not an automatic skip policy. Max/mean visual gap are modest predictors; concentration (`top1_vs_uniform`) is weaker for failure prediction.

Artifacts: `external_low_gap_failure_rows.csv`, `external_low_gap_failure_metrics.csv`.

## Finding 3 — route-confidence features are not yet calibrated predictors of targeted-generation lift

I joined per-video TRIBE route features to matched-question deltas from the cached Haiku, GPT-5, and Opus judge runs.

| Run | videos | mean matched delta | ρ dominance-margin | ρ visual-minus-control | ρ top control-ratio | ρ top1-vs-uniform |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(conf_lines)}

Interpretation: the route works as a **target selector**, but the current confidence fields (`dominance_margin`, `visual_minus_control`, `top1_vs_uniform`) are not a reliable calibrated estimate of how much a generated AD will improve. That is a new negative/guardrail: do not present dominance margin as a probability-of-success until a better calibration model exists.

Artifacts: `route_confidence_*.csv`, `route_confidence_metrics_*.csv`.

## Finding 4 — matched surgical gains are concentrated in scene/spatial and visual-form targets; non-scene types are underpowered

From `tribe_surgical_adqa_perq.csv`, matched-question deltas by TRIBE type:

| TRIBE type | n matched qs | mean delta | wins/losses/ties | one-sided sign p |
|---|---:|---:|---:|---:|
{chr(10).join(type_lines)}

Interpretation: the current positive surgical result is mostly a **scene/spatial + visual-form** story. Action/body/face/object subclaims need more examples before they should be described as equally validated.

Artifact: `surgical_matched_delta_by_tribe_type.csv`.

## Finding 5 — tensor manifest is mostly healthy, with specific caveats to quarantine/mention

Tensor manifest audit:

- Manifest rows: {tensor['manifest_rows']}
- JSON files: {tensor['json_files']}
- Missing JSON files: {len(tensor['missing_json_files'])}
- Extra JSON files: {len(tensor['extra_json_files'])}
- Bad shape count: {tensor['bad_shape_count']}
- `audio_only_ok != True`: {tensor['audio_only_bad_count']}
- `alignment_cosine <= 0.5`: {tensor['alignment_le_0_5_count']} clips — {', '.join(tensor['alignment_le_0_5_keys']) if tensor['alignment_le_0_5_keys'] else 'none'}
- P_AV vs P_A temporal length mismatches: {tensor['av_a_temporal_mismatch_count']}
- JSON/manifest value mismatches: {tensor['json_manifest_mismatch_count']}

Interpretation: the cached tensor-derived metadata is usable, but two zero/low alignment clips and frequent one-TR AV/A length mismatches should be explicitly treated as data-quality caveats rather than silently hidden.

Artifact: `tensor_health_rows.csv`.

## What changed in the research plan

1. Prioritize external low-gap early-exit as a **conservative review-priority** experiment, not an AD omission claim yet.
2. Add a reviewer-defense sentence: in-bench TRIBE AUC=1.00 has family-wise p≈{fmt(fs['exact_familywise_maxstat_p'], 3)} across tested features, so external OOD triage should carry more weight.
3. Do not expose route confidence as calibrated probability in the UI yet.
4. Split matched-target claims by type: scene/spatial is best-supported; action/face/object need targeted data generation.
5. Run a small data-quality quarantine before any next TRIBE tensor-derived paper figure.
"""
    REPORT.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {
        "tensor_health": tensor_health_audit(),
        "feature_selection_null": feature_selection_null(),
        "external_low_gap": external_low_gap_and_failure(),
        "route_confidence": route_confidence_and_controls(),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    write_report(results)
    print(json.dumps({
        "summary": str(OUT_DIR / "summary.json"),
        "report": str(REPORT),
        "feature_selection_best": results["feature_selection_null"]["observed_best_feature"],
        "familywise_p": results["feature_selection_null"]["exact_familywise_maxstat_p"],
        "external_adqa_fail_count": results["external_low_gap"]["adqa_fail_count"],
        "tensor_alignment_low_count": results["tensor_health"]["alignment_le_0_5_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
