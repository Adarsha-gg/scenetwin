#!/usr/bin/env python3
"""Stage 4 LLM-ADQA audit for SceneTwin.

This adds a functional-comprehension layer to the surviving SceneTwin stack.
For each complete 20-clip timing result, it:

1. Generates ADQA-style visual/narrative questions from the professional
   VideoA11y description.
2. Grades each candidate description tier against those questions.
3. Aggregates pass rates by tier and writes a report.

The generated questions use the professional AD as a reference answer key, so
this is a scalable proxy for ADQA, not a substitute for BLV user validation.

Outputs:
  output/scenetwin_timing_20clip/adqa/adqa_questions.csv
  output/scenetwin_timing_20clip/adqa/adqa_grades.csv
  output/scenetwin_timing_20clip/adqa/adqa_tier_scores.csv
  output/scenetwin_timing_20clip/adqa/adqa_aggregate_results.csv
  output/scenetwin_timing_20clip/adqa/adqa_nulls.csv
  output/reports/scenetwin-stage4-llm-adqa.md
  wiki/research/scenetwin-stage4-llm-adqa.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
BUNDLE_ZIP = ROOT / "output" / "scenetwin_description_gain_bundle.zip"
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
GROUNDING_CSV = TIMING_DIR / "clip_scores" / "need_weighted_grounding_results.csv"
ADQA_DIR = TIMING_DIR / "adqa"
CACHE_DIR = ADQA_DIR / "cache"

OUT_QUESTIONS = ADQA_DIR / "adqa_questions.csv"
OUT_GRADES = ADQA_DIR / "adqa_grades.csv"
OUT_TIER_SCORES = ADQA_DIR / "adqa_tier_scores.csv"
OUT_AGG = ADQA_DIR / "adqa_aggregate_results.csv"
OUT_NULLS = ADQA_DIR / "adqa_nulls.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-stage4-llm-adqa.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-stage4-llm-adqa.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {
    "tier0_cross": 0,
    "tier1_vatex_short": 1,
    "tier2_vatex_long": 2,
    "tier3_va11y": 3,
}


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def cache_json(name: str, payload: Any, fn, refresh: bool) -> dict[str, Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{name}_{stable_hash(payload)}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    result = fn()
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def load_clip_metadata(bundle_zip: Path) -> pd.DataFrame:
    with zipfile.ZipFile(bundle_zip) as zf:
        data = json.loads(zf.read("vatex_eval_clips.json"))
    rows = []
    for idx, meta in enumerate(data):
        row = {
            "clip_idx": idx,
            "video_id": meta.get("video_id", ""),
            "yt_id": meta.get("yt_id", ""),
            "start": meta.get("start"),
            "end": meta.get("end"),
            "category": meta.get("category", ""),
        }
        for tier in TIERS:
            row[tier] = str(meta.get(tier, "")).strip()
        rows.append(row)
    return pd.DataFrame(rows)


def complete_clip_indices(grounding_csv: Path) -> list[int]:
    scores = pd.read_csv(grounding_csv)
    complete = []
    for clip_idx, group in scores.groupby("clip_idx"):
        if set(group["tier"]) == set(TIERS):
            complete.append(int(clip_idx))
    return sorted(complete)


def question_prompt(meta: dict[str, Any], n_questions: int) -> str:
    return f"""Generate ADQA-style questions for evaluating audio description.

You are designing questions a blind/low-vision listener should be able to
answer after hearing a good audio description of this clip.

Use the professional AD as the reference answer key. Do not ask about facts
that are absent from the reference. Prefer concrete visual/narrative facts:
actions, objects, spatial relations, character behavior, and readable text.

Clip metadata:
- clip_idx: {meta["clip_idx"]}
- category: {meta["category"]}
- video_id: {meta["video_id"]}

Professional AD reference:
{meta["tier3_va11y"]}

