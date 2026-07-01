#!/usr/bin/env python3
"""Local-only EXPERIMENTS 5-7 pass for TRIBE access-surface triage.

Reads cached router, worksheet, and external ensemble outputs. Writes review-budget
curves, low-gap early-exit summaries, route/surface counts, and reviewer-ready top
cases without external API calls.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cursor" / "research" / "output" / "parallel_research" / "access_surface"
REPORT = ROOT / "output" / "reports" / "parallel-research-access-surface-triage.md"

BUDGETS = [0.05, 0.10, 0.20, 0.25, 1 / 3, 0.50]

# Deterministic local mapping grounded in the existing router vocabulary and
# Access Surface OS page. This is a counting/prep map, not a new product claim.
CASE_SURFACE = {
    "low_gap_skip": {
        "access_surface": "static_ad_low_pressure",
        "surface_family": "static_ad",
        "review_action": "Defer expensive review unless another safety/OCR/identity gate fires.",
        "validation_target": "Confirm no safety-critical visual text, identity, or task step is lost in the suggested low-gap window.",
    },
    "scene_layout_replay": {
        "access_surface": "layout_replay_or_keyframe",
        "surface_family": "defer_replay",
        "review_action": "Review spatial layout, key objects, setting, and camera/geography in the peak window.",
        "validation_target": "Does the AD or replay surface preserve where things are and how the scene is arranged?",
    },
    "agent_action_cue": {
        "access_surface": "action_state_or_agent_cue",
        "surface_family": "concise_cue",
        "review_action": "Review who/what moved, state changes, tool use, and object interaction in the peak window.",
        "validation_target": "Does the AD preserve the agent/action state enough to answer a frame-grounded question?",
    },
    "moment_level_authoring": {
        "access_surface": "peak_window_review_card",
        "surface_family": "creator_qc",
        "review_action": "Spend scarce reviewer/authoring budget on the named moment rather than the whole clip.",
        "validation_target": "Can a reviewer identify the missing moment and propose a concise fix?",
    },
    "dynamic_type_shift": {
        "access_surface": "segmented_scene_action_surface",
        "surface_family": "defer_replay",
        "review_action": "Check whether separate scene/layout and action/state treatments are needed across windows.",
        "validation_target": "Does a single global AD miss a later/earlier route-type shift?",
    },
    "audio_language_confound_check": {
        "access_surface": "evidence_sidecar_qc",
        "surface_family": "creator_qc",
        "review_action": "Treat as an audio/language anomaly; inspect ASR/control signal before visual-AD decisions.",
        "validation_target": "Is the apparent visual need actually an audio/transcript/control artifact?",
    },
}

ROUTE_SURFACE = {
    "static_ad_ok_low_gap": {
        "access_surface": "static_ad_low_pressure",
        "surface_family": "static_ad",
        "review_action": "Use normal scoring; avoid human/frontier review unless other gates fire.",
    },
    "layout_replay_or_scene_cue": {
        "access_surface": "layout_replay_or_keyframe",
        "surface_family": "defer_replay",
        "review_action": "Route to layout cue, keyframe, or replay surface.",
    },
    "action_state_or_agent_cue": {
        "access_surface": "action_state_or_agent_cue",
        "surface_family": "concise_cue",
        "review_action": "Route to concise who-does-what/action-state cue.",
    },
}


def read_csv(rel: str | Path) -> list[dict[str, str]]:
    path = ROOT / rel if isinstance(rel, str) else rel
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        if not fields:
            f.write("")
            return
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value, default=math.nan) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def avg(values) -> float:
    vals = [v for v in values if finite(v)]
    return mean(vals) if vals else math.nan


def fmt(value, digits=3) -> str:
    if not finite(value):
        return "n/a"
    return f"{value:.{digits}f}"


def full_order(vals: list[float]) -> int:
    return int(all(finite(v) for v in vals) and vals[0] < vals[1] < vals[2])


def external_failure_rows() -> dict[str, dict]:
    scores = read_csv("cursor/output/external_ensemble_eval.csv")
    by_vid: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    categories: dict[str, str] = {}
    for row in scores:
        by_vid[row["video_id"]][row["tier"]] = row
        categories[row["video_id"]] = row.get("category", "")

    out: dict[str, dict] = {}
    for vid, tiers in by_vid.items():
        needed = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]
        if not all(t in tiers for t in needed):
            continue

        def vals(col: str) -> list[float]:
            return [fnum(tiers[t].get(col)) for t in needed]

        adqa_full = full_order(vals("adqa_score"))
        clip_full = full_order(vals("clip_top3"))
        ensemble_full = full_order(vals("ensemble_mean_clip_top3"))
        out[vid] = {
            "video_id": vid,
            "category": categories.get(vid, ""),
            "adqa_fail": 1 - adqa_full,
            "clip_fail": 1 - clip_full,
            "ensemble_fail": 1 - ensemble_full,
            "adqa_full_order": adqa_full,
            "clip_full_order": clip_full,
            "ensemble_full_order": ensemble_full,
        }
    return out


def joined_external_clip_rows(fail_by_vid: dict[str, dict]) -> list[dict]:
    summaries = read_csv("cursor/research/output/tribe_blind_spot_clip_summary.csv")
    rows = []
    for row in summaries:
        if row.get("corpus") != "external" or row.get("video_id") not in fail_by_vid:
            continue
        fail = fail_by_vid[row["video_id"]]
        rows.append(
            {
                "video_id": row["video_id"],
                "clip_key": row.get("clip_key", ""),
                "category": row.get("category", fail.get("category", "")),
                "mean_visual_gap": fnum(row.get("mean_visual_gap")),
                "max_visual_gap": fnum(row.get("max_visual_gap")),
                "top1_vs_uniform": fnum(row.get("top1_vs_uniform")),
                "dominant_clip_type": row.get("dominant_clip_type", ""),
                "top_windows": row.get("top_windows", ""),
                **fail,
            }
        )
    return rows


def budget_curves(rows: list[dict]) -> list[dict]:
    curves = []
    features = ["mean_visual_gap", "max_visual_gap", "top1_vs_uniform"]
    targets = ["adqa_fail", "ensemble_fail", "clip_fail"]
    n = len(rows)
    for feature in features:
        sorted_rows = sorted(rows, key=lambda r: r[feature] if finite(r[feature]) else -1e9, reverse=True)
        for target in targets:
            total_pos = sum(int(r[target]) for r in rows)
            for budget in BUDGETS:
                k = max(1, round(n * budget))
                top = sorted_rows[:k]
                hits = sum(int(r[target]) for r in top)
                curves.append(
                    {
                        "queue": feature,
                        "target": target,
                        "budget_frac": budget,
                        "k": k,
                        "hits": hits,
                        "total_pos": total_pos,
                        "recall": hits / total_pos if total_pos else math.nan,
                        "precision": hits / k if k else math.nan,
                        "random_expected_recall": budget,
                    }
                )
    return curves


def case_priority_budget(fail_by_vid: dict[str, dict]) -> list[dict]:
    cases = read_csv("cursor/research/output/tribe_blind_spot_cases.csv")
    # One queue row per external video: take the highest-priority non-low-gap case.
    best: dict[str, dict] = {}
    for row in cases:
        vid = row.get("video_id", "")
        if row.get("corpus") != "external" or vid not in fail_by_vid or row.get("case_id") == "low_gap_skip":
            continue
        score = fnum(row.get("priority_score"), -math.inf)
        if vid not in best or score > fnum(best[vid].get("priority_score"), -math.inf):
            best[vid] = row
    queue = []
    for vid, row in best.items():
        queue.append({**row, **fail_by_vid[vid], "priority_score_float": fnum(row.get("priority_score"))})
    queue.sort(key=lambda r: r["priority_score_float"], reverse=True)

    curves = []
    for target in ["adqa_fail", "ensemble_fail", "clip_fail"]:
        total_pos = sum(int(f[target]) for f in fail_by_vid.values())
        for budget in BUDGETS:
            k = max(1, round(len(fail_by_vid) * budget))
            top = queue[: min(k, len(queue))]
            hits = sum(int(r[target]) for r in top)
            curves.append(
                {
                    "queue": "case_priority_non_low_gap",
                    "target": target,
                    "budget_frac": budget,
                    "k": k,
                    "queue_rows_available": len(queue),
                    "hits": hits,
                    "total_pos": total_pos,
                    "recall": hits / total_pos if total_pos else math.nan,
                    "precision": hits / len(top) if top else math.nan,
                    "random_expected_recall": budget,
                }
            )
    return curves


def low_gap_early_exit(rows: list[dict]) -> list[dict]:
    out = []
    for feature in ["max_visual_gap", "mean_visual_gap"]:
        sorted_low = sorted(rows, key=lambda r: r[feature] if finite(r[feature]) else 1e9)
        n = len(sorted_low)
        for frac in [0.10, 0.20, 0.25, 1 / 3, 0.50]:
            k = max(1, round(n * frac))
            subsets = [("low", sorted_low[:k]), ("high", sorted_low[-k:])]
            for label, subset in subsets:
                out.append(
                    {
                        "gap_feature": feature,
                        "gap_group": label,
                        "frac": frac,
                        "n": len(subset),
                        "adqa_fail_rate": avg([int(r["adqa_fail"]) for r in subset]),
                        "ensemble_fail_rate": avg([int(r["ensemble_fail"]) for r in subset]),
                        "clip_fail_rate": avg([int(r["clip_fail"]) for r in subset]),
                        "adqa_ensemble_full_order_agreement": avg(
                            [int(r["adqa_full_order"] == r["ensemble_full_order"]) for r in subset]
                        ),
                        "clip_ensemble_full_order_agreement": avg(
                            [int(r["clip_full_order"] == r["ensemble_full_order"]) for r in subset]
                        ),
                        "review_budget_saved_if_early_exit": frac if label == "low" else 0,
                    }
                )
    return out


def route_counts() -> tuple[list[dict], list[dict]]:
    windows = read_csv("cursor/research/output/tribe_blind_spot_windows.csv")
    route_counter = Counter()
    route_dom_counter = Counter()
    for row in windows:
        route = row.get("route", "")
        route_counter[("all", route)] += 1
        route_counter[(row.get("corpus", ""), route)] += 1
        route_dom_counter[("all", route, row.get("dominant_type", ""))] += 1
        route_dom_counter[(row.get("corpus", ""), route, row.get("dominant_type", ""))] += 1
    route_rows = [
        {"corpus": corpus, "route": route, "windows": count}
        for (corpus, route), count in sorted(route_counter.items(), key=lambda kv: (kv[0][0] != "all", kv[0][0], kv[0][1]))
    ]
    route_dom_rows = [
        {"corpus": corpus, "route": route, "dominant_type": dom, "windows": count}
        for (corpus, route, dom), count in sorted(route_dom_counter.items(), key=lambda kv: (kv[0][0] != "all", kv[0][0], kv[0][1], kv[0][2]))
    ]
    return route_rows, route_dom_rows


def surface_mapping_counts() -> tuple[list[dict], list[dict]]:
    cases = read_csv("cursor/research/output/tribe_blind_spot_cases.csv")
    windows = read_csv("cursor/research/output/tribe_blind_spot_windows.csv")
    case_counts = Counter()
    for row in cases:
        mapping = CASE_SURFACE.get(row.get("case_id", ""), {})
        surface = mapping.get("access_surface", "unmapped")
        family = mapping.get("surface_family", "unmapped")
        case_counts[("all", row.get("case_id", ""), surface, family)] += 1
        case_counts[(row.get("corpus", ""), row.get("case_id", ""), surface, family)] += 1
    case_rows = [
        {"corpus": corpus, "case_id": case_id, "access_surface": surface, "surface_family": family, "cases": count}
        for (corpus, case_id, surface, family), count in sorted(case_counts.items(), key=lambda kv: (kv[0][0] != "all", kv[0][0], kv[0][1]))
    ]

    window_counts = Counter()
    for row in windows:
        mapping = ROUTE_SURFACE.get(row.get("route", ""), {})
        surface = mapping.get("access_surface", "unmapped")
        family = mapping.get("surface_family", "unmapped")
        window_counts[("all", row.get("route", ""), surface, family)] += 1
        window_counts[(row.get("corpus", ""), row.get("route", ""), surface, family)] += 1
    window_rows = [
        {"corpus": corpus, "route": route, "access_surface": surface, "surface_family": family, "windows": count}
        for (corpus, route, surface, family), count in sorted(window_counts.items(), key=lambda kv: (kv[0][0] != "all", kv[0][0], kv[0][1]))
    ]
    return case_rows, window_rows


def reviewer_ready_cases(fail_by_vid: dict[str, dict]) -> list[dict]:
    worksheet = read_csv("cursor/research/output/new_findings_round3/review_worksheet_rows.csv")
    windows = read_csv("cursor/research/output/tribe_blind_spot_windows.csv")
    by_vid: dict[str, list[dict]] = defaultdict(list)
    for row in windows:
        by_vid[row.get("video_id", "")].append(row)

    out = []
    for row in worksheet[:25]:
        vid = row.get("video_id", "")
        mapping = CASE_SURFACE.get(row.get("case_id", ""), {})
        topwins = sorted(by_vid.get(vid, []), key=lambda r: fnum(r.get("peak_visual_gap"), -math.inf), reverse=True)[:3]
        f = fail_by_vid.get(vid, {})
        adqa_fail = row.get("adqa_fail", "") if row.get("adqa_fail", "") != "" else f.get("adqa_fail", "")
        ensemble_fail = row.get("ensemble_fail", "") if row.get("ensemble_fail", "") != "" else f.get("ensemble_fail", "")
        top_window_summary = "; ".join(
            f"{fnum(w.get('start_s')):.1f}-{fnum(w.get('end_s')):.1f}s {w.get('dominant_type')} route={w.get('route')} peak={fnum(w.get('peak_visual_gap')):.3f}"
            for w in topwins
        )
        out.append(
            {
                "rank": row.get("rank", ""),
                "clip_key": row.get("clip_key", ""),
                "corpus": row.get("corpus", ""),
                "video_id": vid,
                "category": row.get("category", ""),
                "case_id": row.get("case_id", ""),
                "priority_score": row.get("priority_score", ""),
                "suggested_window": row.get("window", ""),
                "access_surface": mapping.get("access_surface", "unmapped"),
                "surface_family": mapping.get("surface_family", "unmapped"),
                "review_action": mapping.get("review_action", ""),
                "validation_target": mapping.get("validation_target", ""),
                "why": row.get("why", ""),
                "adqa_fail": adqa_fail,
                "ensemble_fail": ensemble_fail,
                "top_router_windows": top_window_summary,
                "reviewer_pass_fail_column": "blank_for_manual_or_vlm_review",
                "reviewer_notes_column": "blank_for_evidence_notes",
            }
        )
    return out


def write_reviewer_markdown(rows: list[dict]) -> None:
    lines = [
        "---",
        "title: Access Surface Reviewer-Ready Top Cases",
        "category: research",
        "created: 2026-06-23",
        "updated: 2026-06-23",
        "---",
        "",
        "# Access Surface Reviewer-Ready Top Cases",
        "",
        "Local-only enrichment of the round-3 top-25 worksheet. No external API/human review was run; blank pass/fail columns are prepared for the next validation step.",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## {row['rank']}. {row['video_id']} — {row['case_id']}",
                "",
                f"- Corpus/category: `{row['corpus']}` / `{row['category']}`",
                f"- Priority score: `{fmt(fnum(row['priority_score']))}`",
                f"- Suggested window: `{row['suggested_window']}`",
                f"- Access surface: `{row['access_surface']}` (`{row['surface_family']}`)",
                f"- Review action: {row['review_action']}",
                f"- Validation target: {row['validation_target']}",
                f"- Existing external fail flags: ADQA `{row['adqa_fail']}`, ensemble `{row['ensemble_fail']}`",
                f"- Why queued: {row['why']}",
                f"- Top router windows: {row['top_router_windows'] or 'n/a'}",
                "- Reviewer pass/fail: `_______`",
                "- Evidence notes: `_______`",
                "",
            ]
        )
    (OUT / "top25_reviewer_cases.md").write_text("\n".join(lines), encoding="utf-8")


def write_report(results: dict) -> None:
    budget = results["review_budget_curves"]
    early = results["low_gap_early_exit"]
    route_rows = results["route_counts"]
    case_surface = results["case_surface_counts"]
    window_surface = results["window_surface_counts"]
    top_cases = results["top25_reviewer_cases"]
    summary = results["summary"]

    selected_budget = [
        r
        for r in budget
        if r["target"] == "adqa_fail" and r["queue"] in {"mean_visual_gap", "case_priority_non_low_gap"} and r["budget_frac"] in {0.10, 0.20, 0.25, 1 / 3}
    ]
    budget_lines = [
        f"| {r['queue']} | {fmt(r['budget_frac'], 2)} | {r['k']} | {r['hits']}/{r['total_pos']} | {fmt(r['recall'])} | {fmt(r['precision'])} |"
        for r in selected_budget
    ]

    early_lines = [
        f"| {r['gap_feature']} | {r['gap_group']} | {fmt(r['frac'], 2)} | {r['n']} | {fmt(r['adqa_fail_rate'])} | {fmt(r['ensemble_fail_rate'])} | {fmt(r['adqa_ensemble_full_order_agreement'])} |"
        for r in early
        if (r["gap_feature"] == "max_visual_gap" and (abs(r["frac"] - 0.25) < 1e-9 or abs(r["frac"] - 1 / 3) < 1e-9))
    ]

    route_lines = [
        f"| {r['corpus']} | {r['route']} | {r['windows']} |"
        for r in route_rows
        if r["corpus"] == "all"
    ]
    case_surface_lines = [
        f"| {r['case_id']} | {r['access_surface']} | {r['surface_family']} | {r['cases']} |"
        for r in case_surface
        if r["corpus"] == "all"
    ]
    window_surface_lines = [
        f"| {r['route']} | {r['access_surface']} | {r['surface_family']} | {r['windows']} |"
        for r in window_surface
        if r["corpus"] == "all"
    ]
    top_lines = [
        f"| {r['rank']} | {r['video_id']} | {r['case_id']} | {fmt(fnum(r['priority_score']))} | {r['access_surface']} | {r['suggested_window']} | {r['adqa_fail']} | {r['ensemble_fail']} |"
        for r in top_cases[:10]
    ]

    report = f"""---
