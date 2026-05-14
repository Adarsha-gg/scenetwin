#!/usr/bin/env python3
"""Unified frame-grounded ADQA for SceneTwin.

Supports any combo of Anthropic and OpenAI models for question generation
and grading. Run with different --question-model / --grader-model pairs to
produce cross-model ablations. Each run gets its own output directory; a
comparison table across all prior runs is printed at the end.

Usage examples:
  # same-model baseline (Claude→Claude)
  python3 tools/scenetwin_adqa.py

  # cross-model: Claude questions, GPT-4o grades
  python3 tools/scenetwin_adqa.py --grader-model openai:gpt-4o

  # flipped: GPT-4o questions, Claude grades
  python3 tools/scenetwin_adqa.py --question-model openai:gpt-4o

  # both OpenAI
  python3 tools/scenetwin_adqa.py --question-model openai:gpt-4o --grader-model openai:gpt-4o

Model string format: "provider:model-id"
  provider = anthropic | openai
  model-id = e.g. claude-haiku-4-5-20251001, gpt-4o, gpt-4o-mini
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
from pathlib import Path
from typing import Any

import cv2
import pandas as pd
from scipy.stats import kendalltau, spearmanr

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
BUNDLE_ZIP = ROOT / "output" / "scenetwin_description_gain_bundle.zip"
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
GROUNDING_CSV = TIMING_DIR / "clip_scores" / "need_weighted_grounding_results.csv"
SHARED_FRAMES_DIR = TIMING_DIR / "adqa_frames"  # shared across all runs

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}

N_FRAMES = 8
JPEG_QUALITY = 80
JPEG_RESIZE_MAX = 720


# ── Helpers ────────────────────────────────────────────────────────────────

def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
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


def cache_call(cache_dir: Path, key_obj: Any, prefix: str, fn, refresh: bool) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(key_obj, sort_keys=True, default=str)
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    p = cache_dir / f"{prefix}_{h}.json"
    if p.exists() and not refresh:
        return json.loads(p.read_text(encoding="utf-8"))
    result = fn()
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def short_name(model_str: str) -> str:
    provider, _, model = model_str.partition(":")
    # strip date suffix like -20251001
    model = re.sub(r"-\d{8}$", "", model)
    return model


def run_dir_name(q_model: str, g_model: str) -> str:
    return f"adqa_q-{short_name(q_model)}_g-{short_name(g_model)}"


def encode_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ── Data loading ───────────────────────────────────────────────────────────

def load_clip_metadata() -> pd.DataFrame:
    with zipfile.ZipFile(BUNDLE_ZIP) as zf:
        data = json.loads(zf.read("vatex_eval_clips.json"))
    rows = []
    for idx, meta in enumerate(data):
        row = {"clip_idx": idx, "video_id": meta.get("video_id", ""), "category": meta.get("category", "")}
        for tier in TIERS:
            row[tier] = str(meta.get(tier, "")).strip()
        rows.append(row)
    return pd.DataFrame(rows)


def complete_clip_indices() -> list[int]:
    scores = pd.read_csv(GROUNDING_CSV)
    return sorted(
        int(clip_idx)
        for clip_idx, group in scores.groupby("clip_idx")
        if set(group["tier"]) == set(TIERS)
    )


def extract_video(clip_idx: int) -> Path:
    videos_dir = SHARED_FRAMES_DIR / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE_ZIP) as zf:
        for name in zf.namelist():
            if name.startswith(f"vatex_clips/clip_{clip_idx:02d}.") and not name.endswith("/"):
                target = videos_dir / Path(name).name
                if not target.exists():
                    target.write_bytes(zf.read(name))
                return target
    raise FileNotFoundError(f"No clip_{clip_idx:02d}.* in bundle")


def sample_frames(clip_idx: int) -> list[Path]:
    out_dir = SHARED_FRAMES_DIR / f"clip_{clip_idx:02d}"
    existing = sorted(out_dir.glob("frame_*.jpg"))
    if len(existing) >= N_FRAMES:
        return existing[:N_FRAMES]

    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = extract_video(clip_idx)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps
    times = [(i + 0.5) * duration / N_FRAMES for i in range(N_FRAMES)]
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
    return paths


# ── Prompts ────────────────────────────────────────────────────────────────

def question_prompt(n_questions: int) -> str:
    return f"""You are designing ADQA-style questions for evaluating audio descriptions of short video clips.
