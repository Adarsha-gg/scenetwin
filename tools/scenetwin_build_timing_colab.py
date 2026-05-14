#!/usr/bin/env python3
"""Build the SceneTwin 20-clip timing-stack Colab notebook.

Runs the surviving pipeline only:
  TRIBE accessibility-gap need curve  (P_AV, P_A per clip; no P_D)
  Need-weighted CLIP-L14 grounding    (per-window, per-tier)
  OCR coverage                        (per-window)
  Aggregates + permutation null       (across 20 clips)

Input data comes from the existing bundle the user already has:
  /Users/adarsha/Knowledge/output/scenetwin_description_gain_bundle.zip
which contains:
  vatex_eval_clips.json   (per-clip metadata + 4 AD tiers per clip)
  vatex_clips/clip_NN.mp4

Output:
  output/scenetwin_timing_20clip_colab.ipynb
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_NB = ROOT / "output" / "scenetwin_timing_20clip_colab.ipynb"


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

CELLS.append(md("""# SceneTwin — 20-Clip Timing Stack

This notebook scales the **surviving** SceneTwin pipeline to all 20
VideoA11y/VATEX overlap clips. It does NOT run anything on the dead branches
(Description Gain, MVRR, ROI typing, trajectory metrics, closed-loop AD).

What it computes per clip:

```text
P_AV = TRIBE(audiovisual)
P_A  = TRIBE(audio-only)

AccessibilityGap(t) = distance(P_AV[t], P_A[t])

windows_3s   = aggregate to 3s (TRIBE-honest resolution)
ad_need      = combine gap with speech density per window

per_window:
  CLIP-L14 grounding (need-weighted) for each of 4 description tiers
  OCR coverage of visible on-screen text
```

What it reports across 20 clips:

- Spearman rho / Kendall tau on tier ranking
- tier3-vs-control pairwise wins
- full-order-correct clip count
- permutation null p-values

## Runtime

Use a Colab L4 GPU runtime. Expect ~60–90 minutes for the TRIBE pass over 20
clips and a few extra minutes for CLIP + OCR. Everything is checkpointed
per-clip so a disconnect lets you resume.
"""))

CELLS.append(code("""!rm -rf /content/tribev2
!git clone https://github.com/facebookresearch/tribev2.git
!pip install -e tribev2 --quiet
!pip install --quiet \\
    huggingface_hub \\
    pandas scipy matplotlib seaborn \\
    "numpy==2.2.6" \\
    opencv-python-headless \\
    open_clip_torch \\
    pytesseract \\
    pillow

!apt-get update -qq && apt-get install -y -qq tesseract-ocr ffmpeg

# Restart so numpy / torch extensions load cleanly.
import os
os.kill(os.getpid(), 9)
"""))

CELLS.append(md("""## Upload Data Bundle

Locally:
```bash
cd /Users/adarsha/Knowledge/output
ls scenetwin_description_gain_bundle.zip
```

Upload that zip in the next cell. Layout after extract:
```text
/content/scenetwin_real_eval/vatex_eval_clips.json
/content/scenetwin_real_eval/vatex_clips/clip_00.mp4
... clip_19.mp4
```
"""))

CELLS.append(code("""from pathlib import Path
from google.colab import files
import zipfile

ROOT = Path('/content/scenetwin_real_eval')
ROOT.mkdir(parents=True, exist_ok=True)

if not (ROOT / 'vatex_eval_clips.json').exists():
    print('Upload scenetwin_description_gain_bundle.zip')
    uploaded = files.upload()
    zip_name = next(iter(uploaded.keys()))
    with zipfile.ZipFile(zip_name) as zf:
        zf.extractall(ROOT)

print('Files under ROOT:')
for p in sorted(ROOT.iterdir()):
    print(' ', p)
"""))

CELLS.append(md("""## Imports, Paths, Helpers, Model Load
"""))

CELLS.append(code("""import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau
import matplotlib.pyplot as plt

try:
    from moviepy.editor import VideoFileClip
except Exception:
    from moviepy import VideoFileClip

from huggingface_hub import login
login()

sys.path.insert(0, '/content/tribev2')
from tribev2 import TribeModel
from tribev2.demo_utils import get_audio_and_text_events

