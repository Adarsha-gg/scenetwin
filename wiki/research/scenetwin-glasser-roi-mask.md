---
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

| roi                  |   n_vertices | parcels                                        |
|:---------------------|-------------:|:-----------------------------------------------|
| early_visual_v1      |          523 | V1                                             |
| higher_visual_v2v3v4 |          805 | V2, V3, V4                                     |
| face_ffc             |          264 | FFC, V8, PIT, VVC                              |
| scene_ppa            |          194 | PHA1, PHA2, PHA3                               |
| retrosplenial_pos    |          594 | RSC, POS1, POS2, ProS, PreS                    |
| lateral_object_loc   |          111 | LO1, LO2, LO3                                  |
| motion_mt_complex    |          212 | MT, MST, FST, V4t, V3CD                        |
| body_eba_region      |          242 | PH, LO2, LO3, FST                              |
| language_control     |          785 | 44, 45, IFJa, IFJp, TPOJ1, STSdp, STSva, STSvp |
| auditory_control     |          590 | A1, A4, A5, MBelt, LBelt, PBelt, RI            |

## Use

```bash
python3 tools/scenetwin_roi_gap_curve.py \
    --mask output/scenetwin_description_gain/glasser_roi_mask.csv
```

## Why This Matters

Destrieux `scene_context_ppa_proxy` was the entire parahippocampal gyrus plus
adjacent sulci — about 1035 vertices. Glasser `scene_ppa` is PHA1+PHA2+PHA3,
which is a much tighter functional definition. Same logic for face (FFC vs
fusiform gyrus) and motion (MT+MST+FST vs middle temporal gyrus). If the
phase-2 typing-validation agreement rises with this atlas, the typing layer
is sound and was just being averaged over too much non-selective cortex.
