"""TRIBE Blind Spot Router.

This turns saved TRIBE P_AV/P_A tensors into product-facing routing artifacts:

  - typed blind-spot timesteps: what kind of visual signal audio drops
  - coarse 3s windows: authoring/review slots that respect TRIBE timing limits
  - clip-level cases: where TRIBE should route SceneTwin beyond plain scoring

The central signal is per-timestep cortical divergence between audiovisual
prediction and audio-only prediction, restricted to functional ROI groups.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import tribe_tensors_load as T


ROOT = Path(__file__).resolve().parents[2]
MASK = ROOT / "output" / "scenetwin_description_gain" / "glasser_roi_mask.csv"
OUT_DIR = ROOT / "cursor" / "research" / "output"
REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-blind-spot-router.md"
WIKI = ROOT / "wiki" / "research" / "scenetwin-tribe-blind-spot-router.md"

WINDOW_SECONDS = 3.0

ROI_GROUPS = {
    "scene_spatial": [
        "early_visual_v1",
        "higher_visual_v2v3v4",
        "scene_ppa",
        "retrosplenial_pos",
    ],
    "agent_action": [
        "face_ffc",
        "body_eba_region",
        "motion_mt_complex",
        "lateral_object_loc",
    ],
    "auditory_language_control": [
        "auditory_control",
        "language_control",
    ],
}


def roi_vertices() -> dict[str, np.ndarray]:
    mask = pd.read_csv(MASK)
    mask = mask[mask["roi"] != "_unassigned_padding"]
    return {roi: group["vertex"].to_numpy(dtype=int) for roi, group in mask.groupby("roi")}


def cosine_gap(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(float)
    b = b.astype(float)
    return 1.0 - float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def safe_duration(meta: dict, manifest_row: pd.Series, n_steps: int) -> float:
    for value in (
        meta.get("duration_s"),
        manifest_row.get("duration_s"),
        (manifest_row.get("end_s", np.nan) - manifest_row.get("start_s", np.nan)),
    ):
        try:
            duration = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(duration) and duration > 0:
            return duration
    return float(max(n_steps, 1))


def group_timestep_gap(p_av: np.ndarray, p_a: np.ndarray, verts: np.ndarray) -> np.ndarray:
    n = min(p_av.shape[0], p_a.shape[0])
    out = np.zeros(n, dtype=float)
    for t in range(n):
        out[t] = cosine_gap(p_av[t, verts], p_a[t, verts])
    return out


def dominant_type(scene_gap: float, agent_gap: float) -> str:
    return "scene_spatial" if scene_gap >= agent_gap else "agent_action"


def route_window(row: pd.Series, high_threshold: float) -> str:
    if row["peak_visual_gap"] < high_threshold:
        return "static_ad_ok_low_gap"
    if row["dominant_type"] == "scene_spatial":
        return "layout_replay_or_scene_cue"
    return "action_state_or_agent_cue"


def build_timesteps() -> pd.DataFrame:
    idx = roi_vertices()
    group_verts = {
        name: np.concatenate([idx[roi] for roi in rois if roi in idx])
        for name, rois in ROI_GROUPS.items()
    }

    rows = []
    manifest = T.load_manifest()
    for _, manifest_row in manifest.iterrows():
        clip_key = manifest_row["clip_key"]
        try:
            tensors, meta = T.load_clip(clip_key)
        except FileNotFoundError:
            continue

        p_av = tensors["P_AV"]
        p_a = tensors["P_A"]
        n = min(p_av.shape[0], p_a.shape[0])
        duration = safe_duration(meta, manifest_row, n)
        step = duration / max(n, 1)

        gaps = {
            name: group_timestep_gap(p_av, p_a, verts)
            for name, verts in group_verts.items()
        }
        visual_gap = np.maximum(gaps["scene_spatial"], gaps["agent_action"])

        for t in range(n):
            scene = float(gaps["scene_spatial"][t])
            agent = float(gaps["agent_action"][t])
            control = float(gaps["auditory_language_control"][t])
            dom = dominant_type(scene, agent)
            rows.append(
                {
                    "clip_key": clip_key,
                    "corpus": meta.get("corpus") or manifest_row.get("corpus"),
                    "clip_idx": manifest_row.get("clip_idx"),
                    "video_id": meta.get("video_id") or manifest_row.get("video_id"),
                    "category": meta.get("category") or manifest_row.get("category"),
                    "duration_s": duration,
                    "t": t,
                    "start_s": t * step,
                    "end_s": (t + 1) * step,
                    "scene_spatial_gap": scene,
                    "agent_action_gap": agent,
                    "control_gap": control,
                    "visual_gap": float(visual_gap[t]),
                    "dominant_type": dom,
                    "dominance_margin": abs(scene - agent),
                    "visual_minus_control": float(visual_gap[t] - control),
                }
            )

    return pd.DataFrame(rows)


def build_windows(timesteps: pd.DataFrame) -> pd.DataFrame:
    df = timesteps.copy()
    df["window_idx"] = np.floor(df["start_s"] / WINDOW_SECONDS).astype(int)
    high_threshold = float(df["visual_gap"].quantile(0.75))

    rows = []
    for (clip_key, window_idx), group in df.groupby(["clip_key", "window_idx"], sort=False):
        scene = float(group["scene_spatial_gap"].mean())
        agent = float(group["agent_action_gap"].mean())
        control = float(group["control_gap"].mean())
        peak = float(group["visual_gap"].max())
        dom = dominant_type(scene, agent)
        rec = {
            "clip_key": clip_key,
            "corpus": group["corpus"].iloc[0],
            "clip_idx": group["clip_idx"].iloc[0],
            "video_id": group["video_id"].iloc[0],
            "category": group["category"].iloc[0],
            "window_idx": int(window_idx),
            "start_s": float(group["start_s"].min()),
            "end_s": float(group["end_s"].max()),
            "scene_spatial_gap": scene,
            "agent_action_gap": agent,
            "control_gap": control,
            "mean_visual_gap": float(group["visual_gap"].mean()),
            "peak_visual_gap": peak,
            "dominant_type": dom,
            "dominance_margin": abs(scene - agent),
            "visual_minus_control": float(max(scene, agent) - control),
            "raw_trs": int(len(group)),
        }
        rec["route"] = route_window(pd.Series(rec), high_threshold)
        rows.append(rec)

    out = pd.DataFrame(rows)
    return out.sort_values(["corpus", "clip_key", "start_s"])


def corr_or_nan(a: pd.Series, b: pd.Series) -> float:
    if len(a) < 2 or a.std() <= 1e-12 or b.std() <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a.to_numpy(dtype=float), b.to_numpy(dtype=float))[0, 1])


def build_clip_summary(timesteps: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for clip_key, group in timesteps.groupby("clip_key", sort=False):
        win = windows[windows["clip_key"] == clip_key]
        top = win.sort_values("peak_visual_gap", ascending=False).head(3)
        scene = group["scene_spatial_gap"]
        agent = group["agent_action_gap"]
        visual = group["visual_gap"]
        uniform = 1.0 / max(len(group), 1)
        top1_share = float(visual.max() / visual.sum()) if visual.sum() > 1e-9 else 0.0
        scene_peak_t = int(scene.idxmax())
        agent_peak_t = int(agent.idxmax())
        rows.append(
            {
                "clip_key": clip_key,
                "corpus": group["corpus"].iloc[0],
                "clip_idx": group["clip_idx"].iloc[0],
                "video_id": group["video_id"].iloc[0],
                "category": group["category"].iloc[0],
                "duration_s": float(group["duration_s"].iloc[0]),
                "n_trs": int(len(group)),
                "mean_scene_spatial_gap": float(scene.mean()),
                "mean_agent_action_gap": float(agent.mean()),
                "mean_control_gap": float(group["control_gap"].mean()),
                "mean_visual_gap": float(visual.mean()),
                "max_visual_gap": float(visual.max()),
                "dominant_clip_type": dominant_type(float(scene.mean()), float(agent.mean())),
                "scene_agent_time_rho": corr_or_nan(scene, agent),
                "scene_agent_peak_apart": int(scene_peak_t != agent_peak_t),
                "top1_share": top1_share,
                "uniform_null": uniform,
                "top1_vs_uniform": top1_share / uniform if uniform else float("nan"),
                "top_windows": "; ".join(
                    f"{r.start_s:.1f}-{r.end_s:.1f}s {r.dominant_type} ({r.route}, peak={r.peak_visual_gap:.3f})"
                    for r in top.itertuples(index=False)
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(["corpus", "max_visual_gap"], ascending=[True, False])


def build_cases(summary: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    high_gap = float(windows["peak_visual_gap"].quantile(0.75))
    high_concentration = float(summary["top1_vs_uniform"].quantile(0.75))

    rows = []
    for row in summary.itertuples(index=False):
        clip_windows = windows[windows["clip_key"] == row.clip_key]
        top_window = clip_windows.sort_values("peak_visual_gap", ascending=False).iloc[0]

        if row.max_visual_gap >= high_gap and row.dominant_clip_type == "scene_spatial":
            rows.append(
                {
                    "clip_key": row.clip_key,
                    "corpus": row.corpus,
                    "video_id": row.video_id,
                    "category": row.category,
                    "case_id": "scene_layout_replay",
                    "priority_score": row.max_visual_gap,
                    "window": f"{top_window.start_s:.1f}-{top_window.end_s:.1f}s",
                    "why": "Audio drops scene/spatial cortex most; route to layout cue, keyframe, or replay surface.",
                }
            )

        if row.max_visual_gap >= high_gap and row.dominant_clip_type == "agent_action":
            rows.append(
                {
                    "clip_key": row.clip_key,
                    "corpus": row.corpus,
                    "video_id": row.video_id,
                    "category": row.category,
                    "case_id": "agent_action_cue",
                    "priority_score": row.max_visual_gap,
                    "window": f"{top_window.start_s:.1f}-{top_window.end_s:.1f}s",
                    "why": "Audio drops face/body/motion/object cortex most; route to action-state or agent cue.",
                }
            )

        if row.scene_agent_peak_apart and row.scene_agent_time_rho < 0.5:
            rows.append(
                {
                    "clip_key": row.clip_key,
                    "corpus": row.corpus,
                    "video_id": row.video_id,
                    "category": row.category,
                    "case_id": "dynamic_type_shift",
                    "priority_score": 1.0 - max(row.scene_agent_time_rho, -1.0),
                    "window": row.top_windows,
                    "why": "Scene/spatial and agent/action losses peak at different moments; one global AD prompt is under-specified.",
                }
            )

        if row.top1_vs_uniform >= high_concentration:
            rows.append(
                {
                    "clip_key": row.clip_key,
                    "corpus": row.corpus,
                    "video_id": row.video_id,
                    "category": row.category,
                    "case_id": "moment_level_authoring",
                    "priority_score": row.top1_vs_uniform,
                    "window": f"{top_window.start_s:.1f}-{top_window.end_s:.1f}s",
                    "why": "Gap is temporally concentrated; spend AD/review budget on the peak window.",
                }
            )

        if row.max_visual_gap < high_gap:
            rows.append(
                {
                    "clip_key": row.clip_key,
                    "corpus": row.corpus,
                    "video_id": row.video_id,
                    "category": row.category,
                    "case_id": "low_gap_skip",
                    "priority_score": high_gap - row.max_visual_gap,
                    "window": row.top_windows,
                    "why": "No high TRIBE blind spot; do not spend expensive neural/human review budget here first.",
                }
            )

        if row.mean_control_gap >= row.mean_visual_gap:
            rows.append(
                {
                    "clip_key": row.clip_key,
                    "corpus": row.corpus,
                    "video_id": row.video_id,
                    "category": row.category,
                    "case_id": "audio_language_confound_check",
                    "priority_score": row.mean_control_gap - row.mean_visual_gap,
                    "window": row.top_windows,
                    "why": "Control cortex gap matches/exceeds visual gap; treat as audio/language anomaly, not visual AD need.",
                }
            )

    return pd.DataFrame(rows).sort_values(["case_id", "priority_score"], ascending=[True, False])


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in df.itertuples(index=False):
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:.3f}")
            else:
                text = str(value).replace("\n", " ").replace("|", "/")
                values.append(text)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def compact_table(df: pd.DataFrame, columns: list[str], n: int = 10) -> str:
    if df.empty:
        return "_No rows._"
    return markdown_table(df[columns].head(n))


def write_report(timesteps: pd.DataFrame, windows: pd.DataFrame,
                 summary: pd.DataFrame, cases: pd.DataFrame) -> None:
    case_counts = cases["case_id"].value_counts().rename_axis("case_id").reset_index(name="clips")
    route_counts = windows["route"].value_counts().rename_axis("route").reset_index(name="windows")
    external = summary[summary["corpus"] == "external"]
    low_rho = external["scene_agent_time_rho"] < 0.5
    peak_apart = external["scene_agent_peak_apart"] == 1

    top_cases = (
        cases[cases["case_id"] != "low_gap_skip"]
        .sort_values("priority_score", ascending=False)
    )
    top_windows = windows.sort_values("peak_visual_gap", ascending=False)

    report = f"""---
