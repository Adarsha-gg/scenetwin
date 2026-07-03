"""Loop D11+D12 — combined triage-queue fusion (D11) and ADQA question-type
reliability (D12). Cached data only, Python stdlib only.

Reuses AUC / permutation helper patterns from cursor/research/new_directions_run.py.
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

def ranks(vals, direction):
    """Average-rank of vals so that HIGHER rank == higher predicted risk.
    direction 'high' -> larger value is riskier; 'low' -> smaller value riskier."""
    order = vals if direction == 'high' else [-v for v in vals]
    idx = sorted(range(len(order)), key=lambda i: order[i])
    r = [0.0] * len(order)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and order[idx[j + 1]] == order[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r

def recall_at_budget(scores, labels, frac, direction='high'):
    """Recall of positives among the top `frac` fraction of clips (highest risk)."""
    n = len(scores)
    k = max(1, round(frac * n))
    sgn = 1 if direction == 'high' else -1
    order = sorted(range(n), key=lambda i: sgn * scores[i], reverse=True)
    top = order[:k]
    npos = sum(labels)
    hit = sum(labels[i] for i in top)
    return hit, npos, k, hit / npos if npos else float('nan')

OUT = []
def log(s=""):
    OUT.append(s); print(s)

# ======================================================================
log("=" * 70)
log("D11  COMBINED REVIEW-TRIAGE QUEUE (fuse cached signals vs single best)")
log("=" * 70)
ef = readcsv(p("cursor/research/output/parallel_research/cheap_baselines/external_features.csv"))
labels = [int(r['adqa_fail']) for r in ef]
N = len(ef); NPOS = sum(labels)
log(f"n={N} clips, positives(adqa_fail)={NPOS}")

# candidate signals to consider for fusion
feats = ['accessibility_gap', 'mean_visual_gap', 'max_visual_gap',
         'mean_scene_spatial_gap', 'mean_agent_action_gap', 'description_loss',
         'alignment_loss', 'tier3_word_count', 'tier3_words_per_sec',
         'transcript_word_count', 'transcript_words_per_sec',
         'transcript_unique_ratio', 'transcript_sound_cue_count',
         'category_loo_adqa_fail_rate']
col = {f: [float(r[f]) for r in ef] for f in feats}
indiv = {}
log("\nIndividual feature AUC (best direction):")
for f in feats:
    a, d = best_auc(col[f], labels)
    indiv[f] = (a, d)
    log(f"  {f:28s} AUC={a:.3f} ({d})")

# baseline: accessibility_gap alone (leakage-free note below)
acc = col['accessibility_gap']
acc_auc, acc_dir = best_auc(acc, labels)
acc_p, _ = perm_p(acc, labels, n=20000)
log(f"\naccessibility_gap ALONE: AUC={acc_auc:.3f} ({acc_dir}), label-perm p={acc_p:.4f}")

# ---- Fusions ----
# NOTE: category_loo_adqa_fail_rate is a label-derived leave-one-out feature
# (built from the ADQA labels themselves); we keep it OUT of the honest fusion
# to avoid label leakage, but report a leaky variant separately for context.
neural = ['accessibility_gap', 'mean_visual_gap', 'max_visual_gap',
          'mean_scene_spatial_gap', 'mean_agent_action_gap']
cheap_clean = ['description_loss', 'alignment_loss', 'tier3_word_count',
               'tier3_words_per_sec', 'transcript_words_per_sec',
               'transcript_unique_ratio']

def rank_fuse(feature_list):
    aligned = [ranks(col[f], indiv[f][1]) for f in feature_list]
    return [sum(vals) for vals in zip(*aligned)]

def z(vals):
    m = mean(vals)
    sd = (sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5 or 1.0
    return [(x - m) / sd for x in vals]

def zsum_fuse(feature_list):
    aligned = []
    for f in feature_list:
        zz = z(col[f])
        aligned.append(zz if indiv[f][1] == 'high' else [-v for v in zz])
    return [sum(vals) for vals in zip(*aligned)]

# pick the best complementary partners by individual AUC (excluding acc itself
# and the leaky loo feature)
partners = sorted([f for f in feats if f not in ('accessibility_gap',
                  'category_loo_adqa_fail_rate')],
                  key=lambda f: -indiv[f][0])
log("\nTop non-leaky partner features by individual AUC:")
for f in partners[:5]:
    log(f"  {f:28s} AUC={indiv[f][0]:.3f}")

log("\nFusion candidates (rank-average, direction-aligned):")
fusion_defs = {
    'acc+best_partner': ['accessibility_gap', partners[0]],
    'acc+top2': ['accessibility_gap'] + partners[:2],
    'acc+top3': ['accessibility_gap'] + partners[:3],
    'acc+all_neural': neural,
    'acc+neural+cheap': list(dict.fromkeys(neural + cheap_clean)),
}
fusion_results = {}
for name, fl in fusion_defs.items():
    fs = rank_fuse(fl)
    a, d = best_auc(fs, labels)
    fusion_results[name] = (a, fl, fs, d)
    log(f"  {name:20s} AUC={a:.3f}   [{', '.join(fl)}]")

# z-score-sum variant of the best rank fusion
best_name = max(fusion_results, key=lambda k: fusion_results[k][0])
best_auc_val, best_fl, best_fs, best_d = fusion_results[best_name]
zfs = zsum_fuse(best_fl)
za, zd = best_auc(zfs, labels)
log(f"\nBest rank-fusion = '{best_name}' AUC={best_auc_val:.3f}")
log(f"  same features via z-score-sum: AUC={za:.3f}")

# permutation p for the best fusion
fus_p, _ = perm_p(best_fs, labels, n=20000)
log(f"  best-fusion label-perm p={fus_p:.4f}")
log(f"  delta vs accessibility_gap alone: {best_auc_val - acc_auc:+.3f} AUC")

# leaky context: include the loo feature
leaky = rank_fuse(['accessibility_gap', 'category_loo_adqa_fail_rate'] + partners[:2])
la, ld = best_auc(leaky, labels)
log(f"\n(context, LEAKY) acc+category_loo+top2 rank-fusion AUC={la:.3f} "
    f"(category_loo is label-derived; not a fair comparison)")

# ---- Recall at review budgets ----
log("\nRecall of ADQA failures at review budgets (top X% highest-risk clips):")
log(f"{'budget':>7s} | {'k':>3s} | {'acc_gap':>18s} | {'fusion('+best_name+')':>22s} | {'random(exp)':>11s}")
for frac in (0.10, 0.20, 0.30):
    h_a, npos, k, r_a = recall_at_budget(acc, labels, frac, acc_dir)
    h_f, _, _, r_f = recall_at_budget(best_fs, labels, frac, best_d)
    rand_r = k * (NPOS / N) / NPOS  # == k/N
    log(f"{frac*100:5.0f}% | {k:3d} | {h_a:2d}/{npos} recall={r_a:.2f} | "
        f"{h_f:2d}/{npos} recall={r_f:.2f} | {rand_r:.2f}")

# ======================================================================
log("\n" + "=" * 70)
log("D12  QUESTION-TYPE ADQA RELIABILITY")
log("=" * 70)
qt = readcsv(p("cursor/output/scene_model_correctness_gap/adqa_question_types.csv"))

# map each question_types 'source' path (backslash) to its grades.csv path
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

# type lookup: (source, video_id, q_idx) -> question_type
qtype = {}
for r in qt:
    qtype[(r['source'], r['video_id'], r['q_idx'])] = r['question_type']

log(f"question_types.csv: {len(qt)} tagged questions across {len(src2grades)} variants")

# gather graded instances tagged with a question type, pooled across variants
# each record: (question_type, tier, score)
records = []
matched = 0; unmatched = 0
missing_files = []
for src, gpath in src2grades.items():
    full = p(gpath)
    if not os.path.exists(full):
        missing_files.append(gpath); continue
    grades = readcsv(full)
    for g in grades:
        key = (src, g['video_id'], g['q_idx'])
        t = qtype.get(key)
        if t is None:
            unmatched += 1; continue
        matched += 1
        try:
            sc = float(g['score'])
        except (ValueError, KeyError):
            continue
        records.append((t, g['tier'], sc))

log(f"joined graded instances: matched={matched}, unmatched(q_idx not in types)={unmatched}")
if missing_files:
    log(f"MISSING grades files: {missing_files}")

# per question-type: overall yes-rate (mean score), tier0 vs tier3 means,
# discrimination (tier3-tier0), and AUC(tier3 vs tier0) using score
types = sorted(set(t for t, _, _ in records))
log("\nPer question-type reliability (pooled over all 8 ADQA variants):")
log(f"{'type':18s} {'n':>4s} {'yes%':>6s} {'T0':>6s} {'T1':>6s} {'T3':>6s} "
    f"{'T3-T0':>7s} {'AUC(T3vsT0)':>12s}")
type_rows = []
for t in types:
    recs = [r for r in records if r[0] == t]
    allsc = [s for _, _, s in recs]
    t0 = [s for _, tier, s in recs if tier == 'tier0_cross']
    t1 = [s for _, tier, s in recs if tier == 'tier1_vatex_short']
    t3 = [s for _, tier, s in recs if tier == 'tier3_va11y']
    disc = (mean(t3) - mean(t0)) if (t3 and t0) else float('nan')
    a = auc(t3, t0) if (t3 and t0) else float('nan')
    type_rows.append((t, len(recs), mean(allsc), mean(t0), mean(t1), mean(t3), disc, a))
    log(f"{t:18s} {len(recs):4d} {mean(allsc)*100:5.0f}% {mean(t0):6.2f} "
        f"{mean(t1):6.2f} {mean(t3):6.2f} {disc:+7.2f} {a:12.3f}")

# scene-model vs non-scene-model rollup
sm_keys = {(r['source'], r['video_id'], r['q_idx']): r['is_scene_model_question']
           for r in qt}
sm_recs = {'1': [], '0': []}
for src, gpath in src2grades.items():
    full = p(gpath)
    if not os.path.exists(full): continue
    for g in readcsv(full):
        k = (src, g['video_id'], g['q_idx'])
        flag = sm_keys.get(k)
        if flag is None: continue
        try: sc = float(g['score'])
        except (ValueError, KeyError): continue
        sm_recs[flag].append((g['tier'], sc))
log("\nScene-model vs non-scene-model questions (discrimination T3 vs T0):")
for flag, name in (('1', 'scene-model'), ('0', 'non-scene-model')):
    recs = sm_recs[flag]
    t0 = [s for tier, s in recs if tier == 'tier0_cross']
    t3 = [s for tier, s in recs if tier == 'tier3_va11y']
    a = auc(t3, t0) if (t0 and t3) else float('nan')
    log(f"  {name:16s} n={len(recs):4d}  T0={mean(t0):.2f} T3={mean(t3):.2f} "
        f"T3-T0={mean(t3)-mean(t0):+.2f} AUC={a:.3f}")

log("\nDONE.")

# persist raw log for the report writer
with open(p("cursor/research/output", "loop_d11d12_console.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(OUT))
