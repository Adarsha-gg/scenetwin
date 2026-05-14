# SceneTwin closure metric sweep

Comparing 5 closure metrics on the 2 clips that finished the visual-closure Colab (clip_01, clip_03). Goal: find a magnitude-invariant metric where tier3 (pro AD) ranks above tier0 (cross-category AD).

## Monotonicity summary

| scope        | metric            |   n_clips |   fully_monotonic |   tier3_ranked_top |   tier3_beats_tier0 |
|:-------------|:------------------|----------:|------------------:|-------------------:|--------------------:|
| whole_cortex | L2_closure (orig) |         2 |                 0 |                  1 |                   1 |
| whole_cortex | cosine_closure    |         2 |                 0 |                  1 |                   1 |
| whole_cortex | topk10_gap_L2     |         2 |                 0 |                  1 |                   1 |
| visual_roi   | L2_closure (orig) |         2 |                 0 |                  0 |                   1 |
| visual_roi   | cosine_closure    |         2 |                 0 |                  0 |                   1 |
| visual_roi   | topk10_gap_L2     |         2 |                 0 |                  0 |                   1 |
| visual_roi   | per_voxel_corr    |         2 |                 0 |                  0 |                   0 |
| visual_roi   | voxel_direction   |         2 |                 0 |                  0 |                   0 |
| whole_cortex | per_voxel_corr    |         2 |                 0 |                  0 |                   0 |
| whole_cortex | voxel_direction   |         2 |                 0 |                  0 |                   0 |

## Raw per-tier values

|                                                  |   tier0_cross |   tier1_vatex_short |   tier2_vatex_long |   tier3_va11y |
|:-------------------------------------------------|--------------:|--------------------:|-------------------:|--------------:|
| ('visual_roi', 'L2_closure (orig)', 'clip_01')   |      -12.696  |             -7.8476 |            -8.8373 |       -8.8809 |
| ('visual_roi', 'L2_closure (orig)', 'clip_03')   |      -12.4941 |            -12.3836 |           -10.8901 |      -13.183  |
| ('visual_roi', 'cosine_closure', 'clip_01')      |       -0.3587 |             -0.2107 |            -0.2769 |       -0.2641 |
| ('visual_roi', 'cosine_closure', 'clip_03')      |       -0.2039 |             -0.1862 |            -0.1525 |       -0.2408 |
| ('visual_roi', 'per_voxel_corr', 'clip_01')      |       -0.5837 |             -0.5418 |            -0.6983 |       -0.6349 |
| ('visual_roi', 'per_voxel_corr', 'clip_03')      |       -0.5447 |             -0.398  |            -0.4039 |       -0.6382 |
| ('visual_roi', 'topk10_gap_L2', 'clip_01')       |       -5.3265 |             -2.9365 |            -3.3652 |       -3.2956 |
| ('visual_roi', 'topk10_gap_L2', 'clip_03')       |       -2.4009 |             -3.4555 |            -2.3618 |       -2.5828 |
| ('visual_roi', 'voxel_direction', 'clip_01')     |       -0.5    |             -0.5    |            -0.5    |       -0.5    |
| ('visual_roi', 'voxel_direction', 'clip_03')     |       -0.5    |             -0.5    |            -0.5    |       -0.5    |
| ('whole_cortex', 'L2_closure (orig)', 'clip_01') |      -63.1752 |            -62.2211 |           -70.4774 |      -64.4235 |
| ('whole_cortex', 'L2_closure (orig)', 'clip_03') |      -76.8307 |            -84.7717 |           -77.8742 |      -75.9212 |
| ('whole_cortex', 'cosine_closure', 'clip_01')    |       -0.2856 |             -0.2946 |            -0.3544 |       -0.3336 |
| ('whole_cortex', 'cosine_closure', 'clip_03')    |       -0.2681 |             -0.3396 |            -0.2632 |       -0.2603 |
| ('whole_cortex', 'per_voxel_corr', 'clip_01')    |       -0.6973 |             -0.4106 |            -0.4779 |       -0.8102 |
| ('whole_cortex', 'per_voxel_corr', 'clip_03')    |       -0.474  |             -0.3844 |            -0.2957 |       -0.5463 |
| ('whole_cortex', 'topk10_gap_L2', 'clip_01')     |      -19.5532 |            -18.0523 |           -20.3458 |      -20.0453 |
| ('whole_cortex', 'topk10_gap_L2', 'clip_03')     |      -24.5346 |            -27.2188 |           -25.4043 |      -23.8675 |
| ('whole_cortex', 'voxel_direction', 'clip_01')   |       -0.5    |             -0.5    |            -0.5    |       -0.5    |
| ('whole_cortex', 'voxel_direction', 'clip_03')   |       -0.5    |             -0.5    |            -0.5    |       -0.5    |