Return JSON only with exactly {n_questions} questions:
{{
  "questions": [
    {{
      "q_idx": 0,
      "question": "What visible action happens?",
      "answer_key": "short reference answer",
      "required_visual_evidence": ["key phrase 1", "key phrase 2"],
      "importance": "critical|useful",
      "rationale": "under 12 words"
    }}
  ]
}}
"""


def grade_prompt(meta: dict[str, Any], questions: list[dict[str, Any]]) -> str:
    candidates = [
        {
            "tier": tier,
            "gt": TIER_GT[tier],
            "description": meta[tier],
        }
        for tier in TIERS
    ]
    return f"""Grade candidate audio descriptions using ADQA-style questions.

For each candidate and each question, decide whether the description gives a
blind/low-vision listener enough information to answer the question.

Scoring:
- 1.0 = answers the question clearly.
- 0.5 = partially answers, vague but usable, or missing one key detail.
- 0.0 = does not answer or contradicts the answer key.

Rules:
- Grade only the candidate description text. Do not reward outside knowledge.
- Cross-category descriptions should score 0 unless they accidentally answer.
- Be stricter for concrete actions/objects than for broad scene context.
- Return JSON only.

Clip:
- clip_idx: {meta["clip_idx"]}
- category: {meta["category"]}

Questions:
{json.dumps(questions, indent=2)}

Candidate descriptions:
{json.dumps(candidates, indent=2)}

Output schema:
{{
  "grades": [
    {{
      "tier": "tier3_va11y",
      "q_idx": 0,
      "score": 1.0,
      "label": "yes|partial|no",
      "evidence_quote": "short quote or empty",
      "rationale": "under 12 words"
    }}
  ]
}}
"""


def call_anthropic(prompt: str, model: str, max_tokens: int = 3000) -> dict[str, Any]:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return parse_json_object(text)


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip(" .") for p in pieces if p.strip()]


def keywords(text: str) -> set[str]:
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "at", "with",
        "is", "are", "was", "were", "he", "she", "they", "it", "his", "her",
        "their", "as", "by", "for", "from", "into", "this", "that", "while",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", text.lower())
    return {w for w in words if w not in stop}


def local_questions(meta: dict[str, Any], n_questions: int) -> dict[str, Any]:
    sentences = split_sentences(meta["tier3_va11y"])
    if not sentences:
        sentences = [meta["tier3_va11y"]]
    questions = []
    for q_idx, sent in enumerate(sentences[:n_questions]):
        keys = sorted(keywords(sent), key=len, reverse=True)[:5]
        questions.append({
            "q_idx": q_idx,
            "question": f"What key visual detail is described here: {sent}?",
            "answer_key": sent,
            "required_visual_evidence": keys,
            "importance": "critical" if q_idx == 0 else "useful",
            "rationale": "offline fallback",
        })
    while len(questions) < n_questions:
        q_idx = len(questions)
        questions.append({
            "q_idx": q_idx,
            "question": "What is the main visual event in the clip?",
            "answer_key": meta["tier3_va11y"],
            "required_visual_evidence": sorted(keywords(meta["tier3_va11y"]))[:5],
            "importance": "useful",
            "rationale": "offline fallback",
        })
    return {"questions": questions}


def local_grades(meta: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any]:
    grades = []
    for tier in TIERS:
        desc_words = keywords(meta[tier])
        for question in questions:
            evidence_words = set()
            for phrase in question.get("required_visual_evidence", []):
                evidence_words |= keywords(str(phrase))
            if not evidence_words:
                evidence_words = keywords(str(question.get("answer_key", "")))
            overlap = len(desc_words & evidence_words)
            denom = max(1, len(evidence_words))
            ratio = overlap / denom
            if ratio >= 0.45:
                score, label = 1.0, "yes"
            elif ratio >= 0.2:
                score, label = 0.5, "partial"
            else:
                score, label = 0.0, "no"
            grades.append({
                "tier": tier,
                "q_idx": int(question["q_idx"]),
                "score": score,
                "label": label,
                "evidence_quote": "",
                "rationale": "offline fallback",
            })
    return {"grades": grades}


def sanitize_questions(parsed: dict[str, Any], n_questions: int) -> list[dict[str, Any]]:
    questions = list(parsed.get("questions", []))[:n_questions]
    out = []
    for fallback_idx, q in enumerate(questions):
        q_idx = int(q.get("q_idx", fallback_idx))
        out.append({
            "q_idx": q_idx,
            "question": str(q.get("question", "")).strip(),
            "answer_key": str(q.get("answer_key", "")).strip(),
            "required_visual_evidence": "; ".join(map(str, q.get("required_visual_evidence", []))),
            "importance": str(q.get("importance", "useful")).strip(),
            "question_rationale": str(q.get("rationale", "")).strip()[:160],
        })
    return out


def sanitize_grades(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for grade in parsed.get("grades", []):
        tier = str(grade.get("tier", ""))
        if tier not in TIERS:
            continue
        raw_score = float(grade.get("score", 0.0) or 0.0)
        score = min(1.0, max(0.0, raw_score))
        out.append({
            "tier": tier,
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
    pairwise_wins = 0
    pairwise_total = 0
    full_order = 0
    full_total = 0
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
        "spearman_rho": float(rho),
        "spearman_p": float(rho_p),
        "kendall_tau": float(tau),
        "kendall_p": float(tau_p),
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


def build_report(
    provider: str,
    model: str,
    complete_clips: list[int],
    questions: pd.DataFrame,
    grades: pd.DataFrame,
    tier_scores: pd.DataFrame,
    aggregate: pd.DataFrame,
    nulls: pd.DataFrame,
) -> str:
    tier_mean = tier_scores.groupby("tier", as_index=False)["adqa_score"].mean()
    tier_mean["gt"] = tier_mean["tier"].map(TIER_GT)
    tier_mean = tier_mean.sort_values("gt", ascending=False)
    agg_md = aggregate.to_markdown(index=False)
    null_md = nulls.to_markdown(index=False)
    tier_md = tier_mean[["tier", "adqa_score"]].to_markdown(index=False)
    sample_cols = ["clip_idx", "q_idx", "question", "answer_key"]
    sample_questions = questions[sample_cols].head(12).to_markdown(index=False)

    caveat = (
        "This run used Anthropic for generation/grading."
        if provider == "anthropic"
        else "This run used the offline local fallback, so it is a code smoke test, not evidence."
    )

    return f"""---