title: "TRIBE Blind Spot Router"
category: research
tags: [SceneTwin, TRIBE, tensors, accessibility, routing, audio-description]
created: 2026-05-31
updated: 2026-05-31
sources:
  - cursor/research/output/tribe_tensors/
  - output/scenetwin_description_gain/glasser_roi_mask.csv
  - cursor/research/output/tribe_blind_spot_timesteps.csv
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_blind_spot_cases.csv
---

# TRIBE Blind Spot Router

## Claim

The surviving use case for TRIBE in SceneTwin is not direct AD scoring. It is a
typed blind-spot router: compare TRIBE's audiovisual prediction (`P_AV`) against
audio-only prediction (`P_A`) to identify **when** audio drops visual information
and **what kind** of visual information is lost.

This makes TRIBE operationally necessary because CLIP+ADQA can rank candidate
descriptions, but it cannot expose cortical, time-localized, ROI-typed access
gaps before a description exists.

## Outputs

- `tribe_blind_spot_timesteps.csv`: per-TR scene/spatial, agent/action, and control gaps.
- `tribe_blind_spot_windows.csv`: 3s authoring/review windows with a route.
- `tribe_blind_spot_clip_summary.csv`: per-clip concentration and type-shift features.
- `tribe_blind_spot_cases.csv`: deployment cases SceneTwin can act on.

