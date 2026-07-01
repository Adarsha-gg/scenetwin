#!/usr/bin/env python3
"""
Round 70 — claude — wrong_content_gate
Separation-margin + measurement-noise robustness of the locked wrong-content gate.

Every prior round in this loop (gate_outcome, LOCO thresholds, Bayesian base-rate,
two-scorer CLIP consensus) reports the 100% catch on NOISE-FREE scores. None asks:
how much score *headroom* backs that 100%, and at what level of measurement noise
does it break?

The deployed gate flags the lowest-scoring AD in a clip's candidate pool
(argmin of ensemble_mean_clip_top3) as wrong-content. The catch survives only while
the cross-content AD stays the minimum. This script:

  1. Separation margin per clip = (2nd-lowest ensemble score) - (lowest). In the
     per-clip min-max-normalised ensemble the cross AD is pinned to 0.0, so the margin
     IS the normalised score of the nearest genuine AD. Reported in raw signal units too.
  2. z-margin = raw margin / within-clip SD of the genuine ADs' scores — how many
     "natural genuine-AD score units" separate the wrong AD from the nearest real one.
  3. Monte-Carlo noise robustness: inject Gaussian measurement noise into the RAW
     signals (adqa_score, clip_top3) at sigma swept as a fraction of the pooled
     within-clip genuine-AD SD, re-normalise per clip, re-decide. Catch rate vs sigma
     gives the brittleness curve and the noise level at which catch falls below 99/95%.

Free, no LLM. Reads only cursor/output/external_ensemble_eval.csv.
"""
import csv, json, statistics as st, random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cursor/output/external_ensemble_eval.csv"
OUT = ROOT / "cursor/output/gate_margin_robustness.json"

WRONG = "tier0_cross"
RAW_SIGNALS = ["adqa_score", "clip_top3"]


def load():
    rows = list(csv.DictReader(open(SRC)))
    clips = defaultdict(dict)  # video_id -> tier -> {signal: val}
    for r in rows:
        clips[r["video_id"]][r["tier"]] = {s: float(r[s]) for s in RAW_SIGNALS}
    return clips


def normalise(vals):
    """per-clip min-max, matches ensemble_mean_clip_top3 construction."""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return [0.0 for _ in vals]
    return [(v - lo) / (hi - lo) for v in vals]


def ensemble_scores(clip, noise=None, rng=None):
    """Return {tier: normalised ensemble score} with optional raw-signal noise."""
    tiers = list(clip.keys())
    perturbed = {}
    for t in tiers:
        d = {}
        for s in RAW_SIGNALS:
            v = clip[t][s]
            if noise is not None:
                v = v + rng.gauss(0.0, noise[s])
            d[s] = v
        perturbed[t] = d
    # normalise each signal across the pool, then mean -> ensemble
    norm = {}
    for s in RAW_SIGNALS:
        ns = normalise([perturbed[t][s] for t in tiers])
        for t, x in zip(tiers, ns):
            norm.setdefault(t, []).append(x)
    return {t: st.mean(v) for t, v in norm.items()}


def flagged_is_wrong(scores):
    flagged = min(scores, key=scores.get)
    return flagged == WRONG


def main():
    clips = load()
    n = len(clips)

    # ---- 1+2. separation margins (noise-free) ----
    margins_norm, z_margins = [], []
    genuine_sd = {s: [] for s in RAW_SIGNALS}  # pooled within-clip genuine SD per signal
    base_catch = 0
    for vid, clip in clips.items():
        scores = ensemble_scores(clip)
        if flagged_is_wrong(scores):
            base_catch += 1
        ordered = sorted(scores.values())
        margins_norm.append(ordered[1] - ordered[0])  # 2nd lowest - lowest
        # raw z-margin on each signal: gap to nearest genuine / genuine SD
        for s in RAW_SIGNALS:
            gvals = [clip[t][s] for t in clip if t != WRONG]
            sd = st.pstdev(gvals) if len(gvals) > 1 else 0.0
            genuine_sd[s].append(sd)
            if sd > 1e-9:
                margin = min(gvals) - clip[WRONG][s]
                z_margins.append(margin / sd)

    pooled_sd = {s: st.mean(genuine_sd[s]) for s in RAW_SIGNALS}

    def pct(xs, p):
        xs = sorted(xs)
        return xs[max(0, min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1)))))]

    # ---- 3. Monte-Carlo noise robustness ----
    random.seed(70)
    B = 2000
    sigmas = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]  # x pooled genuine SD
    curve = []
    rng = random.Random(70)
    for frac in sigmas:
        noise = {s: frac * pooled_sd[s] for s in RAW_SIGNALS}
        if frac == 0.0:
            curve.append({"sigma_frac": frac, "catch_rate": base_catch / n,
                          "ci95": [base_catch / n, base_catch / n]})
            continue
        trial_rates = []
        for _ in range(B):
            c = sum(flagged_is_wrong(ensemble_scores(clip, noise, rng))
                    for clip in clips.values())
            trial_rates.append(c / n)
        trial_rates.sort()
        curve.append({
            "sigma_frac": frac,
            "catch_rate": round(st.mean(trial_rates), 4),
            "ci95": [round(trial_rates[int(0.025 * B)], 4),
                     round(trial_rates[int(0.975 * B)], 4)],
        })

    # noise level where mean catch first drops below thresholds
    def break_sigma(thresh):
        for pt in curve:
            if pt["catch_rate"] < thresh:
                return pt["sigma_frac"]
        return None

    result = {
        "source": str(SRC),
        "n_clips": n,
        "noise_free_catch": base_catch / n,
        "separation_margin": {
            "normalised_ensemble": {
                "median": round(st.median(margins_norm), 4),
                "min": round(min(margins_norm), 4),
                "p10": round(pct(margins_norm, 10), 4),
                "frac_le_0": round(sum(m <= 0 for m in margins_norm) / n, 4),
            },
            "z_margin_raw_signals": {
                "median": round(st.median(z_margins), 3),
                "min": round(min(z_margins), 3),
                "p10": round(pct(z_margins, 10), 3),
                "frac_lt_1sigma": round(sum(z < 1 for z in z_margins) / len(z_margins), 4),
            },
            "pooled_genuine_sd": {s: round(v, 4) for s, v in pooled_sd.items()},
        },
        "noise_robustness_curve": curve,
        "catch_below_99pct_at_sigma_frac": break_sigma(0.99),
        "catch_below_95pct_at_sigma_frac": break_sigma(0.95),
        "interpretation": (
            "Gate flags argmin of per-clip ensemble. Headroom = median z-margin of "
            f"{round(st.median(z_margins),2)} genuine-AD SDs; 100% catch tolerates "
            "Gaussian measurement noise up to the reported sigma before degrading."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
