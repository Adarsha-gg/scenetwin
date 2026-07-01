#!/usr/bin/env python3
"""Local-only analysis of uniform vs TRIBE-guided ADQA frame sampling.

No external APIs are called. The script reads existing frame directories and
cached CSV outputs, then writes reproducible artifacts for the parallel research
pass requested on TRIBE-guided frame sampling.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
FRAMES = TIMING / "adqa_frames"
OUT = ROOT / "cursor" / "research" / "output" / "parallel_research" / "frame_sampling"
REPORT = ROOT / "output" / "reports" / "parallel-research-tribe-frame-sampling.md"
SUBREPORT = ROOT / "subagent-reports" / "parallel-frame-sampling.md"

NEED_CSV = TIMING / "need" / "coarse_need_windows.csv"
ROUTER_CSV = ROOT / "cursor" / "research" / "output" / "tribe_blind_spot_windows.csv"
ROUTING_CSV = TIMING / "tribe_native" / "tribe_failure_routing.csv"
BASE_AGG = TIMING / "adqa_q-claude-haiku-4-5_g-claude-haiku-4-5" / "aggregate_results.csv"
TRIBE_AGG = TIMING / "adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5" / "aggregate_results.csv"
BASE_TIER = TIMING / "adqa_q-claude-haiku-4-5_g-claude-haiku-4-5" / "tier_scores.csv"
TRIBE_TIER = TIMING / "adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5" / "tier_scores.csv"

FRAME_RE = re.compile(r"frame_\d+_t([0-9]+(?:\.[0-9]+)?)\.jpg$")
DIR_RE = re.compile(r"clip_(\d{2})(_tribe)?$")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({k for row in rows for k in row.keys()}) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fnum(value: str | int | float | None, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def inventory_frames() -> dict[int, dict[str, list[dict]]]:
    inv: dict[int, dict[str, list[dict]]] = defaultdict(lambda: {"uniform": [], "tribe": []})
    if not FRAMES.exists():
        return inv
    for d in sorted(p for p in FRAMES.iterdir() if p.is_dir()):
        mdir = DIR_RE.match(d.name)
        if not mdir:
            continue
        clip_idx = int(mdir.group(1))
        sampler = "tribe" if mdir.group(2) else "uniform"
        for jpg in sorted(d.glob("frame_*.jpg")):
            mf = FRAME_RE.search(jpg.name)
            if not mf:
                continue
            inv[clip_idx][sampler].append({"time_s": fnum(mf.group(1)), "path": str(jpg.relative_to(ROOT))})
    for clip in inv:
        for sampler in ("uniform", "tribe"):
            inv[clip][sampler].sort(key=lambda r: r["time_s"])
    return inv


def load_need_windows() -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = defaultdict(list)
    for r in read_csv(NEED_CSV):
        c = int(float(r["clip_idx"]))
        need = fnum(r.get("need_score"))
        out[c].append({
            "source": "coarse_need_windows",
            "window_idx": int(float(r["window_idx"])),
            "start_s": fnum(r["start_s"]),
            "end_s": fnum(r["end_s"]),
            "need_score": need,
            "recommendation": r.get("recommendation", ""),
            "high_need_ge_0_4": need >= 0.4,
            "routed_high": r.get("recommendation") != "low_ad_need",
            "route": r.get("recommendation", ""),
            "dominant_type": "",
        })
    for c in out:
        out[c].sort(key=lambda r: r["window_idx"])
    return out


def load_router_windows() -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = defaultdict(list)
    for r in read_csv(ROUTER_CSV):
        if r.get("corpus") != "inbench" or not r.get("clip_idx"):
            continue
        c = int(float(r["clip_idx"]))
        route = r.get("route", "")
        out[c].append({
            "source": "tribe_blind_spot_windows",
            "window_idx": int(float(r["window_idx"])),
            "start_s": fnum(r["start_s"]),
            "end_s": fnum(r["end_s"]),
            "need_score": fnum(r.get("mean_visual_gap")),
            "recommendation": route,
            "high_need_ge_0_4": route != "static_ad_ok_low_gap",
            "routed_high": route != "static_ad_ok_low_gap",
            "route": route,
            "dominant_type": r.get("dominant_type", ""),
        })
    for c in out:
        out[c].sort(key=lambda r: r["window_idx"])
    return out


def frames_in_windows(frames: list[dict], windows: list[dict], predicate) -> tuple[int, int, set[int]]:
    selected = [w for w in windows if predicate(w)]
    hit_windows: set[int] = set()
    count = 0
    for fr in frames:
        t = fr["time_s"]
        hit = False
        for w in selected:
            if w["start_s"] <= t <= w["end_s"]:
                hit = True
                hit_windows.add(w["window_idx"])
        if hit:
            count += 1
    return count, len(selected), hit_windows


def nearest_stats(a: list[dict], b: list[dict]) -> dict[str, float]:
    if not a or not b:
        return {"mean": math.nan, "median": math.nan, "max": math.nan, "new_count_0_35s": 0}
    ds = [min(abs(x["time_s"] - y["time_s"]) for y in b) for x in a]
    return {"mean": mean(ds), "median": median(ds), "max": max(ds), "new_count_0_35s": sum(d > 0.35 for d in ds)}


def rate(num: int, den: int) -> float:
    return (num / den) if den else math.nan


def fmt(x, digits=3):
    if isinstance(x, float):
        if math.isnan(x):
            return ""
        return f"{x:.{digits}f}"
    return x


def agg_one(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def score_col(rows: list[dict]) -> str | None:
    if not rows:
        return None
    for k in rows[0]:
        if k.endswith("_score"):
            return k
    return None


def full_order_status(rows: list[dict], score_key: str) -> dict[int, bool]:
    by_clip: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_clip[int(float(r["clip_idx"]))].append(r)
    status = {}
    for c, rs in by_clip.items():
        scores = {int(float(r["gt"])): fnum(r[score_key]) for r in rs}
        status[c] = all(gt in scores for gt in (0, 1, 2, 3)) and scores[3] > scores[2] > scores[1] > scores[0]
    return status


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inv = inventory_frames()
    need = load_need_windows()
    router = load_router_windows()
    routing = {int(float(r["clip_idx"])): r for r in read_csv(ROUTING_CSV) if r.get("clip_idx")}

    clip_rows: list[dict] = []
    window_rows: list[dict] = []
    material_rows: list[dict] = []
    all_clips = sorted(set(inv) | set(need) | set(router))

    for c in all_clips:
        uni = inv.get(c, {}).get("uniform", [])
        tri = inv.get(c, {}).get("tribe", [])
        nw = need.get(c, [])
        rw = router.get(c, [])

        u_high, n_high, u_hit = frames_in_windows(uni, nw, lambda w: w["high_need_ge_0_4"])
        t_high, _, t_hit = frames_in_windows(tri, nw, lambda w: w["high_need_ge_0_4"])
        u_rec, n_rec, u_rec_hit = frames_in_windows(uni, nw, lambda w: w["routed_high"])
        t_rec, _, t_rec_hit = frames_in_windows(tri, nw, lambda w: w["routed_high"])
        u_route, n_route, u_route_hit = frames_in_windows(uni, rw, lambda w: w["routed_high"])
        t_route, _, t_route_hit = frames_in_windows(tri, rw, lambda w: w["routed_high"])
        u_action, n_action, u_action_hit = frames_in_windows(uni, rw, lambda w: w["route"] == "action_state_or_agent_cue")
        t_action, _, t_action_hit = frames_in_windows(tri, rw, lambda w: w["route"] == "action_state_or_agent_cue")
        ns = nearest_stats(tri, uni)
        duplicate_tribe_times = len(tri) - len({round(fr["time_s"], 2) for fr in tri})
        material = (
            abs(rate(t_high, len(tri)) - rate(u_high, len(uni))) >= 0.20 if tri and uni else False
        ) or (
            abs(rate(t_route, len(tri)) - rate(u_route, len(uni))) >= 0.20 if tri and uni and n_route else False
        ) or ns["mean"] >= 0.60 or duplicate_tribe_times > 0

        clip_row = {
            "clip_idx": c,
            "category": routing.get(c, {}).get("category", ""),
            "uniform_n": len(uni),
            "tribe_n": len(tri),
            "uniform_times_s": ";".join(fmt(fr["time_s"], 2) for fr in uni),
            "tribe_times_s": ";".join(fmt(fr["time_s"], 2) for fr in tri),
            "high_need_windows_ge_0_4": n_high,
            "uniform_high_need_frame_rate": rate(u_high, len(uni)),
            "tribe_high_need_frame_rate": rate(t_high, len(tri)),
            "delta_high_need_frame_rate": rate(t_high, len(tri)) - rate(u_high, len(uni)) if tri and uni else math.nan,
            "uniform_high_need_window_coverage": rate(len(u_hit), n_high),
            "tribe_high_need_window_coverage": rate(len(t_hit), n_high),
            "delta_high_need_window_coverage": rate(len(t_hit), n_high) - rate(len(u_hit), n_high) if n_high else math.nan,
            "routed_need_windows_non_low": n_rec,
            "uniform_routed_need_frame_rate": rate(u_rec, len(uni)),
            "tribe_routed_need_frame_rate": rate(t_rec, len(tri)),
            "router_blindspot_windows": n_route,
            "uniform_router_frame_rate": rate(u_route, len(uni)),
            "tribe_router_frame_rate": rate(t_route, len(tri)),
            "delta_router_frame_rate": rate(t_route, len(tri)) - rate(u_route, len(uni)) if tri and uni and n_route else math.nan,
            "action_route_windows": n_action,
            "uniform_action_frame_rate": rate(u_action, len(uni)),
            "tribe_action_frame_rate": rate(t_action, len(tri)),
            "delta_action_frame_rate": rate(t_action, len(tri)) - rate(u_action, len(uni)) if tri and uni and n_action else math.nan,
            "tribe_mean_nearest_uniform_delta_s": ns["mean"],
            "tribe_max_nearest_uniform_delta_s": ns["max"],
            "tribe_frames_not_near_uniform_0_35s": ns["new_count_0_35s"],
            "tribe_duplicate_timestamps": duplicate_tribe_times,
            "materially_different": material,
            "tribe_route": routing.get(c, {}).get("tribe_route", ""),
            "quality_risk": routing.get(c, {}).get("quality_risk", ""),
        }
        clip_rows.append(clip_row)
        if material:
            material_rows.append(clip_row)

        for source, windows in (("coarse_need_windows", nw), ("tribe_blind_spot_windows", rw)):
            for w in windows:
                if source == "coarse_need_windows":
                    high = w["high_need_ge_0_4"]
                else:
                    high = w["routed_high"]
                if not high:
                    continue
                uc = sum(1 for fr in uni if w["start_s"] <= fr["time_s"] <= w["end_s"])
                tc = sum(1 for fr in tri if w["start_s"] <= fr["time_s"] <= w["end_s"])
                window_rows.append({
                    "clip_idx": c,
                    "source": source,
                    "window_idx": w["window_idx"],
                    "start_s": w["start_s"],
                    "end_s": w["end_s"],
                    "route_or_recommendation": w["route"],
                    "dominant_type": w["dominant_type"],
                    "need_or_gap_score": w["need_score"],
                    "uniform_frame_count": uc,
                    "tribe_frame_count": tc,
                    "delta_tribe_minus_uniform": tc - uc,
                })

    # Existing cached scoring comparison (no re-scoring/API call).
    base_agg = agg_one(BASE_AGG)
    tribe_agg = agg_one(TRIBE_AGG)
    base_rows = read_csv(BASE_TIER)
    tribe_rows = read_csv(TRIBE_TIER)
    base_col = score_col(base_rows)
    tribe_col = score_col(tribe_rows)
    base_order = full_order_status(base_rows, base_col) if base_col else {}
    tribe_order = full_order_status(tribe_rows, tribe_col) if tribe_col else {}
    score_rows = []
    if base_col and tribe_col:
        by_base = {(int(float(r["clip_idx"])), r["tier"]): r for r in base_rows}
        for r in tribe_rows:
            key = (int(float(r["clip_idx"])), r["tier"])
            b = by_base.get(key)
            if not b:
                continue
            score_rows.append({
                "clip_idx": key[0],
                "tier": key[1],
                "gt": r["gt"],
                "uniform_adqa_score": fnum(b[base_col]),
                "tribe_adqa_score": fnum(r[tribe_col]),
                "delta_tribe_minus_uniform": fnum(r[tribe_col]) - fnum(b[base_col]),
            })

    write_csv(OUT / "frame_sampling_overlap_by_clip.csv", clip_rows, [
        "clip_idx", "category", "uniform_n", "tribe_n", "uniform_times_s", "tribe_times_s",
        "high_need_windows_ge_0_4", "uniform_high_need_frame_rate", "tribe_high_need_frame_rate", "delta_high_need_frame_rate",
        "uniform_high_need_window_coverage", "tribe_high_need_window_coverage", "delta_high_need_window_coverage",
        "routed_need_windows_non_low", "uniform_routed_need_frame_rate", "tribe_routed_need_frame_rate",
        "router_blindspot_windows", "uniform_router_frame_rate", "tribe_router_frame_rate", "delta_router_frame_rate",
        "action_route_windows", "uniform_action_frame_rate", "tribe_action_frame_rate", "delta_action_frame_rate",
        "tribe_mean_nearest_uniform_delta_s", "tribe_max_nearest_uniform_delta_s", "tribe_frames_not_near_uniform_0_35s",
        "tribe_duplicate_timestamps", "materially_different", "tribe_route", "quality_risk"
    ])
    write_csv(OUT / "high_gap_window_frame_counts.csv", window_rows)
    write_csv(OUT / "materially_different_clips.csv", material_rows)
    write_csv(OUT / "cached_adqa_uniform_vs_tribe_scores.csv", score_rows)

    def agg_rate(rows, key_num, key_den=None):
        if key_den:
            den = sum(int(r[key_den]) for r in rows)
            num = sum(int(r[key_num]) for r in rows)
            return rate(num, den)
        vals = [float(r[key_num]) for r in rows if r.get(key_num) not in ("", None) and not math.isnan(float(r[key_num]))]
        return mean(vals) if vals else math.nan

    total_uniform = sum(r["uniform_n"] for r in clip_rows)
    total_tribe = sum(r["tribe_n"] for r in clip_rows)
    total_high_frames_uniform = sum(round(r["uniform_high_need_frame_rate"] * r["uniform_n"]) for r in clip_rows if r["uniform_n"])
    total_high_frames_tribe = sum(round(r["tribe_high_need_frame_rate"] * r["tribe_n"]) for r in clip_rows if r["tribe_n"])
    total_router_frames_uniform = sum(round(r["uniform_router_frame_rate"] * r["uniform_n"]) for r in clip_rows if r["uniform_n"] and not math.isnan(r["uniform_router_frame_rate"]))
    total_router_frames_tribe = sum(round(r["tribe_router_frame_rate"] * r["tribe_n"]) for r in clip_rows if r["tribe_n"] and not math.isnan(r["tribe_router_frame_rate"]))
    action_rows = [r for r in clip_rows if r["action_route_windows"]]
    total_action_frames_uniform = sum(round(r["uniform_action_frame_rate"] * r["uniform_n"]) for r in action_rows if r["uniform_n"] and not math.isnan(r["uniform_action_frame_rate"]))
    total_action_frames_tribe = sum(round(r["tribe_action_frame_rate"] * r["tribe_n"]) for r in action_rows if r["tribe_n"] and not math.isnan(r["tribe_action_frame_rate"]))

    summary = {
        "inputs": {
            "frames_dir": str(FRAMES.relative_to(ROOT)),
            "need_csv": str(NEED_CSV.relative_to(ROOT)),
            "router_csv": str(ROUTER_CSV.relative_to(ROOT)),
            "uniform_adqa_aggregate": str(BASE_AGG.relative_to(ROOT)),
            "tribe_adqa_aggregate": str(TRIBE_AGG.relative_to(ROOT)),
        },
        "counts": {
            "clips_with_any_frames": len([r for r in clip_rows if r["uniform_n"] or r["tribe_n"]]),
            "clips_with_uniform_and_tribe_frames": len([r for r in clip_rows if r["uniform_n"] and r["tribe_n"]]),
            "clips_with_tribe_under_8_frames": len([r for r in clip_rows if r["uniform_n"] and r["tribe_n"] and r["tribe_n"] < 8]),
            "clips_with_uniform_under_8_frames": len([r for r in clip_rows if r["uniform_n"] and r["tribe_n"] and r["uniform_n"] < 8]),
            "uniform_frames": total_uniform,
            "tribe_frames": total_tribe,
            "high_need_windows_ge_0_4": sum(r["high_need_windows_ge_0_4"] for r in clip_rows),
            "router_blindspot_windows": sum(r["router_blindspot_windows"] for r in clip_rows),
            "action_route_clips": len(action_rows),
            "materially_different_clips": len(material_rows),
        },
        "coverage": {
            "uniform_high_need_frame_rate": rate(total_high_frames_uniform, total_uniform),
            "tribe_high_need_frame_rate": rate(total_high_frames_tribe, total_tribe),
            "uniform_router_frame_rate": rate(total_router_frames_uniform, total_uniform),
            "tribe_router_frame_rate": rate(total_router_frames_tribe, total_tribe),
            "uniform_action_frame_rate_on_action_clips": rate(total_action_frames_uniform, sum(r["uniform_n"] for r in action_rows)),
            "tribe_action_frame_rate_on_action_clips": rate(total_action_frames_tribe, sum(r["tribe_n"] for r in action_rows)),
            "mean_clip_high_need_frame_rate_delta": mean([r["delta_high_need_frame_rate"] for r in clip_rows if not math.isnan(r["delta_high_need_frame_rate"])]),
            "mean_clip_router_frame_rate_delta": mean([r["delta_router_frame_rate"] for r in clip_rows if not math.isnan(r["delta_router_frame_rate"])]),
        },
        "cached_scoring": {
            "uniform_spearman_rho": fnum(base_agg.get("spearman_rho"), math.nan),
            "tribe_spearman_rho": fnum(tribe_agg.get("spearman_rho"), math.nan),
            "uniform_pairwise_wins": f"{base_agg.get('pairwise_wins')}/{base_agg.get('pairwise_total')}",
            "tribe_pairwise_wins": f"{tribe_agg.get('pairwise_wins')}/{tribe_agg.get('pairwise_total')}",
            "uniform_full_order": f"{base_agg.get('full_order_clips')}/{base_agg.get('full_order_total')}",
            "tribe_full_order": f"{tribe_agg.get('full_order_clips')}/{tribe_agg.get('full_order_total')}",
            "full_order_flips_to_tribe": sorted([c for c in tribe_order if tribe_order.get(c) and not base_order.get(c)]),
            "full_order_flips_against_tribe": sorted([c for c in base_order if base_order.get(c) and not tribe_order.get(c)]),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    top_material = sorted(material_rows, key=lambda r: (
        abs(r["delta_high_need_frame_rate"]) if not math.isnan(r["delta_high_need_frame_rate"]) else 0,
        r["tribe_mean_nearest_uniform_delta_s"] if not math.isnan(r["tribe_mean_nearest_uniform_delta_s"]) else 0,
    ), reverse=True)[:8]
    duplicate_clips = [r for r in clip_rows if r["tribe_duplicate_timestamps"]]

    md = []
    md.append("# Parallel research: TRIBE-guided frame sampling\n")
    md.append("## Scope\n")
    md.append("Local-only pass over existing uniform vs TRIBE ADQA frame directories, cached timing/window/router CSVs, and cached ADQA aggregate outputs. No external APIs were called. The requested `context.md` and `plan.md` were not present in the repo, so this report uses the explicit task plus local artifacts as source of truth.\n")
    md.append("## Inputs and artifacts\n")
    for k, v in summary["inputs"].items():
        md.append(f"- `{v.replace(chr(92), '/')}` ({k})\n")
    md.append("- Output artifacts: `cursor/research/output/parallel_research/frame_sampling/`\n")

    md.append("## Findings\n")
    md.append(f"1. **TRIBE sampling does target more high-gap need windows, but only modestly.** Across {summary['counts']['clips_with_uniform_and_tribe_frames']} clips with both frame sets, uniform frames landed in `need_score >= 0.4` windows at {summary['coverage']['uniform_high_need_frame_rate']:.1%}; TRIBE frames landed there at {summary['coverage']['tribe_high_need_frame_rate']:.1%}. Mean per-clip high-need frame-rate delta was {summary['coverage']['mean_clip_high_need_frame_rate_delta']:+.1%}.\n")
    md.append(f"2. **Typed router overlap also improves only slightly.** Against `tribe_blind_spot_windows.csv` routed windows (`layout_replay_or_scene_cue` or `action_state_or_agent_cue`), uniform frame overlap was {summary['coverage']['uniform_router_frame_rate']:.1%} and TRIBE frame overlap was {summary['coverage']['tribe_router_frame_rate']:.1%}; mean per-clip routed-window delta was {summary['coverage']['mean_clip_router_frame_rate_delta']:+.1%}.\n")
    md.append(f"3. **Action-window coverage does not improve overall.** On {summary['counts']['action_route_clips']} clips with an `action_state_or_agent_cue` router window, uniform frame overlap was {summary['coverage']['uniform_action_frame_rate_on_action_clips']:.1%}; TRIBE overlap was {summary['coverage']['tribe_action_frame_rate_on_action_clips']:.1%}. Clip 08 improves locally, but the aggregate action-route result does **not** yet show that current TRIBE sampling fixes the static-composition-over-temporal-action blind spot.\n")
    md.append(f"4. **Material differences exist, but budget parity is weak.** {summary['counts']['materially_different_clips']} clips met the material-difference rule (`>=20pp` frame-rate shift into high/routed windows, mean nearest-frame shift `>=0.60s`, or duplicate TRIBE timestamps). However, {summary['counts']['clips_with_tribe_under_8_frames']}/{summary['counts']['clips_with_uniform_and_tribe_frames']} TRIBE frame folders and {summary['counts']['clips_with_uniform_under_8_frames']}/{summary['counts']['clips_with_uniform_and_tribe_frames']} uniform folders contain fewer than the intended 8 frames, so comparisons are not fully budget matched.\n")
    md.append(f"5. **Cached ADQA scoring does not show a global ranking lift.** With the same cached Claude-Haiku questioner/grader, uniform ADQA has Spearman rho `{summary['cached_scoring']['uniform_spearman_rho']:.3f}`, pairwise `{summary['cached_scoring']['uniform_pairwise_wins']}`, full-order `{summary['cached_scoring']['uniform_full_order']}`; TRIBE-frame ADQA has rho `{summary['cached_scoring']['tribe_spearman_rho']:.3f}`, pairwise `{summary['cached_scoring']['tribe_pairwise_wins']}`, full-order `{summary['cached_scoring']['tribe_full_order']}`. This supports TRIBE sampling as a targeted coverage/triage change, not a proven aggregate leaderboard improvement.\n")
    md.append("\n## Review findings\n")
    md.append(f"- **Medium — frame-budget mismatch:** Existing `_tribe` directories contain only {summary['counts']['tribe_frames']} frames vs {summary['counts']['uniform_frames']} uniform frames, and {summary['counts']['clips_with_tribe_under_8_frames']}/{summary['counts']['clips_with_uniform_and_tribe_frames']} TRIBE clip folders are below `N_FRAMES=8`. Path: `output/scenetwin_timing_20clip/adqa_frames`; evidence: `cursor/research/output/parallel_research/frame_sampling/frame_sampling_overlap_by_clip.csv`.\n")
    md.append(f"- **Medium — temporal/action blind spot not solved:** Action-route overlap is lower for TRIBE than uniform ({summary['coverage']['tribe_action_frame_rate_on_action_clips']:.1%} vs {summary['coverage']['uniform_action_frame_rate_on_action_clips']:.1%}) on the 9 action-route clips. Path: `cursor/research/output/tribe_blind_spot_windows.csv`; evidence: `high_gap_window_frame_counts.csv`.\n")
    md.append(f"- **Low — aggregate scorer lift not established:** Cached TRIBE-frame ADQA improves pairwise wins ({summary['cached_scoring']['tribe_pairwise_wins']} vs {summary['cached_scoring']['uniform_pairwise_wins']}) but has lower rho ({summary['cached_scoring']['tribe_spearman_rho']:.3f} vs {summary['cached_scoring']['uniform_spearman_rho']:.3f}). Path: `output/scenetwin_timing_20clip/adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5/aggregate_results.csv`.\n")
    md.append("\n## Materially different clips (top local examples)\n")
    md.append("| clip | category | uniform n | TRIBE n | high-gap frame-rate delta | routed frame-rate delta | action delta | mean nearest shift | notes |\n")
    md.append("|---:|---|---:|---:|---:|---:|---:|---:|---|\n")
    for r in top_material:
        notes = []
        if r["tribe_duplicate_timestamps"]:
            notes.append(f"{r['tribe_duplicate_timestamps']} duplicate TRIBE timestamps")
        if r["tribe_n"] < 8:
            notes.append("TRIBE frame dir has <8 frames")
        if r["action_route_windows"]:
            notes.append("action-route clip")
        md.append(f"| {r['clip_idx']:02d} | {r['category']} | {r['uniform_n']} | {r['tribe_n']} | {r['delta_high_need_frame_rate']:+.1%} | {fmt(r['delta_router_frame_rate'])} | {fmt(r['delta_action_frame_rate'])} | {r['tribe_mean_nearest_uniform_delta_s']:.2f}s | {'; '.join(notes)} |\n")

    md.append("\n## Known temporal blind spot assessment\n")
    md.append("The prior limitation was that 8 evenly sampled frames can reward static composition and miss temporal actions such as pouring, sports motion, or fast state changes. The local evidence is mixed-to-negative for the current implementation: TRIBE sampling shifts frames toward coarse high-gap windows, which is a plausible mechanism for better temporal targeting, but it does **not** increase aggregate `action_state_or_agent_cue` coverage in the typed router. The available cached score comparison is also insufficient to claim a solved blind spot: aggregate rho decreases slightly while pairwise wins improve, and many TRIBE frame folders contain fewer than the intended 8 frames, reducing budget parity.\n")

    md.append("\n## Residual risks / limits\n")
    md.append("- No new LLM/CLIP/VLM scoring was run. Existing cached scoring can be summarized, but verifying whether the new frames improve question relevance requires re-running ADQA generation/grading or CLIP/video-native scoring.\n")
    md.append("- The TRIBE sampler in `tools/scenetwin_tribe_adqa.py` allocates frames over all need windows with a minimum-per-window rule; existing `_tribe` directories often have fewer than `N_FRAMES=8`, so current comparison is not fully budget matched.\n")
    md.append("- Local window overlap measures temporal coverage, not semantic correctness. A frame inside an action window may still miss the critical sub-action.\n")
    md.append("- `context.md` and `plan.md` requested by the task were absent, so no additional experiment-specific constraints could be applied.\n")

    md.append("\n## Next runnable command/batch\n")
    md.append("If API credentials are available and external calls are allowed later, rerun the matched ADQA comparison after deleting/regenerating incomplete TRIBE frame folders so both samplers use 8 frames:\n")
    md.append("```bash\npython tools/scenetwin_tribe_adqa.py --question-model anthropic:claude-haiku-4-5-20251001 --grader-model anthropic:claude-haiku-4-5-20251001 --refresh-cache\n```\n")
    md.append("For a local-only reproducibility check of this pass:\n")
    md.append("```bash\npython cursor/research/parallel_frame_sampling_analysis.py\n```\n")

    md.append("\n## Artifact index\n")
    md.append("- `cursor/research/output/parallel_research/frame_sampling/frame_sampling_overlap_by_clip.csv` — per-clip frame timestamp overlap/coverage metrics.\n")
    md.append("- `cursor/research/output/parallel_research/frame_sampling/high_gap_window_frame_counts.csv` — per-high-window uniform vs TRIBE frame counts.\n")
    md.append("- `cursor/research/output/parallel_research/frame_sampling/materially_different_clips.csv` — clips with material timestamp/coverage shifts.\n")
    md.append("- `cursor/research/output/parallel_research/frame_sampling/cached_adqa_uniform_vs_tribe_scores.csv` — cached per-tier ADQA score comparison; no re-scoring.\n")
    md.append("- `cursor/research/output/parallel_research/frame_sampling/summary.json` — machine-readable summary.\n")

    report_text = "".join(md)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text, encoding="utf-8")
    SUBREPORT.parent.mkdir(parents=True, exist_ok=True)
    SUBREPORT.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
