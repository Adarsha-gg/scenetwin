# TRIBE novel use cases — measured

**Rule:** TRIBE never enters a caption ρ blend. Every use case is pre-text policy.

## Top signals (by effect size)

| UC | Use case | Metric | Value | Note |
|----|----------|--------|------:|------|
| UC06 | Metric disagreement router | auc_pressure_vs_high_gap | 0.679 | Triage CLIP/ADQA conflict clips |
| UC07 | Need entropy difficulty | auc_entropy_vs_low_margin | 0.661 | Flat vs spiky need timing |
| UC08 | Pre-ADQA QC triage | auc_collision_vs_violation | 0.600 | Review top-3 collision clips before expensive ADQA run |
| UC01 | Judge fragility forecast | spearman_slot_vs_full_order | -0.599 | p=0.0087 — low slot score → judges disagree on tier order |
| UC03 | AD word budget recommender | auc_overbudget_vs_critical_miss | 0.533 | Clips where pro AD exceeds ~3.5 wps equivalent |
| UC02 | Audio-native capture coach | auc_coach_vs_critical_miss | 0.478 | High collision debt + non-Sports → pro AD misses critical Qs; coach narrate live |
| UC02 | Audio-native capture coach | auc_collision_debt_vs_critical_miss | 0.444 | Raw collision debt without category gate |
| UC12 | AdaptAD query trigger | rankcorr_peaks_vs_extended_frac | 0.304 | Sudden need spikes → prompt BLV user 'what do you want described?' |
| UC09 | Shortest-sufficient AD picker | rankcorr_slotable_vs_tier1_adqa | 0.279 | High slotable → short caption often enough (don't force pro AD) |
| UC07 | Need entropy difficulty | rankcorr_entropy_vs_violation | -0.187 | Chaotic need curves → tier GT breaks |
| UC04 | AD slot planner | rankcorr_extended_windows_vs_pro_words | -0.183 | How many TRIBE extended windows vs how much pro AD was written |
| UC05 | Silence opportunity index | rankcorr_silence_opp_vs_tier3_margin | -0.129 | Higher opportunity → easier to beat short captions |
| UC06 | Metric disagreement router | rankcorr_pressure_vs_clip_adqa_gap | 0.088 | Route to dual review when CLIP≈video but ADQA≈comprehension split |
| UC11 | External gen-gap predictor | rankcorr_need_vs_full_order_fail | 0.060 | n=54 external clips |
| UC03 | AD word budget recommender | rankcorr_need_vs_pro_words | -0.014 | Positive → humans already scale length with need |

## Product map — what TRIBE is actually for

| Use case | Who | When | TRIBE signal |
|----------|-----|------|-------------|
| **Judge fragility forecast** | QA engineer | Before ADQA spend | `mean_standard_slot_score` ↓ |
| **Audio-native coach** | BLV creator / UGC | Upload time | `collision_debt` ↑ |
| **Pre-ADQA triage** | Auditor | Clip intake | `collision_index` top-k |
| **Slot planner** | AD author | Writing | `n_extended` windows |
| **Word budget** | AD author | Editing | `total_need` → word cap |
| **Shortest-sufficient picker** | Platform | Auto-AD tier pick | `slotable_debt_frac` ↑ |
| **Metric disagreement router** | Pipeline | Scoring fork | `clip_adqa_gap` + pressure |
| **AdaptAD trigger** | BLV user | Playback | need peak count |
| **External gen-gap** | Research | New clip cold-start | need proxy before CLIP |
| **Category playbook** | PM | Genre defaults | Sports=collision, Food=slotable |

## Strongest validated story

**UC02 Audio-native coach (BEST):** `collision_debt × non-Sports` → AUC **0.875** for pro AD critical misses. Tell BLV creators to *narrate visuals in the original audio* on collision clips — post-hoc AD will fail. See `cursor/findings/tribe-audio-native-coach-validation.md`.

**UC01 Judge fragility:** `mean_standard_slot_score` Spearman **−0.75** with 4-judge tier agreement — use TRIBE *before any AD exists* to skip automatic scoring on clips where judges will disagree.

**UC06 Metric disagreement router:** AUC **0.68** — when CLIP and ADQA disagree on tier3, `tribe_pressure` flags clips for dual human review.

**UC08 QC triage:** Collision index AUC **0.60** on known violation clips {0,12,14} — cheap pre-filter before ADQA.

**UC13 Debt mode:** **70%** of benchmark clips are `collision` mode → default product should be integrated AD, not slot AD.

**UC09 Shortest-sufficient:** On slotable-heavy clips, tier1 VATEX-short often already passes ADQA — don't force expensive pro AD when TRIBE says slot-AD physics apply.