ROOT = Path('/content/scenetwin_real_eval')
CLIPS_JSON = ROOT / 'vatex_eval_clips.json'
CLIPS_DIR = ROOT / 'vatex_clips'
OUT_DIR = Path('/content/scenetwin_timing_20clip')
PRED_DIR = OUT_DIR / 'preds'
AUDIO_DIR = OUT_DIR / 'audio'
NEED_DIR = OUT_DIR / 'need'
FRAME_DIR = OUT_DIR / 'frames'
CLIP_DIR = OUT_DIR / 'clip_scores'
OCR_DIR = OUT_DIR / 'ocr'
for d in [OUT_DIR, PRED_DIR, AUDIO_DIR, NEED_DIR, FRAME_DIR, CLIP_DIR, OCR_DIR]:
    d.mkdir(parents=True, exist_ok=True)

with CLIPS_JSON.open() as f:
    clips_meta = json.load(f)

TIER_KEYS = ['tier3_va11y', 'tier2_vatex_long', 'tier1_vatex_short', 'tier0_cross']
GT = {'tier3_va11y': 3, 'tier2_vatex_long': 2, 'tier1_vatex_short': 1, 'tier0_cross': 0}
WINDOW_S = 3.0
FRAMES_PER_WINDOW = 3

def find_clip_path(idx):
    matches = sorted(CLIPS_DIR.glob(f'clip_{idx:02d}.*'))
    return matches[0] if matches else None

def extract_audio(video_path, idx):
    audio_path = AUDIO_DIR / f'clip_{idx:02d}.wav'
    if audio_path.exists():
        return audio_path
    clip = VideoFileClip(str(video_path))
    if clip.audio is None:
        clip.close()
        return None
    try:
        clip.audio.write_audiofile(str(audio_path), fps=16000, verbose=False, logger=None)
    except TypeError:
        clip.audio.write_audiofile(str(audio_path), fps=16000, logger=None)
    clip.close()
    return audio_path

def predict_cached(model, name, events_fn):
    path = PRED_DIR / f'{name}.npy'
    if path.exists():
        return np.load(path)
    print(f'  TRIBE: {name}')
    events = events_fn()
    preds, _ = model.predict(events)
    np.save(path, preds)
    return preds

def audio_only_events_no_transcript(audio_path):
    # Some clips produce tiny ASR transcripts whose sentence/word alignment fails.
    # For P_A we only need audio features, so retry without text transforms.
    event = {
        'type': 'Audio',
        'filepath': str(audio_path),
        'start': 0,
        'timeline': 'default',
        'subject': 'default',
    }
    return get_audio_and_text_events(pd.DataFrame([event]), audio_only=True)

print(f'Loaded {len(clips_meta)} clip metadata rows.')
valid = [(i, c, find_clip_path(i)) for i, c in enumerate(clips_meta) if find_clip_path(i) is not None]
print(f'Found {len(valid)} local clip files.')

print('Loading TRIBE v2...')
model = TribeModel.from_pretrained('facebook/tribev2', cache_folder='/content/tribe_cache')
print('Model loaded.')
"""))

CELLS.append(md("""## TRIBE Inference: P_AV and P_A per clip

Only audiovisual and audio-only predictions. We do not run TRIBE on
description text (that branch was killed by validation). Each tensor is
checkpointed so disconnects don't waste compute.
"""))

CELLS.append(code("""for idx, meta, video_path in valid:
    print(f'=== clip_{idx:02d}: {meta.get("video_id", "unknown")} ===')

    p_av = predict_cached(
        model,
        f'clip_{idx:02d}_P_AV',
        lambda video_path=video_path: model.get_events_dataframe(video_path=str(video_path)),
    )

    audio_path = extract_audio(video_path, idx)
    if audio_path is None:
        print(f'  no audio track, skipping P_A')
        continue

    try:
        p_a = predict_cached(
            model,
            f'clip_{idx:02d}_P_A',
            lambda audio_path=audio_path: model.get_events_dataframe(audio_path=str(audio_path)),
        )
    except RuntimeError as e:
        if 'Ratio of unmatched words' not in str(e):
            raise
        print('  audio transcript alignment failed; retrying P_A as audio-only without text transforms')
        p_a_path = PRED_DIR / f'clip_{idx:02d}_P_A.npy'
        events = audio_only_events_no_transcript(audio_path)
        p_a, _ = model.predict(events)
        np.save(p_a_path, p_a)
    print(f'  P_AV {p_av.shape}  P_A {p_a.shape}')

