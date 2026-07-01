#!/usr/bin/env python3
"""Second cached-data sweep for SceneTwin/TRIBE new findings.

Focus: validation curves, cross-judge meta, length confounds, tie-aware target
checks, low-alignment sensitivity, and cheap/low-pressure policies.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cursor" / "research" / "output" / "new_findings_round2"
REPORT = ROOT / "output" / "reports" / "tribe-new-findings-round2.md"
random.seed(20260623)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    p = ROOT / path if isinstance(path, str) else path
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def fnum(v, default=math.nan):
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def avg(xs):
    vals = [x for x in xs if finite(x)]
    return mean(vals) if vals else math.nan


def quantile(xs, q):
    vals = sorted(x for x in xs if finite(x))
    if not vals:
        return math.nan
    idx = (len(vals) - 1) * q
    lo = math.floor(idx); hi = math.ceil(idx)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - idx) + vals[hi] * (idx - lo)


def spearman(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if finite(x) and finite(y)]
    if len(pairs) < 3:
        return math.nan
    x, y = zip(*pairs)
    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            r = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = r
            i = j + 1
        return out
    rx, ry = ranks(x), ranks(y)
    mx, my = mean(rx), mean(ry)
    denx = math.sqrt(sum((a-mx)**2 for a in rx))
    deny = math.sqrt(sum((b-my)**2 for b in ry))
    if not denx or not deny:
        return math.nan
    return sum((a-mx)*(b-my) for a,b in zip(rx,ry)) / (denx*deny)


def auc(vals, labels):
    pairs = [(v, y) for v, y in zip(vals, labels) if finite(v) and y in (0, 1)]
    pos = [v for v,y in pairs if y == 1]
    neg = [v for v,y in pairs if y == 0]
    if not pos or not neg:
        return math.nan
    total = wins = ties = 0
    for p in pos:
        for n in neg:
            total += 1
            if p > n: wins += 1
            elif p == n: ties += 1
    return (wins + 0.5*ties) / total


def sign_p(wins, losses):
    n = wins + losses
    if n == 0: return math.nan
    return sum(math.comb(n, k) for k in range(wins, n+1)) / (2**n)


def paired_deltas(path: str, positive="gap_targeted"):
    rows = read_csv(path)
    by = defaultdict(dict)
    meta = {}
    for r in rows:
        key = (r["video_id"], str(r["q_idx"]))
        by[key][r["condition"]] = fnum(r["score"])
        meta[key] = {k: r.get(k, "") for k in r if k not in {"condition", "score"}}
    out = []
    for key, scores in by.items():
        if "baseline" not in scores:
            continue
        cond = positive if positive in scores else next((c for c in scores if c != "baseline"), None)
        if not cond:
            continue
        m = meta[key]
        out.append({
            **m,
            "video_id": key[0], "q_idx": key[1], "condition": cond,
            "delta": scores[cond] - scores["baseline"],
            "matched": int(str(m.get("matched", "0")) == "1"),
        })
    return out


def bootstrap_video_ci(deltas, selector, B=3000):
    by_vid = defaultdict(list)
    for r in deltas:
        if selector(r):
            by_vid[r["video_id"]].append(r["delta"])
    vids = list(by_vid)
    if not vids:
        return {"n_videos": 0, "n_questions": 0, "mean": math.nan, "ci_low": math.nan, "ci_high": math.nan}
    qn = sum(len(v) for v in by_vid.values())
    obs = avg([d for vals in by_vid.values() for d in vals])
    boots = []
    for _ in range(B):
        sample = [random.choice(vids) for _ in vids]
        vals = []
        for vid in sample:
            vals.extend(by_vid[vid])
        boots.append(avg(vals))
    return {"n_videos": len(vids), "n_questions": qn, "mean": obs, "ci_low": quantile(boots, 0.025), "ci_high": quantile(boots, 0.975)}


def crossjudge_meta():
    runs = {
        "haiku_surgical": "cursor/research/output/tribe_surgical_adqa_perq.csv",
        "gpt5_crossjudge": "cursor/research/output/tribe_crossjudge_gpt5_perq.csv",
        "opus17_crossjudge": "cursor/research/output/tribe_crossjudge_opus_17_perq.csv",
        "opus15_subset": "cursor/research/output/tribe_crossjudge_opus_subset_perq.csv",
    }
    rows = []
    for name, path in runs.items():
        if not (ROOT / path).exists():
            continue
        ds = paired_deltas(path)
        for group, sel in [
            ("matched", lambda r: r["matched"] == 1),
            ("unmatched", lambda r: r["matched"] == 0),
            ("all", lambda r: True),
        ]:
            vals = [r["delta"] for r in ds if sel(r)]
            ci = bootstrap_video_ci(ds, sel)
            wins = sum(1 for x in vals if x > 0); losses = sum(1 for x in vals if x < 0); ties = sum(1 for x in vals if x == 0)
            rows.append({
                "run": name, "group": group, **ci,
                "wins": wins, "losses": losses, "ties": ties,
                "sign_p_one_sided": sign_p(wins, losses),
            })
        # matched minus unmatched at video level
        by_vid = defaultdict(lambda: {"m": [], "u": []})
        for r in ds:
            by_vid[r["video_id"]]["m" if r["matched"] else "u"].append(r["delta"])
        diffs = []
        for vid, d in by_vid.items():
            if d["m"] and d["u"]:
                diffs.append({"video_id": vid, "delta": avg(d["m"]) - avg(d["u"]), "matched": 1})
        ci = bootstrap_video_ci(diffs, lambda r: True)
        rows.append({"run": name, "group": "matched_minus_unmatched", **ci,
                     "wins": sum(1 for r in diffs if r["delta"] > 0),
                     "losses": sum(1 for r in diffs if r["delta"] < 0),
                     "ties": sum(1 for r in diffs if r["delta"] == 0),
                     "sign_p_one_sided": sign_p(sum(1 for r in diffs if r["delta"] > 0), sum(1 for r in diffs if r["delta"] < 0))})
    write_csv(OUT / "crossjudge_meta.csv", rows)
    return rows


def length_control():
    # Full-window generation: row-level text lengths aggregate to clip-level AD.
    gen = read_csv("cursor/research/output/tribe_gap_targeted_external_full_scores.csv")
    adqa = read_csv("cursor/research/output/tribe_gap_targeted_adqa_full_scores.csv")
    words = defaultdict(lambda: defaultdict(float))
    windows = defaultdict(lambda: defaultdict(int))
    for r in gen:
        words[r["video_id"]][r["condition"]] += fnum(r.get("word_count"), 0)
        windows[r["video_id"]][r["condition"]] += 1
    scores = defaultdict(dict)
    for r in adqa:
        scores[r["video_id"]][r["condition"]] = fnum(r.get("adqa"))
    rows = []
    for vid in sorted(set(words) & set(scores)):
        if not {"baseline", "gap_targeted"}.issubset(words[vid]) or not {"baseline", "gap_targeted"}.issubset(scores[vid]):
            continue
        rows.append({
            "video_id": vid,
            "baseline_words": words[vid]["baseline"],
            "gap_words": words[vid]["gap_targeted"],
            "word_delta": words[vid]["gap_targeted"] - words[vid]["baseline"],
            "baseline_adqa": scores[vid]["baseline"],
            "gap_adqa": scores[vid]["gap_targeted"],
            "adqa_delta": scores[vid]["gap_targeted"] - scores[vid]["baseline"],
            "baseline_windows": windows[vid]["baseline"],
            "gap_windows": windows[vid]["gap_targeted"],
        })
    # Linear residual of adqa_delta on word_delta.
    xs = [r["word_delta"] for r in rows]; ys = [r["adqa_delta"] for r in rows]
    mx, my = mean(xs), mean(ys)
    den = sum((x-mx)**2 for x in xs)
    slope = sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / den if den else 0.0
    intercept = my - slope*mx
    for r in rows:
        r["length_pred_delta"] = intercept + slope*r["word_delta"]
        r["length_residual_delta"] = r["adqa_delta"] - r["length_pred_delta"]
    write_csv(OUT / "length_control_full_adqa.csv", rows)
    low = [r for r in rows if r["word_delta"] <= median([x["word_delta"] for x in rows])]
    high = [r for r in rows if r["word_delta"] > median([x["word_delta"] for x in rows])]
    nonlonger = [r for r in rows if r["word_delta"] <= 0]
    summary = {
        "n": len(rows),
        "mean_word_delta": avg([r["word_delta"] for r in rows]),
        "median_word_delta": median([r["word_delta"] for r in rows]),
        "mean_adqa_delta": avg([r["adqa_delta"] for r in rows]),
        "spearman_word_delta_vs_adqa_delta": spearman([r["word_delta"] for r in rows], [r["adqa_delta"] for r in rows]),
        "linear_slope_adqa_per_word": slope,
        "low_length_half_mean_adqa_delta": avg([r["adqa_delta"] for r in low]),
        "high_length_half_mean_adqa_delta": avg([r["adqa_delta"] for r in high]),
        "nonlonger_n": len(nonlonger),
        "nonlonger_mean_adqa_delta": avg([r["adqa_delta"] for r in nonlonger]),
        "positive_adqa_wins": sum(1 for r in rows if r["adqa_delta"] > 0),
        "negative_adqa_losses": sum(1 for r in rows if r["adqa_delta"] < 0),
        "ties": sum(1 for r in rows if r["adqa_delta"] == 0),
    }
    return summary


def external_rows_joined():
    scores = read_csv("cursor/output/external_ensemble_eval.csv")
    by_vid = defaultdict(dict)
    cats = {}
    for r in scores:
        by_vid[r["video_id"]][r["tier"]] = r
        cats[r["video_id"]] = r.get("category", "")
    clip_summary = {r["video_id"]: r for r in read_csv("cursor/research/output/tribe_blind_spot_clip_summary.csv") if r.get("corpus") == "external"}
    manifest = {r["video_id"]: r for r in read_csv("cursor/research/output/tribe_tensors/manifest.csv") if r.get("corpus") == "external"}
    out = []
    for vid, tiers in by_vid.items():
        need = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]
        if not all(t in tiers for t in need) or vid not in clip_summary:
            continue
        def vals(col): return [fnum(tiers[t][col]) for t in need]
        def full(v): return int(v[0] < v[1] < v[2])
        cs = clip_summary[vid]
        mf = manifest.get(vid, {})
        out.append({
            "video_id": vid, "category": cats.get(vid, ""),
            "adqa_fail": 1-full(vals("adqa_score")),
            "ensemble_fail": 1-full(vals("ensemble_mean_clip_top3")),
            "clip_fail": 1-full(vals("clip_top3")),
            "adqa_full_order": full(vals("adqa_score")),
            "ensemble_full_order": full(vals("ensemble_mean_clip_top3")),
            "clip_full_order": full(vals("clip_top3")),
            "mean_visual_gap": fnum(cs.get("mean_visual_gap")),
            "max_visual_gap": fnum(cs.get("max_visual_gap")),
            "top1_vs_uniform": fnum(cs.get("top1_vs_uniform")),
            "alignment_cosine": fnum(mf.get("alignment_cosine")),
        })
    return out


def triage_curves_and_early_exit():
    rows = external_rows_joined()
    budgets = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50]
    curve_rows = []
    for feature in ["mean_visual_gap", "max_visual_gap", "top1_vs_uniform"]:
        for target in ["adqa_fail", "ensemble_fail"]:
            total_pos = sum(r[target] for r in rows)
            sorted_rows = sorted(rows, key=lambda r: r[feature], reverse=True)
            for b in budgets:
                k = max(1, round(len(rows)*b))
                top = sorted_rows[:k]
                hits = sum(r[target] for r in top)
                curve_rows.append({"feature": feature, "target": target, "budget_frac": b, "k": k,
                                   "hits": hits, "total_pos": total_pos,
                                   "recall": hits/total_pos if total_pos else math.nan,
                                   "precision": hits/k if k else math.nan,
                                   "random_expected_recall": b})
    write_csv(OUT / "external_triage_budget_curves.csv", curve_rows)
    # Low-pressure early exit: bottom max_visual_gap can use cheaper ADQA-only? compare failures and agreement.
    sorted_low = sorted(rows, key=lambda r: r["max_visual_gap"])
    early_rows = []
    for frac in [0.10, 0.20, 0.25, 1/3, 0.50]:
        k = max(1, round(len(rows)*frac))
        low = sorted_low[:k]
        high = sorted_low[-k:]
        for label, subset in [("low", low), ("high", high)]:
            early_rows.append({
                "gap_group": label, "frac": frac, "n": len(subset),
                "adqa_fail_rate": avg([r["adqa_fail"] for r in subset]),
                "ensemble_fail_rate": avg([r["ensemble_fail"] for r in subset]),
                "clip_fail_rate": avg([r["clip_fail"] for r in subset]),
                "adqa_ensemble_full_order_agreement": avg([int(r["adqa_full_order"] == r["ensemble_full_order"]) for r in subset]),
                "clip_ensemble_full_order_agreement": avg([int(r["clip_full_order"] == r["ensemble_full_order"]) for r in subset]),
            })
    write_csv(OUT / "low_pressure_early_exit.csv", early_rows)
    # Quarantine low AD alignment sensitivity for P_AD-dependent analyses/derived external rows.
    hi_align = [r for r in rows if finite(r["alignment_cosine"]) and r["alignment_cosine"] > 0.5]
    lo_align = [r for r in rows if finite(r["alignment_cosine"]) and r["alignment_cosine"] <= 0.5]
    align_summary = {
        "all_n": len(rows), "high_alignment_n": len(hi_align), "low_alignment_n": len(lo_align),
        "all_mean_gap_auc_adqa_fail": auc([r["mean_visual_gap"] for r in rows], [r["adqa_fail"] for r in rows]),
        "hi_align_mean_gap_auc_adqa_fail": auc([r["mean_visual_gap"] for r in hi_align], [r["adqa_fail"] for r in hi_align]),
        "lo_align_mean_gap_auc_adqa_fail": auc([r["mean_visual_gap"] for r in lo_align], [r["adqa_fail"] for r in lo_align]),
        "hi_align_adqa_fail_rate": avg([r["adqa_fail"] for r in hi_align]),
        "lo_align_adqa_fail_rate": avg([r["adqa_fail"] for r in lo_align]),
    }
    return {"curves": curve_rows, "early_exit": early_rows, "alignment": align_summary}


def tie_and_confound_checks():
    rows = read_csv("output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv")
    target_rows = []
    for r in rows:
        all4_fail = int(fnum(r["all4_fail"]) > 0)
        t3_margin = fnum(r["all4_mean_tier3_margin"])
        t2_t1 = fnum(r["all4_mean_tier2_vs_tier1"])
        fail_kind = "ok"
        if all4_fail:
            if t3_margin < 0:
                fail_kind = "t3_margin_inversion"
            elif t2_t1 < 0:
                fail_kind = "tier2_tier1_inversion"
            else:
                fail_kind = "tie_or_other"
        target_rows.append({
            "clip_idx": r["clip_idx"], "video_id": r["video_id"], "category": r["category"],
            "all4_fail": all4_fail, "fail_kind": fail_kind,
            "t3_margin": t3_margin, "tier2_vs_tier1": t2_t1,
            "risk_rank": int(fnum(r["risk_rank"])),
            "mean_standard_slot_score": fnum(r["mean_standard_slot_score"]),
            "mean_speech_density": fnum(r["mean_speech_density"]),
            "duration_s": fnum(r["duration_s"]),
            "need_entropy": fnum(r["need_entropy"]),
        })
    write_csv(OUT / "tie_target_audit_inbench.csv", target_rows)
    labels = [r["all4_fail"] for r in target_rows]
    confound_rows = []
    for feat in ["mean_standard_slot_score", "mean_speech_density", "duration_s", "need_entropy"]:
        vals = [r[feat] for r in target_rows]
        confound_rows.append({"feature": feat, "auc_high_bad": auc(vals, labels), "auc_low_bad": auc([-v for v in vals], labels)})
    # Category-only high-risk if category is Sports or Pets (where positives live)
    cats = sorted(set(r["category"] for r in target_rows))
    for cat in cats:
        vals = [1 if r["category"] == cat else 0 for r in target_rows]
        confound_rows.append({"feature": f"category_eq_{cat}", "auc_high_bad": auc(vals, labels), "auc_low_bad": auc([-v for v in vals], labels)})
    vals = [1 if r["category"] in {"Sports", "Pets & Animals"} else 0 for r in target_rows]
    confound_rows.append({"feature": "category_sports_or_pets", "auc_high_bad": auc(vals, labels), "auc_low_bad": auc([-v for v in vals], labels)})
    write_csv(OUT / "inbench_simple_confound_auc.csv", confound_rows)
    return {
        "fail_kind_counts": dict(Counter(r["fail_kind"] for r in target_rows)),
        "confounds": confound_rows,
    }


def write_report(results):
    def fmt(x, d=3): return "n/a" if not finite(x) else f"{x:.{d}f}"
    meta = results["crossjudge_meta"]
    meta_lines = []
    for r in meta:
        if r["group"] in {"matched", "unmatched", "matched_minus_unmatched"}:
            meta_lines.append(f"| {r['run']} | {r['group']} | {r['n_videos']} | {r['n_questions']} | {fmt(r['mean'])} | [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] | {r['wins']}/{r['losses']}/{r['ties']} | {fmt(r['sign_p_one_sided'],4)} |")
    lc = results["length_control"]
    triage = results["triage"]
    # selected budget lines
    curve_lines = []
    for r in triage["curves"]:
        if r["budget_frac"] in {0.1, 0.2, 0.3} and r["target"] == "adqa_fail" and r["feature"] in {"mean_visual_gap", "max_visual_gap"}:
            curve_lines.append(f"| {r['feature']} | {int(r['budget_frac']*100)}% | {r['hits']}/{r['total_pos']} | {fmt(r['recall'])} | {fmt(r['precision'])} |")
    early_lines = []
    for r in triage["early_exit"]:
        if abs(r["frac"] - 0.25) < 1e-6 or abs(r["frac"] - (1/3)) < 1e-6:
            early_lines.append(f"| {r['gap_group']} | {fmt(r['frac'],2)} | {r['n']} | {fmt(r['adqa_fail_rate'])} | {fmt(r['ensemble_fail_rate'])} | {fmt(r['adqa_ensemble_full_order_agreement'])} |")
    tie = results["tie_confound"]
    confound_lines = []
    for r in tie["confounds"]:
        confound_lines.append(f"| {r['feature']} | {fmt(r['auc_high_bad'])} | {fmt(r['auc_low_bad'])} |")
    align = triage["alignment"]
    text = f"""---
