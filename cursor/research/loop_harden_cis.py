"""Hardening: clustered bootstrap 95% CIs for the detection headlines the manuscript cites,
plus D21 dropped-clip robustness. Stdlib only."""
import csv, os, random, statistics

ROOT = r"C:\Users\adars\Coding\scenetwin"
def rd(p): return list(csv.DictReader(open(os.path.join(ROOT,p),encoding='utf-8')))

def auc(pos,neg):
    if not pos or not neg: return float('nan')
    c=sum((a>b)+0.5*(a==b) for a in pos for b in neg)
    return c/(len(pos)*len(neg))

# ---- fabrication detector: per-clip CLIP/ADQA fab & para drops ----
hg=rd("cursor/output/halluc_gate/halluc_gate.csv")
clips=[]
for r in hg:
    clips.append(dict(
        clip_fab=float(r['clip_expert'])-float(r['clip_halluc']),
        clip_par=float(r['clip_expert'])-float(r['clip_para']),
        adqa_fab=float(r['adqa_expert'])-float(r['adqa_halluc']),
        adqa_par=float(r['adqa_expert'])-float(r['adqa_para'])))

def zpool(vals):
    m=statistics.mean(vals); sd=statistics.pstdev(vals) or 1.0
    return m,sd

def fusion_auc(sample):
    # z-normalize each signal over pooled fab+para within the sample, mean-fuse, AUC
    sample=[dict(c) for c in sample]
    out={}
    for sig in ['clip','adqa']:
        pooled=[c[f'{sig}_fab'] for c in sample]+[c[f'{sig}_par'] for c in sample]
        m,sd=zpool(pooled)
        for c in sample:
            c[f'{sig}_fab_z']=(c[f'{sig}_fab']-m)/sd
            c[f'{sig}_par_z']=(c[f'{sig}_par']-m)/sd
    fab=[ (c['clip_fab_z']+c['adqa_fab_z'])/2 for c in sample]
    par=[ (c['clip_par_z']+c['adqa_par_z'])/2 for c in sample]
    return auc(fab,par)

def clip_auc(sample): return auc([c['clip_fab'] for c in sample],[c['clip_par'] for c in sample])

def boot_ci(fn, data, B=5000, seed=1):
    rng=random.Random(seed); n=len(data); vals=[]
    for _ in range(B):
        s=[data[rng.randrange(n)] for _ in range(n)]
        vals.append(fn(s))
    vals.sort()
    return vals[int(0.025*B)], vals[int(0.975*B)]

print("== Fabrication detector (n=60 clips, clustered bootstrap 95% CI) ==")
print(f"  CLIP-drop  AUC={clip_auc(clips):.3f}  CI={boot_ci(clip_auc,clips)}")
print(f"  MEAN-fusion AUC={fusion_auc([dict(c) for c in clips]):.3f}  CI={boot_ci(fusion_auc,[dict(c) for c in clips])}")

# ---- omission (23 clips): clip-level AUC CI, using cached labels ----
pr=rd("cursor/output/relational_hallucination_probe_set/probes.csv")
byclip={}
for r in pr:
    byclip.setdefault(r['video_id'],[]).append(r)
oclips=[]
for vid,rows in byclip.items():
    ex=sum(1-int(x['truth_ad_mentions_true']) for x in rows)/len(rows)
    ha=sum(1-int(x['halluc_ad_mentions_true']) for x in rows)/len(rows)
    oclips.append((ex,ha))
def omis_auc(sample): return auc([h for e,h in sample],[e for e,h in sample])
print(f"\n== Omission scorer (n=23 clips, cached LLM mention labels) ==")
print(f"  clip-level AUC={omis_auc(oclips):.3f}  CI={boot_ci(lambda s: omis_auc(s), oclips)}")

# ---- D21 dropped-clip robustness ----
ef=rd("cursor/research/output/parallel_research/cheap_baselines/external_features.csv")
got=set(os.listdir(os.path.join(ROOT,"cursor/research/output/ext60_frames")))
pos_all=[r['video_id'] for r in ef if int(r['adqa_fail'])==1]
pos_missing=[v for v in pos_all if v not in got]
print(f"\n== D21 dropped-clip robustness ==")
print(f"  adqa_fail positives total={len(pos_all)}; missing frames for {len(pos_missing)} of them: {pos_missing}")
print(f"  => all failure positives retained: {len(pos_missing)==0}")
