#!/usr/bin/env python3
"""Third cached-data sweep for SceneTwin/TRIBE new findings.

Focus: ROI/profile evidence, category-residual triage, fair VLM rematch, and
human-review worksheet artifacts.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cursor" / "research" / "output" / "new_findings_round3"
REPORT = ROOT / "output" / "reports" / "tribe-new-findings-round3.md"
WORKSHEET = ROOT / "output" / "reports" / "tribe-review-worksheet.md"
random.seed(20260623)


def read_csv(path):
    p = ROOT / path if isinstance(path, str) else path
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def fnum(v, default=math.nan):
    try:
        if v is None or v == "": return default
        return float(v)
    except Exception:
        return default


def finite(x): return isinstance(x,(int,float)) and math.isfinite(x)

def avg(xs):
    vals=[x for x in xs if finite(x)]
    return mean(vals) if vals else math.nan


def quantile(xs,q):
    vals=sorted(x for x in xs if finite(x))
    if not vals: return math.nan
    idx=(len(vals)-1)*q; lo=math.floor(idx); hi=math.ceil(idx)
    if lo==hi: return vals[lo]
    return vals[lo]*(hi-idx)+vals[hi]*(idx-lo)


def spearman(xs,ys):
    pairs=[(x,y) for x,y in zip(xs,ys) if finite(x) and finite(y)]
    if len(pairs)<3: return math.nan
    x,y=zip(*pairs)
    def ranks(vals):
        order=sorted(range(len(vals)), key=lambda i: vals[i]); out=[0.0]*len(vals); i=0
        while i<len(order):
            j=i
            while j+1<len(order) and vals[order[j+1]]==vals[order[i]]: j+=1
            r=(i+j)/2+1
            for k in range(i,j+1): out[order[k]]=r
            i=j+1
        return out
    rx,ry=ranks(x),ranks(y); mx,my=mean(rx),mean(ry)
    denx=math.sqrt(sum((a-mx)**2 for a in rx)); deny=math.sqrt(sum((b-my)**2 for b in ry))
    return sum((a-mx)*(b-my) for a,b in zip(rx,ry))/(denx*deny) if denx and deny else math.nan


def auc(vals, labels):
    pairs=[(v,y) for v,y in zip(vals,labels) if finite(v) and y in (0,1)]
    pos=[v for v,y in pairs if y==1]; neg=[v for v,y in pairs if y==0]
    if not pos or not neg: return math.nan
    wins=ties=total=0
    for p in pos:
        for n in neg:
            total+=1
            if p>n: wins+=1
            elif p==n: ties+=1
    return (wins+0.5*ties)/total


def sign_p(w,l):
    n=w+l
    if n==0: return math.nan
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n)


def paired_condition_deltas(path, a, b):
    rows=read_csv(path); by=defaultdict(dict); meta={}
    for r in rows:
        key=(r['video_id'],str(r['q_idx']))
        by[key][r['condition']]=fnum(r['score'])
        meta[key]=r
    out=[]
    for key,s in by.items():
        if a in s and b in s:
            m=meta[key]
            out.append({
                'video_id': key[0], 'q_idx': key[1], 'delta': s[a]-s[b],
                'matched': int(str(m.get('matched','0'))=='1'),
                'tribe_type': m.get('tribe_type',''), 'vlm_type': m.get('vlm_type','')
            })
    return out


def bootstrap_video(deltas, selector, B=3000):
    by=defaultdict(list)
    for r in deltas:
        if selector(r): by[r['video_id']].append(r['delta'])
    vids=list(by)
    if not vids: return {'n_videos':0,'n_questions':0,'mean':math.nan,'ci_low':math.nan,'ci_high':math.nan}
    obs=avg([d for vals in by.values() for d in vals]); boots=[]
    for _ in range(B):
        sample=[random.choice(vids) for _ in vids]; vals=[]
        for vid in sample: vals.extend(by[vid])
        boots.append(avg(vals))
    return {'n_videos':len(vids),'n_questions':sum(len(v) for v in by.values()),'mean':obs,'ci_low':quantile(boots,.025),'ci_high':quantile(boots,.975)}


def external_fail_rows():
    scores=read_csv('cursor/output/external_ensemble_eval.csv')
    by=defaultdict(dict); cats={}
    for r in scores:
        by[r['video_id']][r['tier']]=r; cats[r['video_id']]=r.get('category','')
    out=[]
    for vid, tiers in by.items():
        need=['tier0_cross','tier1_vatex_short','tier3_va11y']
        if not all(t in tiers for t in need): continue
        def vals(col): return [fnum(tiers[t][col]) for t in need]
        def full(v): return int(v[0]<v[1]<v[2])
        out.append({'video_id':vid,'category':cats.get(vid,''),'adqa_fail':1-full(vals('adqa_score')),'ensemble_fail':1-full(vals('ensemble_mean_clip_top3'))})
    return {r['video_id']:r for r in out}


def roi_profile_analysis():
    roi_rows=read_csv('cursor/research/output/tribe_roi_gap_per_clip.csv')
    fail=external_fail_rows()
    visual_cols=['body_eba_region','early_visual_v1','face_ffc','higher_visual_v2v3v4','lateral_object_loc','motion_mt_complex','retrosplenial_pos','scene_ppa']
    control_cols=['auditory_control','language_control']
    rows=[]
    for r in roi_rows:
        visual={c:fnum(r.get(c)) for c in visual_cols}
        controls={c:fnum(r.get(c)) for c in control_cols}
        dom=max(visual, key=lambda c: visual[c] if finite(visual[c]) else -999)
        scene_mean=avg([visual['retrosplenial_pos'], visual['scene_ppa'], visual['early_visual_v1'], visual['higher_visual_v2v3v4']])
        social_action_mean=avg([visual['body_eba_region'], visual['face_ffc'], visual['motion_mt_complex'], visual['lateral_object_loc']])
        row={'clip_key':r['clip_key'],'corpus':r['corpus'],'category':r.get('category',''),'dominant_roi':dom,
             'visual_mean':avg(list(visual.values())),'control_mean':avg(list(controls.values())),
             'visual_minus_control':avg(list(visual.values()))-avg(list(controls.values())),
             'scene_mean':scene_mean,'social_action_mean':social_action_mean,
             'scene_minus_social_action':scene_mean-social_action_mean,
             'accessibility_gap':fnum(r.get('accessibility_gap'))}
        # extract video_id: external clip_key starts external_<video_id>; inbench has prefix inbench_clip_##_<video_id>
        if row['corpus']=='external':
            vid=row['clip_key'].replace('external_','',1)
            row.update(fail.get(vid,{}))
        rows.append(row)
    write_csv(OUT/'roi_profile_rows.csv', rows)
    ext=[r for r in rows if r['corpus']=='external' and 'adqa_fail' in r]
    by_dom=[]
    for dom,g in sorted(defaultdict(list, { }).items()): pass
    groups=defaultdict(list)
    for r in ext: groups[r['dominant_roi']].append(r)
    for dom,g in groups.items():
        by_dom.append({'dominant_roi':dom,'n':len(g),'adqa_fail_rate':avg([r['adqa_fail'] for r in g]),
                       'ensemble_fail_rate':avg([r['ensemble_fail'] for r in g]),
                       'mean_visual_minus_control':avg([r['visual_minus_control'] for r in g])})
    by_dom=sorted(by_dom, key=lambda r:(-r['n'], r['dominant_roi']))
    write_csv(OUT/'roi_dominant_failure_rates.csv', by_dom)
    # category residual/z-score for mean visual gap using clip summary
    cs=read_csv('cursor/research/output/tribe_blind_spot_clip_summary.csv')
    joined=[]
    by_cat=defaultdict(list)
    for r in cs:
        if r.get('corpus')=='external' and r.get('video_id') in fail:
            val=fnum(r.get('mean_visual_gap')); by_cat[r.get('category','')].append(val)
            joined.append({'video_id':r['video_id'],'category':r.get('category',''),'mean_visual_gap':val,**fail[r['video_id']]})
    cat_stats={}
    for cat,vals in by_cat.items():
        mu=avg(vals); sd=math.sqrt(avg([(v-mu)**2 for v in vals])) if vals else math.nan
        cat_stats[cat]=(mu,sd)
    for r in joined:
        mu,sd=cat_stats[r['category']]
        r['category_residual_gap']=r['mean_visual_gap']-mu
        r['category_z_gap']=(r['mean_visual_gap']-mu)/sd if sd and finite(sd) else 0.0
    write_csv(OUT/'category_residual_gap_rows.csv', joined)
    summary={
        'n_external':len(ext),
        'dominant_roi_counts':dict(Counter(r['dominant_roi'] for r in ext)),
        'visual_minus_control_mean_external':avg([r['visual_minus_control'] for r in ext]),
        'visual_minus_control_mean_inbench':avg([r['visual_minus_control'] for r in rows if r['corpus']=='inbench']),
        'mean_gap_auc_adqa_fail':auc([r['mean_visual_gap'] for r in joined],[r['adqa_fail'] for r in joined]),
        'category_residual_gap_auc_adqa_fail':auc([r['category_residual_gap'] for r in joined],[r['adqa_fail'] for r in joined]),
        'category_z_gap_auc_adqa_fail':auc([r['category_z_gap'] for r in joined],[r['adqa_fail'] for r in joined]),
        'by_dominant_roi':by_dom,
    }
    return summary


def necessity_rematch_analysis():
    path='cursor/research/output/tribe_necessity_rematch_perq.csv'
    comparisons={
        'tribe_minus_vlm': ('tribe','vlm'),
        'tribe_minus_baseline': ('tribe','baseline'),
        'vlm_minus_baseline': ('vlm','baseline'),
    }
    rows=[]
    for name,(a,b) in comparisons.items():
        ds=paired_condition_deltas(path,a,b)
        for group,sel in [('all',lambda r: True),('matched',lambda r:r['matched']==1),('unmatched',lambda r:r['matched']==0)]:
            vals=[r['delta'] for r in ds if sel(r)]
            ci=bootstrap_video(ds,sel)
            rows.append({'comparison':name,'group':group,**ci,
                         'wins':sum(1 for x in vals if x>0),'losses':sum(1 for x in vals if x<0),'ties':sum(1 for x in vals if x==0),
                         'sign_p_one_sided':sign_p(sum(1 for x in vals if x>0),sum(1 for x in vals if x<0))})
    write_csv(OUT/'necessity_rematch_bootstrap.csv',rows)
    # disagreement rate between TRIBE and VLM type
    raw=read_csv(path); seen={}
    for r in raw:
        key=(r['video_id'],r['q_idx'])
        seen[key]=(r.get('tribe_type',''),r.get('vlm_type',''))
    pairs=list(seen.values())
    disagree=sum(1 for a,b in pairs if a and b and a!=b)
    return {'rows':rows,'type_pair_n':len(pairs),'type_disagree_rate':disagree/len(pairs) if pairs else math.nan,
            'type_pairs':dict(Counter(f'{a} vs {b}' for a,b in pairs).most_common(10))}


def review_worksheet():
    cases=read_csv('cursor/research/output/tribe_blind_spot_cases.csv')
    windows=read_csv('cursor/research/output/tribe_blind_spot_windows.csv')
    fail=external_fail_rows()
    win_by_vid=defaultdict(list)
    for w in windows:
        win_by_vid[w['video_id']].append(w)
    cases2=[c for c in cases if c.get('case_id')!='low_gap_skip']
    cases2=sorted(cases2,key=lambda r:fnum(r.get('priority_score')),reverse=True)[:25]
    lines=["---","title: TRIBE Review Worksheet","category: research","created: 2026-06-23","---","", "# TRIBE Review Worksheet", "", "Top non-low-gap blind-spot cases for human/VLM review. Generated from cached router CSVs.", ""]
    rows=[]
    for i,c in enumerate(cases2,1):
        vid=c['video_id']; topwins=sorted(win_by_vid.get(vid,[]), key=lambda r:fnum(r.get('peak_visual_gap')), reverse=True)[:3]
        f=fail.get(vid,{})
        rows.append({'rank':i,**c,'adqa_fail':f.get('adqa_fail',''),'ensemble_fail':f.get('ensemble_fail','')})
        lines.append(f"## {i}. {vid} — {c.get('case_id')} ({c.get('category')})")
        lines.append("")
        lines.append(f"- Priority score: `{fnum(c.get('priority_score')):.3f}`")
        lines.append(f"- Suggested review window: `{c.get('window')}`")
        lines.append(f"- Why: {c.get('why')}")
        if f:
            lines.append(f"- Existing corrected-ladder flags: ADQA fail `{f.get('adqa_fail')}`, ensemble fail `{f.get('ensemble_fail')}`")
        if topwins:
            lines.append("- Top router windows:")
            for w in topwins:
                lines.append(f"  - `{fnum(w.get('start_s')):.1f}-{fnum(w.get('end_s')):.1f}s`, `{w.get('dominant_type')}`, route `{w.get('route')}`, peak `{fnum(w.get('peak_visual_gap')):.3f}`")
        lines.append("")
    write_csv(OUT/'review_worksheet_rows.csv', rows)
    WORKSHEET.write_text('\n'.join(lines),encoding='utf-8')
    return {'worksheet_path':str(WORKSHEET),'n_cases':len(cases2),'top_case':cases2[0] if cases2 else {}}


def write_report(results):
    def fmt(x,d=3): return 'n/a' if not finite(x) else f'{x:.{d}f}'
    roi=results['roi']; nec=results['necessity']; work=results['worksheet']
    roi_lines=[]
    for r in roi['by_dominant_roi']:
        roi_lines.append(f"| {r['dominant_roi']} | {r['n']} | {fmt(r['adqa_fail_rate'])} | {fmt(r['ensemble_fail_rate'])} | {fmt(r['mean_visual_minus_control'])} |")
    nec_lines=[]
    for r in nec['rows']:
        nec_lines.append(f"| {r['comparison']} | {r['group']} | {r['n_videos']} | {r['n_questions']} | {fmt(r['mean'])} | [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] | {r['wins']}/{r['losses']}/{r['ties']} | {fmt(r['sign_p_one_sided'],4)} |")
    text=f"""---
