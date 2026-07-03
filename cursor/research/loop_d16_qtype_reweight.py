"""Loop D16 — Question-type-reweighted ADQA.

Question: can weighting each ADQA question's contribution by its question-type's
per-type reliability (D12 tier3-vs-tier0 AUC) improve the tier-ranking of the
ADQA score, or is equal-weight (parsimony) just as good?

Cached data only, Python stdlib only. Reuses the loader / join pattern from
cursor/research/loop_d11d12_triage_qtype.py and rank stats from
cursor/research/recompute_corrected_ladder.py.

Eval task: the SceneTwin tier ladder on the 20-clip timing set. For each clip we
have three (kept) description tiers T0 (cross-category decoy) < T1 (crowd caption)
< T3 (professional AD); tier2 (deprecated verbosity rung) is dropped. A good ADQA
score should rank these tiers correctly. We measure Spearman rho between the tier
order and the (equal-weight or reweighted) per-(clip,tier) ADQA score, pooled over
all (clip,tier) observations, pooled over the 8 cached ADQA variants (matching the
pool D12 used to derive the weights).
"""
import csv, os, random, math

ROOT = r"C:\Users\adars\Coding\scenetwin"
def p(*a): return os.path.join(ROOT, *a)

def readcsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

# ---- rank stats (stdlib) ----
def _ranks(xs):
    s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[s[j + 1]] == xs[s[i]]:
            j += 1
        for k in range(i, j + 1):
            r[s[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r

def _pearson(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((x - mb) ** 2 for x in b))
    return num / (da * db) if da and db else 0.0

def spearman(x, y):
    return _pearson(_ranks(x), _ranks(y))

def mean(x): return sum(x) / len(x) if x else float('nan')

OUT = []
def log(s=""):
    OUT.append(s); print(s)

# ---- tier ordering (drop deprecated verbosity rung) ----
DROP = "tier2_vatex_long"
ORDER = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier3_va11y": 2}

# ---- D12-derived per-type reliability weights (tier3-vs-tier0 AUC) ----
D12_AUC = {
    "action_relation": 0.959,
    "count":           0.920,
    "other":           0.917,
    "who_role":        0.899,
    "spatial_relation": 0.818,
    "object_attr":     0.811,
}
WEAKEST2 = {"spatial_relation", "object_attr"}

# ======================================================================
log("=" * 70)
log("D16  QUESTION-TYPE-REWEIGHTED ADQA")
log("=" * 70)

# ---- load question-type tags ----
qt = readcsv(p("cursor/output/scene_model_correctness_gap/adqa_question_types.csv"))
qtype = {}   # (source, video_id, q_idx) -> question_type
qsm = {}     # (source, video_id, q_idx) -> is_scene_model ('0'/'1')
for r in qt:
    key = (r['source'], r['video_id'], r['q_idx'])
    qtype[key] = r['question_type']
    qsm[key] = r['is_scene_model_question']

# ---- map question-type source path to its grades.csv ----
src2grades = {
 r"output\scenetwin_timing_20clip\adqa\adqa_questions.csv":
    "output/scenetwin_timing_20clip/adqa/adqa_grades.csv",
 r"output\scenetwin_timing_20clip\adqa_q-claude-haiku-4-5_g-claude-haiku-4-5\questions.csv":
    "output/scenetwin_timing_20clip/adqa_q-claude-haiku-4-5_g-claude-haiku-4-5/grades.csv",
 r"output\scenetwin_timing_20clip\adqa_q-claude-haiku-4-5_g-gpt-4o\questions.csv":
    "output/scenetwin_timing_20clip/adqa_q-claude-haiku-4-5_g-gpt-4o/grades.csv",
 r"output\scenetwin_timing_20clip\adqa_q-gpt-4o_g-claude-haiku-4-5\questions.csv":
    "output/scenetwin_timing_20clip/adqa_q-gpt-4o_g-claude-haiku-4-5/grades.csv",
 r"output\scenetwin_timing_20clip\adqa_q-gpt-4o_g-gpt-4o\questions.csv":
    "output/scenetwin_timing_20clip/adqa_q-gpt-4o_g-gpt-4o/grades.csv",
 r"output\scenetwin_timing_20clip\adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5\questions.csv":
    "output/scenetwin_timing_20clip/adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5/grades.csv",
 r"output\scenetwin_timing_20clip\adqa_v2\adqa_v2_questions.csv":
    "output/scenetwin_timing_20clip/adqa_v2/adqa_v2_grades.csv",
 r"output\scenetwin_timing_20clip\adqa_v4\adqa_v4_questions.csv":
    "output/scenetwin_timing_20clip/adqa_v4/adqa_v4_grades.csv",
}

# ---- gather graded question instances joined to type ----
# record: dict(variant, clip, tier, qtype, sm, score)
records = []
matched = unmatched = 0
missing = []
for src, gpath in src2grades.items():
    full = p(gpath)
    if not os.path.exists(full):
        missing.append(gpath); continue
    variant = os.path.basename(os.path.dirname(gpath))
    for g in readcsv(full):
        if g['tier'] == DROP:
            continue
        key = (src, g['video_id'], g['q_idx'])
        t = qtype.get(key)
        if t is None:
            unmatched += 1; continue
        try:
            sc = float(g['score'])
        except (ValueError, KeyError):
            continue
        matched += 1
        records.append({'variant': variant, 'clip': g['video_id'],
                        'tier': g['tier'], 'qtype': t,
                        'sm': qsm.get(key), 'score': sc})

log(f"joined graded instances (tier2 dropped): matched={matched}, "
    f"unmatched={unmatched}")
if missing:
    log(f"MISSING grades files: {missing}")
clips_all = sorted(set(r['clip'] for r in records))
log(f"coverage: {len(clips_all)} clips x 3 kept tiers, pooled over "
    f"{len(src2grades)} ADQA variants")
tcounts = {}
for r in records:
    tcounts[r['qtype']] = tcounts.get(r['qtype'], 0) + 1
log("question-type instance counts: " +
    ", ".join(f"{k}={v}" for k, v in sorted(tcounts.items(), key=lambda x: -x[1])))

# ======================================================================
# Weighted per-(clip,tier) ADQA score, then Spearman vs tier order.
# A "scheme" maps qtype -> weight (and optionally a scene-model filter).
# ======================================================================
def clip_tier_scores(recs, weight_fn):
    """Return dict[(clip,tier)] = weighted mean score (or None if no weight)."""
    num = {}; den = {}
    for r in recs:
        w = weight_fn(r)
        if w <= 0:
            continue
        k = (r['clip'], r['tier'])
        num[k] = num.get(k, 0.0) + w * r['score']
        den[k] = den.get(k, 0.0) + w
    return {k: num[k] / den[k] for k in num if den[k] > 0}

def rho_for_scheme(recs, weight_fn):
    cts = clip_tier_scores(recs, weight_fn)
    g = []; s = []
    for (clip, tier), sc in cts.items():
        g.append(ORDER[tier]); s.append(sc)
    return spearman(g, s), len(s), cts

# weight functions
schemes = {
    'equal (baseline)':      lambda r: 1.0,
    'linear AUC':            lambda r: D12_AUC[r['qtype']],
    'AUC^2':                 lambda r: D12_AUC[r['qtype']] ** 2,
    'AUC-0.5 (excess)':      lambda r: max(D12_AUC[r['qtype']] - 0.5, 0.0),
    'drop 2 weakest':        lambda r: 0.0 if r['qtype'] in WEAKEST2 else 1.0,
}

log("\n" + "-" * 70)
log("TASK 1+2: tier-ranking Spearman rho vs tier order (pooled clip,tier obs)")
log("-" * 70)
results = {}
base_cts = None
for name, fn in schemes.items():
    rho, n, cts = rho_for_scheme(records, fn)
    results[name] = (rho, n, cts)
    if name.startswith('equal'):
        base_cts = cts
    log(f"  {name:22s} rho={rho:+.4f}  (n_obs={n})")

base_rho = results['equal (baseline)'][0]
log(f"\n  baseline (equal-weight) rho = {base_rho:+.4f}")
log("  deltas vs equal-weight:")
for name in schemes:
    if name.startswith('equal'):
        continue
    log(f"    {name:22s} d_rho = {results[name][0]-base_rho:+.4f}")

# ======================================================================
# TASK 3: scene-model-only vs non-scene-model-only vs all
# ======================================================================
log("\n" + "-" * 70)
log("TASK 3: ablation by scene-model flag (equal weight within subset)")
log("-" * 70)
ablations = {
    'all questions':        lambda r: 1.0,
    'scene-model only':     lambda r: 1.0 if r['sm'] == '1' else 0.0,
    'non-scene-model only': lambda r: 1.0 if r['sm'] == '0' else 0.0,
}
abl_results = {}
for name, fn in ablations.items():
    rho, n, cts = rho_for_scheme(records, fn)
    abl_results[name] = (rho, n, cts)
    log(f"  {name:22s} rho={rho:+.4f}  (n_obs={n})")

# ======================================================================
# TASK 4: bootstrap over clips -> CI on rho and on delta vs equal-weight.
# permutation of tier labels within clip for baseline significance.
# ======================================================================
log("\n" + "-" * 70)
log("TASK 4: bootstrap (resample clips) CI on rho and on delta vs equal")
log("-" * 70)

# index records by clip for fast resampling
by_clip = {}
for r in records:
    by_clip.setdefault(r['clip'], []).append(r)
clips = sorted(by_clip)

def boot_rho(sample_clips, weight_fn):
    recs = []
    for c in sample_clips:
        recs.extend(by_clip[c])
    return rho_for_scheme(recs, weight_fn)[0]

def pct(sorted_vals, q):
    i = min(len(sorted_vals) - 1, max(0, int(q * len(sorted_vals))))
    return sorted_vals[i]

B = 5000
rng = random.Random(7)
# pre-generate resamples so rho and delta use the SAME resample
resamples = [[rng.choice(clips) for _ in clips] for _ in range(B)]

compare = {
    'linear AUC': schemes['linear AUC'],
    'AUC^2': schemes['AUC^2'],
    'drop 2 weakest': schemes['drop 2 weakest'],
    'scene-model only': ablations['scene-model only'],
    'non-scene-model only': ablations['non-scene-model only'],
}
base_fn = schemes['equal (baseline)']

log(f"  bootstrap B={B}, resample {len(clips)} clips with replacement (seed=7)")
# baseline rho CI
base_boot = sorted(boot_rho(s, base_fn) for s in resamples)
log(f"  equal-weight rho={base_rho:+.4f}  95% CI [{pct(base_boot,0.025):+.4f}, "
    f"{pct(base_boot,0.975):+.4f}]")

log("\n  scheme                 rho     d_rho   95% CI(d_rho)      P(d_rho>0)")
for name, fn in compare.items():
    obs_rho = (results.get(name) or abl_results.get(name))[0]
    d_obs = obs_rho - base_rho
    deltas = []
    for s in resamples:
        deltas.append(boot_rho(s, fn) - boot_rho(s, base_fn))
    deltas.sort()
    lo, hi = pct(deltas, 0.025), pct(deltas, 0.975)
    p_pos = sum(1 for d in deltas if d > 0) / len(deltas)
    log(f"  {name:22s} {obs_rho:+.4f} {d_obs:+.4f}  [{lo:+.4f}, {hi:+.4f}]   {p_pos:.3f}")

# permutation test: is baseline rho itself meaningful? shuffle tier labels within clip
log("\n  permutation null for equal-weight rho (shuffle tier labels within clip):")
base_cts = results['equal (baseline)'][2]
# build per-clip tier->score map
clip_tier_val = {}
for (clip, tier), sc in base_cts.items():
    clip_tier_val.setdefault(clip, {})[tier] = sc
obs = base_rho
rngp = random.Random(11)
NP = 20000; ge = 0
tier_keys = list(ORDER)
for _ in range(NP):
    g = []; s = []
    for clip, tv in clip_tier_val.items():
        present = [t for t in tier_keys if t in tv]
        labs = [ORDER[t] for t in present]
        rngp.shuffle(labs)
        for i, t in enumerate(present):
            g.append(labs[i]); s.append(tv[t])
    if spearman(g, s) >= obs:
        ge += 1
perm_p = (ge + 1) / (NP + 1)
log(f"    equal-weight rho={obs:+.4f}, within-clip label-perm p={perm_p:.5f} "
    f"({NP} perms)")

# ======================================================================
# Per-variant robustness: rho for equal vs best reweight, per variant
# ======================================================================
log("\n" + "-" * 70)
log("ROBUSTNESS: per-variant rho (equal vs linear-AUC vs drop-2-weakest)")
log("-" * 70)
variants = sorted(set(r['variant'] for r in records))
log(f"  {'variant':44s} {'equal':>7s} {'linAUC':>7s} {'drop2':>7s}")
for v in variants:
    vr = [r for r in records if r['variant'] == v]
    re, _, _ = rho_for_scheme(vr, schemes['equal (baseline)'])
    rl, _, _ = rho_for_scheme(vr, schemes['linear AUC'])
    rd, _, _ = rho_for_scheme(vr, schemes['drop 2 weakest'])
    log(f"  {v:44s} {re:+.4f} {rl:+.4f} {rd:+.4f}")

log("\nDONE.")

# persist console log
outdir = p("cursor/research/output")
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, "loop_d16_console.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))
