#!/usr/bin/env python3
"""Build a Colab notebook for a tiny SceneTwin neural-closure pilot.

The pilot tests whether candidate AD text closes the TRIBE cortical gap:

    closure = dist(P_A, P_AV) - dist(P_A+AD, P_AV)

Positive closure means audio + AD moved predicted cortical response closer to
the original audiovisual response than audio alone.

The notebook is intentionally small: default clips are [1, 5] and default tiers
are tier3_va11y vs tier0_cross. It saves every prediction immediately and can
reuse cached P_AV/P_A tensors from the existing timing-stack zip.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_NB = ROOT / "output" / "scenetwin_neural_closure_pilot_colab.ipynb"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


CELLS: list[dict] = []

CELLS.append(md("""# SceneTwin — Neural Closure Pilot

Tiny Colab test for the experimental TRIBE-heavy score:

```text
closure = dist(P_A, P_AV) - dist(P_A+AD, P_AV)
```

Interpretation:

- `P_AV`: TRIBE prediction for original video + audio.
- `P_A`: TRIBE prediction for soundtrack/audio only.
- `P_A+AD`: TRIBE prediction for real soundtrack plus candidate AD text.
- Positive closure: the candidate AD moved the audio-only predicted brain state
  closer to the full audiovisual predicted brain state.

This is **not** the full experiment. Default run is only:

```text
clips = [1, 5]
tiers = ["tier3_va11y", "tier0_cross"]
```

That means only 4 new `P_A+AD` predictions if `P_AV` and `P_A` are already
cached. Edit `CLIP_IDXS` and `TIERS_TO_TEST` if you want to scale.

## Runtime / cache

Use Colab L4. Set `USE_DRIVE=True` if you want the `.npy` cache to survive a
full runtime reset. The notebook saves every prediction immediately.
"""))

CELLS.append(code("""!rm -rf /content/tribev2
!git clone https://github.com/facebookresearch/tribev2.git
!pip install -e tribev2 --quiet
!pip install --quiet \\
    huggingface_hub \\
    pandas scipy matplotlib seaborn \\
    "numpy==2.2.6" \\
    moviepy

!apt-get update -qq && apt-get install -y -qq ffmpeg

# Restart so numpy / torch extensions load cleanly.
import os
os.kill(os.getpid(), 9)
"""))

CELLS.append(md("""## Upload inputs

Upload:

1. `scenetwin_description_gain_bundle.zip`
   Required. Contains `vatex_eval_clips.json` and `vatex_clips/clip_NN.*`.

2. Optional: `scenetwin_timing_20clip_results.zip`
   If you have it, upload it too. The notebook will import cached
   `clip_NN_P_AV.npy` and `clip_NN_P_A.npy` so it only needs to run new
   `P_A+AD` predictions.

If you skip the timing zip, the notebook computes `P_AV` and `P_A` for the
selected clips only.
"""))

CELLS.append(code("""from pathlib import Path
from google.colab import files, drive
import zipfile
import shutil

USE_DRIVE = True

if USE_DRIVE:
    drive.mount('/content/drive')
    OUT_DIR = Path('/content/drive/MyDrive/scenetwin_neural_closure_pilot')
else:
    OUT_DIR = Path('/content/scenetwin_neural_closure_pilot')

