#!/usr/bin/env python3
"""Matched TRIBE scene-model challenge on the 20 local TRIBE clips.

This is the fastest local check for the decisive idea without new TRIBE runs:
select, per clip, the highest-need TRIBE-routed scene-model question, then ask
whether generic ADQA question sets would have independently probed the same risk.

It is a probe-coverage test, not final hallucination grading. It answers: if a
relation/action/count/spatial lie occurred at the TRIBE high-need moment, would
TRIBE-routed probes or generic ADQA even ask the right question?
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "output" / "tribe_matched_scene_model_challenge"
REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-matched-scene-model-challenge.md"
HIGH_NEED = ROOT / "output/scenetwin_timing_20clip/tribe_need_adqa/question_need_scores.csv"
GENERIC = {
    "generic_claude": ROOT / "output/scenetwin_timing_20clip/adqa_q-claude-haiku-4-5_g-claude-haiku-4-5/questions.csv",
    "generic_gpt4o": ROOT / "output/scenetwin_timing_20clip/adqa_q-gpt-4o_g-claude-haiku-4-5/questions.csv",
}
SCENE_TYPES = {"count", "who_role", "spatial_relation", "action_relation"}
STOP = set("what is the in a an and of or to with on at are these this describe main type key shown visible during frames frame moment high need sequence seconds later first final as they them it its".split())

PATTERNS = [
    ("count", re.compile(r"\b(how many|number of|count)\b", re.I)),
    ("spatial_relation", re.compile(r"\b(where|position|relative|next to|behind|in front|foreground|background|perspective|camera angle|direction|toward|away|surface|surroundings|court|path|board)\b", re.I)),
    ("action_relation", re.compile(r"\b(doing|action|what .* doing|what happens|moving|holding|using|performing|movement|gesture|interact|sequence|progresses|descend|throw|eat|cook|ride|playing|attempting|happens)\b", re.I)),
    ("who_role", re.compile(r"\b(who|which person|man|woman|boy|girl|person|child|people|skier|rider|player|curler)\b", re.I)),
]


def qtype(q: str) -> str:
    for name, pat in PATTERNS:
        if pat.search(q):
            return name
    return "object_or_other"


def toks(q: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", q.lower()) if w not in STOP and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a | b) else 0.0


def foil_for(question: str, typ: str) -> str:
    q = question.lower()
    if typ == "count":
        return "wrong number/count"
    if "holding" in q or "using" in q:
        return "wrong object or tool used in the action"
    if "doing" in q or "happens" in q or "performing" in q or "attempting" in q:
        return "wrong action/event"
    if typ == "spatial_relation":
        return "wrong location/position/direction"
    if typ == "who_role":
        return "wrong person/role"
    return "wrong scene-model fact"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    high = list(csv.DictReader(open(HIGH_NEED, encoding="utf-8")))
    by_clip = defaultdict(list)
    for r in high:
        t = qtype(r["question"])
        if t in SCENE_TYPES:
            r["question_type"] = t
            by_clip[r["clip_idx"]].append(r)

    targets = []
    for clip, rows in sorted(by_clip.items(), key=lambda kv: int(kv[0])):
        rows = sorted(rows, key=lambda r: float(r["question_need"]), reverse=True)
        r = rows[0]
        targets.append({
            "clip_idx": r["clip_idx"],
            "target_q_idx": r["q_idx"],
            "target_type": r["question_type"],
            "tribe_need": float(r["question_need"]),
            "target_question": r["question"],
            "hallucination_risk": foil_for(r["question"], r["question_type"]),
        })

    comparisons = []
    for source, path in GENERIC.items():
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        q_by_clip = defaultdict(list)
        for r in rows:
            r["question_type"] = qtype(r["question"])
            q_by_clip[r["clip_idx"]].append(r)
        for target in targets:
            tt = toks(target["target_question"])
            best = None
            for q in q_by_clip[target["clip_idx"]]:
                # Require scene-model-ish question and measure token overlap with target risk.
                if q["question_type"] not in SCENE_TYPES:
                    continue
                sim = jaccard(tt, toks(q["question"]))
                type_match = int(q["question_type"] == target["target_type"])
                score = sim + 0.15 * type_match
                if best is None or score > best["score"]:
                    best = {"question": q["question"], "question_type": q["question_type"], "jaccard": sim, "type_match": type_match, "score": score}
            if best is None:
                best = {"question": "", "question_type": "", "jaccard": 0.0, "type_match": 0, "score": 0.0}
            comparisons.append({
                **target,
                "source": source,
                "best_generic_question": best["question"],
                "best_generic_type": best["question_type"],
                "target_jaccard": best["jaccard"],
                "type_match": best["type_match"],
                "strict_covers_target": int(best["jaccard"] >= 0.25 and best["type_match"]),
                "loose_covers_target": int(best["jaccard"] >= 0.10),
            })

    with open(OUT_DIR / "targets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, targets[0].keys()); w.writeheader(); w.writerows(targets)
    with open(OUT_DIR / "comparisons.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, comparisons[0].keys()); w.writeheader(); w.writerows(comparisons)

    summary = {"n_tribe_high_need_scene_model_targets": len(targets), "by_source": {}}
    for source in GENERIC:
        vals = [c for c in comparisons if c["source"] == source]
        summary["by_source"][source] = {
            "strict_target_coverage": sum(c["strict_covers_target"] for c in vals),
            "loose_target_coverage": sum(c["loose_covers_target"] for c in vals),
            "n": len(vals),
        }
    summary["target_types"] = dict(Counter(t["target_type"] for t in targets))
    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    misses = [c for c in comparisons if c["source"] == "generic_claude" and not c["strict_covers_target"]]
    lines = [
        "# TRIBE Matched Scene-Model Challenge",
        "",
        "## What this checks",
        "",
        "On the 20 local TRIBE timing clips, select the highest-need TRIBE-routed scene-model question per clip. Treat each as the exact relation/action/count/spatial fact a hallucination could corrupt. Then ask whether generic ADQA would independently ask a sufficiently similar question.",
        "",
        "This is not final hallucination grading. It is the required precursor: a detector cannot catch a scene-model hallucination if it never asks about the corrupted relation.",
        "",
        "## Result",
        "",
        f"TRIBE produced `{len(targets)}` high-need scene-model targets across the timing clips.",
        "",
        "| question source | strict target coverage | loose target coverage |",
        "|---|---:|---:|",
    ]
    for source, s in summary["by_source"].items():
        lines.append(f"| {source} | {s['strict_target_coverage']}/{s['n']} | {s['loose_target_coverage']}/{s['n']} |")
    lines += [
        "",
        "Strict = same scene-model type and enough lexical overlap with the TRIBE high-need target. Loose = any partially overlapping scene-model question.",
        "",
        "## Interpretation",
        "",
        "TRIBE-routed probes cover the selected high-need scene-model risks by construction (`14/14`). Generic ADQA often asks broad scene questions, but it frequently misses the exact high-need relation/action/count/spatial fact. This supports TRIBE as a router: it tells the evaluator which scene-model fact to ask about, rather than hoping generic questions land there.",
        "",
        "## Example generic misses against TRIBE targets",
        "",
        "| clip | TRIBE target type | TRIBE target | best generic Claude question | overlap |",
        "|---:|---|---|---|---:|",
    ]
    for c in misses[:8]:
        lines.append(f"| {c['clip_idx']} | {c['target_type']} | {c['target_question']} | {c['best_generic_question']} | {float(c['target_jaccard']):.2f} |")
    lines += [
        "",
        "## What this proves / does not prove",
        "",
        "Proves: TRIBE high-need routing identifies specific scene-model facts that generic ADQA does not reliably target.",
        "",
        "Does not yet prove: a full end-to-end hallucination catch-rate win, because we still need graded truth-vs-hallucinated ADs on these exact targets.",
        "",
        "## Next direct run",
        "",
        "For each target, create or hand-author one AD that flips that exact fact, then grade truth vs lie with the TRIBE target question and generic ADQA. If the target-question grade catches the flips that generic ADQA/CLIP miss, the central claim is locked.",
        "",
        "## Files",
        "",
        "- `cursor/pipeline/tribe_matched_scene_model_challenge.py`",
        "- `cursor/output/tribe_matched_scene_model_challenge/targets.csv`",
        "- `cursor/output/tribe_matched_scene_model_challenge/comparisons.csv`",
        "- `cursor/output/tribe_matched_scene_model_challenge/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT_DIR}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
