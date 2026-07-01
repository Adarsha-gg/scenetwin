#!/usr/bin/env python3
"""Post-hoc analysis of NCR full-run results for hidden patterns/guardrails."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cursor" / "research" / "output" / "ncr_hidden_patterns"
OUT.mkdir(parents=True, exist_ok=True)
QUERY = ROOT / "cursor" / "research" / "output" / "ncr_query_metrics.csv"
META = ROOT / "cursor" / "research" / "output" / "ncr_external60_metadata.json"
ENS = ROOT / "cursor" / "output" / "external_ensemble_eval.csv"
BLIND = ROOT / "cursor" / "research" / "output" / "tribe_blind_spot_clip_summary.csv"
REPORT = ROOT / "output" / "reports" / "tribe-ncr-hidden-patterns.md"
TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x: object, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def rankdata(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and xs[order[j]] == xs[order[i]]:
            j += 1
        r = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[order[k]] = r
        i = j
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    if len(x) < 2 or len(x) != len(y): return float("nan")
    mx, my = mean(x), mean(y)
    vx, vy = sum((v-mx)**2 for v in x), sum((v-my)**2 for v in y)
    if vx <= 0 or vy <= 0: return float("nan")
    return sum((a-mx)*(b-my) for a,b in zip(x,y)) / math.sqrt(vx*vy)


def spearman(x: list[float], y: list[float]) -> float:
    return pearson(rankdata(x), rankdata(y))


def binom_sf_ge(k: int, n: int) -> float:
    if n <= 0: return float("nan")
    return sum(math.comb(n, i) * 0.5**n for i in range(k, n+1))


def auc(scores: list[float], labels: list[int], high_bad: bool = True) -> float:
    vals = [(s if high_bad else -s, y) for s, y in zip(scores, labels) if math.isfinite(s)]
    pos = [s for s,y in vals if y]
    neg = [s for s,y in vals if not y]
    if not pos or not neg: return float("nan")
    wins = ties = 0
    for p in pos:
        for n in neg:
            if p > n: wins += 1
            elif p == n: ties += 1
    return (wins + 0.5*ties) / (len(pos)*len(neg))


def fmt(x: object, d: int = 3) -> str:
    try: v = float(x)
    except Exception: return str(x)
    return "NA" if not math.isfinite(v) else f"{v:.{d}f}"


def corrected_fail_flags(rows: list[dict[str,str]], score_col: str) -> dict[str, int]:
    """Corrected ladder failure: wrong-content < short crowd caption < pro AD.

    The long-VATEX tier is intentionally excluded because it is a fake/noisy rung.
    """
    by = defaultdict(dict)
    for r in rows:
        by[r["video_id"]][r["tier"]] = f(r[score_col])
    out = {}
    for vid, vals in by.items():
        if all(t in vals for t in ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]):
            out[vid] = int(not (vals["tier3_va11y"] > vals["tier1_vatex_short"] > vals["tier0_cross"]))
    return out


def main() -> None:
    qrows = read_csv(QUERY)
    meta = {r["video_id"]: r for r in json.loads(META.read_text(encoding="utf-8"))}
    blind = {r["video_id"]: r for r in read_csv(BLIND) if r.get("corpus") == "external"}
    ens_rows = read_csv(ENS)
    adqa_fail = corrected_fail_flags(ens_rows, "adqa_score")
    ensemble_fail = corrected_fail_flags(ens_rows, "ensemble_mean_clip_top3")

    by_vid = defaultdict(dict)
    for r in qrows:
        by_vid[r["query_vid"]][r["tier"]] = r

    clip_rows = []
    for vid, tiers in by_vid.items():
        if not all(t in tiers for t in TIERS):
            continue
        t3 = f(tiers["tier3_va11y"]["correct_rank_pct"])
        t2 = f(tiers["tier2_vatex_long"]["correct_rank_pct"])
        t1 = f(tiers["tier1_vatex_short"]["correct_rank_pct"])
        t0 = f(tiers["tier0_cross"]["correct_rank_pct"])
        src = f(tiers["tier0_cross"].get("source_rank_pct"))
        row = {
            "video_id": vid,
            "category": meta.get(vid, {}).get("category", ""),
            "tier3_rank_pct": t3,
            "tier3_minus_tier0": t3 - t0,
            "tier3_minus_tier1": t3 - t1,
            "tier3_minus_tier2": t3 - t2,
            "tier0_source_minus_target": src - t0,
            "tier0_source_rank_pct": src,
            "tier0_target_rank_pct": t0,
            "adqa_fail": adqa_fail.get(vid, ""),
            "ensemble_fail": ensemble_fail.get(vid, ""),
            "mean_visual_gap": f(blind.get(vid, {}).get("mean_visual_gap")),
            "max_visual_gap": f(blind.get(vid, {}).get("max_visual_gap")),
            "top1_vs_uniform": f(blind.get(vid, {}).get("top1_vs_uniform")),
            "dominant_clip_type": blind.get(vid, {}).get("dominant_clip_type", ""),
        }
        clip_rows.append(row)

    with (OUT / "ncr_clip_patterns.csv").open("w", newline="", encoding="utf-8") as fp:
        fields = list(clip_rows[0].keys()) if clip_rows else []
        w = csv.DictWriter(fp, fieldnames=fields); w.writeheader(); w.writerows(clip_rows)

    # Category summaries.
    cat_rows = []
    for cat in sorted({r["category"] for r in clip_rows}):
        rs = [r for r in clip_rows if r["category"] == cat]
        wins_t1 = sum(r["tier3_minus_tier1"] > 0 for r in rs)
        losses_t1 = sum(r["tier3_minus_tier1"] < 0 for r in rs)
        src_wins = sum(r["tier0_source_minus_target"] > 0 for r in rs)
        cat_rows.append({
            "category": cat,
            "n": len(rs),
            "mean_t3_minus_t1": mean(r["tier3_minus_tier1"] for r in rs),
            "t3_gt_t1_w_l_t": f"{wins_t1}/{losses_t1}/{len(rs)-wins_t1-losses_t1}",
            "mean_source_minus_target": mean(r["tier0_source_minus_target"] for r in rs),
            "source_gt_target": f"{src_wins}/{len(rs)}",
            "mean_t3_rank_pct": mean(r["tier3_rank_pct"] for r in rs),
        })
    with (OUT / "ncr_category_patterns.csv").open("w", newline="", encoding="utf-8") as fp:
        fields = list(cat_rows[0].keys()) if cat_rows else []
        w = csv.DictWriter(fp, fieldnames=fields); w.writeheader(); w.writerows(cat_rows)

    # Hubness/top-ref attractors.
    top_ref_counts = Counter(r["top_ref"] for r in qrows)
    top_ref_by_tier = {t: Counter(r["top_ref"] for r in qrows if r["tier"] == t).most_common(5) for t in TIERS}
    self_top1 = {t: sum(r["top_ref"] == r["query_vid"] for r in qrows if r["tier"] == t) for t in TIERS}
    tier_counts = {t: sum(1 for r in qrows if r["tier"] == t) for t in TIERS}
    tier0 = [r for r in qrows if r["tier"] == "tier0_cross"]
    source_top1 = sum(r["top_ref"] == r["source_vid"] for r in tier0)
    source_gt_target = sum(f(r["source_rank_pct"]) > f(r["correct_rank_pct"]) for r in tier0)
    source_lt_target = sum(f(r["source_rank_pct"]) < f(r["correct_rank_pct"]) for r in tier0)

    # Correlations/AUCs with existing signals.
    corr_rows = []
    features = ["tier3_rank_pct", "tier3_minus_tier0", "tier3_minus_tier1", "tier0_source_minus_target"]
    for feat in features:
        xs = [r[feat] for r in clip_rows]
        for target, labelmap in [("adqa_fail", adqa_fail), ("ensemble_fail", ensemble_fail)]:
            ys = [int(r[target]) for r in clip_rows if r[target] != ""]
            x2 = [r[feat] for r in clip_rows if r[target] != ""]
            corr_rows.append({
                "feature": feat,
                "target": target,
                "spearman": spearman(x2, ys),
                "auc_high_predicts_fail": auc(x2, ys, True),
                "n": len(x2),
                "positives": sum(ys),
            })
    for feat in ["mean_visual_gap", "max_visual_gap", "top1_vs_uniform"]:
        pairs = [(r[feat], r["tier3_minus_tier1"]) for r in clip_rows if math.isfinite(r[feat])]
        corr_rows.append({"feature": feat, "target": "tier3_minus_tier1", "spearman": spearman([p[0] for p in pairs], [p[1] for p in pairs]), "auc_high_predicts_fail": "", "n": len(pairs), "positives": ""})
    with (OUT / "ncr_correlations.csv").open("w", newline="", encoding="utf-8") as fp:
        fields = list(corr_rows[0].keys()) if corr_rows else []
        w = csv.DictWriter(fp, fieldnames=fields); w.writeheader(); w.writerows(corr_rows)

    # Top positive/negative examples.
    strongest = sorted(clip_rows, key=lambda r: r["tier3_minus_tier1"], reverse=True)[:8]
    weakest = sorted(clip_rows, key=lambda r: r["tier3_minus_tier1"])[:8]
    source_cases = sorted(clip_rows, key=lambda r: r["tier0_source_minus_target"], reverse=True)[:8]

    summary = {
        "self_top1_by_tier": {t: {"hits": self_top1[t], "n": tier_counts[t], "rate": self_top1[t]/tier_counts[t]} for t in TIERS},
        "tier0_source_top1": {"hits": source_top1, "n": len(tier0), "rate": source_top1/len(tier0)},
        "tier0_source_gt_target": {"wins": source_gt_target, "losses": source_lt_target, "ties": len(tier0)-source_gt_target-source_lt_target, "one_sided_sign_p": binom_sf_ge(source_gt_target, source_gt_target+source_lt_target)},
        "top_ref_counts": top_ref_counts.most_common(12),
        "top_ref_by_tier": top_ref_by_tier,
        "category_rows": cat_rows,
        "correlations": corr_rows,
    }
    (OUT / "ncr_hidden_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=True), encoding="utf-8")

    lines = [
        "---",
        "title: TRIBE NCR Hidden Patterns and Guardrails",
        "category: research",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "sources:",
        "  - cursor/research/output/ncr_query_metrics.csv",
        "  - cursor/research/output/ncr_hidden_patterns/",
        "---",
        "",
        "# TRIBE NCR Hidden Patterns and Guardrails",
        "",
        "This analyzes the full 60-clip NCR run after the first headline pass. The run used the robust **TTS-audio-only AD query** variant because the full TRIBE text extractor requires gated Llama access; video references used video+audio with text stages disabled.",
        "",
        "## Bottom line",
        "",
        "NCR is **not a revolutionary ranking metric** in this form: tier means stay near chance and global Spearman is ~0.03. The useful signal is weaker and narrower: professional AD beats the short crowd caption on 36/57 non-tie clips (sign p=0.031), and wrong-content AD retrieves its source clip more often than its target (37/60). That is a mechanism hint, not a headline result.",
        "",
        "## Retrieval hubness / top-1 rates",
        "",
        "| Tier | self top-1 hits | rate |",
        "|---|---:|---:|",
    ]
    for t in TIERS:
        s = summary["self_top1_by_tier"][t]
        lines.append(f"| {t} | {s['hits']}/{s['n']} | {s['rate']:.3f} |")
    lines += [
        "",
        f"Wrong-content source top-1: **{source_top1}/{len(tier0)}** ({source_top1/len(tier0):.3f}). Source rank > target rank: **{source_gt_target}/{len(tier0)}**, one-sided sign p={binom_sf_ge(source_gt_target, source_gt_target+source_lt_target):.4f}.",
        "",
        "Most common top-reference attractors across all queries:",
        "",
    ]
    for vid, count in top_ref_counts.most_common(8):
        lines.append(f"- `{vid}`: {count} top-1 assignments")
    lines += [
        "",
        "Interpretation: top-1 retrieval is sparse and hubbed; a few references attract many AD queries. Use rank-percentile/margins and source controls, not top-1 accuracy alone.",
        "",
        "## Category splits",
        "",
        "| Category | n | mean T3-T1 rank pct | T3>T1 W/L/T | mean source-target | source>target |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(cat_rows, key=lambda x: x["mean_t3_minus_t1"], reverse=True):
        lines.append(f"| {r['category']} | {r['n']} | {fmt(r['mean_t3_minus_t1'])} | {r['t3_gt_t1_w_l_t']} | {fmt(r['mean_source_minus_target'])} | {r['source_gt_target']} |")
    lines += [
        "",
        "## Existing-failure correlations",
        "",
        "| Feature | Target | Spearman | AUC(high=>fail) | positives/n |",
        "|---|---|---:|---:|---:|",
    ]
    for r in corr_rows:
        if r["target"] in {"adqa_fail", "ensemble_fail"}:
            lines.append(f"| {r['feature']} | {r['target']} | {fmt(r['spearman'])} | {fmt(r['auc_high_predicts_fail'])} | {r['positives']}/{r['n']} |")
    lines += [
        "",
        "Failure labels use the corrected 3-tier ladder (cross < short crowd caption < pro AD), excluding the fake long-VATEX rung. NCR does not obviously predict existing ADQA/ensemble failure labels. That supports keeping TRIBE's current role as blind-spot routing/triage rather than replacing the scoring stack.",
        "",
        "## Strongest T3-vs-short positives",
        "",
    ]
    for r in strongest:
        lines.append(f"- `{r['video_id']}` ({r['category']}): T3-T1={fmt(r['tier3_minus_tier1'])}, source-target={fmt(r['tier0_source_minus_target'])}")
    lines += ["", "## Strongest T3-vs-short negatives", ""]
    for r in weakest:
        lines.append(f"- `{r['video_id']}` ({r['category']}): T3-T1={fmt(r['tier3_minus_tier1'])}, source-target={fmt(r['tier0_source_minus_target'])}")
    lines += [
        "",
        "## Paper implication",
        "",
        "Do **not** claim NCR solves AD-dependent brain scoring. The publishable value is a negative/guardrail plus a small source-specificity hint: when the wrong AD is a professional description from another clip, its TTS-audio TRIBE response weakly points to the source more than the target. The next scientifically clean version would require authenticated/gated text extractor access and a pre-registered text-vs-audio ablation, not more post-hoc thresholding.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