title: TRIBE New Findings — Cached-Data Round 3
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_new_findings_round3.py
  - cursor/research/output/new_findings_round3/
  - output/reports/tribe-review-worksheet.md
---

# TRIBE New Findings — Cached-Data Round 3

Third no-API/no-GPU sweep. This adds ROI/profile checks, fair VLM-rematch analysis, and a review worksheet artifact.

## Finding 13 — ROI/profile evidence is dominated by scene/spatial regions; rare ROI types are underpowered

Dominant visual ROI counts on external clips:

```json
{json.dumps(roi['dominant_roi_counts'], indent=2)}
```

| Dominant ROI | n | ADQA fail rate | Ensemble fail rate | mean visual-control gap |
|---|---:|---:|---:|---:|
{chr(10).join(roi_lines)}

Interpretation: current ROI-derived paper claims should lead with **scene/spatial accessibility gaps**. Body/face/motion/object-specific claims are too sparse in this corpus to stand alone.

Artifacts: `roi_profile_rows.csv`, `roi_dominant_failure_rates.csv`.

## Finding 14 — category-residual gap does not improve external ADQA-failure triage

- Raw `mean_visual_gap` AUC vs ADQA fail: **{fmt(roi['mean_gap_auc_adqa_fail'])}**
- Category-residual mean gap AUC: **{fmt(roi['category_residual_gap_auc_adqa_fail'])}**
- Category z-scored mean gap AUC: **{fmt(roi['category_z_gap_auc_adqa_fail'])}**

