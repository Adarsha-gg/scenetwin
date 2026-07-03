"""New research directions — real analysis on cached SceneTwin data (stdlib only)."""
import csv, os, random, math, itertools

ROOT = r"C:\Users\adars\Coding\scenetwin"
def p(*a): return os.path.join(ROOT, *a)

def readcsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def auc(pos, neg):
    """Mann-Whitney AUC: P(pos>neg), ties=0.5."""
    if not pos or not neg: return float('nan')
    c=0.0
    for a in pos:
        for b in neg:
            if a>b: c+=1
            elif a==b: c+=0.5
    return c/(len(pos)*len(neg))

def best_auc(scores, labels):
    """AUC choosing better of the two directions; returns (auc, direction)."""
    pos=[s for s,l in zip(scores,labels) if l==1]
    neg=[s for s,l in zip(scores,labels) if l==0]
    a=auc(pos,neg)
    if a>=0.5: return a,'high'
    return 1-a,'low'

def perm_p(scores, labels, n=20000, seed=0):
    """One-sided label-permutation p for best-direction AUC."""
    rng=random.Random(seed)
    obs,_=best_auc(scores,labels)
    labs=list(labels); ge=0
    for _ in range(n):
        rng.shuffle(labs)
        a,_=best_auc(scores,labs)
        if a>=obs: ge+=1
    return (ge+1)/(n+1), obs

def mean(x): return sum(x)/len(x) if x else float('nan')

print("="*70)
print("D1  AD ERROR-TAXONOMY DETECTOR")
print("="*70)
hg=readcsv(p("cursor/output/halluc_gate/halluc_gate.csv"))
# fabrication drop vs paraphrase drop (control) for CLIP and ADQA
clip_fab=[float(r['clip_expert'])-float(r['clip_halluc']) for r in hg]
clip_par=[float(r['clip_expert'])-float(r['clip_para'])  for r in hg]
adqa_fab=[float(r['adqa_expert'])-float(r['adqa_halluc']) for r in hg]
adqa_par=[float(r['adqa_expert'])-float(r['adqa_para'])  for r in hg]
n=len(hg)
print(f"n clips = {n}")
print(f"CLIP fab-vs-paraphrase detection AUC = {auc(clip_fab,clip_par):.3f}  "
      f"(mean fab drop {mean(clip_fab):+.4f} vs para {mean(clip_par):+.4f})")
print(f"ADQA fab-vs-paraphrase detection AUC = {auc(adqa_fab,adqa_par):.3f}  "
      f"(mean fab drop {mean(adqa_fab):+.4f} vs para {mean(adqa_par):+.4f})")
# how often is each signal BLIND (fabrication produces no drop)?
clip_blind=sum(1 for d in clip_fab if d<=0)
adqa_blind=sum(1 for d in adqa_fab if d<=0)
print(f"CLIP blind (fab drop<=0): {clip_blind}/{n} = {clip_blind/n:.1%}")
print(f"ADQA blind (fab drop<=0): {adqa_blind}/{n} = {adqa_blind/n:.1%}")
# complementarity: clips where ADQA blind, does CLIP catch?
both=sum(1 for a,c in zip(adqa_fab,clip_fab) if a<=0 and c>0)
adqa_blind_clips=[c for a,c in zip(adqa_fab,clip_fab) if a<=0]
print(f"of {len(adqa_blind_clips)} ADQA-blind clips, CLIP catches {both} "
      f"({both/len(adqa_blind_clips):.1%})")

# per-error-type using the relational probe set labels (join by video_id)
probes=readcsv(p("cursor/output/relational_hallucination_probe_set/probes.csv"))
clip_class={}
for r in probes:
    clip_class[r['video_id']]=int(r['is_relation_action_count'])
hg_by_id={r['video_id']:r for r in hg}
groups={'object_scene':[], 'relation_action_count':[]}
for vid,flag in clip_class.items():
    if vid in hg_by_id:
        g='relation_action_count' if flag==1 else 'object_scene'
        groups[g].append(hg_by_id[vid])
print("\nPer-error-type (clips present in both probe set and halluc gate):")
for g,rows in groups.items():
    if not rows: continue
    cf=[float(r['clip_expert'])-float(r['clip_halluc']) for r in rows]
    af=[float(r['adqa_expert'])-float(r['adqa_halluc']) for r in rows]
    cb=sum(1 for d in cf if d<=0); ab=sum(1 for d in af if d<=0)
    print(f"  {g:22s} n={len(rows):2d} | CLIP mean drop {mean(cf):+.4f} blind {cb}/{len(rows)}"
          f" | ADQA mean drop {mean(af):+.4f} blind {ab}/{len(rows)}")

print("\n"+"="*70)
print("D2  COMPREHENSION-GROUNDED TARGET (AD-only answerability)")
print("="*70)
# does the professional (truth) AD actually STATE the probed visual fact?
by_type={}
tot_truth_true=0; tot=0
for r in probes:
    t=r['probe_type']
    by_type.setdefault(t,{'n':0,'truth_true':0,'halluc_true':0})
    by_type[t]['n']+=1
    by_type[t]['truth_true']+=int(r['truth_ad_mentions_true'])
    by_type[t]['halluc_true']+=int(r['halluc_ad_mentions_true'])
    tot_truth_true+=int(r['truth_ad_mentions_true']); tot+=1
