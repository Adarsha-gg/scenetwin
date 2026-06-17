#!/usr/bin/env python3
"""Full external-clip eval pipeline — frames → CLIP → metrics → report.

End-to-end test, not markdown-only:
  1. Extract frames from each external clip.mp4
  2. CLIP ViT-L-14 top3 grounding per tier
  3. StoryRecall + VT consistency + subjectivity
  4. Compare tier ordering vs benchmark CLIP stats
  5. Write JSON + CSV under cursor/output/
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
EXT_DIR = CURSOR / "data" / "external_clips"
REGISTRY = EXT_DIR / "registry.jsonl"
FRAMES_ROOT = EXT_DIR / "frames"
OUT_DIR = CURSOR / "output"
OUT_CSV = OUT_DIR / "external_clip_full_eval.csv"
OUT_JSON = OUT_DIR / "external_clip_full_eval.json"
BENCH_CLIP = ROOT / "output" / "scenetwin_timing_20clip" / "clip_scores" / "need_weighted_grounding_results.csv"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}
N_FRAMES = 8
JPEG_MAX = 512


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_registry() -> list[dict]:
    rows = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return [r for r in rows if r.get("download_ok", True)]


def extract_frames(video_id: str, mp4: Path) -> list[Path]:
    out = FRAMES_ROOT / video_id
    existing = sorted(out.glob("frame_*.jpg"))
    if len(existing) >= N_FRAMES:
        return existing[:N_FRAMES]
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(mp4))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {mp4}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps if total else 10.0
    paths = []
    for k in range(N_FRAMES):
        t = (k + 0.5) * duration / N_FRAMES
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        h, w = frame.shape[:2]
        if max(h, w) > JPEG_MAX:
            s = JPEG_MAX / max(h, w)
            frame = cv2.resize(frame, (int(w * s), int(h * s)))
        p = out / f"frame_{k:02d}_t{t:.2f}.jpg"
        cv2.imwrite(str(p), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        paths.append(p)
    cap.release()
    return paths


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def vt_score(ad: str, evidence: set[str]) -> float:
    if not evidence:
        return 0.5
    ad_t = tokenize(ad)
    hit = len(evidence & ad_t)
    return min(1.0, hit / max(3, len(evidence) * 0.4))


def evidence_from_pro(pro_text: str) -> set[str]:
    terms = set()
    for sent in re.split(r"[.!?]+", pro_text):
        for w in re.findall(r"[a-z]{4,}", sent.lower()):
            terms.add(w)
    return terms


def story_recall(beats: list[str], hyp: str) -> float:
    if not beats:
        return float("nan")
    hyp_l = hyp.lower()
    hit = sum(
        1 for b in beats
        if sum(1 for w in re.findall(r"[a-z]{4,}", b) if w in hyp_l) / max(1, len(re.findall(r"[a-z]{4,}", b))) >= 0.35
    )
    return hit / len(beats)


def clip_score(model, preprocess, tokenizer, device, frame_paths: list[Path], text: str) -> float:
    imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in frame_paths]).to(device)
    tokens = tokenizer([text]).to(device)
    with torch.no_grad():
        img_f = model.encode_image(imgs)
        img_f = img_f / img_f.norm(dim=-1, keepdim=True)
        txt_f = model.encode_text(tokens)
        txt_f = txt_f / txt_f.norm(dim=-1, keepdim=True)
        sims = (img_f @ txt_f.T).squeeze().cpu().numpy()
    k = min(3, len(sims))
    return float(np.sort(sims)[-k:].mean())


def evaluate_clip(meta: dict, model, preprocess, tokenizer, device) -> list[dict]:
    vid = meta["video_id"]
    mp4 = EXT_DIR / vid / "clip.mp4"
    if not mp4.exists():
        return []
    frames = extract_frames(vid, mp4)
    if not frames:
        return []
    evidence = evidence_from_pro(meta["tier3_va11y"])
    beats = [s.strip().lower() for s in re.split(r"[.!?]+", meta["tier3_va11y"]) if len(s.strip()) > 12]
    rows = []
    for tier in TIERS:
        text = meta[tier]
        clip_t3 = clip_score(model, preprocess, tokenizer, device, frames, text)
        rows.append({
            "video_id": vid,
            "category": meta["category"],
            "tier": tier,
            "gt": TIER_GT[tier],
            "clip_top3": clip_t3,
            "vt_consistency": vt_score(text, evidence),
            "story_recall": story_recall(beats, text),
            "subjectivity_vs_short": 1.0 - len(tokenize(text) & tokenize(meta["tier1_vatex_short"])) / max(1, len(tokenize(text) | tokenize(meta["tier1_vatex_short"]))),
            "n_frames": len(frames),
        })
    return rows


def clip_summary(g: pd.DataFrame) -> dict:
    v = dict(zip(g["tier"], g["clip_top3"]))
    return {
        "full_order_clip": int(
            v.get("tier3_va11y", 0) > v.get("tier2_vatex_long", 0) > v.get("tier1_vatex_short", 0) > v.get("tier0_cross", 0)
        ),
        "pro_beats_short": int(v.get("tier3_va11y", 0) > v.get("tier1_vatex_short", 0)),
        "tier3_clip": v.get("tier3_va11y"),
        "tier1_clip": v.get("tier1_vatex_short"),
    }


def benchmark_same_method(model, preprocess, tokenizer, device) -> dict:
    """Same plain CLIP top3 on benchmark frames — apples-to-apples vs external."""
    if not BENCH_CLIP.exists() or not (ROOT / "output" / "scenetwin_timing_20clip" / "adqa_frames").exists():
        return {}
    forecast = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv")
    frames_root = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_frames"
    rows = []
    for cidx in sorted(forecast["clip_idx"].unique()):
        paths = sorted((frames_root / f"clip_{int(cidx):02d}").glob("frame_*.jpg"))
        if not paths:
            continue
        fc = forecast[forecast["clip_idx"] == cidx].iloc[0]
        for tier, gt in TIER_GT.items():
            col = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
                   "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}[tier]
            score = clip_score(model, preprocess, tokenizer, device, paths, str(fc[col]))
            rows.append({"clip_idx": cidx, "tier": tier, "gt": gt, "clip_top3": score})
    if not rows:
        return {}
    bdf = pd.DataFrame(rows)
    rho, p = spearmanr(bdf["gt"], bdf["clip_top3"])
    summaries = []
    for _, g in bdf.groupby("clip_idx"):
        v = dict(zip(g["tier"], g["clip_top3"]))
        summaries.append(
            v.get("tier3_va11y", 0) > v.get("tier2_vatex_long", 0) > v.get("tier1_vatex_short", 0) > v.get("tier0_cross", 0)
        )
    return {
        "spearman_rho": float(rho),
        "spearman_p": float(p),
        "full_order_count": int(sum(summaries)),
        "full_order_rate": float(np.mean(summaries)),
        "n_clips": len(summaries),
    }


def main() -> None:
    registry = load_registry()
    if not registry:
        print("No external clips in registry", file=sys.stderr)
        sys.exit(1)

    device = torch.device(device_name())
    print(f"Loading CLIP on {device}...")
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    all_rows = []
    for i, meta in enumerate(registry):
        print(f"[{i+1}/{len(registry)}] {meta['video_id']} ({meta['category']})")
        try:
            all_rows.extend(evaluate_clip(meta, model, preprocess, tokenizer, device))
        except Exception as e:
            print(f"  FAIL: {e}", file=sys.stderr)

    df = pd.DataFrame(all_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    per_clip = []
    for vid, g in df.groupby("video_id"):
        s = clip_summary(g)
        s["video_id"] = vid
        s["category"] = g["category"].iloc[0]
        per_clip.append(s)
    pc = pd.DataFrame(per_clip)

    # Spearman on external CLIP scores
    rho, p = spearmanr(df["gt"], df["clip_top3"]) if len(df) > 4 else (float("nan"), float("nan"))

    bench_same = benchmark_same_method(model, preprocess, tokenizer, device)
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "n_external_clips": len(pc),
        "n_tier_rows": len(df),
        "external_clip_spearman_rho": float(rho),
        "external_clip_spearman_p": float(p),
        "external_full_order": int(pc["full_order_clip"].sum()),
        "external_full_order_rate": float(pc["full_order_clip"].mean()),
        "external_pro_beats_short": int(pc["pro_beats_short"].sum()),
        "benchmark_same_clip_method": bench_same,
        "per_clip": per_clip,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== RESULTS ===")
    print(f"External CLIP ρ: {rho:.3f} (p={p:.4f}) | full order {report['external_full_order']}/{len(pc)}")
    if bench_same:
        print(f"Benchmark SAME method ρ: {bench_same['spearman_rho']:.3f} | full order {bench_same['full_order_count']}/{bench_same['n_clips']}")
        gap = bench_same["spearman_rho"] - rho
        print(f"Generalization gap Δρ: {gap:.3f}")
    print(f"Wrote {OUT_CSV} and {OUT_JSON}")
    sys.exit(0)


if __name__ == "__main__":
    main()
