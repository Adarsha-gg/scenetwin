#!/usr/bin/env python3
"""Task assistant affordance probe.

This maps the newest task/video-assistant papers onto the external clip corpus.
The question is no longer "what access surface?" or "what assistant mode?" but:

    what evidence/action loop would make this clip usable?

Vid2Coach and AROMA imply step indices, completion criteria, current-state
monitoring, and user-provided non-visual cues. StreetReaderAI implies geospatial
context and orientation controls. CoSight implies timeline-anchored community
descriptions with quality gates.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
REGISTRY = CURSOR / "data" / "external_clips" / "registry.jsonl"
ASSISTANT = CURSOR / "methods" / "output" / "visual_assistant_skill_policy.csv"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "task_assistant_affordance.csv"
OUT_JSON = OUT_DIR / "task_assistant_affordance_summary.json"

COOKING_WORDS = {
    "cook", "cooking", "recipe", "food", "dish", "egg", "eggs", "sauce", "pan",
    "bowl", "knife", "chop", "chopping", "cut", "stir", "mix", "oven", "bake",
    "fry", "boil", "kitchen", "ingredient", "ingredients",
}
HOWTO_WORDS = {
    "step", "steps", "instruction", "instructions", "tutorial", "how", "uses",
    "using", "tool", "tools", "make", "makes", "clean", "cleaning", "shape",
    "shaping", "assemble", "place", "put", "turn", "hold", "apply",
}
COMPLETION_WORDS = {
    "finished", "complete", "done", "ready", "golden", "brown", "smooth",
    "clean", "shape", "aligned", "position", "correct", "properly",
}
NAV_WORDS = {
    "street", "road", "sidewalk", "crosswalk", "door", "entrance", "path",
    "stairs", "walk", "walking", "route", "left", "right", "ahead", "behind",
    "near", "nearby", "front", "intersection", "sign", "landmark",
}
COMMENT_WORDS = {
    "smile", "laugh", "reaction", "audience", "funny", "beautiful", "dramatic",
    "cute", "surprising", "dance", "music", "performance", "crowd", "emotion",
    "emotional", "stage", "scene",
}
SAFETY_WORDS = {
    "knife", "hot", "oven", "pan", "stairs", "road", "street", "crosswalk",
    "traffic", "fire", "glass", "sharp", "danger", "hazard",
}


def toks(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def count_vocab(text: str, vocab: set[str]) -> int:
    return sum(1 for tok in toks(text) if tok in vocab)


def load_registry() -> dict[str, dict]:
    out = {}
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("download_ok", True):
                out[str(row["video_id"])] = row
    return out


def classify(row: pd.Series, meta: dict) -> dict:
    text = " ".join(
        str(meta.get(k, ""))
        for k in ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short"]
    )
    category = str(row["category"])
    cooking = count_vocab(text, COOKING_WORDS) + (2 if category == "Food & Cooking" else 0)
    howto = count_vocab(text, HOWTO_WORDS) + (2 if category == "How-to & Instructional" else 0)
    completion = count_vocab(text, COMPLETION_WORDS)
    nav = count_vocab(text, NAV_WORDS)
    comment = count_vocab(text, COMMENT_WORDS)
    safety = count_vocab(text, SAFETY_WORDS)

    need = float(row["need_z"])
    speech = float(row["mean_speech_density"])
    slot = float(row["mean_standard_slot_score"])
    target = int(row["target"])
    mode = str(row["assistant_mode"])
    surface = str(row["surface"])

    task_score = 0.0
    task_score += 0.20 if howto >= 2 else 0.0
    task_score += 0.18 if cooking >= 2 else 0.0
    task_score += 0.16 if completion else 0.0
    task_score += 0.18 * max(0.0, min(1.0, need))
    task_score += 0.12 if mode in {"verify_before_answer", "depth_guarded_guidance"} else 0.0
    task_score += 0.08 if speech >= 0.75 and slot <= 0.15 else 0.0

    if (cooking >= 2 or category == "Food & Cooking") and (howto >= 2 or completion or need >= 0.45):
        affordance = "reality_video_task_coach"
        evidence_loop = "step_index+completion_criteria+wearer_camera+nonvisual_user_cues"
        reason = "video_recipe_or_cooking_clip_needs_alignment_between_demonstration_and_current_state"
    elif howto >= 3 and (completion or mode == "verify_before_answer" or need >= 0.35):
        affordance = "stepwise_task_coach"
        evidence_loop = "step_index+completion_criteria+progress_feedback"
        reason = "howto_clip_needs_step_state_and_completion_feedback_not_description_only"
    elif nav >= 3 or mode == "depth_guarded_guidance":
        affordance = "route_or_spatial_rehearsal"
        evidence_loop = "geospatial_context+orientation_state+depth_or_obstacle_guard"
        reason = "navigation_or_spatial_clip_needs_orientation_and_obstacle_evidence"
    elif surface in {"identity_chip", "emotive_style"} or comment >= 2:
        affordance = "community_context_layer"
        evidence_loop = "timeline_comments+caption_refs+quality_gate"
        reason = "social_or_emotional_visual_detail_could_benefit_from_grounded_viewer_comments"
    elif mode == "stateful_video_agent":
        affordance = "evidence_indexed_video_agent"
        evidence_loop = "timestamp_index+storyboard+transcript+metadata"
        reason = "temporal_question_needs_video_memory_and_retrieval"
    else:
        affordance = "watch_only_access"
        evidence_loop = "surface_router_output"
        reason = "no_strong_task_or_spatial_loop_detected"

    return {
        "task_affordance": affordance,
        "evidence_loop": evidence_loop,
        "task_reason": reason,
        "task_score": round(task_score, 4),
        "cooking_terms": cooking,
        "howto_terms": howto,
        "completion_terms": completion,
        "navigation_terms": nav,
        "comment_terms": comment,
        "safety_terms": safety,
        "needs_current_state_monitoring": affordance in {"reality_video_task_coach", "stepwise_task_coach"},
        "needs_human_or_community_layer": affordance == "community_context_layer" or (safety > 0 and target == 1),
    }


def summarize(df: pd.DataFrame) -> dict:
    target = df["target"].astype(int).eq(1)
    task_loop = df["task_affordance"].ne("watch_only_access")
    return {
        "n_clips": int(len(df)),
        "task_affordance_counts": {str(k): int(v) for k, v in Counter(df["task_affordance"]).items()},
        "evidence_loop_counts": {str(k): int(v) for k, v in Counter(df["evidence_loop"]).items()},
        "mean_task_score": float(df["task_score"].mean()),
        "current_state_monitoring_n": int(df["needs_current_state_monitoring"].sum()),
        "human_or_community_layer_n": int(df["needs_human_or_community_layer"].sum()),
        "task_loop_target_recall": float((target & task_loop).sum() / target.sum()) if target.sum() else 0.0,
        "watch_only_target_misses": int((target & ~task_loop).sum()),
    }


def main() -> None:
    registry = load_registry()
    assistant = pd.read_csv(ASSISTANT)
    rows = []
    for _, row in assistant.iterrows():
        meta = registry.get(str(row["video_id"]), {})
        rows.append({**row.to_dict(), **classify(row, meta)})
    out = pd.DataFrame(rows).sort_values(
        ["task_affordance", "task_score", "followup_pressure"],
        ascending=[True, False, False],
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    summary = summarize(out)
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
