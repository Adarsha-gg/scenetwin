#!/usr/bin/env python3
"""Chart: wrong-content gate precision vs deployment base rate (round 69 claude)."""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = os.path.join(ROOT, "cursor", "output", "gate_deployment_precision.json")
OUT = os.path.join(ROOT, "output", "charts", "scenetwin_gate_deployment_precision.png")

with open(J) as f:
    d = json.load(f)

rows = d["by_prevalence"]
prev = [r["prevalence"] for r in rows]
ppv = [r["loco"]["precision"] * 100 for r in rows]
alert = [r["loco"]["alert_rate"] * 100 for r in rows]
be = [b["min_cost_ratio_miss_over_review"] for b in d["break_even_cost_ratio"]]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

ax1.plot(prev, ppv, "o-", color="#c0392b", lw=2, label="precision (PPV)")
ax1.plot(prev, alert, "s--", color="#2980b9", lw=2, label="alert rate")
ax1.set_xscale("log")
ax1.set_xlabel("wrong-content base rate (prevalence)")
ax1.set_ylabel("percent")
ax1.set_title("Catch holds (recall 98%) but precision\ncollapses at realistic rarity")
ax1.axhline(50, color="grey", ls=":", lw=1)
ax1.grid(alpha=0.3)
ax1.legend(loc="center left")

ax2.plot(prev, be, "o-", color="#27ae60", lw=2)
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("wrong-content base rate (prevalence)")
ax2.set_ylabel("min cost(miss)/cost(review) to justify gate")
ax2.set_title("Cost asymmetry rescues it:\ngate wins if one missed error > a few reviews")
ax2.grid(alpha=0.3, which="both")

fig.suptitle("Wrong-content gate: deployment base-rate analysis (LOCO TPR=0.983, FPR=0.022)",
             fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=130)
print(f"Wrote {OUT}")
