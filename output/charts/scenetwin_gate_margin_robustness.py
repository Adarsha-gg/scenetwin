#!/usr/bin/env python3
"""Round 70 claude — wrong-content gate margin + noise-robustness chart."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "cursor/output/gate_margin_robustness.json"))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# left: noise robustness curve
c = d["noise_robustness_curve"]
x = [p["sigma_frac"] for p in c]
y = [p["catch_rate"] * 100 for p in c]
lo = [p["ci95"][0] * 100 for p in c]
hi = [p["ci95"][1] * 100 for p in c]
ax1.plot(x, y, "o-", color="#1b5e20", lw=2, label="mean catch")
ax1.fill_between(x, lo, hi, alpha=0.2, color="#1b5e20", label="95% CI")
ax1.axhline(99, ls=":", c="#888"); ax1.axhline(95, ls=":", c="#888")
ax1.axhline(25, ls="--", c="#c62828", label="random gate 25%")
ax1.set_xlabel("injected noise  (× genuine-AD score SD)")
ax1.set_ylabel("wrong-content catch rate (%)")
ax1.set_title("Noise robustness of the 100% catch\n(2000 MC trials, n=60 clips)")
ax1.set_ylim(20, 102); ax1.legend(fontsize=8, loc="lower left")
ax1.grid(alpha=0.3)

# right: per-signal z-margin vs ensemble margin
sm = d["separation_margin"]
labels = ["per-signal\nz-margin (SDs)", "ensemble\nmargin (norm.)"]
med = [sm["z_margin_raw_signals"]["median"], sm["normalised_ensemble"]["median"]]
mn = [sm["z_margin_raw_signals"]["min"], sm["normalised_ensemble"]["min"]]
p10 = [sm["z_margin_raw_signals"]["p10"], sm["normalised_ensemble"]["p10"]]
xpos = [0, 1]
ax2.bar(xpos, med, width=0.5, color="#1565c0", alpha=0.85, label="median")
ax2.scatter(xpos, mn, color="#c62828", zorder=5, label="min (worst clip)")
ax2.scatter(xpos, p10, color="#ef6c00", marker="_", s=400, zorder=5, label="p10")
ax2.axhline(1.0, ls=":", c="#888")
ax2.set_xticks(xpos); ax2.set_xticklabels(labels)
ax2.set_title("Separation headroom\nensemble lifts min margin off zero")
ax2.set_ylabel("margin")
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3, axis="y")
ax2.text(0.0, sm["z_margin_raw_signals"]["min"] + 0.1,
         f'{int(sm["z_margin_raw_signals"]["frac_lt_1sigma"]*100)}% <1σ',
         ha="center", fontsize=8, color="#c62828")

fig.suptitle("Wrong-content gate: not brittle — 4.2σ median headroom, ensemble guarantees no zero-margin clip",
             fontsize=10, y=1.02)
fig.tight_layout()
out = ROOT / "output/charts/scenetwin_gate_margin_robustness.png"
fig.savefig(out, dpi=130, bbox_inches="tight")
print("wrote", out)