A blind/low-vision listener should be able to answer these questions after hearing a typical audio description.

Look ONLY at the {N_FRAMES} attached video frames. Do NOT use outside knowledge or guesses.

Generate {n_questions} questions whose answers are:
1. Visible/derivable from the attached frames.
2. The kind of fact a competent AD writer working with a 30-60 word budget WOULD include.
3. Cover: main subject, main action, setting/location, key objects, visible on-screen text.

DO NOT ask about tiny details, background extras, colors of secondary objects, or things visible in only one frame.
Each question must have a short factual answer (under 15 words). Avoid yes/no questions.

Return JSON only:
{{
  "questions": [
    {{
      "q_idx": 0,
      "question": "What is the main subject doing?",
      "answer_key": "short answer derived from the frames",
      "required_visual_evidence": ["key phrase 1", "key phrase 2"],
      "importance": "critical|useful",
      "rationale": "under 12 words"
    }}
  ]
}}"""


def grade_prompt(questions: list[dict], candidates: list[dict]) -> str:
    return f"""Grade candidate audio descriptions using ADQA-style questions.

Scoring:
- 1.0 = description directly states the answer or makes it inferable.
- 0.5 = description gestures at the right answer but listener would be uncertain.
- 0.0 = description ignores, contradicts, or answers a different question.

Rules:
- Grade each candidate independently. Candidates are unlabeled.
- Do not infer candidate identity or impose a target score distribution.
- Answer keys come from sampled video frames — treat as ground truth.
- Return JSON only.

Questions:
{json.dumps(questions, indent=2)}

Candidate descriptions (unlabeled):
{json.dumps(candidates, indent=2)}

