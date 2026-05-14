#!/usr/bin/env python3
"""Build fsaverage5 ROI proxy masks from Nilearn's Destrieux surface atlas.

This unblocks ROI-restricted SceneTwin experiments without pretending we have
functional localizer ROIs. These are anatomical proxy groups on fsaverage5:
useful for smoke tests, not a replacement for Glasser/Wang/localizer masks.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from nilearn.datasets import fetch_atlas_surf_destrieux


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
OUT_CSV = DG_DIR / "destrieux_proxy_roi_mask.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-destrieux-roi-mask.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-destrieux-roi-mask.md"

N_VERTICES_HEMI = 10242

# Destrieux labels are anatomical parcels. Names below are intentionally
# suffixed with "_proxy" where they approximate functional systems.
ROI_LABELS = {
    "early_visual_v1_proxy": [
        "S_calcarine",
    ],
    "occipital_visual_proxy": [
        "G_cuneus",
        "G_occipital_middle",
        "G_occipital_sup",
        "G_and_S_occipital_inf",
        "Pole_occipital",
        "S_oc_middle_and_Lunatus",
        "S_oc_sup_and_transversal",
        "S_occipital_ant",
        "S_parieto_occipital",
    ],
    "ventral_visual_ffa_proxy": [
        "G_oc-temp_lat-fusifor",
    ],
    "scene_context_ppa_proxy": [
        "G_oc-temp_med-Parahip",
        "G_oc-temp_med-Lingual",
        "S_oc-temp_med_and_Lingual",
        "S_collat_transv_ant",
        "S_collat_transv_post",
    ],
    "retrosplenial_precuneus_proxy": [
        "G_cingul-Post-dorsal",
        "G_cingul-Post-ventral",
        "G_precuneus",
        "S_subparietal",
        "S_parieto_occipital",
    ],
    "lateral_object_loc_proxy": [
        "G_occipital_middle",
        "G_and_S_occipital_inf",
        "S_oc_middle_and_Lunatus",
        "S_oc-temp_lat",
        "G_oc-temp_lat-fusifor",
    ],
    "motion_mt_proxy": [
        "G_temporal_middle",
        "G_temporal_inf",
        "S_temporal_inf",
        "S_oc-temp_lat",
        "S_occipital_ant",
    ],
    "body_eba_proxy": [
        "G_oc-temp_lat-fusifor",
        "S_oc-temp_lat",
        "G_occipital_middle",
    ],
    "language_control": [
        "G_front_inf-Opercular",
        "G_front_inf-Triangul",
        "S_front_inf",
        "G_pariet_inf-Angular",
        "G_pariet_inf-Supramar",
        "G_temp_sup-Lateral",
        "G_temporal_middle",
    ],
    "auditory_control": [
        "G_temp_sup-G_T_transv",
        "G_temp_sup-Plan_polar",
        "G_temp_sup-Plan_tempo",
        "G_temp_sup-Lateral",
        "S_temporal_sup",
        "S_temporal_transverse",
    ],
}


def main() -> None:
    atlas = fetch_atlas_surf_destrieux()
    labels = list(atlas["labels"])
    label_to_index = {name: idx for idx, name in enumerate(labels)}
    maps = {
        "L": atlas["map_left"],
        "R": atlas["map_right"],
    }

    missing = sorted({name for names in ROI_LABELS.values() for name in names if name not in label_to_index})
    if missing:
        raise ValueError(f"Destrieux labels not found: {missing}")

    rows = []
    for roi, label_names in ROI_LABELS.items():
        label_indices = [label_to_index[name] for name in label_names]
        for hemi, hemi_map in maps.items():
            offset = 0 if hemi == "L" else N_VERTICES_HEMI
            for local_vertex, parcel_id in enumerate(hemi_map):
                parcel_id = int(parcel_id)
                if parcel_id in label_indices:
                    rows.append(
                        {
                            "roi": roi,
                            "vertex": offset + int(local_vertex),
                            "hemi": hemi,
                            "label_index": parcel_id,
                            "label_name": labels[parcel_id],
                            "atlas": "nilearn_destrieux_surface_fsaverage5",
                        }
                    )

    out = pd.DataFrame(rows).sort_values(["roi", "vertex"])
    summary = (
        out.groupby("roi")
        .agg(n_vertices=("vertex", "nunique"), labels=("label_name", lambda s: ", ".join(sorted(set(s)))))
        .reset_index()
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    report = f"""---
title: "SceneTwin Destrieux fsaverage5 ROI Proxy Mask"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5, Destrieux]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
  - https://nilearn.github.io/stable/auto_examples/01_plotting/plot_surf_atlas.html
---

# SceneTwin Destrieux fsaverage5 ROI Proxy Mask

## Status

Built a real fsaverage5 surface mask from Nilearn's Destrieux atlas. This is not a functional Glasser/Wang/localizer atlas; it is an anatomical proxy that unblocks ROI-restricted smoke tests.

## Summary

{summary.to_markdown(index=False)}

## Use

```bash
python tools/scenetwin_roi_gap_curve.py --mask output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
```

## Caveat

Labels such as `ventral_visual_ffa_proxy`, `scene_context_ppa_proxy`, `motion_mt_proxy`, and `body_eba_proxy` are coarse anatomical approximations. If these results look promising, replace this mask with a functional atlas/localizer mask before making strong neuroscience claims.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print(summary)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
