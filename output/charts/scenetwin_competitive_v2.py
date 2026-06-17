"""Fig 1 - competitive map, restyled. Cost (log USD) vs quality (rho)."""
from __future__ import annotations

import matplotlib.pyplot as plt
import scenetwin_style as st

# (name, rho, cost_usd, kind, label_dx_pts, label_dy_pts, ha)
E = [
    ("SceneTwin (CLIP + ADQA)", 0.929, 0.001, "ours", 12, 6, "left"),
    ("LLM-AD-Eval",            0.899, 0.0001, "base", 10, 4, "left"),
    ("ADQA alone",             0.789, 0.0005, "base", 10, 6, "left"),
    ("VT consistency",         0.768, 0.0001, "base", -10, 8, "right"),
    ("Need-weighted CLIP",     0.733, 0.0005, "base", 10, -4, "left"),
    ("Story recall",           0.703, 0.0001, "base", -10, -6, "right"),
    ("CRITIC entity",          0.638, 0.00005, "base", 10, 6, "left"),
    ("Action coverage",        0.601, 0.0001, "base", 10, -10, "left"),
    ("Multi-ref R@3 (leakage)", 0.532, 0.00001, "leak", 12, 0, "left"),
    ("Gemini 2.5 Pro",         0.756, 0.0131, "vlm", 0, 12, "center"),
    ("GPT-5",                  0.727, 0.0263, "vlm", 0, -16, "center"),
    ("Claude Sonnet 4.6",      0.713, 0.0318, "vlm", 10, 4, "left"),
]
STYLE = {
    "ours": dict(c=st.OURS, m="*", s=520, ec=st.OURS_HI),
    "base": dict(c=st.NEUTRAL, m="o", s=95, ec=st.NEUTRAL_D),
    "vlm":  dict(c=st.VLM, m="s", s=110, ec="#2742A8"),
    "leak": dict(c=st.DANGER, m="X", s=110, ec="#8E2E36"),
}

fig, ax = st.figure(w=8.6, h=5.4)
st.style_axes(ax)
ax.set_xscale("log")

# desirable corner: high quality, low cost -> top-left. Shade it faintly (solid, very light).
ax.axhspan(0.85, 1.02, xmin=0, xmax=0.60, color="#EAF4F1", zorder=0)
ax.text(1.4e-5, 0.985, "best:  high quality, low cost", fontsize=9.5, color=st.OURS_HI,
        style="italic", va="top")

for name, rho, cost, kind, dx, dy, ha in E:
    s = STYLE[kind]
    ax.scatter(cost, rho, s=s["s"], marker=s["m"], color=s["c"], edgecolor=s["ec"],
               linewidth=1.3, zorder=5, clip_on=False)
    bold = kind == "ours"
    ax.annotate(name, (cost, rho), textcoords="offset points", xytext=(dx, dy),
                ha=ha, va="center", fontsize=10.5 if bold else 9.5,
                fontweight="bold" if bold else "normal",
                color=st.OURS_HI if bold else (st.VLM if kind == "vlm" else
                      (st.DANGER if kind == "leak" else st.MUTE)))

ax.set_xlim(7e-6, 7e-2)
ax.set_ylim(0.5, 1.0)
ax.set_xlabel("cost per evaluation  (USD, log scale)")
ax.set_ylabel("Spearman ρ  vs quality tiers  (in-benchmark)")
ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

# legend, top-right outside the cloud
import matplotlib.lines as mlines
handles = [
    mlines.Line2D([], [], marker="*", color="none", markerfacecolor=st.OURS,
                  markeredgecolor=st.OURS_HI, markersize=16, label="SceneTwin (ours)"),
    mlines.Line2D([], [], marker="s", color="none", markerfacecolor=st.VLM,
                  markeredgecolor="#2742A8", markersize=10, label="frontier VLM judge"),
    mlines.Line2D([], [], marker="o", color="none", markerfacecolor=st.NEUTRAL,
                  markeredgecolor=st.NEUTRAL_D, markersize=10, label="published baseline"),
    mlines.Line2D([], [], marker="X", color="none", markerfacecolor=st.DANGER,
                  markeredgecolor="#8E2E36", markersize=10, label="reference leakage (excluded)"),
]
ax.legend(handles=handles, loc="lower right", fontsize=9.5, handletextpad=0.4,
          borderaxespad=0.6, labelspacing=0.6)

st.titles(ax,
          "Best quality at the lowest cost, alone in the top-left",
          "Two cheap signals beat 10 published metrics and 3 frontier VLM judges that cost "
          "10 to 30 times more.")
st.save(fig, "scenetwin_competitive_v2")