Output schema:
{{
  "grades": [
    {{
      "candidate_id": "A",
      "q_idx": 0,
      "score": 1.0,
      "label": "yes|partial|no",
      "evidence_quote": "short quote or empty",
      "rationale": "under 12 words"
    }}
  ]
}}"""


# ── API callers ────────────────────────────────────────────────────────────

def call_with_images(model_str: str, prompt: str, frame_paths: list[Path]) -> dict[str, Any]:
    provider, _, model = model_str.partition(":")
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic()
        content: list[dict] = []
        for p in frame_paths:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": encode_b64(p)}})
        content.append({"type": "text", "text": prompt})
        resp = client.messages.create(model=model, max_tokens=3000, temperature=0, messages=[{"role": "user", "content": content}])
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_b64(p)}", "detail": "low"}} for p in frame_paths]
        content.append({"type": "text", "text": prompt})
        resp = client.chat.completions.create(model=model, temperature=0, messages=[{"role": "user", "content": content}])
        text = resp.choices[0].message.content or ""
    else:
        raise ValueError(f"Unknown provider: {provider}")
    return parse_json_object(text)


def call_text(model_str: str, prompt: str) -> dict[str, Any]:
    provider, _, model = model_str.partition(":")
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic()
        resp = client.messages.create(model=model, max_tokens=5000, temperature=0, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(model=model, temperature=0, messages=[{"role": "user", "content": prompt}])
        text = resp.choices[0].message.content or ""
    else:
        raise ValueError(f"Unknown provider: {provider}")
    return parse_json_object(text)


# ── Sanitizers ─────────────────────────────────────────────────────────────

def sanitize_questions(parsed: dict, n: int) -> list[dict]:
    out = []
    for i, q in enumerate(parsed.get("questions", [])[:n]):
        ev = q.get("required_visual_evidence", [])
        out.append({
            "q_idx": int(q.get("q_idx", i)),
            "question": str(q.get("question", "")).strip(),
            "answer_key": str(q.get("answer_key", "")).strip(),
            "required_visual_evidence": "; ".join(map(str, ev)),
            "importance": str(q.get("importance", "useful")).strip(),
            "rationale": str(q.get("rationale", "")).strip()[:160],
        })
    return out


def sanitize_grades(parsed: dict, id_to_tier: dict[str, str]) -> list[dict]:
    out = []
    for g in parsed.get("grades", []):
        cid = str(g.get("candidate_id", "")).strip()
        tier = id_to_tier.get(cid)
        if tier not in TIERS:
            continue
        out.append({
            "tier": tier,
            "candidate_id": cid,
            "q_idx": int(g.get("q_idx", 0)),
            "score": min(1.0, max(0.0, float(g.get("score", 0.0) or 0.0))),
            "label": str(g.get("label", "")).strip(),
            "evidence_quote": str(g.get("evidence_quote", "")).strip()[:220],
            "rationale": str(g.get("rationale", "")).strip()[:160],
        })
    return out


# ── Metrics ────────────────────────────────────────────────────────────────

def compute_metrics(df: pd.DataFrame, score_col: str) -> dict:
    scored = df.dropna(subset=[score_col, "gt"])
    rho, rho_p = spearmanr(scored["gt"], scored[score_col])
    tau, tau_p = kendalltau(scored["gt"], scored[score_col])
    pw_wins = pw_total = fo = fo_total = 0
    for _, group in scored.groupby("clip_idx"):
        bt = {row.tier: float(getattr(row, score_col)) for row in group.itertuples()}
        if "tier3_va11y" in bt:
            for t in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
                if t in bt:
                    pw_total += 1
                    pw_wins += int(bt["tier3_va11y"] > bt[t])
        if set(TIERS).issubset(bt):
            fo_total += 1
            fo += int(bt["tier3_va11y"] > bt["tier2_vatex_long"] > bt["tier1_vatex_short"] > bt["tier0_cross"])
    nan = float("nan")
    return {
        "spearman_rho": float(rho) if not math.isnan(rho) else nan,
        "spearman_p": float(rho_p) if not math.isnan(rho_p) else nan,
        "kendall_tau": float(tau) if not math.isnan(tau) else nan,
        "kendall_p": float(tau_p) if not math.isnan(tau_p) else nan,
        "pairwise_wins": pw_wins,
        "pairwise_total": pw_total,
        "full_order_clips": fo,
        "full_order_total": fo_total,
    }


def permutation_null(df: pd.DataFrame, score_col: str, n: int, seed: int) -> dict:
    rng = random.Random(seed)
    observed = compute_metrics(df, score_col)["spearman_rho"]
    nulls = []
    for _ in range(n):
        sh = df.copy()
        for cid in sh["clip_idx"].unique():
            mask = sh["clip_idx"] == cid
            vals = list(sh.loc[mask, "gt"])
            rng.shuffle(vals)
            sh.loc[mask, "gt"] = vals
        r = compute_metrics(sh, score_col)["spearman_rho"]
        if not math.isnan(r):
            nulls.append(r)
    p_ge = sum(r >= observed for r in nulls) / len(nulls) if nulls else float("nan")
    return {"observed_rho": observed, "null_mean_rho": sum(nulls) / len(nulls) if nulls else float("nan"),
            "null_p_ge_observed": p_ge, "n_permutations": len(nulls)}


# ── Cross-run comparison ───────────────────────────────────────────────────

def print_comparison() -> None:
    runs = []
    for d in sorted(TIMING_DIR.glob("adqa_q-*_g-*")):
        agg_files = list(d.glob("*_aggregate_results.csv"))
        tier_files = list(d.glob("*_tier_scores.csv"))
        if not agg_files or not tier_files:
            continue
        agg = pd.read_csv(agg_files[0])
        tier = pd.read_csv(tier_files[0])
        if "filter" in agg.columns:
            agg = agg[agg["filter"] == "unfiltered"]
        if agg.empty:
            continue
        score_col = [c for c in tier.columns if c.startswith("adqa_") and c.endswith("_score")]
        if not score_col:
            continue
        row = agg.iloc[0]
        means = tier.groupby("tier")[score_col[0]].mean()
        runs.append({
            "run": d.name,
            "rho": float(row.get("spearman_rho", float("nan"))),
            "pw": f"{int(row.get('pairwise_wins',0))}/{int(row.get('pairwise_total',0))}",
            "fo": f"{int(row.get('full_order_clips',0))}/{int(row.get('full_order_total',0))}",
            "t3": means.get("tier3_va11y", float("nan")),
            "t2": means.get("tier2_vatex_long", float("nan")),
            "t1": means.get("tier1_vatex_short", float("nan")),
            "t0": means.get("tier0_cross", float("nan")),
        })

    if not runs:
        return

    print("\n=== All ADQA runs ===")
    header = f"{'Run':<45} {'ρ':>6} {'pw':>6} {'fo':>6} {'t3':>6} {'t2':>6} {'t1':>6} {'t0':>6}"
    print(header)
    print("-" * len(header))
    for r in runs:
        print(f"{r['run']:<45} {r['rho']:>6.3f} {r['pw']:>6} {r['fo']:>6} "
              f"{r['t3']:>6.3f} {r['t2']:>6.3f} {r['t1']:>6.3f} {r['t0']:>6.3f}")


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--question-model", default="anthropic:claude-haiku-4-5-20251001",
                        help="provider:model for question generation (needs vision)")
    parser.add_argument("--grader-model", default="anthropic:claude-haiku-4-5-20251001",
                        help="provider:model for blind grading (text only)")
    parser.add_argument("--questions-per-clip", type=int, default=5)
    parser.add_argument("--n-permutations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--clip-limit", type=int, default=0, help="0 = all clips")
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    q_model = args.question_model
    g_model = args.grader_model

    if q_model.startswith("anthropic") and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set")
    if q_model.startswith("openai") and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")
    if g_model.startswith("anthropic") and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set")
    if g_model.startswith("openai") and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")

    out_dir = TIMING_DIR / run_dir_name(q_model, g_model)
    cache_dir = out_dir / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)

    score_col = re.sub(r"[^a-zA-Z0-9_]", "_", f"adqa_{short_name(q_model)}_{short_name(g_model)}_score")

    meta_df = load_clip_metadata()
    clip_indices = complete_clip_indices()
    if args.clip_limit > 0:
        clip_indices = clip_indices[:args.clip_limit]
    meta_df = meta_df[meta_df["clip_idx"].isin(clip_indices)]

    print(f"Questioner : {q_model}")
    print(f"Grader     : {g_model}")
    print(f"Clips      : {len(clip_indices)}")
    print(f"Output     : {out_dir}\n")

    question_rows: list[dict] = []
    grade_rows: list[dict] = []

    for meta in meta_df.to_dict(orient="records"):
        clip_idx = int(meta["clip_idx"])
        print(f"=== clip_{clip_idx:02d} ===")

        try:
            frame_paths = sample_frames(clip_idx)
        except Exception as exc:
            print(f"  skipping (frames): {exc}")
            continue

        # Step 1: generate questions
        q_key = {"q_model": q_model, "clip_idx": clip_idx, "n": args.questions_per_clip,
                 "frames": [p.name for p in frame_paths]}
        try:
            parsed_q = cache_call(cache_dir, q_key, "questions",
                                  lambda fp=frame_paths: call_with_images(q_model, question_prompt(args.questions_per_clip), fp),
                                  args.refresh_cache)
        except Exception as exc:
            print(f"  question gen failed: {exc}")
            continue

        questions = sanitize_questions(parsed_q, args.questions_per_clip)
        if not questions:
            print("  no questions parsed, skipping")
            continue

        for q in questions:
            question_rows.append({"clip_idx": clip_idx, "video_id": meta["video_id"],
                                   "category": meta["category"], "question_model": q_model, **q})

        q_for_prompt = [
            {"q_idx": q["q_idx"], "question": q["question"], "answer_key": q["answer_key"],
             "required_visual_evidence": [e.strip() for e in q["required_visual_evidence"].split(";") if e.strip()],
             "importance": q["importance"]}
            for q in questions
        ]

        # Anonymize candidates — same seed logic across all runs for consistency
        rng_clip = random.Random(args.seed * 1009 + clip_idx)
        shuffled_tiers = list(TIERS)
        rng_clip.shuffle(shuffled_tiers)
        ids = ["A", "B", "C", "D"]
        id_to_tier = dict(zip(ids, shuffled_tiers))
        anon_candidates = [{"candidate_id": cid, "description": meta.get(id_to_tier[cid], "")} for cid in ids]

        # Step 2: grade
        g_key = {"g_model": g_model, "clip_idx": clip_idx, "questions": q_for_prompt, "candidates": anon_candidates}
        try:
            parsed_g = cache_call(cache_dir, g_key, "grades",
                                  lambda qp=q_for_prompt, ac=anon_candidates: call_text(g_model, grade_prompt(qp, ac)),
                                  args.refresh_cache)
        except Exception as exc:
            print(f"  grading failed: {exc}")
            continue

        grades = sanitize_grades(parsed_g, id_to_tier)
        for g in grades:
            tier = g["tier"]
            grade_rows.append({"clip_idx": clip_idx, "video_id": meta["video_id"], "category": meta["category"],
                                "tier": tier, "gt": TIER_GT[tier], "description": meta.get(tier, ""),
                                "question_model": q_model, "grader_model": g_model, **g})

        print(f"  {len(questions)} qs, {len(grades)} grades")

    if not grade_rows:
        raise RuntimeError("No grades produced.")

    questions_df = pd.DataFrame(question_rows)
    grades_df = pd.DataFrame(grade_rows)
    questions_df.to_csv(out_dir / "questions.csv", index=False)
    grades_df.to_csv(out_dir / "grades.csv", index=False)

    tier_scores = (
        grades_df.groupby(["clip_idx", "video_id", "category", "tier", "gt"], as_index=False)
        .agg(**{score_col: ("score", "mean"), "n_questions": ("q_idx", "count")})
    )
    tier_scores.to_csv(out_dir / "tier_scores.csv", index=False)

    metrics = compute_metrics(tier_scores, score_col)
    null = permutation_null(tier_scores, score_col, args.n_permutations, args.seed)
    pd.DataFrame([{**metrics, "question_model": q_model, "grader_model": g_model}]).to_csv(out_dir / "aggregate_results.csv", index=False)
    pd.DataFrame([null]).to_csv(out_dir / "nulls.csv", index=False)

    print(f"\n=== Results ===")
    print(f"  Spearman ρ     = {metrics['spearman_rho']:.4f}  (p={metrics['spearman_p']:.2e})")
    print(f"  Kendall τ      = {metrics['kendall_tau']:.4f}  (p={metrics['kendall_p']:.2e})")
    print(f"  Pairwise wins  = {metrics['pairwise_wins']}/{metrics['pairwise_total']}")
    print(f"  Fully ordered  = {metrics['full_order_clips']}/{metrics['full_order_total']}")
    print(f"  Null p         = {null['null_p_ge_observed']}")

    tier_mean = tier_scores.groupby("tier")[score_col].mean()
    print("\n=== Tier means ===")
    for tier in sorted(TIERS, key=lambda t: TIER_GT[t], reverse=True):
        print(f"  {tier}: {tier_mean.get(tier, float('nan')):.3f}")

    print_comparison()


if __name__ == "__main__":
    main()
