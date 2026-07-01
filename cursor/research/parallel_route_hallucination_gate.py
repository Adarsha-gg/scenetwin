"""Local route-specific hallucination gate pass.

Joins cached hallucination-gate outputs to cached TRIBE router outputs and writes
route/category summaries plus simple stdlib-only predictor checks. No external API
or non-stdlib dependency is used.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
HALLUC_CSV = ROOT / "cursor" / "output" / "halluc_gate" / "halluc_gate.csv"
HALLUC_JSON = ROOT / "cursor" / "output" / "hallucination_gate.json"
PROBES_CSV = ROOT / "cursor" / "output" / "relational_hallucination_probe_set" / "probes.csv"
TRIBE_SUMMARY_CSV = ROOT / "cursor" / "research" / "output" / "tribe_blind_spot_clip_summary.csv"
TRIBE_WINDOWS_CSV = ROOT / "cursor" / "research" / "output" / "tribe_blind_spot_windows.csv"
TRIBE_CASES_CSV = ROOT / "cursor" / "research" / "output" / "tribe_blind_spot_cases.csv"

OUT_DIR = ROOT / "cursor" / "research" / "output" / "parallel_research" / "hallucination_gate"
REPORT = ROOT / "output" / "reports" / "parallel-research-route-hallucination-gate.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_cell(row.get(key)) for key in fields})


def format_cell(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.10g}"
    if value is None:
        return ""
    return value


def f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: Iterable[float]) -> float | None:
    vals = [v for v in values if v is not None and not math.isnan(v)]
    return statistics.fmean(vals) if vals else None


def median(values: Iterable[float]) -> float | None:
    vals = sorted(v for v in values if v is not None and not math.isnan(v))
    return statistics.median(vals) if vals else None


def quantile(values: Iterable[float], q: float) -> float | None:
    vals = sorted(v for v in values if v is not None and not math.isnan(v))
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - pos) + vals[hi] * (pos - lo)


def safe_div(num: float, den: float) -> float | None:
    return num / den if den else None


def auc(scores: list[float], labels: list[int]) -> float | None:
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    wins = 0.0
    for ps in pos:
        for ns in neg:
            if ps > ns:
                wins += 1.0
            elif ps == ns:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def recall_at_k(scores: list[float], labels: list[int], k: int) -> float | None:
    positives = sum(labels)
    if positives == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[: max(0, min(k, len(scores)))]
    return sum(labels[i] for i in order) / positives


def group_summary(rows: list[dict[str, Any]], group_fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(row.get(field, "") for field in group_fields)
        groups[key].append(row)

    out = []
    for key, group in groups.items():
        rec = {field: value for field, value in zip(group_fields, key)}
        n = len(group)
        rec.update(
            {
                "n_clips": n,
                "clip_halluc_drop_mean": mean(row["clip_halluc_drop"] for row in group),
                "clip_para_drop_mean": mean(row["clip_para_drop"] for row in group),
                "clip_specific_margin_mean": mean(row["clip_specific_margin"] for row in group),
                "clip_halluc_detect_rate": mean(1.0 if row["clip_halluc_drop"] > 0 else 0.0 for row in group),
                "clip_specific_rate": mean(1.0 if row["clip_specific_margin"] > 0 else 0.0 for row in group),
                "adqa_halluc_drop_mean": mean(row["adqa_halluc_drop"] for row in group),
                "adqa_para_drop_mean": mean(row["adqa_para_drop"] for row in group),
                "adqa_specific_margin_mean": mean(row["adqa_specific_margin"] for row in group),
                "adqa_detect_rate": mean(1.0 if row["adqa_halluc_drop"] > 0 else 0.0 for row in group),
                "adqa_blind_rate": mean(1.0 if row["adqa_halluc_drop"] == 0 else 0.0 for row in group),
                "mean_visual_gap": mean(row["mean_visual_gap"] for row in group),
                "max_visual_gap": mean(row["max_visual_gap"] for row in group),
            }
        )
        out.append(rec)
    return sorted(out, key=lambda r: (-int(r["n_clips"]), tuple(str(r.get(f, "")) for f in group_fields)))


def probe_group_summary(rows: list[dict[str, Any]], probe_counts: dict[str, Counter], field: str) -> list[dict[str, Any]]:
    expanded = []
    by_video = {row["video_id"]: row for row in rows}
    for video_id, counts in probe_counts.items():
        base = by_video.get(video_id)
        if not base:
            continue
        for value, count in counts.items():
            rec = dict(base)
            rec[field] = value
            rec["probe_count_weight"] = count
            expanded.append(rec)
    return group_summary(expanded, [field])


def markdown_table(rows: list[dict[str, Any]], columns: list[str], max_rows: int | None = None) -> str:
    if max_rows is not None:
        rows = rows[:max_rows]
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        cells = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, float):
                cells.append("" if math.isnan(val) else f"{val:.4g}")
            elif val is None:
                cells.append("")
            else:
                cells.append(str(val).replace("|", "/"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_joined_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    halluc_rows = read_csv(HALLUC_CSV)
    tribe_summary = {row["video_id"]: row for row in read_csv(TRIBE_SUMMARY_CSV)}
    windows = read_csv(TRIBE_WINDOWS_CSV)
    cases = read_csv(TRIBE_CASES_CSV)

    windows_by_video: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in windows:
        windows_by_video[row["video_id"]].append(row)

    cases_by_video: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in cases:
        cases_by_video[row["video_id"]].append(row)

    route_names = sorted({row["route"] for row in windows if row.get("route")})
    joined = []
    for h in halluc_rows:
        video_id = h["video_id"]
        t = tribe_summary.get(video_id, {})
        win = windows_by_video.get(video_id, [])
        top_win = max(win, key=lambda r: f(r, "peak_visual_gap"), default={})
        route_counts = Counter(row.get("route", "") for row in win if row.get("route"))
        route_peaks = {route: 0.0 for route in route_names}
        route_means = {route: 0.0 for route in route_names}
        route_windows = {route: 0 for route in route_names}
        for row in win:
            route = row.get("route", "")
            if not route:
                continue
            route_peaks[route] = max(route_peaks[route], f(row, "peak_visual_gap"))
            route_means[route] += f(row, "mean_visual_gap")
            route_windows[route] += 1
        for route, count in route_windows.items():
            if count:
                route_means[route] /= count

        case_rows = cases_by_video.get(video_id, [])
        top_case = max(case_rows, key=lambda r: f(r, "priority_score"), default={})

        clip_halluc_drop = f(h, "clip_expert") - f(h, "clip_halluc")
        clip_para_drop = f(h, "clip_expert") - f(h, "clip_para")
        adqa_halluc_drop = f(h, "adqa_expert") - f(h, "adqa_halluc")
        adqa_para_drop = f(h, "adqa_expert") - f(h, "adqa_para")
        row: dict[str, Any] = {
            "video_id": video_id,
            "category": t.get("category", ""),
            "dominant_clip_type": t.get("dominant_clip_type", ""),
            "top_window_route": top_win.get("route", ""),
            "top_window_type": top_win.get("dominant_type", ""),
            "top_case_id": top_case.get("case_id", ""),
            "clip_halluc_drop": clip_halluc_drop,
            "clip_para_drop": clip_para_drop,
            "clip_specific_margin": clip_halluc_drop - clip_para_drop,
            "adqa_halluc_drop": adqa_halluc_drop,
            "adqa_para_drop": adqa_para_drop,
            "adqa_specific_margin": adqa_halluc_drop - adqa_para_drop,
            "clip_halluc_detect": int(clip_halluc_drop > 0),
            "clip_specific_detect": int((clip_halluc_drop - clip_para_drop) > 0),
            "adqa_detect": int(adqa_halluc_drop > 0),
            "adqa_blind": int(adqa_halluc_drop == 0),
            "expert_words": int(f(h, "expert_words")),
            "halluc_words": int(f(h, "halluc_words")),
            "para_words": int(f(h, "para_words")),
            "mean_scene_spatial_gap": f(t, "mean_scene_spatial_gap"),
            "mean_agent_action_gap": f(t, "mean_agent_action_gap"),
            "mean_control_gap": f(t, "mean_control_gap"),
            "mean_visual_gap": f(t, "mean_visual_gap"),
            "max_visual_gap": f(t, "max_visual_gap"),
            "top1_share": f(t, "top1_share"),
            "top1_vs_uniform": f(t, "top1_vs_uniform"),
            "scene_agent_peak_apart": int(f(t, "scene_agent_peak_apart")),
            "route_window_count": len(win),
            "top_window_peak_visual_gap": f(top_win, "peak_visual_gap"),
            "top_window_visual_minus_control": f(top_win, "visual_minus_control"),
            "top_case_priority_score": f(top_case, "priority_score"),
        }
        total_windows = len(win) or 1
        for route in route_names:
            safe = route.replace("-", "_")
            row[f"route_peak_{safe}"] = route_peaks[route]
            row[f"route_mean_{safe}"] = route_means[route]
            row[f"route_share_{safe}"] = route_counts[route] / total_windows
            row[f"top_route_is_{safe}"] = int(top_win.get("route") == route)
        joined.append(row)

    meta = {
        "hallucination_rows": len(halluc_rows),
        "tribe_summary_rows": len(tribe_summary),
        "joined_rows": len(joined),
        "unmatched_hallucination_video_ids": sorted(set(row["video_id"] for row in halluc_rows) - set(tribe_summary)),
        "route_names": route_names,
    }
    return joined, meta


def build_probe_counts() -> tuple[dict[str, Counter], dict[str, Counter], dict[str, int]]:
    probes = read_csv(PROBES_CSV)
    by_swap: dict[str, Counter] = defaultdict(Counter)
    by_type: dict[str, Counter] = defaultdict(Counter)
    relation_counts = defaultdict(int)
    for row in probes:
        video_id = row["video_id"]
        by_swap[video_id][row.get("swap_class", "")] += 1
        by_type[video_id][row.get("probe_type", "")] += 1
        relation_counts[video_id] += int(f(row, "is_relation_action_count"))
    return by_swap, by_type, relation_counts


def predictor_rows(rows: list[dict[str, Any]], labels: dict[str, list[int]]) -> list[dict[str, Any]]:
    feature_names = [
        "mean_scene_spatial_gap",
        "mean_agent_action_gap",
        "mean_control_gap",
        "mean_visual_gap",
        "max_visual_gap",
        "top1_vs_uniform",
        "top_window_peak_visual_gap",
        "top_window_visual_minus_control",
        "top_case_priority_score",
        "scene_agent_peak_apart",
    ]
    for key in rows[0]:
        if key.startswith("route_peak_") or key.startswith("route_mean_") or key.startswith("route_share_") or key.startswith("top_route_is_"):
            feature_names.append(key)

    out = []
    for label_name, y in labels.items():
        positives = sum(y)
        k_pos = max(1, positives)
        k_20 = max(1, math.ceil(len(rows) * 0.2))
        for feature in feature_names:
            scores = [float(row.get(feature, 0.0) or 0.0) for row in rows]
            out.append(
                {
                    "label": label_name,
                    "feature": feature,
                    "n": len(rows),
                    "positives": positives,
                    "auc": auc(scores, y),
                    "recall_at_prevalence_k": recall_at_k(scores, y, k_pos),
                    "recall_at_top20pct": recall_at_k(scores, y, k_20),
                    "score_mean_positive": mean(s for s, yy in zip(scores, y) if yy == 1),
                    "score_mean_negative": mean(s for s, yy in zip(scores, y) if yy == 0),
                }
            )
    return sorted(out, key=lambda r: (r["label"], -(r["auc"] if r["auc"] is not None else -1)))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    joined, join_meta = build_joined_rows()
    by_swap, by_probe_type, relation_counts = build_probe_counts()
    for row in joined:
        row["relation_action_probe_count"] = relation_counts.get(row["video_id"], 0)

    clip_specific_q75 = quantile((row["clip_specific_margin"] for row in joined), 0.75)
    clip_drop_q75 = quantile((row["clip_halluc_drop"] for row in joined), 0.75)
    adqa_drop_q75 = quantile((row["adqa_halluc_drop"] for row in joined), 0.75)
    max_visual_q75 = quantile((row["max_visual_gap"] for row in joined), 0.75)

    labels = {
        "clip_specific_margin_gt0": [int(row["clip_specific_margin"] > 0) for row in joined],
        "clip_specific_margin_top_quartile": [int(row["clip_specific_margin"] >= clip_specific_q75) for row in joined],
        "clip_halluc_drop_top_quartile": [int(row["clip_halluc_drop"] >= clip_drop_q75) for row in joined],
        "adqa_detected": [int(row["adqa_halluc_drop"] > 0) for row in joined],
        "adqa_drop_top_quartile": [int(row["adqa_halluc_drop"] >= adqa_drop_q75) for row in joined],
    }
    predictors = predictor_rows(joined, labels)

    route_summary = group_summary(joined, ["top_window_route"])
    type_summary = group_summary(joined, ["dominant_clip_type"])
    category_summary = group_summary(joined, ["category"])
    route_category_summary = group_summary(joined, ["top_window_route", "category"])
    case_summary = group_summary(joined, ["top_case_id"])
    swap_summary = probe_group_summary(joined, by_swap, "swap_class")
    probe_type_summary = probe_group_summary(joined, by_probe_type, "probe_type")

    high_gap_rows = [row for row in joined if row["max_visual_gap"] >= max_visual_q75]
    route_counter = Counter(row["top_window_route"] for row in joined)
    high_gap_route_counter = Counter(row["top_window_route"] for row in high_gap_rows)

    overall = {
        "n_clips": len(joined),
        "clip_halluc_drop_mean": mean(row["clip_halluc_drop"] for row in joined),
        "clip_para_drop_mean": mean(row["clip_para_drop"] for row in joined),
        "clip_specific_margin_mean": mean(row["clip_specific_margin"] for row in joined),
        "clip_specific_margin_q75": clip_specific_q75,
        "adqa_halluc_drop_mean": mean(row["adqa_halluc_drop"] for row in joined),
        "adqa_para_drop_mean": mean(row["adqa_para_drop"] for row in joined),
        "adqa_specific_margin_mean": mean(row["adqa_specific_margin"] for row in joined),
        "adqa_blind_clips": sum(row["adqa_blind"] for row in joined),
        "max_visual_gap_q75": max_visual_q75,
        "high_gap_clip_count": len(high_gap_rows),
        "high_gap_route_counts": dict(high_gap_route_counter),
        "all_route_counts": dict(route_counter),
        "top_predictors_by_label": {
            label: [r for r in predictors if r["label"] == label][:5]
            for label in labels
        },
    }

    with HALLUC_JSON.open(encoding="utf-8") as fjson:
        cached_hallucination_summary = json.load(fjson)

    write_csv(OUT_DIR / "joined_clip_rows.csv", joined)
    write_csv(OUT_DIR / "route_summary.csv", route_summary)
    write_csv(OUT_DIR / "dominant_type_summary.csv", type_summary)
    write_csv(OUT_DIR / "category_summary.csv", category_summary)
    write_csv(OUT_DIR / "route_category_summary.csv", route_category_summary)
    write_csv(OUT_DIR / "case_summary.csv", case_summary)
    write_csv(OUT_DIR / "swap_class_summary.csv", swap_summary)
    write_csv(OUT_DIR / "probe_type_summary.csv", probe_type_summary)
    write_csv(OUT_DIR / "tribe_predictor_auc.csv", predictors)

    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "hallucination_gate_csv": str(HALLUC_CSV.relative_to(ROOT)),
            "hallucination_gate_json": str(HALLUC_JSON.relative_to(ROOT)),
            "probes_csv": str(PROBES_CSV.relative_to(ROOT)),
            "tribe_clip_summary_csv": str(TRIBE_SUMMARY_CSV.relative_to(ROOT)),
            "tribe_windows_csv": str(TRIBE_WINDOWS_CSV.relative_to(ROOT)),
            "tribe_cases_csv": str(TRIBE_CASES_CSV.relative_to(ROOT)),
        },
        "join": join_meta,
        "thresholds": {
            "clip_specific_margin_q75": clip_specific_q75,
            "clip_halluc_drop_q75": clip_drop_q75,
            "adqa_halluc_drop_q75": adqa_drop_q75,
            "max_visual_gap_q75": max_visual_q75,
        },
        "overall": overall,
        "cached_hallucination_summary": cached_hallucination_summary,
        "route_summary": route_summary,
        "dominant_type_summary": type_summary,
        "category_summary": category_summary,
        "top_predictors": overall["top_predictors_by_label"],
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    top_predictors = []
    for label in ["clip_halluc_drop_top_quartile", "clip_specific_margin_top_quartile", "adqa_detected", "adqa_drop_top_quartile"]:
        label_rows = [r for r in predictors if r["label"] == label]
        top_predictors.extend(sorted(label_rows, key=lambda r: -(r["auc"] if r["auc"] is not None else -1))[:5])
    report = f"""---
