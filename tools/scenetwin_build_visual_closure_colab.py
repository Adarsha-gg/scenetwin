#!/usr/bin/env python3
"""Build the visual-ROI closure Colab notebook.

What changed from the first closure pilot
==========================================
The first pilot showed that whole-cortex closure metrics are dominated by
TRIBE's language/auditory networks -- longer AD texts inflate those regions
regardless of content quality (62-word pro AD vs 35-word control). The visual
ROI sub-analysis already showed the right direction (4/6 tier3 wins on
closure_mean, 6/6 on top-gap) but was only 2 clips × 2 tiers.

This notebook fixes that:

  1. Visual-ROI-only evaluation by default. Language/auditory ROIs are
     reported separately as a sanity/confound check, not as headline metrics.
  2. All 4 tiers tested per clip so we get a Spearman rho, not just a
     pairwise comparison.
  3. More clips: default pilot is 6 clips. Can scale to all 18.
  4. Length-controlled view: Spearman rho after partialling out word count.
  5. Glasser mask uploaded from local results.

What the experiment actually tests
===================================
This is NOT simulating a blind user listening to audio description. TRIBE's
text modality processes AD text through LLaMA -- it adds word-timing events
to the model, not TTS speech. The correct framing is:

  "Does TRIBE's text pathway carry enough visual semantic content to
   push visual cortex predictions closer to audiovisual viewing when
   conditioned on a better description?"

If tier3 > tier2 > tier1 > tier0 on visual ROI closure, that is evidence that
the text of a good AD encodes visual information that TRIBE can decode into
visual cortex activity. That is a meaningful finding about the model and about
what distinguishes good AD from bad AD -- even if it is not a direct simulation
of blind user experience.

Run on Colab L4. Upload:
  - scenetwin_description_gain_bundle.zip
  - glasser_roi_mask.csv  (from output/colab_upload_closure/)
  - Optional: scenetwin_timing_20clip_results.zip  (to reuse cached P_AV/P_A)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_NB = ROOT / "output" / "scenetwin_visual_closure_colab.ipynb"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": text.splitlines(keepends=True)}


CELLS: list[dict] = []

# ── Title ──────────────────────────────────────────────────────────────────
CELLS.append(md("""# SceneTwin — Visual ROI Closure

Tests whether TRIBE's **text modality** carries visual semantic content:
given the same movie audio, does a better audio description push predicted
**visual cortex activity** closer to what you'd see with the full video?

```
closure = dist(P_A, P_AV) - dist(P_A+ADtext, P_AV)
```
Positive = AD text moved the prediction closer to the audiovisual baseline.

**What this is not:** a simulation of a blind user hearing AD.
TRIBE processes AD as word-timing text events through LLaMA, not TTS audio.
The test is whether TRIBE's text pathway encodes visual semantics from a
good description.

**Key fix over the first pilot:** evaluation is restricted to **visual ROIs
only** (Glasser MT+/MST, PPA/PHC, early visual). Language/auditory ROIs are
logged separately as a confound check. All 4 tiers are tested per clip to
compute a proper Spearman ρ.

## Inputs to upload
1. `scenetwin_description_gain_bundle.zip` — video clips + descriptions
2. `glasser_roi_mask.csv` — Glasser ROI parcel assignments
3. `scenetwin_timing_20clip_results.zip` *(optional)* — cached P_AV/P_A tensors
"""))

# ── Install ────────────────────────────────────────────────────────────────
CELLS.append(code("""!rm -rf /content/tribev2
!git clone https://github.com/facebookresearch/tribev2.git --quiet
!pip install -e tribev2 --quiet
!pip install --quiet huggingface_hub pandas scipy numpy==2.2.6 moviepy matplotlib seaborn
!apt-get update -qq && apt-get install -y -qq ffmpeg
import os; os.kill(os.getpid(), 9)
"""))

# ── Upload ─────────────────────────────────────────────────────────────────
CELLS.append(md("## Upload inputs"))
CELLS.append(code("""from pathlib import Path
from google.colab import files, drive
import zipfile, shutil

USE_DRIVE = True

if USE_DRIVE:
    drive.mount('/content/drive')
    OUT_DIR = Path('/content/drive/MyDrive/scenetwin_visual_closure')
else:
    OUT_DIR = Path('/content/scenetwin_visual_closure')