title: Parallel Research — Access Surface Triage
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/parallel_access_surface_triage.py
  - cursor/research/output/tribe_blind_spot_cases.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/new_findings_round3/review_worksheet_rows.csv
  - cursor/output/external_ensemble_eval.csv
  - cursor/research/output/parallel_research/access_surface/
---

# Parallel Research — Access Surface Triage

Local-only pass for EXPERIMENTS 5-7: low-gap early-exit/review-budget, top-25 review worksheet validation prep, and Access Surface OS mapping. No external APIs or humans were called.

## Data coverage

- External clips with corrected-ladder ensemble labels joined to TRIBE summaries: **{summary['n_external_joined']}**.
- Total router windows: **{summary['n_windows']}**.
- Total router cases: **{summary['n_cases']}**.
- Top worksheet rows enriched for validation: **{summary['n_top_cases']}**.

## Experiment 5 — low-gap early-exit and review budget

Budget curves continue to support TRIBE as a **review-priority queue**, not an automatic AD omission policy.

| Queue | Budget frac | k clips | ADQA failures caught | Recall | Precision |
|---|---:|---:|---:|---:|---:|
{chr(10).join(budget_lines)}

Selected early-exit checks using bottom/top max visual gap:

| Gap feature | group | frac | n | ADQA fail rate | Ensemble fail rate | ADQA/ensemble agreement |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(early_lines)}

