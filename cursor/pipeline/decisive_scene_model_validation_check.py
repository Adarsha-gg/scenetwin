#!/usr/bin/env python3
"""Check whether the decisive 'revolutionary' SceneTwin claim is proven locally.

Decisive claim would be:
TRIBE-routed scene-model probes catch relation/action/count hallucinations better
than CLIP/generic ADQA.

This script checks whether current artifacts can support that exact claim, and
summarizes the closest available evidence.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "output" / "decisive_scene_model_validation_check"
REPORT = ROOT / "output" / "reports" / "scenetwin-decisive-scene-model-validation-check.md"


def pct(a: int, b: int) -> str:
    return f"{100*a/b:.1f}%" if b else "n/a"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    halluc = [json.loads(l) for l in open(ROOT / "cursor/data/human_hallucinations.jsonl", encoding="utf-8")]
    halluc_ids = {x["video_id"] for x in halluc}
    timing = json.load(open(ROOT / "workspace/vatex_eval_clips.json", encoding="utf-8"))[:20]
    timing_ids = {x["video_id"] for x in timing}
    overlap = sorted(halluc_ids & timing_ids)

    scene_gap = json.load(open(ROOT / "cursor/output/scene_model_correctness_gap/summary.json", encoding="utf-8"))
    tribe_route = json.load(open(ROOT / "cursor/output/tribe_scene_model_probe_routing/summary.json", encoding="utf-8"))
    all_clip = json.load(open(ROOT / "cursor/output/all_clip_scene_model_audit/summary.json", encoding="utf-8"))
    probes = list(csv.DictReader(open(ROOT / "cursor/output/relational_hallucination_probe_set/probes.csv", encoding="utf-8")))

    rel_probes = [p for p in probes if int(p["is_relation_action_count"])]
    obj_probes = [p for p in probes if not int(p["is_relation_action_count"])]
    # Text-manifest validity: exact authored true/foil strings are visible in the corresponding ADs.
    rel_valid = [p for p in rel_probes if int(p["truth_ad_mentions_true"]) and int(p["halluc_ad_mentions_foil"])]
    obj_valid = [p for p in obj_probes if int(p["truth_ad_mentions_true"]) and int(p["halluc_ad_mentions_foil"])]

    summary = {
        "decisive_claim_proven_locally": False,
        "blocker": "No overlap between local TRIBE timing clips and human hallucination clips.",
        "hallucination_clips": len(halluc_ids),
        "tribe_timing_clips": len(timing_ids),
        "overlap_n": len(overlap),
        "overlap_ids": overlap,
        "closest_evidence": {
            "all_clip_scene_model_axis_wins": all_clip["pro_vs_avg_caption_axis_wins"],
            "all_clip_n": all_clip["n_clips"],
            "all_clip_sign_p": all_clip["pro_vs_avg_caption_axis_sign_p"],
            "clip_gate_object_scene_catch_rate": scene_gap["clip_gate_by_slice"]["object_scene"]["catch_rate"],
            "clip_gate_scene_model_catch_rate": scene_gap["clip_gate_by_slice"]["scene_model"]["catch_rate"],
            "tribe_high_need_scene_model_rate": tribe_route["sources"]["tribe_high_need_matched"]["scene_model_rate"],
            "generic_claude_scene_model_rate": tribe_route["sources"]["generic_claude"]["scene_model_rate"],
            "generic_gpt4o_scene_model_rate": tribe_route["sources"]["generic_gpt4o"]["scene_model_rate"],
            "relational_probe_manifest_valid": len(rel_valid),
            "relational_probe_manifest_total": len(rel_probes),
            "object_probe_manifest_valid": len(obj_valid),
            "object_probe_manifest_total": len(obj_probes),
        },
        "minimal_next_run": "Generate/apply TRIBE high-need windows for the 23 hallucination clips OR author relation/action/count hallucinations on the existing 20 TRIBE clips, then compare CLIP vs generic ADQA vs TRIBE-routed scene-model probes.",
    }
    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    lines = [
        "# Decisive Scene-Model Validation Check",
        "",
        "## Verdict",
        "",
        "**Not proven locally yet.** The decisive claim needs TRIBE-routed scene-model probes evaluated on the same clips as relation/action/count hallucinations. The current checkout has zero overlap between those sets.",
        "",
        "| set | n |",
        "|---|---:|",
        f"| human hallucination clips | {len(halluc_ids)} |",
        f"| local TRIBE timing clips | {len(timing_ids)} |",
        f"| overlap | {len(overlap)} |",
        "",
        "## What is proven / strong already",
        "",
        f"1. All-clip corpus thesis: professional AD adds more scene-model axes than captions on `{all_clip['pro_vs_avg_caption_axis_wins']}/{all_clip['n_clips']}` clips, p `{all_clip['pro_vs_avg_caption_axis_sign_p']:.2e}`.",
        f"2. Object grounding failure: CLIP gate catches object/scene lies at `{100*scene_gap['clip_gate_by_slice']['object_scene']['catch_rate']:.1f}%`, but scene-model lies at only `{100*scene_gap['clip_gate_by_slice']['scene_model']['catch_rate']:.1f}%`.",
        f"3. TRIBE routing signal: TRIBE high-need questions are `{100*tribe_route['sources']['tribe_high_need_matched']['scene_model_rate']:.1f}%` scene-model probes vs generic Claude `{100*tribe_route['sources']['generic_claude']['scene_model_rate']:.1f}%` and GPT-4o `{100*tribe_route['sources']['generic_gpt4o']['scene_model_rate']:.1f}%`.",
        f"4. Probe artifact: authored relation/action/count probes have exact true+foil manifest support for `{len(rel_valid)}/{len(rel_probes)}` probes. Imperfect because exact-string matching undercounts paraphrases.",
        "",
        "## What is missing for the revolutionary claim",
        "",
        "Need one matched experiment:",
        "",
        "```text",
        "same clips + same hallucinated ADs",
        "compare:",
        "  CLIP grounding gate",
        "  generic ADQA",
        "  TRIBE-routed scene-model probes",
        "endpoint:",
        "  relation/action/count hallucination catch rate",
        "```",
        "",
        "## Minimal next run",
        "",
        "Either:",
        "",
        "A. Run/generate TRIBE high-need windows for the 23 existing hallucination clips; or",
        "B. Author relation/action/count hallucinations on the existing 20 TRIBE timing clips.",
        "",
        "Then evaluate whether TRIBE-routed probes catch the scene-model lies CLIP misses.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT_DIR / 'summary.json'}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
