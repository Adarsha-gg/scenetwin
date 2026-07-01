"""Need-weighted CLIP grounding on external clips, using the REAL TRIBE
per-timestep need (not the motion+speech proxy).

The prior external eval (cursor/output/external_need_weighted_eval.csv,
2026-05-27) used a motion+speech proxy because per-timestep TRIBE preds were
unavailable; need-weighting then HURT (lift vs plain top3 = -0.010). The
tribe_tensors_all78 dump now provides real per-timestep P_AV/P_A for all 60
external clips, so we can finally test whether the genuine fMRI-encoder need
helps where the proxy did not.

Pipeline (mirrors cursor/pipeline/external_need_weighted_eval.py):
  - CLIP ViT-L-14 image features per frame, text features per tier
  - sims = frame x tier cosine
  - real TRIBE need(t) = 0.5*minmax(residual_norm)+0.5*minmax(cosine_gap),
    same formula as tools/scenetwin_neural_need_curve.py, interpolated from the
    ~T TRIBE timesteps onto the N CLIP frames by relative time.
  - need_weighted_clip = weighted_avg(sims, need_at_frame)
  - compare Spearman vs gt across 4 tiers x 60 clips.
"""
import json
from pathlib import Path

import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from scipy.stats import spearmanr

import tribe_tensors_load as T

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "cursor" / "data" / "external_clips"
TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
GT = {t: i for i, t in enumerate(TIERS)}


def minmax(v):
    v = np.asarray(v, float)
    lo, hi = v.min(), v.max()
    return np.zeros_like(v) if hi == lo else (v - lo) / (hi - lo)


def tribe_need(pav, pa):
    n = min(pav.shape[0], pa.shape[0])
    pav, pa = pav[:n], pa[:n]
    resid = np.linalg.norm(pav - pa, axis=1) / np.sqrt(pav.shape[1])
    cos = np.array([1.0 - np.dot(pav[i], pa[i]) /
                    (np.linalg.norm(pav[i]) * np.linalg.norm(pa[i]) + 1e-9) for i in range(n)])
    return 0.5 * minmax(resid) + 0.5 * minmax(cos)


def interp_to_frames(need, n_frames):
    """Map T TRIBE need values onto n_frames by relative position in [0,1]."""
    if len(need) == n_frames:
        return need
    xt = np.linspace(0, 1, len(need))
    xf = np.linspace(0, 1, n_frames)
    return np.interp(xf, xt, need)


def wavg(vals, w):
    w = np.asarray(w, float)
    return float(np.dot(vals, w) / w.sum()) if w.sum() > 1e-9 else float(vals.mean())


def full_order(df, col):
    n = wins = 0
    for _, g in df.groupby("video_id"):
        v = dict(zip(g.tier, g[col])); n += 1
        if v["tier3_va11y"] > v["tier2_vatex_long"] > v["tier1_vatex_short"] > v["tier0_cross"]:
            wins += 1
    return wins, n


def main():
    reg = {m["video_id"]: m for m in
           (json.loads(l) for l in (EXT / "registry.jsonl").read_text().splitlines() if l.strip())}
    man = T.load_manifest()
    man = man[man.corpus == "external"]

    dev = ("cuda" if torch.cuda.is_available() else
           "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
    print(f"CLIP ViT-L-14 on {dev} ...")
    model, _, prep = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tok = open_clip.get_tokenizer("ViT-L-14")
    model.to(dev).eval()

    rows = []
    for i, (_, r) in enumerate(man.iterrows()):
        vid = r.video_id
        meta = reg.get(vid)
        frames = sorted((EXT / "frames" / vid).glob("frame_*.jpg"))
        if not meta or not frames:
            continue
        tens, _ = T.load_clip(r.clip_key)
        need = interp_to_frames(tribe_need(tens["P_AV"], tens["P_A"]), len(frames))
        imgs = torch.stack([prep(Image.open(p).convert("RGB")) for p in frames]).to(dev)
        with torch.no_grad():
            imf = model.encode_image(imgs); imf = imf / imf.norm(dim=-1, keepdim=True)
        for tier in TIERS:
            tk = tok([meta[tier]]).to(dev)
            with torch.no_grad():
                tf = model.encode_text(tk); tf = tf / tf.norm(dim=-1, keepdim=True)
            sims = (imf @ tf.T).squeeze().cpu().numpy()
            k = min(3, len(sims))
            rows.append({"video_id": vid, "tier": tier, "gt": GT[tier],
                         "clip_top3": float(np.sort(sims)[-k:].mean()),
                         "clip_mean": float(sims.mean()),
                         "tribe_need_weighted": wavg(sims, need)})
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(man)} clips")

    df = pd.DataFrame(rows)
    out = ROOT / "cursor/research/output/tribe_need_weighted_real.csv"
    df.to_csv(out, index=False)

    print("\n=== REAL TRIBE need-weighted CLIP vs plain (external, n_clips="
          f"{df.video_id.nunique()}) ===")
    base = None
    for col in ["clip_top3", "clip_mean", "tribe_need_weighted"]:
        rho, p = spearmanr(df.gt, df[col])
        fo, n = full_order(df, col)
        if col == "clip_top3":
            base = rho
        lift = f"  (lift vs top3 {rho-base:+.4f})" if col == "tribe_need_weighted" else ""
        print(f"  {col:22s} rho={rho:.4f} p={p:.1e}  full_order={fo}/{n}{lift}")
    print(f"\n  prior PROXY need lift vs top3 was -0.0104 (motion+speech)")
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
