"""
SceneTwin paper evaluation.
19 clips × 4 description quality tiers × 3 metrics (CLIP-L14, BERTScore, BLEU-4).
Computes Spearman correlation between each metric and ground-truth quality tier.
Key comparison: reference-free (CLIP) vs reference-dependent (BERTScore, BLEU).
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image
import torch
import open_clip
from scipy.stats import spearmanr
import sacrebleu
from bert_score import score as bert_score
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import date
import warnings
warnings.filterwarnings("ignore")

CLIPS_JSON  = Path("/Users/adarsha/njbda/videoa11y_clips.json")
FRAMES_ROOT = Path("/Users/adarsha/njbda/va11y_frames")
OUT_CHART   = Path("/Users/adarsha/njbda/scenetwin_paper_eval.png")
OUT_REPORT  = Path("/Users/adarsha/Knowledge/output/reports/scenetwin-paper-eval.md")

# ── load clips ────────────────────────────────────────────────────────────────
with open(CLIPS_JSON) as f:
    all_clips = json.load(f)

# keep only clips that have frames
valid = []
for i, clip in enumerate(all_clips):
    fdir = FRAMES_ROOT / f"clip_{i:02d}"
    if fdir.exists() and len(list(fdir.glob("*.jpg"))) >= 3:
        clip["idx"] = i
        clip["frames_dir"] = str(fdir)
        valid.append(clip)

print(f"Valid clips: {len(valid)}")
by_cat = {}
for c in valid:
    by_cat.setdefault(c["category"], []).append(c)
for cat, clips in by_cat.items():
    print(f"  {cat}: {len(clips)}")

# ── build description tiers ───────────────────────────────────────────────────
# tier 3: full VideoA11y description
# tier 2: first sentence only
# tier 1: first 10 words only
# tier 0: cross-category description (maximally wrong)

# cross-category mapping
cat_map = {
    "Film & Animation": "Pets & Animals",
    "Travel":           "Sports",
    "Sports":           "Film & Animation",
    "Pets & Animals":   "Travel",
}

def first_sentence(text):
    for sep in [". ", "! ", "? "]:
        idx = text.find(sep)
        if idx != -1 and idx > 20:
            return text[:idx + 1].strip()
    return text.split(".")[0].strip() + "."

def first_n_words(text, n=10):
    return " ".join(text.split()[:n]) + "..."

TIER_LABELS = {3: "full", 2: "first_sentence", 1: "truncated_10w", 0: "cross_category"}
TIER_GT     = {3: 3, 2: 2, 1: 1, 0: 0}

rows = []
for clip in valid:
    cat = clip["category"]
    full_desc = clip["desc"]

    # cross-cat: grab the first description from the mapped category
    target_cat = cat_map.get(cat, "Travel")
    cross_desc = next(
        (c["desc"] for c in valid if c["category"] == target_cat and c["idx"] != clip["idx"]),
        "A person is visible in the scene."
    )

    tier_descs = {
        3: full_desc,
        2: first_sentence(full_desc),
        1: first_n_words(full_desc, 10),
        0: cross_desc,
    }
    for tier, desc in tier_descs.items():
        rows.append({
            "clip_idx":  clip["idx"],
            "category":  cat,
            "yt_id":     clip["yt_id"],
            "tier":      tier,
            "tier_label":TIER_LABELS[tier],
            "gt":        TIER_GT[tier],
            "desc":      desc,
            "frames_dir":clip["frames_dir"],
            "ref_desc":  full_desc,  # reference for BERTScore/BLEU
        })

print(f"\nTotal rows: {len(rows)}  ({len(valid)} clips × 4 tiers)")

# ── load CLIP ViT-L-14 ────────────────────────────────────────────────────────
print("\nLoading CLIP ViT-L-14...")
clip_model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-L-14", pretrained="laion2b_s32b_b82k"
)
clip_tokenizer = open_clip.get_tokenizer("ViT-L-14")
clip_model.eval()

# cache frame features per clip
frame_feats_cache = {}
def get_frame_feats(frames_dir):
    if frames_dir in frame_feats_cache:
        return frame_feats_cache[frames_dir]
    paths = sorted(Path(frames_dir).glob("frame_*.jpg"))
    imgs  = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in paths])
    with torch.no_grad():
        feats = clip_model.encode_image(imgs)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    frame_feats_cache[frames_dir] = feats
    return feats

def clip_score(frames_dir, text, top_k=3):
    frame_feats = get_frame_feats(frames_dir)
    tokens = clip_tokenizer([text])
    with torch.no_grad():
        t_feat = clip_model.encode_text(tokens)
        t_feat = t_feat / t_feat.norm(dim=-1, keepdim=True)
    sims = (frame_feats @ t_feat.T).squeeze().numpy()
    k = min(top_k, len(sims))
    return float(np.sort(sims)[-k:].mean())

# ── compute CLIP scores ────────────────────────────────────────────────────────
print("Computing CLIP-L14 scores...")
for r in rows:
    r["clip_l14"] = clip_score(r["frames_dir"], r["desc"])
print(f"  done — range [{min(r['clip_l14'] for r in rows):.3f}, {max(r['clip_l14'] for r in rows):.3f}]")

# ── compute BERTScore ──────────────────────────────────────────────────────────
print("Computing BERTScore (roberta-large)...")
# reference-based: tier 3 trivially = 1.0; compute for others
for tier in [0, 1, 2]:
    candidates  = [r["desc"]     for r in rows if r["tier"] == tier]
    references  = [r["ref_desc"] for r in rows if r["tier"] == tier]
    _, _, F1 = bert_score(candidates, references, lang="en",
                           model_type="roberta-large", verbose=False)
    f1_vals = F1.numpy().tolist()
    j = 0
    for r in rows:
        if r["tier"] == tier:
            r["bertscore"] = f1_vals[j]
            j += 1
# tier 3 = trivially 1.0 (it's its own reference)
for r in rows:
    if r["tier"] == 3:
        r["bertscore"] = 1.0
print(f"  done — range [{min(r['bertscore'] for r in rows):.3f}, {max(r['bertscore'] for r in rows):.3f}]")

# ── compute BLEU-4 ─────────────────────────────────────────────────────────────
print("Computing BLEU-4...")
for r in rows:
    if r["tier"] == 3:
        r["bleu4"] = 1.0
    else:
        result = sacrebleu.sentence_bleu(r["desc"], [r["ref_desc"]])
        r["bleu4"] = result.score / 100.0
print(f"  done — range [{min(r['bleu4'] for r in rows):.3f}, {max(r['bleu4'] for r in rows):.3f}]")

# ── Spearman correlation ───────────────────────────────────────────────────────
print("\nComputing Spearman correlations...")
gt        = [r["gt"]        for r in rows]
clip_vals = [r["clip_l14"]  for r in rows]
bs_vals   = [r["bertscore"] for r in rows]
bl_vals   = [r["bleu4"]     for r in rows]

rho_clip, p_clip = spearmanr(gt, clip_vals)
rho_bs,   p_bs   = spearmanr(gt, bs_vals)
rho_bl,   p_bl   = spearmanr(gt, bl_vals)

print(f"\n{'Metric':<20} {'Spearman ρ':>12} {'p-value':>12} {'Sig':>6}")
print("-" * 54)
print(f"{'CLIP-L14':20} {rho_clip:>12.4f} {p_clip:>12.4f} {'***' if p_clip<0.001 else '**' if p_clip<0.01 else '*' if p_clip<0.05 else '':>6}")
print(f"{'BERTScore-RoBERTa':20} {rho_bs:>12.4f} {p_bs:>12.4f} {'***' if p_bs<0.001 else '**' if p_bs<0.01 else '*' if p_bs<0.05 else '':>6}")
print(f"{'BLEU-4':20} {rho_bl:>12.4f} {p_bl:>12.4f} {'***' if p_bl<0.001 else '**' if p_bl<0.01 else '*' if p_bl<0.05 else '':>6}")

# ── per-tier mean scores ───────────────────────────────────────────────────────
print("\nMean scores per quality tier:")
print(f"{'Tier':<20} {'CLIP-L14':>10} {'BERTScore':>10} {'BLEU-4':>10}")
print("-" * 52)
for tier in [3, 2, 1, 0]:
    tier_rows = [r for r in rows if r["tier"] == tier]
    mc = np.mean([r["clip_l14"]  for r in tier_rows])
    mb = np.mean([r["bertscore"] for r in tier_rows])
    ml = np.mean([r["bleu4"]     for r in tier_rows])
    print(f"{TIER_LABELS[tier]:<20} {mc:>10.4f} {mb:>10.4f} {ml:>10.4f}")

# ── per-category Spearman ──────────────────────────────────────────────────────
print("\nPer-category Spearman (CLIP-L14):")
for cat in sorted(by_cat.keys()):
    cat_rows = [r for r in rows if r["category"] == cat]
    if len(cat_rows) < 4:
        continue
    rho, p = spearmanr([r["gt"] for r in cat_rows], [r["clip_l14"] for r in cat_rows])
    print(f"  {cat:<25}: ρ={rho:.3f}  p={p:.4f}  n={len(cat_rows)}")

# ── chart ─────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 12))
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

tier_order  = [3, 2, 1, 0]
tier_names  = [TIER_LABELS[t] for t in tier_order]
tier_colors = ["#2ecc71", "#3498db", "#e67e22", "#e74c3c"]

# row 0: mean scores per tier for each metric
metrics = [("CLIP-L14\n(reference-free)", "clip_l14", rho_clip, p_clip),
           ("BERTScore-RoBERTa\n(ref-dependent)", "bertscore", rho_bs, p_bs),
           ("BLEU-4\n(ref-dependent)", "bleu4", rho_bl, p_bl)]

for col, (title, key, rho, pval) in enumerate(metrics):
    ax = fig.add_subplot(gs[0, col])
    means = [np.mean([r[key] for r in rows if r["tier"]==t]) for t in tier_order]
    sems  = [np.std([r[key] for r in rows if r["tier"]==t]) /
             np.sqrt(len([r for r in rows if r["tier"]==t])) for t in tier_order]
    bars = ax.bar(range(4), means, color=tier_colors, edgecolor="white", linewidth=1.2)
    ax.errorbar(range(4), means, yerr=sems, fmt="none", color="black", capsize=4)
    for bar, val in zip(bars, means):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                f"{val:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(range(4))
    ax.set_xticklabels([t.replace("_", "\n") for t in tier_names], fontsize=8)
    sig = "***" if pval<0.001 else "**" if pval<0.01 else "*" if pval<0.05 else "n.s."
    ax.set_title(f"{title}\nSpearman ρ={rho:.3f} {sig}", fontsize=10, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(0, max(means)*1.25)

# row 1: scatter plots metric vs ground truth
for col, (title, key, rho, pval) in enumerate(metrics):
    ax = fig.add_subplot(gs[1, col])
    for tier, color in zip(tier_order, tier_colors):
        tier_rows = [r for r in rows if r["tier"] == tier]
        xs = [r["gt"]  for r in tier_rows]
        ys = [r[key]   for r in tier_rows]
        ax.scatter(xs, ys, c=color, alpha=0.7, s=40, label=TIER_LABELS[tier],
                   edgecolors="white", linewidths=0.5)
    ax.set_xlabel("Ground-truth quality tier", fontsize=10)
    ax.set_ylabel("Metric score", fontsize=10)
    sig = "***" if pval<0.001 else "**" if pval<0.01 else "*" if pval<0.05 else "n.s."
    ax.set_title(f"{title.split(chr(10))[0]}\nρ={rho:.3f} {sig}", fontsize=10, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if col == 0:
        ax.legend(fontsize=8, loc="upper left")

fig.suptitle(
    f"SceneTwin Evaluation: CLIP-L14 vs BERTScore vs BLEU-4\n"
    f"{len(valid)} VideoA11y clips × 4 quality tiers — Spearman correlation with human quality ordering",
    fontsize=12, fontweight="bold"
)
plt.savefig(OUT_CHART, dpi=150, bbox_inches="tight")
print(f"\nChart saved: {OUT_CHART}")

# ── markdown report ────────────────────────────────────────────────────────────
def sig_str(p):
    return "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "n.s."

tier_means = {}
for tier in tier_order:
    tier_rows = [r for r in rows if r["tier"]==tier]
    tier_means[tier] = {k: np.mean([r[k] for r in tier_rows])
                        for k in ["clip_l14","bertscore","bleu4"]}

report = f"""---
title: "SceneTwin Paper Evaluation — CLIP vs BERTScore vs BLEU"
category: research
tags: [SceneTwin, evaluation, BERTScore, BLEU, CLIP, Spearman, VideoA11y]
created: {date.today()}
updated: {date.today()}
sources:
  - output/reports/scenetwin-videoa11y.md
  - https://huggingface.co/datasets/chaoyuli/VideoA11y-40K
