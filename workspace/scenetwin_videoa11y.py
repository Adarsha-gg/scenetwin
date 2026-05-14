"""
SceneTwin — Real VideoA11y Description Test
Uses descriptions from chaoyuli/VideoA11y-40K (GPT-4V generated, AD guidelines, independently written).
Tests whether CLIP-L14 grounding can match real audio descriptions to their source clips.
"""

import numpy as np
from pathlib import Path
from PIL import Image
import torch
import open_clip
import matplotlib.pyplot as plt
from datasets import load_dataset
from datetime import date

FRAMES_ROOT = Path("/Users/adarsha/njbda/frames")
OUT_CHART   = Path("/Users/adarsha/njbda/scenetwin_videoa11y.png")
OUT_REPORT  = Path("/Users/adarsha/Knowledge/output/reports/scenetwin-videoa11y.md")

# VideoA11y video IDs for our 4 clips
VIDEO_IDS = {
    "waterfall": "4ztYgv_AzmY_70.000_80.000",
    "skate":     "lGf_L6i6AZI_20.000_30.000",
    "bread":     "N-aqYNfr6VA_90.000_100.000",
    "dance":     "_VDyZ1DwgQE_100.000_110.000",
}
CLIP_NAMES = list(VIDEO_IDS.keys())
N = len(CLIP_NAMES)

LABELS = {
    "waterfall": "Waterfall\n(rocky stream)",
    "skate":     "Skateboard\n(street trick)",
    "bread":     "Bread\n(food closeup)",
    "dance":     "Dance\n(game animation)",
}

# ── pull descriptions from VideoA11y ──────────────────────────────────────────
print("Loading VideoA11y-40K descriptions...")
ds = load_dataset("chaoyuli/VideoA11y-40K", split="test")
id_to_desc = {row["Video_ID"]: row["Desc"] for row in ds}

descriptions = {}
print("\nVideoA11y descriptions (real, GPT-4V generated, independently written):\n")
for clip_name, vid_id in VIDEO_IDS.items():
    desc = id_to_desc.get(vid_id)
    if desc is None:
        # try train split
        ds_train = load_dataset("chaoyuli/VideoA11y-40K", split="train")
        id_to_desc_train = {row["Video_ID"]: row["Desc"] for row in ds_train}
        desc = id_to_desc_train.get(vid_id, "[NOT FOUND]")
    descriptions[clip_name] = desc
    print(f"[{clip_name}] {desc}\n")

# ── load CLIP ViT-L-14 ────────────────────────────────────────────────────────
print("Loading CLIP ViT-L-14...")
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-L-14", pretrained="laion2b_s32b_b82k"
)
tokenizer = open_clip.get_tokenizer("ViT-L-14")
model.eval()

def encode_frames(frame_dir):
    paths = sorted(Path(frame_dir).glob("frame_*.jpg"))
    imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in paths])
    with torch.no_grad():
        feats = model.encode_image(imgs)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats

def encode_text(text):
    tokens = tokenizer([text])
    with torch.no_grad():
        feat = model.encode_text(tokens)
        feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat

def top3_sim(frame_feats, text_feat):
    sims = (frame_feats @ text_feat.T).squeeze().numpy()
    return float(np.sort(sims)[-3:].mean())

# ── encode clips ──────────────────────────────────────────────────────────────
print("Encoding frames...")
clip_feats = {}
for name in CLIP_NAMES:
    clip_feats[name] = encode_frames(FRAMES_ROOT / name)
    print(f"  {name}: {clip_feats[name].shape[0]} frames")

# ── build 4×4 contrastive matrix ──────────────────────────────────────────────
print("\nBuilding contrastive matrix...")
matrix = np.zeros((N, N))
for i, clip_name in enumerate(CLIP_NAMES):
    for j, desc_name in enumerate(CLIP_NAMES):
        text_feat = encode_text(descriptions[desc_name])
        matrix[i, j] = top3_sim(clip_feats[clip_name], text_feat)

# ── retrieval accuracy ─────────────────────────────────────────────────────────
correct = sum(1 for i in range(N) if np.argmax(matrix[i]) == i)
print(f"\nRetrieval accuracy: {correct}/{N}")

# ── print matrix ───────────────────────────────────────────────────────────────
clip_labels_short = [LABELS[n].replace("\n", " / ") for n in CLIP_NAMES]
print(f"\n{'':30s}" + "".join(f"{l:>22s}" for l in clip_labels_short))
for i, cname in enumerate(CLIP_NAMES):
    row = f"{clip_labels_short[i]:30s}"
    for j in range(N):
        marker = " *" if i == j else "  "
        row += f"{matrix[i,j]:>20.4f}{marker}"
    print(row)

# ── chart ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
labels_short = [LABELS[n].replace("\n", "\n") for n in CLIP_NAMES]