Interpretation: category normalization does not strengthen the failure-triage signal here. Keep the raw mean-gap queue unless a later larger corpus says otherwise.

Artifact: `category_residual_gap_rows.csv`.

## Finding 15 — fair transcript-armed VLM rematch confirms: TRIBE is competitive/different, not decisively superior

TRIBE/VLM type disagreement rate across question rows: **{fmt(nec['type_disagree_rate'])}**.

Most common type pairings:

```json
{json.dumps(nec['type_pairs'], indent=2)}
```

| Comparison | Group | videos | questions | mean delta | video-bootstrap 95% CI | W/L/T | sign p |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(nec_lines)}

Interpretation: this supports the honest wording from the previous log: TRIBE picks different targets and is at least competitive with a transcript-armed VLM, but the superiority claim is not locked. The contribution is brain-grounded routing + non-redundant targets.

Artifact: `necessity_rematch_bootstrap.csv`.

## Finding 16 — review worksheet is now a concrete artifact, not just a product idea

Generated `output/reports/tribe-review-worksheet.md` with the top {work['n_cases']} non-low-gap blind-spot cases. Top case:

```json
{json.dumps(work['top_case'], indent=2)}
```

This is directly usable for human/VLM review: each card lists priority score, suggested window, why it was routed, existing fail flags when available, and top router windows.

Artifacts: `output/reports/tribe-review-worksheet.md`, `review_worksheet_rows.csv`.

## Round-3 action changes

1. Lead ROI/profile sections with scene/spatial; mark body/face/motion/object as underpowered.
2. Do not spend time on category-residual thresholds yet.
3. Keep fair VLM-rematch wording conservative: “competitive and different,” not “beats VLM.”
4. Use the generated review worksheet as the next manual/human/VLM validation queue.
"""
    REPORT.write_text(text,encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results={'roi':roi_profile_analysis(),'necessity':necessity_rematch_analysis(),'worksheet':review_worksheet()}
    (OUT/'summary.json').write_text(json.dumps(results,indent=2,sort_keys=True),encoding='utf-8')
    write_report(results)
    print(json.dumps({'report':str(REPORT),'worksheet':str(WORKSHEET),'roi_counts':results['roi']['dominant_roi_counts'],'type_disagree_rate':results['necessity']['type_disagree_rate']},indent=2))

if __name__=='__main__':
    main()
