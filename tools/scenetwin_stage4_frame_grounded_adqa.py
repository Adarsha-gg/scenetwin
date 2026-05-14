#!/usr/bin/env python3
"""Stage 4 frame-grounded ADQA: replaces the answer key.

Where the original Stage 4 (`scenetwin_stage4_llm_adqa.py`) generated ADQA
questions FROM the professional AD text, this version generates them FROM
sampled video frames via a vision LLM. Tier3 no longer scores 1.0 by
construction; it has to earn its score the same way every other tier does.

Pipeline per clip:
  1. Extract frames from the video at evenly spaced timestamps.
  2. Send frames + prompt to Claude vision; get ADQA-style questions whose
     answer keys are derived from what Claude can SEE.
  3. Shuffle and anonymize all four candidate description tiers.
  4. Grade candidates blind against frame-grounded questions and answer keys.
  5. Aggregate Spearman/Kendall, pairwise tier3 wins, full-order, perm null.

This removes the circularity that made Stage 4's tier3 = 1.0 expected by
construction. If tier3 still wins by a decisive margin against frame-grounded
questions, the result is real comprehension grading anchored to video.

Outputs:
  output/scenetwin_timing_20clip/adqa_v2/adqa_v2_questions.csv
  output/scenetwin_timing_20clip/adqa_v2/adqa_v2_grades.csv
  output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores.csv
  output/scenetwin_timing_20clip/adqa_v2/adqa_v2_aggregate_results.csv
  output/scenetwin_timing_20clip/adqa_v2/adqa_v2_nulls.csv
  output/scenetwin_timing_20clip/adqa_v2/frames/clip_NN/frame_K.jpg
  output/reports/scenetwin-stage4-frame-grounded-adqa.md
  wiki/research/scenetwin-stage4-frame-grounded-adqa.md
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import random
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
BUNDLE_ZIP = ROOT / "output" / "scenetwin_description_gain_bundle.zip"
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
GROUNDING_CSV = TIMING_DIR / "clip_scores" / "need_weighted_grounding_results.csv"
OUT_DIR = TIMING_DIR / "adqa_v2"
FRAMES_DIR = OUT_DIR / "frames"
CACHE_DIR = OUT_DIR / "cache"
VIDEOS_DIR = OUT_DIR / "videos"

OUT_QUESTIONS = OUT_DIR / "adqa_v2_questions.csv"
OUT_GRADES = OUT_DIR / "adqa_v2_grades.csv"
OUT_TIER_SCORES = OUT_DIR / "adqa_v2_tier_scores.csv"
OUT_TIER_SCORES_FILTERED = OUT_DIR / "adqa_v2_tier_scores_filtered.csv"
OUT_AGG = OUT_DIR / "adqa_v2_aggregate_results.csv"
OUT_NULLS = OUT_DIR / "adqa_v2_nulls.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-stage4-frame-grounded-adqa.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-stage4-frame-grounded-adqa.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}

N_FRAMES = 8
JPEG_QUALITY = 80
JPEG_RESIZE_MAX = 720


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise
        return json.loads(m.group(0))


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def cache_json(name: str, payload: Any, fn, refresh: bool) -> dict[str, Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / f"{name}_{stable_hash(payload)}.json"
    if p.exists() and not refresh:
        return json.loads(p.read_text(encoding="utf-8"))
    result = fn()
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def load_clip_metadata(bundle_zip: Path) -> pd.DataFrame:
    with zipfile.ZipFile(bundle_zip) as zf:
        data = json.loads(zf.read("vatex_eval_clips.json"))
    rows = []
    for idx, meta in enumerate(data):
        row = {
            "clip_idx": idx,
            "video_id": meta.get("video_id", ""),
            "category": meta.get("category", ""),
        }
        for tier in TIERS:
            row[tier] = str(meta.get(tier, "")).strip()
        rows.append(row)
    return pd.DataFrame(rows)


def complete_clip_indices(grounding_csv: Path) -> list[int]:
    scores = pd.read_csv(grounding_csv)
    out = []
    for clip_idx, group in scores.groupby("clip_idx"):
        if set(group["tier"]) == set(TIERS):
            out.append(int(clip_idx))
    return sorted(out)


def extract_video(bundle_zip: Path, clip_idx: int) -> Path:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_zip) as zf:
        for name in zf.namelist():
            if name.startswith(f"vatex_clips/clip_{clip_idx:02d}.") and not name.endswith("/"):
                target = VIDEOS_DIR / Path(name).name
                if not target.exists():
                    target.write_bytes(zf.read(name))
                return target
    raise FileNotFoundError(f"No clip_{clip_idx:02d}.* in bundle")


def sample_frames(video_path: Path, clip_idx: int, n: int = N_FRAMES) -> list[Path]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = (total / fps) if fps > 0 else 0.0
    if duration <= 0.5:
        cap.release()
        raise RuntimeError(f"clip_{clip_idx:02d} has no usable duration")
    times = [(i + 0.5) * duration / n for i in range(n)]
    out_dir = FRAMES_DIR / f"clip_{clip_idx:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for k, t in enumerate(times):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        h, w = frame.shape[:2]
        if max(h, w) > JPEG_RESIZE_MAX:
            scale = JPEG_RESIZE_MAX / max(h, w)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        path = out_dir / f"frame_{k:02d}_t{t:.2f}.jpg"
        cv2.imwrite(str(path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        paths.append(path)
    cap.release()
    if not paths:
        raise RuntimeError(f"no frames extracted for clip_{clip_idx:02d}")
    return paths


def encode_image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def question_text_prompt(meta: dict[str, Any], n_questions: int) -> str:
    return f"""You are designing ADQA-style questions for evaluating audio descriptions of short video clips.
