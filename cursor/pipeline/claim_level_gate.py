#!/usr/bin/env python3
"""A REAL reference-free hallucination gate via CLAIM-LEVEL visual grounding.

The paired experiment (hallucination_gate.py) needed the expert AD to measure a grounding
DROP. In deployment you only have a candidate AD + the frames. This gate removes the
reference: decompose the candidate AD into atomic visual claims, CLIP-ground EACH claim
against the frames, and judge the AD by its WEAKEST claim. A fabricated fact ("red mittens",
"concert hall") is an ungrounded claim that drags the minimum down — no reference needed.

Calibration: the faithful-paraphrase + expert ADs are all-true (negatives); the corrupted
ADs carry a lie (positives). We set the threshold on the clean ADs' weakest-claim grounding
(operating point = fixed false-positive rate) and report the hallucination recall there.

Two levels:
  CLAIM level  — are the fabricated claims the lowest-grounded? (AUC, no threshold needed)
  AD level     — flag the AD if its weakest claim grounds below tau (a deployable gate)

The DECISION is 100% CLIP (deterministic, grader-free). The LLM is used only to split text
into claims (content extraction, not judgement), so the gate does not grade its own work.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine_ad_tier as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
SRC = CURSOR / "output" / "halluc_gate" / "halluc_gate.csv"
CACHE = CURSOR / "output" / "claim_gate" / "cache"
OUT_JSON = CURSOR / "output" / "claim_level_gate.json"
OUT_CSV = CURSOR / "output" / "claim_gate" / "claims.csv"
CHART = ROOT / "output" / "charts" / "scenetwin_claim_gate.png"
FINDINGS = CURSOR / "findings" / "claim-level-gate.md"

CLAIM_PROMPT = """Break this audio description into atomic VISUAL claims. Each claim is a short
self-contained phrase (3-7 words) asserting ONE thing a viewer could see: a subject, an
attribute (color/size), an action, an object, or the setting. Do not invent anything; only
restate what the text says.
Description: "{ad}"
Return JSON only: {{"claims": ["...", "..."]}}"""


def decompose(cl, key, ad, refresh):
    payload = {"kind": "claims_v1", "model": M.MODEL, "ad": ad}

    def call():
        return M.parse_json(M.gen_content(cl, CLAIM_PROMPT.format(ad=ad)))

    M.CACHE = CACHE
    r = M.cache_json(f"claims_{key}", payload, call, refresh) or {}
    cs = [str(c).strip() for c in r.get("claims", []) if str(c).strip()]
    return [c for c in cs if 1 <= len(c.split()) <= 12]


def clip_image_feats(model, preprocess, device, paths):
    import torch
    imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in paths]).to(device)
    with torch.no_grad():
        f = model.encode_image(imgs); f = f / f.norm(dim=-1, keepdim=True)
    return f


def ground(model, tokenizer, device, img_feats, text):
    """Return (top3-mean, top1-max) cosine of a claim vs the precomputed frame features.
    top1 = 'does the single best frame show this?' -> better for object presence."""
    import torch
    tok = tokenizer([text]).to(device)
    with torch.no_grad():
        t = model.encode_text(tok); t = t / t.norm(dim=-1, keepdim=True)
        sims = np.sort((img_feats @ t.T).squeeze(-1).cpu().numpy())
    return float(sims[-min(3, len(sims)):].mean()), float(sims[-1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--provider", default="gemini")
    ap.add_argument("--model", default=None)
    ap.add_argument("--fpr", type=float, default=0.10, help="target false-positive rate for the operating point")
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()
    M.load_env(); M.configure(args.provider, args.model)
    cl = M.client()

    import open_clip, torch
    from sentence_transformers import SentenceTransformer
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    clipm, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    clipm.to(device).eval()
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    df = pd.read_csv(SRC)
    if args.limit:
        df = df.head(args.limit)

    claim_rows, ad_rows = [], []
    for i, r in df.iterrows():
        vid = r["video_id"]
        paths = M.frame_paths(vid)
        if len(paths) < M.N_FRAMES:
            continue
        feats = clip_image_feats(clipm, preprocess, device, paths)
        kinds = {"expert": r["expert_text"], "halluc": r["halluc_text"], "para": r["para_text"]}
        if any(not isinstance(v, str) or len(v.split()) < 6 for v in kinds.values()):
            continue
        exp_claims = decompose(cl, f"{vid}_e", kinds["expert"], args.refresh_cache)
        if not exp_claims:
            continue
        exp_emb = embedder.encode(exp_claims, normalize_embeddings=True)
        for kind, text in kinds.items():
            claims = exp_claims if kind == "expert" else decompose(cl, f"{vid}_{kind[0]}", text, args.refresh_cache)
            if not claims:
                continue
            g3, g1 = zip(*[ground(clipm, tokenizer, device, feats, c) for c in claims])
            g3, g1 = np.array(g3), np.array(g1)
            # for halluc claims, flag the ones with no close match in the expert -> fabricated
            if kind == "halluc":
                hemb = embedder.encode(claims, normalize_embeddings=True)
                novelty = 1 - (hemb @ exp_emb.T).max(axis=1)  # high => not in expert => fabricated
            else:
                novelty = np.zeros(len(claims))
            for c, gg3, gg1, nov in zip(claims, g3, g1, novelty):
                claim_rows.append({"video_id": vid, "kind": kind, "claim": c,
                                   "grounding": float(gg3), "grounding_top1": float(gg1),
                                   "novelty": float(nov),
                                   "fabricated": int(kind == "halluc" and nov > 0.5)})
            # within-AD standardized minimum: how much the weakest claim stands out from
            # the AD's own claims (reference-free; a lie should be an internal outlier)
            sd = g1.std() if g1.std() > 1e-6 else 1.0
            min_z = float((g1.min() - g1.mean()) / sd)
            ad_rows.append({"video_id": vid, "kind": kind, "n_claims": len(claims),
                            "min_ground": float(g1.min()),
                            "mean_bottom2": float(np.sort(g1)[:2].mean()),
                            "min_z": min_z,
                            "label": int(kind == "halluc")})
        print(f"[{i+1}/{len(df)}] {vid}: claims e/h/p done")

    cdf = pd.DataFrame(claim_rows); adf = pd.DataFrame(ad_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True); cdf.to_csv(OUT_CSV, index=False)

    from sklearn.metrics import roc_auc_score, roc_curve

    # CLAIM level: fabricated vs true claims (true = expert/para claims + matched halluc claims)
    GCOL = "grounding_top1"
    fab = cdf[cdf.fabricated == 1][GCOL].values
    tru = cdf[(cdf.kind.isin(["expert", "para"])) | ((cdf.kind == "halluc") & (cdf.fabricated == 0))][GCOL].values
    yc = np.r_[np.ones(len(fab)), np.zeros(len(tru))]
    sc = np.r_[fab, tru]
    claim_auc = float(roc_auc_score(yc, -sc))  # lower grounding => more likely fabricated

    # AD level: flag AD by weakest claim; clean = expert+para, lie = halluc
    def ad_gate(score_col):
        clean = adf[adf.kind != "halluc"][score_col].values
        lie = adf[adf.kind == "halluc"][score_col].values
        y = np.r_[np.ones(len(lie)), np.zeros(len(clean))]
        s = -np.r_[lie, clean]  # lower grounding => positive (lie)
        auc = float(roc_auc_score(y, s))
        # operating point: threshold at target FPR on clean
        tau = float(np.quantile(clean, args.fpr))   # flag if score < tau
        recall = float((lie < tau).mean())
        fpr = float((clean < tau).mean())
        return {"auc": auc, "tau": tau, "recall_at_fpr": recall, "actual_fpr": fpr,
                "clean_median": float(np.median(clean)), "lie_median": float(np.median(lie))}

    rep = {"run_at": datetime.now(timezone.utc).isoformat(), "grader": f"{M.PROVIDER}/{M.MODEL}",
           "decision_signal": "CLIP claim grounding (grader-free)",
           "n_clips": int(adf.video_id.nunique()),
           "n_claims": int(len(cdf)), "n_fabricated_claims": int(len(fab)),
           "claim_level": {"auc_fabricated_vs_true": claim_auc,
                           "fabricated_grounding_mean": float(fab.mean()),
                           "true_grounding_mean": float(tru.mean())},
           "ad_gate_min": ad_gate("min_ground"),
           "ad_gate_bottom2": ad_gate("mean_bottom2"),
           "ad_gate_min_z": ad_gate("min_z"),
           "target_fpr": args.fpr}
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.7))
    ax1.hist(tru, bins=20, alpha=0.6, label="true claims", color="#90a4ae", density=True)
    ax1.hist(fab, bins=20, alpha=0.7, label="fabricated claims", color="#b71c1c", density=True)
    ax1.axvline(fab.mean(), color="#b71c1c", ls="--", lw=1)
    ax1.axvline(tru.mean(), color="#455a64", ls="--", lw=1)
    ax1.set_xlabel("CLIP claim grounding"); ax1.set_ylabel("density")
    ax1.set_title(f"Claim level: fabricated claims are less grounded\nAUC={claim_auc:.2f} "
                  f"(n_fab={len(fab)}, n_true={len(tru)})")
    ax1.legend(fontsize=8); ax1.grid(alpha=0.25)

    g = rep["ad_gate_min"]
    y = np.r_[np.ones((adf.kind == "halluc").sum()), np.zeros((adf.kind != "halluc").sum())]
    s = -np.r_[adf[adf.kind == "halluc"]["min_ground"].values, adf[adf.kind != "halluc"]["min_ground"].values]
    fpr, tpr, _ = roc_curve(y, s)
    ax2.plot(fpr, tpr, "-", color="#1b5e20", lw=2, label=f"weakest-claim gate (AUC={g['auc']:.2f})")
    ax2.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    ax2.scatter([g["actual_fpr"]], [g["recall_at_fpr"]], color="#b71c1c", zorder=5,
                label=f"operating pt: recall {g['recall_at_fpr']:.0%} @ FPR {g['actual_fpr']:.0%}")
    ax2.set_xlabel("false-positive rate (flagging a true AD)")
    ax2.set_ylabel("hallucination recall")
    ax2.set_title("AD-level gate: reference-free ROC")
    ax2.legend(fontsize=8, loc="lower right"); ax2.grid(alpha=0.25)
    fig.suptitle(f"Reference-free claim-level hallucination gate (n={rep['n_clips']} clips)", fontsize=11)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    print(f"\nCLAIM level: fabricated grounding {fab.mean():.3f} vs true {tru.mean():.3f}  AUC={claim_auc:.3f}")
    print(f"AD gate (weakest claim):  AUC={g['auc']:.3f}  recall={g['recall_at_fpr']:.0%} @ FPR={g['actual_fpr']:.0%}")
    b = rep["ad_gate_bottom2"]; z = rep["ad_gate_min_z"]
    print(f"AD gate (mean bottom-2):  AUC={b['auc']:.3f}  recall={b['recall_at_fpr']:.0%} @ FPR={b['actual_fpr']:.0%}")
    print(f"AD gate (within-AD min-z):AUC={z['auc']:.3f}  recall={z['recall_at_fpr']:.0%} @ FPR={z['actual_fpr']:.0%}")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