Interpretation: low-gap clips can lower human/frontier-review pressure after normal scoring. CLIP-only replacement remains unsafe enough to avoid deployable skip language.

Artifacts: `review_budget_curves.csv`, `low_gap_early_exit.csv`, `external_joined_failure_rows.csv`.

## Experiment 6 — top-25 review worksheet validation prep

Prepared reviewer-ready top cases with deterministic surface labels, validation targets, existing fail flags, and blank reviewer pass/fail columns.

| Rank | Video | Case | Priority | Surface | Window | ADQA fail | Ensemble fail |
|---:|---|---|---:|---|---|---:|---:|
{chr(10).join(top_lines)}

Artifacts: `top25_reviewer_cases.csv`, `top25_reviewer_cases.md`.

## Experiment 7 — Access Surface OS mapping counts

### Window route counts

| Corpus | Route | Windows |
|---|---|---:|
{chr(10).join(route_lines)}

### Window-level access-surface mapping

| Route | Access surface | Surface family | Windows |
|---|---|---|---:|
{chr(10).join(window_surface_lines)}

### Case-level access-surface mapping

| Case ID | Access surface | Surface family | Cases |
|---|---|---|---:|
{chr(10).join(case_surface_lines)}

Interpretation: the router is already shaped like an Access Surface OS input: static low-pressure windows dominate, while non-low-gap cases route to layout replay/keyframe, action-state cue, peak-window QC, segmented scene/action treatment, or evidence-sidecar QC.

