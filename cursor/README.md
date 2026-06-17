# SceneTwin — Cursor experiment workspace

Self-contained scripts and artifacts for exploring TRIBE, ADQA, and ensemble
signals without touching `raw/` or the poster pipeline.

## Quick start

```bash
source .venv/bin/activate
python3 cursor/loop_worker.py              # ONE iteration of real work (8+ tasks)
./cursor/run_loop.sh                        # repeat every 120s
./cursor/loop_guard.sh                        # watchdog restarts loop if dead

# Watch it work:
tail -f cursor/loop-heartbeat.txt
tail -f cursor/findings/auto-discoveries.md
ls -lt cursor/output/loop_runs/

python3 cursor/run_experiments.py            # full static suite (manual)
touch cursor/STOP                             # halt loop + guard
```

Each loop tick runs **`loop_worker.py`**, which increments an iteration and executes rotating tasks: bootstrap ρ, clip deep-dive (0–17), weight sweep, TRIBE ablation, permutation null, upstream tool, JSON export, insights HTML. Writes `loop-status.json`, `loop-heartbeat.txt`, and appends `findings/auto-discoveries.md`.

## What lives here

| Script | Purpose |
|--------|---------|
| **`loop_worker.py`** | **Loop brain — rotating experiments each tick** |
| `run_loop.sh` | Shell loop calling loop_worker every 120s |
| `loop_guard.sh` | Restarts run_loop if dead |
| `run_experiments.py` | Full static suite (manual) |
| `export_static_api.py` | `/api/tribe-risk` + `/api/cached-clips` as static JSON |
| `category_risk_analysis.py` | TRIBE pressure vs ADQA margin by video category |
| `combined_review_priority.py` | Composite human-review score (TRIBE × fragility) |
| `ensemble_validation.py` | Bootstrap CI on ρ=0.929 (fixed repo paths) |
| `tribe_correlation_digest.py` | Top TRIBE↔outcome correlations, plain English |
| `need_slot_calendar.py` | Per-clip AD slot recommendations from need curves |
| `health_check.py` | CSV presence, venv deps, chart assets |

## TRIBE in one paragraph

TRIBE v2 predicts cortical responses to video, audio, and text on ~20k surface
vertices. SceneTwin uses the **audio-vs-audiovisual gap** as a pre-scoring risk
signal: when visual content is neurologically expensive and speech is sparse,
automatic ADQA judges disagree more (ρ = −0.75, p = 0.0003). TRIBE does **not**
replace CLIP or ADQA; it routes human review (recall@2 = 100% on 2/18 failures).

## Outputs

- `cursor/data/*.json` — static API snapshots for offline web
- `cursor/output/*.csv` — experiment tables
- `cursor/findings/*.md` — session logs (append-only)
