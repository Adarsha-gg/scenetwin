"""D9 paraphrase false-alarm audit + D10 severity-weighted error score.

Cached-data-only analysis on SceneTwin halluc_gate + relational probe set.
Stdlib only. Reuses AUC/permutation/mean helper patterns from
cursor/research/new_directions_run.py.
"""
import csv, os, random

ROOT = r"C:\Users\adars\Coding\scenetwin"
def p(*a): return os.path.join(ROOT, *a)

def readcsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def mean(x): return sum(x)/len(x) if x else float('nan')

def median(x):
    if not x: return float('nan')
    s=sorted(x); n=len(s)
    return s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2

def auc(pos, neg):
    """Mann-Whitney AUC: P(pos>neg), ties=0.5."""
    if not pos or not neg: return float('nan')
    c=0.0
    for a in pos:
        for b in neg:
            if a>b: c+=1
            elif a==b: c+=0.5
    return c/(len(pos)*len(neg))

def ranks(x):
    """Average-rank of values (1-based), ties averaged."""
    order=sorted(range(len(x)), key=lambda i:x[i])
    r=[0.0]*len(x); i=0
    while i<len(x):
        j=i
        while j+1<len(x) and x[order[j+1]]==x[order[i]]: j+=1
        avg=(i+j)/2.0+1
        for k in range(i,j+1): r[order[k]]=avg
        i=j+1
    return r

def spearman(a,b):
    """Spearman rho via Pearson on ranks."""
    if len(a)<2: return float('nan')
    ra,rb=ranks(a),ranks(b)
    ma,mb=mean(ra),mean(rb)
    num=sum((x-ma)*(y-mb) for x,y in zip(ra,rb))
    da=sum((x-ma)**2 for x in ra)**0.5
    db=sum((y-mb)**2 for y in rb)**0.5
    if da==0 or db==0: return float('nan')
    return num/(da*db)

def perm_p_spearman(a,b,n=20000,seed=0):
    """Two-sided label-permutation p for Spearman |rho|."""
    rng=random.Random(seed)
    obs=spearman(a,b); bb=list(b); ge=0
    for _ in range(n):
        rng.shuffle(bb)
        if abs(spearman(a,bb))>=abs(obs): ge+=1
    return (ge+1)/(n+1), obs

hg=readcsv(p("cursor/output/halluc_gate/halluc_gate.csv"))
probes=readcsv(p("cursor/output/relational_hallucination_probe_set/probes.csv"))
n=len(hg)

# signed drops: expert - variant (higher => variant looks worse => flag)
clip_fab=[float(r['clip_expert'])-float(r['clip_halluc']) for r in hg]
clip_par=[float(r['clip_expert'])-float(r['clip_para'])   for r in hg]
adqa_fab=[float(r['adqa_expert'])-float(r['adqa_halluc']) for r in hg]
adqa_par=[float(r['adqa_expert'])-float(r['adqa_para'])   for r in hg]

print("="*72)
print("D9  PARAPHRASE FALSE-ALARM AUDIT")
print("="*72)
print(f"n clips = {n}  (60 paraphrase pairs = faithful negatives; 60 fabrication pairs = positives)")

# ---- (1) naive SIGN rule ----
def frac(cond): return sum(1 for x in cond if x)/len(cond)
clip_sign_fa = frac([d>0 for d in clip_par])
adqa_sign_fa = frac([d>0 for d in adqa_par])
clip_sign_recall = frac([d>0 for d in clip_fab])
adqa_sign_recall = frac([d>0 for d in adqa_fab])
print("\n-- Naive SIGN rule (flag if drop > 0) --")
print(f"CLIP sign  FALSE-ALARM on paraphrases = {clip_sign_fa:.1%} "
      f"({sum(d>0 for d in clip_par)}/{n})   | fabrication recall = {clip_sign_recall:.1%}")
print(f"ADQA sign  FALSE-ALARM on paraphrases = {adqa_sign_fa:.1%} "
      f"({sum(d>0 for d in adqa_par)}/{n})   | fabrication recall = {adqa_sign_recall:.1%}")
# ADQA note: paraphrase can even IMPROVE score; count ties/negatives
print(f"  ADQA para drop: >0 {sum(d>0 for d in adqa_par)}, ==0 {sum(d==0 for d in adqa_par)}, "
      f"<0 {sum(d<0 for d in adqa_par)} (paraphrase sometimes RAISES ADQA)")

# ---- (2) MAGNITUDE threshold at 10% paraphrase false-alarm ----
def thresh_at_fa(par, target_fa=0.10):
    """Threshold t s.t. ~target_fa of paraphrase drops are >= t (flagged)."""
    k=max(1,round(target_fa*len(par)))          # number of paraphrases allowed to flag
    s=sorted(par, reverse=True)
    t=s[k-1]                                      # k-th largest paraphrase drop
    fa=frac([d>=t for d in par])
    return t, fa, k

def recall_at(fab, t): return frac([d>=t for d in fab])

