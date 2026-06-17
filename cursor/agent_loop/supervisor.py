#!/usr/bin/env python3
"""Supervisor loop: Claude + Codex workers, learn from outputs, skill-based tasks, anti-repeat.

Usage:
  .venv/bin/python cursor/agent_loop/supervisor.py --poll 4m --agents claude,codex
  .venv/bin/python cursor/agent_loop/supervisor.py --once
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOOP = ROOT / "cursor" / "agent_loop"
SKILLS = ROOT / ".cursor" / "skills"
TASKS = LOOP / "tasks"
RESULTS = LOOP / "results"
LOG = LOOP / "log.md"
STATE = LOOP / "state.json"
PEER = LOOP / "peer_learnings.md"

CREDIT_PAT = re.compile(
    r"credit balance is too low|insufficient_quota|429|quota exceeded|"
    r"rate.?limit|billing|CREDIT_EXHAUSTED",
    re.I,
)
BREAKTHROUGH_PAT = re.compile(r"^BREAKTHROUGH:\s*(.+)$", re.I | re.M)
CMD_RUN_PAT = re.compile(r"^COMMANDS_RUN:\s*(.+)$", re.I | re.M)
MISTAKE_PAT = re.compile(r"^MISTAKE_AVOIDED:\s*(.+)$", re.I | re.M)
APPROACH_PAT = re.compile(r"^NEW_APPROACH:\s*(.+)$", re.I | re.M)
PR_PAT = re.compile(r"^PR:\s*(.+)$", re.I | re.M)
PIPELINE_PAT = re.compile(r"cursor/pipeline/(\w+\.py)")

# id, agents, skill, one-line task, primary script (for dedup)
ANGLES = [
    {"id": "wrong_content_gate", "agents": ["codex", "claude"],
     "skill": "scenetwin-gate-eval", "script": "gate_outcome.py",
     "task": "Run gate_outcome.py (free). Report catch/ship-best rates vs random 25%. Outcome or null."},
    {"id": "human_lies_expand", "agents": ["claude"],
     "skill": "scenetwin-human-lies", "script": "gate_review_holes.py",
     "task": "Add 5 NEW hand lies to human_hallucinations.jsonl (unused video_ids), re-run gate_review_holes.py."},
    {"id": "clip_local_analysis", "agents": ["codex"],
     "skill": "scenetwin-clip-local", "script": None,
     "task": "Analyze existing CSV/JSON only. Propose+test ONE new CLIP-only signal (no LLM). Code in cursor/pipeline/ if needed."},
    {"id": "self_consistency_expand", "agents": ["codex"],
     "skill": "scenetwin-gate-eval", "script": "best_of_n_rerank.py",
     "task": "Expand best-of-N cache for clips WITHOUT cache entries only; then gate_review_holes.py. Skip if CREDIT_EXHAUSTED."},
    {"id": "gate_roc_refresh", "agents": ["codex"],
     "skill": "scenetwin-gate-eval", "script": "gate_summary.py",
     "task": "Run gate_summary.py. Summarize ROC numbers; only BREAKTHROUGH if beat 0.84 CLIP-only on new evidence."},
    {"id": "ncr_selftest", "agents": ["codex"],
     "skill": "scenetwin-clip-local", "script": "neural_contrastive_retrieval.py",
     "task": "Run neural_contrastive_retrieval.py --selftest. Report tier separation; no Colab."},
    {"id": "tribe_gate_combo", "agents": ["claude"],
     "skill": "scenetwin-clip-local", "script": None,
     "task": "Design+implement clip-level TRIBE triage THEN per-clip gate (read tribe-clip-level-triage.md + gate JSON). Local only."},
    {"id": "zero_ref_beat_058", "agents": ["claude"],
     "skill": "scenetwin-clip-local", "script": "claim_level_gate.py",
     "task": "Beat zero-reference AUC 0.58 WITHOUT reference AD. Use existing claim CSV or new CLIP feature. Honest if fail."},
    {"id": "paper_subsection_patch", "agents": ["claude"],
     "skill": "scenetwin-agent-worker", "script": None,
     "task": "Patch output/reports/paper-ad-safety-gate.md with any new numbers from cursor/output/*.json. No demo."},
    {"id": "category_gate_breakdown", "agents": ["codex"],
     "skill": "scenetwin-clip-local", "script": None,
     "task": "Per-category hallucination gate recall from external_ensemble_eval.csv + halluc_gate.csv. Script ok."},
    {"id": "novel_approach_web", "agents": ["claude", "codex"],
     "skill": "scenetwin-peer-pr", "script": None,
     "task": "Read peer latest + peer_learnings.md. Web-search ONE idea for reference-free AD hallucination detection; implement or analyze locally. Must differ from peer's NEW_APPROACH."},
    {"id": "novel_approach_pr", "agents": ["claude", "codex"],
     "skill": "scenetwin-peer-pr", "script": None,
     "task": "Ship best code from prior rounds: branch agent-loop/{agent}-*, commit, push, gh pr create. Include peer learning in PR body."},
]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_interval(s: str) -> int:
    s = s.strip().lower()
    if s.endswith("m"):
        return int(float(s[:-1]) * 60)
    if s.endswith("s"):
        return int(float(s[:-1]))
    if s.endswith("h"):
        return int(float(s[:-1]) * 3600)
    return int(s)


def load_state() -> dict:
    default = {"round": 0, "agents": {}, "breakthroughs": [], "done": {"angles": [], "scripts": [], "anti_patterns": []}, "started_at": now()}
    if STATE.exists():
        st = json.loads(STATE.read_text())
        st.setdefault("done", default["done"])
        return st
    return default


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def append_log(line: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n## [{now()}] {line}\n")


def read_latest(agent: str) -> str:
    p = RESULTS / agent / "latest.md"
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def learn_from_text(st: dict, agent: str, text: str) -> None:
    done = st.setdefault("done", {"angles": [], "scripts": [], "anti_patterns": []})
    for m in CMD_RUN_PAT.finditer(text):
        for part in m.group(1).split(","):
            part = part.strip()
            if part and part not in done["scripts"]:
                done["scripts"].append(part)
    for m in PIPELINE_PAT.finditer(text):
        script = m.group(1)
        if script not in done["scripts"]:
            done["scripts"].append(script)
    # detect waste patterns
    if ".venv39" in text or "venv39" in text:
        if "venv39_probe" not in done["anti_patterns"]:
            done["anti_patterns"].append("venv39_probe")
            append_log(f"learn | {agent} probed .venv39 — banned in next task")
    if re.search(r"ls cursor/pipeline|sed -n.*gate_review", text):
        if "pipeline_recon" not in done["anti_patterns"]:
            done["anti_patterns"].append("pipeline_recon")


def pick_angle(agent: str, st: dict) -> dict:
    done_angles = set(st.get("done", {}).get("angles", []))
    done_scripts = set(st.get("done", {}).get("scripts", []))
    bts = {b.get("angle_id") for b in st.get("breakthroughs", []) if b.get("angle_id")}

    for a in ANGLES:
        if agent not in a["agents"]:
            continue
        if a["id"] in done_angles:
            continue
        if a["id"] in bts:
            continue  # already breakthrough on this angle
        sc = a.get("script")
        if sc and sc in done_scripts and a["id"] != "self_consistency_expand":
            continue
        return a
    # fallback: least recently done angle for this agent
    for a in ANGLES:
        if agent in a["agents"] and a["id"] not in bts:
            return a
    return ANGLES[0]


def peer_of(agent: str) -> str:
    return "codex" if agent == "claude" else "claude"


def peer_excerpt(agent: str, limit: int = 600) -> str:
    text = read_latest(peer_of(agent))
    if not text.strip():
        log = LOOP / "workers" / f"{peer_of(agent)}.log"
        if log.exists():
            text = log.read_text(encoding="utf-8", errors="replace")[-4000:]
    return text[:limit] + ("..." if len(text) > limit else "")


def append_peer_learning(agent: str, rnd: int, text: str) -> None:
    lines = [f"\n### {now()} — {agent} round {rnd}\n"]
    for label, pat in [("Mistake avoided", MISTAKE_PAT), ("New approach", APPROACH_PAT), ("PR", PR_PAT)]:
        for m in pat.finditer(text):
            lines.append(f"- **{label}:** {m.group(1).strip()}\n")
    snippet = " ".join(text.split()[:60])
    if snippet:
        lines.append(f"- Summary: {snippet}...\n")
    if len(lines) > 1:
        with PEER.open("a", encoding="utf-8") as f:
            f.writelines(lines)


def build_task(agent: str, st: dict, prev: str, angle: dict) -> str:
    rnd = st["agents"].get(agent, {}).get("round", 0) + 1
    skill_path = SKILLS / angle["skill"] / "SKILL.md"
    prev_brief = " ".join(prev.split()[:80]) if prev else "(first round)"
    done_scripts = st.get("done", {}).get("scripts", [])[-8:]
    anti = st.get("done", {}).get("anti_patterns", [])
    peer = peer_of(agent)
    peer_snip = peer_excerpt(agent)
    peer_approaches = st.get("peer_approaches", {}).get(peer, "unknown")

    novel_block = ""
    if rnd >= 2:
        novel_block = f"""