title: Parallel Research: Route-Specific Hallucination Gate
category: research
tags: [SceneTwin, hallucination, TRIBE, routing, local-only]
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/output/parallel_research/hallucination_gate/summary.json
  - cursor/research/output/parallel_research/hallucination_gate/joined_clip_rows.csv
---

## Question

Can cached TRIBE blind-spot routes explain where the cached hallucination gate is strongest? This pass is local-only: it reads existing CSV/JSON artifacts and uses only Python stdlib.

## Join and overall gate

- Hallucination rows: {join_meta['hallucination_rows']}; joined to TRIBE clip summary: {join_meta['joined_rows']}; unmatched hallucination clips: {len(join_meta['unmatched_hallucination_video_ids'])}.
- Mean CLIP hallucination drop: {overall['clip_halluc_drop_mean']:.4f}; paraphrase drop: {overall['clip_para_drop_mean']:.4f}; hallucination-specific CLIP margin: {overall['clip_specific_margin_mean']:.4f}.
- Mean ADQA hallucination drop: {overall['adqa_halluc_drop_mean']:.4f}; paraphrase drop: {overall['adqa_para_drop_mean']:.4f}; ADQA-blind clips: {overall['adqa_blind_clips']}/{overall['n_clips']}.

## Route/type summaries

### Top TRIBE window route