Artifacts: `route_counts.csv`, `route_dominant_type_counts.csv`, `case_surface_counts.csv`, `window_surface_counts.csv`, `surface_mapping_rules.json`.

## Actionable next use

Use `top25_reviewer_cases.csv` as the reviewer/VLM worksheet. Each row has a concrete validation target; the next pass should fill only the prepared blank columns rather than re-ranking the queue.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    fail_by_vid = external_failure_rows()
    joined = joined_external_clip_rows(fail_by_vid)
    budget = budget_curves(joined) + case_priority_budget(fail_by_vid)
    early = low_gap_early_exit(joined)
    route_rows, route_dom_rows = route_counts()
    case_surface, window_surface = surface_mapping_counts()
    top_cases = reviewer_ready_cases(fail_by_vid)
    write_reviewer_markdown(top_cases)

    write_csv(OUT / "external_joined_failure_rows.csv", joined)
    write_csv(OUT / "review_budget_curves.csv", budget)
    write_csv(OUT / "low_gap_early_exit.csv", early)
    write_csv(OUT / "route_counts.csv", route_rows)
    write_csv(OUT / "route_dominant_type_counts.csv", route_dom_rows)
    write_csv(OUT / "case_surface_counts.csv", case_surface)
    write_csv(OUT / "window_surface_counts.csv", window_surface)
    write_csv(OUT / "top25_reviewer_cases.csv", top_cases)

    mapping_rules = {
        "case_surface": CASE_SURFACE,
        "route_surface": ROUTE_SURFACE,
        "note": "Local deterministic mapping for EXPERIMENT 7 counts/prep; not learned and not user-validated.",
    }
    (OUT / "surface_mapping_rules.json").write_text(json.dumps(mapping_rules, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "n_external_joined": len(joined),
        "n_windows": sum(int(r["windows"]) for r in route_rows if r["corpus"] == "all"),
        "n_cases": sum(int(r["cases"]) for r in case_surface if r["corpus"] == "all"),
        "n_top_cases": len(top_cases),
        "output_dir": str(OUT.relative_to(ROOT)),
        "report": str(REPORT.relative_to(ROOT)),
        "best_adqa_review_budget_rows": [
            r for r in budget if r["target"] == "adqa_fail" and r["queue"] == "mean_visual_gap" and r["budget_frac"] in {0.20, 0.25, 1 / 3}
        ],
    }
    results = {
        "summary": summary,
        "review_budget_curves": budget,
        "low_gap_early_exit": early,
        "route_counts": route_rows,
        "route_dominant_type_counts": route_dom_rows,
        "case_surface_counts": case_surface,
        "window_surface_counts": window_surface,
        "top25_reviewer_cases": top_cases,
    }
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    write_report(results)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
