# Agent loop (Claude + Codex breakthrough hunt)

Supervisor v2: **skill-based tasks**, learns from worker output, **anti-repeat** on scripts/angles.

## Start

```bash
.venv/bin/python cursor/agent_loop/supervisor.py --poll 4m --agents claude,codex
```

## Skills (read first — saves tokens)

| Skill | When |
|---|---|
| `.cursor/skills/scenetwin-agent-worker/` | Every spawn |
| `.cursor/skills/scenetwin-done-cache/` | Before any experiment |
| `.cursor/skills/scenetwin-gate-eval/` | Gate / ROC / self-consistency |
| `.cursor/skills/scenetwin-clip-local/` | CLIP-only, zero API |
| `.cursor/skills/scenetwin-human-lies/` | Hand-authored fabrications |

## Supervisor learns

- Parses `COMMANDS_RUN:`, `MISTAKE_AVOIDED:`, `NEW_APPROACH:`, `PR:` from worker output
- **`peer_learnings.md`** — shared mistake table; supervisor appends after each round
- Round ≥2: must read peer's `latest.md` and use a **different** approach
- **Web search allowed**; **PR via `gh pr create`** on branch `agent-loop/{agent}-*`
- Skill: `.cursor/skills/scenetwin-peer-pr/SKILL.md`

## Worker output

Must end with `COMMANDS_RUN: ...` plus optional `BREAKTHROUGH:` / `CREDIT_EXHAUSTED`.

## Files

- `state.json` — PIDs, learnings, breakthroughs
- `log.md` — append-only
- `results/{agent}/latest.md`
