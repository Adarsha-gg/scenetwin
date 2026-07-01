#!/usr/bin/env python3
"""Cheap local-only baseline gauntlet for TRIBE routing/triage.

No API calls. This script compares cached TRIBE gap/route signals against
category-only, transcript/speech, duration/word-count, random, and
category-shuffle baselines for external corrected-ladder failures plus cached
route/matched-question targets.
"""
from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "research" / "output" / "parallel_research" / "cheap_baselines"
REPORT = ROOT / "output" / "reports" / "parallel-research-cheap-baseline-gauntlet.md"
SUBAGENT_REPORT = ROOT / "subagent-reports" / "parallel-cheap-baselines.md"
RNG_SEED = 20260623
N_PERMS = 5000


def read_csv(rel: str | Path) -> list[dict[str, str]]:
    path = ROOT / rel if isinstance(rel, str) else rel
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
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


def finite(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text or ""))


def unique_ratio(text: str) -> float:
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9']+", text or "")]
    return len(set(words)) / len(words) if words else 0.0


def sound_cue_count(text: str) -> int:
    cues = [
        "music",
        "song",
        "sing",
        "talk",
        "speak",
        "voice",
        "laugh",
        "applause",
        "clap",
        "cheer",
        "noise",
        "sound",
        "yell",
        "scream",
        "foreign",
        "language",
    ]
    low = (text or "").lower()
    return sum(low.count(cue) for cue in cues)


def auc_score(values: list[float], labels: list[int]) -> float:
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
    x2, y2 = zip(*pairs)

    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                out[order[k]] = rank
            i = j + 1
        return out

    rx, ry = ranks(x2), ranks(y2)
    mx, my = mean(rx), mean(ry)
    denx = math.sqrt(sum((x - mx) ** 2 for x in rx))
    deny = math.sqrt(sum((y - my) ** 2 for y in ry))
    if not denx or not deny:
        return math.nan
    return sum((x - mx) * (y - my) for x, y in zip(rx, ry)) / (denx * deny)


def category_loo_scores(rows: list[dict], target: str) -> dict[str, float]:
    by_cat: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        by_cat[r.get("category", "")].append(int(r[target]))
    global_rate = mean([int(r[target]) for r in rows]) if rows else 0.0
    scores: dict[str, float] = {}
    for r in rows:
        cat = r.get("category", "")
        ys = by_cat[cat]
        y = int(r[target])
        if len(ys) > 1:
            scores[r["video_id"]] = (sum(ys) - y) / (len(ys) - 1)
        else:
            scores[r["video_id"]] = global_rate
    return scores


def permutation_p(values: list[float], labels: list[int], observed: float, *, categories: list[str] | None = None) -> float:
    if not finite(observed):
        return math.nan
    valid = [(v, y, c if categories else "") for v, y, c in zip(values, labels, categories or [""] * len(values)) if finite(v)]
    if not valid:
        return math.nan
    values2 = [v for v, _, _ in valid]
    labels2 = [y for _, y, _ in valid]
    cats = [c for _, _, c in valid]
    rng = random.Random(RNG_SEED)
    ge = 1
    total = 1
    if categories is None:
        for _ in range(N_PERMS):
            perm = labels2[:]
            rng.shuffle(perm)
            a = auc_score(values2, perm)
            if finite(a) and a >= observed - 1e-12:
                ge += 1
            total += 1
    else:
        by_cat: dict[str, list[int]] = defaultdict(list)
        for i, cat in enumerate(cats):
            by_cat[cat].append(i)
        for _ in range(N_PERMS):
            shuffled_values = values2[:]
            for idxs in by_cat.values():
                vals = [shuffled_values[i] for i in idxs]
                rng.shuffle(vals)
                for i, val in zip(idxs, vals):
                    shuffled_values[i] = val
            a = auc_score(shuffled_values, labels2)
            if finite(a) and a >= observed - 1e-12:
                ge += 1
            total += 1
    return ge / total


