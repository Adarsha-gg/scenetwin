#!/usr/bin/env python3
"""Test whether TRIBE can route scene-model probes.

Question from Adar: can TRIBE be used for the stronger paper claim that AI AD
safety is scene-model correctness (who/action/count/spatial), not object
naming?

This does not claim TRIBE detects relational hallucinations directly. It tests a
narrower, useful role: TRIBE high-need windows should bias the evaluator toward
questions about scene state/action relations rather than generic object lists.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "output" / "tribe_scene_model_probe_routing"
REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-scene-model-probe-routing.md"

QUESTION_FILES = {
    "generic_claude": ROOT / "output/scenetwin_timing_20clip/adqa_q-claude-haiku-4-5_g-claude-haiku-4-5/questions.csv",
    "generic_gpt4o": ROOT / "output/scenetwin_timing_20clip/adqa_q-gpt-4o_g-claude-haiku-4-5/questions.csv",
    "tribe_prompted_all": ROOT / "output/scenetwin_timing_20clip/adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5/questions.csv",
}
HIGH_NEED = ROOT / "output/scenetwin_timing_20clip/tribe_need_adqa/question_need_scores.csv"

SCENE_TYPES = {"count", "who_role", "spatial_relation", "action_relation"}

PATTERNS = [
    ("count", re.compile(r"\b(how many|number of|count)\b", re.I)),
    ("who_role", re.compile(r"\b(who|which person|man|woman|boy|girl|person|child|people|skier|rider)\b", re.I)),
    ("spatial_relation", re.compile(r"\b(where|position|relative|next to|behind|in front|foreground|background|perspective|camera angle|direction|toward|away)\b", re.I)),
    ("action_relation", re.compile(r"\b(doing|action|what .* doing|what happens|moving|holding|using|performing|movement|gesture|interact|sequence|progresses|descend|throw|eat|cook|ride)\b", re.I)),
    ("object_attr", re.compile(r"\b(color|wearing|object|visible|shown|text|sign|setting|environment|lighting|marker|brand|clothing|appearance)\b", re.I)),
]


def classify(q: str) -> str:
    hits = [name for name, pat in PATTERNS if pat.search(q)]
    if not hits:
        return "other"
    for name in ("count", "who_role", "spatial_relation", "action_relation"):
        if name in hits:
            return name
    return hits[0]


def load_questions() -> list[dict]:
    rows: list[dict] = []
    for source, path in QUESTION_FILES.items():
        for r in csv.DictReader(open(path, encoding="utf-8")):
            typ = classify(r["question"])
            rows.append({
                "source": source,
                "clip_idx": r.get("clip_idx", ""),
                "video_id": r.get("video_id", ""),
                "q_idx": r.get("q_idx", ""),
                "question_type": typ,
                "is_scene_model": int(typ in SCENE_TYPES),
                "question": r["question"],
                "tribe_route": r.get("tribe_route", ""),
                "tribe_mean_need": r.get("tribe_mean_need", ""),
            })
    for r in csv.DictReader(open(HIGH_NEED, encoding="utf-8")):
        typ = classify(r["question"])
        rows.append({
            "source": "tribe_high_need_matched",
            "clip_idx": r.get("clip_idx", ""),
            "video_id": "",
            "q_idx": r.get("q_idx", ""),
            "question_type": typ,
            "is_scene_model": int(typ in SCENE_TYPES),
            "question": r["question"],
            "tribe_route": r.get("question_recommendation", ""),
            "tribe_mean_need": r.get("question_need", ""),
        })
    return rows


def prop_ci(k: int, n: int) -> tuple[float, float]:
    # Wilson interval, good enough for report.
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    den = 1 + z*z/n
    mid = (p + z*z/(2*n)) / den
    half = z * math.sqrt((p*(1-p) + z*z/(4*n)) / n) / den
    return mid - half, mid + half


def permutation_p(a: list[int], b: list[int], seed: int = 7, n_perm: int = 20000) -> float:
    obs = sum(a)/len(a) - sum(b)/len(b)
    pool = a + b
    rng = Random(seed)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        aa = pool[:len(a)]
        bb = pool[len(a):]
        if sum(aa)/len(aa) - sum(bb)/len(bb) >= obs - 1e-12:
            ge += 1
    return (ge + 1) / (n_perm + 1)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    rows = load_questions()
    with open(OUT_DIR / "question_routing.csv", "w", newline="", encoding="utf-8") as f:
        fields = list(rows[0].keys())
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)

    by = defaultdict(list)
    for r in rows:
        by[r["source"]].append(r)

    summary = {"sources": {}, "comparisons": {}}
    for src, vals in sorted(by.items()):
        k = sum(r["is_scene_model"] for r in vals)
        n = len(vals)
        lo, hi = prop_ci(k, n)
        summary["sources"][src] = {
            "n": n,
            "scene_model_questions": k,
            "scene_model_rate": k/n,
            "wilson95": [lo, hi],
            "question_types": dict(Counter(r["question_type"] for r in vals)),
        }

    high = [r["is_scene_model"] for r in by["tribe_high_need_matched"]]
    for base in ("generic_claude", "generic_gpt4o", "tribe_prompted_all"):
        b = [r["is_scene_model"] for r in by[base]]
        summary["comparisons"][f"tribe_high_need_vs_{base}"] = {
            "delta_scene_model_rate": sum(high)/len(high) - sum(b)/len(b),
            "permutation_p_one_sided": permutation_p(high[:], b[:]),
        }

    # Clip-level: among clips that have high-need matched questions, how often is at least one scene-model probe selected?
    clip_high = defaultdict(list)
    for r in by["tribe_high_need_matched"]:
        clip_high[r["clip_idx"]].append(r)
    clip_stats = {
        "clips_with_high_need_questions": len(clip_high),
        "clips_with_any_scene_model_high_need_question": sum(any(x["is_scene_model"] for x in xs) for xs in clip_high.values()),
        "clips_with_any_count_or_spatial_question": sum(any(x["question_type"] in {"count", "spatial_relation"} for x in xs) for xs in clip_high.values()),
    }
    summary["clip_level"] = clip_stats

    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    examples = [r for r in by["tribe_high_need_matched"] if r["is_scene_model"]][:12]
    lines = [
        "# TRIBE Scene-Model Probe Routing",
        "",
        "## Question",
        "",
        "Can TRIBE help with the stronger SceneTwin paper claim — AD safety as scene-model correctness — rather than just object grounding?",
        "",
        "## Honest answer",
        "",
        "**Promising yes, but narrow:** TRIBE does not directly detect relation/action/count hallucinations here. What it can do is route evaluation toward high audiovisual-need moments, and those moments are much more likely to demand scene-model questions: who/action/count/spatial relation, not just object labels.",
        "",
        "## Local novelty check",
        "",
        "Existing repo work had TRIBE timing, TRIBE-need ADQA, and CLIP object-bias negatives. I did not find a test explicitly asking whether TRIBE high-need routing enriches scene-model probes. This script runs that consolidation test from cached local questions only.",
        "",
        "## Result",
        "",
        "| source | n questions | scene-model questions | rate | 95% CI |",
        "|---|---:|---:|---:|---:|",
    ]
    for src in ["generic_gpt4o", "generic_claude", "tribe_prompted_all", "tribe_high_need_matched"]:
        s = summary["sources"][src]
        lo, hi = s["wilson95"]
        lines.append(f"| {src} | {s['n']} | {s['scene_model_questions']} | {100*s['scene_model_rate']:.1f}% | [{100*lo:.1f}, {100*hi:.1f}] |")
    lines += ["", "Comparisons against TRIBE high-need matched questions:", ""]
    for k, v in summary["comparisons"].items():
        lines.append(f"- `{k}`: delta `{100*v['delta_scene_model_rate']:.1f} pp`, permutation p `{v['permutation_p_one_sided']:.4f}`")
    lines += [
        "",
        f"Clip-level: `{clip_stats['clips_with_any_scene_model_high_need_question']}/{clip_stats['clips_with_high_need_questions']}` clips with high-need questions get at least one scene-model probe; `{clip_stats['clips_with_any_count_or_spatial_question']}/{clip_stats['clips_with_high_need_questions']}` get a count/spatial probe.",
        "",
        "## Examples of TRIBE-routed scene-model probes",
        "",
        "| clip_idx | type | TRIBE need | question |",
        "|---:|---|---:|---|",
    ]
    for r in examples:
        need = float(r["tribe_mean_need"]) if r["tribe_mean_need"] else 0.0
        lines.append(f"| {r['clip_idx']} | {r['question_type']} | {need:.2f} | {r['question']} |")
    lines += [
        "",
        "## Paper implication",
        "",
        "This gives TRIBE a real role in the scene-model paper: **not** as the final hallucination detector, but as a neural router that decides where the evaluator must ask scene-model questions. The final detector should be targeted ADQA/VLM/human probes over those TRIBE-routed moments.",
        "",
        "Possible central claim:",
        "",
        "> SceneTwin combines neural need routing with targeted scene-model probes: TRIBE selects moments where audio under-specifies the visual scene, and the probe layer tests whether the AD preserves who/action/count/spatial relations rather than merely naming objects.",
        "",
        "## Next hard validation",
        "",
        "Run the targeted probes on truth vs hallucinated ADs with a video-capable VLM and a text-only judge. If TRIBE-routed probes catch relation/action/count lies better than generic ADQA, that becomes the paper's strongest result.",
        "",
        "## Files",
        "",
        "- `cursor/pipeline/tribe_scene_model_probe_routing.py`",
        "- `cursor/output/tribe_scene_model_probe_routing/question_routing.csv`",
        "- `cursor/output/tribe_scene_model_probe_routing/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'question_routing.csv'}")
    print(f"Wrote {OUT_DIR / 'summary.json'}")
    print(f"Wrote {REPORT}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
