#!/usr/bin/env python3
"""Wrong-content vs thin-but-genuine confounder separability (round 71, claude)."""
import csv, json
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "cursor/output/external_ensemble_eval.csv"
RES = json.load(open(ROOT / "cursor/output/wrong_content_confounder.json"))

clips = defaultdict(dict)
for r in csv.DictReader(open(CSV)):
    clips[r["video_id"]][r["tier"]] = {"clip": float(r["clip_top3"]), "adqa": float(r["adqa_score"])}
C = list(clips)
adqa_fail = set(RES["complementarity"]["adqa_only_fails"])

fig, axes = plt.subplots(1, 2, figsize=(11, 5))
for ax, sig, title in [(axes[0], "clip", "CLIP grounding"), (axes[1], "adqa", "ADQA")]:
    cross = [clips[c]["tier0_cross"][sig] for c in C]
    short = [clips[c]["tier1_vatex_short"][sig] for c in C]
    s = RES["signals"][sig]
    for i, c in enumerate(C):
        bad = c in adqa_fail and sig == "adqa"
        ax.plot([0, 1], [cross[i], short[i]], "-",
                color="#d62728" if bad else "#cccccc", lw=1.6 if bad else 0.7,
                zorder=3 if bad else 1, alpha=0.95 if bad else 0.6)
    ax.scatter([0] * len(C), cross, c="#d62728", s=22, label="wrong-content (tier0_cross)", zorder=4)
    ax.scatter([1] * len(C), short, c="#1f77b4", s=22, label="thin-but-genuine (vatex_short)", zorder=4)
    ax.axhline(s["global_thr"], ls="--", color="black", lw=1,
               label=f"best global thr {s['global_thr']:.3f}")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["wrong", "genuine-short"])
    ax.set_xlim(-0.35, 1.35)
    ax.set_title(f"{title}\n2-class AUC {s['two_class_auc']:.3f} | "
                 f"thr-acc {s['global_thr_acc']:.3f} | inversions {s['inversions']}/60")
    ax.set_ylabel("raw score")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(axis="y", alpha=0.25)

fig.suptitle("Wrong-content gate: can a fixed threshold spare thin-but-correct ADs?\n"
             "Red lines = 7 clips where ADQA puts a genuine short AD at-or-below wrong content (CLIP rescues all)",
             fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.93])
out = ROOT / "output/charts/scenetwin_wrong_content_confounder.png"
fig.savefig(out, dpi=130)
print(f"wrote {out}")
