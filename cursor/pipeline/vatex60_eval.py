#!/usr/bin/env python3
"""VATEX-only held-out eval — up to 60 clips from vatex_overlap.json (excl. benchmark).

All clips use the same 4-tier scaffold as the 18-clip benchmark:
  tier3 = VideoA11y pro AD, tier1/2 = VATEX captions, tier0 = cross control.

Reuses CLIP + ADQA ensemble pipeline; filters registry to vatex_overlap membership.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
OVERLAP = ROOT / "workspace" / "vatex_overlap.json"
BENCHMARK = ROOT / "workspace" / "vatex_eval_clips.json"
EXT_DIR = CURSOR / "data" / "external_clips"
REGISTRY = EXT_DIR / "registry.jsonl"
OUT_DIR = CURSOR / "output" / "vatex60"
OUT_JSON = OUT_DIR / "vatex60_ensemble_eval.json"
OUT_CSV = OUT_DIR / "vatex60_ensemble_eval.csv"
FINDINGS = CURSOR / "findings" / "vatex60-generalization.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}
N_FRAMES = 8


def load_vatex60_registry(limit: int = 60) -> list[dict]:
    bench_ids = {c["video_id"] for c in json.loads(BENCHMARK.read_text())}
    overlap_ids = {c["video_id"] for c in json.loads(OVERLAP.read_text())}
    rows = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["video_id"] in bench_ids:
            continue
        if r["video_id"] not in overlap_ids:
            continue
        if not r.get("download_ok", True):
            continue
        rows.append(r)
    return rows[:limit]


def ensure_frames(video_id: str, mp4: Path) -> None:
    out = EXT_DIR / "frames" / video_id
    if len(list(out.glob("frame_*.jpg"))) >= N_FRAMES:
        return
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(mp4))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {mp4}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps if total else 10.0
    for k in range(N_FRAMES):
        t = (k + 0.5) * duration / N_FRAMES
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        h, w = frame.shape[:2]
        if max(h, w) > 512:
            s = 512 / max(h, w)
            frame = cv2.resize(frame, (int(w * s), int(h * s)))
        cv2.imwrite(str(out / f"frame_{k:02d}_t{t:.2f}.jpg"), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    cap.release()


def minmax_clipwise(df: pd.DataFrame, col: str, group: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        if not np.isfinite(lo) or hi == lo:
            return pd.Series(np.full(len(s), 0.5), index=s.index)
        return (s - lo) / (hi - lo)

    return df.groupby(group, group_keys=False)[col].apply(scale)


def metrics(df: pd.DataFrame, col: str, group: str) -> dict:
    rho, p = spearmanr(df["gt"], df[col], nan_policy="omit")
    fo = pw = 0
    fo_t = pw_t = 0
    comparisons = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]
    for _, g in df.groupby(group):
        by = dict(zip(g["tier"], g[col]))
        if all(t in by for t in TIERS):
            fo_t += 1
            t3, t2, t1, t0 = (by["tier3_va11y"], by["tier2_vatex_long"],
                              by["tier1_vatex_short"], by["tier0_cross"])
            fo += int(t3 > t2 > t1 > t0)
        if "tier3_va11y" in by:
            for lo in comparisons:
                if lo in by:
                    pw_t += 1
                    pw += int(by["tier3_va11y"] > by[lo])
    return {
        "spearman_rho": float(rho),
        "spearman_p": float(p),
        "full_order": fo,
        "full_order_total": fo_t,
        "full_order_rate": float(fo / fo_t) if fo_t else float("nan"),
        "pairwise_wins": pw,
        "pairwise_total": pw_t,
        "n_rows": len(df),
        "n_clips": df[group].nunique(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--skip-adqa", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    registry = load_vatex60_registry(args.limit)
    if not registry:
        raise SystemExit("No VATEX clips in registry — run acquire_external_clip.py first")
    print(f"VATEX held-out set: {len(registry)} clips (benchmark excluded)")

    for meta in registry:
        mp4 = EXT_DIR / meta["video_id"] / "clip.mp4"
        if mp4.exists():
            ensure_frames(meta["video_id"], mp4)

    # CLIP scores (reuse cached CSV unless missing)
    clip_csv = CURSOR / "output" / "external_clip_full_eval.csv"
    if not clip_csv.exists():
        subprocess.run(
            [sys.executable, str(CURSOR / "pipeline" / "external_clip_pipeline.py")],
            cwd=str(ROOT),
            check=True,
        )

    if not args.skip_adqa:
        subprocess.run(
            [sys.executable, str(CURSOR / "pipeline" / "external_ensemble_eval.py")]
            + (["--refresh-cache"] if args.refresh_cache else []),
            cwd=str(ROOT),
            check=True,
        )

    vatex_ids = {m["video_id"] for m in registry}
    clip_df = pd.read_csv(clip_csv)
    clip_df = clip_df[clip_df["video_id"].isin(vatex_ids)]

    ens_path = CURSOR / "output" / "external_ensemble_eval.csv"
    if ens_path.exists():
        ens = pd.read_csv(ens_path)
        ens = ens[ens["video_id"].isin(vatex_ids)]
    else:
        ens = clip_df.copy()
        ens["adqa_score"] = float("nan")
        ens["adqa_norm"] = float("nan")
        ens["clip_top3_norm"] = minmax_clipwise(ens, "clip_top3", "video_id")
        ens["ensemble_mean_clip_top3"] = ens["clip_top3_norm"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ens.to_csv(OUT_CSV, index=False)

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "source": "vatex_overlap.json",
        "n_clips": len(registry),
        "n_scored": ens["video_id"].nunique(),
        "clip_only": metrics(clip_df, "clip_top3", "video_id"),
    }
    if ens["adqa_score"].notna().any():
        adqa = ens.dropna(subset=["adqa_score"])
        report["adqa_only"] = metrics(adqa, "adqa_score", "video_id")
        report["ensemble"] = metrics(adqa, "ensemble_mean_clip_top3", "video_id")
        bench = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "ensemble" / "adqa_clip_ensemble_scores.csv")
        bench_rho = float(spearmanr(bench["gt"], bench["ensemble_mean_clip_top3"])[0])
        report["benchmark_ensemble_rho"] = bench_rho
        report["generalization_gap"] = bench_rho - report["ensemble"]["spearman_rho"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "---",
        "title: VATEX-60 Held-Out Generalization",
        "category: research",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "---",
        "",
        "# VATEX-60 Held-Out Eval",
        "",
        f"**{report['n_scored']}** clips from `vatex_overlap.json` (VideoA11y + VATEX tiers, benchmark 18 excluded).",
        "",
        "| Metric | ρ | full order | pairwise |",
        "|--------|---|------------|----------|",
    ]
    for key, label in [("clip_only", "CLIP top3"), ("adqa_only", "ADQA"), ("ensemble", "Ensemble 50/50")]:
        if key in report:
            b = report[key]
            lines.append(
                f"| {label} | {b['spearman_rho']:.3f} | "
                f"{b['full_order']}/{b['full_order_total']} | {b['pairwise_wins']}/{b['pairwise_total']} |"
            )
    if "benchmark_ensemble_rho" in report:
        lines.append(f"\nBenchmark ensemble ρ = **{report['benchmark_ensemble_rho']:.3f}**; gap Δρ = **{report['generalization_gap']:.3f}**")
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== VATEX-60 ===")
    for key in ("clip_only", "adqa_only", "ensemble"):
        if key in report:
            b = report[key]
            print(f"{key}: ρ={b['spearman_rho']:.3f} full={b['full_order']}/{b['full_order_total']}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
