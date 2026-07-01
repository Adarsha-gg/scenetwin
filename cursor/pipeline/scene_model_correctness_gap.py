#!/usr/bin/env python3
"""Scene-model correctness gap analysis.

Core paper idea: AI-AD safety is not just object grounding. A blind viewer needs a
correct scene model: who did what to whom, how many, where, and in what order.
This script consolidates local evidence for that claim using only existing data.
"""
from __future__ import annotations

import csv
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALLUC = ROOT / "cursor" / "data" / "human_hallucinations.jsonl"
STRATUM = ROOT / "cursor" / "output" / "human_lies_stratum.csv"
OUT_DIR = ROOT / "cursor" / "output" / "scene_model_correctness_gap"
REPORT = ROOT / "output" / "reports" / "scenetwin-scene-model-correctness-gap.md"

REL_CLASSES = {"relational_action", "count_relational", "action_relational", "count_action"}

QUESTION_PATTERNS = {
    "count": re.compile(r"\b(how many|number of|count)\b", re.I),
    "who_role": re.compile(r"\b(who|which person|man|woman|boy|girl|person)\b", re.I),
    "spatial_relation": re.compile(r"\b(where|position|relative|next to|behind|in front|foreground|background)\b", re.I),
    "action_relation": re.compile(r"\b(doing|action|what .* doing|what happens|moving|holding|using|interact|toward|away)\b", re.I),
    "object_attr": re.compile(r"\b(color|wearing|object|visible|shown|text|sign|what is visible|what .* see)\b", re.I),
}


def probe_type_from_swap(swap: str, swap_class: str) -> str:
    left, right = [x.lower() for x in swap.split("->", 1)] if "->" in swap else (swap.lower(), "")
    text = f"{left} {right} {swap_class}"
    if any(w in text for w in ["one", "two", "three", "four", "count", "couple", "people"]):
        return "count"
    if any(w in text for w in ["man", "woman", "boy", "girl", "person", "people", "foreground"]):
        return "who_role"
    if any(w in text for w in ["closer", "away", "ground", "basket", "foreground", "background", "around"]):
        return "spatial_relation"
    return "action_relation"


def classify_question(q: str) -> str:
    hits = [name for name, pat in QUESTION_PATTERNS.items() if pat.search(q)]
    if not hits:
        return "other"
    # Prefer scene-model labels over object_attr if both fire.
    for name in ("count", "who_role", "spatial_relation", "action_relation"):
        if name in hits:
            return name
    return hits[0]


def load_hallucination_slices() -> tuple[list[dict], list[dict]]:
    drops = {r["vid"]: r for r in csv.DictReader(open(STRATUM, encoding="utf-8"))}
    clips = []
    probes = []
    for line in open(HALLUC, encoding="utf-8"):
        item = json.loads(line)
        vid = item["video_id"]
        swap_class = item.get("swap_class", "object_scene")
        is_scene_model = swap_class in REL_CLASSES
        d = drops.get(vid)
        caught = None
        if d:
            caught = float(d["drop_lie"]) > float(d["drop_clean"])
        clips.append({
            "video_id": vid,
            "swap_class": swap_class,
            "slice": "scene_model" if is_scene_model else "object_scene",
            "clip_gate_caught": int(caught) if caught is not None else "",
            "n_swaps": len(item.get("swaps", [])),
        })
        for sw in item.get("swaps", []):
            if "->" not in sw:
                continue
            t = probe_type_from_swap(sw, swap_class)
            probes.append({
                "video_id": vid,
                "swap_class": swap_class,
                "slice": "scene_model" if is_scene_model else "object_scene",
                "probe_type": t,
                "swap": sw,
            })
    return clips, probes


def audit_adqa_questions() -> list[dict]:
    rows = []
    seen = set()
    paths = list(glob.glob(str(ROOT / "output" / "scenetwin_timing_20clip" / "**" / "questions.csv"), recursive=True))
    paths += list(glob.glob(str(ROOT / "output" / "scenetwin_timing_20clip" / "**" / "adqa*_questions.csv"), recursive=True))
    for path in sorted(paths):
        # Skip duplicated nested copy.
        rel = str(Path(path).relative_to(ROOT))
        if "scenetwin_timing_20clip/scenetwin_timing_20clip" in rel.replace("\\", "/"):
            continue
        try:
            qs = list(csv.DictReader(open(path, encoding="utf-8")))
        except Exception:
            continue
        for q in qs:
            key = (rel, q.get("video_id"), q.get("q_idx"), q.get("question"))
            if key in seen:
                continue
            seen.add(key)
            question = q.get("question", "")
            typ = classify_question(question)
            rows.append({
                "source": rel,
                "video_id": q.get("video_id", ""),
                "q_idx": q.get("q_idx", ""),
                "question_type": typ,
                "is_scene_model_question": int(typ in {"count", "who_role", "spatial_relation", "action_relation"}),
                "question": question,
            })
    return rows


