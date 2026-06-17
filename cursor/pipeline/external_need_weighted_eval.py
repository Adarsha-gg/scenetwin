#!/usr/bin/env python3
"""Need-weighted CLIP on external clips — full eval with plain vs weighted comparison."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
EXT = CURSOR / "data" / "external_clips"
REGISTRY = EXT / "registry.jsonl"
FRAMES = EXT / "frames"
NEED_DIR = EXT / "need"
OUT = CURSOR / "output" / "external_need_weighted_eval.csv"
OUT_JSON = CURSOR / "output" / "external_need_weighted_eval.json"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def weighted_avg(vals: np.ndarray, w: np.ndarray) -> float:
    w = np.asarray(w, dtype=float)
    if w.sum() <= 1e-9:
        return float(vals.mean())
    return float(np.dot(vals, w) / w.sum())


def full_order_rate(df: pd.DataFrame, col: str) -> tuple[int, int]:
    n = 0
    wins = 0
    for _, g in df.groupby("video_id"):
        v = dict(zip(g["tier"], g[col]))
        n += 1
        if v.get("tier3_va11y", 0) > v.get("tier2_vatex_long", 0) > v.get("tier1_vatex_short", 0) > v.get("tier0_cross", 0):
            wins += 1
    return wins, n


def eval_df(df: pd.DataFrame, col: str) -> dict:
    rho, p = spearmanr(df["gt"], df[col])
    fo, n = full_order_rate(df, col)
    return {"spearman_rho": float(rho), "spearman_p": float(p), "full_order": fo, "n_clips": n}


def main() -> None:
    # Step 1: need curves
    import subprocess
    subprocess.check_call([sys.executable, str(Path(__file__).parent / "external_need_proxy.py")], cwd=str(ROOT))

    registry = [json.loads(l) for l in REGISTRY.read_text().splitlines() if l.strip()]
    device = torch.device(device_name())
    print(f"CLIP ViT-L-14 on {device}")
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    rows = []
    for meta in registry:
        vid = meta["video_id"]
        frames = sorted((FRAMES / vid).glob("frame_*.jpg"))
        need_path = NEED_DIR / f"{vid}.csv"
        if not frames or not need_path.exists():
            continue
        need = pd.read_csv(need_path)
        w_need = need["need_score"].to_numpy()
        w_std = need["standard_slot_score"].to_numpy()
        imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in frames]).to(device)
        with torch.no_grad():
            img_f = model.encode_image(imgs)
            img_f = img_f / img_f.norm(dim=-1, keepdim=True)
        img_f_cpu = img_f.cpu().numpy()

        for tier in TIERS:
            text = meta[tier]
            tokens = tokenizer([text]).to(device)
            with torch.no_grad():
                txt_f = model.encode_text(tokens)
                txt_f = txt_f / txt_f.norm(dim=-1, keepdim=True)
            sims = (img_f @ txt_f.T).squeeze().cpu().numpy()
            k = min(3, len(sims))
            rows.append({
                "video_id": vid,
                "category": meta["category"],
                "tier": tier,
                "gt": TIER_GT[tier],
                "clip_top3": float(np.sort(sims)[-k:].mean()),
                "clip_mean": float(sims.mean()),
                "need_weighted_clip": weighted_avg(sims, w_need),
                "standard_slot_weighted": weighted_avg(sims, w_std),
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    metrics = {}
    for col in ["clip_top3", "clip_mean", "need_weighted_clip", "standard_slot_weighted"]:
        metrics[col] = eval_df(df, col)

    # Does need-weighting help vs plain top3?
    lift = metrics["need_weighted_clip"]["spearman_rho"] - metrics["clip_top3"]["spearman_rho"]
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "n_clips": df["video_id"].nunique(),
        "metrics": metrics,
        "need_weighted_lift_vs_top3": lift,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== NEED-WEIGHTED CLIP (external) ===")
    for k, v in metrics.items():
        print(f"  {k}: ρ={v['spearman_rho']:.3f} full_order={v['full_order']}/{v['n_clips']}")
    print(f"  lift need-weighted vs top3: {lift:+.3f}")
    print(f"Wrote {OUT} {OUT_JSON}")


if __name__ == "__main__":
    main()