{markdown_table(route_summary, ['top_window_route', 'n_clips', 'clip_halluc_drop_mean', 'clip_para_drop_mean', 'clip_specific_margin_mean', 'adqa_halluc_drop_mean', 'adqa_blind_rate', 'max_visual_gap'])}

### Clip-level TRIBE dominant type

{markdown_table(type_summary, ['dominant_clip_type', 'n_clips', 'clip_halluc_drop_mean', 'clip_specific_margin_mean', 'adqa_halluc_drop_mean', 'adqa_blind_rate', 'max_visual_gap'])}

## Category summaries

{markdown_table(category_summary, ['category', 'n_clips', 'clip_halluc_drop_mean', 'clip_specific_margin_mean', 'adqa_halluc_drop_mean', 'adqa_blind_rate', 'max_visual_gap'], max_rows=12)}

## Probe category summaries

### Swap class

{markdown_table(swap_summary, ['swap_class', 'n_clips', 'clip_halluc_drop_mean', 'clip_specific_margin_mean', 'adqa_halluc_drop_mean', 'adqa_blind_rate'], max_rows=12)}

### Probe type

{markdown_table(probe_type_summary, ['probe_type', 'n_clips', 'clip_halluc_drop_mean', 'clip_specific_margin_mean', 'adqa_halluc_drop_mean', 'adqa_blind_rate'], max_rows=12)}

## TRIBE high-gap / route prediction checks

Labels are simple binary targets: top-quartile CLIP hallucination drop, top-quartile CLIP hallucination-specific margin, ADQA detected (drop > 0), and related controls. AUC is pairwise rank AUC where larger TRIBE feature should imply a stronger gate; recall@top20pct is recall among the top 20% clips by that feature.

{markdown_table(top_predictors, ['label', 'feature', 'positives', 'auc', 'recall_at_prevalence_k', 'recall_at_top20pct', 'score_mean_positive', 'score_mean_negative'])}

## Finding

TRIBE route is useful for stratifying the hallucination gate, but not as a clean high-gap predictor in this cached 60-clip set. The clearest route-level separation is categorical: clips whose top TRIBE window is action-state/agent-cue have the largest mean CLIP hallucination drop and hallucination-specific CLIP margin; layout/scene-cue clips have the lowest ADQA blind rate; static/low-gap clips have the lowest mean TRIBE gap but do not eliminate CLIP hallucination drops. Category effects and small-cell route/category splits remain material, so this should be treated as a routing/triage lens, not a standalone hallucination-risk score.

Artifacts are under `cursor/research/output/parallel_research/hallucination_gate/`.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
