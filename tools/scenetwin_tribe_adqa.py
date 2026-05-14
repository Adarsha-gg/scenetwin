#!/usr/bin/env python3
"""TRIBE-weighted frame-grounded ADQA.

Ablation against scenetwin_adqa.py (uniform frame sampling).

Key difference: frames are sampled proportional to TRIBE accessibility-gap
need scores. High-need windows (where the brain misses the most visual
information) get more frames fed to the question generator. The LLM therefore
sees — and asks about — the moments TRIBE says a blind person misses most.

The question prompt also receives a TRIBE context block telling it which
windows are high-need and what TRIBE's overall pressure is.

Everything else (blind grading, anonymization, metrics) is identical to the
baseline scenetwin_adqa.py so results are directly comparable.

Usage:
  python3 tools/scenetwin_tribe_adqa.py
  python3 tools/scenetwin_tribe_adqa.py --question-model openai:gpt-4o
  python3 tools/scenetwin_tribe_adqa.py --refresh-cache
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

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
BUNDLE_ZIP = ROOT / "output" / "scenetwin_description_gain_bundle.zip"
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
GROUNDING_CSV = TIMING_DIR / "clip_scores" / "need_weighted_grounding_results.csv"
NEED_CSV = TIMING_DIR / "need" / "coarse_need_windows.csv"
CLIP_FEATURES_CSV = TIMING_DIR / "tribe_native" / "tribe_clip_features.csv"
SHARED_FRAMES_DIR = TIMING_DIR / "adqa_frames"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}

N_FRAMES = 8
JPEG_QUALITY = 80
JPEG_RESIZE_MAX = 720
SEED = 17
N_PERMUTATIONS = 2000


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
    _, _, model = model_str.partition(":")
    return re.sub(r"-\d{8}$", "", model)


def encode_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ── Data ───────────────────────────────────────────────────────────────────

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
        int(cid) for cid, g in scores.groupby("clip_idx")
        if set(g["tier"]) == set(TIERS)
    )


def load_tribe_profile(clip_idx: int) -> dict:
    """Return per-clip TRIBE context: need windows + aggregate features."""
    need_df = pd.read_csv(NEED_CSV)
    clip_windows = need_df[need_df["clip_idx"] == clip_idx].sort_values("window_idx")

    feat_df = pd.read_csv(CLIP_FEATURES_CSV)
    feat_row = feat_df[feat_df["clip_idx"] == clip_idx]

    mean_need = float(feat_row["mean_need"].iloc[0]) if not feat_row.empty else 0.5
    tribe_pressure = float(feat_row["tribe_pressure"].iloc[0]) if not feat_row.empty else 0.5
    tribe_route = "extended/integrated AD likely needed" if tribe_pressure > 0.6 else "standard AD priority"
    mean_speech = float(feat_row["mean_speech_density"].iloc[0]) if not feat_row.empty else 0.5

    high_need_windows = clip_windows[clip_windows["need_score"] >= 0.4].to_dict(orient="records")
    all_windows = clip_windows.to_dict(orient="records")

    return {
        "mean_need": mean_need,
        "tribe_route": tribe_route,
        "mean_speech_density": mean_speech,
        "high_need_windows": high_need_windows,
        "all_windows": all_windows,
    }


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


def sample_frames_tribe_weighted(clip_idx: int, tribe_profile: dict) -> list[Path]:
    """Sample N_FRAMES frames weighted by TRIBE need scores.

    Windows with higher need scores get proportionally more frames. This
    biases the LLM toward seeing — and asking about — what TRIBE says the
    brain misses most visually.
    """
    out_dir = SHARED_FRAMES_DIR / f"clip_{clip_idx:02d}_tribe"
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

    # Build sampling timestamps weighted by TRIBE need
    windows = tribe_profile["all_windows"]
    if not windows:
        # Fallback: uniform
        times = [(i + 0.5) * duration / N_FRAMES for i in range(N_FRAMES)]
    else:
        # Allocate frames proportional to need score (min 1 frame per window if budget allows)
        needs = [max(w["need_score"], 0.05) for w in windows]
        total_need = sum(needs)
        raw_allocs = [n / total_need * N_FRAMES for n in needs]

        # Round to integers, ensure total = N_FRAMES
        allocs = [max(1, round(a)) for a in raw_allocs]
        diff = N_FRAMES - sum(allocs)
        # Distribute remainder to highest-need windows
        sorted_idx = sorted(range(len(windows)), key=lambda i: needs[i], reverse=True)
        for i in range(abs(diff)):
            allocs[sorted_idx[i % len(sorted_idx)]] += 1 if diff > 0 else -1
            allocs[sorted_idx[i % len(sorted_idx)]] = max(0, allocs[sorted_idx[i % len(sorted_idx)]])

        times = []
        for w, n_frames in zip(windows, allocs):
            start, end = w["start_s"], w["end_s"]
            for k in range(n_frames):
                t = start + (k + 0.5) * (end - start) / max(n_frames, 1)
                t = min(max(t, 0.0), duration - 0.05)
                times.append(t)
        times = sorted(times)[:N_FRAMES]

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

def tribe_context_block(tribe_profile: dict) -> str:
    mean_need = tribe_profile["mean_need"]
    route = tribe_profile["tribe_route"]
    speech = tribe_profile["mean_speech_density"]
    high_windows = tribe_profile["high_need_windows"]

    pressure = "HIGH" if mean_need > 0.45 else ("MODERATE" if mean_need > 0.25 else "LOW")
    speech_label = "dense speech (less room for AD)" if speech > 0.6 else "sparse speech (room for AD)"

    window_str = ""
    if high_windows:
        parts = [f"t={w['start_s']:.1f}–{w['end_s']:.1f}s (need={w['need_score']:.2f}, {w['recommendation']})"
                 for w in high_windows]
        window_str = "\nHigh-need windows where visual information is most missing:\n  " + "\n  ".join(parts)

    return f"""TRIBE brain-encoding context for this clip:
