"""
Two sanity checks on the CLIP + ADQA ensemble result:
  1. Per-clip Spearman between CLIP and ADQA — are they actually complementary?
  2. Bootstrap 95% CI on ensemble ρ=0.929 (N=18 clips, 1000 resamples)
"""

import numpy as np
import pandas as pd
from scipy import stats

SCORES = "/Users/adarsha/Knowledge/output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv"
OUT    = "/Users/adarsha/Knowledge/output/reports/scenetwin_ensemble_validation.md"

df = pd.read_csv(SCORES)

# use the best single metrics from the working stack
CLIP_COL  = "clip_top3_norm_clip"   # ρ=0.799 single best CLIP
ADQA_COL  = "adqa_norm_clip"        # normalised ADQA
ENS_COL   = "ensemble_mean_clip_top3"  # 50/50 mean ensemble

# ── restrict to clips with complete data ──────────────────────────────────
clips_ok = (
    df.groupby("clip_idx")
      .filter(lambda g: g[CLIP_COL].notna().all() and g[ADQA_COL].notna().all())
      ["clip_idx"].unique()
)
df = df[df.clip_idx.isin(clips_ok)].copy()
print(f"Clips with complete data: {len(clips_ok)}  |  rows: {len(df)}")

# ── 1. per-clip rank correlation between CLIP and ADQA ───────────────────
per_clip = []
for cid, grp in df.groupby("clip_idx"):
    grp = grp.sort_values("gt")
    if len(grp) < 3:
        continue
    r_clip_adqa, _ = stats.spearmanr(grp[CLIP_COL], grp[ADQA_COL])
    r_clip_gt,   _ = stats.spearmanr(grp[CLIP_COL], grp["gt"])
    r_adqa_gt,   _ = stats.spearmanr(grp[ADQA_COL], grp["gt"])
    r_ens_gt,    _ = stats.spearmanr(grp[ENS_COL],  grp["gt"])
    # agreement = both rank in the same direction as gt
    clip_dir  = np.sign(r_clip_gt)
    adqa_dir  = np.sign(r_adqa_gt)
    agree = (clip_dir == adqa_dir)
    per_clip.append({
        "clip_idx":       cid,
        "clip_adqa_rho":  round(r_clip_adqa, 3),
        "clip_gt_rho":    round(r_clip_gt,   3),
        "adqa_gt_rho":    round(r_adqa_gt,   3),
        "ens_gt_rho":     round(r_ens_gt,    3),
        "clip_adqa_agree": agree,
    })

pc = pd.DataFrame(per_clip)
mean_clip_adqa = pc["clip_adqa_rho"].mean()
pct_agree      = pc["clip_adqa_agree"].mean() * 100
disagree_clips = pc[~pc["clip_adqa_agree"]]

print(f"\nMean per-clip CLIP↔ADQA ρ: {mean_clip_adqa:.3f}")
print(f"Clips where CLIP & ADQA agree on direction: {pct_agree:.0f}%")
print(f"\nDisagreement clips ({len(disagree_clips)}):")
print(disagree_clips[["clip_idx","clip_gt_rho","adqa_gt_rho","ens_gt_rho"]].to_string(index=False))

# ── 2. bootstrap CI on ensemble ρ ────────────────────────────────────────
rng = np.random.default_rng(42)
N_BOOT = 2000
clip_ids = pc["clip_idx"].values

boot_rhos = []
for _ in range(N_BOOT):
    sampled = rng.choice(clip_ids, size=len(clip_ids), replace=True)
    subset  = df[df.clip_idx.isin(sampled)]
    r, _    = stats.spearmanr(subset[ENS_COL], subset["gt"])
    boot_rhos.append(r)

boot_rhos = np.array(boot_rhos)
ci_lo, ci_hi = np.percentile(boot_rhos, [2.5, 97.5])
ens_obs, _   = stats.spearmanr(df[ENS_COL], df["gt"])

print(f"\nEnsemble ρ (observed):   {ens_obs:.4f}")
print(f"Bootstrap 95% CI:        [{ci_lo:.3f}, {ci_hi:.3f}]")
print(f"Bootstrap mean ρ:        {boot_rhos.mean():.4f}")
print(f"Bootstrap std:           {boot_rhos.std():.4f}")

# also bootstrap CLIP alone for comparison
boot_clip = []
for _ in range(N_BOOT):
    sampled = rng.choice(clip_ids, size=len(clip_ids), replace=True)
    subset  = df[df.clip_ids.isin(sampled)] if False else df[df.clip_idx.isin(sampled)]
    r, _    = stats.spearmanr(subset[CLIP_COL], subset["gt"])
    boot_clip.append(r)
boot_clip = np.array(boot_clip)
clip_obs, _ = stats.spearmanr(df[CLIP_COL], df["gt"])
clip_lo, clip_hi = np.percentile(boot_clip, [2.5, 97.5])

print(f"\nCLIP-only ρ (observed):  {clip_obs:.4f}")
print(f"Bootstrap 95% CI:        [{clip_lo:.3f}, {clip_hi:.3f}]")

# ── write report ──────────────────────────────────────────────────────────
lines = [
    "# SceneTwin Ensemble Validation\n",
    "## 1. CLIP ↔ ADQA Per-Clip Complementarity\n",
    f"- Mean per-clip Spearman between CLIP and ADQA scores: **{mean_clip_adqa:.3f}**",
    f"- Clips where CLIP and ADQA agree on ranking direction: **{pct_agree:.0f}%**\n",
]

if mean_clip_adqa > 0.85:
    lines.append(
        "> **Caution**: CLIP and ADQA are highly correlated per clip "
        f"(ρ={mean_clip_adqa:.3f}). The ensemble improvement is likely "
        "smoothing noise, not exploiting independent signals.\n"
    )
elif mean_clip_adqa > 0.6:
    lines.append(
        "> **Moderate correlation**: CLIP and ADQA share signal but are not "
        f"identical (ρ={mean_clip_adqa:.3f}). Ensemble gains are plausible "
        "but not guaranteed to generalise.\n"
    )
else:
    lines.append(
        "> **Genuine complementarity**: CLIP and ADQA are weakly correlated "
        f"(ρ={mean_clip_adqa:.3f}). The ensemble is combining independent signals.\n"
    )

lines += [
    "### Per-Clip Detail\n",
    pc[["clip_idx","clip_adqa_rho","clip_gt_rho","adqa_gt_rho","ens_gt_rho","clip_adqa_agree"]]
      .to_markdown(index=False),
    "\n",
    "## 2. Bootstrap 95% CI on Ensemble ρ\n",
    f"| Metric | Observed ρ | 95% CI |",
    "|---|---|---|",
    f"| Ensemble (CLIP + ADQA, 50/50) | **{ens_obs:.4f}** | [{ci_lo:.3f}, {ci_hi:.3f}] |",
    f"| CLIP-only | {clip_obs:.4f} | [{clip_lo:.3f}, {clip_hi:.3f}] |",
    "\n",
    f"N clips: {len(clip_ids)} | N bootstrap resamples: {N_BOOT}\n",
]

if ci_lo > clip_hi:
    lines.append(
        "> CIs do not overlap. Ensemble improvement is robust at this sample size.\n"
    )
else:
    lines.append(
        "> CIs overlap. The ensemble improvement is real in expectation but "
        "the confidence intervals do not rule out CLIP-only performing similarly "
        "on a different sample of clips. Report both numbers on the poster.\n"
    )

with open(OUT, "w") as f:
    f.write("\n".join(lines))

print(f"\nReport → {OUT}")
