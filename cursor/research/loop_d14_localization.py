"""D14 — Claim/sentence-level error LOCALIZATION (reference-free), stdlib only.

Prior rounds detect AD errors at the CLIP level (AUC 0.835-0.945). This asks a
harder, deployment-relevant question: can we point to WHICH sentence/claim is
wrong, using only reference-free lexical signals + cached ground truth?

Data (cached, no API/GPU/network):
  cursor/output/halluc_gate/halluc_gate.csv         expert/halluc/para AD text
  cursor/output/relational_hallucination_probe_set/probes.csv  swap spans true->foil

Tasks:
  1. Sentence-align expert vs halluc; find the changed sentence(s) = GT location.
  2. Reference-free localizer: score each candidate sentence by a TEXT-ONLY
     suspicion signal (no per-sentence visual grounding is cached). Top-1 acc
     vs random-sentence baseline.
  3. Reference-COMPARISON check via probes: does foil appear in halluc & true in
     expert (swap lexically localizable)? Establishes the with-reference ceiling.
  4. Honest verdict + what is BLOCKED (per-sentence CLIP/ADQA visual grounding).
"""
import csv, os, re, random

ROOT = r"C:\Users\adars\Coding\scenetwin"
def p(*a): return os.path.join(ROOT, *a)
def readcsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))
def mean(x): return sum(x)/len(x) if x else float('nan')

# ---- text helpers ----------------------------------------------------------
_SENT = re.compile(r'[^.!?]+[.!?]?')
def sents(t):
    return [s.strip() for s in _SENT.findall(t or "") if s.strip()]
_WORD = re.compile(r"[a-z0-9']+")
def toks(s): return _WORD.findall(s.lower())
def norm(s): return " ".join(toks(s))

STOP = set("a an the of in on at to and or but with without into onto is are was "
           "were be been being he she it they them his her their its him as by for "
           "from that this these those who whom which what where when while over "
           "under near next then so then also both each other another one two some "
           "creating filled focusing".split())

hg = readcsv(p("cursor/output/halluc_gate/halluc_gate.csv"))
probes = readcsv(p("cursor/output/relational_hallucination_probe_set/probes.csv"))
N = len(hg)
print("="*72)
print("D14  CLAIM/SENTENCE-LEVEL ERROR LOCALIZATION (reference-free)")
print("="*72)
print(f"clips in halluc_gate = {N} | probe rows = {len(probes)}")

# ---- Task 1: sentence alignment & ground-truth changed sentences -----------
print("\n"+"-"*72)
print("TASK 1  Sentence alignment (expert vs halluc) -> GT changed sentence(s)")
print("-"*72)
records = []          # per clip: dict with sentences + changed index set
alignable = 0
mismatch = 0
for r in hg:
    es, hs = sents(r['expert_text']), sents(r['halluc_text'])
    rec = {'vid': r['video_id'], 'es': es, 'hs': hs}
    if len(es) == len(hs) and len(es) >= 2:
        alignable += 1
        changed = {i for i in range(len(es)) if norm(es[i]) != norm(hs[i])}
        rec['aligned'] = True
        rec['changed'] = changed
        rec['nsent'] = len(es)
    else:
        rec['aligned'] = False
        rec['changed'] = set()
        rec['nsent'] = len(hs)
        mismatch += 1
    records.append(rec)

al = [r for r in records if r['aligned']]
nch = [len(r['changed']) for r in al]
zero_change = sum(1 for c in nch if c == 0)
print(f"cleanly alignable clips (equal sentence count, >=2 sents): {alignable}/{N}")
print(f"  positional-mismatch clips (unequal counts): {mismatch}/{N}")
print(f"  mean sentences/clip (alignable): {mean([r['nsent'] for r in al]):.2f}"
      f"  | mean changed sentences/clip: {mean(nch):.2f}")
print(f"  clips with 0 detected changed sentences: {zero_change}/{alignable}"
      "  (swap collapsed under normalization)")
dist = {}
for c in nch: dist[c] = dist.get(c, 0) + 1
print("  distribution of #changed sentences: "
      + ", ".join(f"{k}->{dist[k]}" for k in sorted(dist)))

# usable localization set = alignable clips with >=1 changed sentence
LOC = [r for r in al if len(r['changed']) >= 1]
print(f"  => localization-usable clips (>=1 changed sentence): {len(LOC)}")

# ---- Task 2: reference-free (text-only) localizer --------------------------
print("\n"+"-"*72)
print("TASK 2  Reference-free localizer  (TEXT-ONLY; no per-sentence grounding)")
print("-"*72)
# Background document frequency over ALL halluc sentences (reference-free:
# uses only candidate-side text + a background corpus, never the expert AD).
allhs = [s for r in records for s in r['hs']]
df = {}
for s in allhs:
    for w in set(toks(s)):
        df[w] = df.get(w, 0) + 1
import math
D = len(allhs)
def idf(w): return math.log((D + 1) / (df.get(w, 0) + 1)) + 1.0