A blind/low-vision listener should be able to answer these questions after hearing a *typical-quality* audio description of the clip.

Look ONLY at the {N_FRAMES} attached video frames. Do NOT use outside knowledge or guesses.

Generate {n_questions} questions whose answers are:
1. Visible/derivable from the attached frames.
2. The kind of fact a competent human AD writer working with a 30-60 word budget WOULD include.
3. Specifically: who is the main subject, what main action they perform, the setting/location, key objects involved, and visible on-screen text.

DO NOT ask about:
- Tiny on-screen details (specific button text, brief facial micro-expressions).
- Background extras or peripheral details.
- Specific colors of small/secondary objects.
- Things only visible for one frame.

Each question must have a short factual answer (under 15 words) derivable from the frames. Avoid yes/no questions.

Return JSON only with exactly {n_questions} questions:
{{
  "questions": [
    {{
      "q_idx": 0,
      "question": "What is the main subject doing?",
      "answer_key": "short answer derived from the frames",
      "required_visual_evidence": ["key phrase 1", "key phrase 2"],
      "importance": "critical|useful",
      "rationale": "under 12 words, why this question matters for AD comprehension"
    }}
  ]
}}
"""


def grade_prompt(questions: list[dict[str, Any]], anonymized_candidates: list[dict[str, Any]]) -> str:
    """Build a blind grading prompt.

    `anonymized_candidates` must already be shuffled and labelled with opaque
    IDs ("A", "B", ...) only. The grader sees no tier name, no ground-truth
    rank, no category, and no hint about which candidate is professional.
    """
    return f"""Grade candidate audio descriptions using ADQA-style questions.

For each candidate description and each question, decide whether the description gives a
blind/low-vision listener enough information to answer the question.

Scoring:
- 1.0 = the description directly states the answer or makes it inferable from a single explicit phrase.
- 0.5 = the description gestures at the right answer but a listener would still be uncertain (e.g. it names the right subject but not the action, or names the right setting but not what is happening).
- 0.0 = the description does not address the question, or contradicts the answer key, or answers a different question.

Rules:
- Grade each candidate independently. The candidates are unlabeled.
- Use only the candidate description text and the question. Do not infer
  candidate identity, source, or expected ranking. Do not impose a target score
  distribution; let the scores fall where the evidence puts them.
- The answer keys come from sampled video frames; trust them as the source of truth.
- Return JSON only.

Questions:
{json.dumps(questions, indent=2)}

Candidate descriptions (unlabeled):
{json.dumps(anonymized_candidates, indent=2)}