## Case Inventory

{markdown_table(case_counts)}

## Window Routes

{markdown_table(route_counts)}

## External Generalization Check

On the 60 external clips:

- Scene/action temporal correlation < 0.5 in {int(low_rho.sum())}/{len(external)} clips.
- Scene and action peaks occur at different TRIBE timesteps in {int(peak_apart.sum())}/{len(external)} clips.
- Mean top-1 concentration is {external["top1_vs_uniform"].mean():.2f}x a uniform-timing null.

These are exactly the conditions where a single scalar or one generic AD prompt
is insufficient: the access need is typed and moment-specific.

## Highest-Priority Cases

{compact_table(top_cases, ["case_id", "corpus", "video_id", "category", "priority_score", "window", "why"], 16)}

## Highest-Gap Windows

{compact_table(top_windows, ["corpus", "video_id", "category", "start_s", "end_s", "dominant_type", "peak_visual_gap", "route"], 16)}

## Product Use

The router should sit upstream of scoring:

1. Run TRIBE once per clip to get `P_AV` and `P_A`.
2. Convert tensor gaps into typed 3s windows.
3. Use top windows to create targeted ADQA questions, AD authoring prompts,
   replay/keyframe surfaces, or human-review queues.
4. Leave CLIP+ADQA as the scoring layer.

Recommended product name: **Neural Blind Spot Map**.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    WIKI.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    WIKI.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timesteps = build_timesteps()
    windows = build_windows(timesteps)
    summary = build_clip_summary(timesteps, windows)
    cases = build_cases(summary, windows)

    timesteps.to_csv(OUT_DIR / "tribe_blind_spot_timesteps.csv", index=False)
    windows.to_csv(OUT_DIR / "tribe_blind_spot_windows.csv", index=False)
    summary.to_csv(OUT_DIR / "tribe_blind_spot_clip_summary.csv", index=False)
    cases.to_csv(OUT_DIR / "tribe_blind_spot_cases.csv", index=False)
    write_report(timesteps, windows, summary, cases)

    print("TRIBE Blind Spot Router")
    print(f"  timesteps: {len(timesteps)}")
    print(f"  windows:   {len(windows)}")
    print(f"  clips:     {len(summary)}")
    print(f"  cases:     {len(cases)}")
    print("\nCase inventory:")
    print(cases["case_id"].value_counts().to_string())
    print(f"\nWrote {OUT_DIR / 'tribe_blind_spot_cases.csv'}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
