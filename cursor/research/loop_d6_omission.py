"""D6 — Reference-free OMISSION SCORER (stdlib only, cached data).

Omission score for an AD = fraction of a clip's key visual facts (probed
true_answer terms) that the AD does NOT mention. The cached *_ad_mentions_true
fields provide the ground-truth "mentioned" signal. We also build an
independent, purely lexical mention detector and test whether it reproduces the
cached truth_ad_mentions_true labels.

Reuses the AUC / permutation / mean helper patterns from
cursor/research/new_directions_run.py.
"""
import csv, os, random, re

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

# ----------------------------------------------------------------------
probes = readcsv(p("cursor/output/relational_hallucination_probe_set/probes.csv"))
hg = readcsv(p("cursor/output/halluc_gate/halluc_gate.csv"))
hg_by_id = {r['video_id']: r for r in hg}

clips = sorted(set(r['video_id'] for r in probes))
print("=" * 70)
print("D6  REFERENCE-FREE OMISSION SCORER")
print("=" * 70)
print(f"probes = {len(probes)}  clips = {len(clips)}  "
      f"(all present in halluc_gate: {all(v in hg_by_id for v in clips)})")

# ----------------------------------------------------------------------
# TASK 1 — omission from cached mention labels
# probe-level omission = 1 - mentions_true (fact NOT stated by the AD)
# clip-level omission   = fraction of that clip's probed facts omitted
# ----------------------------------------------------------------------
print("\n" + "-" * 70)
print("TASK 1  Omission from cached *_ad_mentions_true labels")
print("-" * 70)

expert_om_probe = [1 - int(r['truth_ad_mentions_true']) for r in probes]
halluc_om_probe = [1 - int(r['halluc_ad_mentions_true']) for r in probes]

print(f"Probe-level omission rate  expert AD  = "
      f"{mean(expert_om_probe):.3f} ({sum(expert_om_probe)}/{len(probes)})")
print(f"Probe-level omission rate  halluc AD  = "
      f"{mean(halluc_om_probe):.3f} ({sum(halluc_om_probe)}/{len(probes)})")

# per-clip omission (fraction of that clip's facts omitted)
clip_expert_om = {}; clip_halluc_om = {}
for v in clips:
    rows = [r for r in probes if r['video_id'] == v]
    clip_expert_om[v] = mean([1 - int(r['truth_ad_mentions_true']) for r in rows])
    clip_halluc_om[v] = mean([1 - int(r['halluc_ad_mentions_true']) for r in rows])
print(f"Clip-level omission rate   expert AD  = {mean(list(clip_expert_om.values())):.3f}")
print(f"Clip-level omission rate   halluc AD  = {mean(list(clip_halluc_om.values())):.3f}")

# ----------------------------------------------------------------------
# TASK 3a — omission by probe_type
# ----------------------------------------------------------------------
print("\n" + "-" * 70)
print("TASK 3a  Omission rate by probe_type (probe-level)")
print("-" * 70)
by_type = {}
for r in probes:
    t = r['probe_type']
    d = by_type.setdefault(t, {'n': 0, 'exp_om': 0, 'hal_om': 0})
    d['n'] += 1
    d['exp_om'] += 1 - int(r['truth_ad_mentions_true'])
    d['hal_om'] += 1 - int(r['halluc_ad_mentions_true'])
print(f"{'probe_type':16s} {'n':>3s} {'expert_omit':>12s} {'halluc_omit':>12s}")
for t, d in sorted(by_type.items(), key=lambda x: -x[1]['n']):
    print(f"{t:16s} {d['n']:>3d} "
          f"{d['exp_om']/d['n']:>11.1%} {d['hal_om']/d['n']:>11.1%}")

# ----------------------------------------------------------------------
# TASK 3b — does omission separate expert (neg) from hallucinated (pos)?
# hallucinated = higher-omission positive.  Pool all probe-level scores.
# ----------------------------------------------------------------------
print("\n" + "-" * 70)
print("TASK 3b  Does omission separate expert vs hallucinated ADs? (AUC)")
print("-" * 70)
scores = expert_om_probe + halluc_om_probe          # 0/1 omission
labels = [0] * len(expert_om_probe) + [1] * len(halluc_om_probe)  # 1 = halluc
a_probe = auc(halluc_om_probe, expert_om_probe)
pval, _ = perm_p(scores, labels, n=20000, seed=0)
print(f"Probe-level  AUC(halluc>expert) = {a_probe:.3f}  "
      f"(perm best-dir p = {pval:.4f}, n=20000)")
# clip-level (paired distributions)
ce = list(clip_expert_om.values()); ch = list(clip_halluc_om.values())
a_clip = auc(ch, ce)
print(f"Clip-level   AUC(halluc>expert) = {a_clip:.3f}")
paired_worse = sum(1 for v in clips if clip_halluc_om[v] > clip_expert_om[v])
paired_tie = sum(1 for v in clips if clip_halluc_om[v] == clip_expert_om[v])
print(f"Clips where halluc AD omits MORE than expert: "
      f"{paired_worse}/{len(clips)}  (ties {paired_tie})")

