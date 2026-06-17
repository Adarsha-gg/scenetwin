#!/usr/bin/env python3
"""Close the two review holes before the paper subsection (zero API credits).

1. Same-family circularity: hand-authored fabrications (cursor/data/human_hallucinations.jsonl)
   scored with CLIP only; compare grounding-drop separation to Gemini-generated lies.
2. Reference-free identity: self-consistency gate where the reference is a SECOND model
   generation (machine AD or best-of-N candidate), not the human expert AD.

Decision signal throughout: CLIP top-3 grounding only (grader-free).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
HUMAN = CURSOR / "data" / "human_hallucinations.jsonl"
HG = CURSOR / "output" / "halluc_gate" / "halluc_gate.csv"
MAD = CURSOR / "output" / "machine_ad" / "machine_ad_tier.csv"
BON = CURSOR / "output" / "best_of_n" / "best_of_n_candidates.csv"
OUT_JSON = CURSOR / "output" / "gate_review_holes.json"
CHART = ROOT / "output" / "charts" / "scenetwin_gate_review_holes.png"
FINDINGS = CURSOR / "findings" / "gate-review-holes.md"
SUBSECTION = ROOT / "output" / "reports" / "paper-ad-safety-gate.md"

sys_path = str(CURSOR / "pipeline")
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
import machine_ad_tier as M  # noqa: E402


def clip_score(model, preprocess, tokenizer, device, paths, text):
    return M.clip_top3(model, preprocess, tokenizer, device, paths, text)


def op_at_fpr(y, s, fpr_target=0.10):
    neg, pos = s[y == 0], s[y == 1]
    tau = float(np.quantile(neg, 1 - fpr_target))
    return {"auc": float(roc_auc_score(y, s)), "recall": float((pos > tau).mean()),
            "fpr": float((neg > tau).mean()), "tau": tau}


def gate_auc(positive_drops, negative_drops):
    y = np.r_[np.ones(len(positive_drops)), np.zeros(len(negative_drops))]
    s = np.r_[positive_drops, negative_drops]
    return op_at_fpr(y, s)


def main() -> None:
    human = {}
    for line in HUMAN.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            human[rec["video_id"]] = rec
    hg = pd.read_csv(HG).set_index("video_id")
    mad = pd.read_csv(MAD)
    mad_text = mad[mad.tier == "tierM_machine_ad"].set_index("video_id")["text"].to_dict()
    bon = pd.read_csv(BON)
    bon_ref = bon[bon.cand == "c0"].set_index("video_id")["ad"].to_dict()
    bon_clean = bon[bon.cand == "c1"].set_index("video_id")["ad"].to_dict()

    import open_clip, torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    clipm, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    clipm.to(device).eval()

    rows = []
    for vid, rec in human.items():
        if vid not in hg.index:
            continue
        paths = M.frame_paths(vid)
        if len(paths) < M.N_FRAMES:
            continue
        ex = hg.loc[vid, "expert_text"]
        gh = hg.loc[vid, "halluc_text"]
        gp = hg.loc[vid, "para_text"]
        hh = rec["human_halluc"]
        c_ex = float(hg.loc[vid, "clip_expert"])  # reuse cached
        c_gh = float(hg.loc[vid, "clip_halluc"])
        c_gp = float(hg.loc[vid, "clip_para"])
        c_hh = clip_score(clipm, preprocess, tokenizer, device, paths, hh)
        rows.append({"video_id": vid, "clip_human_halluc": c_hh,
                     "drop_human_vs_expert": c_ex - c_hh,
                     "drop_gemini_vs_expert": c_ex - c_gh,
                     "drop_para_vs_expert": c_ex - c_gp})
    hdf = pd.DataFrame(rows)

    # --- Hole 1: human lies vs expert reference ---
    h1_human = gate_auc(hdf.drop_human_vs_expert.values, hdf.drop_para_vs_expert.values)
    h1_gemini = gate_auc(hdf.drop_gemini_vs_expert.values, hdf.drop_para_vs_expert.values)
    h1_human["n"] = len(hdf)
    h1_gemini["n"] = len(hdf)
    h1_human["mean_drop_lie"] = float(hdf.drop_human_vs_expert.mean())
    h1_human["mean_drop_clean"] = float(hdf.drop_para_vs_expert.mean())
    h1_gemini["mean_drop_lie"] = float(hdf.drop_gemini_vs_expert.mean())

    # --- Hole 2: self-consistency (second-gen reference) ---
    # Reference = machine AD or bon c0; clean = other bon candidates (c1,c2,c3) from same model.
    sc_lie, sc_clean = [], []
    sc_meta = []
    for vid in human:
        ref = mad_text.get(vid) or bon_ref.get(vid)
        cleans = [bon.loc[(bon.video_id == vid) & (bon.cand == c), "ad"].values
                  for c in ("c1", "c2", "c3")]
        cleans = [c[0] for c in cleans if len(c)]
        if not ref or not cleans or vid not in hg.index:
            continue
        paths = M.frame_paths(vid)
        if len(paths) < M.N_FRAMES:
            continue
        c_ref = clip_score(clipm, preprocess, tokenizer, device, paths, ref)
        c_lie = clip_score(clipm, preprocess, tokenizer, device, paths, human[vid]["human_halluc"])
        sc_lie.append(c_ref - c_lie)
        for clean in cleans:
            c_clean = clip_score(clipm, preprocess, tokenizer, device, paths, clean)
            sc_clean.append(c_ref - c_clean)
        sc_meta.append(vid)
    h2 = gate_auc(np.array(sc_lie), np.array(sc_clean))
    h2["n_clips"] = len(sc_meta)
    h2["n_clean_pairs"] = len(sc_clean)
    h2["mean_drop_lie"] = float(np.mean(sc_lie))
    h2["mean_drop_clean"] = float(np.mean(sc_clean))

    # Full 60-clip expert-reference CLIP-only (from cached scores, grader-free)
    hg60 = pd.read_csv(HG).dropna(subset=["clip_para"])
    full_clip = gate_auc((hg60.clip_expert - hg60.clip_halluc).values,
                         (hg60.clip_expert - hg60.clip_para).values)
    full_clip["n"] = len(hg60)

    rep = {"human_fabrications_n": len(hdf), "self_consistency_clips": h2["n_clips"],
           "expert_reference_clip_gate_n60": full_clip,
           "human_lies_expert_ref": h1_human, "gemini_lies_expert_ref": h1_gemini,
           "human_lies_self_consistency_ref": h2,
           "headline_defensible": "CLIP grounding-drop gate, expert reference, n=60: "
                                  f"AUC {full_clip['auc']:.2f}, {full_clip['recall']:.0%} recall @ {full_clip['fpr']:.0%} FPR"}
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))

    # panel A: drop distributions human vs gemini lies (expert ref)
    ax = axes[0]
    ax.boxplot([hdf.drop_para_vs_expert, hdf.drop_human_vs_expert, hdf.drop_gemini_vs_expert],
               tick_labels=["paraphrase\n(clean)", "human lie", "Gemini lie"], widths=0.55)
    ax.axhline(0, ls="--", c="gray", lw=0.8)
    ax.set_ylabel("CLIP grounding drop vs expert AD")
    ax.set_title(f"Hole 1: human-authored lies (n={len(hdf)})\n"
                 f"human AUC={h1_human['auc']:.2f}  Gemini AUC={h1_gemini['auc']:.2f}")
    ax.grid(axis="y", alpha=0.25)

    # panel B: self-consistency ROC
    ax = axes[1]
    y = np.r_[np.ones(len(sc_lie)), np.zeros(len(sc_clean))]
    s = np.r_[sc_lie, sc_clean]
    fpr, tpr, _ = roc_curve(y, s)
    ax.plot(fpr, tpr, color="#1b5e20", lw=2.2, label=f"self-consistency (AUC={h2['auc']:.2f})")
    ax.scatter([h2["fpr"]], [h2["recall"]], color="#b71c1c", s=45, zorder=5)
    ax.plot([0, 1], [0, 1], "--", c="gray", lw=1)
    ax.axvline(0.10, ls=":", c="gray", lw=1)
    ax.set_xlabel("FPR (flagging clean 2nd-gen AD)"); ax.set_ylabel("recall (catching human lie)")
    ax.set_title(f"Hole 2: ref = 2nd model gen (n={h2['n_clips']} clips)")
    ax.legend(fontsize=8); ax.grid(alpha=0.25)

    # panel C: headline ROC expert-ref n=60
    ax = axes[2]
    dh = (hg60.clip_expert - hg60.clip_halluc).values
    dp = (hg60.clip_expert - hg60.clip_para).values
    y60 = np.r_[np.ones(len(dh)), np.zeros(len(dp))]
    s60 = np.r_[dh, dp]
    fpr60, tpr60, _ = roc_curve(y60, s60)
    ax.plot(fpr60, tpr60, color="#1565c0", lw=2.2, label=f"CLIP-only expert-ref (AUC={full_clip['auc']:.2f})")
    ax.scatter([full_clip["fpr"]], [full_clip["recall"]], color="#b71c1c", s=45, zorder=5)
    ax.plot([0, 1], [0, 1], "--", c="gray", lw=1)
    ax.axvline(0.10, ls=":", c="gray", lw=1)
    ax.set_xlabel("FPR"); ax.set_ylabel("recall")
    ax.set_title(f"Headline (defensible): n=60\n{full_clip['recall']:.0%} recall @ {full_clip['fpr']:.0%} FPR")
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    fig.suptitle("Review-hole closure: grader-free CLIP grounding-drop gate", fontsize=11)
    fig.tight_layout()
    CHART.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART, dpi=150)

    print(json.dumps(rep, indent=2))
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