print("\n-- MAGNITUDE threshold calibrated to 10% paraphrase false-alarm --")
for name,par,fab in [("CLIP",clip_par,clip_fab),("ADQA",adqa_par,adqa_fab)]:
    t,fa,k=thresh_at_fa(par,0.10)
    rec=recall_at(fab,t)
    print(f"{name}: threshold={t:.4f}  achieved paraphrase FA={fa:.1%} ({sum(d>=t for d in par)}/{n})  "
          f"=> fabrication recall={rec:.1%} ({sum(d>=t for d in fab)}/{n})")

# separability of fab vs paraphrase drops (magnitude discriminability)
print("\n-- Magnitude separability (fab-drop vs paraphrase-drop, AUC) --")
print(f"CLIP  AUC(fab>para) = {auc(clip_fab,clip_par):.3f}")
print(f"ADQA  AUC(fab>para) = {auc(adqa_fab,adqa_par):.3f}")

# ---- (3) distribution stats ----
print("\n-- Distribution of drops (mean / median / max) --")
def stats(x): return f"mean {mean(x):+.4f}  median {median(x):+.4f}  max {max(x):+.4f}"
print(f"CLIP paraphrase : {stats(clip_par)}")
print(f"CLIP fabrication: {stats(clip_fab)}")
print(f"ADQA paraphrase : {stats(adqa_par)}")
print(f"ADQA fabrication: {stats(adqa_fab)}")

print("\n"+"="*72)
print("D10  SEVERITY-WEIGHTED ERROR SCORE")
print("="*72)
# Severity weights by probe_type. Present types: action_relation, who_role,
# spatial_relation, count. (No 'object attribute' probe_type exists in the set.)
SEV={'who_role':3,'action_relation':3,'spatial_relation':3,'count':2}  # high=3 med=2
# aggregate per clip
by_clip={}
for r in probes:
    vid=r['video_id']
    by_clip.setdefault(vid,{'w':[],'types':[],'rel':int(r['is_relation_action_count'])})
    by_clip[vid]['w'].append(SEV.get(r['probe_type'],1))
    by_clip[vid]['types'].append(r['probe_type'])

hg_by_id={r['video_id']:r for r in hg}
clips=[v for v in by_clip if v in hg_by_id]
print(f"probe-labelled clips joined to halluc_gate: {len(clips)}")
from collections import Counter
tc=Counter(t for r in probes for t in [r['probe_type']])
print("probe_type counts (probe-level):", dict(tc))

# per-clip arrays
sev=[]; cf=[]; af=[]; rel=[]
for vid in clips:
    d=by_clip[vid]
    sev.append(mean(d['w']))            # mean probe severity for the clip
    rel.append(d['rel'])
    r=hg_by_id[vid]
    cf.append(float(r['clip_expert'])-float(r['clip_halluc']))
    af.append(float(r['adqa_expert'])-float(r['adqa_halluc']))

print("\n-- Spearman: per-clip mean severity vs fabrication drop magnitude --")
pc,rc=perm_p_spearman(sev,cf); pa,ra=perm_p_spearman(sev,af)
print(f"severity vs CLIP drop : rho={rc:+.3f}  perm p={pc:.4f}")
print(f"severity vs ADQA drop : rho={ra:+.3f}  perm p={pa:.4f}")

# group means: high-severity (relation/action/count clips, is_relation_action_count=1)
# vs low-severity (object_scene clips). This is the natural 5-vs-18 split.
hi_c=[c for c,rr in zip(cf,rel) if rr==1]; lo_c=[c for c,rr in zip(cf,rel) if rr==0]
hi_a=[a for a,rr in zip(af,rel) if rr==1]; lo_a=[a for a,rr in zip(af,rel) if rr==0]
print(f"\n-- Group means (is_relation_action_count split: {len(hi_c)} high vs {len(lo_c)} low) --")
print(f"CLIP drop: high {mean(hi_c):+.4f}  vs  low {mean(lo_c):+.4f}   AUC(high>low)={auc(hi_c,lo_c):.3f}")
print(f"ADQA drop: high {mean(hi_a):+.4f}  vs  low {mean(lo_a):+.4f}   AUC(high>low)={auc(hi_a,lo_a):.3f}")

# probe_type-weighting split: all-high clips (mean sev==3) vs clips containing a
# medium 'count' probe (mean sev<3). Severity is near-constant (see distribution).
print(f"\nper-clip mean-severity distribution: "
      f"min {min(sev):.2f} median {median(sev):.2f} max {max(sev):.2f} "
      f"(==3.0: {sum(1 for s in sev if s==3)}/{len(sev)} clips are all-high)")
hi2_c=[c for c,s in zip(cf,sev) if s>=3]; lo2_c=[c for c,s in zip(cf,sev) if s<3]
hi2_a=[a for a,s in zip(af,sev) if s>=3]; lo2_a=[a for a,s in zip(af,sev) if s<3]
print(f"-- Group means (all-high sev>=3 vs contains-medium sev<3: {len(hi2_c)} vs {len(lo2_c)}) --")
print(f"CLIP drop: all-high {mean(hi2_c):+.4f}  vs  contains-count {mean(lo2_c):+.4f}")
print(f"ADQA drop: all-high {mean(hi2_a):+.4f}  vs  contains-count {mean(lo2_a):+.4f}")