print('TRIBE inference complete.')
"""))

CELLS.append(md("""## Accessibility-Gap Need Curves

Per clip, compute `gap(t) = distance(P_AV[t], P_A[t])` and aggregate to 3s
windows. Speech density comes from rough VAD on the audio. The script
matches the layout the local `scenetwin_neural_need_curve.py` and
`scenetwin_coarse_need_windows.py` tools expect, so the existing analysis
runs unchanged on download.
"""))

CELLS.append(code("""import subprocess
import wave

def speech_density_per_tr(audio_path, n_trs, tr_s=1.49):
    \"\"\"Cheap energy-based VAD per TR. Better than nothing for this scale.\"\"\"
    if audio_path is None or not Path(audio_path).exists():
        return np.zeros(n_trs)
    with wave.open(str(audio_path), 'rb') as w:
        sr = w.getframerate()
        frames = w.readframes(w.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    samples_per_tr = int(sr * tr_s)
    out = np.zeros(n_trs)
    for t in range(n_trs):
        seg = samples[t * samples_per_tr : (t + 1) * samples_per_tr]
        if len(seg) == 0:
            continue
        rms = np.sqrt(np.mean(seg ** 2))
        out[t] = float(rms)
    if out.max() > 0:
        out = out / out.max()
    return (out > 0.15).astype(float)

def cosine_per_tr(p_av, p_a):
    # P shape: (T, V) or (T, 1, V) depending on TRIBE; flatten to (T, V).
    if p_av.ndim == 3:
        p_av = p_av.squeeze(1)
        p_a = p_a.squeeze(1)
    T = min(p_av.shape[0], p_a.shape[0])
    out = np.zeros(T)
    for t in range(T):
        a, b = p_av[t], p_a[t]
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        out[t] = 1 - float(np.dot(a, b) / denom) if denom > 0 else 0.0
    return out

def residual_norm_per_tr(p_av, p_a):
    if p_av.ndim == 3:
        p_av = p_av.squeeze(1)
        p_a = p_a.squeeze(1)
    T = min(p_av.shape[0], p_a.shape[0])
    return np.array([np.linalg.norm(p_av[t] - p_a[t]) for t in range(T)])

def normalize(v):
    if v.max() == v.min():
        return np.zeros_like(v)
    return (v - v.min()) / (v.max() - v.min())

need_rows = []
window_rows = []

for idx, meta, video_path in valid:
    p_av_path = PRED_DIR / f'clip_{idx:02d}_P_AV.npy'
    p_a_path = PRED_DIR / f'clip_{idx:02d}_P_A.npy'
    if not (p_av_path.exists() and p_a_path.exists()):
        continue
    p_av = np.load(p_av_path)
    p_a = np.load(p_a_path)

    cos_gap = cosine_per_tr(p_av, p_a)
    res_norm = residual_norm_per_tr(p_av, p_a)
    n_trs = len(cos_gap)

    audio_path = AUDIO_DIR / f'clip_{idx:02d}.wav'
    speech = speech_density_per_tr(audio_path if audio_path.exists() else None, n_trs)

    need = 0.5 * normalize(cos_gap) + 0.5 * normalize(res_norm)
    standard_slot = need * (1 - speech)
    extended_need = need * speech

    tr_s = 1.49
    for t in range(n_trs):
        need_rows.append({
            'clip_idx': idx,
            't': t,
            'start_s': t * tr_s,
            'end_s': (t + 1) * tr_s,
            'cosine_gap': cos_gap[t],
            'residual_norm': res_norm[t],
            'need_score': need[t],
            'speech_density': speech[t],
            'standard_slot_score': standard_slot[t],
            'extended_need_score': extended_need[t],
        })

    # Coarse 3s windows
    win_size = max(1, int(round(WINDOW_S / tr_s)))
    for w0 in range(0, n_trs, win_size):
        w1 = min(w0 + win_size, n_trs)
        if w1 <= w0:
            break
        win_need = float(need[w0:w1].mean())
        win_speech = float(speech[w0:w1].mean())
        if win_need >= 0.4 and win_speech < 0.3:
            rec = 'standard_ad_slot'
        elif win_need >= 0.4 and win_speech >= 0.3:
            rec = 'extended_or_integrated_ad'
        else:
            rec = 'low_ad_need'
        window_rows.append({
            'clip_idx': idx,
            'window_idx': w0 // win_size,
            'start_s': w0 * tr_s,
            'end_s': w1 * tr_s,
            'need_score': win_need,
            'speech_density': win_speech,
            'recommendation': rec,
            'raw_trs': w1 - w0,
        })

need_df = pd.DataFrame(need_rows)
window_df = pd.DataFrame(window_rows)
need_df.to_csv(NEED_DIR / 'neural_description_need_curve.csv', index=False)
window_df.to_csv(NEED_DIR / 'coarse_need_windows.csv', index=False)
print(f'Need curves: {len(need_df)} TR rows, {len(window_df)} 3s windows across {window_df.clip_idx.nunique()} clips')
"""))

CELLS.append(md("""## Frame Extraction at Need-Weighted Positions

For each window, sample 3 frames (early/mid/late) so CLIP and OCR have
something to score. Frames are saved to disk for download.
"""))

CELLS.append(code("""import cv2

def sample_frames(video_path, start_s, end_s, n=FRAMES_PER_WINDOW):
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    times = np.linspace(start_s, max(start_s + 0.05, end_s - 0.05), n)
    frames = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        frames.append((float(t), cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    cap.release()
    return frames

frame_rows = []
for _, row in window_df.iterrows():
    idx = int(row['clip_idx'])
    video_path = find_clip_path(idx)
    if video_path is None:
        continue
    out_clip_dir = FRAME_DIR / f'clip_{idx:02d}' / f'win_{int(row["window_idx"]):02d}'
    out_clip_dir.mkdir(parents=True, exist_ok=True)
    frames = sample_frames(video_path, float(row['start_s']), float(row['end_s']))
    for k, (t, frame) in enumerate(frames):
        path = out_clip_dir / f'f{k:02d}_t{t:.2f}.jpg'
        cv2.imwrite(str(path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        frame_rows.append({
            'clip_idx': idx,
            'window_idx': int(row['window_idx']),
            'start_s': row['start_s'],
            'end_s': row['end_s'],
            'recommendation': row['recommendation'],
            'frame_idx': k,
            'frame_time_s': t,
            'frame_path': str(path),
        })

frame_df = pd.DataFrame(frame_rows)
frame_df.to_csv(NEED_DIR / 'window_frames.csv', index=False)
print(f'Saved {len(frame_df)} validation frames.')
"""))

CELLS.append(md("""## CLIP-L14 Need-Weighted Grounding

For each (clip, window, tier) combination, score the description text
against the window's frames with CLIP-L14, then aggregate per clip with
need weighting.
"""))

CELLS.append(code("""import torch
import open_clip
from PIL import Image

device = 'cuda' if torch.cuda.is_available() else 'cpu'
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms('ViT-L-14', pretrained='openai')
clip_model = clip_model.to(device).eval()
clip_tokenizer = open_clip.get_tokenizer('ViT-L-14')

@torch.no_grad()
def clip_score(image_path, text):
    image = clip_preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0).to(device)
    tokens = clip_tokenizer([text]).to(device)
    img_f = clip_model.encode_image(image)
    txt_f = clip_model.encode_text(tokens)
    img_f = img_f / img_f.norm(dim=-1, keepdim=True)
    txt_f = txt_f / txt_f.norm(dim=-1, keepdim=True)
    return float((img_f @ txt_f.T).item())

clip_rows = []
for (clip_idx, win_idx), group in frame_df.groupby(['clip_idx', 'window_idx']):
    meta = clips_meta[clip_idx]
    win_row = window_df[(window_df.clip_idx == clip_idx) & (window_df.window_idx == win_idx)].iloc[0]
    need_score = float(win_row['need_score'])
    for tier in TIER_KEYS:
        text = meta[tier]
        scores = [clip_score(r['frame_path'], text) for _, r in group.iterrows()]
        if not scores:
            continue
        clip_rows.append({
            'clip_idx': clip_idx,
            'window_idx': win_idx,
            'tier': tier,
            'gt': GT[tier],
            'frame_clip_mean': float(np.mean(scores)),
            'frame_clip_max': float(np.max(scores)),
            'need_score': need_score,
            'recommendation': win_row['recommendation'],
        })

clip_df = pd.DataFrame(clip_rows)
clip_df.to_csv(CLIP_DIR / 'window_clip_scores.csv', index=False)

# Aggregate: clip-level need-weighted score per tier.
agg_rows = []
for (clip_idx, tier), group in clip_df.groupby(['clip_idx', 'tier']):
    weights = group['need_score'].to_numpy()
    if weights.sum() <= 0:
        weights = np.ones_like(weights)
    nw_clip = float(np.average(group['frame_clip_mean'], weights=weights))
    plain_clip = float(group['frame_clip_mean'].mean())
    plain_clip_top3 = float(group['frame_clip_mean'].nlargest(3).mean())
    high_need = group[group['recommendation'] != 'low_ad_need']
    critical_clip = float(np.average(high_need['frame_clip_mean'], weights=high_need['need_score']) if len(high_need) and high_need['need_score'].sum() > 0 else nw_clip)
    agg_rows.append({
        'clip_idx': clip_idx,
        'tier': tier,
        'gt': GT[tier],
        'need_weighted_clip': nw_clip,
        'critical_weighted_clip': critical_clip,
        'clip_mean': plain_clip,
        'clip_top3': plain_clip_top3,
    })
agg_df = pd.DataFrame(agg_rows)
agg_df.to_csv(CLIP_DIR / 'need_weighted_grounding_results.csv', index=False)
print(f'CLIP scoring done over {clip_df.clip_idx.nunique()} clips, {len(clip_df)} (window, tier) rows.')
"""))

CELLS.append(md("""## OCR Coverage on Validation Frames

Tesseract over each validation frame to detect on-screen text. For each
window we then compute weighted phrase coverage per tier (does the
description mention the visible text?).
"""))

CELLS.append(code("""import re
import pytesseract

def ocr_text(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path)).strip()
    except Exception:
        return ''

def tokens(text):
    return [t.lower() for t in re.findall(r'[A-Za-z0-9]+', text or '')]

def phrase_coverage(ocr_words, ad_text):
    if not ocr_words:
        return float('nan')
    ad_tokens = set(tokens(ad_text))
    ocr_set = set(ocr_words)
    if not ocr_set:
        return float('nan')
    return len(ocr_set & ad_tokens) / len(ocr_set)

ocr_rows = []
for (clip_idx, win_idx), group in frame_df.groupby(['clip_idx', 'window_idx']):
    detected = []
    for _, r in group.iterrows():
        text = ocr_text(r['frame_path'])
        detected.extend(tokens(text))
    if not detected:
        continue
    meta = clips_meta[clip_idx]
    win_row = window_df[(window_df.clip_idx == clip_idx) & (window_df.window_idx == win_idx)].iloc[0]
    for tier in TIER_KEYS:
        cov = phrase_coverage(detected, meta[tier])
        if np.isnan(cov):
            continue
        ocr_rows.append({
            'clip_idx': clip_idx,
            'window_idx': win_idx,
            'tier': tier,
            'gt': GT[tier],
            'ocr_phrase_coverage': cov,
            'need_score': float(win_row['need_score']),
            'ocr_token_count': len(set(detected)),
        })

ocr_df = pd.DataFrame(ocr_rows)
ocr_df.to_csv(OCR_DIR / 'window_ocr_coverage.csv', index=False)

if not ocr_df.empty:
    ocr_agg = []
    for (clip_idx, tier), group in ocr_df.groupby(['clip_idx', 'tier']):
        weights = group['need_score'].to_numpy()
        if weights.sum() <= 0:
            weights = np.ones_like(weights)
        ocr_agg.append({
            'clip_idx': clip_idx,
            'tier': tier,
            'gt': GT[tier],
            'weighted_ocr_score': float(np.average(group['ocr_phrase_coverage'], weights=weights)),
            'mean_ocr_score': float(group['ocr_phrase_coverage'].mean()),
        })
    pd.DataFrame(ocr_agg).to_csv(OCR_DIR / 'ocr_coverage_results.csv', index=False)

print(f'OCR-positive windows across {ocr_df.clip_idx.nunique() if not ocr_df.empty else 0} clips, {len(ocr_df)} rows.')
"""))

CELLS.append(md("""## Aggregate Stats and Permutation Null

Spearman / Kendall on tier ranking, tier3-vs-control pairwise wins,
full-order-correct clip count, and a within-clip permutation null over
the 4! shuffles per clip.
"""))

CELLS.append(code("""from itertools import permutations

def evaluate(metric_df, metric_col):
    rho_all, rho_p = spearmanr(metric_df[metric_col], metric_df['gt'])
    tau_all, tau_p = kendalltau(metric_df[metric_col], metric_df['gt'])
    full_order = 0
    pair_wins = pair_total = 0
    for clip_idx, group in metric_df.groupby('clip_idx'):
        ordered = group.sort_values(metric_col, ascending=False).reset_index(drop=True)
        if list(ordered['gt']) == sorted(ordered['gt'], reverse=True):
            full_order += 1
        tier3 = group[group['tier'] == 'tier3_va11y'][metric_col]
        for ctrl in ['tier2_vatex_long', 'tier1_vatex_short', 'tier0_cross']:
            tc = group[group['tier'] == ctrl][metric_col]
            if not tier3.empty and not tc.empty:
                pair_total += 1
                if tier3.iloc[0] > tc.iloc[0]:
                    pair_wins += 1
    return {
        'metric': metric_col,
        'spearman_rho': float(rho_all),
        'spearman_p': float(rho_p),
        'kendall_tau': float(tau_all),
        'kendall_p': float(tau_p),
        'pairwise_wins': pair_wins,
        'pairwise_total': pair_total,
        'full_order_clips': full_order,
        'full_order_total': metric_df['clip_idx'].nunique(),
    }

def permutation_null(metric_df, metric_col, n_iter=5000, seed=0):
    rng = np.random.default_rng(seed)
    observed = evaluate(metric_df, metric_col)
    rho = observed['spearman_rho']
    null_rhos = []
    work = metric_df.copy()
    for _ in range(n_iter):
        for clip_idx, group in work.groupby('clip_idx'):
            shuffled = group[metric_col].sample(frac=1.0, random_state=int(rng.integers(0, 2**31))).to_numpy()
            work.loc[group.index, metric_col] = shuffled
        try:
            r, _ = spearmanr(work[metric_col], work['gt'])
        except Exception:
            r = 0.0
        null_rhos.append(r if r is not None else 0.0)
        work = metric_df.copy()  # reset
    null_rhos = np.array(null_rhos)
    p_ge = float((null_rhos >= rho).mean())
    return {
        'metric': metric_col,
        'observed_rho': rho,
        'null_mean_rho': float(null_rhos.mean()),
        'null_p_ge_observed': p_ge,
        'n_permutations': n_iter,
    }

eval_rows = []
null_rows = []
for col in ['need_weighted_clip', 'critical_weighted_clip', 'clip_mean', 'clip_top3']:
    eval_rows.append(evaluate(agg_df, col))
    null_rows.append(permutation_null(agg_df, col, n_iter=2000))

if not ocr_df.empty:
    ocr_agg_df = pd.read_csv(OCR_DIR / 'ocr_coverage_results.csv')
    for col in ['weighted_ocr_score', 'mean_ocr_score']:
        eval_rows.append(evaluate(ocr_agg_df, col))
        null_rows.append(permutation_null(ocr_agg_df, col, n_iter=2000))

results = pd.DataFrame(eval_rows)
nulls = pd.DataFrame(null_rows)
results.to_csv(OUT_DIR / 'aggregate_results.csv', index=False)
nulls.to_csv(OUT_DIR / 'aggregate_nulls.csv', index=False)
print('=== Aggregate ===')
print(results.to_string(index=False))
print('=== Permutation Null ===')
print(nulls.to_string(index=False))
"""))

CELLS.append(md("""## Download Results Bundle
"""))

CELLS.append(code("""import zipfile
from google.colab import files

bundle = Path('/content/scenetwin_timing_20clip_results.zip')
with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as zf:
    for path in OUT_DIR.rglob('*'):
        if path.is_file():
            zf.write(path, path.relative_to(OUT_DIR.parent))
print(f'bundle size: {bundle.stat().st_size / 1e6:.1f} MB')
files.download(str(bundle))
"""))


def main() -> None:
    nb = {
        "cells": CELLS,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
            "colab": {"provenance": []},
            "accelerator": "GPU",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, indent=1) + "\n")
    print(f"Wrote {OUT_NB} ({len(CELLS)} cells)")


if __name__ == "__main__":
    main()
