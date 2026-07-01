#!/usr/bin/env python3
"""Wrong-content gate: thin-but-genuine confounder separability (round 71, claude).

All prior wrong-content rounds measured tier0_cross against the BEST genuine tier
(gate_outcome argmin), against a global threshold over all tiers (r68), against
prevalence (r69), or against measurement noise (r70). None asked the deployment
question that actually drives FALSE REJECTS: can a fixed threshold reject a
wrong-content AD WITHOUT rejecting a sparse-but-correct AD?

The hardest genuine class for that is tier1_vatex_short: short, low-coverage, but
truthful. This script measures 2-class separability of tier0_cross (wrong, gt=0)
vs tier1_vatex_short (weakest genuine, gt=1) on each raw signal and the fusion,
and surfaces the per-signal complementary failure structure.

Free, no LLM. Reads cursor/output/external_ensemble_eval.csv.
"""
import csv, json, statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "cursor/output/external_ensemble_eval.csv"
OUT = ROOT / "cursor/output/wrong_content_confounder.json"

WRONG = "tier0_cross"          # wrong-content AD (gt=0)
HARD_GENUINE = "tier1_vatex_short"  # weakest truthful AD (gt=1) -> the confounder


def load():
    clips = defaultdict(dict)
    for r in csv.DictReader(open(CSV)):
        clips[r["video_id"]][r["tier"]] = {
            "clip": float(r["clip_top3"]),
            "adqa": float(r["adqa_score"]),
        }
    return clips


def auc(pos, neg):
    """P(pos > neg); pos = genuine-short (want high), neg = wrong (want low)."""
    n = w = 0
    for p in pos:
        for q in neg:
            n += 1
            w += 1.0 if p > q else (0.5 if p == q else 0.0)
    return w / n


def best_global(pos, neg):
    """Single threshold maximising accuracy separating the two classes."""
    vals = sorted(set(pos + neg))
    best = (0.0, None)
    for t in vals + [vals[0] - 1e-6]:
        acc = (sum(x >= t for x in pos) + sum(x < t for x in neg)) / (len(pos) + len(neg))
        if acc > best[0]:
            best = (acc, t)
    return best


def main():
    clips = load()
    C = list(clips)
    res = {"n_clips": len(C), "wrong_tier": WRONG, "confounder_tier": HARD_GENUINE,
           "question": "separate wrong-content from thin-but-genuine without falsely rejecting the genuine",
           "signals": {}}

    fail_clips = {}
    for sig in ("clip", "adqa"):
        pos = [clips[c][HARD_GENUINE][sig] for c in C]
        neg = [clips[c][WRONG][sig] for c in C]
        gaps = [clips[c][HARD_GENUINE][sig] - clips[c][WRONG][sig] for c in C]
        inv = [c for c, g in zip(C, gaps) if g <= 0]
        acc, thr = best_global(pos, neg)
        res["signals"][sig] = {
            "two_class_auc": round(auc(pos, neg), 4),
            "global_thr_acc": round(acc, 4),
            "global_thr": round(thr, 4),
            "gap_mean": round(st.mean(gaps), 4),
            "gap_median": round(st.median(gaps), 4),
            "gap_min": round(min(gaps), 4),
            "inversions": len(inv),
            "inversion_clips": inv,
        }
        fail_clips[sig] = set(inv)

    # fusion = raw clip + raw adqa
    posf = [clips[c][HARD_GENUINE]["clip"] + clips[c][HARD_GENUINE]["adqa"] for c in C]
    negf = [clips[c][WRONG]["clip"] + clips[c][WRONG]["adqa"] for c in C]
    gapsf = [p - q for p, q in zip(posf, negf)]
    acc, thr = best_global(posf, negf)
    res["signals"]["fused"] = {
        "two_class_auc": round(auc(posf, negf), 4),
        "global_thr_acc": round(acc, 4),
        "global_thr": round(thr, 4),
        "gap_min": round(min(gapsf), 4),
        "inversions": sum(g <= 0 for g in gapsf),
    }

    # complementarity: do the signals' confounder-failures overlap?
    inter = fail_clips["clip"] & fail_clips["adqa"]
    res["complementarity"] = {
        "adqa_only_fails": sorted(fail_clips["adqa"] - fail_clips["clip"]),
        "clip_only_fails": sorted(fail_clips["clip"] - fail_clips["adqa"]),
        "both_fail": sorted(inter),
        "clip_rescues_adqa_min_gap": round(
            min((clips[c][HARD_GENUINE]["clip"] - clips[c][WRONG]["clip"])
                for c in fail_clips["adqa"]), 4) if fail_clips["adqa"] else None,
    }
    OUT.write_text(json.dumps(res, indent=2))
    print(f"wrote {OUT}")
    for sig in ("clip", "adqa", "fused"):
        s = res["signals"][sig]
        print(f"  {sig:6s} AUC={s['two_class_auc']:.3f}  glob-thr acc={s['global_thr_acc']:.3f}  inversions={s['inversions']}/{len(C)}")
    print(f"  ADQA-only confounder fails: {len(res['complementarity']['adqa_only_fails'])}  "
          f"both-fail: {len(res['complementarity']['both_fail'])}  "
          f"CLIP rescue min-gap: {res['complementarity']['clip_rescues_adqa_min_gap']}")


if __name__ == "__main__":
    main()
