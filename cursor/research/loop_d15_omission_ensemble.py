"""D15 - Omission-aware ensemble: does penalizing omission improve ladder ranking?

Question (round-2 synthesis): omission is a strong untapped signal. Test whether
folding an omission-sensitivity term into the CLIP+ADQA ranking score (a) helps or
hurts the corrected three-tier ladder Spearman rho, and (b) recovers the two known
T1-beats-T3 pairwise losses without breaking other pairs.

Data (cached only, stdlib only):
  cursor/output/external_ensemble_eval.csv                 60-clip ladder, 4 tiers
  cursor/research/output/external_t3_pairwise_losses.csv   cached T3 pairwise losses

Method matches cursor/research/recompute_corrected_ladder.py:
  drop tier2_vatex_long; order T0(cross) < T1(vatex_short) < T3(pro AD);
  per-clip min-max normalise clip_top3 and adqa_score over the 3 tiers;
  ensemble = 0.5*clip_n + 0.5*adqa_n. Baseline rho target = 0.9516.

OMISSION PROXY (labelled proxy - see report): no true per-tier omission score is
cached for the ladder tiers (D6's omission labels live on the halluc-gate
expert-vs-hallucinated set, not the ladder). We use adqa_yes_rate = fraction of the
5 frame-grounded visual questions the AD lets you answer "yes" = COVERAGE of probed
visual facts. Low yes-rate => the AD omitted the probed content. Penalising omission
== rewarding coverage: add +w * coverage_norm. coverage_norm is per-clip min-max of
adqa_yes_rate over the 3 tiers (same scheme as the other signals).
"""
import csv, os, math, random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)

DROP = "tier2_vatex_long"
ORDER = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier3_va11y": 2}
TIERS = list(ORDER)

def readcsv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ---- rank stats (stdlib) -----------------------------------------------------
def _ranks(xs):
    s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0]*len(xs); i = 0
    while i < len(xs):
        j = i
        while j+1 < len(xs) and xs[s[j+1]] == xs[s[i]]: j += 1
        for k in range(i, j+1): r[s[k]] = (i+j)/2.0 + 1
        i = j+1
    return r

def _pearson(a, b):
    n = len(a); ma = sum(a)/n; mb = sum(b)/n
    num = sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    da = math.sqrt(sum((x-ma)**2 for x in a)); db = math.sqrt(sum((x-mb)**2 for x in b))
    return num/(da*db) if da and db else 0.0

def spearman(x, y): return _pearson(_ranks(x), _ranks(y))

# ---- load / normalise --------------------------------------------------------
def load():
    clips = {}
    for r in readcsv(p("cursor/output/external_ensemble_eval.csv")):
        if r["tier"] == DROP: continue
        v = r["video_id"]; clips.setdefault(v, {})
        clips[v][r["tier"]] = {
            "clip": float(r["clip_top3"]),
            "adqa": float(r["adqa_score"]),
            "yes":  float(r["adqa_yes_rate"]),
        }
    return clips

def minmax(clips, key):
    out = {}
    for v, tiers in clips.items():
        vals = [tiers[t][key] for t in tiers]; lo, hi = min(vals), max(vals)
        out[v] = {t: (tiers[t][key]-lo)/(hi-lo) if hi > lo else 0.0 for t in tiers}
    return out

def flat(clips, d): return [d[v][t] for v in clips for t in TIERS]

# ---- build normalised signals ------------------------------------------------
clips = load()
cn  = minmax(clips, "clip")
an  = minmax(clips, "adqa")
cov = minmax(clips, "yes")            # omission (coverage) proxy, per-clip min-max
gt  = [ORDER[t] for v in clips for t in TIERS]
ens = {v: {t: 0.5*cn[v][t] + 0.5*an[v][t] for t in TIERS} for v in clips}

print("="*72)
print("D15  OMISSION-AWARE ENSEMBLE   (n_clips=%d, n_obs=%d)" % (len(clips), len(gt)))
print("="*72)

# ---- Task 1: baselines -------------------------------------------------------
rho_ens  = spearman(gt, flat(clips, ens))
rho_adqa = spearman(gt, flat(clips, an))
rho_clip = spearman(gt, flat(clips, cn))
rho_cov  = spearman(gt, flat(clips, cov))
print("\nTask1  Baseline Spearman rho vs gt (corrected 3-tier ladder):")
print("  ensemble (0.5 clip + 0.5 adqa)  rho = %.4f   (target 0.9516)" % rho_ens)
print("  adqa_norm alone                 rho = %.4f" % rho_adqa)
print("  clip_norm alone                 rho = %.4f" % rho_clip)
print("  coverage proxy (adqa_yes_rate)  rho = %.4f" % rho_cov)
# how redundant is the proxy with the adqa signal it is drawn from?
r_cov_adqa = _pearson(flat(clips, cov), flat(clips, an))
print("  Pearson(coverage_norm, adqa_norm) = %.3f  <- proxy is drawn from ADQA" % r_cov_adqa)