- Overall accessibility pressure: {pressure} (mean_need={mean_need:.3f})
- AD routing: {route}
- Speech density: {speech_label} (density={speech:.2f}){window_str}

This means: a blind/low-vision listener misses {'a large amount' if pressure == 'HIGH' else ('a moderate amount' if pressure == 'MODERATE' else 'a small amount')} of visual information in this clip.
Focus your comprehension questions on what is happening in the HIGH-NEED time windows above — those are the moments the brain most needs visual description."""


def question_prompt(n_questions: int, tribe_profile: dict) -> str:
    ctx = tribe_context_block(tribe_profile)
    return f"""You are designing ADQA-style comprehension questions for evaluating audio descriptions of short video clips.

{ctx}

Look at the attached video frames. These frames were sampled with emphasis on HIGH-NEED windows identified by TRIBE.

Generate {n_questions} questions whose answers are:
1. Visible/derivable from the frames, especially in the high-need time windows noted above.
2. The kind of fact a competent AD writer working with a 30-60 word budget WOULD include for a blind listener.
3. Cover: main subject, main action, setting/location, key objects, visible on-screen text.

DO NOT ask about tiny details, background extras, or things visible in only one frame.
Each question must have a short factual answer (under 15 words). Avoid yes/no questions.
Prioritize questions about what happens in the HIGH-NEED windows — that is where the brain most misses visual information.

Return JSON only:
{{
  "questions": [
    {{
      "q_idx": 0,
      "question": "What is the main subject doing?",
      "answer_key": "short answer derived from the frames",
      "required_visual_evidence": ["key phrase 1"],
      "importance": "critical|useful",
      "rationale": "under 12 words, why this matters for a blind listener"
    }}
  ]
}}"""


def grade_prompt(questions: list[dict], candidates: list[dict]) -> str:
    return f"""Grade candidate audio descriptions using ADQA-style questions.

Scoring:
- 1.0 = description directly states the answer or makes it clearly inferable.
- 0.5 = description gestures at the right answer but a listener would still be uncertain.
- 0.0 = description ignores, contradicts, or answers a different question.

