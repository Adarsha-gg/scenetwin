#!/usr/bin/env python3
"""Risk-coverage chart for the ship-best selective-prediction gate (round 72)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "cursor/output/gate_shipbest_selective.json")
PNG = os.path.join(ROOT, "output/charts/scenetwin_gate_shipbest_selective.png")

d = json.load(open(DATA))
curve = d["adqa_margin_risk_coverage"]
cov = [c["coverage"] * 100 for c in curve]
acc = [c["shipbest_acc"] * 100 for c in curve]

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(cov, acc, "o-", color="#1f5fa8", lw=2.5, ms=7, label="ADQA margin gate")
ax.axhline(d["full_coverage_shipbest_ensemble"] * 100, ls="--", color="#888",
           label=f"ensemble, full coverage ({d['full_coverage_shipbest_ensemble']:.0%})")
cross = d["cross_signal_agreement_gate"]
ax.plot(cross["coverage"] * 100, cross["shipbest_acc_on_agree"] * 100, "s",
        color="#c0392b", ms=10, label="CLIP↔ADQA agreement gate (fails)")
for c in curve:
    ax.annotate(f"{c['shipbest_acc']:.0%}", (c["coverage"] * 100, c["shipbest_acc"] * 100),
                textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
ax.set_xlabel("coverage (% of clips auto-shipped, rest -> human review)")
ax.set_ylabel("ship-best accuracy on shipped clips (%)")
ax.set_title("Ship-best becomes 100%% reliable by abstaining the\nlowest-margin 20%% "
             "(every error but one is an ADQA tie, n=%d)" % d["n_clips"])
ax.set_ylim(84, 101)
ax.invert_xaxis()
ax.grid(alpha=0.3)
ax.legend(loc="lower left", fontsize=8)
fig.tight_layout()
fig.savefig(PNG, dpi=130)
print("Wrote", PNG)