title: TRIBE New Findings — Cached-Data Round 2
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_new_findings_round2.py
  - cursor/research/output/new_findings_round2/
---

# TRIBE New Findings — Cached-Data Round 2

Second no-API/no-GPU sweep. This turns more backlog items into actual local evidence.

## Finding 6 — cross-judge matched-question effect survives cluster bootstrap, but matched>unmatched is not uniformly strong

| Run | Group | videos | questions | mean delta | video-bootstrap 95% CI | W/L/T | sign p |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(meta_lines)}

Interpretation: the matched-question lift is real across judges. However, the **matched-minus-unmatched** contrast is strongest in the surgical/Opus subsets and weaker in the GPT-5 all-clip run, so paper language should say “targeted questions improve reliably” rather than “all unmatched questions are unaffected in every run.”

Artifact: `crossjudge_meta.csv`.

## Finding 7 — full-window gap-targeted AD gains are not explained by extra length alone, but length is a confound to report

Full-window generated AD is longer by an average of **{fmt(lc['mean_word_delta'])} words/clip** (median **{fmt(lc['median_word_delta'])}**) and improves ADQA by **{fmt(lc['mean_adqa_delta'])}**.

- Spearman(word delta, ADQA delta): **{fmt(lc['spearman_word_delta_vs_adqa_delta'])}**
- Linear slope: **{fmt(lc['linear_slope_adqa_per_word'],4)} ADQA per extra word**
- Low length-increase half ADQA delta: **{fmt(lc['low_length_half_mean_adqa_delta'])}**
- High length-increase half ADQA delta: **{fmt(lc['high_length_half_mean_adqa_delta'])}**
- Non-longer cases: n={lc['nonlonger_n']}, mean ADQA delta **{fmt(lc['nonlonger_mean_adqa_delta'])}**
- Win/loss/tie by clip: {lc['positive_adqa_wins']}/{lc['negative_adqa_losses']}/{lc['ties']}

