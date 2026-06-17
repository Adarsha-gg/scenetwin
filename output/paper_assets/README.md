# SceneTwin Paper Assets

Paper-grade graph assets are generated deterministically from project outputs
with:

```bash
MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/scenetwin_mpl XDG_CACHE_HOME=/private/tmp/scenetwin_cache \
  .venv/bin/python3 output/paper_assets/build_combined_paper_figures.py
```

Canonical graph assets used in the combined paper:

- `fig_scoring_leaderboard.png`
  - Use: scoring leaderboard against metric and VLM baselines.

- `fig_blind_spot_router_inventory.png`
  - Use: TRIBE blind-spot router inventory and temporal structure.

- `fig_matched_target_validation.png`
  - Use: matched-target ADQA gains.

- `fig_negative_control_pro_ad_priority.png`
  - Use: negative control showing TRIBE is not a global pro-AD topic model.

Generated concept images are present only as discarded exploration assets. They
are not referenced by the paper draft.