ROOT = Path('/content/scenetwin_real_eval')
PRED_DIR = OUT_DIR / 'preds'
TEXT_DIR = OUT_DIR / 'texts'
AUDIO_DIR = OUT_DIR / 'audio'
REPORT_DIR = OUT_DIR / 'reports'
for d in [ROOT, OUT_DIR, PRED_DIR, TEXT_DIR, AUDIO_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print('Upload bundle zip, and optionally timing results zip.')
uploaded = files.upload()

for name in uploaded:
    p = Path(name)
    if not p.suffix.lower() == '.zip':
        continue
    lower = p.name.lower()
    if 'description_gain_bundle' in lower or 'bundle' in lower:
        print('Extracting data bundle:', p)
        with zipfile.ZipFile(p) as zf:
            zf.extractall(ROOT)
    else:
        import_dir = Path('/content/imported_timing')
        import_dir.mkdir(parents=True, exist_ok=True)
        print('Extracting optional timing/cache zip:', p)
        with zipfile.ZipFile(p) as zf:
            zf.extractall(import_dir)
        copied = 0
        for pred in import_dir.rglob('clip_*_P_A*.npy'):
            # This imports P_A and P_AV. It ignores AD-closure tensors unless
            # they happen to match, which is harmless.
            target = PRED_DIR / pred.name
            if not target.exists():
                shutil.copy2(pred, target)
                copied += 1
        for pred in import_dir.rglob('clip_*_P_AV.npy'):
            target = PRED_DIR / pred.name
            if not target.exists():
                shutil.copy2(pred, target)
                copied += 1
        print('Imported cached predictions:', copied)

print('Bundle JSON exists:', (ROOT / 'vatex_eval_clips.json').exists())
print('Cached preds:', len(list(PRED_DIR.glob('*.npy'))))
print('OUT_DIR:', OUT_DIR)

# Normalize ROOT if the uploaded bundle extracted with an extra top-level folder.
json_matches = sorted(Path('/content').rglob('vatex_eval_clips.json'))
if json_matches:
    ROOT = json_matches[0].parent
    print('Using data ROOT:', ROOT)
else:
    raise FileNotFoundError('Could not find vatex_eval_clips.json after upload/extract')
"""))

CELLS.append(md("""## Setup

Edit `CLIP_IDXS` and `TIERS_TO_TEST` here. Keep this tiny until the signal
looks real.
"""))

CELLS.append(code("""import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import kendalltau, spearmanr

try:
    from moviepy.editor import VideoFileClip
except Exception:
    from moviepy import VideoFileClip

from huggingface_hub import login
login()

sys.path.insert(0, '/content/tribev2')
from tribev2 import TribeModel
from tribev2.demo_utils import TextToEvents, get_audio_and_text_events

CLIPS_JSON = ROOT / 'vatex_eval_clips.json'
CLIPS_DIR = ROOT / 'vatex_clips'

if not CLIPS_JSON.exists():
    json_matches = sorted(Path('/content').rglob('vatex_eval_clips.json'))
    if not json_matches:
        raise FileNotFoundError('Could not find vatex_eval_clips.json. Re-run the upload cell with the bundle zip.')
    ROOT = json_matches[0].parent
    CLIPS_JSON = ROOT / 'vatex_eval_clips.json'
    CLIPS_DIR = ROOT / 'vatex_clips'
    print('Recovered data ROOT:', ROOT)

# Tiny default pilot. Add clip IDs only after this shows signal.
CLIP_IDXS = [1, 5]
TIERS_TO_TEST = ['tier3_va11y', 'tier0_cross']

TIER_GT = {
    'tier0_cross': 0,
    'tier1_vatex_short': 1,
    'tier2_vatex_long': 2,
    'tier3_va11y': 3,
}

with CLIPS_JSON.open() as f:
    clips_meta = json.load(f)

def find_clip_path(idx):
    matches = sorted(CLIPS_DIR.glob(f'clip_{idx:02d}.*'))
    if not matches:
        raise FileNotFoundError(f'clip_{idx:02d}.* not found in {CLIPS_DIR}')
    return matches[0]

def extract_audio(video_path, idx):
    audio_path = AUDIO_DIR / f'clip_{idx:02d}.wav'
    if audio_path.exists():
        return audio_path
    clip = VideoFileClip(str(video_path))
    if clip.audio is None:
        clip.close()
        raise ValueError(f'No audio track in {video_path}')
    try:
        clip.audio.write_audiofile(str(audio_path), fps=16000, verbose=False, logger=None)
    except TypeError:
        clip.audio.write_audiofile(str(audio_path), fps=16000, logger=None)
    clip.close()
    return audio_path

def write_text(idx, tier, text):
    path = TEXT_DIR / f'clip_{idx:02d}_{tier}.txt'
    path.write_text(str(text).strip(), encoding='utf-8')
    return path

def audio_only_events(audio_path):
    event = {
        'type': 'Audio',
        'filepath': str(audio_path),
        'start': 0,
        'timeline': 'default',
        'subject': 'default',
    }
    return get_audio_and_text_events(pd.DataFrame([event]), audio_only=True)

def ad_word_events_from_text(model, text):
    # TRIBE's text helper makes TTS audio and then word/text events. For
    # P_A+AD we keep only non-Audio events so the candidate AD contributes text
    # content but not synthetic speech audio.
    events = TextToEvents(
        text=str(text).strip(),
        infra={'folder': model.cache_folder, 'mode': 'retry'},
    ).get_events()
    if 'type' not in events.columns:
        raise RuntimeError('TextToEvents returned no type column')
    text_events = events[events['type'].astype(str) != 'Audio'].copy()
    if text_events.empty:
        raise RuntimeError('No non-audio text/word events created from AD text')
    return text_events

def audio_plus_ad_events(model, audio_path, ad_text):
    a_events = audio_only_events(audio_path)
    t_events = ad_word_events_from_text(model, ad_text)
    # Keep same timeline/subject. Starts come from TTS transcript; for this
    # pilot that means AD begins at clip start. Later versions can schedule AD
    # into high-gap dialogue-free windows.
    all_cols = list(dict.fromkeys([*a_events.columns, *t_events.columns]))
    events = pd.concat(
        [
            a_events.reindex(columns=all_cols),
            t_events.reindex(columns=all_cols),
        ],
        ignore_index=True,
    )
    return events

def predict_cached(model, name, events_fn):
    path = PRED_DIR / f'{name}.npy'
    if path.exists():
        arr = np.load(path)
        print(f'  cache hit: {path.name} {arr.shape}')
        return arr
    print(f'  running TRIBE: {name}')
    events = events_fn()
    preds, _ = model.predict(events)
    np.save(path, preds)
    print(f'  saved: {path.name} {preds.shape}')
    return preds

def flatten_pred(x):
    x = np.asarray(x)
    if x.ndim == 3 and x.shape[1] == 1:
        x = x[:, 0, :]
    elif x.ndim > 2:
        x = x.reshape(x.shape[0], -1)
    return x

def align(a, b, c=None):
    a = flatten_pred(a)
    b = flatten_pred(b)
    if c is None:
        T = min(len(a), len(b))
        return a[:T], b[:T]
    c = flatten_pred(c)
    T = min(len(a), len(b), len(c))
    return a[:T], b[:T], c[:T]

def residual_distance(x, y):
    x, y = align(x, y)
    return np.linalg.norm(x - y, axis=1)

def cosine_distance(x, y):
    x, y = align(x, y)
    num = (x * y).sum(axis=1)
    den = np.linalg.norm(x, axis=1) * np.linalg.norm(y, axis=1)
    return 1 - np.divide(num, den, out=np.zeros_like(num), where=den > 0)

def closure_metrics(p_av, p_a, p_a_ad, top_frac=0.25):
    p_av, p_a, p_a_ad = align(p_av, p_a, p_a_ad)
    base_res = np.linalg.norm(p_a - p_av, axis=1)
    ad_res = np.linalg.norm(p_a_ad - p_av, axis=1)
    res_closure = base_res - ad_res

    base_cos = cosine_distance(p_a, p_av)
    ad_cos = cosine_distance(p_a_ad, p_av)
    cos_closure = base_cos - ad_cos

    k = max(1, int(np.ceil(len(base_res) * top_frac)))
    top_idx = np.argsort(base_res)[-k:]
    return {
        'n_trs': len(base_res),
        'base_residual_dist_mean': float(base_res.mean()),
        'ad_residual_dist_mean': float(ad_res.mean()),
        'closure_residual_mean': float(res_closure.mean()),
        'closure_residual_top_gap_mean': float(res_closure[top_idx].mean()),
        'base_cosine_dist_mean': float(base_cos.mean()),
        'ad_cosine_dist_mean': float(ad_cos.mean()),
        'closure_cosine_mean': float(cos_closure.mean()),
        'closure_cosine_top_gap_mean': float(cos_closure[top_idx].mean()),
    }

print('Loading TRIBE v2...')
model = TribeModel.from_pretrained('facebook/tribev2', cache_folder=str(OUT_DIR / 'tribe_cache'))
print('Model loaded.')
print('Pilot clips:', CLIP_IDXS)
print('Pilot tiers:', TIERS_TO_TEST)
"""))

CELLS.append(md("""## Run neural-closure pilot

This is the main cell. If `P_AV` and `P_A` are cached, it only runs the new
`P_A+AD` predictions. Every tensor is saved before moving to the next tier.
"""))

CELLS.append(code("""rows = []

for idx in CLIP_IDXS:
    meta = clips_meta[idx]
    video_path = find_clip_path(idx)
    audio_path = extract_audio(video_path, idx)

    print(f'\\n=== clip_{idx:02d}: {meta.get("video_id", "unknown")} ===')

    p_av = predict_cached(
        model,
        f'clip_{idx:02d}_P_AV',
        lambda video_path=video_path: model.get_events_dataframe(video_path=str(video_path)),
    )

    try:
        p_a = predict_cached(
            model,
            f'clip_{idx:02d}_P_A',
            lambda audio_path=audio_path: model.get_events_dataframe(audio_path=str(audio_path)),
        )
    except RuntimeError as exc:
        if 'Ratio of unmatched words' not in str(exc):
            raise
        print('  transcript alignment failed; retrying P_A as audio-only')
        p_a = predict_cached(
            model,
            f'clip_{idx:02d}_P_A_audio_only',
            lambda audio_path=audio_path: audio_only_events(audio_path),
        )
        # Also save under canonical name so later reruns find it.
        np.save(PRED_DIR / f'clip_{idx:02d}_P_A.npy', p_a)

    for tier in TIERS_TO_TEST:
        ad_text = meta[tier]
        write_text(idx, tier, ad_text)
        p_a_ad = predict_cached(
            model,
            f'clip_{idx:02d}_{tier}_P_A_AD',
            lambda audio_path=audio_path, ad_text=ad_text: audio_plus_ad_events(model, audio_path, ad_text),
        )
        metrics = closure_metrics(p_av, p_a, p_a_ad)
        row = {
            'clip_idx': idx,
            'video_id': meta.get('video_id', ''),
            'category': meta.get('category', ''),
            'tier': tier,
            'gt': TIER_GT[tier],
            'desc_words': len(str(ad_text).split()),
            **metrics,
        }
        rows.append(row)
        pd.DataFrame(rows).to_csv(OUT_DIR / 'neural_closure_partial.csv', index=False)
        print(
            f\"  {tier}: closure_res={row['closure_residual_mean']:.4f}  \"
            f\"top_gap={row['closure_residual_top_gap_mean']:.4f}  \"
            f\"closure_cos={row['closure_cosine_mean']:.4f}\"
        )

df = pd.DataFrame(rows)
df.to_csv(OUT_DIR / 'neural_closure_results.csv', index=False)
df
"""))

CELLS.append(md("""## Interpret the pilot

For this metric, higher is better. The basic smoke test is:

```text
tier3_va11y closure > tier0_cross closure
```

Do not scale to all tiers/clips unless this tiny comparison looks sane.
"""))

CELLS.append(code("""df = pd.read_csv(OUT_DIR / 'neural_closure_results.csv')
display(df)

metric_cols = [
    'closure_residual_mean',
    'closure_residual_top_gap_mean',
    'closure_cosine_mean',
    'closure_cosine_top_gap_mean',
]

print('\\nTier means:')
display(df.groupby('tier')[metric_cols].mean().sort_values('closure_residual_mean', ascending=False))

print('\\nPairwise tier3 > tier0 by clip:')
pair_rows = []
for clip_idx, group in df.groupby('clip_idx'):
    vals = dict(zip(group['tier'], group['closure_residual_mean']))
    if 'tier3_va11y' in vals and 'tier0_cross' in vals:
        pair_rows.append({
            'clip_idx': clip_idx,
            'tier3_closure': vals['tier3_va11y'],
            'tier0_closure': vals['tier0_cross'],
            'tier3_gt_tier0': vals['tier3_va11y'] > vals['tier0_cross'],
            'margin': vals['tier3_va11y'] - vals['tier0_cross'],
        })
pair_df = pd.DataFrame(pair_rows)
display(pair_df)
pair_df.to_csv(OUT_DIR / 'neural_closure_pairwise.csv', index=False)

if len(df['gt'].unique()) > 1 and len(df) >= 4:
    for metric in metric_cols:
        rho, p = spearmanr(df['gt'], df[metric], nan_policy='omit')
        tau, tp = kendalltau(df['gt'], df[metric], nan_policy='omit')
        print(f'{metric}: rho={rho:.3f} p={p:.4g}; tau={tau:.3f} p={tp:.4g}')

ax = df.pivot(index='clip_idx', columns='tier', values='closure_residual_mean').plot(
    kind='bar',
    figsize=(8, 4),
    title='Neural closure pilot: residual-distance closure',
)
ax.axhline(0, color='black', linewidth=1)
ax.set_ylabel('positive = closer to P_AV than audio alone')
plt.tight_layout()
plt.savefig(REPORT_DIR / 'neural_closure_pilot.png', dpi=160)
plt.show()
"""))

CELLS.append(md("""## Export results

This creates a small zip you can download. If `USE_DRIVE=True`, the same files
are already in your Drive folder.
"""))

CELLS.append(code("""import zipfile
from google.colab import files

zip_path = Path('/content/scenetwin_neural_closure_pilot_results.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for p in [
        OUT_DIR / 'neural_closure_results.csv',
        OUT_DIR / 'neural_closure_partial.csv',
        OUT_DIR / 'neural_closure_pairwise.csv',
        REPORT_DIR / 'neural_closure_pilot.png',
    ]:
        if p.exists():
            zf.write(p, arcname=p.name)
    for p in sorted(PRED_DIR.glob('clip_*_P_A_AD.npy')):
        zf.write(p, arcname=f'preds/{p.name}')

print('Wrote', zip_path)
files.download(str(zip_path))
"""))


def main() -> None:
    nb = {
        "cells": CELLS,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"provenance": []},
            "kernelspec": {
                "display_name": "Python 3",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_NB}")


if __name__ == "__main__":
    main()