# heatmap
ax = axes[0]
im = ax.imshow(matrix, cmap="YlOrRd", vmin=matrix.min()*0.95, vmax=matrix.max()*1.02)
ax.set_xticks(range(N))
ax.set_yticks(range(N))
ax.set_xticklabels(labels_short, fontsize=9)
ax.set_yticklabels(labels_short, fontsize=9)
ax.set_xlabel("Description source", fontsize=10)
ax.set_ylabel("Video clip", fontsize=10)
ax.set_title(f"Contrastive matrix — real VideoA11y descriptions\nRetrieval: {correct}/{N}", fontsize=11, fontweight="bold")
for i in range(N):
    for j in range(N):
        color = "white" if matrix[i,j] > matrix.max()*0.85 else "black"
        weight = "bold" if i == j else "normal"
        ax.text(j, i, f"{matrix[i,j]:.3f}", ha="center", va="center",
                fontsize=10, color=color, fontweight=weight)
    ax.add_patch(plt.Rectangle((i-0.5, i-0.5), 1, 1,
                                fill=False, edgecolor="lime", linewidth=2.5))
plt.colorbar(im, ax=ax, shrink=0.8)

# bar chart — each clip's correct vs best wrong score
ax2 = axes[1]
correct_scores = [matrix[i, i] for i in range(N)]
best_wrong = [max(matrix[i, j] for j in range(N) if j != i) for i in range(N)]
x = np.arange(N)
w = 0.35
b1 = ax2.bar(x - w/2, correct_scores, w, label="Correct description", color="#2ecc71", edgecolor="white")
b2 = ax2.bar(x + w/2, best_wrong, w, label="Best wrong description", color="#e74c3c", alpha=0.8, edgecolor="white")
ax2.set_xticks(x)
ax2.set_xticklabels(labels_short, fontsize=9)
ax2.set_ylabel("CLIP-L14 top-3 similarity", fontsize=10)
ax2.set_title("Correct vs best-wrong score per clip\n(green should be taller)", fontsize=11, fontweight="bold")
ax2.legend()
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
for bar, val in zip(list(b1) + list(b2), correct_scores + best_wrong):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
             f"{val:.3f}", ha="center", fontsize=9, fontweight="bold")

fig.suptitle("SceneTwin — Real VideoA11y Descriptions (GPT-4V, AD guidelines, n=4 clips)",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(OUT_CHART, dpi=150, bbox_inches="tight")
print(f"\nChart saved: {OUT_CHART}")

# ── markdown report ────────────────────────────────────────────────────────────
margin = [matrix[i,i] - max(matrix[i,j] for j in range(N) if j!=i) for i in range(N)]
report = f"""---
title: "SceneTwin Real VideoA11y Description Test"
category: research
tags: [SceneTwin, CLIP, VideoA11y, real-descriptions, contrastive]
created: {date.today()}
updated: {date.today()}
sources:
  - output/reports/scenetwin-multiclip.md
  - https://huggingface.co/datasets/chaoyuli/VideoA11y-40K
---

# SceneTwin — Real VideoA11y Description Test

Tests CLIP-L14 grounding with **real, independently-generated** audio descriptions from
VideoA11y-40K (GPT-4V generated following proper AD guidelines, zero knowledge of the grounding metric).

This is the legitimate test. Prior multi-clip results used descriptions I wrote after looking at the frames — circular.

## Clips and Real Descriptions

""" + "\n\n".join(
    f"**{LABELS[n].replace(chr(10), ' ')}** (`{VIDEO_IDS[n]}`)\n> {descriptions[n]}"
    for n in CLIP_NAMES
) + f"""

## Contrastive Matrix (CLIP-L14, top-3 frame similarity)

| Clip \\ Description | """ + " | ".join(LABELS[n].replace("\n", " ") for n in CLIP_NAMES) + " |\n" + \
"|---|" + "---|"*N + "\n" + \
"\n".join(
    "| " + LABELS[CLIP_NAMES[i]].replace("\n", " ") + " | " +
    " | ".join(
        f"**{matrix[i,j]:.4f}**" if i==j else f"{matrix[i,j]:.4f}"
        for j in range(N)
    ) + " |"
    for i in range(N)
) + f"""

## Retrieval Accuracy: {correct}/{N}

### Margin (correct score − best wrong score)
""" + "\n".join(
    f"- {LABELS[CLIP_NAMES[i]].replace(chr(10), ' ')}: {margin[i]:+.4f} ({'✓' if margin[i]>0 else '✗'})"
    for i in range(N)
) + """

## Interpretation

A positive margin means the correct description scored higher than any wrong description.
A negative margin means the metric failed — a wrong description was more similar to the clip.

This is the honest baseline: real descriptions, real errors possible, no circular self-evaluation.

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-improvement-research]]
"""

OUT_REPORT.write_text(report)
print(f"Report saved: {OUT_REPORT}")
print("\nDone.")
