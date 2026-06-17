#!/usr/bin/env python3
"""Visual assistant skill policy probe.

This prototype applies the latest BLV-assistant paper batch to the 58 external
clips. It does not ask whether the caption is semantically good. It asks what
assistant behavior the system should prepare:

- likely follow-up / question anticipation
- verification before answering hallucination-sensitive requests
- stateful video-agent index for temporal/player questions
- depth/spatial guard for guidance-like scenes

The rules are intentionally lexical and auditable until we have ASR, OCR, and
object/depth models wired into the clip corpus.
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
ROUTER = CURSOR / "methods" / "output" / "access_surface_router.csv"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "visual_assistant_skill_policy.csv"
OUT_JSON = OUT_DIR / "visual_assistant_skill_policy_summary.json"

TEXT_WORDS = {
    "text", "label", "labels", "letter", "sign", "number", "numbers", "address",
    "recipe", "instructions", "dosage", "dose", "medication", "medicine", "nutrition",
    "ingredient", "ingredients", "expiration", "date", "price", "screen", "code",
}
IDENTITY_WORDS = {
    "man", "woman", "person", "people", "player", "doctor", "teacher", "child",
    "boy", "girl", "friend", "mother", "father", "someone", "group", "character",
}
SPATIAL_WORDS = {
    "left", "right", "front", "behind", "near", "nearby", "beside", "across",
    "around", "background", "foreground", "room", "table", "floor", "path",
    "door", "entrance", "street", "road", "sidewalk", "crosswalk", "stairs",
}
ACTION_WORDS = {
    "uses", "using", "does", "doing", "make", "makes", "shaping", "cleaning",
    "cooking", "playing", "throws", "walks", "runs", "turns", "gestures",
}
DEPTH_SAFETY_WORDS = {
    "path", "walk", "walking", "road", "street", "sidewalk", "crosswalk",
    "obstacle", "avoid", "behind", "ahead", "near", "nearby", "front",
    "door", "entrance", "stairs", "step", "steps",
}

QUESTION_PRIORS = {
    "How-to & Instructional": "how_do_i_do_this_or_what_step_is_next",
    "Education, Seminar & Talks": "what_visual_evidence_supports_the_talk",
    "Sports": "who_has_the_ball_and_what_just_changed",
    "People & Vlogs": "who_is_present_and_what_are_they_doing",
    "Entertainment": "who_changed_state_or_what_visual_reaction_matters",
    "Film & Animation": "what_visual_action_or_object_changed",
    "Health & Wellness": "is_the_body_position_or_safety_cue_correct",
    "Music": "who_or_what_instrument_is_active",
}


def toks(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def count_vocab(text: str, vocab: set[str]) -> int:
    return sum(1 for tok in toks(text) if tok in vocab)


def load_registry() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("download_ok", True):
                rows[str(row["video_id"])] = row
    return rows


def policy_for(row: pd.Series, meta: dict) -> dict:
    text = " ".join(
        [
            str(meta.get("tier3_va11y", "")),
            str(meta.get("tier2_vatex_long", "")),
            str(meta.get("tier1_vatex_short", "")),
        ]
    )
    category = str(row["category"])
    text_terms = count_vocab(text, TEXT_WORDS)
    identity_terms = count_vocab(text, IDENTITY_WORDS)
    spatial_terms = count_vocab(text, SPATIAL_WORDS)
    action_terms = count_vocab(text, ACTION_WORDS)
    depth_terms = count_vocab(text, DEPTH_SAFETY_WORDS)

    need = float(row["need_z"])
    speech = float(row["mean_speech_density"])
    collision = float(row["social_collision_boundary"])
    slot = float(row["mean_standard_slot_score"])
    margin = float(row["pro_margin"])
    surface = str(row["surface"])

    followup_pressure = 0.0
    followup_pressure += 0.24 * max(0.0, min(1.0, need))
    followup_pressure += 0.16 * max(0.0, min(1.0, speech))
    followup_pressure += 0.18 if surface in {"identity_chip", "defer_replay", "creator_qc"} else 0.0
    followup_pressure += 0.14 if collision >= 1.0 else 0.0
    followup_pressure += 0.12 if text_terms or spatial_terms >= 3 or identity_terms >= 3 else 0.0
    followup_pressure += 0.10 if margin <= 0.02 else 0.0
    followup_pressure += 0.06 if slot <= 0.15 and speech >= 0.75 else 0.0

    hallucination_sensitive = (
        text_terms > 0
        or depth_terms >= 2
        or "Health" in category
        or (category == "How-to & Instructional" and action_terms >= 2)
    )
    depth_guard = depth_terms >= 2 or (spatial_terms >= 4 and category in {"How-to & Instructional", "Sports"})
    needs_video_index = surface in {"defer_replay", "identity_chip"} or category in {
        "Sports",
        "Entertainment",
        "Film & Animation",
        "Music",
    }

    if hallucination_sensitive and margin <= 0.02:
        assistant_mode = "verify_before_answer"
        reason = "question_likely_and_answer_is_hallucination_sensitive"
    elif depth_guard:
        assistant_mode = "depth_guarded_guidance"
        reason = "spatial_or_navigation_answer_needs_depth_and_obstacle_standard"
    elif needs_video_index and followup_pressure >= 0.52:
        assistant_mode = "stateful_video_agent"
        reason = "likely_followup_requires_video_index_storyboard_or_history"
    elif followup_pressure >= 0.46:
        assistant_mode = "proactive_question_chip"
        reason = "historical_blv_question_prior_suggests_likely_followup"
    elif surface != "static_ad":
        assistant_mode = "passive_affordance"
        reason = "nonstatic_surface_should_offer_optional_question_path"
    else:
        assistant_mode = "plain_description"
        reason = "low_followup_pressure_and_low_hallucination_sensitivity"

    return {
        "question_prior": QUESTION_PRIORS.get(category, "what_detail_is_missing"),
        "assistant_mode": assistant_mode,
        "assistant_reason": reason,
        "followup_pressure": round(followup_pressure, 4),
        "hallucination_sensitive": hallucination_sensitive,
        "depth_guard": depth_guard,
        "needs_video_index": needs_video_index,
        "text_terms": text_terms,
        "identity_terms": identity_terms,
        "spatial_terms": spatial_terms,
        "action_terms": action_terms,
        "depth_safety_terms": depth_terms,
    }


def summarize(df: pd.DataFrame) -> dict:
    target = df["target"].astype(int).eq(1)
    not_plain = df["assistant_mode"].ne("plain_description")
    verify = df["assistant_mode"].eq("verify_before_answer")
    stateful = df["assistant_mode"].eq("stateful_video_agent")
    return {
        "n_clips": int(len(df)),
        "assistant_mode_counts": {str(k): int(v) for k, v in Counter(df["assistant_mode"]).items()},
        "mean_followup_pressure": float(df["followup_pressure"].mean()),
        "hallucination_sensitive_n": int(df["hallucination_sensitive"].sum()),
        "depth_guard_n": int(df["depth_guard"].sum()),
        "needs_video_index_n": int(df["needs_video_index"].sum()),
        "assistant_not_plain_target_recall": float((target & not_plain).sum() / target.sum()) if target.sum() else 0.0,
        "verify_before_answer_target_n": int((target & verify).sum()),
        "stateful_video_agent_target_n": int((target & stateful).sum()),
        "plain_description_target_misses": int((target & ~not_plain).sum()),
    }


def main() -> None:
    registry = load_registry()
    router = pd.read_csv(ROUTER)
    rows = []
    for _, row in router.iterrows():
        meta = registry.get(str(row["video_id"]), {})
        routed = policy_for(row, meta)
        rows.append({**row.to_dict(), **routed})
    out = pd.DataFrame(rows).sort_values(
        ["assistant_mode", "followup_pressure", "social_collision_boundary"],
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