Interpretation: targeted AD is somewhat longer, but more words do not explain the gain; if anything the low length-increase half has stronger gains. Still, every paper/demo statement should mention word-count control.

Artifact: `length_control_full_adqa.csv`.

## Finding 8 — review-budget curves support TRIBE as a triage queue, especially with mean visual gap

| Feature | Budget | ADQA failures caught | Recall | Precision |
|---|---:|---:|---:|---:|
{chr(10).join(curve_lines)}

Interpretation: `mean_visual_gap` is a better triage queue than `max_visual_gap` for ADQA failures in this cached external check. Use budget curves, not only AUC.

Artifact: `external_triage_budget_curves.csv`.

## Finding 9 — low-pressure early exit is plausible for review reduction, not for CLIP-only replacement

| Gap group | frac | n | ADQA fail rate | Ensemble fail rate | ADQA/ensemble full-order agreement |
|---|---:|---:|---:|---:|---:|
{chr(10).join(early_lines)}

Interpretation: bottom-gap clips are safer under ensemble, but CLIP-only still fails often (see artifact). Early exit should mean “less human/frontier review,” not “drop to CLIP-only scoring.”

Artifact: `low_pressure_early_exit.csv`.

## Finding 10 — old all4_fail targets are not a strict-tie artifact

Fail-kind counts from the in-benchmark TRIBE target audit:

