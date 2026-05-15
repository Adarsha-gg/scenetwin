"""Render per-clip TRIBE brain panels for the web demo.

Each panel shows the predicted audiovisual response, audio-only response, and
the directional visual lift max(P_AV - P_A, 0) for one cached benchmark clip.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from nilearn.datasets import load_fsaverage
from nilearn.plotting import plot_surf_stat_map


ROOT = Path(__file__).resolve().parents[1]
PREDS = ROOT / "output" / "visual_closure_preds"
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = ROOT / "output" / "charts" / "tribe_clip_brains"
N_VERTS = 10242


def brain_mean(path: Path) -> np.ndarray:
    arr = np.load(path)
    if arr.ndim == 2:
        return arr.mean(axis=0)
    if arr.ndim == 1:
        return arr
    raise ValueError(f"Unexpected prediction shape for {path}: {arr.shape}")


def robust_max(values: np.ndarray, pct: float = 98.0) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 1.0
    val = float(np.percentile(np.abs(finite), pct))
    return max(val, 1e-6)


def hot_overlay_limits(values: np.ndarray, threshold_pct: float = 72.0) -> tuple[float, float]:
    """Return threshold/vmax for poster-style gray cortex with hot overlay."""
    finite = values[np.isfinite(values)]
    positive = finite[finite > 1e-8]
    if positive.size:
        finite = positive
    if finite.size == 0:
        return 0.0, 1.0
    threshold = float(np.percentile(finite, threshold_pct))
    vmax = float(np.percentile(finite, 98.5))
    if vmax <= threshold:
        vmax = threshold + 1e-6
    return threshold, vmax


def positive_response(values: np.ndarray) -> np.ndarray:
    """Render positive predicted response intensity, not signed model residuals."""
    return np.maximum(values, 0)


def plot_hemi_pair(fig, axes, fs, brain: np.ndarray, *, title: str, threshold: float, vmax: float) -> None:
    left = brain[:N_VERTS]
    right = brain[N_VERTS:]
    plot_surf_stat_map(
        fs["inflated"].parts["left"],
        stat_map=left,
        axes=axes[0],
        view=(0, 180),
        colorbar=False,
        bg_on_data=True,
        cmap="hot",
        threshold=threshold,
        vmin=threshold,
        vmax=vmax,
        darkness=None,
    )
    plot_surf_stat_map(
        fs["inflated"].parts["right"],
        stat_map=right,
        axes=axes[1],
        view=(0, 0),
        colorbar=False,
        bg_on_data=True,
        cmap="hot",
        threshold=threshold,
        vmin=threshold,
        vmax=vmax,
        darkness=None,
    )
    for ax in axes:
        ax.set_axis_off()
        ax.set_box_aspect(None, zoom=1.38)
    x0 = (axes[0].get_position().x0 + axes[1].get_position().x1) / 2
    fig.text(x0, 0.82, title, ha="center", va="center", fontsize=11, fontweight="bold")


def render_clip(row: pd.Series, fs) -> Path:
    clip_idx = int(row["clip_idx"])
    av_path = PREDS / f"clip_{clip_idx:02d}_P_AV.npy"
    a_path = PREDS / f"clip_{clip_idx:02d}_P_A.npy"
    if not av_path.exists() or not a_path.exists():
        raise FileNotFoundError(f"Missing TRIBE preds for clip_{clip_idx:02d}")

    av = positive_response(brain_mean(av_path))
    audio = positive_response(brain_mean(a_path))
    visual_lift = np.maximum(av - audio, 0)

    response_threshold, response_max = hot_overlay_limits(np.concatenate([av, audio]))
    lift_threshold, lift_max = hot_overlay_limits(visual_lift)

    fig, axes = plt.subplots(
        1,
        6,
        figsize=(12.8, 3.8),
        subplot_kw={"projection": "3d"},
        gridspec_kw={"wspace": -0.18, "left": 0.02, "right": 0.98, "bottom": 0.08, "top": 0.78},
    )
    fig.patch.set_facecolor("white")
    fig.text(
        0.02,
        0.96,
        f"clip_{clip_idx:02d} · {row['category']} · risk rank #{int(row['risk_rank'])}",
        ha="left",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#1f2328",
    )
    fig.text(
        0.02,
        0.90,
        f"TRIBE visual lift: max(P_AV - P_A, 0) · risk {float(row['risk_score']):.3f} · mean need {float(row['mean_need']):.2f}",
        ha="left",
        va="center",
        fontsize=10,
        color="#57606a",
    )

    plot_hemi_pair(
        fig, axes[0:2], fs, av,
        title="Audiovisual viewing  P_AV",
        threshold=response_threshold,
        vmax=response_max,
    )
    plot_hemi_pair(
        fig, axes[2:4], fs, audio,
        title="Audio only  P_A",
        threshold=response_threshold,
        vmax=response_max,
    )
    plot_hemi_pair(
        fig, axes[4:6], fs, visual_lift,
        title="Visual-only lift",
        threshold=lift_threshold,
        vmax=lift_max,
    )

    fig.text(0.18, 0.045, "visual + audio predicted cortex", ha="center", fontsize=9, style="italic", color="#6e7781")
    fig.text(0.50, 0.045, "soundtrack-only predicted cortex", ha="center", fontsize=9, style="italic", color="#6e7781")
    fig.text(0.82, 0.045, "only lights up when video adds signal beyond audio", ha="center", fontsize=9, style="italic", color="#6e7781")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"clip_{clip_idx:02d}_tribe_gap.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def main() -> None:
    rows = pd.read_csv(FORECAST).sort_values("clip_idx")
    fs = load_fsaverage(mesh="fsaverage5")
    rendered = []
    for _, row in rows.iterrows():
        out = render_clip(row, fs)
        rendered.append(out)
        print(out.relative_to(ROOT))
    print(f"Rendered {len(rendered)} clip brain panels")


if __name__ == "__main__":
    main()