ROOT       = Path('/content/scenetwin_data')
PRED_DIR   = OUT_DIR / 'preds'
AUDIO_DIR  = OUT_DIR / 'audio'
REPORT_DIR = OUT_DIR / 'reports'
for d in [ROOT, OUT_DIR, PRED_DIR, AUDIO_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print('Upload: bundle zip, glasser_roi_mask.csv, and optionally timing zip.')
uploaded = files.upload()

for name, data in uploaded.items():
    p = Path(name)
    lower = p.name.lower()
    if lower.endswith('.zip') and ('bundle' in lower or 'description_gain' in lower):
        print('Extracting data bundle:', p)
        with zipfile.ZipFile(p) as zf:
            zf.extractall(ROOT)
    elif lower.endswith('.zip'):
        import_dir = Path('/content/imported_timing')
        import_dir.mkdir(exist_ok=True)
        print('Extracting timing zip:', p)
        with zipfile.ZipFile(p) as zf:
            zf.extractall(import_dir)
        copied = 0
        for pred in list(import_dir.rglob('clip_*_P_AV.npy')) + list(import_dir.rglob('clip_*_P_A.npy')):
            t = PRED_DIR / pred.name
            if not t.exists():
                shutil.copy2(pred, t); copied += 1
        print('  Imported cached predictions:', copied)
    elif lower == 'glasser_roi_mask.csv':
        (OUT_DIR / 'glasser_roi_mask.csv').write_bytes(data)
        print('Saved Glasser mask.')

# Normalize ROOT
json_matches = sorted(Path('/content').rglob('vatex_eval_clips.json'))
if json_matches:
    ROOT = json_matches[0].parent
    print('Data ROOT:', ROOT)
else:
    raise FileNotFoundError('vatex_eval_clips.json not found after upload.')

print('Cached preds:', len(list(PRED_DIR.glob('*.npy'))))
"""))

# ── Setup ──────────────────────────────────────────────────────────────────
CELLS.append(md("""## Setup

Edit `CLIP_IDXS` to choose which clips to run. Default: 6 clips covering all
4 categories. All 4 tiers are tested per clip.

`VISUAL_GROUPS` controls which Glasser ROI groups count as visual signal.
"""))
CELLS.append(code("""import json, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, kendalltau, pearsonr
from huggingface_hub import login
login()

try:
    from moviepy.editor import VideoFileClip
except Exception:
    from moviepy import VideoFileClip

sys.path.insert(0, '/content/tribev2')
from tribev2 import TribeModel
from tribev2.demo_utils import TextToEvents, get_audio_and_text_events

CLIPS_JSON = ROOT / 'vatex_eval_clips.json'
CLIPS_DIR  = ROOT / 'vatex_clips'

with CLIPS_JSON.open() as f:
    clips_meta = json.load(f)

# ── Pilot clip selection: 6 clips, 4 categories ───────────────────────────
# Change these after you've verified the signal is real.
CLIP_IDXS = [1, 3, 9, 11, 15, 17]   # Food×2, Sports×2, Pets×2
ALL_TIERS = ['tier0_cross', 'tier1_vatex_short', 'tier2_vatex_long', 'tier3_va11y']
TIER_GT   = {'tier0_cross': 0, 'tier1_vatex_short': 1, 'tier2_vatex_long': 2, 'tier3_va11y': 3}

# ── ROI groups to treat as visual signal vs confound ──────────────────────
VISUAL_GROUPS   = {
    'early_visual_v1', 'higher_visual_v2v3v4', 'motion_mt_complex',
    'scene_ppa', 'lateral_object_loc', 'face_ffc', 'body_eba_region',
    'retrosplenial_pos',
}
LANGUAGE_GROUPS = {'language_control', 'auditory_control'}

# Load Glasser mask
mask_path = OUT_DIR / 'glasser_roi_mask.csv'
if mask_path.exists():
    glasser_df = pd.read_csv(mask_path)
    print('Glasser mask loaded:', glasser_df.shape)
    print('ROI groups:', glasser_df['roi'].value_counts().to_dict())
else:
    glasser_df = None
    print('WARNING: glasser_roi_mask.csv not found. Will use whole-cortex only.')

def get_roi_indices(groups):
    if glasser_df is None:
        return None
    sub = glasser_df[glasser_df['roi'].isin(groups)]
    return sub['vertex'].values

visual_idx   = get_roi_indices(VISUAL_GROUPS)
language_idx = get_roi_indices(LANGUAGE_GROUPS)
print(f'Visual ROI parcels: {len(visual_idx) if visual_idx is not None else "all"}')
print(f'Language ROI parcels: {len(language_idx) if language_idx is not None else "all"}')

print('Model loading...')
model = TribeModel.from_pretrained('facebook/tribev2', cache_folder=str(OUT_DIR / 'tribe_cache'))
print('Model loaded.')
print('Clips:', CLIP_IDXS, '| Tiers:', len(ALL_TIERS))
"""))

# ── Helper functions ───────────────────────────────────────────────────────
CELLS.append(md("## Helper functions"))
CELLS.append(code("""def find_clip_path(idx):
    for ext in ['.mp4', '.webm', '.mkv', '.avi']:
        p = CLIPS_DIR / f'clip_{idx:02d}{ext}'
        if p.exists(): return p
    matches = sorted(CLIPS_DIR.glob(f'clip_{idx:02d}.*'))
    if matches: return matches[0]
    raise FileNotFoundError(f'clip_{idx:02d}.* not found')

def extract_audio(video_path, idx):
    audio_path = AUDIO_DIR / f'clip_{idx:02d}.wav'
    if audio_path.exists(): return audio_path
    clip = VideoFileClip(str(video_path))
    if clip.audio is None:
        clip.close(); raise ValueError(f'No audio in {video_path}')
    try:
        clip.audio.write_audiofile(str(audio_path), fps=16000, verbose=False, logger=None)
    except TypeError:
        clip.audio.write_audiofile(str(audio_path), fps=16000, logger=None)
    clip.close()
    return audio_path

def audio_only_events(audio_path):
    event = {'type': 'Audio', 'filepath': str(audio_path),
             'start': 0, 'timeline': 'default', 'subject': 'default'}
    return get_audio_and_text_events(pd.DataFrame([event]), audio_only=True)

def ad_text_events(model, text):
    # Word-timing text events only — no TTS audio, just LLaMA text semantics.
    events = TextToEvents(
        text=str(text).strip(),
        infra={'folder': model.cache_folder, 'mode': 'retry'},
    ).get_events()
    text_only = events[events['type'].astype(str) != 'Audio'].copy()
    if text_only.empty:
        raise RuntimeError('No text events from TextToEvents')
    return text_only

def audio_plus_ad_events(model, audio_path, ad_text):
    # Movie audio + AD text events (no extra TTS audio).
    a_ev = audio_only_events(audio_path)
    t_ev = ad_text_events(model, ad_text)
    all_cols = list(dict.fromkeys([*a_ev.columns, *t_ev.columns]))
    return pd.concat([a_ev.reindex(columns=all_cols),
                      t_ev.reindex(columns=all_cols)], ignore_index=True)

def predict_cached(name, events_fn):
    p = PRED_DIR / f'{name}.npy'
    if p.exists():
        arr = np.load(p)
        print(f'  cache: {p.name} {arr.shape}')
        return arr
    print(f'  TRIBE inference: {name}')
    events = events_fn()
    preds, _ = model.predict(events)
    np.save(p, preds)
    print(f'  saved: {p.name} {preds.shape}')
    return preds

def flatten(x):
    x = np.asarray(x)
    if x.ndim == 3 and x.shape[1] == 1: x = x[:, 0, :]
    elif x.ndim > 2: x = x.reshape(x.shape[0], -1)
    return x

def roi_slice(arr, idx):
    # Restrict to specific parcel indices if mask available.
    if idx is None or len(idx) == 0: return arr
    valid = idx[idx < arr.shape[1]]
    return arr[:, valid] if len(valid) > 0 else arr

def closure_stats(p_av, p_a, p_a_ad, roi_idx=None):
    p_av = roi_slice(flatten(p_av), roi_idx)
    p_a  = roi_slice(flatten(p_a),  roi_idx)
    p_ad = roi_slice(flatten(p_a_ad), roi_idx)
    T = min(len(p_av), len(p_a), len(p_ad))
    p_av, p_a, p_ad = p_av[:T], p_a[:T], p_ad[:T]

    base = np.linalg.norm(p_a  - p_av, axis=1)
    ad   = np.linalg.norm(p_ad - p_av, axis=1)
    res  = base - ad  # positive = AD moved closer to P_AV

    # cosine distance
    def cdist(x, y):
        num = (x * y).sum(1)
        den = np.linalg.norm(x,1) * np.linalg.norm(y,1)
        return 1 - np.divide(num, den, out=np.zeros_like(num), where=den>0)

    base_c = cdist(p_a, p_av)
    ad_c   = cdist(p_ad, p_av)
    cos    = base_c - ad_c

    k = max(1, int(np.ceil(T * 0.25)))
    top = np.argsort(base)[-k:]
    return {
        'n_trs': T,
        'closure_residual_mean': float(res.mean()),
        'closure_residual_top25': float(res[top].mean()),
        'closure_cosine_mean': float(cos.mean()),
        'base_dist': float(base.mean()),
        'ad_dist':   float(ad.mean()),
    }

print('Helpers ready.')
"""))

# ── Main inference loop ────────────────────────────────────────────────────
CELLS.append(md("""## Run inference

Every prediction is cached immediately. If P_AV and P_A are already cached
(from a previous run or from the timing zip), only the 4 new P_A+AD predictions
are computed per clip.

For 6 clips × 4 tiers = 24 new predictions on an L4, expect ~40-60 min total
if no cache exists. With P_AV/P_A cached: ~25-35 min.
"""))
CELLS.append(code("""rows = []

for idx in CLIP_IDXS:
    meta  = clips_meta[idx]
    vpath = find_clip_path(idx)
    apath = extract_audio(vpath, idx)
    cat   = meta.get('category', '')
    print(f'\\n=== clip_{idx:02d} [{cat}] ===')

    p_av = predict_cached(f'clip_{idx:02d}_P_AV',
        lambda vp=vpath: model.get_events_dataframe(video_path=str(vp)))

    try:
        p_a = predict_cached(f'clip_{idx:02d}_P_A',
            lambda ap=apath: model.get_events_dataframe(audio_path=str(ap)))
    except Exception:
        p_a = predict_cached(f'clip_{idx:02d}_P_A',
            lambda ap=apath: audio_only_events(ap))

    for tier in ALL_TIERS:
        ad_text = str(meta.get(tier, '')).strip()
        n_words = len(ad_text.split())

        p_a_ad = predict_cached(f'clip_{idx:02d}_{tier}_P_A_ADtext',
            lambda ap=apath, txt=ad_text: audio_plus_ad_events(model, ap, txt))

        vis  = closure_stats(p_av, p_a, p_a_ad, visual_idx)
        lang = closure_stats(p_av, p_a, p_a_ad, language_idx)
        full = closure_stats(p_av, p_a, p_a_ad, None)

        row = {
            'clip_idx': idx, 'category': cat,
            'tier': tier, 'gt': TIER_GT[tier], 'n_words': n_words,
            'vis_closure_mean':    vis['closure_residual_mean'],
            'vis_closure_top25':   vis['closure_residual_top25'],
            'vis_cosine_mean':     vis['closure_cosine_mean'],
            'lang_closure_mean':   lang['closure_residual_mean'],
            'full_closure_mean':   full['closure_residual_mean'],
            'vis_base_dist':       vis['base_dist'],
            'vis_ad_dist':         vis['ad_dist'],
        }
        rows.append(row)
        pd.DataFrame(rows).to_csv(OUT_DIR / 'visual_closure_partial.csv', index=False)

        print(f'  {tier:25s} vis={vis["closure_residual_mean"]:+.4f}  '
              f'lang={lang["closure_residual_mean"]:+.4f}  words={n_words}')

df = pd.DataFrame(rows)
df.to_csv(OUT_DIR / 'visual_closure_results.csv', index=False)
print('\\nDone. Total rows:', len(df))
df
"""))

# ── Analysis ───────────────────────────────────────────────────────────────
CELLS.append(md("## Analysis"))
CELLS.append(code("""df = pd.read_csv(OUT_DIR / 'visual_closure_results.csv')

METRIC     = 'vis_closure_mean'     # headline: visual ROI closure
LANG_CHECK = 'lang_closure_mean'    # confound: language/auditory ROI closure

print('=' * 60)
print('PRIMARY: Visual ROI closure')
print('=' * 60)

# Tier means
tier_means = df.groupby('tier')[METRIC].mean().reindex(
    ['tier3_va11y', 'tier2_vatex_long', 'tier1_vatex_short', 'tier0_cross'])
print('\\nTier means (visual ROI):')
print(tier_means.to_string())

# Spearman rho across all rows
rho, rho_p = spearmanr(df['gt'], df[METRIC])
tau, tau_p = kendalltau(df['gt'], df[METRIC])
print(f'\\nSpearman rho = {rho:.4f}  (p={rho_p:.4g})')
print(f'Kendall tau  = {tau:.4f}  (p={tau_p:.4g})')

# Pairwise tier3 wins per clip
pw_wins = pw_total = 0
for _, grp in df.groupby('clip_idx'):
    bt = dict(zip(grp['tier'], grp[METRIC]))
    for t in ['tier0_cross', 'tier1_vatex_short', 'tier2_vatex_long']:
        if t in bt and 'tier3_va11y' in bt:
            pw_total += 1
            pw_wins  += int(bt['tier3_va11y'] > bt[t])
print(f'Pairwise tier3 wins: {pw_wins}/{pw_total}')

print()
print('=' * 60)
print('CONFOUND CHECK: Language/auditory ROI closure')
print('Expected: dominated by word count, not tier quality')
print('=' * 60)
rho_l, rho_lp = spearmanr(df['gt'], df[LANG_CHECK])
rho_w, rho_wp = spearmanr(df['n_words'], df[LANG_CHECK])
print(f'rho(gt, lang_closure)    = {rho_l:.4f}  (p={rho_lp:.4g})')
print(f'rho(n_words, lang_closure) = {rho_w:.4f}  (p={rho_wp:.4g})')
print('If n_words drives lang more than gt does, confound confirmed.')

# Length partial: does visual closure survive controlling for word count?
print()
print('=' * 60)
print('LENGTH CONTROL: residualize vis_closure on n_words')
print('=' * 60)
from numpy.linalg import lstsq
X = np.column_stack([df['n_words'].values, np.ones(len(df))])
resid = df[METRIC].values - X @ lstsq(X, df[METRIC].values, rcond=None)[0]
rho_r, rho_rp = spearmanr(df['gt'], resid)
print(f'Spearman rho (length-residualized) = {rho_r:.4f}  (p={rho_rp:.4g})')
print('If rho stays significant, visual closure is not just a word-count proxy.')
"""))

# ── Plot ───────────────────────────────────────────────────────────────────
CELLS.append(code("""fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# 1. Visual closure by tier
tier_order = ['tier3_va11y', 'tier2_vatex_long', 'tier1_vatex_short', 'tier0_cross']
means = df.groupby('tier')[METRIC].mean().reindex(tier_order)
sems  = df.groupby('tier')[METRIC].sem().reindex(tier_order)
ax = axes[0]
colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336']
bars = ax.bar(range(4), means.values, yerr=sems.values, color=colors, capsize=4)
ax.set_xticks(range(4))
ax.set_xticklabels(['tier3\n(pro)', 'tier2\n(long)', 'tier1\n(short)', 'tier0\n(cross)'], fontsize=9)
ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax.set_ylabel('Visual ROI closure (positive = better)')
ax.set_title(f'Visual ROI closure by tier\\nSpearman ρ={rho:.3f} (p={rho_p:.3g})')
ax.grid(axis='y', alpha=0.3)

# 2. Visual vs language closure scatter (word count confound check)
ax = axes[1]
for tier, grp in df.groupby('tier'):
    ax.scatter(grp[LANG_CHECK], grp[METRIC],
               label=tier.replace('tier', 'T').replace('_va11y', '').replace('_vatex', ''),
               alpha=0.7, s=50)
ax.axhline(0, color='gray', linewidth=0.5)
ax.axvline(0, color='gray', linewidth=0.5)
ax.set_xlabel('Language ROI closure (confound)')
ax.set_ylabel('Visual ROI closure (signal)')
ax.set_title('Visual vs language closure\n(should NOT be correlated)')
ax.legend(fontsize=7)

# 3. Per-clip tier ordering
ax = axes[2]
pivot = df.pivot(index='clip_idx', columns='tier', values=METRIC)[tier_order]
pivot.plot(kind='bar', ax=ax, color=colors)
ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax.set_xlabel('Clip')
ax.set_ylabel('Visual ROI closure')
ax.set_title('Per-clip visual closure by tier')
ax.legend(fontsize=7, loc='lower right')
ax.tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig(REPORT_DIR / 'visual_closure_analysis.png', dpi=160)
plt.show()
print(f'Saved to {REPORT_DIR}/visual_closure_analysis.png')
"""))

# ── Export ─────────────────────────────────────────────────────────────────
CELLS.append(md("## Export"))
CELLS.append(code("""import zipfile
from google.colab import files

zip_path = Path('/content/scenetwin_visual_closure_results.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for p in [OUT_DIR / 'visual_closure_results.csv',
              OUT_DIR / 'visual_closure_partial.csv',
              REPORT_DIR / 'visual_closure_analysis.png']:
        if p.exists(): zf.write(p, arcname=p.name)
    for p in sorted(PRED_DIR.glob('clip_*_P_A_ADtext.npy')):
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
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
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