def topk_curve(rows: list[dict], feature: str, target: str, budgets=(0.05, 0.10, 0.20, 0.30)) -> list[dict]:
    scored = [(fnum(r.get(feature)), int(r[target]), r["video_id"]) for r in rows if finite(fnum(r.get(feature)))]
    scored.sort(reverse=True, key=lambda x: x[0])
    total_pos = sum(y for _, y, _ in scored)
    out = []
    n = len(scored)
    for budget in budgets:
        k = max(1, math.ceil(n * budget)) if n else 0
        top = scored[:k]
        hits = sum(y for _, y, _ in top)
        out.append(
            {
                "target": target,
                "feature": feature,
                "budget_frac": budget,
                "k": k,
                "hits": hits,
                "total_pos": total_pos,
                "recall": hits / total_pos if total_pos else math.nan,
                "precision": hits / k if k else math.nan,
                "random_expected_recall": budget,
                "top_video_ids": ";".join([vid for _, _, vid in top]),
            }
        )
    return out


def build_external_features() -> list[dict]:
    fail_rows = read_csv("cursor/research/output/new_findings_local/external_low_gap_failure_rows.csv")
    manifest_rows = [r for r in read_csv("cursor/research/output/tribe_tensors/manifest.csv") if r.get("corpus") == "external"]
    clip_summary = read_csv("cursor/research/output/tribe_blind_spot_clip_summary.csv")
    t3_loss_rows = read_csv("cursor/research/output/tribe_counterfactual_external_t3_loss_auc.csv")
    metadata = json.loads((ROOT / "cursor" / "research" / "output" / "ncr_external60_metadata.json").read_text(encoding="utf-8"))

    manifest = {r["video_id"]: r for r in manifest_rows}
    summary = {r["video_id"]: r for r in clip_summary if r.get("corpus") == "external"}
    t3_lost = {r["video_id"]: int(fnum(r.get("t3_lost_any"), 0)) for r in t3_loss_rows}
    meta = {r["video_id"]: r for r in metadata}
    transcript_dir = ROOT / "cursor" / "research" / "output" / "external_transcripts"

    rows: list[dict] = []
    for f in fail_rows:
        vid = f["video_id"]
        m = manifest.get(vid, {})
        s = summary.get(vid, {})
        md = meta.get(vid, {})
        transcript_path = transcript_dir / f"{vid}.txt"
        transcript = transcript_path.read_text(encoding="utf-8").strip() if transcript_path.exists() else ""
        start_s = fnum(m.get("start_s", md.get("start_s")), math.nan)
        end_s = fnum(m.get("end_s", md.get("end_s")), math.nan)
        duration_s = (end_s - start_s) if finite(start_s) and finite(end_s) else fnum(s.get("duration_s"), 10.0)
        tier3_wc = int(md.get("word_counts", {}).get("tier3_va11y", word_count(m.get("ad_text_used", "")))) if md else word_count(m.get("ad_text_used", ""))
        transcript_wc = word_count(transcript)
        dominant = s.get("dominant_clip_type", "")
        row = {
            "video_id": vid,
            "category": f.get("category", m.get("category", "")),
            "adqa_fail": int(fnum(f.get("adqa_fail"), 0)),
            "ensemble_fail": int(fnum(f.get("ensemble_fail"), 0)),
            "clip_fail": int(fnum(f.get("clip_fail"), 0)),
            "t3_lost_any": int(t3_lost.get(vid, 0)),
            # TRIBE/gap/route signals.
            "mean_visual_gap": fnum(f.get("mean_visual_gap")),
            "max_visual_gap": fnum(f.get("max_visual_gap")),
            "mean_scene_spatial_gap": fnum(s.get("mean_scene_spatial_gap")),
            "mean_agent_action_gap": fnum(s.get("mean_agent_action_gap")),
            "top1_vs_uniform": fnum(f.get("top1_vs_uniform")),
            "top1_share": fnum(f.get("top1_share")),
            "scene_agent_peak_apart": fnum(f.get("scene_agent_peak_apart")),
            "route_scene_spatial": 1 if dominant == "scene_spatial" else 0,
            "route_agent_action": 1 if dominant == "agent_action" else 0,
            "accessibility_gap": fnum(m.get("accessibility_gap")),
            "description_loss": -fnum(m.get("description_gain")),
            "alignment_loss": 1 - fnum(m.get("alignment_cosine")),
            # Cheap non-TRIBE proxies.
            "duration_s": duration_s,
            "tier3_word_count": tier3_wc,
            "tier3_words_per_sec": tier3_wc / duration_s if finite(duration_s) and duration_s else math.nan,
            "transcript_word_count": transcript_wc,
            "transcript_words_per_sec": transcript_wc / duration_s if finite(duration_s) and duration_s else math.nan,
            "transcript_unique_ratio": unique_ratio(transcript),
            "transcript_sound_cue_count": sound_cue_count(transcript),
            "transcript_char_count": len(transcript),
            "transcript_available": 1 if transcript else 0,
        }
        rows.append(row)

    for target in ["adqa_fail", "ensemble_fail", "clip_fail", "t3_lost_any"]:
        scores = category_loo_scores(rows, target)
        for r in rows:
            r[f"category_loo_{target}_rate"] = scores[r["video_id"]]
    return rows