Rules:
- Grade each candidate independently. Candidates are unlabeled.
- Do not infer identity or impose a target score distribution.
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


# ── API ────────────────────────────────────────────────────────────────────

def call_with_images(model_str: str, prompt: str, frame_paths: list[Path]) -> dict[str, Any]:
    provider, _, model = model_str.partition(":")
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic()
        content: list[dict] = []
        for p in frame_paths:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": encode_b64(p)}})
        content.append({"type": "text", "text": prompt})
        resp = client.messages.create(model=model, max_tokens=3000, temperature=0,
                                      messages=[{"role": "user", "content": content}])
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_b64(p)}", "detail": "low"}}
                   for p in frame_paths]
        content.append({"type": "text", "text": prompt})
        resp = client.chat.completions.create(model=model, temperature=0,
                                              messages=[{"role": "user", "content": content}])
        text = resp.choices[0].message.content or ""
    else:
        raise ValueError(f"Unknown provider: {provider}")
    return parse_json_object(text)


def call_text(model_str: str, prompt: str) -> dict[str, Any]:
    provider, _, model = model_str.partition(":")
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic()
        resp = client.messages.create(model=model, max_tokens=5000, temperature=0,
                                      messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(model=model, temperature=0,
                                              messages=[{"role": "user", "content": prompt}])
        text = resp.choices[0].message.content or ""
    else:
        raise ValueError(f"Unknown provider: {provider}")
    return parse_json_object(text)


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
        "pairwise_wins": pw_wins, "pairwise_total": pw_total,
        "full_order_clips": fo, "full_order_total": fo_total,
    }


def permutation_null(df: pd.DataFrame, score_col: str) -> dict:
    rng = random.Random(SEED)
    observed = compute_metrics(df, score_col)["spearman_rho"]
    nulls = []
    for _ in range(N_PERMUTATIONS):
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
    return {"observed_rho": observed, "null_mean_rho": sum(nulls)/len(nulls) if nulls else float("nan"),
            "null_p_ge_observed": p_ge, "n_permutations": len(nulls)}


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


def sanitize_grades(parsed: dict, id_to_tier: dict) -> list[dict]:
    out = []
    for g in parsed.get("grades", []):
        cid = str(g.get("candidate_id", "")).strip()
        tier = id_to_tier.get(cid)
        if tier not in TIERS:
            continue
        out.append({
            "tier": tier, "candidate_id": cid, "q_idx": int(g.get("q_idx", 0)),
            "score": min(1.0, max(0.0, float(g.get("score", 0.0) or 0.0))),
            "label": str(g.get("label", "")).strip(),
            "evidence_quote": str(g.get("evidence_quote", "")).strip()[:220],
            "rationale": str(g.get("rationale", "")).strip()[:160],
        })
    return out


