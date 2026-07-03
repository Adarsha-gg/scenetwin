"""D7 (fused error detector) + D8 (operating points / decision curve).

Cached-data-only, Python stdlib only. Reuses AUC/permutation helpers from
cursor/research/new_directions_run.py.

Detection framing (per project spec):
  positives = fabrication drops (60 clips)   [clip_expert - clip_halluc, etc.]
  negatives = paraphrase   drops (60 clips)   [clip_expert - clip_para,   etc.]
  AUC = P(fab drop > para drop).
Established single-signal baselines: CLIP AUC ~0.835, ADQA ~0.801.
"""
import csv, os, random

ROOT = r"C:\Users\adars\Coding\scenetwin"
def p(*a): return os.path.join(ROOT, *a)

def readcsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def auc(pos, neg):
    """Mann-Whitney AUC: P(pos>neg), ties=0.5."""
    if not pos or not neg: return float('nan')
    c = 0.0
    for a in pos:
        for b in neg:
            if a > b: c += 1
            elif a == b: c += 0.5
    return c / (len(pos) * len(neg))

def best_auc(scores, labels):
    """AUC choosing better of the two directions; returns (auc, direction)."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    a = auc(pos, neg)
    if a >= 0.5: return a, 'high'
    return 1 - a, 'low'

def perm_p(scores, labels, n=20000, seed=0):
    """One-sided label-permutation p for best-direction AUC."""
    rng = random.Random(seed)
    obs, _ = best_auc(scores, labels)
    labs = list(labels); ge = 0
    for _ in range(n):
        rng.shuffle(labs)
        a, _ = best_auc(scores, labs)
        if a >= obs: ge += 1
    return (ge + 1) / (n + 1), obs

def mean(x): return sum(x) / len(x) if x else float('nan')
def sd(x):
    m = mean(x)
    return (sum((v - m) ** 2 for v in x) / len(x)) ** 0.5

# ---------------------------------------------------------------- load signals
hg = readcsv(p("cursor/output/halluc_gate/halluc_gate.csv"))
n = len(hg)
clip_fab = [float(r['clip_expert']) - float(r['clip_halluc']) for r in hg]
clip_par = [float(r['clip_expert']) - float(r['clip_para'])   for r in hg]
adqa_fab = [float(r['adqa_expert']) - float(r['adqa_halluc']) for r in hg]
adqa_par = [float(r['adqa_expert']) - float(r['adqa_para'])   for r in hg]

# scores + labels arrays (positives first, then negatives) for AUC/perm helpers
def scores_labels(pos, neg):
    return pos + neg, [1] * len(pos) + [0] * len(neg)

print("=" * 70)
print("D7  FUSED ERROR DETECTOR")
print("=" * 70)
print(f"n clips = {n}   (positives = {n} fab drops, negatives = {n} para drops)")

clip_auc = auc(clip_fab, clip_par)
adqa_auc = auc(adqa_fab, adqa_par)
print(f"\nSingle-signal baselines:")
print(f"  CLIP-drop AUC = {clip_auc:.3f}")
print(f"  ADQA-drop AUC = {adqa_auc:.3f}")

# z-normalize each drop signal over the POOLED fab+para values (120 per signal)
clip_pool = clip_fab + clip_par
adqa_pool = adqa_fab + adqa_par
mc, sc = mean(clip_pool), sd(clip_pool) or 1.0
ma, sa = mean(adqa_pool), sd(adqa_pool) or 1.0
zc_fab = [(v - mc) / sc for v in clip_fab]
zc_par = [(v - mc) / sc for v in clip_par]
za_fab = [(v - ma) / sa for v in adqa_fab]
za_par = [(v - ma) / sa for v in adqa_par]

# (a) MEAN fusion
mean_fab = [(c + a) / 2 for c, a in zip(zc_fab, za_fab)]
mean_par = [(c + a) / 2 for c, a in zip(zc_par, za_par)]
mean_auc = auc(mean_fab, mean_par)

# (b) MAX fusion  (== shared-threshold OR at the score level)
max_fab = [max(c, a) for c, a in zip(zc_fab, za_fab)]
max_par = [max(c, a) for c, a in zip(zc_par, za_par)]
max_auc = auc(max_fab, max_par)

print(f"\nFusion (z-normalized over pooled fab+para, per signal):")
print(f"  (a) MEAN fusion AUC = {mean_auc:.3f}")
print(f"  (b) MAX  fusion AUC = {max_auc:.3f}   (== shared-threshold OR score)")

# permutation p for the BEST fusion
fusions = {'mean': (mean_fab, mean_par, mean_auc), 'max': (max_fab, max_par, max_auc)}
best_name = max(fusions, key=lambda k: fusions[k][2])
bf_pos, bf_neg, bf_auc = fusions[best_name]
bscores, blabels = scores_labels(bf_pos, bf_neg)
pval, obs = perm_p(bscores, blabels, n=20000, seed=0)
print(f"\nBest fusion = {best_name.upper()} (AUC={bf_auc:.3f})")
print(f"  label-permutation p (20k, best-direction) = {pval:.4f}")

best_single = max(clip_auc, adqa_auc)
best_single_name = 'CLIP' if clip_auc >= adqa_auc else 'ADQA'
delta = bf_auc - best_single
print(f"\nBest single signal = {best_single_name} (AUC={best_single:.3f})")
print(f"Best fusion - best single = {delta:+.3f}")
print("Honest read: " + ("fusion beats" if delta > 0 else "fusion does NOT beat") +
      f" the best single signal by {delta:+.3f} AUC.")

# ---- (c) OR rule at concrete per-signal operating points -------------------
# 'flag if either drop exceeds its own chosen threshold'
# threshold each signal at its own target FPR on the paraphrase negatives.
def thr_for_fpr(neg, target):
    """threshold t s.t. exactly floor(target*N) negatives are strictly > t."""
    m = int(target * len(neg))
    ds = sorted(neg, reverse=True)   # descending
    # t = m-th largest value -> exactly the top m are strictly greater
    return ds[m] if m < len(neg) else ds[-1] - 1e-9, m

def flags(scores, t): return [1 if s > t else 0 for s in scores]

print("\nOR rule (each signal thresholded at its OWN target FPR, then OR):")
for tgt in (0.05, 0.10, 0.20):
    tc, mc_n = thr_for_fpr(clip_par, tgt)
    ta, ma_n = thr_for_fpr(adqa_par, tgt)
    # combined recall on positives
    tp = sum(1 for cf, af in zip(clip_fab, adqa_fab) if cf > tc or af > ta)
    # combined false alarms on negatives
    fp = sum(1 for cp, ap in zip(clip_par, adqa_par) if cp > tc or ap > ta)
    print(f"  per-signal FPR target {tgt:.0%}: OR recall = {tp}/{n} = {tp/n:.1%}"
          f"  | combined FPR = {fp}/{n} = {fp/n:.1%}")

# ============================================================================
print("\n" + "=" * 70)
print("D8  OPERATING POINTS / DECISION CURVE")
print("=" * 70)

# best detector for the decision curve
detectors = {
    'CLIP-drop':   (clip_fab, clip_par),
    'ADQA-drop':   (adqa_fab, adqa_par),
    f'{best_name}-fusion': (bf_pos, bf_neg),
}

def recall_at_fpr(pos, neg, target):
    """recall (TPR) at threshold giving FPR = floor(target*N)/N on negatives."""
    m = int(target * len(neg))
    ds = sorted(neg, reverse=True)
    t = ds[m] if m < len(neg) else ds[-1] - 1e-9
    tp = sum(1 for s in pos if s > t)
    fp = sum(1 for s in neg if s > t)
    return tp / len(pos), fp / len(neg), t

print("\nRecall (sensitivity) at fixed FPR (FPR on paraphrase negatives):")
print(f"{'detector':16s} {'FPR=5%':>10s} {'FPR=10%':>10s} {'FPR=20%':>10s}")
op = {}
for name, (pos, neg) in detectors.items():
    row = []
    for tgt in (0.05, 0.10, 0.20):
        tpr, fpr, t = recall_at_fpr(pos, neg, tgt)
        row.append((tpr, fpr))
        op[(name, tgt)] = (tpr, fpr)
    print(f"{name:16s} {row[0][0]:>9.1%} {row[1][0]:>9.1%} {row[2][0]:>9.1%}")

# ---- PPV at the 10% FPR operating point under assumed base rates ----------
print("\nPPV (precision) at the 10% FPR operating point:")
print("  Formula: PPV = (pi*TPR) / (pi*TPR + (1-pi)*FPR),  pi = base rate")
print(f"{'detector':16s} {'TPR@10%':>9s} {'FPR':>6s} "
      f"{'PPV@5%':>8s} {'PPV@15%':>8s} {'PPV@30%':>8s}")
def ppv(pi, tpr, fpr):
    denom = pi * tpr + (1 - pi) * fpr
    return (pi * tpr) / denom if denom > 0 else float('nan')
ppv_table = {}
for name in detectors:
    tpr, fpr = op[(name, 0.10)]
    ppvs = [ppv(pi, tpr, fpr) for pi in (0.05, 0.15, 0.30)]
    ppv_table[name] = (tpr, fpr, ppvs)
    print(f"{name:16s} {tpr:>8.1%} {fpr:>6.1%} "
          f"{ppvs[0]:>8.1%} {ppvs[1]:>8.1%} {ppvs[2]:>8.1%}")

# ---- net benefit / decision curve read (best detector) --------------------
# Net benefit at harm-threshold prob pt (odds O = pt/(1-pt)):
#   NB(model) = TPR*pi - FPR*(1-pi)*O
#   NB(all)   = pi     - (1-pi)*O      (review everything)
#   NB(none)  = 0                       (review nothing)
# Model is the BEST of the three for pt in [pt_low, pt_high]:
#   O_low  (model overtakes review-all)  = pi*(1-TPR) / ((1-pi)*(1-FPR))
#   O_high (model overtakes review-none) = pi*TPR     / ((1-pi)*FPR)
print("\nNet-benefit / decision-curve read (best detector, 10% FPR op point):")
best_det = f'{best_name}-fusion' if bf_auc >= best_single else best_single_name
tpr_b, fpr_b = op[(best_det, 0.10)]
print(f"  using {best_det}: TPR={tpr_b:.1%}, FPR={fpr_b:.1%}")
print(f"  Harm-threshold window (pt) where FLAGGING beats both defaults:")
print(f"{'base rate pi':>14s} {'pt_low':>8s} {'pt_high':>8s}   interpretation")
def odds_to_pt(o): return o / (1 + o)
for pi in (0.05, 0.15, 0.30):
    o_low = pi * (1 - tpr_b) / ((1 - pi) * (1 - fpr_b))
    o_high = pi * tpr_b / ((1 - pi) * fpr_b)
    pt_low, pt_high = odds_to_pt(o_low), odds_to_pt(o_high)
    print(f"{pi:>13.0%} {pt_low:>8.1%} {pt_high:>8.1%}   "
          f"below pt_low review-all wins; above pt_high review-none wins")

print("\nDONE.")