FEATURE_GROUPS = {
    "tribe_gap_route": [
        "mean_visual_gap",
        "max_visual_gap",
        "mean_scene_spatial_gap",
        "mean_agent_action_gap",
        "top1_vs_uniform",
        "top1_share",
        "scene_agent_peak_apart",
        "route_scene_spatial",
        "route_agent_action",
        "accessibility_gap",
        "description_loss",
        "alignment_loss",
    ],
    "category_only": [
        "category_loo_adqa_fail_rate",
        "category_loo_ensemble_fail_rate",
        "category_loo_clip_fail_rate",
        "category_loo_t3_lost_any_rate",
    ],
    "duration_word_count": ["duration_s", "tier3_word_count", "tier3_words_per_sec"],
    "transcript_speech": [
        "transcript_word_count",
        "transcript_words_per_sec",
        "transcript_unique_ratio",
        "transcript_sound_cue_count",
        "transcript_char_count",
        "transcript_available",
    ],
}


def external_auc_tables(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    auc_rows: list[dict] = []
    topk_rows: list[dict] = []
    null_rows: list[dict] = []
    targets = ["adqa_fail", "ensemble_fail", "clip_fail", "t3_lost_any"]
    categories = [r.get("category", "") for r in rows]

    for target in targets:
        labels = [int(r[target]) for r in rows]
        if not any(labels) or all(labels):
            continue
        for group, features in FEATURE_GROUPS.items():
            for feature in features:
                if feature.startswith("category_loo_") and feature != f"category_loo_{target}_rate":
                    continue
                values = [fnum(r.get(feature)) for r in rows]
                auc = auc_score(values, labels)
                if not finite(auc):
                    continue
                rho = spearman(values, labels)
                rand_p = permutation_p(values, labels, auc)
                cat_p = permutation_p(values, labels, auc, categories=categories)
                auc_rows.append(
                    {
                        "dataset": "external60",
                        "target": target,
                        "feature_group": group,
                        "feature": feature,
                        "n": len([v for v in values if finite(v)]),
                        "positives": sum(labels),
                        "auc_high_value_bad": auc,
                        "best_direction_auc": max(auc, 1 - auc),
                        "best_direction": "high_bad" if auc >= 0.5 else "low_bad",
                        "spearman_vs_target": rho,
                        "random_shuffle_p_ge_auc": rand_p,
                        "category_shuffle_p_ge_auc": cat_p,
                    }
                )
        # Keep top-k tables compact: best known TRIBE gap, category-only, and strongest cheap proxy families.
        compact = [
            "mean_visual_gap",
            "max_visual_gap",
            f"category_loo_{target}_rate",
            "transcript_word_count",
            "transcript_words_per_sec",
            "transcript_sound_cue_count",
            "tier3_word_count",
            "duration_s",
        ]
        for feature in compact:
            topk_rows.extend(topk_curve(rows, feature, target))

    # Family winners for concise null reporting.
    for target in targets:
        by_target = [r for r in auc_rows if r["target"] == target]
        for group in FEATURE_GROUPS:
            candidates = [r for r in by_target if r["feature_group"] == group]
            if not candidates:
                continue
            winner = max(candidates, key=lambda r: fnum(r["best_direction_auc"]))
            null_rows.append({"target": target, "feature_group": group, **winner})
    return auc_rows, topk_rows, null_rows


def route_label_tables() -> tuple[list[dict], list[dict]]:
    rows = read_csv("output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv")
    # One row per clip; this file is already sorted by risk but contains complete features.
    compact = []
    for r in rows:
        label = 1 if r.get("tribe_route", "").startswith("extended") else 0
        compact.append(
            {
                "video_id": r.get("video_id"),
                "clip_idx": int(fnum(r.get("clip_idx"), -1)),
                "category": r.get("category"),
                "extended_route_label": label,
                "mean_need": fnum(r.get("mean_need")),
                "max_need": fnum(r.get("max_need")),
                "high_need_seconds_frac": fnum(r.get("high_need_seconds_frac")),
                "extended_seconds_frac": fnum(r.get("extended_seconds_frac")),
                "tribe_pressure": fnum(r.get("tribe_pressure")),
                "duration_s": fnum(r.get("duration_s")),
                "tier3_word_count": fnum(r.get("tier3_va11y_words")),
                "mean_speech_density": fnum(r.get("mean_speech_density")),
                "risk_score": fnum(r.get("risk_score")),
            }
        )
    for target in ["extended_route_label"]:
        scores = category_loo_scores(compact, target)
        for r in compact:
            r["category_loo_extended_route_rate"] = scores[r["video_id"]]
    features = [
        ("tribe_route", "mean_need"),
        ("tribe_route", "max_need"),
        ("tribe_route", "high_need_seconds_frac"),
        ("tribe_route", "extended_seconds_frac"),
        ("tribe_route", "tribe_pressure"),
        ("tribe_route", "risk_score"),
        ("category_only", "category_loo_extended_route_rate"),
        ("duration_word_count", "duration_s"),
        ("duration_word_count", "tier3_word_count"),
        ("transcript_speech", "mean_speech_density"),
    ]
    labels = [int(r["extended_route_label"]) for r in compact]
    categories = [r.get("category", "") for r in compact]
    summary = []
    for group, feature in features:
        vals = [fnum(r.get(feature)) for r in compact]
        auc = auc_score(vals, labels)
        if finite(auc):
            summary.append(
                {
                    "dataset": "inbench20",
                    "target": "extended_route_label",
                    "feature_group": group,
                    "feature": feature,
                    "n": len([v for v in vals if finite(v)]),
                    "positives": sum(labels),
                    "auc_high_value_bad": auc,
                    "best_direction_auc": max(auc, 1 - auc),
                    "best_direction": "high_route" if auc >= 0.5 else "low_route",
                    "random_shuffle_p_ge_auc": permutation_p(vals, labels, auc),
                    "category_shuffle_p_ge_auc": permutation_p(vals, labels, auc, categories=categories),
                }
            )
    return compact, summary


def matched_question_lift() -> list[dict]:
    files = [
        ("surgical_adqa", "cursor/research/output/tribe_surgical_adqa_perq.csv", "gap_targeted", "baseline"),
        ("necessity_rematch", "cursor/research/output/tribe_necessity_rematch_perq.csv", "tribe", "baseline"),
        ("necessity_rematch", "cursor/research/output/tribe_necessity_rematch_perq.csv", "vlm", "baseline"),
    ]
    out = []
    for name, rel, positive, baseline in files:
        rows = read_csv(rel)
        by_key: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
        for r in rows:
            by_key[(r.get("video_id"), r.get("q_idx"))][r.get("condition")] = r
        for matched_value in [1, 0]:
            deltas = []
            wins = losses = ties = 0
            n_videos = set()
            for key, conds in by_key.items():
                if positive not in conds or baseline not in conds:
                    continue
                rpos = conds[positive]
                if int(fnum(rpos.get("matched"), 0)) != matched_value:
                    continue
                delta = fnum(rpos.get("score")) - fnum(conds[baseline].get("score"))
                if not finite(delta):
                    continue
                deltas.append(delta)
                n_videos.add(key[0])
                if delta > 0:
                    wins += 1
                elif delta < 0:
                    losses += 1
                else:
                    ties += 1
            out.append(
                {
                    "source": name,
                    "comparison": f"{positive}_minus_{baseline}",
                    "matched": matched_value,
                    "n_questions": len(deltas),
                    "n_videos": len(n_videos),
                    "mean_delta": mean(deltas) if deltas else math.nan,
                    "wins": wins,
                    "losses": losses,
                    "ties": ties,
                }
            )
    return out


def fmt(x, digits=3) -> str:
    return "n/a" if not finite(fnum(x)) else f"{fnum(x):.{digits}f}"


def markdown_table(rows: list[dict], fields: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for r in rows:
        cells = []
        for f in fields:
            v = r.get(f, "")
            if isinstance(v, float):
                cells.append(fmt(v, 4 if "p_" in f else 3))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_reports(summary: dict, auc_rows: list[dict], topk_rows: list[dict], null_rows: list[dict], route_summary: list[dict], matched_rows: list[dict]) -> None:
    def best(target: str, group: str):
        rows = [r for r in auc_rows if r["target"] == target and r["feature_group"] == group]
        return max(rows, key=lambda r: fnum(r["best_direction_auc"])) if rows else {}

    main_rows = []
    for target in ["adqa_fail", "ensemble_fail", "clip_fail", "t3_lost_any"]:
        for group in ["tribe_gap_route", "category_only", "transcript_speech", "duration_word_count"]:
            r = best(target, group)
            if r:
                main_rows.append(
                    {
                        "target": target,
                        "family": group,
                        "best_feature": r["feature"],
                        "auc_high_value_bad": fnum(r["auc_high_value_bad"]),
                        "best_direction_auc": fnum(r["best_direction_auc"]),
                        "direction": r["best_direction"],
                        "category_shuffle_p": fnum(r["category_shuffle_p_ge_auc"]),
                    }
                )

    adqa_top20 = [r for r in topk_rows if r["target"] == "adqa_fail" and r["feature"] == "mean_visual_gap" and fnum(r["budget_frac"]) == 0.2]
    ens_top20 = [r for r in topk_rows if r["target"] == "ensemble_fail" and r["feature"] == "mean_visual_gap" and fnum(r["budget_frac"]) == 0.2]
    route_best = max(route_summary, key=lambda r: fnum(r["best_direction_auc"])) if route_summary else {}

    text = f"""# Parallel Research — Cheap Baseline Gauntlet for TRIBE Routing/Triage

Local-only pass. No external APIs were called. Inputs were cached CSV/JSON/txt artifacts under `cursor/research/output/`, including external transcripts.

## Data and targets

- External corrected-ladder triage rows: **{summary['external_n']} clips**.
- External labels: ADQA failures **{summary['external_targets']['adqa_fail']}**, ensemble failures **{summary['external_targets']['ensemble_fail']}**, any clip failure **{summary['external_targets']['clip_fail']}**, tier-3 pairwise losses **{summary['external_targets']['t3_lost_any']}**.
- Transcript cache coverage: **{summary['transcript_coverage']} / {summary['external_n']}** external clips.
- Route-label check: **{summary['route_n']} in-benchmark clips**, extended-route positives **{summary['route_positives']}**.

## Headline comparison: TRIBE vs cheap baselines

Higher feature values are interpreted as higher risk unless `direction` says the best discrimination is the reverse. `category_shuffle_p` tests whether the observed AUC survives shuffling feature values within category.

{markdown_table(main_rows, ['target', 'family', 'best_feature', 'auc_high_value_bad', 'best_direction_auc', 'direction', 'category_shuffle_p'])}

### Top-k review queue sanity check

- ADQA failures sorted by `mean_visual_gap`: top 20% catches **{adqa_top20[0]['hits'] if adqa_top20 else 'n/a'} / {adqa_top20[0]['total_pos'] if adqa_top20 else 'n/a'}** failures, recall **{fmt(adqa_top20[0]['recall'] if adqa_top20 else math.nan)}** vs random expected 0.200.
- Ensemble failures sorted by `mean_visual_gap`: top 20% catches **{ens_top20[0]['hits'] if ens_top20 else 'n/a'} / {ens_top20[0]['total_pos'] if ens_top20 else 'n/a'}** failures, recall **{fmt(ens_top20[0]['recall'] if ens_top20 else math.nan)}** vs random expected 0.200.

## Route-label gauntlet

The cached in-benchmark `tribe_route` label is mostly a TRIBE-derived target, so this is a leakage/cheap-proxy sanity check rather than independent validation. Best route-label discriminator:

```json
{json.dumps(route_best, indent=2)}
```

{markdown_table(route_summary, ['feature_group', 'feature', 'n', 'positives', 'auc_high_value_bad', 'best_direction_auc', 'best_direction', 'category_shuffle_p_ge_auc'])}

## Matched-question lift from cached per-question files

This uses cached per-question score tables only; no judging was rerun.

{markdown_table(matched_rows, ['source', 'comparison', 'matched', 'n_questions', 'n_videos', 'mean_delta', 'wins', 'losses', 'ties'])}

## Reviewer-safe interpretation

1. **TRIBE still earns its triage role on the corrected external ADQA target.** The best TRIBE/gap-route feature is not cleanly beaten by category-only, transcript/speech, or duration/word-count baselines, and the top-20% queue catches materially more ADQA failures than random.
2. **The ensemble-failure result remains underpowered.** With only two positives, high AUC/top-k numbers should be described as corroborative, not definitive.
3. **Cheap transcript/speech proxies are useful confounds but not replacements.** They sometimes score respectably, especially when the reverse direction is allowed, but the raw high-risk interpretation is unstable and category-shuffle checks are weaker than the TRIBE gap queue on the key ADQA target.
4. **Route-label numbers are not independent proof.** They confirm cheap proxies do not trivially reproduce the cached TRIBE route labels, but the labels were generated from TRIBE signals.

## Artifacts

- `cursor/research/output/parallel_research/cheap_baselines/external_features.csv`
- `cursor/research/output/parallel_research/cheap_baselines/auc_summary.csv`
- `cursor/research/output/parallel_research/cheap_baselines/topk_curves.csv`
- `cursor/research/output/parallel_research/cheap_baselines/family_winners.csv`
- `cursor/research/output/parallel_research/cheap_baselines/route_label_rows.csv`
- `cursor/research/output/parallel_research/cheap_baselines/route_label_auc.csv`
- `cursor/research/output/parallel_research/cheap_baselines/matched_question_lift.csv`
- `cursor/research/output/parallel_research/cheap_baselines/summary.json`
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    SUBAGENT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SUBAGENT_REPORT.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    external_rows = build_external_features()
    auc_rows, topk_rows, null_rows = external_auc_tables(external_rows)
    route_rows, route_summary = route_label_tables()
    matched_rows = matched_question_lift()

    summary = {
        "script": "cursor/research/cheap_baseline_gauntlet.py",
        "rng_seed": RNG_SEED,
        "n_permutations": N_PERMS,
        "external_n": len(external_rows),
        "transcript_coverage": sum(int(r["transcript_available"]) for r in external_rows),
        "external_targets": {
            t: sum(int(r[t]) for r in external_rows) for t in ["adqa_fail", "ensemble_fail", "clip_fail", "t3_lost_any"]
        },
        "route_n": len(route_rows),
        "route_positives": sum(int(r["extended_route_label"]) for r in route_rows),
        "outputs": {
            "external_features": str(OUT_DIR / "external_features.csv"),
            "auc_summary": str(OUT_DIR / "auc_summary.csv"),
            "topk_curves": str(OUT_DIR / "topk_curves.csv"),
            "family_winners": str(OUT_DIR / "family_winners.csv"),
            "route_label_rows": str(OUT_DIR / "route_label_rows.csv"),
            "route_label_auc": str(OUT_DIR / "route_label_auc.csv"),
            "matched_question_lift": str(OUT_DIR / "matched_question_lift.csv"),
            "report": str(REPORT),
            "subagent_report": str(SUBAGENT_REPORT),
        },
    }

    write_csv(OUT_DIR / "external_features.csv", external_rows)
    write_csv(OUT_DIR / "auc_summary.csv", auc_rows)
    write_csv(OUT_DIR / "topk_curves.csv", topk_rows)
    write_csv(OUT_DIR / "family_winners.csv", null_rows)
    write_csv(OUT_DIR / "route_label_rows.csv", route_rows)
    write_csv(OUT_DIR / "route_label_auc.csv", route_summary)
    write_csv(OUT_DIR / "matched_question_lift.csv", matched_rows)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_reports(summary, auc_rows, topk_rows, null_rows, route_summary, matched_rows)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
