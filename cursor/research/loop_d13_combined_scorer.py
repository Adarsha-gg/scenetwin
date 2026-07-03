"""D13 - Combined reference-free omission + fabrication AD-error scorer.

Merges the D6 omission scorer (clip-level AUC 0.945, gold vs hallucinated) and the
D7 fused fabrication detector (z-norm CLIP-drop + ADQA-drop, mean fusion AUC 0.904)
into ONE reference-free per-AD error score, and evaluates it two ways:

  1. DETECTION: on the 23 probe-labelled clips (where both signals are available),
     does combining fabrication + omission beat each alone at separating the gold AD
     from the hallucinated AD? (AUC, gold vs hallucinated.)
  2. RANKING: does the ensemble already rank the tier ladder well? Baseline Spearman
     rho of ensemble_mean_clip_top3 vs gt. An omission-aware ranking term is BLOCKED
     (no per-tier AD texts cached for the full ladder) - reported as a spec.

Pure stdlib. Cached data only. No fabricated numbers.
Run: %LOCALAPPDATA%\\Programs\\Python\\Python313\\python.exe cursor/research/loop_d13_combined_scorer.py
"""
import csv, os, random, math
from collections import defaultdict

ROOT = r"C:\Users\adars\Coding\scenetwin"
def p(*a): return os.path.join(ROOT, *a)

def readcsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def mean(x): return sum(x)/len(x) if x else float('nan')

def sd(x):
    m = mean(x); return (sum((v-m)**2 for v in x)/len(x))**0.5 if x else float('nan')

def zscore(xs):
    m = mean(xs); s = sd(xs) or 1.0
    return [(v-m)/s for v in xs]

def auc(pos, neg):
    """Mann-Whitney AUC: P(pos>neg), ties=0.5."""
    if not pos or not neg: return float('nan')
    c = 0.0
    for a in pos:
        for b in neg:
            if a > b: c += 1
            elif a == b: c += 0.5
    return c/(len(pos)*len(neg))

def best_auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    a = auc(pos, neg)
    return (a, 'high') if a >= 0.5 else (1-a, 'low')

def perm_p(scores, labels, n=20000, seed=0):
    rng = random.Random(seed)
    obs, _ = best_auc(scores, labels)
    labs = list(labels); ge = 0
    for _ in range(n):
        rng.shuffle(labs)
        a, _ = best_auc(scores, labs)
        if a >= obs: ge += 1
    return (ge+1)/(n+1), obs

def _ranks(xs):
    s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0]*len(xs); i = 0
    while i < len(xs):
        j = i
        while j+1 < len(xs) and xs[s[j+1]] == xs[s[i]]: j += 1
        for k in range(i, j+1): r[s[k]] = (i+j)/2.0 + 1
        i = j+1
    return r

def _pearson(a, b):
    n = len(a); ma = mean(a); mb = mean(b)
    num = sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    da = math.sqrt(sum((x-ma)**2 for x in a)); db = math.sqrt(sum((x-mb)**2 for x in b))
    return num/(da*db) if da and db else 0.0

def spearman(x, y): return _pearson(_ranks(x), _ranks(y))

# ============================================================================
print("="*74)
print("D13  COMBINED reference-free omission + fabrication AD-error scorer")
print("="*74)

hg = readcsv(p("cursor/output/halluc_gate/halluc_gate.csv"))
hg_by = {r['video_id']: r for r in hg}
probes = readcsv(p("cursor/output/relational_hallucination_probe_set/probes.csv"))

# omission per clip, per condition (fraction of key facts the AD does NOT state)
by_clip = defaultdict(list)
for r in probes: by_clip[r['video_id']].append(r)
clips = [v for v in by_clip if v in hg_by]
clips.sort()
print(f"\nprobe-labelled clips also in halluc_gate: n = {len(clips)}")

om_gold, om_hal = {}, {}
for v in clips:
    rows = by_clip[v]
    om_gold[v] = 1.0 - mean([int(r['truth_ad_mentions_true'])  for r in rows])
    om_hal[v]  = 1.0 - mean([int(r['halluc_ad_mentions_true']) for r in rows])

# ---- build per-AD instances: 23 gold (label 0) + 23 hallucinated (label 1) ----
# fabrication signal = raw CLIP & ADQA grounding of that AD (reference-free per-AD)
#   NOTE: halluc CLIP/ADQA come from halluc_gate's halluc_text; halluc omission comes
#   from the probe-set hallucinated_ad. These are DIFFERENT hallucinated generations
#   of the same clip (gold/expert AD is identical across both files). So the combined
#   score is a CLIP-LEVEL hallucinated-CONDITION indicator, not a same-text score.
vids, labels = [], []
clip_raw, adqa_raw, om_raw = [], [], []
for v in clips:
    r = hg_by[v]
    # gold
    vids.append(v); labels.append(0)
    clip_raw.append(float(r['clip_expert'])); adqa_raw.append(float(r['adqa_expert']))
    om_raw.append(om_gold[v])
    # hallucinated
    vids.append(v); labels.append(1)
    clip_raw.append(float(r['clip_halluc'])); adqa_raw.append(float(r['adqa_halluc']))
    om_raw.append(om_hal[v])