# ---- Task 2: weight sweep ----------------------------------------------------
def score_w(w):
    # renormalise so the omission term is *added* weight, ensemble kept at unit total
    return {v: {t: (1-w)*ens[v][t] + w*cov[v][t] for t in TIERS} for v in clips}

print("\nTask2  Omission-aware weight sweep  score(w) = (1-w)*ensemble + w*coverage:")
print("   w      rho      delta_vs_baseline")
sweep = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
rhos = {}
for w in sweep:
    r = spearman(gt, flat(clips, score_w(w))); rhos[w] = r
    print("  %.2f   %.4f   %+.4f" % (w, r, r-rho_ens))
best_w = max(sweep, key=lambda w: rhos[w])
print("  best w = %.2f (rho=%.4f, delta=%+.4f)" % (best_w, rhos[best_w], rhos[best_w]-rho_ens))

# permutation test: is the best-w rho distinguishable from the baseline rho?
# (within-clip tier-label shuffle, same scheme as recompute_corrected_ladder)
def perm_p(scored, B=5000, seed=7):
    rng = random.Random(seed); obs = spearman(gt, flat(clips, scored)); ge = 0
    for _ in range(B):
        pg, ps = [], []
        for v in clips:
            labs = [ORDER[t] for t in TIERS]; rng.shuffle(labs)
            for i, t in enumerate(TIERS): pg.append(labs[i]); ps.append(scored[v][t])
        ge += 1 if spearman(pg, ps) >= obs else 0
    return (ge+1)/(B+1)
print("  perm p (baseline)   = %.4g" % perm_p(ens))
print("  perm p (best-w=%.2f) = %.4g" % (best_w, perm_p(score_w(best_w))))

# ---- Task 3: T3-loss recovery ------------------------------------------------
# Corrected-ladder pairwise set: T0<T1, T0<T3, T1<T3 for every clip.
PAIRS = [("tier0_cross","tier1_vatex_short","T0<T1"),
         ("tier0_cross","tier3_va11y","T0<T3"),
         ("tier1_vatex_short","tier3_va11y","T1<T3")]
def pair_status(scored):
    ok = {}
    for v in clips:
        for lo, hi, nm in PAIRS:
            ok[(v, nm)] = scored[v][hi] > scored[v][lo]
    return ok
base_ok = pair_status(ens)
base_losses = [k for k, o in base_ok.items() if not o]
print("\nTask3  T3-loss recovery (corrected 3-tier ladder, %d pairwise):" % len(base_ok))
print("  baseline pairwise correct = %d/%d" % (sum(base_ok.values()), len(base_ok)))
print("  baseline losses:", [f"{v}:{nm}" for (v, nm) in base_losses])
# cross-check against cached losses file (note: it was computed on the 4-tier
# ensemble_mean_clip_top3 column; its tier2 losses fall outside the corrected ladder)
cached = readcsv(p("cursor/research/output/external_t3_pairwise_losses.csv"))
cached_t1 = sorted({r["video_id"] for r in cached if r["beating_tier"] == "tier1_vatex_short"})
print("  cached-file T3 losses vs tier1 (in-ladder):", cached_t1)
print("\n   w    recovered  newly_broken  net  pairwise_correct")
for w in sweep:
    ok = pair_status(score_w(w))
    rec = sum(1 for k in base_losses if ok[k])
    brk = sum(1 for k, o in base_ok.items() if o and not ok[k])
    print("  %.2f      %d           %d        %+d      %d/%d"
          % (w, rec, brk, rec-brk, sum(ok.values()), len(ok)))

# detail on the two target losses across the sweep
print("\n  Target-loss detail (T3 score must exceed T1 to recover):")
for v, nm in base_losses:
    lo, hi = "tier1_vatex_short", "tier3_va11y"
    row = "   %-26s" % v
    for w in [0.0, 0.1, 0.2, 0.3, 0.5]:
        s = score_w(w)
        row += " w%.1f:T1=%.2f/T3=%.2f%s" % (w, s[v][lo], s[v][hi],
                                             "(rec)" if s[v][hi] > s[v][lo] else "")
    print(row)
print("\nDone.")
