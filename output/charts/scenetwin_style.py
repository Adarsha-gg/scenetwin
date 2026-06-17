"""Shared visual style for all SceneTwin paper figures.

Import this first in every figure script:

    import scenetwin_style as st
    fig, ax = st.figure(w=7.2, h=4.4)
    st.titles(ax, "The claim", "the setup / n")
    ...
    st.save(fig, "scenetwin_xxx_v2")

Design rules (locked):
  - one sans family (Helvetica Neue), clear type hierarchy
  - semantic palette, SOLID colors only (no gradients / no rgba fills) for PDF perf
  - no top/right spine, light horizontal grid only, generous margins
  - titles ABOVE the axes, left-aligned; grey subtitle under the title
  - direct value labels, legends outside the data
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---- palette: fixed semantic roles, never reuse a color for two meanings ----
OURS     = "#0F766E"   # teal: SceneTwin / the winning method / "good"
OURS_HI  = "#0B5C56"   # darker teal for accents/edges
NEUTRAL  = "#C2C7CE"   # grey fill: baselines / "before" / control
NEUTRAL_D= "#8A929B"   # darker grey for edges/secondary text
VLM      = "#3B5BDB"   # indigo: frontier VLM judges / alternatives
DANGER   = "#C2424D"   # brick red: hallucination / wrong-content / leakage / chance
HIGHLIGHT= "#E0A33E"   # amber: operating points / thresholds / the flagged stratum

OURS_SOFT = "#E7F2F0"  # pale teal fill for callout chips
AMBER_SOFT= "#FBF1DC"  # pale amber fill for threshold bands

INK      = "#1A1D21"   # near-black text
MUTE     = "#6B7280"   # muted grey text (subtitles, secondary labels)
GRID     = "#E8EAED"   # very light gridlines
PANEL    = "#FFFFFF"   # background

_FONT = "Helvetica Neue"


def use():
    mpl.rcParams.update({
        "font.family": _FONT,
        "font.size": 11,
        "text.color": INK,
        "axes.edgecolor": "#C9CDD2",
        "axes.linewidth": 1.0,
        "axes.labelcolor": INK,
        "axes.labelsize": 11,
        "axes.titlesize": 13,
        "axes.facecolor": PANEL,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 1.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTE,
        "ytick.color": MUTE,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "figure.facecolor": PANEL,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.facecolor": PANEL,
        "legend.frameon": False,
        "legend.fontsize": 10,
    })


def figure(w=7.2, h=4.4):
    use()
    fig, ax = plt.subplots(figsize=(w, h))
    return fig, ax


def titles(ax, title, subtitle=None, pad=14):
    """Bold left-aligned title above the axes, optional grey subtitle under it."""
    ax.set_title("")  # clear any default
    t = ax.annotate(title, xy=(0, 1), xytext=(0, pad + (14 if subtitle else 0)),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="left", va="bottom", fontsize=14, fontweight="bold", color=INK)
    if subtitle:
        ax.annotate(subtitle, xy=(0, 1), xytext=(0, pad),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="left", va="bottom", fontsize=10, color=MUTE)
    return t


def save(fig, stem):
    """Write 300dpi PNG (and SVG) to output/charts/<stem>.{png,svg}."""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    png = os.path.join(here, f"{stem}.png")
    fig.savefig(png)
    fig.savefig(os.path.join(here, f"{stem}.svg"))
    print("wrote", png)
    plt.close(fig)


def style_axes(ax):
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