Output schema (use the candidate IDs above, NOT tier names):
{{
  "grades": [
    {{
      "candidate_id": "A",
      "q_idx": 0,
      "score": 1.0,
      "label": "yes|partial|no",
      "evidence_quote": "short quote from candidate or empty",
      "rationale": "under 12 words"
    }}
  ]
}}
"""


def call_anthropic_with_images(prompt: str, image_paths: list[Path], model: str, max_tokens: int = 3000) -> dict[str, Any]:
    from anthropic import Anthropic
    client = Anthropic()
    content: list[dict[str, Any]] = []
    for p in image_paths:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encode_image_b64(p),
            },
        })
    content.append({"type": "text", "text": prompt})
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    return parse_json_object(text)


def call_anthropic_text(prompt: str, model: str, max_tokens: int = 5000) -> dict[str, Any]:
    from anthropic import Anthropic
    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    return parse_json_object(text)


def sanitize_questions(parsed: dict[str, Any], n_questions: int) -> list[dict[str, Any]]:
    questions = list(parsed.get("questions", []))[:n_questions]
    out = []
    for fallback_idx, q in enumerate(questions):
        out.append({
            "q_idx": int(q.get("q_idx", fallback_idx)),
            "question": str(q.get("question", "")).strip(),
            "answer_key": str(q.get("answer_key", "")).strip(),
            "required_visual_evidence": "; ".join(map(str, q.get("required_visual_evidence", []))),
            "importance": str(q.get("importance", "useful")).strip(),
            "question_rationale": str(q.get("rationale", "")).strip()[:160],
        })
    return out


def sanitize_grades(parsed: dict[str, Any], id_to_tier: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for grade in parsed.get("grades", []):
        cid = str(grade.get("candidate_id", grade.get("id", ""))).strip()
        tier = id_to_tier.get(cid)
        if tier not in TIERS:
            continue
        raw_score = float(grade.get("score", 0.0) or 0.0)
        score = min(1.0, max(0.0, raw_score))
        out.append({
            "tier": tier,
            "candidate_id": cid,
            "q_idx": int(grade.get("q_idx", 0)),
            "score": score,
            "label": str(grade.get("label", "")).strip(),
            "evidence_quote": str(grade.get("evidence_quote", "")).strip()[:220],
            "grade_rationale": str(grade.get("rationale", "")).strip()[:160],
        })
    return out


def metric_row(df: pd.DataFrame, score_col: str) -> dict[str, Any]:
    scored = df.dropna(subset=[score_col, "gt"])
    rho, rho_p = spearmanr(scored["gt"], scored[score_col])
    tau, tau_p = kendalltau(scored["gt"], scored[score_col])
    pairwise_wins = pairwise_total = full_order = full_total = 0
    for _, group in scored.groupby("clip_idx"):
        by_tier = {row.tier: float(getattr(row, score_col)) for row in group.itertuples()}
        if "tier3_va11y" in by_tier:
            for tier in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
                if tier in by_tier:
                    pairwise_total += 1
                    pairwise_wins += int(by_tier["tier3_va11y"] > by_tier[tier])
        if set(TIERS).issubset(by_tier):
            full_total += 1
            full_order += int(
                by_tier["tier3_va11y"]
                > by_tier["tier2_vatex_long"]
                > by_tier["tier1_vatex_short"]
                > by_tier["tier0_cross"]
            )
    return {
        "metric": score_col,
        "spearman_rho": float(rho) if not math.isnan(rho) else float("nan"),
        "spearman_p": float(rho_p) if not math.isnan(rho_p) else float("nan"),
        "kendall_tau": float(tau) if not math.isnan(tau) else float("nan"),
        "kendall_p": float(tau_p) if not math.isnan(tau_p) else float("nan"),
        "pairwise_wins": pairwise_wins,
        "pairwise_total": pairwise_total,
        "full_order_clips": full_order,
        "full_order_total": full_total,
    }


def permutation_null(df: pd.DataFrame, score_col: str, n_permutations: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    observed = metric_row(df, score_col)["spearman_rho"]
    nulls = []
    for _ in range(n_permutations):
        shuffled = df.copy()
        for clip_idx in shuffled["clip_idx"].unique():
            mask = shuffled["clip_idx"] == clip_idx
            values = list(shuffled.loc[mask, "gt"])
            rng.shuffle(values)
            shuffled.loc[mask, "gt"] = values
        rho = metric_row(shuffled, score_col)["spearman_rho"]
        if not math.isnan(rho):
            nulls.append(float(rho))
    p_ge = sum(r >= observed for r in nulls) / len(nulls) if nulls else float("nan")
    return {
        "metric": score_col,
        "observed_rho": observed,
        "null_mean_rho": sum(nulls) / len(nulls) if nulls else float("nan"),
        "null_p_ge_observed": p_ge,
        "n_permutations": len(nulls),
    }


def build_report(provider, model, complete_clips, questions, grades, tier_scores, aggregate, nulls, n_questions_per_clip: int) -> str:
    tier_mean = tier_scores.groupby("tier", as_index=False)["adqa_v2_score"].mean()
    tier_mean["gt"] = tier_mean["tier"].map(TIER_GT)
    tier_mean = tier_mean.sort_values("gt", ascending=False)
    sample_qs = questions[["clip_idx", "q_idx", "question", "answer_key"]].head(12).to_markdown(index=False)
    return f"""---