def print_comparison(out_dir: Path, score_col: str, tribe_metrics: dict, tribe_null: dict) -> None:
    """Print tribe-weighted vs baseline ADQA side by side."""
    baseline_dir = TIMING_DIR / "adqa_q-claude-haiku-4-5_g-claude-haiku-4-5"
    baseline_agg = baseline_dir / "aggregate_results.csv"
    baseline_tier = baseline_dir / "tier_scores.csv"

    print("\n=== TRIBE-weighted vs baseline ADQA ===")
    print(f"{'Metric':<25} {'Baseline (uniform)':<22} {'TRIBE-weighted':<22} {'Delta'}")
    print("-" * 80)

    if baseline_agg.exists() and baseline_tier.exists():
        bagg = pd.read_csv(baseline_agg).iloc[0]
        btier = pd.read_csv(baseline_tier)
        b_score_col = [c for c in btier.columns if c.startswith("adqa_") and c.endswith("_score")]
        b_rho = float(bagg.get("spearman_rho", float("nan")))
        b_pw = f"{int(bagg.get('pairwise_wins',0))}/{int(bagg.get('pairwise_total',0))}"
        b_fo = f"{int(bagg.get('full_order_clips',0))}/{int(bagg.get('full_order_total',0))}"

        t_rho = tribe_metrics["spearman_rho"]
        t_pw = f"{tribe_metrics['pairwise_wins']}/{tribe_metrics['pairwise_total']}"
        t_fo = f"{tribe_metrics['full_order_clips']}/{tribe_metrics['full_order_total']}"

        print(f"{'Spearman ρ':<25} {b_rho:<22.4f} {t_rho:<22.4f} {t_rho-b_rho:+.4f}")
        print(f"{'Pairwise wins':<25} {b_pw:<22} {t_pw:<22}")
        print(f"{'Fully ordered':<25} {b_fo:<22} {t_fo:<22}")

        if b_score_col:
            tier_tribe = pd.read_csv(out_dir / "tier_scores.csv")
            b_means = btier.groupby("tier")[b_score_col[0]].mean()
            t_means = tier_tribe.groupby("tier")[score_col].mean()
            print(f"\n{'Tier':<25} {'Baseline':>12} {'TRIBE-weighted':>16} {'Delta':>8}")
            for tier in sorted(TIERS, key=lambda t: TIER_GT[t], reverse=True):
                bm = b_means.get(tier, float("nan"))
                tm = t_means.get(tier, float("nan"))
                print(f"  {tier:<23} {bm:>12.3f} {tm:>16.3f} {tm-bm:>+8.3f}")
    else:
        print("  (baseline not found — run scenetwin_adqa.py first for comparison)")
        print(f"  TRIBE-weighted ρ = {tribe_metrics['spearman_rho']:.4f}")


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--question-model", default="anthropic:claude-haiku-4-5-20251001")
    parser.add_argument("--grader-model", default="anthropic:claude-haiku-4-5-20251001")
    parser.add_argument("--questions-per-clip", type=int, default=5)
    parser.add_argument("--clip-limit", type=int, default=0)
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

    run_name = f"adqa_tribe_q-{short_name(q_model)}_g-{short_name(g_model)}"
    out_dir = TIMING_DIR / run_name
    cache_dir = out_dir / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)

    score_col = re.sub(r"[^a-zA-Z0-9_]", "_", f"adqa_tribe_{short_name(q_model)}_{short_name(g_model)}_score")

    meta_df = load_clip_metadata()
    clip_indices = complete_clip_indices()
    if args.clip_limit > 0:
        clip_indices = clip_indices[:args.clip_limit]
    meta_df = meta_df[meta_df["clip_idx"].isin(clip_indices)]

    print(f"Questioner   : {q_model}")
    print(f"Grader       : {g_model}")
    print(f"Frame sample : TRIBE need-weighted (high-need windows get more frames)")
    print(f"Clips        : {len(clip_indices)}")
    print(f"Output       : {out_dir}\n")

    question_rows: list[dict] = []
    grade_rows: list[dict] = []

    for meta in meta_df.to_dict(orient="records"):
        clip_idx = int(meta["clip_idx"])
        print(f"=== clip_{clip_idx:02d} ({meta['category']}) ===")

        tribe_profile = load_tribe_profile(clip_idx)
        pressure = "HIGH" if tribe_profile["mean_need"] > 0.45 else ("MOD" if tribe_profile["mean_need"] > 0.25 else "LOW")
        n_high = len(tribe_profile["high_need_windows"])
        print(f"  TRIBE: mean_need={tribe_profile['mean_need']:.3f} [{pressure}], {n_high} high-need windows")

        try:
            frame_paths = sample_frames_tribe_weighted(clip_idx, tribe_profile)
        except Exception as exc:
            print(f"  skipping (frames): {exc}")
            continue

        q_key = {"q_model": q_model, "clip_idx": clip_idx, "n": args.questions_per_clip,
                 "frames": [p.name for p in frame_paths], "tribe_mean_need": round(tribe_profile["mean_need"], 3)}
        try:
            parsed_q = cache_call(cache_dir, q_key, "questions",
                                  lambda fp=frame_paths, tp=tribe_profile:
                                  call_with_images(q_model, question_prompt(args.questions_per_clip, tp), fp),
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
                                   "category": meta["category"], "question_model": q_model,
                                   "tribe_mean_need": tribe_profile["mean_need"],
                                   "tribe_route": tribe_profile["tribe_route"], **q})

        q_for_prompt = [
            {"q_idx": q["q_idx"], "question": q["question"], "answer_key": q["answer_key"],
             "required_visual_evidence": [e.strip() for e in q["required_visual_evidence"].split(";") if e.strip()],
             "importance": q["importance"]}
            for q in questions
        ]

        rng_clip = random.Random(SEED * 1009 + clip_idx)
        shuffled_tiers = list(TIERS)
        rng_clip.shuffle(shuffled_tiers)
        ids = ["A", "B", "C", "D"]
        id_to_tier = dict(zip(ids, shuffled_tiers))
        anon_candidates = [{"candidate_id": cid, "description": meta.get(id_to_tier[cid], "")} for cid in ids]

        g_key = {"g_model": g_model, "clip_idx": clip_idx, "questions": q_for_prompt, "candidates": anon_candidates}
        try:
            parsed_g = cache_call(cache_dir, g_key, "grades",
                                  lambda qp=q_for_prompt, ac=anon_candidates:
                                  call_text(g_model, grade_prompt(qp, ac)),
                                  args.refresh_cache)
        except Exception as exc:
            print(f"  grading failed: {exc}")
            continue

        grades = sanitize_grades(parsed_g, id_to_tier)
        for g in grades:
            tier = g["tier"]
            grade_rows.append({"clip_idx": clip_idx, "video_id": meta["video_id"],
                                "category": meta["category"], "tier": tier, "gt": TIER_GT[tier],
                                "description": meta.get(tier, ""), "question_model": q_model,
                                "grader_model": g_model,
                                "tribe_mean_need": tribe_profile["mean_need"], **g})

        print(f"  {len(questions)} qs, {len(grades)} grades")

    if not grade_rows:
        raise RuntimeError("No grades produced.")

    questions_df = pd.DataFrame(question_rows)
    grades_df = pd.DataFrame(grade_rows)
    questions_df.to_csv(out_dir / "questions.csv", index=False)
    grades_df.to_csv(out_dir / "grades.csv", index=False)

    tier_scores = (
        grades_df.groupby(["clip_idx", "video_id", "category", "tier", "gt"], as_index=False)
        .agg(**{score_col: ("score", "mean"), "n_questions": ("q_idx", "count"),
                "tribe_mean_need": ("tribe_mean_need", "first")})
    )
    tier_scores.to_csv(out_dir / "tier_scores.csv", index=False)

    metrics = compute_metrics(tier_scores, score_col)
    null = permutation_null(tier_scores, score_col)
    pd.DataFrame([{**metrics, "question_model": q_model, "grader_model": g_model}]).to_csv(
        out_dir / "aggregate_results.csv", index=False)
    pd.DataFrame([null]).to_csv(out_dir / "nulls.csv", index=False)

    print(f"\n=== TRIBE-weighted ADQA Results ===")
    print(f"  Spearman ρ    = {metrics['spearman_rho']:.4f}  (p={metrics['spearman_p']:.2e})")
    print(f"  Kendall τ     = {metrics['kendall_tau']:.4f}  (p={metrics['kendall_p']:.2e})")
    print(f"  Pairwise wins = {metrics['pairwise_wins']}/{metrics['pairwise_total']}")
    print(f"  Fully ordered = {metrics['full_order_clips']}/{metrics['full_order_total']}")
    print(f"  Null p        = {null['null_p_ge_observed']}")

    tier_mean = tier_scores.groupby("tier")[score_col].mean()
    print("\n=== Tier means ===")
    for tier in sorted(TIERS, key=lambda t: TIER_GT[t], reverse=True):
        print(f"  {tier}: {tier_mean.get(tier, float('nan')):.3f}")

    print_comparison(out_dir, score_col, metrics, null)


if __name__ == "__main__":
    main()
