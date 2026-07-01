#!/usr/bin/env python3
"""Analyze TRIBE Neural Contrastive Retrieval (NCR) outputs.

Input from Colab runner:
  cursor/research/output/ncr_similarity.csv
  cursor/research/output/ncr_external60_metadata.json

Outputs:
  cursor/research/output/ncr_query_metrics.csv
  cursor/research/output/ncr_summary.json
  output/reports/tribe-ncr-results.md

No third-party dependencies required.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "research" / "output"
SIM_CSV = OUT_DIR / "ncr_similarity.csv"
META_JSON = OUT_DIR / "ncr_external60_metadata.json"
QUERY_CSV = OUT_DIR / "ncr_query_metrics.csv"
SUMMARY_JSON = OUT_DIR / "ncr_summary.json"
REPORT = ROOT / "output" / "reports" / "tribe-ncr-results.md"
TENSOR_HEALTH = OUT_DIR / "new_findings_local" / "tensor_health_rows.csv"
TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rankdata(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg
        i = j
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    if len(x) < 2 or len(x) != len(y):
        return float("nan")
    mx, my = mean(x), mean(y)
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    if vx <= 0 or vy <= 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(vx * vy)


def spearman(x: list[float], y: list[float]) -> float:
    return pearson(rankdata(x), rankdata(y))


def binom_sf_ge(k: int, n: int, p: float = 0.5) -> float:
    if n <= 0:
        return float("nan")
    return sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


def ci(vals: list[float], rng: random.Random, n_boot: int = 4000) -> tuple[float, float]:
    vals = [v for v in vals if math.isfinite(v)]
    if not vals:
        return (float("nan"), float("nan"))
    boots = []
    for _ in range(n_boot):
        boots.append(mean(rng.choice(vals) for _ in vals))
    boots.sort()
    return boots[int(0.025 * (len(boots) - 1))], boots[int(0.975 * (len(boots) - 1))]


def ols_residuals(x: list[float], y: list[float]) -> list[float]:
    mx, my = mean(x), mean(y)
    vx = sum((a - mx) ** 2 for a in x)
    b = 0.0 if vx == 0 else sum((a - mx) * (b_ - my) for a, b_ in zip(x, y)) / vx
    a = my - b * mx
    return [yy - (a + b * xx) for xx, yy in zip(x, y)]


def load_metadata() -> dict[str, dict]:
    if not META_JSON.exists():
        return {}
    return {row["video_id"]: row for row in json.loads(META_JSON.read_text(encoding="utf-8"))}


def load_alignment() -> dict[str, float]:
    out: dict[str, float] = {}
    if not TENSOR_HEALTH.exists():
        return out
    for row in read_csv(TENSOR_HEALTH):
        if row.get("corpus") == "external":
            try:
                out[row["video_id"]] = float(row.get("alignment_cosine", "nan"))
            except ValueError:
                pass
    return out


def compute_query_metrics(rows: list[dict[str, str]], meta: dict[str, dict], alignment: dict[str, float]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["query_vid"], row["tier"])].append(row)
    out = []
    for (qvid, tier), vals in groups.items():
        scored = [(r["ref_vid"], float(r["cos"])) for r in vals]
        scored.sort(key=lambda x: x[1], reverse=True)
        n = len(scored)
        ref_to_cos = dict(scored)
        if qvid not in ref_to_cos or n < 2:
            continue
        self_cos = ref_to_cos[qvid]
        rank = 1 + sum(1 for _rv, c in scored if c > self_cos)
        rank_pct = (n - rank) / (n - 1) if n > 1 else float("nan")
        distractors = [c for rv, c in scored if rv != qvid]
        distractor_mean = mean(distractors) if distractors else float("nan")
        distractor_sd = math.sqrt(mean((c - distractor_mean) ** 2 for c in distractors)) if distractors else float("nan")
        margin = self_cos - distractor_mean
        source_vid = str(meta.get(qvid, {}).get("tier0_source_vid", "")) if tier == "tier0_cross" else ""
        source_rank = source_rank_pct = source_cos = float("nan")
        if source_vid and source_vid in ref_to_cos:
            source_cos = ref_to_cos[source_vid]
            source_rank = 1 + sum(1 for _rv, c in scored if c > source_cos)
            source_rank_pct = (n - source_rank) / (n - 1) if n > 1 else float("nan")
        wc = meta.get(qvid, {}).get("word_counts", {}).get(tier, "")
        out.append({
            "query_vid": qvid,
            "tier": tier,
            "gt": GT.get(tier, ""),
            "n_refs": n,
            "correct_rank": rank,
            "correct_rank_pct": rank_pct,
            "self_cos": self_cos,
            "distractor_mean_cos": distractor_mean,
            "cos_margin": margin,
            "z_margin": margin / distractor_sd if distractor_sd and math.isfinite(distractor_sd) and distractor_sd > 0 else float("nan"),
            "top_ref": scored[0][0],
            "top_cos": scored[0][1],
            "source_vid": source_vid,
            "source_rank": source_rank,
            "source_rank_pct": source_rank_pct,
            "source_cos": source_cos,
            "word_count": wc,
            "alignment_cosine": alignment.get(qvid, float("nan")),
            "high_alignment": alignment.get(qvid, 1.0) > 0.5,
        })
    return out


def aggregate(query_rows: list[dict[str, object]]) -> dict:
    rng = random.Random(20260623)
    by_tier: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in query_rows:
        by_tier[str(row["tier"])].append(row)
    tiers = {}
    for tier in TIERS:
        vals = by_tier.get(tier, [])
        rps = [float(r["correct_rank_pct"]) for r in vals if math.isfinite(float(r["correct_rank_pct"]))]
        margins = [float(r["cos_margin"]) for r in vals if math.isfinite(float(r["cos_margin"]))]
        ranks = [float(r["correct_rank"]) for r in vals if math.isfinite(float(r["correct_rank"]))]
        lo, hi = ci(rps, rng) if rps else (float("nan"), float("nan"))
        tiers[tier] = {
            "n": len(vals),
            "mean_rank_pct": mean(rps) if rps else float("nan"),
            "rank_pct_ci95": [lo, hi],
            "median_rank": median(ranks) if ranks else float("nan"),
            "mean_cos_margin": mean(margins) if margins else float("nan"),
        }
    long_gt = [float(r["gt"]) for r in query_rows if r.get("gt") != ""]
    long_rank = [float(r["correct_rank_pct"]) for r in query_rows if r.get("gt") != ""]
    long_margin = [float(r["cos_margin"]) for r in query_rows if r.get("gt") != ""]
    summary = {
        "n_queries": len(query_rows),
        "n_clips": len({str(r["query_vid"]) for r in query_rows}),
        "tiers": tiers,
        "spearman_gt_rank_pct": spearman(long_gt, long_rank),
        "spearman_gt_cos_margin": spearman(long_gt, long_margin),
    }
    # Corrected 3-tier signal excludes fake long-VATEX rung.
    three = [r for r in query_rows if str(r["tier"]) in {"tier0_cross", "tier1_vatex_short", "tier3_va11y"}]
    summary["spearman_gt_rank_pct_3tier"] = spearman([float(r["gt"]) for r in three], [float(r["correct_rank_pct"]) for r in three]) if three else float("nan")
    # Length residualization.
    with_wc = [r for r in query_rows if str(r.get("word_count", "")).strip()]
    if len(with_wc) >= 3:
        x = [float(r["word_count"]) for r in with_wc]
        y = [float(r["correct_rank_pct"]) for r in with_wc]
        res = ols_residuals(x, y)
        summary["spearman_gt_rank_pct_length_residual"] = spearman([float(r["gt"]) for r in with_wc], res)
        summary["spearman_word_count_rank_pct"] = spearman(x, y)
    # Pairwise per clip.
    by_vid: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for r in query_rows:
        by_vid[str(r["query_vid"])][str(r["tier"])] = r
    pairs = {}
    for lo in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
        wins = losses = ties = 0
        diffs = []
        for tiers_for_vid in by_vid.values():
            if "tier3_va11y" not in tiers_for_vid or lo not in tiers_for_vid:
                continue
            d = float(tiers_for_vid["tier3_va11y"]["correct_rank_pct"]) - float(tiers_for_vid[lo]["correct_rank_pct"])
            diffs.append(d)
            if d > 0:
                wins += 1
            elif d < 0:
                losses += 1
            else:
                ties += 1
        pairs[f"tier3_gt_{lo}"] = {
            "n": len(diffs),
            "mean_diff_rank_pct": mean(diffs) if diffs else float("nan"),
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "one_sided_sign_p": binom_sf_ge(wins, wins + losses),
        }
    summary["tier3_pairwise"] = pairs
    # Wrong-content source leakage check.
    t0 = [r for r in query_rows if str(r["tier"]) == "tier0_cross" and math.isfinite(float(r.get("source_rank_pct", float("nan"))))]
    if t0:
        summary["tier0_source_leakage"] = {
            "n": len(t0),
            "mean_target_rank_pct": mean(float(r["correct_rank_pct"]) for r in t0),
            "mean_source_rank_pct": mean(float(r["source_rank_pct"]) for r in t0),
            "source_gt_target_count": sum(float(r["source_rank_pct"]) > float(r["correct_rank_pct"]) for r in t0),
        }
    # High-alignment sensitivity.
    high = [r for r in query_rows if bool(r.get("high_alignment"))]
    low = [r for r in query_rows if not bool(r.get("high_alignment"))]
    if high and low:
        summary["alignment_sensitivity"] = {
            "high_alignment_queries": len(high),
            "low_alignment_queries": len(low),
            "high_alignment_spearman_rank_pct": spearman([float(r["gt"]) for r in high], [float(r["correct_rank_pct"]) for r in high]),
            "low_alignment_spearman_rank_pct": spearman([float(r["gt"]) for r in low], [float(r["correct_rank_pct"]) for r in low]),
        }
    return summary


def safe_fmt(x: object, digits: int = 3) -> str:
    try:
        v = float(x)
    except Exception:
        return str(x)
    if not math.isfinite(v):
        return "NA"
    return f"{v:.{digits}f}"


def write_outputs(query_rows: list[dict[str, object]], summary: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "query_vid", "tier", "gt", "n_refs", "correct_rank", "correct_rank_pct", "self_cos",
        "distractor_mean_cos", "cos_margin", "z_margin", "top_ref", "top_cos", "source_vid",
        "source_rank", "source_rank_pct", "source_cos", "word_count", "alignment_cosine", "high_alignment",
    ]
    with QUERY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(query_rows)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, allow_nan=True), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "title: TRIBE Neural Contrastive Retrieval Results",
        "category: research",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "sources:",
        "  - cursor/research/output/ncr_similarity.csv",
        "  - cursor/research/output/ncr_query_metrics.csv",
        "  - cursor/research/output/ncr_summary.json",
        "---",
        "",
        "# TRIBE Neural Contrastive Retrieval Results",
        "",
        f"Analyzed **{summary['n_queries']}** query vectors across **{summary['n_clips']}** clips. This Colab run used TTS-audio-only AD queries and video+audio references with text stages disabled, because the full TRIBE text extractor requires gated Llama access.",
        "",
        "| Tier | n | mean correct-rank pct | 95% bootstrap CI | median rank | mean cosine margin |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for tier in TIERS:
        t = summary["tiers"].get(tier, {})
        ci_vals = t.get("rank_pct_ci95", [float("nan"), float("nan")])
        lines.append(
            f"| {tier} | {t.get('n', 0)} | {safe_fmt(t.get('mean_rank_pct'))} | "
            f"[{safe_fmt(ci_vals[0])}, {safe_fmt(ci_vals[1])}] | {safe_fmt(t.get('median_rank'), 1)} | {safe_fmt(t.get('mean_cos_margin'))} |"
        )
    lines += [
        "",
        "## Aggregate signal",
        "",
        f"- Spearman(tier, correct-rank percentile), 4-tier: **{safe_fmt(summary.get('spearman_gt_rank_pct'))}**",
        f"- Spearman(tier, cosine margin), 4-tier: **{safe_fmt(summary.get('spearman_gt_cos_margin'))}**",
        f"- Spearman(tier, correct-rank percentile), corrected 3-tier: **{safe_fmt(summary.get('spearman_gt_rank_pct_3tier'))}**",
        f"- Spearman(word count, rank pct): **{safe_fmt(summary.get('spearman_word_count_rank_pct'))}**",
        f"- Spearman(tier, length-residual rank pct): **{safe_fmt(summary.get('spearman_gt_rank_pct_length_residual'))}**",
        "",
        "## Tier-3 pairwise wins by clip",
        "",
        "| Comparison | n | mean diff | W/L/T | one-sided sign p |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, p in summary.get("tier3_pairwise", {}).items():
        lines.append(f"| {name} | {p['n']} | {safe_fmt(p['mean_diff_rank_pct'])} | {p['wins']}/{p['losses']}/{p['ties']} | {safe_fmt(p['one_sided_sign_p'], 4)} |")
    if "tier0_source_leakage" in summary:
        s = summary["tier0_source_leakage"]
        lines += [
            "",
            "## Wrong-content source leakage check",
            "",
            f"For tier0_cross, mean target-rank pct = **{safe_fmt(s['mean_target_rank_pct'])}** and mean source-rank pct = **{safe_fmt(s['mean_source_rank_pct'])}**; source rank beat target rank on **{s['source_gt_target_count']}/{s['n']}** clips.",
        ]
    if "alignment_sensitivity" in summary:
        a = summary["alignment_sensitivity"]
        lines += [
            "",
            "## Alignment quarantine sensitivity",
            "",
            f"High-alignment queries: {a['high_alignment_queries']}, low-alignment queries: {a['low_alignment_queries']}.",
            f"High-alignment Spearman = **{safe_fmt(a['high_alignment_spearman_rank_pct'])}**; low-alignment Spearman = **{safe_fmt(a['low_alignment_spearman_rank_pct'])}**.",
        ]
    lines += [
        "",
        "## Interpretation guardrail",
        "",
        "This score is AD-dependent, but this run is the TTS-audio-only variant rather than the full gated text-extractor variant. Treat the small positive pairwise/source-specificity signals as pilot evidence only; do not market NCR as a working brain-grounded ranker without a pre-registered text-vs-audio ablation.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not SIM_CSV.exists():
        raise SystemExit(f"Missing {SIM_CSV}; run/download Colab NCR first")
    meta = load_metadata()
    alignment = load_alignment()
    query_rows = compute_query_metrics(read_csv(SIM_CSV), meta, alignment)
    summary = aggregate(query_rows)
    write_outputs(query_rows, summary)
    print(f"Wrote {QUERY_CSV}")
    print(f"Wrote {SUMMARY_JSON}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