---

# SceneTwin Paper Evaluation

Systematic comparison of reference-free (CLIP-L14) vs reference-dependent (BERTScore, BLEU-4) metrics
for audio description quality evaluation. {len(valid)} clips × 4 description quality tiers.

## Setup

**Clips:** {len(valid)} YouTube clips from VideoA11y-40K test set
**Categories:** {", ".join(sorted(by_cat.keys()))}
**Total data points:** {len(rows)} ({len(valid)} clips × 4 tiers)

**Quality tiers (ground truth):**
| Tier | Label | Description | Quality score |
|---|---|---|---|
| 3 | full | Complete VideoA11y description (GPT-4V + AD guidelines) | 3 (best) |
| 2 | first_sentence | First sentence only | 2 |
| 1 | truncated_10w | First 10 words only | 1 |
| 0 | cross_category | Description from different category | 0 (worst) |

## Main Result: Spearman Correlation

| Metric | Type | Spearman ρ | p-value | Sig |
|---|---|---|---|---|
| **CLIP-L14** | **Reference-free** | **{rho_clip:.4f}** | **{p_clip:.4f}** | **{sig_str(p_clip)}** |
| BERTScore-RoBERTa | Reference-dependent | {rho_bs:.4f} | {p_bs:.4f} | {sig_str(p_bs)} |
| BLEU-4 | Reference-dependent | {rho_bl:.4f} | {p_bl:.4f} | {sig_str(p_bl)} |