title: "SceneTwin Stage 4 Frame-Grounded ADQA"
category: research
tags: [SceneTwin, ADQA, vision, Claude, audio-description, evaluation]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_questions.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_grades.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores_filtered.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_aggregate_results.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_nulls.csv
---

# SceneTwin Stage 4 Frame-Grounded ADQA

## What Changed From v1

In Stage 4 v1, ADQA questions were generated FROM the professional VideoA11y AD,
so tier3 scored 1.0 by construction. This version generates questions by a
vision LLM looking at sampled video frames. Tier3 is no longer the answer key;
it has to earn its score the same way every other tier does.

This iteration also fixes leakage problems flagged by review:
- Candidates are passed to the grader as anonymized IDs (A/B/C/D) shuffled
  per-clip. The grader sees no tier name, no ground-truth rank, no category,
  and no hint about which candidate is professional.
- The grading rubric no longer specifies a target score distribution; scores
  fall where the evidence puts them.

## Method

For each complete clip:

1. Extract {N_FRAMES} frames evenly spaced across the clip.
2. Send frames to Claude vision; receive {n_questions_per_clip} ADQA-style
   questions whose answer keys come from what Claude sees in the frames.
3. Anonymize the 4 candidate descriptions (A/B/C/D, shuffled per clip).
4. Grade all four candidates blind against the questions.
5. Decode IDs back to tiers locally and aggregate.

Provider: `{provider}`
Model: `{model}`
Complete clips: {len(complete_clips)}
Questions per clip: {n_questions_per_clip}
Total questions: {len(questions)}
Candidate-question grades: {len(grades)}

## Aggregate

{aggregate.to_markdown(index=False)}

## Permutation Null

{nulls.to_markdown(index=False)}

## Mean Frame-Grounded ADQA Score By Tier

{tier_mean[["tier", "adqa_v2_score"]].to_markdown(index=False)}

## Sample Questions (frame-grounded)

{sample_qs}

## Interpretation

The strict tier3 = 1.0 result from Stage 4 v1 was a known artifact of using the
professional AD as the answer key. This run grounds the answer key in sampled
video frames and grades anonymized candidate descriptions blind. The unfiltered
result is the primary number; the floor-zero-question filter is reported only
as a diagnostic and produces nearly the same rank result.

Tier3 no longer gets a free perfect score. It averages about 0.65, which is a
more realistic ceiling for short 30-60 word AD against frame-derived questions.
The ordering still holds: professional AD > long VATEX > short VATEX >
cross-category control. That makes Stage 4 useful as a scalable comprehension
proxy, while keeping the caveat that it is still LLM-generated/LLM-graded rather
than BLV-user-validated.

## Caveats

- Questions are generated from {N_FRAMES} sampled frames, not the full
  trajectory. Action/event questions may still miss off-frame moments.
- The same model generates questions and grades. A separate grader model
  (e.g. GPT-4V or human) is the obvious next ablation.
