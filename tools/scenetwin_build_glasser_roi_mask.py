#!/usr/bin/env python3
"""Build fsaverage5 ROI masks from the Glasser HCP-MMP1.0 functional parcellation.

Replaces the Destrieux anatomical proxy mask with functionally-defined parcels.
PHA1/2/3 instead of the whole parahippocampal gyrus, FFC instead of the whole
fusiform, MT/MST/FST instead of "middle/inferior temporal gyrus." This is the
atlas the project should have started with for scene/face/motion claims.

Pipeline:
  1. Fetch fsaverage subject and HCP-MMP1.0 .annot via MNE.
  2. Read per-vertex parcel ids with nibabel.
  3. Take first 10242 vertices per hemisphere (fsaverage5 = icosahedron lvl 5;
     FreeSurfer fsaverage subjects are nested, so the first 10242 vertices in
     fsaverage map 1:1 to fsaverage5 vertices).
  4. Group Glasser parcels into SceneTwin functional ROIs.
  5. Write CSV in the same shape as `destrieux_proxy_roi_mask.csv`.

Outputs:
  output/scenetwin_description_gain/glasser_roi_mask.csv
  output/reports/scenetwin-glasser-roi-mask.md
  wiki/research/scenetwin-glasser-roi-mask.md
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

import mne
from mne.datasets import fetch_fsaverage, fetch_hcp_mmp_parcellation


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
OUT_CSV = DG_DIR / "glasser_roi_mask.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-glasser-roi-mask.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-glasser-roi-mask.md"

N_VERTICES_HEMI_FS5 = 10242

# Glasser parcels grouped by functional system.
# Names match the HCP-MMP1.0 parc; both hemispheres are picked up automatically
# because MNE writes labels as L_<name>_ROI and R_<name>_ROI per hemi.
GLASSER_GROUPS: dict[str, list[str]] = {
    "early_visual_v1": [
        "V1",
    ],
    "higher_visual_v2v3v4": [
        "V2",
        "V3",
        "V4",
    ],
    "face_ffc": [
        "FFC",
        "V8",
        "PIT",
        "VVC",
    ],
    "scene_ppa": [
        "PHA1",
        "PHA2",
        "PHA3",
    ],
    "retrosplenial_pos": [
        "RSC",
        "POS1",
        "POS2",
        "ProS",
        "PreS",
    ],
    "lateral_object_loc": [
        "LO1",
        "LO2",
        "LO3",
    ],
    "motion_mt_complex": [
        "MT",
        "MST",
        "FST",
        "V4t",
        "V3CD",
    ],
    "body_eba_region": [
        "PH",
        "LO2",
        "LO3",
        "FST",
    ],
    "language_control": [
        "44",
        "45",
        "IFJa",
        "IFJp",
        "TPOJ1",
        "STSdp",
        "STSva",
        "STSvp",
    ],
    "auditory_control": [
        "A1",
        "A4",
        "A5",
        "MBelt",
        "LBelt",
        "PBelt",
        "RI",
    ],
}


def parcel_basename(label_name: str) -> str:
    """Strip the L_/R_ hemisphere prefix and the _ROI suffix from a Glasser label.

    MNE writes labels as e.g. ``L_V1_ROI``. We want ``V1``.
    """
    name = re.sub(r"_ROI$", "", label_name)
    if name.startswith(("L_", "R_")):
        name = name[2:]
    return name


def read_hemi_annot(annot_path: Path) -> tuple[np.ndarray, list[str]]:
    labels, ctab, names = nib.freesurfer.read_annot(str(annot_path))
    decoded = [n.decode() if isinstance(n, bytes) else str(n) for n in names]
    return labels, decoded


def main() -> None:
    subjects_dir = Path(fetch_fsaverage(verbose="ERROR")).parent
    os.environ["SUBJECTS_DIR"] = str(subjects_dir)

    fetch_hcp_mmp_parcellation(
        subjects_dir=str(subjects_dir),
        accept=True,
        verbose="ERROR",
    )

    label_dir = subjects_dir / "fsaverage" / "label"
    lh_annot = label_dir / "lh.HCPMMP1.annot"
    rh_annot = label_dir / "rh.HCPMMP1.annot"
    if not lh_annot.exists() or not rh_annot.exists():
        raise FileNotFoundError(
            f"Glasser .annot files not found. Looked at:\n  {lh_annot}\n  {rh_annot}"
        )

    lh_labels, lh_names = read_hemi_annot(lh_annot)
    rh_labels, rh_names = read_hemi_annot(rh_annot)

    if len(lh_labels) < N_VERTICES_HEMI_FS5 or len(rh_labels) < N_VERTICES_HEMI_FS5:
        raise RuntimeError(
            "fsaverage annot has fewer vertices than fsaverage5 expects."
        )

    # FreeSurfer fsaverage is icosahedron level 7 (163842 verts/hemi);
    # fsaverage5 is level 5 (10242 verts/hemi). They are nested: the first
    # N_VERTICES_HEMI_FS5 vertex indices in fsaverage are the fsaverage5
    # vertices. Slice and we are done.
    lh_fs5 = lh_labels[:N_VERTICES_HEMI_FS5]
    rh_fs5 = rh_labels[:N_VERTICES_HEMI_FS5]

    lh_basename = [parcel_basename(n) for n in lh_names]
    rh_basename = [parcel_basename(n) for n in rh_names]

    rows: list[dict] = []
    summary_rows: list[dict] = []

    for roi_name, parcel_basenames in GLASSER_GROUPS.items():
        wanted = set(parcel_basenames)
        lh_indices = {i for i, name in enumerate(lh_basename) if name in wanted}
        rh_indices = {i for i, name in enumerate(rh_basename) if name in wanted}

        for hemi, fs5_labels, indices, names in [
            ("L", lh_fs5, lh_indices, lh_basename),
            ("R", rh_fs5, rh_indices, rh_basename),
        ]:
            offset = 0 if hemi == "L" else N_VERTICES_HEMI_FS5
            mask = np.isin(fs5_labels, list(indices))
            local_verts = np.where(mask)[0]
            for v in local_verts:
                parcel_id = int(fs5_labels[v])
                rows.append(
                    {
                        "roi": roi_name,
                        "vertex": offset + int(v),
                        "hemi": hemi,
                        "label_index": parcel_id,
                        "label_name": names[parcel_id],
                        "atlas": "hcpmmp1_glasser_fsaverage5",
                    }
                )

        n = sum(1 for r in rows if r["roi"] == roi_name)
        summary_rows.append(
            {
                "roi": roi_name,
                "n_vertices": n,
                "parcels": ", ".join(parcel_basenames),
            }
        )

    df = pd.DataFrame(rows).sort_values(["roi", "vertex"])

    # The downstream `scenetwin_roi_gap_curve.py` infers n_vertices from
    # max(vertex)+1, which fails if the highest fsaverage5 vertex is not in any
    # Glasser-grouped ROI. Pad with a single row covering vertex 20483 in a
    # `_unassigned_padding` group so masks line up with the 20484-vertex TRIBE
    # tensors. The padding ROI is filtered out by the content-profile lookup.
    n_total = 2 * N_VERTICES_HEMI_FS5
    if df["vertex"].max() < n_total - 1:
        df = pd.concat(
            [
                df,
                pd.DataFrame([
                    {
                        "roi": "_unassigned_padding",
                        "vertex": n_total - 1,
                        "hemi": "R",
                        "label_index": -1,
                        "label_name": "_padding",
                        "atlas": "hcpmmp1_glasser_fsaverage5",
                    }
                ]),
            ],
            ignore_index=True,
        ).sort_values(["roi", "vertex"])

    summary = pd.DataFrame(summary_rows)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    report = f"""---