**Peer mandate (round ≥2):** Read `{PEER.relative_to(ROOT)}` and `{RESULTS.relative_to(ROOT)}/{peer}/latest.md`.
Peer's last NEW_APPROACH: {peer_approaches}
You MUST use a **different** strategy. Web search allowed. Open a PR if you have shippable code (`scenetwin-peer-pr` skill).
"""

    return f"""Read `.cursor/skills/scenetwin-agent-worker/SKILL.md` + `.cursor/skills/scenetwin-peer-pr/SKILL.md` + `{skill_path.relative_to(ROOT)}`.

**Round {rnd} | angle `{angle['id']}` | agent {agent}**
{angle['task']}
{novel_block}
**Do NOT re-run:** {', '.join(done_scripts) or 'none yet'}
**Banned:** {', '.join(anti) or 'none'}

Write: `cursor/agent_loop/results/{agent}/round_{rnd:03d}.md` + `latest.md`
End with: `COMMANDS_RUN:` `MISTAKE_AVOIDED:` `NEW_APPROACH:` (+ `BREAKTHROUGH:` / `PR:` / `CREDIT_EXHAUSTED` if applicable)

**Peer ({peer}) excerpt:**
```
{peer_snip or '(peer still running — read peer_learnings.md table)'}
```

Your prev: {prev_brief}
"""


def write_task(agent: str, round_n: int, body: str, angle_id: str) -> None:
    TASKS.mkdir(parents=True, exist_ok=True)
    path = TASKS / f"{agent}.task.md"
    path.write_text(f"# round {round_n} — {agent} — {angle_id}\n\n{body}", encoding="utf-8")


def worker_cmd(agent: str, task_path: Path) -> list[str]:
    prompt = task_path.read_text(encoding="utf-8")
    extra = ("Follow scenetwin-agent-worker + scenetwin-peer-pr skills. "
             "Learn from peer mistakes; propose NEW_APPROACH each round. Web search OK. PR via gh allowed.")
    if agent == "claude":
        return ["claude", "-p", "--dangerously-skip-permissions",
                "--append-system-prompt", extra,
                f"Work in {ROOT}. Task:\n\n{prompt}"]
    return ["codex", "exec", "-s", "workspace-write", "--dangerously-bypass-approvals-and-sandbox",
            f"Work in {ROOT}. {extra}\n\nTask:\n\n{prompt}"]


def spawn(agent: str, st: dict, angle_id: str) -> int | None:
    task_path = TASKS / f"{agent}.task.md"
    if not task_path.exists():
        return None
    log_path = LOOP / "workers" / f"{agent}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    append_log(f"supervisor | spawn {agent} angle={angle_id}")
    with log_path.open("a", encoding="utf-8") as lf:
        lf.write(f"\n--- spawn {now()} angle={angle_id} ---\n")
        proc = subprocess.Popen(
            worker_cmd(agent, task_path), cwd=str(ROOT), stdout=lf, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    ag = st["agents"].setdefault(agent, {})
    ag["pid"] = proc.pid
    ag["spawned_at"] = now()
    ag["status"] = "running"
    ag["current_angle"] = angle_id
    save_state(st)
    return proc.pid


def process_result(agent: str, st: dict) -> None:
    text = read_latest(agent)
    worker_log = LOOP / "workers" / f"{agent}.log"
    if worker_log.exists():
        log_tail = worker_log.read_text(encoding="utf-8", errors="replace")[-15000:]
        learn_from_text(st, agent, log_tail)
        if not text.strip() or len(text) < 80:
            text = log_tail
            (RESULTS / agent / "latest.md").parent.mkdir(parents=True, exist_ok=True)
            (RESULTS / agent / "latest.md").write_text(text, encoding="utf-8")
    learn_from_text(st, agent, text)

    ag = st["agents"].setdefault(agent, {})
    rnd = ag.get("round", 0) + 1
    ag["round"] = rnd
    ag["last_checked"] = now()
    ag["status"] = "idle"
    angle_id = ag.pop("current_angle", None)

    if angle_id:
        st.setdefault("done", {}).setdefault("angles", [])
        if angle_id not in st["done"]["angles"]:
            st["done"]["angles"].append(angle_id)

    if not text.strip():
        append_log(f"{agent} | round {rnd} empty")
        return

    if CREDIT_PAT.search(text):
        ag["status"] = "credit_exhausted"
        ag["alive"] = False
        append_log(f"{agent} | CREDIT_EXHAUSTED")
        return

    ag["alive"] = True
    append_log(f"{agent} | round {rnd} angle={angle_id} — {' '.join(text.split())[:160]}")
    append_peer_learning(agent, rnd, text)

    for m in APPROACH_PAT.finditer(text):
        st.setdefault("peer_approaches", {})[agent] = m.group(1).strip()[:200]

    for m in BREAKTHROUGH_PAT.finditer(text):
        title = m.group(1).strip()
        entry = {"agent": agent, "round": rnd, "title": title, "angle_id": angle_id, "at": now()}
        st.setdefault("breakthroughs", []).append(entry)
        append_log(f"BREAKTHROUGH ({agent}): {title}")


def poll(st: dict, agents: list[str]) -> None:
    st["round"] = st.get("round", 0) + 1
    append_log(f"supervisor | poll {st['round']}")

    for agent in agents:
        ag = st["agents"].setdefault(agent, {"alive": True, "round": 0})
        if ag.get("status") == "credit_exhausted":
            continue

        pid = ag.get("pid")
        running = pid and subprocess.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0

        if running:
            append_log(f"{agent} | running pid={pid} angle={ag.get('current_angle')}")
            continue

        if ag.get("status") == "running":
            process_result(agent, st)

        if ag.get("alive", True) and ag.get("status") != "credit_exhausted":
            angle = pick_angle(agent, st)
            prev = read_latest(agent)
            nxt = ag.get("round", 0) + 1
            write_task(agent, nxt, build_task(agent, st, prev, angle), angle["id"])
            spawn(agent, st, angle["id"])

    save_state(st)


def seed_learnings(st: dict) -> None:
    """Bootstrap from codex round-1 log if supervisor restarted mid-run."""
    log = LOOP / "workers" / "codex.log"
    if log.exists():
        learn_from_text(st, "codex", log.read_text(encoding="utf-8", errors="replace")[-20000:])
    st.setdefault("done", {}).setdefault("angles", [])
    if "self_consistency_expand" not in st["done"]["angles"]:
        if "best_of_n_rerank.py" in st.get("done", {}).get("scripts", []):
            append_log("learn | codex already running best_of_n_rerank — mark angle in-progress")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--poll", default="4m")
    ap.add_argument("--agents", default="claude,codex")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    interval = parse_interval(args.poll)

    st = load_state()
    seed_learnings(st)
    LOG.parent.mkdir(parents=True, exist_ok=True)

    for agent in agents:
        ag = st["agents"].setdefault(agent, {"alive": True, "round": 0})
        if ag.get("round", 0) == 0 and not (TASKS / f"{agent}.task.md").exists():
            angle = pick_angle(agent, st)
            write_task(agent, 1, build_task(agent, st, "", angle), angle["id"])
        if ag.get("alive", True) and ag.get("status") not in ("running", "credit_exhausted") and not ag.get("pid"):
            angle = pick_angle(agent, st)
            if not (TASKS / f"{agent}.task.md").exists():
                write_task(agent, 1, build_task(agent, st, "", angle), angle["id"])
            spawn(agent, st, ag.get("current_angle") or angle["id"])

    save_state(st)
    if args.once:
        poll(st, agents)
        print(json.dumps(st, indent=2))
        return

    append_log(f"supervisor | v2 skill-based loop poll={args.poll}")
    print(f"Supervisor v2 running. State: {STATE}")
    try:
        while True:
            time.sleep(interval)
            st = load_state()
            poll(st, agents)
            st = load_state()
            if not any(st["agents"].get(a, {}).get("alive", True) and st["agents"].get(a, {}).get("status") != "credit_exhausted" for a in agents):
                append_log("supervisor | all agents stopped")
                break
    except KeyboardInterrupt:
        append_log("supervisor | interrupted")


if __name__ == "__main__":
    main()