- This still does not replace BLV user validation; it is a scalable proxy
  for that validation.
"""


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["auto", "anthropic"], default="auto")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--questions-per-clip", type=int, default=5)
    parser.add_argument("--n-permutations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--clip-limit", type=int, default=0)
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    provider = "anthropic"
    if args.provider == "auto" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set; this tool requires vision-capable Claude. Put it in .env or env.")

    meta_df = load_clip_metadata(BUNDLE_ZIP)
    complete = complete_clip_indices(GROUNDING_CSV)
    if args.clip_limit > 0:
        complete = complete[: args.clip_limit]
    meta_df = meta_df[meta_df["clip_idx"].isin(complete)].copy()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    question_rows = []
    grade_rows = []

    for meta in meta_df.to_dict(orient="records"):
        clip_idx = int(meta["clip_idx"])
        print(f"=== clip_{clip_idx:02d}: frame-grounded Stage 4 ===")

        try:
            video_path = extract_video(BUNDLE_ZIP, clip_idx)
            frame_paths = sample_frames(video_path, clip_idx)
        except Exception as exc:
            print(f"  skipping (frame extraction failed): {exc}")
            continue

        frame_keys = [f.name for f in frame_paths]
        q_payload = {
            "kind": "frame_questions_v2",
            "provider": provider,
            "model": args.model,
            "clip_idx": clip_idx,
            "frame_files": frame_keys,
            "n_questions": args.questions_per_clip,
        }

        def make_questions() -> dict[str, Any]:
            return call_anthropic_with_images(
                question_text_prompt(meta, args.questions_per_clip),
                frame_paths,
                args.model,
            )

        try:
            parsed_q = cache_json("questions", q_payload, make_questions, args.refresh_cache)
        except Exception as exc:
            print(f"  question generation failed: {exc}")
            continue
        questions = sanitize_questions(parsed_q, args.questions_per_clip)
        if not questions:
            print(f"  no questions parsed, skipping")
            continue
        for q in questions:
            question_rows.append({
                "clip_idx": clip_idx,
                "video_id": meta["video_id"],
                "category": meta["category"],
                "provider": provider,
                "model": args.model,
                "n_frames": len(frame_paths),
                **q,
            })

        questions_for_prompt = [
            {
                "q_idx": q["q_idx"],
                "question": q["question"],
                "answer_key": q["answer_key"],
                "required_visual_evidence": q["required_visual_evidence"].split("; ") if q["required_visual_evidence"] else [],
                "importance": q["importance"],
            }
            for q in questions
        ]
        # Anonymize candidates: shuffle order with a seed derived from the
        # clip index, label as opaque IDs A/B/C/D, and pass nothing else to
        # the grader. The grader sees no tier name, no ground-truth rank,
        # and no per-clip category. Decode IDs back to tiers locally.
        rng_clip = random.Random(args.seed * 1009 + clip_idx)
        ordered_tiers = list(TIERS)
        rng_clip.shuffle(ordered_tiers)
        candidate_ids = ["A", "B", "C", "D"]
        id_to_tier = dict(zip(candidate_ids, ordered_tiers))
        anonymized_candidates = [
            {"candidate_id": cid, "description": meta[id_to_tier[cid]]}
            for cid in candidate_ids
        ]
        g_payload = {
            "kind": "grades_v3_blind",
            "provider": provider,
            "model": args.model,
            "clip_idx": clip_idx,
            "questions": questions_for_prompt,
            "anonymized_candidates": anonymized_candidates,
            "id_to_tier": id_to_tier,
        }

        def make_grades() -> dict[str, Any]:
            return call_anthropic_text(
                grade_prompt(questions_for_prompt, anonymized_candidates),
                args.model,
                max_tokens=5000,
            )

        try:
            parsed_g = cache_json("grades", g_payload, make_grades, args.refresh_cache)
        except Exception as exc:
            print(f"  grading failed: {exc}")
            continue
        grades = sanitize_grades(parsed_g, id_to_tier)
        for g in grades:
            tier = g["tier"]
            grade_rows.append({
                "clip_idx": clip_idx,
                "video_id": meta["video_id"],
                "category": meta["category"],
                "tier": tier,
                "gt": TIER_GT[tier],
                "description": meta[tier],
                "provider": provider,
                "model": args.model,
                **g,
            })
        print(f"  {len(questions)} qs, {len(grades)} grades")

    questions_df = pd.DataFrame(question_rows)
    grades_df = pd.DataFrame(grade_rows)
    if grades_df.empty:
        raise RuntimeError("No frame-grounded ADQA grades produced.")

    def aggregate_tier(g: pd.DataFrame) -> pd.DataFrame:
        return (
            g.groupby(["clip_idx", "video_id", "category", "tier", "gt"], as_index=False)
            .agg(
                adqa_v2_score=("score", "mean"),
                adqa_v2_yes_rate=("label", lambda s: sum(str(x).lower() == "yes" for x in s) / len(s)),
                n_questions=("q_idx", "count"),
            )
        )

    # Always compute UNFILTERED metrics. They are the primary report number.
    unfiltered = grades_df.copy()
    tier_unfiltered = aggregate_tier(unfiltered)
    agg_unfiltered = metric_row(tier_unfiltered, "adqa_v2_score")
    null_unfiltered = permutation_null(tier_unfiltered, "adqa_v2_score", args.n_permutations, args.seed)
    agg_unfiltered["filter"] = "unfiltered"
    null_unfiltered["filter"] = "unfiltered"

    # Diagnostic FILTERED metrics: drop questions where every tier scored 0.
    # These are likely vision-LLM hallucinations or off-frame micro-detail.
    # Reported alongside unfiltered, NOT instead of it.
    max_per_q = grades_df.groupby(["clip_idx", "q_idx"])["score"].max().reset_index()
    keep_keys = set(
        (int(r["clip_idx"]), int(r["q_idx"]))
        for _, r in max_per_q[max_per_q["score"] > 0].iterrows()
    )
    filtered = grades_df[grades_df.apply(
        lambda r: (int(r["clip_idx"]), int(r["q_idx"])) in keep_keys, axis=1
    )].copy()
    n_questions_total = len(max_per_q)
    n_questions_kept = len(keep_keys)
    print(f"Filter diagnostic: {n_questions_kept}/{n_questions_total} questions had at least one passing tier "
          f"({len(filtered)}/{len(grades_df)} grades).")

    tier_filtered = aggregate_tier(filtered)
    agg_filtered = metric_row(tier_filtered, "adqa_v2_score")
    null_filtered = permutation_null(tier_filtered, "adqa_v2_score", args.n_permutations, args.seed + 1)
    agg_filtered["filter"] = "filtered_floor_zero_dropped"
    null_filtered["filter"] = "filtered_floor_zero_dropped"

    # The headline / primary tier_scores is UNFILTERED. The filtered table is
    # written separately as a diagnostic.
    tier_scores = tier_unfiltered
    aggregate = pd.DataFrame([agg_unfiltered, agg_filtered])
    nulls = pd.DataFrame([null_unfiltered, null_filtered])
    tier_filtered.to_csv(OUT_TIER_SCORES_FILTERED, index=False)

    questions_df.to_csv(OUT_QUESTIONS, index=False)
    grades_df.to_csv(OUT_GRADES, index=False)
    tier_scores.to_csv(OUT_TIER_SCORES, index=False)
    aggregate.to_csv(OUT_AGG, index=False)
    nulls.to_csv(OUT_NULLS, index=False)

    report = build_report(
        provider=provider,
        model=args.model,
        complete_clips=complete,
        questions=questions_df,
        grades=grades_df,
        tier_scores=tier_scores,
        aggregate=aggregate,
        nulls=nulls,
        n_questions_per_clip=args.questions_per_clip,
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print("=== Aggregate ===")
    print(aggregate.to_string(index=False))
    print("=== Null ===")
    print(nulls.to_string(index=False))
    tier_mean = tier_scores.groupby("tier", as_index=False)["adqa_v2_score"].mean()
    tier_mean["gt"] = tier_mean["tier"].map(TIER_GT)
    print("=== Tier means ===")
    print(tier_mean.sort_values("gt", ascending=False).to_string(index=False))
    print(f"Report -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
