"""D21c — cheap visual proxies vs TRIBE gap AND actual ADQA failure, at n=60.

Uses freshly extracted frames (cursor/research/output/ext60_frames/<video_id>/*.jpg)
for the 60 external clips, joined to cursor/research/output/parallel_research/
cheap_baselines/external_features.csv which has accessibility_gap, mean_visual_gap,
mean_scene_spatial_gap, and the real adqa_fail label for all 60.

Tests, at whatever n actually downloaded (reported honestly):
  (1) do cheap visual proxies reproduce the neural gap?  Spearman(proxy, accessibility_gap)
  (2) do cheap visual proxies predict ADQA failure?      AUC(proxy, adqa_fail)
      -> head-to-head vs accessibility_gap's own AUC (0.794 established).
"""
import csv, os, glob, math, random
import numpy as np
from PIL import Image

ROOT = r"C:\Users\adars\Coding\scenetwin"
FRAMES = os.path.join(ROOT, "cursor", "research", "output", "ext60_frames")
FEATS = os.path.join(ROOT, "cursor/research/output/parallel_research/cheap_baselines/external_features.csv")

def load_gray(path, size=(160,120)):
    return np.asarray(Image.open(path).convert("L").resize(size), dtype=np.float64)

def clip_proxies(cdir):
    paths = sorted(glob.glob(os.path.join(cdir, "*.jpg")))
    if len(paths) < 2: return None
    fr = [load_gray(p) for p in paths]
    diffs = [float(np.mean(np.abs(fr[i+1]-fr[i]))) for i in range(len(fr)-1)]
    grads = [float(np.mean(np.hypot(*np.gradient(f)))) for f in fr]
    return dict(motion_mean=float(np.mean(diffs)), motion_max=float(max(diffs)),
                scene_cuts=int(sum(d>25 for d in diffs)),
                brightness_std=float(np.std([np.mean(f) for f in fr])),
                detail_mean=float(np.mean(grads)), n_frames=len(fr))

def spearman(x,y):
    n=len(x)
    def ranks(v):
        o=sorted(range(len(v)),key=lambda i:v[i]); r=[0.0]*len(v); i=0
        while i<len(v):
            j=i
            while j+1<len(v) and v[o[j+1]]==v[o[i]]: j+=1
            a=(i+j)/2.0+1
            for k in range(i,j+1): r[o[k]]=a
            i=j+1
        return r
    rx,ry=ranks(x),ranks(y); mx=sum(rx)/n; my=sum(ry)/n
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den=math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))
    rho=num/den if den else float('nan')
    rng=random.Random(0); ys=list(ry); ge=0; B=10000; obs=abs(rho)
    for _ in range(B):
        rng.shuffle(ys)
        r2=sum((a-mx)*(b-my) for a,b in zip(rx,ys))/den if den else 0
        if abs(r2)>=obs: ge+=1
    return rho,(ge+1)/(B+1)

def auc(pos,neg):
    if not pos or not neg: return float('nan')
    c=sum((a>b)+0.5*(a==b) for a in pos for b in neg)
    return c/(len(pos)*len(neg))
def best_auc(sc,lab):
    p=[s for s,l in zip(sc,lab) if l==1]; n=[s for s,l in zip(sc,lab) if l==0]
    a=auc(p,n); return (a,'high') if a>=0.5 else (1-a,'low')

feats={r['video_id']:r for r in csv.DictReader(open(FEATS))}
rows=[]
for cdir in sorted(glob.glob(os.path.join(FRAMES,"*"))):
    vid=os.path.basename(cdir)
    if vid not in feats: continue
    px=clip_proxies(cdir)
    if px is None: continue
    f=feats[vid]
    rows.append(dict(video_id=vid, adqa_fail=int(f['adqa_fail']),
        accessibility_gap=float(f['accessibility_gap']),
        mean_visual_gap=float(f['mean_visual_gap']),
        mean_scene_spatial_gap=float(f['mean_scene_spatial_gap']),
        duration_s=float(f['duration_s']), **px))

print(f"n clips with frames+features = {len(rows)}  (adqa_fail positives = {sum(r['adqa_fail'] for r in rows)})")
proxies=['motion_mean','motion_max','scene_cuts','brightness_std','detail_mean','duration_s']

print("\n(1) Spearman(cheap visual proxy, TRIBE signal)  [rho (perm p)]")
for t in ['accessibility_gap','mean_visual_gap','mean_scene_spatial_gap']:
    yv=[r[t] for r in rows]
    print(f"  target={t}")
    for px in proxies:
        rho,p=spearman([r[px] for r in rows],yv)
        print(f"      {px:16s} rho={rho:+.2f} (p={p:.3f})")

print("\n(2) AUC(cheap visual proxy, adqa_fail)  vs accessibility_gap baseline")
lab=[r['adqa_fail'] for r in rows]
ag,_=best_auc([r['accessibility_gap'] for r in rows],lab)
print(f"  accessibility_gap (NEURAL)   AUC={ag:.3f}")
for px in proxies:
    a,d=best_auc([r[px] for r in rows],lab)
    print(f"  {px:16s} AUC={a:.3f} ({d})")
print("\nVerdict prints from the numbers above (no fabrication).")
