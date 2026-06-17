#!/usr/bin/env python3
"""Access Surface OS prototype.

This is the first runnable version of the cross-paper synthesis:
TRIBE/proxy debt + audio density + category + text cues should route a clip to
an access surface, not just assign a caption quality score.

The rules are intentionally transparent. They are meant to create an inspectable
CSV over the 58 external clips before adding heavier identity, transcript, or VLM
models.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
ROWS = CURSOR / "output" / "tribe_social_collision_external_rows.csv"
REGISTRY = CURSOR / "data" / "external_clips" / "registry.jsonl"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "access_surface_router.csv"
OUT_JSON = OUT_DIR / "access_surface_router_summary.json"

SOCIAL_CATEGORIES = {
    "Entertainment",
    "People & Vlogs",
    "Health & Wellness",
    "Music",
    "Education, Seminar & Talks",
}
SPORTS_CATEGORIES = {"Sports"}
UTILITY_CATEGORIES = {"How-to & Instructional", "Education, Seminar & Talks", "Health & Wellness"}

PERSON_WORDS = {
    "man", "woman", "boy", "girl", "person", "people", "child", "children",
    "teenager", "player", "doctor", "teacher", "mother", "father", "friend",
    "group", "someone", "they", "he", "she", "his", "her",
}
EMOTION_WORDS = {
    "smile", "smiles", "smiling", "laugh", "laughs", "laughing", "giggle",
    "giggling", "happy", "sad", "angry", "anxious", "relaxed", "friendly",
    "warm", "excited", "solemn", "emotion", "emotional", "pleased",
}
SPATIAL_WORDS = {
    "room", "table", "couch", "floor", "nearby", "behind", "front", "left",
    "right", "beside", "across", "around", "background", "workshop", "kitchen",
    "garage", "bed", "stage", "field", "court",
}
AESTHETIC_WORDS = {
    "music", "drum", "cymbal", "studio", "scene", "atmosphere", "warm",
    "cozy", "creative", "landscape", "nature", "snowy", "water", "candle",
}
ACTION_WORDS = {
    "runs", "running", "walks", "walking", "throws", "plays", "hits", "uses",
    "cleans", "shaping", "molds", "gestures", "talks", "eating", "stretching",
    "massages", "jumps", "turns", "shoots", "navigates",
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def count_terms(text: str, vocab: set[str]) -> int:
    toks = tokenize(text)
    return sum(1 for tok in toks if tok in vocab)


def unique_overlap(a: str, b: str) -> float:
    aa = set(tok for tok in tokenize(a) if len(tok) > 3)
    bb = set(tok for tok in tokenize(b) if len(tok) > 3)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def load_registry() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("download_ok", True):
                rows[row["video_id"]] = row
    return rows


def risk_label(row: pd.Series) -> str:
    score = 0
    score += int(row["social_collision_boundary"] >= 1.0)
    score += int(row["mean_speech_density"] >= 0.75 and row["need_z"] >= 0.55)
    score += int(abs(float(row["pro_margin"])) <= 0.02)
    if score >= 3:
        return "high"
    if score == 2:
        return "medium"
    return "low"


def route(row: pd.Series, meta: dict) -> dict:
    pro = str(meta.get("tier3_va11y", ""))
    short = str(meta.get("tier1_vatex_short", ""))
    long = str(meta.get("tier2_vatex_long", ""))
    category = str(row["category"])

    person_count = count_terms(pro, PERSON_WORDS)
    emotion_count = count_terms(pro, EMOTION_WORDS)
    spatial_count = count_terms(pro, SPATIAL_WORDS)
    aesthetic_count = count_terms(pro, AESTHETIC_WORDS)
    action_count = count_terms(pro, ACTION_WORDS)
    pro_short_overlap = unique_overlap(pro, short)
    pro_long_overlap = unique_overlap(pro, long)
    audio_overlap_proxy = max(pro_short_overlap, pro_long_overlap)

    speech_high = float(row["mean_speech_density"]) >= 0.75
    need_high = float(row["need_z"]) >= 0.60
    collision_high = float(row["social_collision_boundary"]) >= 1.0
    slot_low = float(row["mean_standard_slot_score"]) <= 0.15
    negative_margin = float(row["pro_margin"]) < 0.0
    weak_or_negative_margin = float(row["pro_margin"]) <= 0.02
    social = int(row["social_scene"]) == 1

    surface = "static_ad"
    secondary = "none"
    reason = "low_collision_static_ad_is_probably_adequate"

    if category in SPORTS_CATEGORIES and speech_high:
        surface = "concise_cue"
        secondary = "defer_replay" if slot_low else "detail_chip"
        reason = "sports_or_action_clip_with_dense_audio_needs_commentary_residual_not_echo"
    elif social and collision_high and person_count >= 3:
        surface = "identity_chip"
        secondary = "emotive_style" if emotion_count else "detail_chip"
        reason = "social_collision_with_many_people_terms_needs_identity_or_relation_memory"
    elif social and collision_high and emotion_count >= 2:
        surface = "emotive_style"
        secondary = "detail_chip"
        reason = "emotion_or_reaction_is_likely_the_missing_visual_signal"
    elif speech_high and need_high and slot_low:
        surface = "defer_replay"
        secondary = "detail_chip"
        reason = "high_visual_need_but_no_audio_slot_for_linear_ad"
    elif speech_high and need_high:
        surface = "concise_cue"
        secondary = "detail_chip"
        reason = "high_need_with_dense_audio_prefers_short_then_optional_detail"
    elif weak_or_negative_margin and collision_high:
        surface = "creator_qc"
        secondary = "detail_chip"
        reason = "weak_grounding_margin_under_collision_requires_creator_verification"
    elif negative_margin and speech_high and slot_low:
        surface = "concise_cue"
        secondary = "defer_replay"
        reason = "negative_grounding_margin_with_dense_audio_and_no_slot_needs_concise_residual_cue"
    elif spatial_count >= 4 and need_high:
        surface = "object_explorer"
        secondary = "static_ad"
        reason = "spatial_or_object_inventory_likely_exceeds_linear_caption_budget"
    elif aesthetic_count >= 3 and not speech_high and category not in UTILITY_CATEGORIES:
        surface = "soundscape"
        secondary = "static_ad"
        reason = "aesthetic_low_speech_clip_can_use_optional_nonverbal_surface"

    risk = risk_label(row)
    compute_tier = "local"
    if surface == "creator_qc" or (risk == "high" and weak_or_negative_margin and (person_count >= 3 or emotion_count >= 2)):
        compute_tier = "human"
    elif risk == "high" or surface in {"identity_chip", "object_explorer", "emotive_style"}:
        compute_tier = "cloud"
    elif surface in {"defer_replay", "soundscape"}:
        compute_tier = "cached"

    return {
        "surface": surface,
        "secondary_surface": secondary,
        "reason": reason,
        "risk": risk,
        "compute_tier": compute_tier,
        "person_terms": person_count,
        "emotion_terms": emotion_count,
        "spatial_terms": spatial_count,
        "aesthetic_terms": aesthetic_count,
        "action_terms": action_count,
        "audio_overlap_proxy": round(audio_overlap_proxy, 4),
    }


def summarize(df: pd.DataFrame) -> dict:
    summary: dict[str, object] = {
        "n_clips": int(len(df)),
        "surface_counts": dict(Counter(df["surface"])),
        "risk_counts": dict(Counter(df["risk"])),
        "compute_tier_counts": dict(Counter(df["compute_tier"])),
    }
    high_collision = df[df["social_collision_boundary"] >= 1.0]
    if len(high_collision):
        summary["high_collision_n"] = int(len(high_collision))
        summary["high_collision_not_static_rate"] = float((high_collision["surface"] != "static_ad").mean())
        summary["high_collision_surface_counts"] = dict(Counter(high_collision["surface"]))
    return summary


def main() -> None:
    registry = load_registry()
    rows = pd.read_csv(ROWS)
    rows = rows[rows["score_col"].eq("clip_top3")].copy()
    out_rows = []
    for _, row in rows.iterrows():
        meta = registry.get(str(row["video_id"]), {})
        routed = route(row, meta)
        out_rows.append({**row.to_dict(), **routed})
    out = pd.DataFrame(out_rows).sort_values(
        ["risk", "social_collision_boundary", "need_z"],
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
