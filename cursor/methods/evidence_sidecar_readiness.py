#!/usr/bin/env python3
"""Evidence sidecar readiness probe.

The latest sidecar papers imply that an access/evidence-loop router must state
which supporting evidence is missing before it can safely answer:

- UniTime: temporal grounding / timestamp windows
- T*: sparse keyframe search in long or dense videos
- VidText: video text/OCR sidecars
- VideoMind: planner + grounder + verifier + answerer roles

This script maps those sidecar requirements onto the 58 external clips using the
existing assistant/task-affordance outputs.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
IN_CSV = CURSOR / "methods" / "output" / "task_assistant_affordance.csv"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "evidence_sidecar_readiness.csv"
OUT_JSON = OUT_DIR / "evidence_sidecar_readiness_summary.json"


def sidecars_for(row: pd.Series) -> dict:
    sidecars: set[str] = set()
    reason_bits: list[str] = []

    affordance = str(row["task_affordance"])
    assistant_mode = str(row["assistant_mode"])
    surface = str(row["surface"])
    speech_high = float(row["mean_speech_density"]) >= 0.75
    slot_low = float(row["mean_standard_slot_score"]) <= 0.15
    need_high = float(row["need_z"]) >= 0.60
    weak_margin = float(row["pro_margin"]) <= 0.02
    collision_high = float(row["social_collision_boundary"]) >= 1.0
    if affordance in {
        "evidence_indexed_video_agent",
        "stepwise_task_coach",
        "reality_video_task_coach",
    } or assistant_mode == "stateful_video_agent":
        sidecars.add("temporal_grounding")
        reason_bits.append("answer_needs_timestamped_video_evidence")

    if affordance in {"evidence_indexed_video_agent", "community_context_layer"} or (
        collision_high and surface in {"identity_chip", "creator_qc"}
    ):
        sidecars.add("keyframe_search")
        reason_bits.append("need_sparse_relevant_frames_not_uniform_sampling")

    if bool(row["hallucination_sensitive"]) or int(row["text_terms"]) > 0:
        sidecars.add("video_text_ocr")
        reason_bits.append("text_or_graphics_answer_is_hallucination_sensitive")

    if affordance in {"stepwise_task_coach", "reality_video_task_coach"}:
        sidecars.add("step_index")
        sidecars.add("completion_criteria")
        reason_bits.append("task_clip_needs_step_state_and_done_criteria")

    if affordance == "reality_video_task_coach" or bool(row["needs_current_state_monitoring"]):
        sidecars.add("current_state_monitor")
        reason_bits.append("user_physical_state_must_be_compared_to_video")

    if affordance == "route_or_spatial_rehearsal" or bool(row["depth_guard"]):
        sidecars.add("object_depth")
        reason_bits.append("spatial_guidance_needs_depth_or_obstacle_evidence")

    if speech_high or assistant_mode in {"verify_before_answer", "stateful_video_agent"}:
        sidecars.add("asr_transcript")
        reason_bits.append("audio_context_or_user_query_needs_transcript")

    if affordance == "community_context_layer" or bool(row["needs_human_or_community_layer"]):
        sidecars.add("community_quality_gate")
        reason_bits.append("viewer_or_human_context_needs_quality_filter")

    if assistant_mode == "verify_before_answer" or weak_margin or collision_high:
        sidecars.add("planner_grounder_verifier")
        reason_bits.append("weak_or_high_risk_answer_needs_explicit_verification")

    urgency = "low"
    if (
        (assistant_mode == "verify_before_answer" and weak_margin)
        or (weak_margin and collision_high)
        or (len(sidecars) >= 6 and (weak_margin or collision_high))
    ):
        urgency = "high"
    elif need_high or len(sidecars) >= 4 or (speech_high and slot_low):
        urgency = "medium"

    return {
        "required_sidecars": "|".join(sorted(sidecars)) if sidecars else "none",
        "sidecar_count": len(sidecars),
        "sidecar_urgency": urgency,
        "sidecar_reason": ";".join(reason_bits) if reason_bits else "watch_only_or_already_low_risk",
        "needs_temporal_grounding": "temporal_grounding" in sidecars,
        "needs_keyframe_search": "keyframe_search" in sidecars,
        "needs_video_text_ocr": "video_text_ocr" in sidecars,
        "needs_planner_grounder_verifier": "planner_grounder_verifier" in sidecars,
        "needs_object_depth": "object_depth" in sidecars,
        "needs_asr_transcript": "asr_transcript" in sidecars,
        "needs_current_state_monitor": "current_state_monitor" in sidecars,
        "needs_community_quality_gate": "community_quality_gate" in sidecars,
    }


def summarize(df: pd.DataFrame) -> dict:
    target = df["target"].astype(int).eq(1)
    return {
        "n_clips": int(len(df)),
        "urgency_counts": {str(k): int(v) for k, v in Counter(df["sidecar_urgency"]).items()},
        "mean_sidecar_count": float(df["sidecar_count"].mean()),
        "sidecar_need_counts": {
            col.removeprefix("needs_"): int(df[col].sum())
            for col in [
                "needs_temporal_grounding",
                "needs_keyframe_search",
                "needs_video_text_ocr",
                "needs_planner_grounder_verifier",
                "needs_object_depth",
                "needs_asr_transcript",
                "needs_current_state_monitor",
                "needs_community_quality_gate",
            ]
        },
        "high_urgency_target_n": int((target & df["sidecar_urgency"].eq("high")).sum()),
        "target_with_any_sidecar_rate": float((target & df["sidecar_count"].gt(0)).sum() / target.sum()) if target.sum() else 0.0,
        "no_sidecar_target_misses": int((target & df["sidecar_count"].eq(0)).sum()),
    }


def main() -> None:
    df = pd.read_csv(IN_CSV)
    rows = []
    for _, row in df.iterrows():
        rows.append({**row.to_dict(), **sidecars_for(row)})
    out = pd.DataFrame(rows).sort_values(
        ["sidecar_urgency", "sidecar_count", "followup_pressure"],
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