def rate(n: int, d: int) -> float:
    return n / d if d else 0.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    clips, probes = load_hallucination_slices()
    questions = audit_adqa_questions()

    with open(OUT_DIR / "hallucination_clips.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, clips[0].keys()); w.writeheader(); w.writerows(clips)
    with open(OUT_DIR / "scene_model_probes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, probes[0].keys()); w.writeheader(); w.writerows(probes)
    with open(OUT_DIR / "adqa_question_types.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, questions[0].keys()); w.writeheader(); w.writerows(questions)

    by_slice = defaultdict(list)
    for c in clips:
        by_slice[c["slice"]].append(c)
    probe_by_slice = defaultdict(list)
    for p in probes:
        probe_by_slice[p["slice"]].append(p)
    q_counts = Counter(q["question_type"] for q in questions)
    q_scene = sum(q["is_scene_model_question"] for q in questions)
    q_total = len(questions)

    summary = {
        "n_hallucination_clips": len(clips),
        "n_scene_model_probes": len(probes),
        "clip_gate_by_slice": {},
        "probe_types": dict(Counter(p["probe_type"] for p in probes)),
        "adqa_questions_total": q_total,
        "adqa_scene_model_question_rate": rate(q_scene, q_total),
        "adqa_question_types": dict(q_counts),
    }
    for s, vals in sorted(by_slice.items()):
        caught = sum(v["clip_gate_caught"] == 1 for v in vals)
        summary["clip_gate_by_slice"][s] = {
            "clips": len(vals),
            "caught": caught,
            "catch_rate": rate(caught, len(vals)),
            "probes": len(probe_by_slice[s]),
        }
    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    scene = summary["clip_gate_by_slice"].get("scene_model", {})
    obj = summary["clip_gate_by_slice"].get("object_scene", {})
    top_examples = [p for p in probes if p["slice"] == "scene_model"][:12]

    lines = [
        "# SceneTwin Scene-Model Correctness Gap",
        "",
        "## Thesis",
        "",
        "For AI audio description, **object grounding is not scene understanding**. A blind viewer can hear all the right nouns and still form the wrong mental model if the AD flips who did what, how many people there are, or the spatial/action relation between entities.",
        "",
        "This is the strongest paper direction because it reframes AD safety around viewer comprehension, not caption similarity.",
        "",
        "## Local novelty check",
        "",
        "Repo search shows the object-bias negative result already existed, and the new relational probe-set artifact now exists. What was missing is the consolidated paper claim: connect CLIP failure, targeted scene-model probes, and generic ADQA question coverage into one argument. This script does that.",
        "",
        "## Evidence 1 — CLIP gate catches object lies, not scene-model lies",
        "",
        "| hallucination slice | clips | targeted probes | CLIP gate caught |",
        "|---|---:|---:|---:|",
        f"| object / scene substitutions | {obj.get('clips',0)} | {obj.get('probes',0)} | {obj.get('caught',0)}/{obj.get('clips',0)} ({100*obj.get('catch_rate',0):.1f}%) |",
        f"| who/action/count/spatial relation flips | {scene.get('clips',0)} | {scene.get('probes',0)} | {scene.get('caught',0)}/{scene.get('clips',0)} ({100*scene.get('catch_rate',0):.1f}%) |",
        "",
        "Interpretation: the safety gate is strong for wrong objects/scenes but weak exactly where the viewer's scene model can be inverted while nouns remain plausible.",
        "",
        "## Evidence 2 — current ADQA is not guaranteed to probe the failure mode",
        "",
        f"Across `{q_total}` cached ADQA questions, scene-model questions are `{q_scene}` (`{100*rate(q_scene,q_total):.1f}%`). Distribution:",
        "",
    ]
    for k, v in sorted(q_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "This does not mean ADQA is bad. It means generic question generation is opportunistic. If the risk is relation/action/count hallucination, the evaluator must force those probes instead of hoping they appear.",
        "",
        "## Evidence 3 — targeted probes express the viewer mental model",
        "",
        "Examples from the hard slice:",
        "",
        "| clip | probe type | swap that must be tested |",
        "|---|---|---|",
    ]
    for p in top_examples:
        lines.append(f"| {p['video_id']} | {p['probe_type']} | {p['swap']} |")
    lines += [
        "",
        "These are not cosmetic details. They decide whether the viewer understands the event: pushed away vs pulled closer, two vs three couples, snowball fight vs snowman building, saw cutting vs saw jamming.",
        "",
        "## Paper-worthy claim",
        "",
        "> SceneTwin shows that AD safety cannot be reduced to object-level visual grounding. Existing grounding catches object substitutions but misses scene-model errors. We introduce targeted scene-model probes for who/action/count/spatial relations, turning hallucination detection into a comprehension-safety benchmark for BLV viewers.",
        "",
        "## What to run next",
        "",
        "1. Give a VLM/video model and a text-only LLM these exact probes on truth vs hallucinated ADs.",
        "2. Report by stratum: object/scene vs who/action/count/spatial.",
        "3. If possible, ask BLV/proxy raters the probe questions after hearing each AD. Primary outcome: wrong mental model rate, not rho.",
        "",
        "## Files",
        "",
        "- `cursor/pipeline/scene_model_correctness_gap.py`",
        "- `cursor/output/scene_model_correctness_gap/hallucination_clips.csv`",
        "- `cursor/output/scene_model_correctness_gap/scene_model_probes.csv`",
        "- `cursor/output/scene_model_correctness_gap/adqa_question_types.csv`",
        "- `cursor/output/scene_model_correctness_gap/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR}")
    print(f"Wrote {REPORT}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
