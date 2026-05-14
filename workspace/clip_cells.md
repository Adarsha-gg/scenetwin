# Cell 1: CLIP Grounding Score

```python
# CLIP grounding score for SceneTwin
!pip install -q open-clip-torch

import open_clip
import torch
import cv2
import numpy as np
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", device)

clip_model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="laion2b_s34b_b79k", device=device,
)
tokenizer = open_clip.get_tokenizer("ViT-B-32")
clip_model.eval()

cap = cv2.VideoCapture("/content/scene.mp4")
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print("Total frames:", total)

n_frames = 12
frame_idxs = np.linspace(0, max(total - 1, 0), n_frames).astype(int)

frames = []
for idx in frame_idxs:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame))
cap.release()
print("Sampled frames:", len(frames))

descriptions = {
    "accurate_concise": "A young woman with short hair stands in a snowy landscape. She looks determined and sorrowful. Snow falls around her. The scene is quiet and cold. She begins walking forward through the snow.",
    "accurate_detailed": "A young woman with short dark hair stands alone in a vast, snow-covered landscape under a grey sky. Her expression is a mix of determination and deep sadness. Large snowflakes drift slowly around her. She wears layered clothing suitable for harsh winter conditions. The terrain is flat and featureless, stretching to the horizon. She takes a breath, then begins walking steadily forward through the deep snow, leaving footprints behind her.",
    "bad_vague": "Something happens on screen. A person is there. The weather looks cold maybe. They move.",
    "hallucinated": "A man in a red suit stands on a tropical beach. Palm trees sway in warm wind. He is laughing and holding a drink. Children play in the ocean behind him. The sun is bright and hot.",
}

with torch.no_grad():
    image_batch = torch.stack([preprocess(frame) for frame in frames]).to(device)
    image_features = clip_model.encode_image(image_batch)
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

clip_scores = {}
print("\nCLIP Grounding Scores")
print("=" * 60)

for name, desc in descriptions.items():
    text_prompt = f"a video frame showing {desc}"
    text_tokens = tokenizer([text_prompt]).to(device)
    with torch.no_grad():
        text_features = clip_model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        sims = (image_features @ text_features.T).squeeze().detach().cpu().numpy()
    top_k = min(3, len(sims))
    topk_mean = float(np.mean(np.sort(sims)[-top_k:]))
    mean_score = float(np.mean(sims))
    max_score = float(np.max(sims))
    clip_scores[name] = topk_mean
    print(f"{name:22s} CLIP_top3: {topk_mean:.4f}  mean: {mean_score:.4f}  max: {max_score:.4f}")
```

# Cell 2: Combined SceneTwin Score

```python
# Combine TRIBE + CLIP into final SceneTwin score
try:
    tribe_scores = scores
except NameError:
    tribe_scores = {
        "accurate_concise": 0.7446,
        "accurate_detailed": 0.7602,
        "bad_vague": 0.3850,
        "hallucinated": 0.7908,
    }

def minmax(d):
    vals = np.array(list(d.values()), dtype=float)
    lo, hi = vals.min(), vals.max()
    if abs(hi - lo) < 1e-9:
        return {k: 0.5 for k in d}
    return {k: (v - lo) / (hi - lo) for k, v in d.items()}

tribe_norm = minmax(tribe_scores)
clip_norm = minmax(clip_scores)

final_scores = {
    name: tribe_norm[name] * clip_norm[name]
    for name in descriptions
}

print("\nCorrected SceneTwin Scores")
print("=" * 80)
print(f"{'description':22s} {'TRIBE':>8s} {'CLIP':>8s} {'TRIBE_n':>8s} {'CLIP_n':>8s} {'FINAL':>8s}")

for name in sorted(final_scores, key=final_scores.get, reverse=True):
    print(
        f"{name:22s} "
        f"{tribe_scores[name]:8.4f} "
        f"{clip_scores[name]:8.4f} "
        f"{tribe_norm[name]:8.4f} "
        f"{clip_norm[name]:8.4f} "
        f"{final_scores[name]:8.4f}"
    )
```