# ----------------------------------------------------------------------
# TASK 2 — independent lexical mention-detector vs cached labels
# Purely reference-free: does the true_answer appear in the AD text?
#   detector A: lowercase substring of the whole true_answer phrase
#   detector B: content-token overlap >= 50% of true_answer tokens
# Compare each against cached truth_ad_mentions_true.
# ----------------------------------------------------------------------
print("\n" + "-" * 70)
print("TASK 2  Independent lexical detector vs cached truth_ad_mentions_true")
print("-" * 70)

STOP = {'a', 'an', 'the', 'of', 'on', 'in', 'at', 'to', 'and', 'or', 'with',
        'is', 'are', 'be', 'that', 'for', 'into', 'onto', 'up', 'down', 'by',
        'as', 'his', 'her', 'their', 'its', 'it', 'they'}

def toks(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]

def detect_substring(answer, text):
    return int(answer.lower().strip() in text.lower())

def detect_overlap(answer, text, thresh=0.5):
    at = toks(answer)
    if not at: return 0
    tt = set(toks(text))
    hit = sum(1 for w in at if w in tt)
    return int(hit / len(at) >= thresh)

# evaluate on expert_text (truth AD)
agree_sub = agree_ov = 0
sub_tp = sub_fp = sub_fn = sub_tn = 0
ov_tp = ov_fp = ov_fn = ov_tn = 0
lex_expert_om = {v: [] for v in clips}   # lexical omission per clip (overlap det)
for r in probes:
    txt = hg_by_id[r['video_id']]['expert_text']
    cached = int(r['truth_ad_mentions_true'])
    ds = detect_substring(r['true_answer'], txt)
    do = detect_overlap(r['true_answer'], txt)
    agree_sub += (ds == cached)
    agree_ov += (do == cached)
    # confusion (positive = mentioned)
    if cached and ds: sub_tp += 1
    elif cached and not ds: sub_fn += 1
    elif not cached and ds: sub_fp += 1
    else: sub_tn += 1
    if cached and do: ov_tp += 1
    elif cached and not do: ov_fn += 1
    elif not cached and do: ov_fp += 1
    else: ov_tn += 1
    lex_expert_om[r['video_id']].append(1 - do)

n = len(probes)
print(f"Detector A (substring)       agreement with cached = "
      f"{agree_sub/n:.1%} ({agree_sub}/{n})")
print(f"   confusion vs cached(mentioned=1): TP={sub_tp} FP={sub_fp} "
      f"FN={sub_fn} TN={sub_tn}")
print(f"Detector B (>=50% tok overlap) agreement with cached = "
      f"{agree_ov/n:.1%} ({agree_ov}/{n})")
print(f"   confusion vs cached(mentioned=1): TP={ov_tp} FP={ov_fp} "
      f"FN={ov_fn} TN={ov_tn}")

# does the lexical omission score ALSO separate expert vs halluc? (build halluc lexical)
lex_halluc_om_probe = []
lex_expert_om_probe = []
for r in probes:
    et = hg_by_id[r['video_id']]['expert_text']
    ht = hg_by_id[r['video_id']]['halluc_text']
    lex_expert_om_probe.append(1 - detect_overlap(r['true_answer'], et))
    lex_halluc_om_probe.append(1 - detect_overlap(r['true_answer'], ht))
a_lex = auc(lex_halluc_om_probe, lex_expert_om_probe)
print(f"Lexical omission (overlap) AUC(halluc>expert) = {a_lex:.3f}  "
      f"[expert lex-omit {mean(lex_expert_om_probe):.3f} vs "
      f"halluc {mean(lex_halluc_om_probe):.3f}]")

# ----------------------------------------------------------------------
# TASK 4 — omission vs fabrication separability
# The foil AD states the FALSE fact (halluc_ad_mentions_foil): a fabrication.
# ----------------------------------------------------------------------
print("\n" + "-" * 70)
print("TASK 4  Omission vs fabrication (are they separable here?)")
print("-" * 70)
hal_true = sum(int(r['halluc_ad_mentions_true']) for r in probes)
hal_foil = sum(int(r['halluc_ad_mentions_foil']) for r in probes)
exp_foil = sum(int(r['truth_ad_mentions_foil']) for r in probes)
print(f"Halluc AD states the TRUE fact  : {hal_true}/{n} = {hal_true/n:.1%} "
      f"(=> omits it {1-hal_true/n:.1%})")
print(f"Halluc AD states the FALSE foil  : {hal_foil}/{n} = {hal_foil/n:.1%} "
      f"(= fabrication)")
print(f"Expert AD states the FALSE foil  : {exp_foil}/{n} = {exp_foil/n:.1%}")
# how often is the halluc failure an omission-only vs fabrication?
om_only = sum(1 for r in probes
              if int(r['halluc_ad_mentions_true']) == 0
              and int(r['halluc_ad_mentions_foil']) == 0)
fab = sum(1 for r in probes if int(r['halluc_ad_mentions_foil']) == 1)
both_ok = sum(1 for r in probes if int(r['halluc_ad_mentions_true']) == 1)
print(f"Halluc probe breakdown: fabrication(states foil)={fab}  "
      f"silent-omission(neither)={om_only}  states-true={both_ok}  (n={n})")
