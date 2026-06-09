#!/usr/bin/env python3
"""Round 69 (claude) — wrong_content_gate, deployment base-rate precision.

Prior rounds locked the wrong-content gate's *intrinsic* operating point:
  - gate_outcome.py     : 100% catch / 0% false-reject on a BALANCED 1:3 pool design
  - wrong_content_global_gate.py : LOCO TPR=0.983, FPR=0.022 (single-AD global tau)

Both report catch/false-alarm at (near-)balanced prevalence. That is NOT the
deployment condition: in production, catastrophic wrong-content ADs are RARE.
This script answers the operator's real question via Bayes' rule:

  given the *locked* TPR/FPR, at a realistic base rate pi of wrong-content,
  what is the gate's PRECISION (PPV), how many ADs get flagged, and how many
  human re-reviews must an operator pay per genuine catch (Number-Needed-to-Review)?

No model calls, no pool re-ranking, no re-fit. It only READS the already-locked
TPR/FPR from wrong_content_global_gate.json and propagates them through base rates.
This is the honest deployment caveat on the headline catch — the base-rate fallacy
that a 2.2% false-alarm rate hides when legit ADs outnumber wrong ones 100:1.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = os.path.join(ROOT, "cursor", "output", "wrong_content_global_gate.json")
OUT = os.path.join(ROOT, "cursor", "output", "gate_deployment_precision.json")


def ppv(pi, tpr, fpr):
    """positive predictive value at prevalence pi."""
    num = pi * tpr
    den = pi * tpr + (1.0 - pi) * fpr
    return num / den if den > 0 else 0.0


def alert_rate(pi, tpr, fpr):
    """fraction of ALL ADs the gate flags for human re-review."""
    return pi * tpr + (1.0 - pi) * fpr


def main():
    with open(GATE) as f:
        g = json.load(f)

    # locked, honest single-AD operating point (leave-one-clip-out, never fit on the scored clip)
    loco = g["leave_one_clip_out"]
    tpr = loco["catch_rate"]      # 0.9833
    fpr = loco["false_alarm_rate"]  # 0.0222

    # also carry the conservative a-priori fixed threshold (0% false-alarm in-sample)
    fixed = g["fixed_threshold"]["0.15"]
    tpr_f, fpr_f = fixed["catch_rate"], fixed["false_alarm_rate"]

    prevalences = [0.50, 0.20, 0.10, 0.05, 0.02, 0.01, 0.005, 0.002]

    rows = []
    for pi in prevalences:
        p_loco = ppv(pi, tpr, fpr)
        a_loco = alert_rate(pi, tpr, fpr)
        # Number-Needed-to-Review: human re-reviews paid per genuine wrong-content caught
        nnr = (1.0 / p_loco) if p_loco > 0 else float("inf")
        # per 10k ADs
        alerts_10k = a_loco * 10000
        true_catches_10k = pi * tpr * 10000
        wasted_10k = (1.0 - pi) * fpr * 10000  # legit ADs needlessly re-reviewed
        missed_10k = pi * (1.0 - tpr) * 10000   # wrong-content shipped to a blind viewer

        # fixed-threshold (FPR=0) variant: precision is perfect, recall is 0.90
        p_fixed = ppv(pi, tpr_f, fpr_f)

        rows.append({
            "prevalence": pi,
            "loco": {
                "precision": round(p_loco, 4),
                "recall": tpr,
                "alert_rate": round(a_loco, 4),
                "number_needed_to_review": round(nnr, 2),
                "per_10k_ads": {
                    "alerts": round(alerts_10k, 1),
                    "true_catches": round(true_catches_10k, 1),
                    "wasted_reviews": round(wasted_10k, 1),
                    "missed_shipped": round(missed_10k, 2),
                },
            },
            "fixed_T015": {
                "precision": round(p_fixed, 4),
                "recall": tpr_f,
            },
        })

    # decision-theoretic break-even: the gate is net-beneficial when the cost of a
    # MISSED wrong-content (shipped to a blind viewer) exceeds the cost of the wasted
    # reviews it forces. Cost-ratio break-even C* = (false alerts)/(missed) flips with pi.
    # Operator pays FPR*(1-pi) wasted reviews; gains TPR*pi catches. Gate beats "ship all"
    # iff  c_miss * (catches gained) > c_review * (wasted reviews), i.e.
    #   c_miss/c_review > (1-pi)*fpr / (pi*tpr)
    break_even = []
    for pi in prevalences:
        ratio = ((1.0 - pi) * fpr) / (pi * tpr)
        break_even.append({
            "prevalence": pi,
            "min_cost_ratio_miss_over_review": round(ratio, 1),
        })

    result = {
        "source_gate": "wrong_content_global_gate.json (LOCO single-AD)",
        "operating_point_loco": {"tpr": tpr, "fpr": fpr},
        "operating_point_fixed_T015": {"tpr": tpr_f, "fpr": fpr_f},
        "note": "intrinsic catch is locked; this propagates it through realistic base rates",
        "by_prevalence": rows,
        "break_even_cost_ratio": break_even,
    }
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)

    print(f"locked operating point (LOCO): TPR={tpr:.3f}  FPR={fpr:.3f}")
    print()
    print(f"{'prev':>6} {'PPV':>7} {'alert%':>7} {'NNR':>6} {'wasted/10k':>11} {'missed/10k':>11}")
    for r in rows:
        l = r["loco"]
        print(f"{r['prevalence']:>6.3f} {l['precision']*100:>6.1f}% "
              f"{l['alert_rate']*100:>6.2f}% {l['number_needed_to_review']:>6.1f} "
              f"{l['per_10k_ads']['wasted_reviews']:>11.1f} {l['per_10k_ads']['missed_shipped']:>11.2f}")
    print()
    print("break-even cost ratio (cost_miss / cost_review) for gate to beat ship-all:")
    for b in break_even:
        print(f"  prev={b['prevalence']:>5.3f}  need miss>={b['min_cost_ratio_miss_over_review']:>6.1f}x review")
    print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