title: "SceneTwin Stage 4 LLM-ADQA"
category: research
tags: [SceneTwin, ADQA, Claude, audio-description, evaluation]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_timing_20clip/adqa/adqa_questions.csv
  - output/scenetwin_timing_20clip/adqa/adqa_grades.csv
  - output/scenetwin_timing_20clip/adqa/adqa_tier_scores.csv
  - output/scenetwin_timing_20clip/adqa/adqa_aggregate_results.csv
  - output/scenetwin_timing_20clip/adqa/adqa_nulls.csv
---

# SceneTwin Stage 4 LLM-ADQA

## Question

Can SceneTwin add a functional-comprehension audit layer after TRIBE timing,
CLIP grounding, and OCR coverage?

## Method

For each complete 20-clip timing result, Stage 4 generated ADQA-style questions
from the professional VideoA11y description, then graded every candidate
description tier against those questions. This tests whether a listener could
answer concrete visual/narrative questions from the AD text.

Provider: `{provider}`  
Model: `{model}`  
Complete clips: {len(complete_clips)}  
Questions: {len(questions)}  
Candidate-question grades: {len(grades)}

{caveat}

## Aggregate Results

{agg_md}

## Permutation Null

{null_md}

## Mean ADQA Score By Tier

{tier_md}

## Sample Questions

{sample_questions}

## Interpretation

Stage 4 is the missing user-comprehension layer in the SceneTwin audit stack. It
does not replace BLV validation: the questions are generated from professional
AD text, not from human participants or timestamped visual QA annotations. Its
value is that it turns "does the text look similar?" into "does the text answer
the visual questions a listener needs answered?" at corpus scale.