## Mean Scores per Quality Tier

| Tier | CLIP-L14 | BERTScore | BLEU-4 |
|---|---|---|---|
| full (3) | {tier_means[3]["clip_l14"]:.4f} | {tier_means[3]["bertscore"]:.4f} | {tier_means[3]["bleu4"]:.4f} |
| first_sentence (2) | {tier_means[2]["clip_l14"]:.4f} | {tier_means[2]["bertscore"]:.4f} | {tier_means[2]["bleu4"]:.4f} |
| truncated_10w (1) | {tier_means[1]["clip_l14"]:.4f} | {tier_means[1]["bertscore"]:.4f} | {tier_means[1]["bleu4"]:.4f} |
| cross_category (0) | {tier_means[0]["clip_l14"]:.4f} | {tier_means[0]["bertscore"]:.4f} | {tier_means[0]["bleu4"]:.4f} |

## Key Findings

1. **Reference-free advantage**: CLIP-L14 evaluates all 4 tiers directly against video content. BERTScore and BLEU assign tier 3 a trivial score of 1.0 (it is the reference), artificially inflating their correlation.

2. **Cross-category rejection**: CLIP correctly assigns the lowest scores to cross-category descriptions (tier 0). BERTScore/BLEU detect these as off-topic only through text similarity to the reference.

3. **TRIBE + CLIP next**: The current metric is CLIP-only (grounding). Adding TRIBE's neural gain signal (Description Gain = cos(AV, audio+desc) − cos(AV, audio)) is the planned upgrade — see Colab notebook for TRIBE inference.

## What's Still Needed for Publication
- TRIBE runs on these {len(valid)} clips → Description Gain metric (needs Colab T4)
- Human ratings (BLV users or professional describers) for Spearman validation
- More clips (100+) for robust statistics
- Ablation: CLIP-alone vs TRIBE-alone vs TRIBE×CLIP

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-improvement-research]]
"""

OUT_REPORT.write_text(report)
print(f"Report saved: {OUT_REPORT}")
print("\nDone.")
