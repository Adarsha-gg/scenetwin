# TRIBE use-case lab

Novel applications beyond ρ=0.929 ensemble headline.

### UC1_extended_vs_tier3_adqa

- rho=0.018 p=0.9450 (n=18)
- negative rho → extended need clips are harder for pro AD (expected)

### UC2_category_gap_profile

- ['Sports', 'Pets & Animals', 'Food & Cooking']  (n=4)
- highest pressure categories: ['Sports', 'Pets & Animals', 'Food & Cooking']

### UC3_risk_separates_known_failures

- fail_mean=0.140, ok_mean=0.058 p=0.2686 (n=18)
- risk score should rank clip_00/12 above median

### UC4_speech_density_vs_tier3_ensemble

- rho=0.140, margin_heavy-lean=-0.001  (n=18)
- speech-heavy clips may need integrated AD not standard slots

### UC5_need_windows_vs_generated_slots

- rho=0.989 p=0.0000 (n=12)
- ADX3 slot generator should track TRIBE extended windows

### UC7_pressure_vs_pro_ad_length

- rho=-0.090 p=0.7228 (n=18)
- if positive: high-need clips already have longer pro AD (human alignment)