If the Anthropic run preserves the expected tier order, the system pitch becomes
stronger: TRIBE prioritizes windows, CLIP/OCR catch visual grounding obligations,
and LLM-ADQA checks functional comprehension.
"""


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["auto", "anthropic", "local-fallback"], default="auto")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--questions-per-clip", type=int, default=3)
    parser.add_argument("--n-permutations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--clip-limit", type=int, default=0)
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    provider = args.provider.replace("-", "_")
    if provider == "auto":
        provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "local_fallback"

    meta_df = load_clip_metadata(BUNDLE_ZIP)
    complete = complete_clip_indices(GROUNDING_CSV)
    if args.clip_limit > 0:
        complete = complete[: args.clip_limit]
    meta_df = meta_df[meta_df["clip_idx"].isin(complete)].copy()

    ADQA_DIR.mkdir(parents=True, exist_ok=True)
    question_rows = []
    grade_rows = []

    for meta in meta_df.to_dict(orient="records"):
        clip_idx = int(meta["clip_idx"])
        print(f"=== clip_{clip_idx:02d}: Stage 4 ADQA ===")
        q_payload = {
            "kind": "questions",
            "provider": provider,
            "model": args.model,
            "clip_idx": clip_idx,
            "reference": meta["tier3_va11y"],
            "n_questions": args.questions_per_clip,
        }

        def make_questions() -> dict[str, Any]:
            if provider == "anthropic":
                return call_anthropic(question_prompt(meta, args.questions_per_clip), args.model)
            return local_questions(meta, args.questions_per_clip)

        parsed_q = cache_json("questions", q_payload, make_questions, args.refresh_cache)
        questions = sanitize_questions(parsed_q, args.questions_per_clip)
        for q in questions:
            question_rows.append({
                "clip_idx": clip_idx,
                "video_id": meta["video_id"],
                "category": meta["category"],
                "provider": provider,
                "model": args.model if provider == "anthropic" else "local-fallback",
                **q,
            })

        questions_for_prompt = [
            {
                "q_idx": q["q_idx"],
                "question": q["question"],
                "answer_key": q["answer_key"],
                "required_visual_evidence": q["required_visual_evidence"].split("; "),
                "importance": q["importance"],
            }
            for q in questions
        ]
        g_payload = {
            "kind": "grades",
            "provider": provider,
            "model": args.model,
            "clip_idx": clip_idx,
            "questions": questions_for_prompt,
            "candidates": {tier: meta[tier] for tier in TIERS},
        }

        def make_grades() -> dict[str, Any]:
            if provider == "anthropic":
                return call_anthropic(grade_prompt(meta, questions_for_prompt), args.model, max_tokens=5000)
            return local_grades(meta, questions_for_prompt)

        parsed_g = cache_json("grades", g_payload, make_grades, args.refresh_cache)
        grades = sanitize_grades(parsed_g)
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
                "model": args.model if provider == "anthropic" else "local-fallback",
                **g,
            })

    questions_df = pd.DataFrame(question_rows)
    grades_df = pd.DataFrame(grade_rows)
    if grades_df.empty:
        raise RuntimeError("No ADQA grades produced.")

    tier_scores = (
        grades_df.groupby(["clip_idx", "video_id", "category", "tier", "gt"], as_index=False)
        .agg(
            adqa_score=("score", "mean"),
            adqa_yes_rate=("label", lambda s: sum(str(x).lower() == "yes" for x in s) / len(s)),
            n_questions=("q_idx", "count"),
        )
    )
    aggregate = pd.DataFrame([metric_row(tier_scores, "adqa_score")])
    nulls = pd.DataFrame([
        permutation_null(tier_scores, "adqa_score", args.n_permutations, args.seed)
    ])

    questions_df.to_csv(OUT_QUESTIONS, index=False)
    grades_df.to_csv(OUT_GRADES, index=False)
    tier_scores.to_csv(OUT_TIER_SCORES, index=False)
    aggregate.to_csv(OUT_AGG, index=False)
    nulls.to_csv(OUT_NULLS, index=False)

    report = build_report(
        provider=provider,
        model=args.model if provider == "anthropic" else "local-fallback",
        complete_clips=complete,
        questions=questions_df,
        grades=grades_df,
        tier_scores=tier_scores,
        aggregate=aggregate,
        nulls=nulls,
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print("=== Aggregate ===")
    print(aggregate.to_string(index=False))
    print("=== Null ===")
    print(nulls.to_string(index=False))
    print(f"Questions -> {OUT_QUESTIONS}")
    print(f"Grades    -> {OUT_GRADES}")
    print(f"Report    -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
