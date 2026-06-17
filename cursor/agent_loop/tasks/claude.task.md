# round 117 — claude — wrong_content_gate

Read `.cursor/skills/scenetwin-agent-worker/SKILL.md` + `.cursor/skills/scenetwin-peer-pr/SKILL.md` + `.cursor/skills/scenetwin-gate-eval/SKILL.md`.

**Round 117 | angle `wrong_content_gate` | agent claude**
Run gate_outcome.py (free). Report catch/ship-best rates vs random 25%. Outcome or null.

**Peer mandate (round ≥2):** Read `cursor/agent_loop/peer_learnings.md` and `cursor/agent_loop/results/codex/latest.md`.
Peer's last NEW_APPROACH: two-scorer CLIP consensus floor across existing local CLIP score columns, requiring agreement between independent CLIP scoring recipes for the same AD instead of calibrating an absolute tau or ranking
You MUST use a **different** strategy. Web search allowed. Open a PR if you have shippable code (`scenetwin-peer-pr` skill).

**Do NOT re-run:** gate_shipbest_selective.py, inspect external_ensemble_eval.csv + gate_outcome.json (python), replicate ship-best argmax, CLIP/ADQA agreement structure, ADQA-margin risk-coverage, tie/non-tie error breakdown, .venv/bin/python cursor/pipeline/gate_shipbest_selective.py, .venv/bin/python output/charts/scenetwin_gate_shipbest_selective.py
**Banned:** venv39_probe, pipeline_recon

Write: `cursor/agent_loop/results/claude/round_117.md` + `latest.md`
End with: `COMMANDS_RUN:` `MISTAKE_AVOIDED:` `NEW_APPROACH:` (+ `BREAKTHROUGH:` / `PR:` / `CREDIT_EXHAUSTED` if applicable)

**Peer (codex) excerpt:**
```
# Round 003 — codex

**Angle:** `self_consistency_expand`

## Cache Expansion

Expanded the best-of-N cache without `--refresh-cache`, using the existing first-17 cached clips as cache hits and targeting only missing clips inside the `--limit 20` prefix.

Before expansion:

| artifact | count |
|---|---:|
| cache files | 85 |
| complete best-of-N clips | 17 |

After `.venv/bin/python cursor/pipeline/best_of_n_rerank.py --limit 20 --n 4`:

| artifact | count |
|---|---:|
| cache files | 95 |
| complete best-of-N clips | 19 |

`BHxn3qfPAl4_000018_000028` was a legitimate uncached target but retu...
```

Your prev: # Round 072 — claude **Angle:** `wrong_content_gate` BREAKTHROUGH: the **ship-best** gate decision has a free, near-perfect confidence signal — **ADQA's own decision margin**. Abstaining the lowest-margin 20% of clips to human review makes ship-best **100%** reliable, and **6 of the 7** ship-best errors are *exact ADQA ties* (margin = 0). Cross-signal agreement (CLIP↔ADQA) is the WRONG confidence signal here and FAILS. ## gate_outcome.py (free, as mandated) | scorer | catch | ship-best | false-reject | n | vs random 25%
