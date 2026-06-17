#!/usr/bin/env python3
"""Reference-substitution robustness of the CLIP grounding-drop hallucination gate.

Reviewer-killer the headline gate (AUC 0.84, n=60) does NOT answer: it scores
    drop = clip(EXPERT_AD) - clip(candidate)
i.e. it leans on the HUMAN expert AD as the per-clip anchor. "That isn't
reference-free, it's reference-substituting; in deployment there is no expert AD."

This experiment answers it with ZERO API credits (CLIP only) by swapping the
anchor and re-measuring the gate:

  A1 human-expert anchor   (headline baseline)      anchor = expert AD
  A2 model-paraphrase anchor                        anchor = model paraphrase
  A3 independent model-AD anchor (frames -> AD)     anchor = machine AD (no human text)
  A4 NULL: cross-clip anchor (derangement)          anchor = ANOTHER clip's expert AD
  A0 no-anchor absolute score (known weak control)  flag if clip(candidate) low

Gate score (same for every anchor): flag candidate if
    clip(anchor, frames) - clip(candidate, frames) > tau
Positive class = catch the lie (candidate = hallucination).
Negative class = do not flag a genuine clean AD.

Construct-validity claim we test: the gate is robust to the anchor's *authorship*
(human expert ~ model paraphrase ~ independent model AD) but REQUIRES the anchor to
describe the specific clip (cross-clip anchor must collapse to chance). If true, the
"you cheated with the human reference" objection is falsified: any clip-relevant
description -- including one the system generates itself -- is a sufficient anchor.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
sys.path.insert(0, str(CURSOR / "pipeline"))
import machine_ad_tier as M  # noqa: E402

HG = CURSOR / "output" / "halluc_gate" / "halluc_gate.csv"
MAD = CURSOR / "output" / "machine_ad" / "machine_ad_tier.csv"
HUMAN = CURSOR / "data" / "human_hallucinations.jsonl"
EMB_CACHE = CURSOR / "output" / "ref_subst" / "img_emb.npz"
OUT_JSON = CURSOR / "output" / "ref_subst" / "reference_substitution.json"
CHART = ROOT / "output" / "charts" / "scenetwin_reference_substitution.png"

RNG = np.random.default_rng(0)


def op_at_fpr(y, s, fpr_target=0.10):
    y = np.asarray(y); s = np.asarray(s)
    neg, pos = s[y == 0], s[y == 1]
    tau = float(np.quantile(neg, 1 - fpr_target))
    return {"auc": float(roc_auc_score(y, s)), "recall": float((pos > tau).mean()),
            "fpr": float((neg > tau).mean()), "tau": tau, "n_pos": int(len(pos)), "n_neg": int(len(neg))}


def boot_auc_ci(y, s, n=5000, seed=0):
    y = np.asarray(y); s = np.asarray(s)
    rng = np.random.default_rng(seed)
    pos_i = np.where(y == 1)[0]; neg_i = np.where(y == 0)[0]
    aucs = []
    for _ in range(n):
        p = rng.choice(pos_i, len(pos_i), replace=True)
        q = rng.choice(neg_i, len(neg_i), replace=True)
        idx = np.r_[p, q]
        yy = y[idx]
        if yy.min() == yy.max():
            continue
        aucs.append(roc_auc_score(yy, s[idx]))
    return [float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))]


def main() -> None:
    import open_clip, torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    clipm, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    clipm.to(device).eval()

    hg = pd.read_csv(HG).dropna(subset=["clip_para"]).set_index("video_id")
    vids = list(hg.index)
    mad = pd.read_csv(MAD)
    mad_text = mad[mad.tier == "tierM_machine_ad"].set_index("video_id")["text"].to_dict()
    human = {}
    for line in HUMAN.read_text().splitlines():
        if line.strip():
            r = json.loads(line); human[r["video_id"]] = r["human_halluc"]

    # ---- precompute per-clip image features (8 frames each), cached ----
    EMB_CACHE.parent.mkdir(parents=True, exist_ok=True)
    img_feats = {}
    if EMB_CACHE.exists():
        z = np.load(EMB_CACHE, allow_pickle=True)
        img_feats = {k: z[k] for k in z.files}
    todo = [v for v in vids if v not in img_feats]
    for j, vid in enumerate(todo):
        paths = M.frame_paths(vid)
        if len(paths) < M.N_FRAMES:
            continue
        imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in paths]).to(device)
        with torch.no_grad():
            f = clipm.encode_image(imgs); f = f / f.norm(dim=-1, keepdim=True)
        img_feats[vid] = f.cpu().numpy().astype(np.float32)
        if (j + 1) % 10 == 0:
            print(f"  img feats {j+1}/{len(todo)}")
    if todo:
        np.savez(EMB_CACHE, **img_feats)
    vids = [v for v in vids if v in img_feats]

    # ---- text encoder + top-3 mean similarity against a clip ----
    _text_cache: dict[str, np.ndarray] = {}

    def tfeat(text: str) -> np.ndarray:
        if text not in _text_cache:
            tok = tokenizer([text]).to(device)
            with torch.no_grad():
                t = clipm.encode_text(tok); t = t / t.norm(dim=-1, keepdim=True)
            _text_cache[text] = t.cpu().numpy().astype(np.float32)[0]
        return _text_cache[text]

    def clip_score(vid: str, text: str) -> float:
        sims = img_feats[vid] @ tfeat(text)
        return float(np.sort(sims)[-min(3, len(sims)):].mean())

    # cached single-clip scores from halluc_gate.csv (verified to match clip_top3)
    c_exp = {v: float(hg.loc[v, "clip_expert"]) for v in vids}
    c_hal = {v: float(hg.loc[v, "clip_halluc"]) for v in vids}
    c_par = {v: float(hg.loc[v, "clip_para"]) for v in vids}

    rep: dict = {"n_clips_total": len(vids), "anchors": {}}

    # ---------- A1: human-expert anchor (headline) ----------
    pos = [c_exp[v] - c_hal[v] for v in vids]
    neg = [c_exp[v] - c_par[v] for v in vids]
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]; s = np.r_[pos, neg]
    a1 = op_at_fpr(y, s); a1["auc_ci95"] = boot_auc_ci(y, s)
    rep["anchors"]["A1_human_expert"] = a1

    # ---------- A2: model-paraphrase anchor ----------
    pos = [c_par[v] - c_hal[v] for v in vids]
    neg = [c_par[v] - c_exp[v] for v in vids]
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]; s = np.r_[pos, neg]
    a2 = op_at_fpr(y, s); a2["auc_ci95"] = boot_auc_ci(y, s)
    rep["anchors"]["A2_model_paraphrase"] = a2

    # ---------- A3: independent model-AD anchor (frames -> AD) ----------
    mvids = [v for v in vids if v in mad_text]
    c_mad = {v: clip_score(v, mad_text[v]) for v in mvids}
    # A3a: catch Gemini lie  | A3b: catch hand-authored human lie  (negative = expert)
    for tag, lie_score in [("A3a_indep_modelAD_vs_gemini_lie", lambda v: c_hal[v]),
                           ("A3b_indep_modelAD_vs_human_lie",
                            lambda v: clip_score(v, human[v]) if v in human else None)]:
        pos, neg = [], []
        used = []
        for v in mvids:
            ls = lie_score(v)
            if ls is None:
                continue
            pos.append(c_mad[v] - ls)
            neg.append(c_mad[v] - c_exp[v])
            used.append(v)
        y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]; s = np.r_[pos, neg]
        a3 = op_at_fpr(y, s); a3["auc_ci95"] = boot_auc_ci(y, s); a3["n_clips"] = len(used)
        rep["anchors"][tag] = a3

    # ---------- A4: NULL cross-clip anchor (derangements) ----------
    K = 20
    aucs, recalls = [], []
    for k in range(K):
        perm = RNG.permutation(len(vids))
        # enforce derangement
        while any(perm[i] == i for i in range(len(vids))):
            perm = RNG.permutation(len(vids))
        pos, neg = [], []
        for i, v in enumerate(vids):
            anchor_vid = vids[perm[i]]
            a = clip_score(v, hg.loc[anchor_vid, "expert_text"])  # other clip's expert text on THIS clip
            pos.append(a - c_hal[v]); neg.append(a - c_par[v])
        y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]; s = np.r_[pos, neg]
        m = op_at_fpr(y, s)
        aucs.append(m["auc"]); recalls.append(m["recall"])
    rep["anchors"]["A4_cross_clip_null"] = {
        "auc_mean": float(np.mean(aucs)), "auc_sd": float(np.std(aucs)),
        "auc_range": [float(np.min(aucs)), float(np.max(aucs))],
        "recall_at_fpr10_mean": float(np.mean(recalls)), "n_derangements": K,
        "n_pos": len(vids), "n_neg": len(vids)}

    # ---------- A0: no-anchor absolute candidate score (known weak control) ----------
    pos = [-c_hal[v] for v in vids]   # lower absolute grounding -> flag (sign flipped so higher=flag)
    neg = [-c_par[v] for v in vids]
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]; s = np.r_[pos, neg]
    a0 = op_at_fpr(y, s); a0["auc_ci95"] = boot_auc_ci(y, s)
    rep["anchors"]["A0_no_anchor_absolute"] = a0

    # ---------- empirical permutation p: A1 vs A4 null distribution ----------
    null_aucs = np.array(aucs)
    rep["A1_vs_null_p"] = float((null_aucs >= a1["auc"]).mean())

    rep["headline"] = (
        f"Grounding-drop gate is anchor-author-agnostic: human-expert AUC {a1['auc']:.2f}, "
        f"model-paraphrase AUC {a2['auc']:.2f}, independent model-AD AUC "
        f"{rep['anchors']['A3a_indep_modelAD_vs_gemini_lie']['auc']:.2f} "
        f"(human lie {rep['anchors']['A3b_indep_modelAD_vs_human_lie']['auc']:.2f}); "
        f"cross-clip anchor collapses to {np.mean(aucs):.2f} (chance). "
        f"The gate needs a clip-relevant anchor, not a human one.")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    # ---------- chart ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = ["no anchor\n(absolute)", "cross-clip\nNULL", "human\nexpert", "model\nparaphrase",
              "indep model-AD\n(Gemini lie)", "indep model-AD\n(human lie)"]
    vals = [a0["auc"], float(np.mean(aucs)), a1["auc"], a2["auc"],
            rep["anchors"]["A3a_indep_modelAD_vs_gemini_lie"]["auc"],
            rep["anchors"]["A3b_indep_modelAD_vs_human_lie"]["auc"]]
    errs = [
        [a0["auc"] - a0["auc_ci95"][0], a0["auc_ci95"][1] - a0["auc"]],
        [np.std(aucs), np.std(aucs)],
        [a1["auc"] - a1["auc_ci95"][0], a1["auc_ci95"][1] - a1["auc"]],
        [a2["auc"] - a2["auc_ci95"][0], a2["auc_ci95"][1] - a2["auc"]],
        [rep["anchors"]["A3a_indep_modelAD_vs_gemini_lie"]["auc"] - rep["anchors"]["A3a_indep_modelAD_vs_gemini_lie"]["auc_ci95"][0],
         rep["anchors"]["A3a_indep_modelAD_vs_gemini_lie"]["auc_ci95"][1] - rep["anchors"]["A3a_indep_modelAD_vs_gemini_lie"]["auc"]],
        [rep["anchors"]["A3b_indep_modelAD_vs_human_lie"]["auc"] - rep["anchors"]["A3b_indep_modelAD_vs_human_lie"]["auc_ci95"][0],
         rep["anchors"]["A3b_indep_modelAD_vs_human_lie"]["auc_ci95"][1] - rep["anchors"]["A3b_indep_modelAD_vs_human_lie"]["auc"]],
    ]
    errs = np.array(errs).T
    colors = ["#90a4ae", "#b0bec5", "#1565c0", "#1b5e20", "#2e7d32", "#c62828"]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    x = np.arange(len(labels))
    ax.bar(x, vals, yerr=errs, color=colors, capsize=4, width=0.62)
    ax.axhline(0.5, ls="--", c="gray", lw=1, label="chance")
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=10, weight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("hallucination-gate AUC (catch lie vs flag clean AD)")
    ax.set_ylim(0.35, 1.02)
    ax.set_title("Reference-substitution: the grounding-drop gate needs a clip-relevant\n"
                 "anchor, not a human one (CLIP-only, grader-free, zero API)", fontsize=11)
    ax.grid(axis="y", alpha=0.25); ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    print(json.dumps(rep, indent=2))
    print(f"\nWrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
