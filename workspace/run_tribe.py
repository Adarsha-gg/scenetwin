import sys
sys.path.insert(0, '/Users/adarsha/njbda/tribev2')

import numpy as np
import matplotlib.pyplot as plt

from tribev2 import TribeModel

VIDEO_PATH = '/Users/adarsha/Downloads/stim.mp4'
OUT_DIR = '/Users/adarsha/njbda'

print("Loading TRIBE v2...")
model = TribeModel.from_pretrained(
    'facebook/tribev2',
    config_update={
        "data.text_feature.device": "cpu",
        "data.audio_feature.device": "cpu",
        "data.video_feature.image.device": "cpu",
    }
)
print("Model loaded.")

print("Building events dataframe from video...")
events = model.get_events_dataframe(video_path=VIDEO_PATH)
print(f"Events: {len(events)} rows")

print("Running inference...")
preds, segments = model.predict(events)
print(f"Predictions shape: {preds.shape}")  # (T, 20484)

np.save(f'{OUT_DIR}/predictions.npy', preds)
print(f"Saved predictions to {OUT_DIR}/predictions.npy")

# Average activation over time
avg = preds.mean(axis=0)

# Left hemisphere (vertices 0-10241), Right hemisphere (10242-20483)
lh = avg[:10242]
rh = avg[10242:]

print(f"\nLeft hemisphere  — mean: {lh.mean():.4f}, max: {lh.max():.4f}")
print(f"Right hemisphere — mean: {rh.mean():.4f}, max: {rh.max():.4f}")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(lh, bins=100, color='steelblue', edgecolor='none')
axes[0].set_title('Left Hemisphere Activation')
axes[0].set_xlabel('Predicted fMRI signal')
axes[1].hist(rh, bins=100, color='tomato', edgecolor='none')
axes[1].set_title('Right Hemisphere Activation')
axes[1].set_xlabel('Predicted fMRI signal')
fig.suptitle(f'TRIBE v2 — Brain Activation: stim.mp4\n({preds.shape[0]} time points)')
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/activation_histogram.png', dpi=150)
print(f"Saved plot to {OUT_DIR}/activation_histogram.png")
