#!/usr/bin/env python3
"""Selective-prediction analysis of the SHIP-BEST gate decision (round 72, claude).

Prior wrong_content_gate rounds all targeted the REJECT/catch decision (catch,
false-reject, confounder, noise margin, base-rate precision). This round targets
the *other* gate job — ship-best (pick the truly best AD from the genuine pool) —
and asks: what is a good ABSTENTION/confidence signal for it?

Two candidate confidence signals, both free (no LLM, no extra model):
  1. CROSS-signal agreement (CLIP pick == ADQA pick)  -- codex's consensus idea
  2. INTRA-signal margin (ADQA best - 2nd best)        -- this round

Finding: (1) fails (the minority signal, CLIP, is the wrong one), (2) is a
near-perfect confidence signal: abstaining the lowest-margin 20% -> 100% ship-best.
Every ship-best error but one is an exact ADQA tie.
"""
import csv, collections, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(ROOT, "cursor/output/external_ensemble_eval.csv")
OUT = os.path.join(ROOT, "cursor/output/gate_shipbest_selective.json")
GENUINE = ["tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
BEST = "tier3_va11y"


def load():
    clips = collections.defaultdict(dict)
    for r in csv.DictReader(open(CSV)):
        clips[r["video_id"]][r["tier"]] = r
    return {v: t for v, t in clips.items() if all(x in t for x in GENUINE)}


def vals(t, col):
    return {x: float(t[x][col]) for x in GENUINE}


def main():
    clips = load()
    n = len(clips)

    # --- per-clip picks + ADQA margin ---
    rec = []
    for vid, t in clips.items():
        a, c, e = (vals(t, col) for col in
                   ("adqa_norm", "clip_top3_norm", "ensemble_mean_clip_top3"))
        sv = sorted(a.values(), reverse=True)
        rec.append(dict(
            vid=vid,
            adqa_pick=max(a, key=a.get),
            clip_pick=max(c, key=c.get),
            ens_pick=max(e, key=e.get),
            adqa_margin=sv[0] - sv[1],
        ))

    correct = lambda p: p == BEST

    # --- signal 1: cross-signal (CLIP==ADQA) agreement abstention ---
    agree = [r for r in rec if r["adqa_pick"] == r["clip_pick"]]
    disagree = [r for r in rec if r["adqa_pick"] != r["clip_pick"]]
    agree_acc = sum(correct(r["adqa_pick"]) for r in agree) / len(agree)
    clip_right = sum(correct(r["clip_pick"]) for r in disagree)
    adqa_right = sum(correct(r["adqa_pick"]) for r in disagree)
    ens_right = sum(correct(r["ens_pick"]) for r in disagree)
    cross = dict(
        n_agree=len(agree), n_disagree=len(disagree),
        coverage=len(agree) / n, shipbest_acc_on_agree=agree_acc,
        disagree_clip_correct=clip_right, disagree_adqa_correct=adqa_right,
        disagree_ensemble_correct=ens_right,
    )

    # --- signal 2: ADQA intra-signal margin abstention (risk-coverage curve) ---
    rec.sort(key=lambda r: r["adqa_margin"], reverse=True)  # confident first
    curve = []
    for cov in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5):
        k = round(cov * n)
        kept = rec[:k]
        acc = sum(correct(r["adqa_pick"]) for r in kept) / k
        curve.append(dict(coverage=cov, n_kept=k, shipbest_acc=acc))

    ties = [r for r in rec if r["adqa_margin"] == 0.0]
    tie_err = sum(not correct(r["adqa_pick"]) for r in ties)
    total_err = sum(not correct(r["adqa_pick"]) for r in rec)

    full_acc = sum(correct(r["adqa_pick"]) for r in rec) / n
    out = dict(
        source=CSV, n_clips=n,
        full_coverage_shipbest_adqa=full_acc,
        full_coverage_shipbest_ensemble=sum(correct(r["ens_pick"]) for r in rec) / n,
        cross_signal_agreement_gate=cross,
        adqa_margin_risk_coverage=curve,
        adqa_tie_clips=len(ties), adqa_tie_errors=tie_err, total_errors=total_err,
    )
    json.dump(out, open(OUT, "w"), indent=2)

    print(f"n={n} clips  ship-best (full coverage): ADQA {full_acc:.1%}  "
          f"ensemble {out['full_coverage_shipbest_ensemble']:.1%}\n")
    print("[1] CROSS-signal agreement gate (CLIP pick == ADQA pick):")
    print(f"    agree on {cross['n_agree']}/{n} ({cross['coverage']:.0%}) "
          f"-> ship-best {agree_acc:.1%}  (WORSE than full {full_acc:.1%})")
    print(f"    on {cross['n_disagree']} disagreements: ADQA right {adqa_right}, "
          f"CLIP right {clip_right}, ensemble right {ens_right}")
    print(f"    -> minority signal (CLIP) is the wrong one; agreement is useless\n")
    print("[2] ADQA intra-signal margin gate (abstain smallest margin):")
    print("    coverage  ship-best  n_kept")
    for c in curve:
        print(f"      {c['coverage']:.0%}      {c['shipbest_acc']:.1%}     {c['n_kept']}")
    print(f"\n    {tie_err}/{total_err} ship-best errors are exact ADQA ties "
          f"({len(ties)} tie clips). Abstain the 20% lowest-margin -> 100%.")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
