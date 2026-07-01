#!/usr/bin/env python3
"""Build a targeted probe set for relation/action/count hallucinations.

SceneTwin already found the important negative: CLIP grounding-drop is object
biased and misses relation/action/count lies. This script turns that limitation
into a concrete evaluation artifact: one targeted BLV-comprehension probe per
human-authored swap, with the true fact and the hallucinated foil separated.

No LLM/API. The point is benchmark construction + coverage accounting, not a new
model score.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALLUC = ROOT / "cursor" / "data" / "human_hallucinations.jsonl"
STRATUM = ROOT / "cursor" / "output" / "human_lies_stratum.csv"
META = ROOT / "workspace" / "vatex_overlap.json"
OUT_DIR = ROOT / "cursor" / "output" / "relational_hallucination_probe_set"
REPORT = ROOT / "output" / "reports" / "scenetwin-relational-hallucination-probes.md"

REL_CLASSES = {"relational_action", "count_relational", "action_relational", "count_action"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def classify_swap(left: str, right: str, swap_class: str) -> str:
    text = f"{left} {right} {swap_class}".lower()
    if any(w in text for w in ["one", "two", "three", "four", "count", "couple", "people"]):
        return "count"
    if any(w in text for w in ["man", "woman", "boy", "girl", "person", "people", "couple", "foreground"]):
        return "who_role"
    if any(w in text for w in ["on", "under", "ground", "closer", "away", "foreground", "background", "basket"]):
        return "spatial_relation"
    return "action_relation"


def question_for(kind: str, true_fact: str) -> str:
    if kind == "count":
        return f"What number/count should the AD convey for: {true_fact}?"
    if kind == "who_role":
        return f"Who is involved or in that role: {true_fact}?"
    if kind == "spatial_relation":
        return f"What is the correct spatial/relational fact: {true_fact}?"
    return f"What action or interaction actually happens: {true_fact}?"


def contains_phrase(text: str, phrase: str) -> bool:
    t = norm(text)
    p = norm(phrase)
    if p in t:
        return True
    # Allow slash alternatives in authored swaps, e.g. demonstrating/skillfully.
    parts = [x for x in re.split(r"[/,]", p) if len(x.strip()) >= 3]
    return bool(parts) and any(x.strip() in t for x in parts)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    meta = {r["video_id"]: r for r in json.load(open(META, encoding="utf-8"))}
    drops = {r["vid"]: r for r in csv.DictReader(open(STRATUM, encoding="utf-8"))}

    probes = []
    clip_rows = []
    for line in open(HALLUC, encoding="utf-8"):
        item = json.loads(line)
        vid = item["video_id"]
        swap_class = item.get("swap_class", "object_scene")
        is_rel = swap_class in REL_CLASSES
        d = drops.get(vid, {})
        clip_caught = None
        if d:
            clip_caught = float(d["drop_lie"]) > float(d["drop_clean"])
        clip_rows.append({
            "video_id": vid,
            "swap_class": swap_class,
            "is_relation_action_count": int(is_rel),
            "n_swaps": len(item.get("swaps", [])),
            "clip_gate_caught": "" if clip_caught is None else int(clip_caught),
            "truth_ad": meta.get(vid, {}).get("va11y_desc", ""),
            "hallucinated_ad": item["human_halluc"],
        })
        for i, sw in enumerate(item.get("swaps", [])):
            if "->" not in sw:
                continue
            left, right = [x.strip() for x in sw.split("->", 1)]
            kind = classify_swap(left, right, swap_class)
            truth = meta.get(vid, {}).get("va11y_desc", "")
            halluc = item["human_halluc"]
            probes.append({
                "video_id": vid,
                "swap_class": swap_class,
                "is_relation_action_count": int(is_rel),
                "probe_idx": i,
                "probe_type": kind,
                "question": question_for(kind, left),
                "true_answer": left,
                "hallucinated_foil": right,
                "truth_ad_mentions_true": int(contains_phrase(truth, left)),
                "truth_ad_mentions_foil": int(contains_phrase(truth, right)),
                "halluc_ad_mentions_true": int(contains_phrase(halluc, left)),
                "halluc_ad_mentions_foil": int(contains_phrase(halluc, right)),
                "swap_text": sw,
            })

    with open(OUT_DIR / "probes.csv", "w", newline="", encoding="utf-8") as f:
        fields = list(probes[0].keys())
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(probes)
    with open(OUT_DIR / "clips.csv", "w", newline="", encoding="utf-8") as f:
        fields = list(clip_rows[0].keys())
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(clip_rows)

    rel_clips = [r for r in clip_rows if r["is_relation_action_count"]]
    old_clips = [r for r in clip_rows if not r["is_relation_action_count"]]
    rel_probes = [p for p in probes if p["is_relation_action_count"]]
    old_probes = [p for p in probes if not p["is_relation_action_count"]]
    caught_rel = sum(r["clip_gate_caught"] == 1 for r in rel_clips)
    caught_old = sum(r["clip_gate_caught"] == 1 for r in old_clips)
    probe_types = Counter(p["probe_type"] for p in probes)
    rel_probe_types = Counter(p["probe_type"] for p in rel_probes)

    summary = {
        "n_clips": len(clip_rows),
        "n_probes": len(probes),
        "relation_action_count_clips": len(rel_clips),
        "relation_action_count_probes": len(rel_probes),
        "object_scene_clips": len(old_clips),
        "object_scene_probes": len(old_probes),
        "clip_gate_caught_relation_action_count": caught_rel,
        "clip_gate_caught_object_scene": caught_old,
        "probe_types": dict(probe_types),
        "relation_probe_types": dict(rel_probe_types),
    }
    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    examples = rel_probes[:12]
    lines = [
        "# SceneTwin Relational Hallucination Probe Set",
        "",
        "## New useful artifact",
        "",
        "SceneTwin already proved the CLIP grounding-drop gate is object-biased: it catches object/scene swaps but fails on who-did-what, count, and spatial/action relation errors. "
        "Those errors are exactly the ones that can make a blind viewer misunderstand the scene even when all salient nouns are present.",
        "",
        "This script converts the red-team into a reusable **targeted comprehension probe set**: every authored hallucination swap becomes a concrete question with a true answer and a hallucinated foil. "
        "It is not another metric-number chase; it is the missing benchmark layer for relation/action/count safety.",
        "",
        "## Local novelty check",
        "",
        "Repo search found the existing relational-lie negative result, but no targeted question/probe set built from the swaps. "
        "So this is new: it turns the limitation into an evaluation dataset that future ADQA/VLM/human studies can use.",
        "",
        "## Result",
        "",
        f"Built `{len(probes)}` targeted probes from `{len(clip_rows)}` hand-authored hallucination clips.",
        "",
        "| slice | clips | probes | CLIP gate caught clips |",
        "|---|---:|---:|---:|",
        f"| object/scene swaps | {len(old_clips)} | {len(old_probes)} | {caught_old}/{len(old_clips)} |",
        f"| relation/action/count swaps | {len(rel_clips)} | {len(rel_probes)} | {caught_rel}/{len(rel_clips)} |",
        "",
        "Probe-type distribution:",
        "",
    ]
    for k, v in sorted(probe_types.items()):
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## Relation/action/count examples",
        "",
        "| clip | type | question | true answer | hallucinated foil |",
        "|---|---|---|---|---|",
    ]
    for p in examples:
        lines.append(
            f"| {p['video_id']} | {p['probe_type']} | {p['question']} | {p['true_answer']} | {p['hallucinated_foil']} |"
        )
    lines += [
        "",
        "## Why this is worth keeping",
        "",
        "A BLV viewer often needs the relation, not just the nouns: who pushed whom, how many people danced, whether someone pulled closer or pushed away, whether the saw cut or jammed. "
        "CLIP can see the same nouns and still miss the false relation. These probes force evaluators to ask the exact scene-model question that matters.",
        "",
        "## How to use next",
        "",
        "1. Grade candidate ADs against these probes with a cross-family LLM judge or BLV/proxy raters.",
        "2. Add one relation/action/count probe per clip to ADQA generation prompts.",
        "3. Report safety by stratum: object/scene vs relation/action/count, instead of one inflated hallucination AUC.",
        "",
        "## Files",
        "",
        "- `cursor/pipeline/relational_hallucination_probe_set.py`",
        "- `cursor/output/relational_hallucination_probe_set/probes.csv`",
        "- `cursor/output/relational_hallucination_probe_set/clips.csv`",
        "- `cursor/output/relational_hallucination_probe_set/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'probes.csv'}")
    print(f"Wrote {OUT_DIR / 'clips.csv'}")
    print(f"Wrote {OUT_DIR / 'summary.json'}")
    print(f"Wrote {REPORT}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
