"""D21 — Cheap visual-motion proxies vs the expensive TRIBE neural gap.

Completes the round-1 D4 "fair fight" that was BLOCKED for lack of frames+libs.
Question: does a cheap frame-difference / scene-complexity proxy (computed straight
from cached JPG frames with numpy+PIL) reproduce or predict TRIBE's per-clip neural
accessibility signal (tr_mean_cosine_gap) and need signals? If yes, the expensive
fMRI-encoder signal is partly reducible to cheap pixel statistics; if no, TRIBE
captures something motion/complexity proxies do not.

Data:
  output/scenetwin_timing_20clip/tribe_only_analysis.csv  (clip_idx->video_id,
      tr_mean_cosine_gap, mean_need, max_need, fraction_high_need, duration_s)
  output/scenetwin_timing_20clip/adqa_frames/clip_NN/*.jpg  (cached frames)
Stdlib + numpy + PIL only. No network/API/GPU.
"""
import csv, os, glob, math
import numpy as np
from PIL import Image

ROOT = r"C:\Users\adars\Coding\scenetwin"
FRAMES = os.path.join(ROOT, "output", "scenetwin_timing_20clip", "adqa_frames")
TRIBE = os.path.join(ROOT, "output", "scenetwin_timing_20clip", "tribe_only_analysis.csv")

def spearman(x, y):
    n = len(x)
    if n < 3: return float('nan'), float('nan')
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0]*len(v); i = 0
        while i < len(v):
            j = i
            while j+1 < len(v) and v[order[j+1]] == v[order[i]]: j += 1
            avg = (i+j)/2.0 + 1
            for k in range(i, j+1): r[order[k]] = avg
            i = j+1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx)/n, sum(ry)/n
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))
    rho = num/den if den else float('nan')
    # permutation p (two-sided) — small n, exact-ish via 20000 shuffles
    import random
    rng = random.Random(0); ge = 0; obs = abs(rho); B = 20000
    ys = list(ry)
    for _ in range(B):
        rng.shuffle(ys)
        num2 = sum((a-mx)*(b-my) for a, b in zip(rx, ys))
        r2 = num2/den if den else 0.0
        if abs(r2) >= obs: ge += 1
    return rho, (ge+1)/(B+1)

def load_gray(path, size=(160, 120)):
    im = Image.open(path).convert("L").resize(size)
    return np.asarray(im, dtype=np.float64)

def clip_proxies(frame_dir):
    paths = sorted(glob.glob(os.path.join(frame_dir, "*.jpg")))
    if len(paths) < 2: return None
    frames = [load_gray(p) for p in paths]
    diffs = [np.mean(np.abs(frames[i+1]-frames[i])) for i in range(len(frames)-1)]
    # cheap visual proxies
    motion_mean = float(np.mean(diffs))              # average inter-frame change
    motion_max = float(np.max(diffs))                # biggest cut / jump
    scene_cuts = int(sum(1 for d in diffs if d > 25))  # # of large jumps (~cut)
    brightness_std = float(np.std([np.mean(f) for f in frames]))  # exposure variability
    # spatial detail: mean gradient magnitude across frames (busy scenes = high)
    grads = []
    for f in frames:
        gy, gx = np.gradient(f)
        grads.append(np.mean(np.sqrt(gx*gx+gy*gy)))
    detail_mean = float(np.mean(grads))
    return dict(motion_mean=motion_mean, motion_max=motion_max, scene_cuts=scene_cuts,
                brightness_std=brightness_std, detail_mean=detail_mean, n_frames=len(frames))

# --- load TRIBE per-clip signals ---
tribe = {}
with open(TRIBE, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        tribe[int(r['clip_idx'])] = r

rows = []
for d in sorted(glob.glob(os.path.join(FRAMES, "clip_[0-9][0-9]"))):
    idx = int(os.path.basename(d).split("_")[1])
    if idx not in tribe: continue
    px = clip_proxies(d)
    if px is None: continue
    t = tribe[idx]
    rows.append(dict(clip_idx=idx, video_id=t['video_id'],
                     tr_gap=float(t['tr_mean_cosine_gap']),
                     mean_need=float(t['mean_need']), max_need=float(t['max_need']),
                     frac_high_need=float(t['fraction_high_need']),
                     duration_s=float(t['duration_s']), **px))

print(f"clips with frames + TRIBE signal: {len(rows)}")
print("clip_idx video_id                 tr_gap  motion  cuts  detail")
for r in rows:
    print(f"  {r['clip_idx']:2d}    {r['video_id']:24s} {r['tr_gap']:.3f}  "
          f"{r['motion_mean']:6.2f}  {r['scene_cuts']:2d}   {r['detail_mean']:.2f}")

proxies = ['motion_mean', 'motion_max', 'scene_cuts', 'brightness_std', 'detail_mean', 'duration_s']
targets = ['tr_gap', 'mean_need', 'max_need', 'frac_high_need']
print("\nSpearman(cheap visual proxy, TRIBE signal)   [rho (perm p)]")
print(f"{'proxy':16s}" + "".join(f"{t:>16s}" for t in targets))
for px in proxies:
    xv = [r[px] for r in rows]
    line = f"{px:16s}"
    for t in targets:
        yv = [r[t] for r in rows]
        rho, p = spearman(xv, yv)
        line += f"   {rho:+.2f} (p={p:.3f})"
    print(line)

print("\nInterpretation: if a cheap visual proxy tracks tr_gap with high |rho| and low p,")
print("the expensive neural gap is partly reducible to pixel statistics on these n clips.")