print(f"Overall: professional AD explicitly states the probed true fact in "
      f"{tot_truth_true}/{tot} = {tot_truth_true/tot:.1%} of probes")
print("  => the rest are OMISSIONS a frame-grounded QA key cannot see")
print("By probe type (truth-AD coverage of the key visual fact):")
for t,d in sorted(by_type.items(), key=lambda x:-x[1]['n']):
    print(f"  {t:16s} n={d['n']:2d}  pro-AD states true fact {d['truth_true']}/{d['n']}"
          f" = {d['truth_true']/d['n']:.0%}")

print("\n"+"="*70)
print("D3  VIDEO-NATIVE MOTIVATION (where frame-sampled signals go blind)")
print("="*70)
qt=readcsv(p("cursor/output/scene_model_correctness_gap/adqa_question_types.csv"))
type_ct={}
for r in qt:
    type_ct[r['question_type']]=type_ct.get(r['question_type'],0)+1
print("ADQA question-type distribution (what the QA actually probes):")
for t,c in sorted(type_ct.items(), key=lambda x:-x[1]):
    print(f"  {t:18s} {c}")
sm=sum(1 for r in qt if r['is_scene_model_question']=='1')
print(f"scene-model (relation/action/count/who) questions: {sm}/{len(qt)} = {sm/len(qt):.0%}")
print("ADQA blindness on relation/action/count from D1 is the motivation "
      "for a video-native (temporal) scorer.")

print("\n"+"="*70)
print("D4  CHEAP-PROXY FIGHT FOR TRIBE (predicting ADQA failure)")
print("="*70)
ef=readcsv(p("cursor/research/output/parallel_research/cheap_baselines/external_features.csv"))
labels=[int(r['adqa_fail']) for r in ef]
print(f"n={len(ef)} clips, positives(adqa_fail)={sum(labels)}")
feats=['accessibility_gap','mean_visual_gap','max_visual_gap','mean_scene_spatial_gap',
       'duration_s','tier3_word_count','tier3_words_per_sec','transcript_word_count',
       'transcript_words_per_sec','transcript_unique_ratio','transcript_sound_cue_count',
       'category_loo_adqa_fail_rate']
results={}
for fname in feats:
    sc=[float(r[fname]) for r in ef]
    a,d=best_auc(sc,labels)
    results[fname]=a
    tag='  <-- NEURAL' if fname in ('accessibility_gap','mean_visual_gap','max_visual_gap','mean_scene_spatial_gap') else ''
    print(f"  {fname:28s} AUC={a:.3f} ({d}){tag}")
pval,obs=perm_p([float(r['accessibility_gap']) for r in ef], labels, n=20000)
print(f"accessibility_gap permutation p = {pval:.4f} (AUC={obs:.3f})")

# cheap ensemble: z-score sum of the cheap (non-neural) features, best direction
cheap=['duration_s','tier3_words_per_sec','transcript_words_per_sec',
       'transcript_unique_ratio','category_loo_adqa_fail_rate']
def z(col):
    xs=[float(r[col]) for r in ef]; m=mean(xs)
    sd=(sum((x-m)**2 for x in xs)/len(xs))**0.5 or 1.0
    return [(x-m)/sd for x in xs]
zc=[z(c) for c in cheap]
# align each cheap feature to its best direction vs label first
aligned=[]
for c,col in zip(zc,cheap):
    _,d=best_auc([float(r[col]) for r in ef],labels)
    aligned.append(c if d=='high' else [-v for v in c])
ens=[sum(vals) for vals in zip(*aligned)]
a_ens,_=best_auc(ens,labels)
print(f"cheap-feature ensemble ({'+'.join(cheap)}) AUC={a_ens:.3f}")
print(f"=> accessibility_gap {results['accessibility_gap']:.3f} vs best cheap "
      f"{max(results[f] for f in feats if f not in ('accessibility_gap','mean_visual_gap','max_visual_gap','mean_scene_spatial_gap')):.3f}"
      f" and cheap-ensemble {a_ens:.3f}")

print("\n"+"="*70)
print("D5  COST / QUALITY PARETO (cached rho vs known 2026 run cost)")
print("="*70)
# cached rho (corrected 3-tier, 60-clip primary) + cached run-cost figures from
# wiki/research/scenetwin-vlm-as-judge-protocol (78-clip run cost band $1..$50)
rows=[
 ("SceneTwin CLIP+ADQA (ensemble)", 0.952, "~$1 (Gemini-Flash ADQA gen)"),
 ("ADQA alone",                     0.869, "~$1"),
 ("CLIP alone",                     0.747, "~$0 (local encoder)"),
 ("LLM-AD-Eval proxy (ref-based)",  0.942, "needs human reference AD"),
 ("Best frontier VLM judge",        0.847, "~$50 (Claude Opus, 78 clips)"),
]
print(f"{'method':34s} {'rho(60)':>8s}  approx cost / requirement")
for name,rho,cost in rows:
    print(f"{name:34s} {rho:>8.3f}  {cost}")
print("Pareto point: SceneTwin matches the best reference-free ranking at the "
      "lowest cost and without a human reference; frontier VLM judge is ~50x "
      "cost and lower rho.")
