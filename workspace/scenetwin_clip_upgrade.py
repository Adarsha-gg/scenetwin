"""
SceneTwin CLIP upgrade test.
Compares ViT-B-32 (current) vs ViT-L-14 (upgrade) for grounding,
then combines with existing TRIBE tensors to show final score differences.
"""

import numpy as np
from pathlib import Path
from PIL import Image
import torch
import open_clip

# ── paths ──────────────────────────────────────────────────────────────────────
PREDS_DIR = Path("/Users/adarsha/Knowledge/output/scenetwin_preds")
VIDEO_PREDS = Path("/Users/adarsha/Downloads/video_preds.npy")
FRAMES_DIR = Path("/Users/adarsha/njbda/sintel_frames")

descriptions = {
    "accurate_concise": (
        "A young woman with short hair stands in a snowy landscape. "
        "She looks determined and sorrowful. Snow falls around her. "
        "The scene is quiet and cold. She begins walking forward through the snow."
    ),
    "accurate_detailed": (
        "A young woman with short dark hair stands alone in a vast, "
        "snow-covered landscape under a grey sky. Her expression is a mix of "
        "determination and deep sadness. Large snowflakes drift slowly around her. "
        "She wears layered clothing suitable for harsh winter conditions. "
        "The terrain is flat and featureless, stretching to the horizon. "
        "She takes a breath, then begins walking steadily forward through "
        "the deep snow, leaving footprints behind her."
    ),
    "bad_vague": (
        "Something happens on screen. A person is there. "
        "The weather looks cold maybe. They move."
    ),
    "hallucinated": (
        "A man in a red suit stands on a tropical beach. "
        "Palm trees sway in warm wind. He is laughing and holding a drink. "
        "Children play in the ocean behind him. The sun is bright and hot."
    ),
}

# ── load TRIBE tensors ──────────────────────────────────────────────────────────
print("Loading TRIBE tensors...")
video_preds = np.load(VIDEO_PREDS)  # (30, 20484)
desc_preds = {
    name: np.load(PREDS_DIR / f"desc_{name}_preds.npy")
    for name in descriptions
}

video_avg = video_preds.mean(axis=0)
desc_avgs = {name: arr.mean(axis=0) for name, arr in desc_preds.items()}

def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

tribe_scores = {name: cosine(video_avg, desc_avgs[name]) for name in descriptions}

# ── load frames ────────────────────────────────────────────────────────────────
frame_paths = sorted(FRAMES_DIR.glob("frame_*.jpg"))
print(f"Found {len(frame_paths)} frames")

# ── CLIP grounding: run for a given model/preprocess ───────────────────────────
def run_clip_grounding(model, preprocess, tokenizer, top_k=3):
    device = "cpu"
    model.eval()

    # encode frames
    frame_imgs = [preprocess(Image.open(p).convert("RGB")) for p in frame_paths]
    frame_tensor = torch.stack(frame_imgs).to(device)

    with torch.no_grad():
        frame_feats = model.encode_image(frame_tensor)
        frame_feats = frame_feats / frame_feats.norm(dim=-1, keepdim=True)

    results = {}
    for name, text in descriptions.items():
        tokens = tokenizer([text]).to(device)
        with torch.no_grad():
            text_feat = model.encode_text(tokens)
            text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)

        sims = (frame_feats @ text_feat.T).squeeze().cpu().numpy()
        top_k_score = float(np.sort(sims)[-top_k:].mean())
        results[name] = top_k_score

    return results

# ── run ViT-B-32 (current baseline) ───────────────────────────────────────────
print("\nRunning CLIP ViT-B-32 (current)...")
model_b32, _, preprocess_b32 = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="laion2b_s34b_b79k"
)
tokenizer_b32 = open_clip.get_tokenizer("ViT-B-32")
clip_b32 = run_clip_grounding(model_b32, preprocess_b32, tokenizer_b32)
del model_b32

# ── run ViT-L-14 (upgrade) ────────────────────────────────────────────────────
print("Running CLIP ViT-L-14 (upgrade)...")
model_l14, _, preprocess_l14 = open_clip.create_model_and_transforms(
    "ViT-L-14", pretrained="laion2b_s32b_b82k"
)
tokenizer_l14 = open_clip.get_tokenizer("ViT-L-14")
clip_l14 = run_clip_grounding(model_l14, preprocess_l14, tokenizer_l14)
del model_l14

# ── combine: TRIBE × CLIP (normalized product) ────────────────────────────────
def combine(tribe, clip_scores):
    t_vals = np.array([tribe[n] for n in descriptions])
    c_vals = np.array([clip_scores[n] for n in descriptions])
    t_norm = (t_vals - t_vals.min()) / (t_vals.max() - t_vals.min() + 1e-8)
    c_norm = (c_vals - c_vals.min()) / (c_vals.max() - c_vals.min() + 1e-8)
    return {name: float(t_norm[i] * c_norm[i]) for i, name in enumerate(descriptions)}

final_b32 = combine(tribe_scores, clip_b32)
final_l14 = combine(tribe_scores, clip_l14)

# ── print results ──────────────────────────────────────────────────────────────
col = 22
print(f"\n{'Description':{col}}  TRIBE    CLIP-B32  CLIP-L14  FINAL-B32  FINAL-L14")
print("─" * 80)
for name in descriptions:
    print(
        f"{name:{col}}  "
        f"{tribe_scores[name]:.4f}   "
        f"{clip_b32[name]:.4f}    "
        f"{clip_l14[name]:.4f}    "
        f"{final_b32[name]:.4f}     "
        f"{final_l14[name]:.4f}"
    )

# ── rank check ─────────────────────────────────────────────────────────────────
print("\nRanking (best → worst):")
for label, scores in [("TRIBE alone", tribe_scores), ("TRIBE×CLIP-B32", final_b32), ("TRIBE×CLIP-L14", final_l14)]:
    ranked = sorted(scores, key=scores.get, reverse=True)
    print(f"  {label:18s}: {' > '.join(ranked)}")

# ── bar chart ──────────────────────────────────────────────────────────────────
import matplotlib.pyplot as plt

names = list(descriptions.keys())
x = np.arange(len(names))
width = 0.25
colors_b32 = ["#3498db"] * 4
colors_l14 = ["#e74c3c"] * 4

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, scores, title, color in [
    (axes[0], final_b32, "TRIBE × CLIP ViT-B-32 (current)", "#3498db"),
    (axes[1], final_l14, "TRIBE × CLIP ViT-L-14 (upgrade)", "#e74c3c"),
]:
    vals = [scores[n] for n in names]
    bars = ax.bar(names, vals, color=color, alpha=0.85, edgecolor="white")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle("SceneTwin: ViT-B-32 vs ViT-L-14 Grounding Comparison", fontsize=13)
plt.tight_layout()
out = Path("/Users/adarsha/njbda/scenetwin_clip_upgrade.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nChart saved: {out}")