# z-norm each signal across the pooled 2N instances, oriented so HIGHER = MORE ERROR
zclip = zscore(clip_raw); zadqa = zscore(adqa_raw)
fab_err = [-(zc+za)/2 for zc, za in zip(zclip, zadqa)]   # low grounding -> high error
om_err  = list(om_raw)                                    # already 0..1, higher = worse
zfab = zscore(fab_err); zom = zscore(om_err)
combined = [(a+b)/2 for a, b in zip(zfab, zom)]

def split(sig): return ([s for s, l in zip(sig, labels) if l == 1],
                         [s for s, l in zip(sig, labels) if l == 0])

print("\n--- TASK 1: DETECTION (gold vs hallucinated, per-AD, %d instances) ---" % len(labels))
for name, sig, ref in (("fabrication (fused -z CLIP,-z ADQA)", fab_err, None),
                       ("omission (1 - mention rate)",         om_err, "D6=0.945"),
                       ("COMBINED (z-mean fab+omission)",       combined, None)):
    pos, neg = split(sig)
    a = auc(pos, neg)
    pv, _ = perm_p(sig, labels, n=20000)
    extra = f"  [ref {ref}]" if ref else ""
    print(f"  {name:38s} AUC={a:.3f}  perm p={pv:.4f}  "
          f"(mean pos {mean(pos):+.3f} vs neg {mean(neg):+.3f}){extra}")

# redundancy: correlation between the two error signals across all instances
print(f"\n  Spearman(fabrication, omission) across {len(labels)} instances = "
      f"{spearman(fab_err, om_err):.3f}  (co-occur by construction => partly redundant)")

# secondary: D7-style fab-vs-paraphrase z-drop on THIS 23-clip subset (paired, ref-based)
clip_fab = [float(hg_by[v]['clip_expert'])-float(hg_by[v]['clip_halluc']) for v in clips]
clip_par = [float(hg_by[v]['clip_expert'])-float(hg_by[v]['clip_para'])   for v in clips]
adqa_fab = [float(hg_by[v]['adqa_expert'])-float(hg_by[v]['adqa_halluc']) for v in clips]
adqa_par = [float(hg_by[v]['adqa_expert'])-float(hg_by[v]['adqa_para'])   for v in clips]
# z-norm drops over the pooled fab+para distribution, mean-fuse (D7 recipe)
zc = zscore(clip_fab+clip_par); za = zscore(adqa_fab+adqa_par)
n23 = len(clips)
fus_fab = [(zc[i]+za[i])/2 for i in range(n23)]
fus_par = [(zc[n23+i]+za[n23+i])/2 for i in range(n23)]
print("\n  [secondary] D7-style fab-vs-paraphrase z-drop on these 23 clips:")
print(f"    CLIP-drop AUC={auc(clip_fab,clip_par):.3f}  ADQA-drop AUC={auc(adqa_fab,adqa_par):.3f}  "
      f"mean-fusion AUC={auc(fus_fab,fus_par):.3f}   [D7(60clip)=0.904]")

# ============================================================================
print("\n" + "="*74)
print("D13  TASK 2: RANKING on the tier ladder")
print("="*74)
ext = readcsv(p("cursor/output/external_ensemble_eval.csv"))
DROP = "tier2_vatex_long"

# baseline: pooled Spearman of ensemble_mean_clip_top3 vs gt (as cached in the CSV)
g4 = [int(r['gt']) for r in ext]
e4 = [float(r['ensemble_mean_clip_top3']) for r in ext]
rho4 = spearman(e4, g4)
rows3 = [r for r in ext if r['tier'] != DROP]
g3 = [int(r['gt']) for r in rows3]
e3 = [float(r['ensemble_mean_clip_top3']) for r in rows3]
rho3 = spearman(e3, g3)
n_clips = len({r['video_id'] for r in ext})
print(f"\nladder clips = {n_clips}")
print(f"  baseline pooled Spearman (4-tier, {len(g4)} rows, incl invalid T2) = {rho4:.4f}")
print(f"  baseline pooled Spearman (3-tier corrected T0<T1<T3, {len(g3)} rows) = {rho3:.4f}")
print(f"  (canonical recompute_corrected_ladder.py, re-normalised 3-tier ensemble = 0.9516)")

print("\n  OMISSION-AWARE RANKING TERM: *** BLOCKED ***")
print("  Reason: computing an omission score per tier needs the AD TEXT for every")
print("  rung (tier0_cross, tier1_vatex_short, tier3_va11y) of all %d ladder clips," % n_clips)
print("  plus probe-style key-fact mention labels per tier. Cached data has AD text +")
print("  mention labels only for tier3 (pro = truth_ad) and ONE hallucinated variant,")
print("  and only for the 23 probe clips. external_ensemble_eval.csv carries no AD text.")
print("  SPEC to unblock: per-tier AD text for all tiers x %d clips; run the D6 probe" % n_clips)
print("  key-fact extractor + phrase-match mention detector per tier; then add an")
print("  omission-penalty term to ensemble and recompute ladder rho.")
print("\nDone.")
