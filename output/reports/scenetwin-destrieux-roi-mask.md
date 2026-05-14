---
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

| roi                           |   n_vertices | labels                                                                                                                                                                        |
|:------------------------------|-------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| auditory_control              |         1620 | G_temp_sup-G_T_transv, G_temp_sup-Lateral, G_temp_sup-Plan_polar, G_temp_sup-Plan_tempo, S_temporal_sup, S_temporal_transverse                                                |
| body_eba_proxy                |          597 | G_oc-temp_lat-fusifor, G_occipital_middle, S_oc-temp_lat                                                                                                                      |
| early_visual_v1_proxy         |          375 | S_calcarine                                                                                                                                                                   |
| language_control              |         2296 | G_front_inf-Opercular, G_front_inf-Triangul, G_pariet_inf-Angular, G_pariet_inf-Supramar, G_temp_sup-Lateral, G_temporal_middle, S_front_inf                                  |
| lateral_object_loc_proxy      |          870 | G_and_S_occipital_inf, G_oc-temp_lat-fusifor, G_occipital_middle, S_oc-temp_lat, S_oc_middle_and_Lunatus                                                                      |
| motion_mt_proxy               |         1041 | G_temporal_inf, G_temporal_middle, S_oc-temp_lat, S_occipital_ant, S_temporal_inf                                                                                             |
| occipital_visual_proxy        |         1738 | G_and_S_occipital_inf, G_cuneus, G_occipital_middle, G_occipital_sup, Pole_occipital, S_oc_middle_and_Lunatus, S_oc_sup_and_transversal, S_occipital_ant, S_parieto_occipital |
| retrosplenial_precuneus_proxy |         1129 | G_cingul-Post-dorsal, G_cingul-Post-ventral, G_precuneus, S_parieto_occipital, S_subparietal                                                                                  |
| scene_context_ppa_proxy       |         1035 | G_oc-temp_med-Lingual, G_oc-temp_med-Parahip, S_collat_transv_ant, S_collat_transv_post, S_oc-temp_med_and_Lingual                                                            |
| ventral_visual_ffa_proxy      |          223 | G_oc-temp_lat-fusifor                                                                                                                                                         |

## Use

```bash
python tools/scenetwin_roi_gap_curve.py --mask output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
```

## Caveat

Labels such as `ventral_visual_ffa_proxy`, `scene_context_ppa_proxy`, `motion_mt_proxy`, and `body_eba_proxy` are coarse anatomical approximations. If these results look promising, replace this mask with a functional atlas/localizer mask before making strong neuroscience claims.
