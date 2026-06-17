#!/usr/bin/env python3
"""Finer-grained 4-tier completeness ladder (10 graded questions/clip).

Fixes the top-rung saturation: with only 5 basic questions, half-AD and full-AD
both answer everything. Here we generate 10 questions per clip spanning a
granularity gradient — ~4 core facts (subject/action/setting) plus ~6 secondary
visible details (specific objects, clothing, counts, action sequence) that a
THOROUGH description includes but a brief one omits. This gives the audit enough
resolution to separate:

    tier0 cross  <  tierA expert AD (1 sentence)  <  tierB expert AD (half)  <  tier3 expert AD (full)

Questions generated + all 4 candidates graded blind by the SAME model (Gemini);
CLIP is local. Self-contained, no dependence on the cached 5-question set.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import machine_ad_tier as M  # noqa: E402
from completeness_ladder import truncations  # noqa: E402

ROOT = M.ROOT
CURSOR = M.CURSOR
REGISTRY = M.REGISTRY
OUT_CSV = CURSOR / "output" / "completeness" / "finer_completeness_ladder.csv"
OUT_JSON = CURSOR / "output" / "finer_completeness_ladder.json"
FINDINGS = CURSOR / "findings" / "completeness-ladder.md"
CHART = ROOT / "output" / "charts" / "scenetwin_completeness_ladder.png"

LADDER = ["tier0_cross", "tierA_ad_1sent", "tierB_ad_half", "tier3_va11y"]
LADDER_GT = {t: i for i, t in enumerate(LADDER)}
N_FRAMES = M.N_FRAMES
N_Q = 10

Q_PROMPT = """You are designing ADQA-style questions to evaluate audio descriptions of a ~10s video clip.
Look ONLY at the attached frames. Generate exactly 10 questions with a GRANULARITY GRADIENT:
- 4 CORE questions: the main subject, the main action, the setting/location, the primary object.
- 6 SECONDARY questions: specific but clearly visible details a THOROUGH description would include
  but a brief one would omit — e.g. clothing/colors of the main subject, secondary objects, counts,
  the sequence or change of actions, notable background elements, on-screen text.