def content(s): return [w for w in toks(s) if w not in STOP and len(w) > 2]

def sig_len(s):      return len(toks(s))
def sig_content(s):  return len(content(s))
def sig_sumidf(s):   return sum(idf(w) for w in content(s))
def sig_meanidf(s):
    c = content(s); return mean([idf(w) for w in c]) if c else 0.0
def sig_maxidf(s):
    c = content(s); return max((idf(w) for w in c), default=0.0)
def sig_num(s):      return sum(1 for w in toks(s) if w.isdigit())

SIGS = {
    'sentence_length':   sig_len,
    'content_word_count':sig_content,
    'sum_idf(specificity)': sig_sumidf,
    'mean_idf(rarity)':  sig_meanidf,
    'max_idf(rarest)':   sig_maxidf,
    'numeral_count':     sig_num,
}

def top1_acc(scorer):
    """top-1: highest-suspicion candidate sentence is a changed sentence."""
    hits = 0
    for r in LOC:
        scores = [scorer(s) for s in r['hs']]
        # argmax; ties -> first (deterministic)
        best = max(range(len(scores)), key=lambda i: (scores[i], -i))
        if best in r['changed']: hits += 1
    return hits/len(LOC)

# random baseline: expected top-1 accuracy = mean(#changed / #sentences)
rand_base = mean([len(r['changed'])/r['nsent'] for r in LOC])
# POSITIONAL baselines (no content signal at all) -- the honest control:
def pos_acc(pick):
    hits = 0
    for r in LOC:
        k = 0 if pick=='first' else (r['nsent']-1 if pick=='last'
             else min(1, r['nsent']-1))
        if k in r['changed']: hits += 1
    return hits/len(LOC)
first_changed = sum(1 for r in LOC if 0 in r['changed'])
last_changed  = sum(1 for r in LOC if (r['nsent']-1) in r['changed'])
print(f"localization set n={len(LOC)}  (each: pick 1 of {mean([r['nsent'] for r in LOC]):.1f} sentences)")
print(f"random-sentence baseline top-1 acc = {rand_base:.3f}")
print("STRUCTURAL controls (position only, NO error signal):")
print(f"  opening (1st) sentence is changed: {first_changed}/{len(LOC)}"
      f"  |  closing (last) sentence changed: {last_changed}/{len(LOC)}"
      "  (last = mood/atmosphere boilerplate, rarely swapped)")
print(f"  'always pick FIRST sentence' top-1 = {pos_acc('first'):.3f}")
print(f"  'always pick sentence #2'     top-1 = {pos_acc('idx1'):.3f}")
print(f"  'always pick LAST sentence'   top-1 = {pos_acc('last'):.3f}")
print("reference-free CONTENT signal top-1 accuracy:")
best_name, best_acc = None, -1
for name, fn in SIGS.items():
    a = top1_acc(fn)
    lift = a - rand_base
    print(f"  {name:22s} top-1={a:.3f}  (lift vs random {lift:+.3f})")
    if a > best_acc: best_name, best_acc = name, a
pos_first = pos_acc('first')
print(f"best content signal: {best_name} = {best_acc:.3f}  |  "
      f"'pick-first' structural prior = {pos_first:.3f}  =>  "
      f"content lift over structure = {best_acc-pos_first:+.3f}")
print("  INTERPRETATION: the content signal does NOT beat a trivial positional")
print("  prior. It selects the densest sentence, which coincides with the opening")
print("  scene-setting sentence where swaps are injected -- not error-specific.")

# permutation test: is best signal's top-1 better than random assignment?
def perm_top1(scorer, n=20000, seed=0):
    rng = random.Random(seed)
    obs = top1_acc(scorer)
    ge = 0
    for _ in range(n):
        hits = 0
        for r in LOC:
            k = rng.randrange(r['nsent'])
            if k in r['changed']: hits += 1
        if hits/len(LOC) >= obs: ge += 1
    return (ge+1)/(n+1), obs
pv, obs = perm_top1(SIGS[best_name])
print(f"permutation p(best signal >= random draws) = {pv:.4f}")