title: "SceneTwin Glasser HCP-MMP1.0 fsaverage5 ROI Mask"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5, Glasser, HCP-MMP1, functional-atlas]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/glasser_roi_mask.csv
  - https://www.humanconnectome.org/storage/app/media/articles/HCP_MMP1.0.pdf
  - https://mne.tools/stable/generated/mne.datasets.fetch_hcp_mmp_parcellation.html
---

# SceneTwin Glasser HCP-MMP1.0 fsaverage5 ROI Mask

## Status

Functional parcellation. This replaces the Destrieux anatomical proxy mask.
Parcels are defined by multimodal cortical features (cytoarchitecture, function,
connectivity, topography) — Glasser et al. 2016 Nature.

## Pipeline

1. MNE `fetch_fsaverage` + `fetch_hcp_mmp_parcellation` download fsaverage and
   the HCP-MMP1.0 .annot files.
2. Per-vertex parcel ids read with `nibabel.freesurfer.read_annot`.
3. fsaverage5 vertices are the first 10242 vertices per hemisphere (fsaverage
   subjects are nested across icosahedron subdivision levels).
4. Groups below combine functional parcels into the SceneTwin content-type ROIs.

## Functional Groups

{summary.to_markdown(index=False)}

## Use

```bash
python3 tools/scenetwin_roi_gap_curve.py \\
    --mask output/scenetwin_description_gain/glasser_roi_mask.csv
```

## Why This Matters

Destrieux `scene_context_ppa_proxy` was the entire parahippocampal gyrus plus
adjacent sulci — about 1035 vertices. Glasser `scene_ppa` is PHA1+PHA2+PHA3,
which is a much tighter functional definition. Same logic for face (FFC vs
fusiform gyrus) and motion (MT+MST+FST vs middle temporal gyrus). If the
phase-2 typing-validation agreement rises with this atlas, the typing layer
is sound and was just being averaged over too much non-selective cortex.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"\nWrote {len(df)} rows -> {OUT_CSV}")
    print(f"Report                -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
