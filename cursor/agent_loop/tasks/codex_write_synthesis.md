# Codex write task — consolidate agent-loop gate findings into paper subsection

Read `.cursor/skills/scenetwin-agent-worker/SKILL.md` (venv rules only). **Do not** re-run experiments.

## Your job

Rewrite **`output/reports/paper-ad-safety-gate.md`** as the definitive paper subsection incorporating ALL agent-loop results (Claude rounds 1–72, Codex rounds 1–3). This replaces the June 8 draft.

## Headline ordering (mandatory — reviewer defense)

1. **Lead:** CLIP-only grounding-drop hallucination gate — **AUC 0.84**, 70% recall @ 10% FPR (n=60, grader-free decision)
2. **Wrong-content safety gate** — 100% catch tier0_cross vs expert/pro (ensemble); global raw-CLIP LOCO 98%/2%; deployment base-rate / PPV analysis
3. **Self-consistency / reference-substitution** — model anchor catches human lies AUC 0.81–0.90 without human reference
4. **Dual-signal non-redundancy** — ADQA vs CLIP load-bearing for different deployment properties (ship-best vs confounder separation)
5. **Honest negatives:** zero-ref claim gate AUC 0.58; CLIP object-bias on relational/action lies; fusion 0.90 footnoted as grader-dependent

## Source files (read these, cite numbers from JSON/MD)

- `cursor/output/gate_review_holes.json`, `gate_summary.json`, `gate_outcome.json`
- `cursor/findings/hallucination-gate.md`, `reference-substitution-gate.md`, `wrong-content-global-gate.md`, `2026-06-09-wrong-content-gate-base-rate.md`, `human-lies-relational-stratum.md` (if exists)
- `cursor/agent_loop/results/claude/round_068.md` through `round_072.md`
- `cursor/agent_loop/results/codex/round_001.md` through `round_003.md`
- `cursor/agent_loop/log.md` (breakthrough lines only)
- Existing pipelines: `gate_shipbest_selective.py`, `wrong_content_confounder.py`, `gate_margin_robustness.py`, `gate_deployment_precision.py`

## Structure

- X.1 Motivation (deployment outcome, not ρ)
- X.2 Hallucination grounding-drop gate (headline 0.84)
- X.3 Wrong-content catastrophic-failure gate
- X.4 Reference-free variants (self-consistency, anchor substitution)
- X.5 Dual-signal complementarity + selective prediction on ship-best
- X.6 Honest limitations (object bias, base-rate/PPV, zero-ref failure)
- X.7 Artifacts table

## Output

1. Write the full updated `output/reports/paper-ad-safety-gate.md`
2. Write `cursor/findings/agent-loop-gate-synthesis.md` (500-word executive summary for wiki)
3. Append one line to `cursor/agent_loop/log.md`: loop stopped; codex wrote synthesis
4. End with `COMMANDS_RUN:` listing files written

No demo. No re-running pipelines. Web search optional for framing only.

If you have shippable edits, commit on branch `agent-loop/claude-round-70` with message `agent-loop(codex): consolidated AD safety gate paper subsection`