Each question needs a short factual answer (<15 words) derivable from the frames. Avoid yes/no.
Return JSON only:
{"questions":[{"q_idx":0,"question":"...","answer_key":"...","tier":"core|secondary"}]}"""


def gen_questions(cl, vid, imgs, refresh):
    payload = {"kind": "finer_questions_v1", "model": M.MODEL, "video_id": vid, "n": N_Q}

    def call():
        return M.parse_json(M.gen_content(cl, [Q_PROMPT, *imgs]))

    parsed = M.cache_json("questions10", payload, call, refresh)
    qs = parsed.get("questions", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
    out = []
    for j, q in enumerate(qs[:N_Q]):
        if isinstance(q, dict) and q.get("question"):
            out.append({"q_idx": int(q.get("q_idx", j)), "question": str(q["question"]).strip(),
                        "answer_key": str(q.get("answer_key", "")).strip(),
                        "qtier": str(q.get("tier", "secondary")).strip()})
    return out


def main():
    M.load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--provider", choices=["gemini", "anthropic", "openai"], default="gemini")
    ap.add_argument("--model", default=None, help="override model id (e.g. claude-opus-4-20250514, gpt-4o)")
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()
    M.configure(args.provider, args.model)
    print(f"Grader: {M.PROVIDER} / {M.MODEL}")

    reg = {json.loads(l)["video_id"]: json.loads(l)
           for l in REGISTRY.read_text().splitlines() if l.strip()}
    vids = [v for v in reg if (M.FRAMES_ROOT / v).exists()]
    if args.limit:
        vids = vids[: args.limit]

    cl = M.client()
    import open_clip
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading CLIP on {device} ...")
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    rows = []
    for i, vid in enumerate(vids):
        paths = M.frame_paths(vid)
        if len(paths) < N_FRAMES:
            print(f"[{i+1}/{len(vids)}] {vid}: skip frames"); continue
        meta = reg[vid]
        imgs = [Image.open(p).convert("RGB") for p in paths]
        questions = gen_questions(cl, vid, imgs, args.refresh_cache)
        if len(questions) < 6:
            print(f"[{i+1}/{len(vids)}] {vid}: skip (only {len(questions)} qs)"); continue
        one, half = truncations(str(meta["tier3_va11y"]).strip())
        cand_text = {
            "tier0_cross": meta["tier0_cross"],
            "tierA_ad_1sent": one,
            "tierB_ad_half": half,
            "tier3_va11y": str(meta["tier3_va11y"]).strip(),
        }
        adqa = M.grade_all_tiers(cl, vid, questions, cand_text, args.seed, args.refresh_cache)
        for tier in LADDER:
            ct = M.clip_top3(model, preprocess, tokenizer, device, paths, cand_text[tier])
            rows.append({"video_id": vid, "tier": tier, "gt": LADDER_GT[tier],
                         "adqa_score": adqa.get(tier, 0.0), "clip_top3": ct, "n_q": len(questions)})
        print(f"[{i+1}/{len(vids)}] {vid} ({len(questions)}q): 1sent={adqa.get('tierA_ad_1sent',0):.2f} "
              f"half={adqa.get('tierB_ad_half',0):.2f} full={adqa.get('tier3_va11y',0):.2f}")

    full = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(OUT_CSV, index=False)
    full["adqa_norm"] = full.groupby("video_id", group_keys=False)["adqa_score"].apply(M.minmax)
    full["clip_norm"] = full.groupby("video_id", group_keys=False)["clip_top3"].apply(M.minmax)
    full["ensemble"] = 0.5 * full["adqa_norm"] + 0.5 * full["clip_norm"]

    def metrics(col):
        rho = float(spearmanr(full["gt"], full[col])[0])
        fo = tot = 0
        for _, g in full.groupby("video_id"):
            by = dict(zip(g["tier"], g[col]))
            if all(t in by for t in LADDER):
                tot += 1
                fo += int(by["tier0_cross"] < by["tierA_ad_1sent"] < by["tierB_ad_half"] < by["tier3_va11y"])
        return {"rho": rho, "full_order": fo, "n": tot, "rate": fo / tot if tot else float("nan")}

    piv = full.pivot_table(index="video_id", columns="tier", values="ensemble")
    sanity = {
        "full>half": float((piv["tier3_va11y"] > piv["tierB_ad_half"]).mean()),
        "half>1sent": float((piv["tierB_ad_half"] > piv["tierA_ad_1sent"]).mean()),
        "1sent>cross": float((piv["tierA_ad_1sent"] > piv["tier0_cross"]).mean()),
    }
    adqa_piv = full.pivot_table(index="video_id", columns="tier", values="adqa_score")
    adqa_sanity = {
        "full>half_adqa": float((adqa_piv["tier3_va11y"] > adqa_piv["tierB_ad_half"]).mean()),
        "full>=half_adqa": float((adqa_piv["tier3_va11y"] >= adqa_piv["tierB_ad_half"]).mean()),
    }
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(), "grader": M.MODEL,
        "n_questions": N_Q, "n_clips": int(full.video_id.nunique()),
        "ladder": "cross < expertAD_1sent < expertAD_half < expertAD_full",
        "ensemble": metrics("ensemble"), "adqa_only": metrics("adqa_score"),
        "clip_only": metrics("clip_top3"), "rung_sanity": sanity, "adqa_rung": adqa_sanity,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n=== FINER 4-TIER COMPLETENESS LADDER (10q, Gemini) ===")
    print("ensemble:", json.dumps(report["ensemble"]))
    print("rung sanity:", json.dumps(sanity))
    print("adqa full>half:", json.dumps(adqa_sanity))
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