```json
{json.dumps(tie['fail_kind_counts'], indent=2)}
```

Both positive clips are true inversions: one tier2/tier1 inversion and one negative T3 margin. This is important because a previous dual-signal claim was retracted for strict-tie artifacts; this TRIBE target does **not** appear to have that problem.

Artifact: `tie_target_audit_inbench.csv`.

## Finding 11 — simple/category confounds are not enough to explain the in-bench risk queue, but n=18 remains too small

| Feature | AUC high=bad | AUC low=bad |
|---|---:|---:|
{chr(10).join(confound_lines)}

Interpretation: `mean_standard_slot_score` remains the clean best feature, while category/duration/speech alternatives do not match it. But because family-wise p is only ~0.092 from round 1, this stays pilot/supporting evidence.

Artifact: `inbench_simple_confound_auc.csv`.

## Finding 12 — low AD-response alignment does not invalidate AV-vs-A triage, but it should quarantine P_AD/NCR claims

External rows split by `alignment_cosine > 0.5` from the TRIBE tensor manifest:

- All rows: n={align['all_n']}, mean-gap AUC vs ADQA fail **{fmt(align['all_mean_gap_auc_adqa_fail'])}**
- High-alignment rows: n={align['high_alignment_n']}, AUC **{fmt(align['hi_align_mean_gap_auc_adqa_fail'])}**, fail rate **{fmt(align['hi_align_adqa_fail_rate'])}**
- Low-alignment rows: n={align['low_alignment_n']}, AUC **{fmt(align['lo_align_mean_gap_auc_adqa_fail'])}**, fail rate **{fmt(align['lo_align_adqa_fail_rate'])}**

Interpretation: AV-vs-A triage does not depend directly on P_AD alignment, so the triage result can stand. But any AD-dependent TRIBE score, especially NCR/P_AD claims, must quarantine or separately analyze low-alignment clips.

## Round-2 action changes

1. Use `mean_visual_gap`, not `max_visual_gap`, for external review-budget plots unless a later run beats it.
2. Keep “low-gap early exit” as a review-cost claim only.
3. Add length-control sentence to gap-targeted generation claims.
4. Add tie-audit sentence to defend `all4_fail` target labels.
5. Quarantine low `alignment_cosine` clips for future P_AD/NCR experiments.
"""
    REPORT.write_text(text, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {
        "crossjudge_meta": crossjudge_meta(),
        "length_control": length_control(),
        "triage": triage_curves_and_early_exit(),
        "tie_confound": tie_and_confound_checks(),
    }
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    write_report(results)
    print(json.dumps({
        "report": str(REPORT),
        "out_dir": str(OUT),
        "crossjudge_rows": len(results["crossjudge_meta"]),
        "length_n": results["length_control"]["n"],
        "length_spearman": results["length_control"]["spearman_word_delta_vs_adqa_delta"],
        "fail_kind_counts": results["tie_confound"]["fail_kind_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
