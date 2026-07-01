#!/usr/bin/env python3
"""Audit SceneTwin/TRIBE claims for current support level and overclaim risks."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cursor" / "research" / "output" / "new_findings_claims_audit"
REPORT = ROOT / "output" / "reports" / "tribe-claims-audit.md"

CLAIMS = [
    {
        "claim": "TRIBE is not an AD ranker / rho booster when represented as a clip-level gap.",
        "status": "confirmed structural guardrail",
        "evidence": "Per-clip constants cannot reorder candidate ADs within a clip; calibration/gating attempts failed externally.",
        "primary_sources": "cursor/findings/tribe-clip-level-triage.md; output/reports/paper-scenetwin-audit-framework.md",
        "allowed_wording": "TRIBE is a clip-level triage/router side-car, not part of the AD-level score.",
        "avoid_wording": "TRIBE improves rho / TRIBE calibrates continuous AD quality.",
    },
    {
        "claim": "In-benchmark TRIBE failure queue catches both all4_fail clips.",
        "status": "pilot/supporting evidence",
        "evidence": "AUC=1.00, recall@2=100%; family-wise max-stat p=0.0915 across 14 plausible features in local run #1.",
        "primary_sources": "output/reports/tribe-new-findings-local-run.md; output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv",
        "allowed_wording": "Pilot evidence that TRIBE can prioritize severe benchmark failures.",
        "avoid_wording": "Definitive AUC=1.00 proof without n=2/post-hoc caveat.",
    },
    {
        "claim": "External AV-vs-A mean visual gap provides moderate review triage for ADQA failures.",
        "status": "moderately supported external result",
        "evidence": "Mean visual gap AUC=0.672 vs ADQA failure; top 10/20/30% review catches 2/3/4 of 10 failures.",
        "primary_sources": "output/reports/tribe-new-findings-round2.md; cursor/research/output/new_findings_round2/external_triage_budget_curves.csv",
        "allowed_wording": "Useful review-budget signal, not a replacement scorer.",
        "avoid_wording": "High-recall automatic failure detector.",
    },
    {
        "claim": "Gap-targeted AD improves matched questions across judges.",
        "status": "strong supported mechanism claim",
        "evidence": "Video-cluster bootstrap: Haiku matched +0.167 CI [0.093,0.243], GPT-5 +0.113 CI [0.055,0.183], Opus17 +0.167 CI [0.036,0.333].",
        "primary_sources": "output/reports/tribe-new-findings-round2.md; cursor/research/output/new_findings_round2/crossjudge_meta.csv",
        "allowed_wording": "TRIBE-targeted generation improves the specific questions it targets.",
        "avoid_wording": "TRIBE globally improves all AD quality dimensions.",
    },
    {
        "claim": "Gap-targeted full-window AD gain is not explained by length alone.",
        "status": "supported guardrail",
        "evidence": "Word-delta vs ADQA-delta Spearman=0.049; non-longer cases still +0.050 ADQA.",
        "primary_sources": "output/reports/tribe-new-findings-round2.md; cursor/research/output/new_findings_round2/length_control_full_adqa.csv",
        "allowed_wording": "Word count is a confound checked in cached data; gains persist in low/no-length-increase cases.",
        "avoid_wording": "Length is irrelevant / fully ruled out.",
    },
    {
        "claim": "Current surgical target evidence is mostly scene/spatial.",
        "status": "supported limitation",
        "evidence": "Scene/spatial matched n=50, +0.150, p=0.0007; other route types have n<=4 in surgical cache.",
        "primary_sources": "output/reports/tribe-new-findings-local-run.md; cursor/research/output/new_findings_local/surgical_matched_delta_by_tribe_type.csv",
        "allowed_wording": "Scene/spatial route is best validated; other types are pending/underpowered.",
        "avoid_wording": "All route types are equally validated.",
    },
    {
        "claim": "ROI/profile evidence is scene/spatial-heavy.",
        "status": "supported limitation/interpretability",
        "evidence": "External dominant ROI counts: retrosplenial 30, V1 17, scene PPA 9; object/body/motion sparse.",
        "primary_sources": "output/reports/tribe-new-findings-round3.md; cursor/research/output/new_findings_round3/roi_dominant_failure_rates.csv",
        "allowed_wording": "TRIBE mainly supports scene/spatial blind-spot routing in current corpus.",
        "avoid_wording": "Robust body/face/motion/object specialization across corpus.",
    },
    {
        "claim": "TRIBE is competitive/different from transcript-armed VLM targeting, not decisively superior.",
        "status": "supported conservative finding",
        "evidence": "TRIBE-vs-VLM all-question +0.020 CI [-0.002,0.043]; matched +0.065 CI [0.017,0.113]; type disagreement 90.9%.",
        "primary_sources": "output/reports/tribe-new-findings-round3.md; cursor/research/output/new_findings_round3/necessity_rematch_bootstrap.csv",
        "allowed_wording": "Brain-grounded signal picks different targets and is competitive on matched questions.",
        "avoid_wording": "TRIBE beats VLM / TRIBE is necessary.",
    },
    {
        "claim": "Cheap-baseline gauntlet supports external TRIBE triage.",
        "status": "strongest current external triage support",
        "evidence": "For corrected external ADQA failures, accessibility_gap AUC=0.794 and category-shuffle p=0.003; category/transcript/duration baselines are weaker or unstable.",
        "primary_sources": "output/reports/parallel-research-cheap-baseline-gauntlet.md; cursor/research/output/parallel_research/cheap_baselines/auc_summary.csv",
        "allowed_wording": "TRIBE/gap-route features provide confound-checked review triage beyond category, transcript/speech, and duration baselines in cached external data.",
        "avoid_wording": "TRIBE is a high-recall automatic failure detector / beats every possible cheap proxy.",
    },
    {
        "claim": "Low-gap clips may be lower review priority.",
        "status": "supported hypothesis, not deployable skip policy",
        "evidence": "Bottom third max-gap: ADQA fail 0.050, ensemble fail 0.000; CLIP-only remains weak.",
        "primary_sources": "output/reports/parallel-research-access-surface-triage.md; cursor/research/output/parallel_research/access_surface/low_gap_early_exit.csv",
        "allowed_wording": "Low-gap can reduce review pressure after normal scoring.",
        "avoid_wording": "Low-gap means no AD needed / skip scoring.",
    },
    {
        "claim": "Route-specific hallucination gate is a stratified appendix result.",
        "status": "modest descriptive support",
        "evidence": "TRIBE route/high-gap modestly stratifies cached hallucination-gate behavior; best simple AUC for top-quartile CLIP drop is about 0.659.",
        "primary_sources": "output/reports/parallel-research-route-hallucination-gate.md; cursor/research/output/parallel_research/hallucination_gate/tribe_predictor_auc.csv",
        "allowed_wording": "TRIBE route can contextualize hallucination review sensitivity.",
        "avoid_wording": "TRIBE detects hallucinations / route alone is a hallucination-risk score.",
    },
    {
        "claim": "TRIBE-guided frame sampling is not yet validated as a temporal-action fix.",
        "status": "mixed/negative guardrail",
        "evidence": "High-need coverage improves, but action-route coverage is lower than uniform and cached ADQA rho is lower (0.782 vs 0.801).",
        "primary_sources": "output/reports/parallel-research-tribe-frame-sampling.md; cursor/research/output/parallel_research/frame_sampling/summary.json",
        "allowed_wording": "Current TRIBE frame sampling is a plausible coverage experiment that needs budget parity and rescoring.",
        "avoid_wording": "TRIBE frame sampling solves temporal blind spots / improves ADQA globally.",
    },
    {
        "claim": "Type-swapped prompt control remains pending.",
        "status": "blocked experiment",
        "evidence": "No cached same-clip/same-question generic/matched/swapped result exists; a frozen JSONL candidate batch has 15 records.",
        "primary_sources": "output/reports/parallel-research-type-swapped.md; cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl",
        "allowed_wording": "Type-swapped control is staged for approved future scoring.",
        "avoid_wording": "Swapped controls already prove route specificity.",
    },
    {
        "claim": "P_AD / NCR future claims must quarantine low-alignment rows.",
        "status": "data-quality guardrail",
        "evidence": "23 rows have alignment_cosine<=0.5; 35 AV/A temporal-length mismatches in tensor manifest audit. The 60-clip TTS-audio NCR run is near-null globally.",
        "primary_sources": "output/reports/tribe-new-findings-local-run.md; output/reports/tribe-ncr-results.md; cursor/research/output/new_findings_local/tensor_health_rows.csv",
        "allowed_wording": "Future AD-dependent TRIBE scores need alignment quarantine/sensitivity; current TTS-audio NCR is negative/guardrail evidence.",
        "avoid_wording": "NCR is a working brain-grounded AD scorer / all tensor-derived AD-response scores are equally reliable.",
    },
]

PATTERNS = [
    ("TRIBE improves rho", re.compile(r"TRIBE[^\n]{0,80}(improves|boosts|raises)[^\n]{0,40}(rho|ρ)", re.I)),
    ("calibration layer", re.compile(r"calibration[- ]layer", re.I)),
    ("beats VLM", re.compile(r"beats?\s+(a\s+)?VLM|TRIBE[^\n]{0,60}superior", re.I)),
    ("necessary", re.compile(r"TRIBE[^\n]{0,80}necessary|operationally necessary", re.I)),
    ("AUC=1 no caveat", re.compile(r"AUC\s*=\s*1\.00|AUC=1\.00", re.I)),
]

SCAN_GLOBS = [
    "output/reports/*.md",
    "wiki/research/scenetwin-tribe*.md",
    "cursor/findings/*tribe*.md",
]


def line_context(text: str, idx: int) -> tuple[int, str]:
    line_no = text[:idx].count("\n") + 1
    lines = text.splitlines()
    start = max(0, line_no - 2)
    end = min(len(lines), line_no + 1)
    return line_no, " / ".join(l.strip() for l in lines[start:end])[:500]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "claim_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(CLAIMS[0].keys()))
        w.writeheader(); w.writerows(CLAIMS)

    files = []
    for g in SCAN_GLOBS:
        files.extend(ROOT.glob(g))
    findings = []
    for p in sorted(set(files)):
        if p.resolve() == REPORT.resolve():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, pat in PATTERNS:
            for m in pat.finditer(text):
                line, ctx = line_context(text, m.start())
                findings.append({"pattern": label, "path": str(p.relative_to(ROOT)), "line": line, "context": ctx})
    with (OUT / "overclaim_scan.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pattern", "path", "line", "context"])
        w.writeheader(); w.writerows(findings)

    by_pattern = {}
    for r in findings:
        by_pattern[r["pattern"]] = by_pattern.get(r["pattern"], 0) + 1

    claim_lines = []
    for c in CLAIMS:
        claim_lines.append(f"| {c['claim']} | {c['status']} | {c['allowed_wording']} | {c['avoid_wording']} |")
    scan_lines = []
    for r in findings[:60]:
        scan_lines.append(f"| {r['pattern']} | `{r['path']}:{r['line']}` | {r['context'].replace('|','/')} |")

    report = f"""---
title: TRIBE Claims Audit
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_claims_audit.py
  - cursor/research/output/new_findings_claims_audit/
---

# TRIBE Claims Audit

This audit converts the new cached findings into paper-safe wording and scans existing markdown for overclaim-risk phrases. The scan is conservative: it flags false positives too, so treat it as review queue, not an automatic error list.

## Claim matrix

| Claim | Status | Safe wording | Avoid wording |
|---|---|---|---|
{chr(10).join(claim_lines)}

## Overclaim scan summary

```json
{json.dumps(by_pattern, indent=2)}
```

## First 60 scan hits

| Pattern | Location | Context |
|---|---|---|
{chr(10).join(scan_lines)}

## Action

Use this before editing paper/demo copy. The most important corrections are: keep AUC=1.00 as pilot evidence with n=2/family-wise p caveat; say competitive/different vs VLM, not beats VLM; and keep TRIBE out of rho/scoring language unless a future AD-dependent score such as NCR passes validation.
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "claims": len(CLAIMS), "scan_hits": len(findings), "by_pattern": by_pattern}, indent=2))

if __name__ == "__main__":
    main()