# ---- Task 3: reference-COMPARISON localizability via probe swaps -----------
print("\n"+"-"*72)
print("TASK 3  Reference-COMPARISON ceiling: is the swap lexically localizable?")
print("-"*72)
hg_by_id = {r['video_id']: r for r in hg}
n_probe = 0
foil_sub = true_in_e = both_sub = 0               # strict substring
foil_tok = 0                                      # token-containment (>=1 content tok)
cache_foil_in_h = cache_true_in_e = cache_clean = 0  # cached probe labels
per_type = {}
def ctoks(s): return set(w for w in toks(s) if w not in STOP and len(w) > 2)
for pr in probes:
    vid = pr['video_id']
    if vid not in hg_by_id: continue
    sw = pr.get('swap_text', '')
    if '->' not in sw: continue
    true_p, foil_p = [x.strip().lower() for x in sw.split('->', 1)]
    if not true_p or not foil_p: continue
    n_probe += 1
    et = hg_by_id[vid]['expert_text'].lower()
    ht = hg_by_id[vid]['halluc_text'].lower()
    f_sub = foil_p in ht                      # exact phrase
    t_in_e = true_p in et
    ftoks = ctoks(foil_p)
    f_tok = bool(ftoks & ctoks(ht))           # any foil content token in halluc
    if f_sub: foil_sub += 1
    if t_in_e: true_in_e += 1
    if f_sub and t_in_e: both_sub += 1
    if f_tok: foil_tok += 1
    # cached mention labels (fuzzy token-overlap, as generated)
    cf = int(pr['halluc_ad_mentions_foil']); ct = int(pr['truth_ad_mentions_true'])
    cth = int(pr['halluc_ad_mentions_true'])
    cache_foil_in_h += cf; cache_true_in_e += ct
    if cf and ct and not cth: cache_clean += 1
    t = pr['probe_type']
    d = per_type.setdefault(t, {'n':0,'clean':0})
    d['n'] += 1
    if cf and ct and not cth: d['clean'] += 1

print(f"probes with clip present & parseable swap: {n_probe}")
print("NOTE: probe swap_text foils are QA DISTRACTORS, not the literal text swap.")
print("  e.g. clip pottery: swap_text 'vase->clay jar' but the injected text edit")
print("  is vase->'clay bowl'. So exact foil-phrase substring is near-zero; the")
print("  right signal is token-overlap (and the literal edit = Task-1 diff).")
print("Strict exact-substring on the AD text:")
print(f"  foil PHRASE in halluc_text : {foil_sub}/{n_probe} = {foil_sub/n_probe:.1%}  (distractors are paraphrastic)")
print(f"  true PHRASE in expert_text : {true_in_e}/{n_probe} = {true_in_e/n_probe:.1%}")
print(f"  both exact                 : {both_sub}/{n_probe} = {both_sub/n_probe:.1%}")
print("Token-overlap (>=1 foil content token in halluc):")
print(f"  foil token in halluc_text  : {foil_tok}/{n_probe} = {foil_tok/n_probe:.1%}")
print("Cached probe mention labels (fuzzy, as originally generated):")
print(f"  halluc_ad_mentions_foil : {cache_foil_in_h}/{n_probe} = {cache_foil_in_h/n_probe:.1%}")
print(f"  truth_ad_mentions_true  : {cache_true_in_e}/{n_probe} = {cache_true_in_e/n_probe:.1%}")
print(f"  cached clean swap (foil in H, true in E, true NOT in H): {cache_clean}/{n_probe} = {cache_clean/n_probe:.1%}")
print("by probe type (cached clean-swap rate):")
for t, d in sorted(per_type.items(), key=lambda x:-x[1]['n']):
    print(f"  {t:16s} n={d['n']:2d}  clean {d['clean']}/{d['n']} = {d['clean']/d['n']:.0%}")

# bridge to Task 1: does the reference-comparison localizer (exact alignment diff)
# recover the changed sentence for every alignable clip? (= 100% by construction
# when >=1 sentence differs). Report as the with-reference ceiling.
print("\nReference-comparison sentence localizer (exact alignment diff):")
print(f"  recovers a changed sentence for {len(LOC)}/{len(LOC)} alignable clips = 100% "
      "(trivially, given a trusted reference AD).")

# ---- Task 4: verdict -------------------------------------------------------
print("\n"+"="*72)
print("TASK 4  VERDICT")
print("="*72)
print(f"- Reference-free text-only top-1 = {best_acc:.3f} vs random {rand_base:.3f}, BUT")
print(f"  a trivial 'pick-first-sentence' prior scores {pos_first:.3f} (tie). The")
print("  content signal adds ~0 error-specific information -> reference-free")
print("  claim-level localization is NOT demonstrated on this data.")
print("- Reference-COMPARISON is the working path: sentence-alignment diff recovers")
print(f"  a changed sentence for {len(LOC)}/{len(LOC)} clips = 100% (exact, given a trusted AD).")
print(f"- Probe swaps are QA distractors (exact foil-in-halluc {foil_sub/n_probe:.0%}); "
      f"cached fuzzy clean-swap rate {cache_clean/n_probe:.0%}. Use the alignment diff,")
print("  not the probe foils, as the literal localization ground truth.")
print("- BLOCKED: a genuine ZERO-reference localizer needs PER-SENTENCE VISUAL")
print("  GROUNDING (per-claim CLIP / frame-grounded ADQA), which requires")
print("  video+CLIP/API calls not cached. SPEC: split each candidate AD into")
print("  claims; for each claim compute a CLIP frame-match score and/or a")
print("  frame-grounded yes/no ADQA; flag the lowest-grounded claim. Needs the")
print("  60-clip frames + CLIP encoder + ADQA generation (all uncached here).")
