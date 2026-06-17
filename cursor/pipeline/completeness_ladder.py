#!/usr/bin/env python3
"""Valid 4-tier ladder = AD content completeness (Gemini grader, self-contained).

Replaces the fake "long VATEX" rung with a principled completeness ladder built
by truncating the expert AD. This directly tests SceneTwin's core claim: does it
detect how much visual content an audio description preserves?

    tier0 cross control  <  tierA expert AD (1 sentence)
                          <  tierB expert AD (half)
                          <  tier3 expert AD (full)

Monotonic by construction (each rung is a strict superset of visual content).
All four candidates are graded blind by the SAME model (Gemini) against the
cached frame-grounded questions; CLIP is local. This is a controlled sensitivity
benchmark, distinct from the cross/crowd discrimination task.
"""
from __future__ import annotations

import argparse
import json
import math
import re
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
import machine_ad_tier as M  # reuse robust Gemini helpers  # noqa: E402

ROOT = M.ROOT
CURSOR = M.CURSOR
REGISTRY = M.REGISTRY
FRAMES_ROOT = M.FRAMES_ROOT
QUESTIONS_CSV = M.QUESTIONS_CSV
OUT_CSV = CURSOR / "output" / "completeness" / "completeness_ladder.csv"
OUT_JSON = CURSOR / "output" / "completeness_ladder.json"
FINDINGS = CURSOR / "findings" / "completeness-ladder.md"
CHART = ROOT / "output" / "charts" / "scenetwin_completeness_ladder.png"

LADDER = ["tier0_cross", "tierA_ad_1sent", "tierB_ad_half", "tier3_va11y"]
LADDER_GT = {t: i for i, t in enumerate(LADDER)}
N_FRAMES = M.N_FRAMES


def split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return parts


def truncations(expert: str) -> tuple[str, str]:
    """Return (one_sentence, half) truncations of the expert AD.

    Falls back to word fractions when the AD has too few sentences so the rungs
    never collapse onto each other.
    """
    sents = split_sentences(expert)
    if len(sents) >= 3:
        one = sents[0]
        half = " ".join(sents[: math.ceil(len(sents) / 2)])
    else:
        words = expert.split()
        one = " ".join(words[: max(4, len(words) // 4)])
        half = " ".join(words[: max(8, (len(words) * 6) // 10)])
    return one, half


def main():
    M.load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()

    reg = {json.loads(l)["video_id"]: json.loads(l)
           for l in REGISTRY.read_text().splitlines() if l.strip()}
    qdf = pd.read_csv(QUESTIONS_CSV)
    vids = [v for v in qdf["video_id"].unique() if v in reg]
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
        expert = str(meta["tier3_va11y"]).strip()
        one, half = truncations(expert)
        cand_text = {
            "tier0_cross": meta["tier0_cross"],
            "tierA_ad_1sent": one,
            "tierB_ad_half": half,
            "tier3_va11y": expert,
        }
        questions = qdf[qdf.video_id == vid].to_dict("records")
        adqa = M.grade_all_tiers(cl, vid, questions, cand_text, args.seed, args.refresh_cache)
        for tier in LADDER:
            ct = M.clip_top3(model, preprocess, tokenizer, device, paths, cand_text[tier])
            rows.append({"video_id": vid, "tier": tier, "gt": LADDER_GT[tier],
                         "adqa_score": adqa.get(tier, 0.0), "clip_top3": ct,
                         "words": len(cand_text[tier].split())})
        print(f"[{i+1}/{len(vids)}] {vid}: 1sent={adqa.get('tierA_ad_1sent',0):.2f} "
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
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "grader": M.MODEL, "n_clips": int(full.video_id.nunique()),
        "ladder": "cross < expertAD_1sentence < expertAD_half < expertAD_full",
        "ensemble": metrics("ensemble"), "adqa_only": metrics("adqa_score"),
        "clip_only": metrics("clip_top3"), "rung_sanity": sanity,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n=== 4-TIER COMPLETENESS LADDER (Gemini grader) ===")
    print("ensemble:", json.dumps(report["ensemble"]))
    print("rung sanity:", json.dumps(sanity))
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
