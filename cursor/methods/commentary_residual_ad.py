#!/usr/bin/env python3
"""Commentary residual AD prototype.

Inspired by MCAD: before adding more AD, ask what the original audio/commentary
already carries and what visual state remains.

The current workspace does not contain ASR transcripts for the 58 external
clips. This script is transcript-ready, but falls back to a clearly labeled
`tier_summary_proxy` using tier1/tier2 summaries as a stand-in for audio-context
coverage. That keeps the metric auditable and prevents pretending we have ASR.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
EXT = CURSOR / "data" / "external_clips"
REGISTRY = EXT / "registry.jsonl"
ROUTER = CURSOR / "methods" / "output" / "access_surface_router.csv"
OUT_DIR = CURSOR / "methods" / "output"
OUT_CSV = OUT_DIR / "commentary_residual_ad.csv"
OUT_JSON = OUT_DIR / "commentary_residual_ad_summary.json"

STOP = {
    "the", "and", "that", "with", "from", "this", "they", "then", "into", "while",
    "there", "their", "them", "have", "has", "had", "are", "was", "were", "being",
    "been", "his", "her", "she", "him", "you", "your", "for", "off", "out", "over",
    "under", "near", "next", "some", "very", "more", "less", "onto", "also",
}
PERSON = {
    "man", "woman", "boy", "girl", "person", "people", "child", "children",
    "teenager", "player", "doctor", "teacher", "friend", "group", "someone",
}
ACTION = {
    "walk", "walks", "walking", "run", "runs", "running", "throw", "throws",
    "play", "plays", "playing", "hit", "hits", "using", "uses", "clean", "cleans",
    "talk", "talks", "eating", "gestures", "shaping", "stretching", "turns",
}
SPATIAL = {
    "room", "table", "floor", "couch", "bed", "kitchen", "garage", "workshop",
    "field", "court", "left", "right", "behind", "nearby", "across", "beside",
}
EMOTION = {
    "smile", "smiles", "smiling", "laugh", "laughs", "laughing", "giggle",
    "warm", "friendly", "relaxed", "pleased", "excited", "solemn",
}


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z]{3,}", text.lower()) if t not in STOP]


def token_set(text: str) -> set[str]:
    return set(tokens(text))


def jaccard(a: str, b: str) -> float:
    aa = token_set(a)
    bb = token_set(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def load_registry() -> dict[str, dict]:
    out = {}
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("download_ok", True):
                out[row["video_id"]] = row
    return out


def parse_json3(path: Path, start: float, end: float) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    words: list[str] = []
    for event in data.get("events", []):
        t0 = float(event.get("tStartMs", 0)) / 1000.0
        dur = float(event.get("dDurationMs", 0)) / 1000.0
        t1 = t0 + dur
        if t1 < start or t0 > end:
            continue
        for seg in event.get("segs", []) or []:
            utf8 = seg.get("utf8")
            if utf8:
                words.append(str(utf8))
    return " ".join(words).strip()


def transcript_for(meta: dict) -> tuple[str, str]:
    vid = meta["video_id"]
    clip_dir = EXT / vid
    for name in ["transcript.txt", "asr.txt", "commentary.txt"]:
        path = clip_dir / name
        if path.exists() and path.stat().st_size:
            return path.read_text(encoding="utf-8", errors="ignore"), name

    yt_id = meta.get("yt_id")
    if yt_id:
        for path in sorted(clip_dir.glob(f"{yt_id}*.json3")) + sorted(EXT.glob(f"{yt_id}*.json3")):
            text = parse_json3(path, float(meta.get("start", 0)), float(meta.get("end", 10)))
            if text:
                return text, "youtube_json3"

    proxy = " ".join([str(meta.get("tier1_vatex_short", "")), str(meta.get("tier2_vatex_long", ""))]).strip()
    return proxy, "tier_summary_proxy"


def residual_profile(pro: str, audio_context: str) -> dict:
    pro_terms = token_set(pro)
    audio_terms = token_set(audio_context)
    residual = sorted(pro_terms - audio_terms)
    overlap = jaccard(pro, audio_context)
    residual_text = " ".join(residual)
    return {
        "audio_overlap_penalty": overlap,
        "residual_term_count": len(residual),
        "residual_person_terms": sum(1 for t in residual if t in PERSON),
        "residual_action_terms": sum(1 for t in residual if t in ACTION),
        "residual_spatial_terms": sum(1 for t in residual if t in SPATIAL),
        "residual_emotion_terms": sum(1 for t in residual if t in EMOTION),
        "residual_visual_terms": " ".join(residual[:24]),
        "residual_text": residual_text,
    }


def action_for(row: pd.Series, profile: dict) -> tuple[str, str]:
    speech_high = float(row["mean_speech_density"]) >= 0.75
    need_high = float(row["need_z"]) >= 0.60
    slot_low = float(row["mean_standard_slot_score"]) <= 0.15
    overlap_high = float(profile["audio_overlap_penalty"]) >= 0.35
    residual_high = int(profile["residual_term_count"]) >= 12

    if speech_high and overlap_high and not residual_high:
        return "suppress_echo", "audio_proxy_already_covers_most_candidate_ad"
    if speech_high and need_high and slot_low and residual_high:
        return "queue_residual_replay", "dense_audio_high_need_and_many_residual_terms"
    if speech_high and residual_high:
        return "residual_concise_cue", "dense_audio_requires_short_residual_visual_state"
    if need_high and residual_high:
        return "describe_residual_now", "visual_need_high_and_audio_proxy_does_not_cover_candidate"
    return "static_ok", "low_residual_or_low_need"


def main() -> None:
    registry = load_registry()
    router = pd.read_csv(ROUTER)
    rows = []
    for _, r in router.iterrows():
        vid = str(r["video_id"])
        meta = registry.get(vid)
        if not meta:
            continue
        audio_context, source = transcript_for(meta)
        pro = str(meta.get("tier3_va11y", ""))
        profile = residual_profile(pro, audio_context)
        action, reason = action_for(r, profile)
        rows.append({
            "video_id": vid,
            "category": r["category"],
            "surface": r["surface"],
            "target": int(r["target"]),
            "pro_margin": float(r["pro_margin"]),
            "need_z": float(r["need_z"]),
            "mean_speech_density": float(r["mean_speech_density"]),
            "mean_standard_slot_score": float(r["mean_standard_slot_score"]),
            "audio_context_source": source,
            "audio_context_word_count": len(tokens(audio_context)),
            **profile,
            "residual_action": action,
            "residual_reason": reason,
        })

    out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    summary = {
        "n_clips": int(len(out)),
        "source_counts": {str(k): int(v) for k, v in Counter(out["audio_context_source"]).items()},
        "action_counts": {str(k): int(v) for k, v in Counter(out["residual_action"]).items()},
        "mean_audio_overlap_penalty": float(out["audio_overlap_penalty"].mean()),
        "mean_residual_term_count": float(out["residual_term_count"].mean()),
        "pro_not_best_action_counts": {
            str(k): int(v) for k, v in Counter(out[out["target"].eq(1)]["residual_action"]).items()
        },
        "router_surface_by_residual_action": {
            str(action): {str(k): int(v) for k, v in grp["surface"].value_counts().items()}
            for action, grp in out.groupby("residual_action")
        },
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
